"""
research.py
------------
Fetches research papers and researchers for two independent topics from the
OpenAlex API (https://api.openalex.org), a free, keyless academic index. No
dependency beyond `requests` is needed.

- Age-Friendly University (AFU_SEARCH_PHRASES): papers specifically about the
  Age-Friendly University / AFUGN movement. Backs the "Research" page.
- Social isolation (SOCIAL_ISOLATION_SEARCH_PHRASES): papers about social
  isolation/loneliness among older adults (and campus-based responses to
  it). Backs its own, separate "Social Isolation Research" page. This is
  deliberately its own topic with its own cache rather than merged into the
  AFU dataset -- see the note below on why a combined search was dropped.

Design notes:
- OpenAlex `works` are searched restricted to the *title* field
  (`filter=title.search:...`) rather than OpenAlex's default title+abstract+
  fulltext search. Title-only search is deliberately much stricter: matching
  across abstract/fulltext pulled in a lot of loosely-related papers that
  never substantively discuss the topic. Requiring the phrase in the title
  keeps results on-topic, at the cost of missing papers that discuss the
  topic substantively without naming it in the title -- an acceptable v1
  tradeoff for quality over recall.
- Two broader terms were tried for the AFU topic and deliberately dropped --
  see the AFU_SEARCH_PHRASES comments for why: a bare "afu" collides with
  GETUG-AFU (an unrelated cancer trials group acronym), and "aging"/"age
  friendly" alone surface the WHO's separate, much larger and more-cited
  "age-friendly cities/communities" field, burying actual AFU-university
  papers under it in the citation-sorted /research/papers list.
- A dedicated "social isolation" search was first tried AND-ed onto the AFU
  title phrases (title.search:<AFU phrases>,abstract.search:"social
  isolation"), to add isolation-related papers onto the *same* AFU page.
  That was replaced with a fully separate topic/page instead, once it became
  clear "social isolation" is its own substantial research field (thousands
  of papers) worth browsing on its own terms, not just a one-off addendum to
  AFU papers. SOCIAL_ISOLATION_SEARCH_PHRASES below still avoids the bare,
  single-word "social isolation"/"loneliness" search on its own, though:
  tried alone, it matched ~800+ general papers going back to the 1940s
  having nothing to do with older adults or campuses, the same failure mode
  "aging" caused for the AFU topic. Every title phrase pairs "social
  isolation"/"loneliness" (and synonymous framings -- social exclusion,
  disconnection, withdrawal, "socially isolated", "perceived isolation")
  with a second qualifying word (older adults, aging, elderly, seniors,
  campus, university, students, intergenerational, nursing home,
  community-dwelling, retirement, covid) to stay on-topic while still
  catching papers that a narrower phrase list would miss.
  SOCIAL_ISOLATION_ABSTRACT_PHRASES/_EXPANSION_TITLE_WORDS then apply the
  same title-word + exact-abstract-phrase recovery technique used for
  AFU_ABSTRACT_PHRASE below, to pull in papers that discuss the topic
  substantively without naming it in their own title.
- To recover more AFU papers than the title-phrase list alone catches
  (papers that discuss AFU substantively without naming it in their own
  title -- e.g. a case-study titled after a specific campus program),
  AFU_FILTERS also ANDs a few broad, generic title words ("university",
  "campus", "college") with an exact-phrase abstract requirement
  (`abstract.search:"age-friendly university"`). The broad title word alone
  would be far too noisy on its own (that's exactly the "aging"/"age
  friendly" failure mode above), but requiring the precise phrase in the
  abstract keeps it on-topic -- this recovered ~30 additional genuine AFU
  papers in testing, all substantively about the movement.
- "Top researcher" ranking (per topic) is by total citations across an
  author's topic-matched papers specifically (summed from the fetched
  dataset), not their global OpenAlex citation count -- that keeps the
  ranking scoped to the topic's own relevant output.
- Results are cached to disk (one JSON file per topic, RESEARCH_CACHE_DIR)
  with a multi-day TTL (RESEARCH_CACHE_TTL_DAYS, default 7) rather than a
  same-day one, mirroring geocode.py's disk-cache resilience but at the
  bulk-fetch level: a fresh process reuses the last fetch instead of
  re-querying OpenAlex for every new visitor, only re-fetching once the
  cache has actually gone stale (or a manual /refresh is called).
"""

