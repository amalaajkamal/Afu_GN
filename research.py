"""
research.py
------------
Fetches research papers and researchers related to the Age-Friendly
University movement from the OpenAlex API (https://api.openalex.org), a
free, keyless academic index. No dependency beyond `requests` is needed.

Design notes:
- OpenAlex `works` are searched for "age-friendly university" / "age
  friendly university" restricted to the *title* field
  (`filter=title.search:...`) rather than OpenAlex's default title+abstract+
  fulltext search. Title-only search is deliberately much stricter: matching
  across abstract/fulltext pulled in a lot of general ageism/aging-in-place
  papers that never actually discuss the Age-Friendly University movement.
  Requiring the phrase in the title keeps results on-topic, at the cost of
  missing papers that discuss AFU substantively without naming it in the
  title -- an acceptable v1 tradeoff for quality over recall. Cross-
  referencing author affiliations against the scraped AFUGN institution list
  would recover more borderline cases but isn't implemented here.
- Two broader terms were tried and deliberately dropped -- see the
  SEARCH_PHRASES comments for why: a bare "afu" collides with GETUG-AFU (an
  unrelated cancer trials group acronym), and "aging"/"age friendly" alone
  surface the WHO's separate, much larger and more-cited "age-friendly
  cities/communities" field, burying actual AFU-university papers under it
  in the citation-sorted /research/papers list.
- "Top researcher" ranking is by total citations across an author's
  AFU-matched papers specifically (summed from the fetched dataset), not
  their global OpenAlex citation count -- that keeps the ranking scoped to
  AFU-relevant output.
- Results are cached to disk (RESEARCH_CACHE_PATH) with a TTL, mirroring
  geocode.py's disk-cache resilience but at the bulk-fetch level: a fresh
  process reuses the last fetch instead of always hitting OpenAlex.
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional

import requests

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
USER_AGENT = "AFU-API/1.0 (https://github.com/; unofficial AFUGN research explorer)"
OPENALEX_MAILTO = os.environ.get("OPENALEX_MAILTO")  # optional: joins OpenAlex's "polite pool"

SEARCH_PHRASES = [
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
PER_PAGE = 200
REQUEST_DELAY = 0.25
REQUEST_TIMEOUT = 20

RESEARCH_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_cache.json")
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours -- academic output changes slowly


def _headers() -> dict:
    return {"User-Agent": USER_AGENT}


def _params(phrase: str, cursor: str) -> dict:
    params = {
        "filter": f"title.search:{phrase}",
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


def _fetch_papers(max_results: int) -> list[dict]:
    # Two phrasings (hyphenated / not) are queried separately and merged by
    # work id, since OpenAlex's title.search filter doesn't reliably OR
    # across differently-punctuated phrases in one request.
    papers_by_id: dict[str, dict] = {}
    for phrase in SEARCH_PHRASES:
        cursor = "*"
        while cursor and len(papers_by_id) < max_results:
            try:
                resp = requests.get(
                    OPENALEX_WORKS_URL,
                    params=_params(phrase, cursor),
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


def _load_disk_cache() -> Optional[dict]:
    if not os.path.exists(RESEARCH_CACHE_PATH):
        return None
    try:
        with open(RESEARCH_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_disk_cache(result: dict) -> None:
    try:
        with open(RESEARCH_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
    except OSError:
        pass


def fetch_afu_research(max_results: int = 1000, force: bool = False) -> dict:
    """Return {"papers": [...], "researchers": [...], "fetched_at": epoch}.

    Reuses a fresh disk cache when available so a fresh process doesn't have
    to re-hit OpenAlex on every restart; pass force=True to bypass it (used
    by the API's manual /research/refresh endpoint)."""
    if not force:
        cached = _load_disk_cache()
        if cached and time.time() - cached.get("fetched_at", 0) < CACHE_TTL_SECONDS:
            return cached

    papers = _fetch_papers(max_results)
    researchers = _aggregate_researchers(papers)
    result = {"papers": papers, "researchers": researchers, "fetched_at": time.time()}
    _save_disk_cache(result)
    return result


if __name__ == "__main__":
    import sys

    data = fetch_afu_research(force=True)
    json.dump(data, sys.stdout, indent=2)
