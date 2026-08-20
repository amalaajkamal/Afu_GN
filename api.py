"""
api.py
------
FastAPI service exposing the AFUGN member directory as a JSON API.

Run locally:
    pip install -r requirements.txt
    uvicorn api:app --reload --port 8000

Then browse http://127.0.0.1:8000/docs for interactive Swagger docs.

Design notes:
- Scraping the live site on every request would be slow and impolite, so
  results are cached in memory after the first scrape (or after /refresh
  is called) with a configurable TTL (default 12 hours).
- The scrape can take a while (dozens of pages, each with a polite delay),
  so it runs in a background thread; GET requests made while a scrape is
  in-flight get the previous cached data (or a 202 "still building" if
  there's no cache yet at all).
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import geocode
import research
import scraper

app = FastAPI(
    title="AFUGN Member Directory API",
    description=(
        "Unofficial JSON API for the Age-Friendly University Global Network "
        "member directory (scraped from https://www.afugn.org/afugn-members). "
        "Not affiliated with or endorsed by AFUGN."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_TTL_SECONDS = 12 * 60 * 60  # 12 hours

_cache_lock = threading.Lock()
_cache: dict = {"data": None, "scraped_at": None}
_scrape_in_progress = threading.Event()

class _ResearchCache:
    """Encapsulates the fetch-once-then-poll-fresh pattern for one OpenAlex-
    backed research topic (papers + researchers + fetched_at, refreshed from
    `fetch_fn` on a TTL, blocking the first caller until the initial fetch
    completes). Two instances exist below -- AFU papers and social isolation
    papers are independent topics/pages with their own OpenAlex queries and
    disk caches (see research.py), so this factors out the lock/event/thread
    bookkeeping that would otherwise be duplicated per topic."""

    def __init__(self, fetch_fn: Callable[..., dict]):
        self._fetch_fn = fetch_fn
        self._lock = threading.Lock()
        self._cache: dict = {
            "papers": None,
            "researchers": None,
            "total_citations": None,
            "fetched_at": None,
        }
        self._fetch_in_progress = threading.Event()
        self._fetch_thread: Optional[threading.Thread] = None

    def _run_fetch(self, force: bool = False):
        try:
            result = self._fetch_fn(force=force)
            with self._lock:
                if result["papers"] or self._cache["papers"]:
                    # A non-empty result, or we already have prior good data
                    # to keep: safe to (re)publish, including fetched_at --
                    # this is a genuine fetch, not a total crawl failure.
                    self._cache["papers"] = result["papers"] or self._cache["papers"]
                    self._cache["researchers"] = result["researchers"] or self._cache["researchers"]
                    # .get(): a disk cache written before total_citations existed
                    # (still fresh under the multi-day TTL) won't have this key.
                    self._cache["total_citations"] = result.get("total_citations") or sum(
                        p.get("cited_by_count", 0) for p in (result["papers"] or self._cache["papers"] or [])
                    )
                    if result["papers"]:
                        self._cache["fetched_at"] = result["fetched_at"]
                else:
                    # First-ever fetch came back completely empty (OpenAlex
                    # unreachable/rate-limited, no disk cache to fall back
                    # on). Leave fetched_at unset so ensure_fresh's staleness
                    # check keeps treating the cache as stale and retries on
                    # the next request/poll, instead of locking in an empty
                    # result as "fresh" for CACHE_TTL_SECONDS (up to 7 days)
                    # -- see research.py's own stale-disk-cache fallback,
                    # which this mirrors at the in-memory layer.
                    self._cache["papers"] = []
                    self._cache["researchers"] = []
                    self._cache["total_citations"] = 0
        finally:
            self._fetch_in_progress.clear()

    def ensure_fresh(self, block: bool = False):
        """Kick off a background OpenAlex fetch if the cache is empty or
        stale. If block=True (used by every read endpoint) wait for the
        fetch to finish so we don't return an empty list.

        The frontend's research pages fire the meta/papers/researchers
        endpoints for a topic concurrently on first load, so more than one
        request can land here while the cache is still empty. Stashing the
        thread in self._fetch_thread lets every blocking caller join the
        *same* in-flight fetch, not just the one that started it."""
        stale = (
            self._cache["papers"] is None
            or self._cache["fetched_at"] is None
            or (time.time() - self._cache["fetched_at"]) > research.CACHE_TTL_SECONDS
        )
        if stale and not self._fetch_in_progress.is_set():
            self._fetch_in_progress.set()
            thread = threading.Thread(target=self._run_fetch, daemon=True)
            # Only publish the thread to self._fetch_thread *after* start()
            # returns -- otherwise a concurrent caller (papers/researchers/
            # meta are all requested together on page load) can read the
            # not-yet-started Thread object and call join() on it, which
            # raises "cannot join thread before it is started".
            thread.start()
            self._fetch_thread = thread
        if block and self._cache["papers"] is None and self._fetch_thread is not None:
            self._fetch_thread.join()

    def refresh(self) -> dict:
        if self._fetch_in_progress.is_set():
            return {"status": "already_in_progress"}
        self._fetch_in_progress.set()
        threading.Thread(target=self._run_fetch, args=(True,), daemon=True).start()
        return {"status": "started"}

    def papers(self) -> list[dict]:
        with self._lock:
            return self._cache["papers"] or []

    def researchers(self) -> list[dict]:
        with self._lock:
            return self._cache["researchers"] or []

    def meta(self) -> dict:
        with self._lock:
            papers = self._cache["papers"] or []
            researchers = self._cache["researchers"] or []
            total_citations = self._cache["total_citations"] or 0
            fetched_at = self._cache["fetched_at"]
        return {
            "total_papers": len(papers),
            "total_researchers": len(researchers),
            "total_citations": total_citations,
            "fetched_at": fetched_at,
            "cache_age_seconds": (time.time() - fetched_at) if fetched_at else None,
        }


_afu_research = _ResearchCache(research.fetch_afu_research)
_social_isolation_research = _ResearchCache(research.fetch_social_isolation_research)


class Institution(BaseModel):
    name: str
    region: str
    country: Optional[str] = None
    state_province: Optional[str] = None
    url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MembersResponse(BaseModel):
    count: int
    results: list[Institution]


class MetaInfo(BaseModel):
    total_institutions: int
    scraped_at: Optional[float]
    cache_age_seconds: Optional[float]
    regions: list[str]


class Authorship(BaseModel):
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    institution: Optional[str] = None


class Paper(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    cited_by_count: int = 0
    venue: Optional[str] = None
    oa_url: Optional[str] = None
    authorships: list[Authorship] = []


class Researcher(BaseModel):
    id: str
    name: str
    institutions: list[str] = []
    paper_count: int
    total_citations: int


class PapersResponse(BaseModel):
    count: int
    results: list[Paper]


class ResearchersResponse(BaseModel):
    count: int
    results: list[Researcher]


class ResearchMeta(BaseModel):
    total_papers: int
    total_researchers: int
    total_citations: int
    fetched_at: Optional[float]
    cache_age_seconds: Optional[float]


def _count_by(data: list[dict], field: str) -> dict:
    counts: dict = {}
    for d in data:
        value = d.get(field)
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[0]))


def _run_scrape(regions: Optional[list] = None):
    try:
        data = scraper.scrape_all(regions=regions)
        with _cache_lock:
            if regions is None:
                # Full scrape: replace the whole cache.
                _cache["data"] = data
            else:
                # Partial scrape: merge in, replacing only the affected
                # region(s), keeping everything else from the last full scrape.
                existing = _cache["data"] or []
                kept = [d for d in existing if d["region"] not in regions]
                data = kept + data
                _cache["data"] = data
            _cache["scraped_at"] = time.time()
    finally:
        _scrape_in_progress.clear()

    # Geocoding is rate-limited to ~1 institution/sec by Nominatim's usage
    # policy, so for ~150 institutions it can take well over an hour. Run it
    # in its own background thread *after* publishing the cache, rather than
    # blocking on it here, so /members etc. are usable immediately with
    # whatever coordinates are already disk-cached; latitude/longitude for
    # the rest fill in progressively as this thread mutates the same dicts
    # that are already sitting in `_cache["data"]`.
    threading.Thread(target=geocode.enrich_with_coordinates, args=(data,), daemon=True).start()


def _ensure_cache_fresh(block: bool = False):
    """Kick off a background scrape if the cache is empty or stale.
    If block=True (used the very first time the API is queried with an
    empty cache) wait for it to finish so we don't return an empty list.
    """
    stale = (
        _cache["data"] is None
        or _cache["scraped_at"] is None
        or (time.time() - _cache["scraped_at"]) > CACHE_TTL_SECONDS
    )
    if stale and not _scrape_in_progress.is_set():
        _scrape_in_progress.set()
        t = threading.Thread(target=_run_scrape, daemon=True)
        t.start()
        if block and _cache["data"] is None:
            t.join()


@app.get("/", tags=["meta"])
def root():
    return {
        "message": "AFUGN Member Directory API",
        "docs": "/docs",
        "endpoints": [
            "/members",
            "/members/regions",
            "/members/regions/{region}",
            "/members/countries",
            "/members/countries/{country}",
            "/members/states",
            "/refresh",
            "/research/papers",
            "/research/researchers",
            "/research/meta",
            "/research/refresh",
            "/research/social-isolation/papers",
            "/research/social-isolation/researchers",
            "/research/social-isolation/meta",
            "/research/social-isolation/refresh",
        ],
    }


@app.get("/members", response_model=MembersResponse, tags=["members"])
def get_all_members(
    region: Optional[str] = Query(None, description="Filter by region, e.g. 'Asia'"),
    country: Optional[str] = Query(None, description="Filter by country, e.g. 'Canada'"),
):
    """Return every scraped institution (with a total count), optionally
    filtered by region and/or country."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    if region:
        data = [d for d in data if d["region"].lower() == region.lower()]
    if country:
        data = [d for d in data if (d.get("country") or "").lower() == country.lower()]
    return MembersResponse(count=len(data), results=data)


