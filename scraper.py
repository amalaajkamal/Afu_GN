"""
scraper.py
----------
Scrapes the Age-Friendly University Global Network (AFUGN) member directory
(https://www.afugn.org/afugn-members) into a flat, structured list of
institutions with their region / country / (optional) state-province.

THE SITE IS INCONSISTENT -- READ THIS BEFORE TOUCHING THE PARSER
==================================================================
Manually inspecting every region page turned up THREE different patterns for
how a "group" (country, or state/province) and its institutions are marked up,
and some pages mix more than one:

1. Bold label + plain text lines (most common):
       <strong>Alberta</strong>
       University of Calgary
   Used by: Canada's provinces, all of Asia, Oceania, most of Europe.

2. Nested bullet list -- a <li> containing a nested <ul>/<ol>, where the
   outer <li>'s own text is the group name and each inner <li> is an
   institution:
       <li>Arizona
         <ul><li>Arizona State University</li><li>University of Arizona</li></ul>
       </li>
   Used by: Ireland (inside the Europe page -- mixed with pattern 1!), and
   EVERY state on the United States page (the single largest page on the
   site). Missing this pattern was the #1 cause of undercounting.

3. Bold text wrapped INSIDE a link (institution name, not a group label):
       <a href="https://www.example.edu"><strong>Example University</strong></a>
   Used by: Brazil and Chile on the South America page. A naive "any <strong>
   is a group label" rule misreads these as fake countries and also
   (combined with an over-eager content-boundary heuristic) was the likely
   cause of wildly inflated counts on other pages.

4. Squarespace "accordion" widget -- a <li class="accordion-item"> whose
   title lives in a <span class="accordion-item__title"> (buried inside a
   <button>) and whose institutions live in a *sibling*
   <div class="accordion-item__dropdown"> as one <p> per institution
   (plain text, or a link for the odd institution that has a URL):
       <li class="accordion-item">
         <p class="accordion-item__title-wrapper">
           <button><span class="accordion-item__title">Arizona</span></button>
         </p>
         <div class="accordion-item__dropdown">
           <div class="accordion-item__description">
             <p>Arizona State University</p>
             <p>University of Arizona</p>
           </div>
         </div>
       </li>
   Used by: every state on the United States page (the single largest page
   on the site -- missing this pattern entirely was the #1 cause of
   undercounting, and requires its own detection since it looks like
   pattern 2 but has NO nested <ul>/<ol> -- the institutions live in a
   sibling <div>, not a child list) and the Ireland entry on the Europe
   page.

Also, the region-hub page for North America (the only region with a further
per-country page) uses image-only links whose caption follows as a *separate*
sibling element:
       <a href="/canada"><img></a>
       <strong>Canada</strong>
   so the "label" for that link isn't known until we've looked ahead -- and
   crucially the caption is inside the *next fe-block sibling*, not just
   any next sibling of the link's immediate parent. Climbing only to the
   immediate parent (any div) finds a dead-end with no useful sibling,
   silently fails the lookahead, and lets the *general* strong-tag-is-a-
   label rule catch the caption one link too late -- shifting every label
   on the page by one tile (an earlier bug had Canada's institutions
   getting the URL slug "canada" as a fallback label, and the United
   States' institutions wrongly labelled "Canada"). Always climb to the
   ancestor whose class list contains "fe-block", not just the nearest
   div/p/li.

DESIGN
======
Rather than trying to guess a "content container" by climbing up from the
heading (which risks accidentally including repeated nav-menu links and
caused a bad over-count in an earlier version of this file), we do a single
top-to-bottom walk of the whole page and use two hard, textual boundaries
that are identical on every page of this site:
    START: the heading/bold text containing "Member Institution(s) in ..."
    END:   the <footer> tag
Everything outside [START, END) is ignored, so repeated nav menus (which
appear twice on every page, once for desktop once for mobile) can never leak
in as fake content.

Within [START, END), a single recursive walk classifies each node:
    - <a> tag, internal (afugn.org) link      -> a drill-down page to recurse into
    - <a> tag, external link                  -> an institution (leaf)
    - <strong>/<b> NOT inside an <a>          -> a group label (country/state)
    - <li> with a nested <ul>/<ol>            -> a group label (see pattern 2)
    - other plain text                        -> an institution (leaf), but
      only once we've seen at least one group label (filters out the
      descriptive intro paragraph every page has before its first group).
"""

from __future__ import annotations

import json
import re
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag, NavigableString

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("afugn_scraper")

# Manual overrides mapping institution name -> that institution's own
# dedicated Age-Friendly University page (afugn.org itself rarely links to
# these; most member entries there are plain, un-linked text). Populated
# region-by-region via web research -- see afu_urls.json.
_AFU_URLS_PATH = Path(__file__).with_name("afu_urls.json")


