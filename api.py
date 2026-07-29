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


class MetaInfo(BaseModel):
    total_institutions: int
    scraped_at: Optional[float]
    cache_age_seconds: Optional[float]
    regions: list[str]


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
                _cache["data"] = kept + data
            _cache["scraped_at"] = time.time()
    finally:
        _scrape_in_progress.clear()


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
            "/members/countries/{country}",
            "/refresh",
        ],
    }


@app.get("/members", response_model=list[Institution], tags=["members"])
def get_all_members(
    region: Optional[str] = Query(None, description="Filter by region, e.g. 'Asia'"),
    country: Optional[str] = Query(None, description="Filter by country, e.g. 'Canada'"),
):
    """Return every scraped institution, optionally filtered by region and/or country."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    if region:
        data = [d for d in data if d["region"].lower() == region.lower()]
    if country:
        data = [d for d in data if (d.get("country") or "").lower() == country.lower()]
    return data


@app.get("/members/regions", tags=["members"])
def list_regions():
    """List the five top-level regions and how many institutions are in each."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    counts: dict = {}
    for d in data:
        counts[d["region"]] = counts.get(d["region"], 0) + 1
    return counts


@app.get("/members/regions/{region}", response_model=list[Institution], tags=["members"])
def get_region(region: str):
    """Return all institutions in a given region (e.g. /members/regions/Asia)."""
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
    return result


@app.get("/members/countries/{country}", response_model=list[Institution], tags=["members"])
def get_country(country: str):
    """Return all institutions in a given country (e.g. /members/countries/Canada)."""
    _ensure_cache_fresh(block=True)
    with _cache_lock:
        data = _cache["data"] or []

    result = [d for d in data if (d.get("country") or "").lower() == country.lower()]
    if not result:
        raise HTTPException(status_code=404, detail=f"No institutions found for country '{country}'.")
    return result


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