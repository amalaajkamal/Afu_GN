# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Unofficial JSON API for the Age-Friendly University Global Network (AFUGN) member
directory, scraped from https://www.afugn.org/afugn-members. Two pieces:

- `scraper.py` — scrapes the live site into a flat list of institution dicts.
- `api.py` — FastAPI service that serves the scraped data with an in-memory,
  TTL-based cache.
- `inspect_page.py` — standalone diagnostic tool (not imported by the other
  two files) for dumping a page's real tag structure when the scraper needs
  to be adjusted against actual markup.
- `app.py` — Streamlit dashboard (AFU Global Network Dashboard) visualizing
  membership data (country/region coverage, principle frequency, activity
  type, audience, summary metrics). Institution/country/region counts and
  per-institution links are pulled live from `api.py` via `api_client.py`
  (with graceful fallback to a static snapshot if the API is unreachable);
  see "Dashboard ↔ API integration" below. Population-65+ figures, AFU
  principle/gap analysis, and the Best Practices Explorer have no API
  equivalent and remain static/CSV-driven (`Form Data Entry-Grid view.csv`).
- `api_client.py` — thin `requests`-based client used only by `app.py` to
  call `api.py`'s endpoints, with `st.cache_data` caching and
  `(data, error)`-tuple returns so the dashboard can fall back instead of
  crashing when the API is down.
- `geocode.py` — looks up real lat/lon coordinates per institution via the
  OpenStreetMap Nominatim search API (no key required) so newly-added AFUGN
  members get plotted automatically instead of needing a hardcoded
  coordinate table; see "Institution geocoding" below.
- `frontend/` — a second, independent React dashboard (Vite + TypeScript +
  Tailwind) covering the same five views as `app.py`. It's additive, not a
  replacement: `app.py` is unmodified and keeps running as before. See "New
  frontend (`frontend/`)" below.

## Commands

```bash
pip install -r requirements.txt

# Run the API server (auto-reload)
uvicorn api:app --reload --port 8000
# -> Swagger UI at http://127.0.0.1:8000/docs

# Run the Streamlit dashboard
streamlit run app.py

# Run the new React frontend (separate terminal, alongside the API above)
cd frontend
npm install
npm run dev              # -> http://localhost:5173
npm run build             # production build to frontend/dist/
node scripts/sync-static-data.mjs   # re-sync static JSON after CSVs change

# Run the scraper standalone, dumps JSON to stdout

python scraper.py                 # all regions
python scraper.py Asia Europe     # only specific regions (keys of REGION_ENTRY_POINTS)

# Inspect a live page's real DOM structure between the "Member Institution(s)"
# heading and the footer -- use this before changing scraper.py's parsing
# logic, and paste the output back for reference
python inspect_page.py <url>
```

There is no test suite, linter, or build step configured for the Python side
of this repo. `frontend/` is a normal Vite/TypeScript project and does have
a build step (`npm run build`, type-checked via `tsc -b`) — see "New
frontend (`frontend/`)" below.

## Architecture

### Scraper (`scraper.py`)

The AFUGN site has no API of its own; the scraper is a from-scratch HTML
crawler over Squarespace-rendered pages. `scrape_all()` starts from five
hardcoded region hub URLs (`REGION_ENTRY_POINTS`) and recursively drills into
sub-pages (e.g. North America -> Canada -> per-province pages) up to
`max_depth` hops, accumulating `Institution` records with region / country /
state-province.

The core difficulty, and the reason for the large module docstring at the top
of the file: the site markup for "a group of institutions" (a country or
state/province heading followed by its member list) is **not consistent
across pages** — there are three different patterns in the wild, and some
pages mix more than one. **Read that docstring before touching `_PageParser`
or `_handle_link`** — it documents exactly which pages use which pattern and
which past parsing bugs (undercounting, phantom countries, inflated counts)
each design decision was added to fix.

Key structural points:
- `_PageParser._walk` does a single top-to-bottom recursive walk of the page
  body, scoped between two hard textual boundaries: a heading matching
  `HEADING_RE` ("member institution(s)...") and the `<footer>` tag. Content
  outside that window (nav menus, which appear twice per page) is never
  considered, deliberately avoiding "climb up from the heading to find a
  content container" heuristics that caused over-counting in earlier
  versions.
- Internal (`afugn.org`) links found during the walk become drill-down
  targets for recursion; external links become leaf institutions.
  `FOOTER_HREF_BLOCKLIST` filters out known nav/footer paths that would
  otherwise look like drill-down pages.
- Group labels (`<strong>`/`<b>` not inside an `<a>`, or an `<li>` with a
  nested `<ul>`/`<ol>`) set `self.current_label`, which subsequent leaf
  institutions attach to as `state_province` (if a country was already
  established from the crawl path) or `country` (if not).
- If you're debugging wrong/missing results on a specific page, run
  `inspect_page.py` against that URL first to see the actual markup rather
  than guessing.

### Manual URL overrides (`afu_urls.json`)