def _load_afu_url_overrides() -> dict:
    try:
        with open(_AFU_URLS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    data.pop("_comment", None)
    return data


AFU_URL_OVERRIDES = _load_afu_url_overrides()

BASE_URL = "https://www.afugn.org"
SITE_DOMAINS = {"afugn.org", "www.afugn.org"}

# Hardcoded entry points: the top-level "afugn-members" page links to these
# five regional hub pages. Verified live (July 2026) against the actual site.
REGION_ENTRY_POINTS = {
    "North America": f"{BASE_URL}/north-american-members",
    "Asia": f"{BASE_URL}/asian-institutions",
    "Europe": f"{BASE_URL}/european-members",
    "Oceania": f"{BASE_URL}/oceanian-members",
    "South America": f"{BASE_URL}/south-american-members",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AFUGN-Directory-Bot/1.0; "
        "+https://www.afugn.org) educational/non-commercial use"
    )
}

REQUEST_DELAY = 1.0  # polite delay between requests, seconds

# Boilerplate internal paths that show up in the nav/footer on every page and
# must never be treated as a drill-down link or institution.
FOOTER_HREF_BLOCKLIST = {
    "/become-a-member", "/benefits-of-membership", "/apply",
    "/application-resources", "/bestpractices", "/summit2026", "/lan",
    "/policy-statements", "/eresources", "/research", "/about-us",
    "/governance-structure", "/regional-leads", "/collaborators",
    "/age-friendly-ecosystem", "/principles", "/afugn-members",
    "/news-and-media", "/support-afugn", "/stay-connected", "/contact-us",
    "/about", "/join-us", "/network-in-action", "/cart", "/",
}

HEADING_RE = re.compile(r"(?=.*\bmember)(?=.*\binstitution)", re.I)


@dataclass
class Institution:
    name: str
    region: str
    country: Optional[str] = None
    state_province: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self):
        return {
            "name": self.name,
            "region": self.region,
            "country": self.country,
            "state_province": self.state_province,
            "url": self.url,
        }


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _is_internal_link(href: str) -> bool:
    if not href or href.startswith("#") or href.startswith("mailto:"):
        return False
    parsed = urlparse(urljoin(BASE_URL, href))
    return parsed.netloc in SITE_DOMAINS


def _is_boilerplate_internal_link(href: str) -> bool:
    """True only for known nav/footer paths on afugn.org itself. Never call
    this on an external href -- e.g. https://www.asu.edu has an empty path
    and must NOT be caught here."""
    parsed = urlparse(urljoin(BASE_URL, href))
    path = parsed.path.rstrip("/") or "/"
    return path in FOOTER_HREF_BLOCKLIST


def _fetch(url: str) -> BeautifulSoup:
    logger.info("Fetching %s", url)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def _direct_label_text(li: Tag) -> str:
    """Text owned directly by a <li> before its nested <ul>/<ol> starts
    (e.g. the 'Arizona' in <li>Arizona<ul>...institutions...</ul></li>)."""
    parts = []
    for child in li.children:
        if isinstance(child, Tag) and child.name in ("ul", "ol"):
            break
        parts.append(child.get_text() if isinstance(child, Tag) else str(child))
    return _clean_text("".join(parts))


def _lookahead_caption(a_tag: Tag):
    """For image-only drill-down links whose caption is a *following
    sibling* block (the North-America hub-page pattern), find that caption.
    Returns (label_text, strong_tag_to_mark_consumed) or (None, None).

    The caption lives in the *next fe-block sibling*, not just any next
    sibling of the link's nearest div/p/li -- that nearest ancestor is
    itself several dead-end divs deep with no useful sibling of its own.
    """
    block = a_tag
    while block.parent is not None:
        block = block.parent
        classes = block.get("class") or []
        if "fe-block" in classes:
            break
        if block.name == "body":
            break
    sib = block.find_next_sibling()
    while sib is not None:
        if isinstance(sib, Tag):
            if sib.find("a"):
                return None, None  # hit the next tile's link first
            strong = sib.find(["strong", "b"])
            if strong:
                text = _clean_text(strong.get_text())
                if text and not HEADING_RE.search(text):
                    return text, strong
            if _clean_text(sib.get_text()):
                return None, None  # non-empty content with no caption: give up
        sib = sib.find_next_sibling()
    return None, None