from __future__ import annotations

import json
import os
import time
from typing import Callable, Optional

import requests

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
USER_AGENT = "AFU-API/1.0 (https://github.com/; unofficial AFUGN research explorer)"
OPENALEX_MAILTO = os.environ.get("OPENALEX_MAILTO")  # optional: joins OpenAlex's "polite pool"

AFU_SEARCH_PHRASES = [
    # Precise, AFU-specific phrases -- queried first so they fill the
    # max_results cap before the broad single-word terms below get a turn.
    "age-friendly university",
    "age friendly university",
    "age-friendly universities",
    "age friendly universities",
    "age-friendly campus",
    "age friendly campus",
    "age-friendly higher education",
    "afugn",
    # NOTE: bare "afu" was tried and dropped -- it collides with GETUG-AFU,
    # an unrelated French genito-urinary cancer trials group acronym, which
    # flooded the top of the citation-sorted list with prostate/bladder
    # cancer trial papers (some with 700+ citations). "afugn" alone is
    # precise enough to not need it.
    #
    # NOTE: "aging" and "age friendly" were also tried and dropped. They're
    # not noise in the "wrong field entirely" sense the way "afu" was, but
    # they surface the WHO's separate, much larger and more-cited
    # "age-friendly cities/communities" research field, which outranks
    # actual AFU-university papers in the citation-sorted /research/papers
    # list and buries the papers this page is actually about.
]

# See the module docstring's "recover more AFU papers" note. Every entry
# here requires this exact phrase in the *abstract*, so pairing it with a
# broad, generic title word stays on-topic instead of reintroducing the
# "aging" noise problem.
AFU_ABSTRACT_PHRASE = "age-friendly university"
AFU_ABSTRACT_EXPANSION_TITLE_WORDS = ["university", "campus", "college"]

AFU_FILTERS = [f"title.search:{phrase}" for phrase in AFU_SEARCH_PHRASES] + [
    f'title.search:{word},abstract.search:"{AFU_ABSTRACT_PHRASE}"'
    for word in AFU_ABSTRACT_EXPANSION_TITLE_WORDS
]

SOCIAL_ISOLATION_SEARCH_PHRASES = [
    # Most specific / campus-adjacent phrases first, broader "older
    # adults"/"aging" pairings after -- see the module docstring for why a
    # bare "social isolation"/"loneliness" search is intentionally never
    # used on its own here.
    "social isolation campus",
    "social isolation university",
    "social isolation college students",
    "social isolation intergenerational",
    "combating social isolation",
    "loneliness campus",
    "loneliness college students",
    "loneliness intergenerational",
    # Core older-adult / aging pairings.
    "social isolation older adults",
    "social isolation aging",
    "social isolation elderly",
    "social isolation seniors",
    "social isolation retirement",
    "social isolation nursing home",
    "social isolation community-dwelling",
    "loneliness older adults",
    "loneliness aging",
    "loneliness elderly",
    "loneliness seniors",
    "loneliness nursing home",
    "loneliness community-dwelling",
    # Synonymous framings of the same phenomenon that a plain
    # "social isolation"/"loneliness" search misses entirely -- each is
    # still paired with a qualifying word for the same on-topic reason as
    # above, not used bare.
    "social exclusion older adults",
    "social exclusion elderly",
    "social disconnection older adults",
    "social withdrawal older adults",
    "socially isolated older adults",
    "socially isolated elderly",
    "perceived isolation older adults",
    "social isolation covid older adults",
    "loneliness covid older adults",
]

# See the module docstring's "recover more AFU papers" note -- the same
# technique applied here: a broad, generic title word alone (e.g. "aging")
# would reintroduce exactly the noise problem SOCIAL_ISOLATION_SEARCH_PHRASES
# above avoids, but pairing it with an exact-phrase *abstract* requirement
# stays on-topic while recovering papers that discuss social isolation/
# loneliness substantively without pairing those words in their own title
# (e.g. a paper titled purely after a specific intervention program).
SOCIAL_ISOLATION_ABSTRACT_PHRASES = ["social isolation", "loneliness"]
SOCIAL_ISOLATION_ABSTRACT_EXPANSION_TITLE_WORDS = [
    "older adults",
    "aging",
    "elderly",
    "seniors",
    "campus",
    "university",
]