@app.get("/members/regions", tags=["members"])
def list_regions():
    """List the five top-level regions (continents) and how many institutions
    are in each."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    counts = _count_by(data, "region")
    return {"count": len(counts), "total_institutions": len(data), "regions": counts}


@app.get("/members/regions/{region}", response_model=MembersResponse, tags=["members"])
def get_region(region: str):
    """Return all institutions in a given region (e.g. /members/regions/Asia),
    with a total count."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    result = [d for d in data if d["region"].lower() == region.lower()]
    if not result:
        valid = sorted({d["region"] for d in data})
        raise HTTPException(
            status_code=404,
            detail=f"No institutions found for region '{region}'. Valid regions: {valid}",
        )
    return MembersResponse(count=len(result), results=result)


@app.get("/members/countries", tags=["members"])
def list_countries(
    region: Optional[str] = Query(None, description="Filter by region, e.g. 'Asia'"),
):
    """List every country with at least one institution and how many
    institutions are in each, optionally scoped to a region."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    if region:
        data = [d for d in data if d["region"].lower() == region.lower()]

    counts = _count_by(data, "country")
    return {"count": len(counts), "total_institutions": len(data), "countries": counts}


@app.get("/members/countries/{country}", response_model=MembersResponse, tags=["members"])
def get_country(country: str):
    """Return all institutions in a given country (e.g. /members/countries/Canada),
    with a total count."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    result = [d for d in data if (d.get("country") or "").lower() == country.lower()]
    if not result:
        raise HTTPException(status_code=404, detail=f"No institutions found for country '{country}'.")
    return MembersResponse(count=len(result), results=result)