class _PageParser:
    """Walks one page's HTML (already scoped to <body>) and produces the
    list of institutions and drill-down links found on it."""

    def __init__(self, region: str, country: Optional[str]):
        self.region = region
        self.country = country
        self.institutions: list[Institution] = []
        self.drill_down: list[tuple] = []
        self.current_label: Optional[str] = None
        self.label_seen = False
        self.started = False  # becomes True once we pass the heading
        self.consumed_ids: set = set()

    def run(self, body: Tag):
        self._walk(body)
        return self.institutions, self.drill_down

    # -- helpers -----------------------------------------------------
    def _emit_institution(self, name: str, url: Optional[str]):
        name = _clean_text(name)
        if not name or len(name) < 3:
            return
        self.institutions.append(
            Institution(
                name=name,
                region=self.region,
                country=self.country if self.country else self.current_label,
                state_province=self.current_label if self.country else None,
                url=url,
            )
        )

    def _set_label(self, text: str):
        text = _clean_text(text)
        if text and not HEADING_RE.search(text):
            self.current_label = text
            self.label_seen = True

    # -- main walk -----------------------------------------------------
    def _walk(self, node: Tag):
        for child in node.children:
            if isinstance(child, NavigableString):
                if self.started and self.label_seen:
                    for line in str(child).split("\n"):
                        self._emit_institution(line, None)
                continue
            if not isinstance(child, Tag):
                continue

            if child.name in ("script", "style"):
                continue

            if id(child) in self.consumed_ids:
                continue

            if child.name == "footer":
                return  # hard stop: never look past the footer

            if not self.started:
                # Still looking for the "Member Institution(s) in ..." heading.
                if child.name in ("h1", "h2", "h3", "h4", "strong", "b") and HEADING_RE.search(
                    child.get_text()
                ):
                    self.started = True
                    continue
                self._walk(child)
                continue

            # From here on, self.started is True.
            if child.name == "a":
                self._handle_link(child)
                continue  # never descend into a link's own children separately

            if child.name == "li":
                title_span = child.find("span", class_="accordion-item__title")
                dropdown = child.find("div", class_="accordion-item__dropdown")
                if title_span is not None and dropdown is not None:
                    self._set_label(title_span.get_text())
                    self._walk(dropdown)
                    continue

                nested_list = child.find(["ul", "ol"], recursive=False)
                if nested_list is not None:
                    self._set_label(_direct_label_text(child))
                    self._walk(nested_list)
                    continue
                # Fallback: some Squarespace list blocks render the
                # sub-list as the NEXT SIBLING of the label <li> rather
                # than truly nested inside it, e.g.:
                #   <li>Ireland</li>
                #   <ul><li>Dublin City University</li>...</ul>
                sib = child.find_next_sibling()
                if isinstance(sib, Tag) and sib.name in ("ul", "ol"):
                    label_text = _clean_text(child.get_text())
                    if label_text and not HEADING_RE.search(label_text):
                        self._set_label(label_text)
                        self._walk(sib)
                        self.consumed_ids.add(id(sib))
                        continue
                self._walk(child)
                continue

            if child.name in ("strong", "b"):
                if id(child) in self.consumed_ids:
                    continue
                self._set_label(child.get_text())
                continue

            self._walk(child)

    def _handle_link(self, a_tag: Tag):
        href = a_tag.get("href", "")
        if not href:
            return
        if _is_internal_link(href) and _is_boilerplate_internal_link(href):
            return  # nav/footer link, never content

        full_url = urljoin(BASE_URL, href)
        text = _clean_text(a_tag.get_text())
        if not text:
            img = a_tag.find("img")
            if img and img.get("alt"):
                text = _clean_text(img["alt"])

        if _is_internal_link(href):
            label = self.current_label
            if label is None:
                label, consumed_tag = _lookahead_caption(a_tag)
                if consumed_tag is not None:
                    self.consumed_ids.add(id(consumed_tag))
            if label is None:
                label = text or full_url.rsplit("/", 1)[-1]
            self.drill_down.append((label, full_url))
            # Consume so this one-off tile caption can't bleed into the next
            # tile's link (only matters on hub pages with several tiles).
            self.current_label = None
            return

        if not text:
            return
        self._emit_institution(text, full_url)


def _parse_group_page(url: str, region: str, country: Optional[str] = None):
    soup = _fetch(url)
    body = soup.body or soup
    parser = _PageParser(region, country)
    return parser.run(body)


def scrape_all(regions: Optional[list] = None, max_depth: int = 3) -> list[dict]:
    """Scrape the full AFUGN directory.

    Args:
        regions: optional list of region names to limit scraping to
                  (must match keys in REGION_ENTRY_POINTS).
        max_depth: safety limit on how many drill-down hops to follow.

    Returns:
        A flat list of institution dicts.
    """
    all_institutions: list[Institution] = []
    entry_points = REGION_ENTRY_POINTS
    if regions:
        entry_points = {k: v for k, v in REGION_ENTRY_POINTS.items() if k in regions}

    for region_name, region_url in entry_points.items():
        _crawl(region_url, region_name, country=None, depth=0, max_depth=max_depth,
               out=all_institutions)

    seen = set()
    deduped = []
    for inst in all_institutions:
        key = (inst.name, inst.region, inst.country, inst.state_province)
        if key in seen:
            continue
        seen.add(key)
        if not inst.url:
            inst.url = AFU_URL_OVERRIDES.get(inst.name)
        deduped.append(inst)

    return [inst.to_dict() for inst in deduped]


def _crawl(url: str, region: str, country: Optional[str], depth: int, max_depth: int, out: list):
    if depth > max_depth:
        logger.warning("Max depth exceeded at %s, stopping recursion", url)
        return
    try:
        institutions, drill_down = _parse_group_page(url, region, country)
    except requests.RequestException as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return

    out.extend(institutions)

    for label, sub_url in drill_down:
        next_country = country or label
        _crawl(sub_url, region, next_country, depth + 1, max_depth, out)


if __name__ == "__main__":
    import json
    import sys

    only = sys.argv[1:] or None
    data = scrape_all(regions=only)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\n--- Scraped {len(data)} institutions ---", file=sys.stderr)