`Institution.url` is filled in two ways: primarily by whatever link the
scraper finds on afugn.org itself while walking a page, and — only when that
comes back empty — by looking the institution name up in `afu_urls.json`
(loaded once at import time via `AFU_URL_OVERRIDES` in `scraper.py`, applied
in `scrape_all()`'s dedupe pass). Never add an override for an institution
the scraper already found a URL for; check the override only kicks in as a
fallback.

**Every URL in this file — for any institution, any region — must point to a
page that is specifically about that institution's AFU / AFUGN involvement.**
Concretely, the linked page has to do at least one of:
- Announce or discuss the institution joining/being designated an
  "Age-Friendly University" or the "Age-Friendly University Global Network".
- Be the institution's own dedicated AFU program/initiative page (e.g. a
  `/age-friendly-university` path, or a research centre's AFU sub-page).
- Otherwise substantively discuss the institution's AFU designation, not just
  mention aging/seniors programs in passing.

It is **not enough** that the page is about aging, gerontology, or seniors
programs in general — a university's general "Centre for Aging" or "Aging
Studies" homepage is *not* a valid override target unless that specific page
also discusses the AFU/AFUGN designation. (Trent University's entry was
originally `trentu.ca/aging/`, the Trent Centre for Aging & Society homepage
— wrong, because that page never mentions AFU/AFUGN at all. It was corrected
to Trent's own 2018 news post announcing AFUGN membership.)

Resolution order when fixing/adding an entry:
1. Check whether afugn.org's own listing for that institution is already a
   hyperlink (e.g. `afugn.org/canada`, `/asian-institutions`, etc.) — if so,
   no override is needed; the scraper will pick it up directly.
2. If not, search for the institution's own page/news post specifically
   about its AFU/AFUGN membership or designation, and use that.
3. If no such page can be found and verified, leave the institution out of
   `afu_urls.json` rather than linking to an unrelated or unverified page —
   a missing link is preferable to an incorrect one.

### API (`api.py`)

Thin FastAPI wrapper around `scraper.scrape_all()`:
- Results are cached in-memory (`_cache`) with a 12-hour TTL
  (`CACHE_TTL_SECONDS`). There is no persistent storage — restarting the
  process drops the cache.
- Scrapes run in a background thread (`_run_scrape`) since crawling dozens of
  pages with a polite per-request delay (`scraper.REQUEST_DELAY`) is slow.
  `_ensure_cache_fresh(block=True)` is called from every read endpoint: if
  the cache is empty this blocks until the first scrape finishes; if it's
  merely stale, a background refresh is kicked off and the (stale) cached
  data is served immediately.
- `POST /refresh` (optionally with `?region=`) forces a re-scrape.
  Region-scoped refreshes merge into the existing cache, replacing only that
  region's entries; a full refresh replaces the whole cache.
- Endpoints: `/`, `/members` (filterable by `region`/`country`),
  `/members/regions`, `/members/regions/{region}`,
  `/members/countries/{country}`, `/meta` (cache status), `/refresh`.
- After every scrape (full or region-scoped) is published to the cache,
  `_run_scrape` kicks off `geocode.enrich_with_coordinates()` in its own
  daemon thread rather than blocking on it — geocoding ~150 institutions at
  Nominatim's ~1/sec policy can take well over an hour, and readers
  shouldn't have to wait on that just to get the newly-scraped names/URLs.
  That thread mutates the same dicts already sitting in `_cache["data"]`, so
  `latitude`/`longitude` fill in progressively: `null` until a lookup
  completes (or if it fails), then populated in place. See "Institution
  geocoding" below.

### Institution geocoding (`geocode.py`)

Per-institution coordinates are looked up live against OpenStreetMap's
Nominatim search API (`name, country` as the query, falling back to just
`name` on a miss) — nothing about individual universities is hardcoded, so an
institution AFUGN adds to its site in the future is geocoded automatically
the next time `api.py` scrapes.

- Nominatim's usage policy caps public requests at 1/second and requires a
  descriptive `User-Agent`; `geocode.py` enforces both (`REQUEST_DELAY`,
  `USER_AGENT`).
- Results are cached to disk at `geocode_cache.json` (gitignored, keyed by
  `name|country`, persists across process restarts) so repeat scrapes only
  pay the network/rate-limit cost for institutions not seen before — an
  institution that fails to geocode is cached as `None` too, so it isn't
  retried on every scrape.
- If `api.py` is unreachable, `app.py`/`api_client.py` never see this data at
  all and fall back to `STATIC_INSTITUTIONS` (name-only, no coordinates); see
  below.

### India map boundary (`india_outline.geojson`)

Any map of India rendered in `app.py` (or any future visualization code)
**must show India's external boundary exactly as per the Indian Constitution
and the Government of India** — this includes the full Union Territories of
Jammu & Kashmir and Ladakh as integral parts of India. Plotly's bundled world
atlas draws this boundary incorrectly, so `load_india_geojson()` overlays the
correct outline from `india_outline.geojson` on top of the base map (see the
`india_geojson` usage in the choropleth/scatter map sections). Do not revert
to Plotly's default/bundled India outline, and if `india_outline.geojson` is
ever regenerated or replaced, verify the replacement still matches the
official Government of India boundary before committing it.

### Dashboard ↔ API integration (`app.py` + `api_client.py`)

`app.py` calls `api.py` (default `http://127.0.0.1:8000`, override via
`AFU_API_BASE_URL`) through `api_client.py` for everything the API covers —
per-country/region institution counts, country lists, and per-institution
`url`s and geocoded `latitude`/`longitude` (see "Institution geocoding"
above). `institution_points()` in `app.py` plots each institution at its real
API-supplied coordinates, falling back to a jittered point around the
country's static centroid only when an institution has no coordinates yet
(geocoding miss, or the API-unreachable static fallback list). The country-
and region-level centroid table, population-65+ figures, and
principle/best-practices data still have no API equivalent and stay
static/CSV-driven.

**Country names from the live scrape don't always match this dashboard's
static lat/lon table** (e.g. the site's "United States of America" vs. the
dashboard's "United States", or the full "Hong Kong Special Administrative
Region of the People's Republic of China" vs. "Hong Kong SAR"). `app.py`
normalizes these via `API_TO_STATIC_COUNTRY_NAME` /
`STATIC_TO_API_COUNTRY_NAME`. If the live sidebar warns that a country "has
no plotted coordinates yet," check whether it's a new unmapped name variant
before assuming the country is actually new to AFUGN.

If `api.py` is unreachable (checked via `/meta`), the dashboard falls back
to its static snapshot values and shows a warning in the sidebar rather than
failing — see `merge_live_country_data`/`merge_live_regional_data` in
`app.py`.

### New frontend (`frontend/`)

A second, independently-built dashboard covering the same four views as
`app.py` (Global Overview, Principle Gap Analysis, Regional Equity, Best
Practices Explorer), built with React + TypeScript + Vite +
Tailwind CSS instead of Streamlit. It is purely additive: nothing in
`app.py`, `api.py`, `api_client.py`, `scraper.py`, or `geocode.py` is
modified or depended on for its own logic beyond reading `api.py`'s HTTP
endpoints. Both frontends can run side by side indefinitely. The full design
plan (palette, typography, component inventory, page-by-page parity notes)
lives in `NEW_FRONTEND_PLAN.md` at the repo root.

- **Theming**: light/dark mode via a `.dark` class on `<html>` (toggle in
  the top bar, persisted to `localStorage`, defaults to
  `prefers-color-scheme`). All color tokens are defined as CSS custom
  properties in `frontend/src/index.css` (`:root` = light, `.dark` =
  dark) — a Claude-styled pastel-terracotta palette with WCAG AA-checked
  text contrast. Chart/map code can't read CSS variables, so the same
  palette is duplicated as literal hex in `frontend/src/lib/mapTheme.ts`;
  keep the two in sync if the palette ever changes. `mapTheme.ts` also
  carries darker "ink" variants of every accent (`regionColorsInk`) for use
  as a solid fill behind white/inverse text (nav active states, region
  tabs) — the plain accent tokens are reserved for large graphical marks
  (chart bars, donut slices, map pins) where the lighter WCAG "non-text"
  3:1 threshold applies instead of 4.5:1.
- **Data layer** (see `NEW_FRONTEND_PLAN.md` §5 for the full rationale):
  - *Live*: institution/region/country/geocoded-coordinate data is fetched
    directly from the running `api.py` (`frontend/src/lib/apiClient.ts`,
    `VITE_API_BASE_URL` env var, default `http://127.0.0.1:8000`), cached
    client-side with React Query (`frontend/src/hooks/useApi.ts`,
    `useDashboardData.ts`, `useInstitutions.ts` — the last two port
    `app.py`'s `merge_live_country_data`/`institution_points()` logic to
    TypeScript).
  - *Static*: the AFU principles table, Best Practices CSV, population-65+
    figures, and `india_outline.geojson` are served as plain files from
    `frontend/public/data/`, generated by
    `frontend/scripts/sync-static-data.mjs` from the repo-root
    CSVs/geojson. That script only reads the repo-root files — re-run it
    manually (`node scripts/sync-static-data.mjs` from `frontend/`)
    whenever those source CSVs change; nothing regenerates it
    automatically.
- **India map boundary**: `frontend/public/data/india_outline.geojson` is a
  direct copy of the repo-root `india_outline.geojson` — the same rule in
  "India map boundary" above applies here too. Don't hand-edit the copy;
  re-run the sync script instead.
- If `api.py` is unreachable, hooks fall back to
  `frontend/public/data/static_country_snapshot.json` (a JSON port of
  `app.py`'s `STATIC_INSTITUTIONS`/`load_static_country_data()`), mirroring
  `app.py`'s own fallback behavior.
