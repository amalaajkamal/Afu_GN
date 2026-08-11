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
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import geocode
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