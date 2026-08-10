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

## Commands

```bash
pip install -r requirements.txt

# Run the API server (auto-reload)
uvicorn api:app --reload --port 8000
# -> Swagger UI at http://127.0.0.1:8000/docs

# Run the scraper standalone, dumps JSON to stdout

python scraper.py                 # all regions
python scraper.py Asia Europe     # only specific regions (keys of REGION_ENTRY_POINTS)

# Inspect a live page's real DOM structure between the "Member Institution(s)"
# heading and the footer -- use this before changing scraper.py's parsing
# logic, and paste the output back for reference
python inspect_page.py <url>
```

There is no test suite, linter, or build step configured in this repo.

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