SOCIAL_ISOLATION_FILTERS = [f"title.search:{phrase}" for phrase in SOCIAL_ISOLATION_SEARCH_PHRASES] + [
    f'title.search:{word},abstract.search:"{phrase}"'
    for phrase in SOCIAL_ISOLATION_ABSTRACT_PHRASES
    for word in SOCIAL_ISOLATION_ABSTRACT_EXPANSION_TITLE_WORDS
]

PER_PAGE = 200
REQUEST_DELAY = 0.25
REQUEST_TIMEOUT = 20

RESEARCH_CACHE_DIR = os.path.dirname(os.path.abspath(__file__))
AFU_CACHE_PATH = os.path.join(RESEARCH_CACHE_DIR, "research_cache.json")
SOCIAL_ISOLATION_CACHE_PATH = os.path.join(RESEARCH_CACHE_DIR, "research_cache_social_isolation.json")

# Academic output changes slowly and OpenAlex is rate-limit-sensitive, so a
# fetch is reused across every visitor for several days rather than
# re-querying OpenAlex per-process-restart/per-visitor. Override via env var
# for local testing (e.g. RESEARCH_CACHE_TTL_DAYS=0 to always refetch).
CACHE_TTL_DAYS = float(os.environ.get("RESEARCH_CACHE_TTL_DAYS", "7"))
CACHE_TTL_SECONDS = CACHE_TTL_DAYS * 24 * 60 * 60

# Bump this whenever the cached result dict's shape changes (e.g. adding
# total_citations) or a fetch's underlying query set changes (e.g. widening
# AFU_FILTERS). A disk cache written under an older version is treated as
# stale regardless of its remaining TTL, so a fresh deploy that ships one of
# those changes doesn't keep serving pre-existing on-disk data -- with a
# multi-day TTL, on a host whose disk survives redeploys, that data could
# otherwise look "live" for days despite being computed by the old code.
CACHE_SCHEMA_VERSION = 3


def _headers() -> dict:
    return {"User-Agent": USER_AGENT}


def _params(filter_str: str, cursor: str) -> dict:
    params = {
        "filter": filter_str,
        "per-page": PER_PAGE,
        "cursor": cursor,
    }
    if OPENALEX_MAILTO:
        params["mailto"] = OPENALEX_MAILTO
    return params


def _extract_paper(work: dict) -> dict:
    authorships = []
    for a in work.get("authorships") or []:
        author = a.get("author") or {}
        institutions = a.get("institutions") or []
        authorships.append(
            {
                "author_id": author.get("id"),
                "author_name": author.get("display_name"),
                "institution": institutions[0].get("display_name") if institutions else None,
            }
        )

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    open_access = work.get("open_access") or {}

    return {
        "id": work.get("id"),
        "title": work.get("title") or work.get("display_name"),
        "publication_year": work.get("publication_year"),
        "doi": work.get("doi"),
        "cited_by_count": work.get("cited_by_count") or 0,
        "venue": source.get("display_name"),
        "oa_url": open_access.get("oa_url"),
        "authorships": authorships,
    }


def _fetch_filter(filter_str: str, papers_by_id: dict[str, dict], max_results: int) -> None:
    cursor = "*"
    while cursor and len(papers_by_id) < max_results:
        try:
            resp = requests.get(
                OPENALEX_WORKS_URL,
                params=_params(filter_str, cursor),
                headers=_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError):
            break

        for work in payload.get("results", []):
            paper = _extract_paper(work)
            if paper["id"]:
                papers_by_id[paper["id"]] = paper
            if len(papers_by_id) >= max_results:
                break

        cursor = (payload.get("meta") or {}).get("next_cursor")
        time.sleep(REQUEST_DELAY)


def _fetch_papers(filters: list[str], max_results: int) -> list[dict]:
    # Each filter is queried separately and merged by work id, since
    # OpenAlex's search filters don't reliably OR across differently-shaped
    # queries (different phrasing, or title-only vs. title+abstract) in one
    # request.
    papers_by_id: dict[str, dict] = {}
    for filter_str in filters:
        _fetch_filter(filter_str, papers_by_id, max_results)
    return list(papers_by_id.values())