@app.get("/members/states", tags=["members"])
def list_states(
    country: Optional[str] = Query(None, description="Filter by country, e.g. 'Canada'"),
):
    """List every state/province with at least one institution and how many
    institutions are in each (only meaningful for countries where the
    scraper captured a state/province, e.g. Canada and the United States).
    Optionally scoped to a country."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    if country:
        data = [d for d in data if (d.get("country") or "").lower() == country.lower()]

    counts = _count_by(data, "state_province")
    return {"count": len(counts), "total_institutions": len(data), "states": counts}


@app.get("/meta", response_model=MetaInfo, tags=["meta"])
def get_meta():
    """Cache status: total institutions, when it was last scraped, list of regions."""
    with _cache_lock:
        data = _cache["data"] or []
        scraped_at = _cache["scraped_at"]
    return MetaInfo(
        total_institutions=len(data),
        scraped_at=scraped_at,
        cache_age_seconds=(time.time() - scraped_at) if scraped_at else None,
        regions=sorted({d["region"] for d in data}) if data else [],
    )


@app.post("/refresh", tags=["meta"])
def refresh(region: Optional[str] = Query(None, description="Re-scrape only this region")):
    """Force a fresh scrape. Runs in the background; poll /meta to see when
    scraped_at updates. Without a region param, refreshes everything."""
    if _scrape_in_progress.is_set():
        return {"status": "already_in_progress"}
    regions = [region] if region else None
    _scrape_in_progress.set()
    threading.Thread(target=_run_scrape, args=(regions,), daemon=True).start()
    return {"status": "started", "regions": regions or "all"}


@app.get("/research/papers", response_model=PapersResponse, tags=["research"])
def get_research_papers(
    year: Optional[int] = Query(None, description="Filter by publication year, e.g. 2022"),
):
    """Return AFU-related research papers (from OpenAlex), sorted by citation
    count descending, optionally filtered by publication year. Never blocks
    on a cold/stale cache -- a background fetch is kicked off and this
    returns whatever is cached right now (empty on a fully cold cache);
    poll /research/meta or re-request until total_papers/count is
    non-zero."""
    _afu_research.ensure_fresh(block=False)
    papers = _afu_research.papers()

    if year is not None:
        papers = [p for p in papers if p.get("publication_year") == year]
    papers = sorted(papers, key=lambda p: p.get("cited_by_count") or 0, reverse=True)
    return PapersResponse(count=len(papers), results=papers)


@app.get("/research/researchers", response_model=ResearchersResponse, tags=["research"])
def get_researchers(
    limit: int = Query(50, ge=1, le=500, description="Max number of researchers to return"),
):
    """Return researchers behind AFU-related papers, ranked by total
    citations across their AFU-matched papers, descending. Non-blocking --
    see /research/papers."""
    _afu_research.ensure_fresh(block=False)
    researchers = _afu_research.researchers()
    return ResearchersResponse(count=len(researchers), results=researchers[:limit])


@app.get("/research/meta", response_model=ResearchMeta, tags=["research"])
def get_research_meta():
    """Cache status for the AFU research dataset: paper/researcher counts and
    when it was last fetched from OpenAlex."""
    return ResearchMeta(**_afu_research.meta())


@app.post("/research/refresh", tags=["research"])
def refresh_research():
    """Force a fresh fetch from OpenAlex for the AFU research dataset. Runs
    in the background; poll /research/meta to see when fetched_at updates."""
    return _afu_research.refresh()


@app.get("/research/social-isolation/papers", response_model=PapersResponse, tags=["research"])
def get_social_isolation_papers(
    year: Optional[int] = Query(None, description="Filter by publication year, e.g. 2022"),
):
    """Return social-isolation/loneliness-in-older-adults research papers
    (from OpenAlex), sorted by citation count descending, optionally
    filtered by publication year. Independent topic/dataset from
    /research/papers -- see research.py. Non-blocking -- see
    /research/papers for the cold-cache behavior."""
    _social_isolation_research.ensure_fresh(block=False)
    papers = _social_isolation_research.papers()

    if year is not None:
        papers = [p for p in papers if p.get("publication_year") == year]
    papers = sorted(papers, key=lambda p: p.get("cited_by_count") or 0, reverse=True)
    return PapersResponse(count=len(papers), results=papers)


@app.get(
    "/research/social-isolation/researchers", response_model=ResearchersResponse, tags=["research"]
)
def get_social_isolation_researchers(
    limit: int = Query(50, ge=1, le=500, description="Max number of researchers to return"),
):
    """Return researchers behind social-isolation research papers, ranked by
    total citations across their matched papers, descending."""
    _social_isolation_research.ensure_fresh(block=False)
    researchers = _social_isolation_research.researchers()
    return ResearchersResponse(count=len(researchers), results=researchers[:limit])


@app.get("/research/social-isolation/meta", response_model=ResearchMeta, tags=["research"])
def get_social_isolation_meta():
    """Cache status for the social-isolation research dataset: paper/
    researcher counts and when it was last fetched from OpenAlex."""
    return ResearchMeta(**_social_isolation_research.meta())


@app.post("/research/social-isolation/refresh", tags=["research"])
def refresh_social_isolation_research():
    """Force a fresh fetch from OpenAlex for the social-isolation research
    dataset. Runs in the background; poll /research/social-isolation/meta to
    see when fetched_at updates."""
    return _social_isolation_research.refresh()