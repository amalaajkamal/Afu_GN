"""
geocode.py
----------
Looks up real latitude/longitude coordinates for scraped institutions, so the
dashboard can plot each university at its actual location instead of jittering
markers around a hardcoded country centroid. This runs against the live
OpenStreetMap Nominatim search API (no API key required), so any institution
newly added to the AFUGN site is picked up automatically on the next scrape --
nothing about individual universities is hardcoded here.

Nominatim's usage policy caps public requests at 1/second and requires a
descriptive User-Agent, so results are cached to disk (GEOCODE_CACHE_PATH) --
keyed by institution name + country -- and only cache misses hit the network.
On repeat scrapes, only newly-seen institutions cost any request time at all.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Optional

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "AFU-API/1.0 (https://github.com/; unofficial AFUGN member directory)"
REQUEST_DELAY = 1.1  # Nominatim policy: max 1 request/second, stay under it.
REQUEST_TIMEOUT = 10

GEOCODE_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geocode_cache.json")

_cache_lock = threading.Lock()
_cache: Optional[dict] = None


def _load_cache() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    with _cache_lock:
        if _cache is not None:
            return _cache
        if os.path.exists(GEOCODE_CACHE_PATH):
            try:
                with open(GEOCODE_CACHE_PATH, encoding="utf-8") as f:
                    _cache = json.load(f)
            except (json.JSONDecodeError, OSError):
                _cache = {}
        else:
            _cache = {}
        return _cache


def _save_cache():
    with _cache_lock:
        try:
            with open(GEOCODE_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(_cache, f, indent=2, sort_keys=True)
        except OSError:
            pass


def _cache_key(name: str, country: Optional[str]) -> str:
    return f"{name.strip().lower()}|{(country or '').strip().lower()}"


def _query_nominatim(query: str) -> Optional[dict]:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if not results:
        return None
    try:
        return {"latitude": float(results[0]["lat"]), "longitude": float(results[0]["lon"])}
    except (KeyError, ValueError, TypeError):
        return None


def geocode_institution(name: str, country: Optional[str]) -> Optional[dict]:
    """Look up {"latitude", "longitude"} for one institution, using the disk
    cache first and falling back to a live Nominatim query on a cache miss.
    Returns None if no coordinates could be found."""
    cache = _load_cache()
    key = _cache_key(name, country)
    if key in cache:
        return cache[key]

    query = f"{name}, {country}" if country else name
    coords = _query_nominatim(query)
    if coords is None and country:
        # Retry with just the institution name -- some queries fail when the
        # AFUGN country label doesn't match how OSM names the country.
        coords = _query_nominatim(name)
    time.sleep(REQUEST_DELAY)

    with _cache_lock:
        cache[key] = coords
    _save_cache()
    return coords


def enrich_with_coordinates(institutions: list[dict]) -> list[dict]:
    """Add "latitude"/"longitude" keys (float or None) to each institution
    dict in place, geocoding cache misses live. Safe to call on every scrape
    -- previously-geocoded institutions are served from disk instantly, so
    only newly-added AFUGN members incur any network delay."""
    for inst in institutions:
        coords = geocode_institution(inst["name"], inst.get("country"))
        inst["latitude"] = coords["latitude"] if coords else None
        inst["longitude"] = coords["longitude"] if coords else None
    return institutions