def _aggregate_researchers(papers: list[dict]) -> list[dict]:
    by_author: dict[str, dict] = {}
    for paper in papers:
        for a in paper["authorships"]:
            author_id = a["author_id"]
            if not author_id or not a["author_name"]:
                continue
            entry = by_author.setdefault(
                author_id,
                {
                    "id": author_id,
                    "name": a["author_name"],
                    "institutions": set(),
                    "paper_count": 0,
                    "total_citations": 0,
                },
            )
            entry["paper_count"] += 1
            entry["total_citations"] += paper["cited_by_count"]
            if a["institution"]:
                entry["institutions"].add(a["institution"])

    researchers = []
    for entry in by_author.values():
        entry["institutions"] = sorted(entry["institutions"])
        researchers.append(entry)

    researchers.sort(key=lambda r: r["total_citations"], reverse=True)
    return researchers


def _load_disk_cache(cache_path: str) -> Optional[dict]:
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_disk_cache(cache_path: str, result: dict) -> None:
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
    except OSError:
        pass


def _fetch_research(
    filters: list[str], cache_path: str, max_results: int = 1000, force: bool = False
) -> dict:
    """Return {"papers": [...], "researchers": [...], "total_citations": int,
    "fetched_at": epoch} for one topic's filters, reusing a fresh (within
    CACHE_TTL_SECONDS) disk cache when available so OpenAlex is only
    re-queried once every few days -- not on every process restart or every
    visitor; pass force=True to bypass it (used by the API's manual refresh
    endpoints).

    total_citations is computed once here and cached alongside papers/
    researchers, rather than left for the frontend to sum from the papers
    list on every render -- that summing previously used the *live*
    papers query's data specifically, which (now that /research/papers is
    non-blocking, see api.py) can briefly lag behind the papers/researchers
    counts on /research/meta while the initial fetch is still landing. Pre-
    computing it here means all three KPIs come from the same fetch/cache
    and always agree, even mid-bootstrap."""
    if not force:
        cached = _load_disk_cache(cache_path)
        if (
            cached
            and cached.get("cache_schema_version") == CACHE_SCHEMA_VERSION
            and time.time() - cached.get("fetched_at", 0) < CACHE_TTL_SECONDS
        ):
            return cached

    papers = _fetch_papers(filters, max_results)
    if not papers:
        # _fetch_filter() silently breaks out of a phrase's pagination loop
        # on any request error (timeout, rate limiting, network blip) rather
        # than raising, so a fully empty result here almost always means the
        # whole crawl got shut out, not that the topic genuinely has zero
        # papers. Fall back to whatever's still on disk -- even if it's past
        # its TTL or schema version, stale-but-real beats empty -- instead of
        # overwriting a good cache with an empty one that would then be
        # served as "fresh" for the next CACHE_TTL_SECONDS.
        stale_cached = _load_disk_cache(cache_path)
        if stale_cached and stale_cached.get("papers"):
            return stale_cached
        return {
            "papers": [],
            "researchers": [],
            "total_citations": 0,
            "fetched_at": time.time(),
            "cache_schema_version": CACHE_SCHEMA_VERSION,
        }

    researchers = _aggregate_researchers(papers)
    total_citations = sum(p["cited_by_count"] for p in papers)
    result = {
        "papers": papers,
        "researchers": researchers,
        "total_citations": total_citations,
        "fetched_at": time.time(),
        "cache_schema_version": CACHE_SCHEMA_VERSION,
    }
    _save_disk_cache(cache_path, result)
    return result


def fetch_afu_research(max_results: int = 1000, force: bool = False) -> dict:
    return _fetch_research(AFU_FILTERS, AFU_CACHE_PATH, max_results, force)


def fetch_social_isolation_research(max_results: int = 1000, force: bool = False) -> dict:
    return _fetch_research(SOCIAL_ISOLATION_FILTERS, SOCIAL_ISOLATION_CACHE_PATH, max_results, force)


if __name__ == "__main__":
    import sys

    fetchers: dict[str, Callable[..., dict]] = {
        "afu": fetch_afu_research,
        "social-isolation": fetch_social_isolation_research,
    }
    topic = sys.argv[1] if len(sys.argv) > 1 else "afu"
    data = fetchers[topic](force=True)
    json.dump(data, sys.stdout, indent=2)
