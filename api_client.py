"""
api_client.py
-------------
Thin, cached wrapper around the AFUGN member directory API (api.py) for use
by the Streamlit dashboard (app.py).

Every fetch_* function returns a (data, error) tuple: `error` is None on
success, or a short string describing what went wrong. Callers use this to
fall back to static data instead of raising.
"""

from __future__ import annotations

import os
from typing import Optional

import requests
import streamlit as st

API_BASE_URL = os.environ.get("AFU_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = 5


def is_api_available() -> bool:
    try:
        resp = requests.get(f"{API_BASE_URL}/", timeout=REQUEST_TIMEOUT)
        return resp.ok
    except requests.RequestException:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def fetch_meta():
    try:
        resp = requests.get(f"{API_BASE_URL}/meta", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_regions():
    try:
        resp = requests.get(f"{API_BASE_URL}/members/regions", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_countries(region: Optional[str] = None):
    try:
        params = {"region": region} if region else {}
        resp = requests.get(
            f"{API_BASE_URL}/members/countries", params=params, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_states(country: Optional[str] = None):
    try:
        params = {"country": country} if country else {}
        resp = requests.get(
            f"{API_BASE_URL}/members/states", params=params, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_members(region: Optional[str] = None, country: Optional[str] = None):
    try:
        params = {}
        if region:
            params["region"] = region
        if country:
            params["country"] = country
        resp = requests.get(f"{API_BASE_URL}/members", params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


def trigger_refresh(region: Optional[str] = None):
    try:
        params = {"region": region} if region else {}
        resp = requests.post(f"{API_BASE_URL}/refresh", params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


def clear_cache():
    fetch_meta.clear()
    fetch_regions.clear()
    fetch_countries.clear()
    fetch_states.clear()
    fetch_members.clear()
