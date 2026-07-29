"""
scraper.py
----------
Scrapes the Age-Friendly University Global Network (AFUGN) member directory
(https://www.afugn.org/afugn-members) into a flat, structured list of
institutions with their region / country / (optional) state-province.

Why this needs custom logic instead of a simple table scrape:
The site (Squarespace) is NOT consistent in how many "hops" it takes to get
from a region page to an actual list of institutions:

    North America:  region page --> country page (e.g. /canada) --> institutions
                                                    (sometimes grouped by state)
    Asia:           region page --> institutions directly (grouped by country)

So instead of hardcoding depth, we walk each page's content area in document
order, tracking the current bold "group label" (could be a country name on a
region page, or a state/province name on a country page). For each item under
that label we decide:

    - It's a link to another page on afugn.org        -> recurse into it
      (this is a "drill-down" link, e.g. Region -> Country)
    - It's a link to an external domain, or plain text -> it's an institution
      (leaf node)

This mirrors how the site itself is actually organized and is robust to the
site's inconsistent depth.
"""

from __future__ import annotations

import re
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag, NavigableString

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("afugn_scraper")

BASE_URL = "https://www.afugn.org"
MEMBERS_URL = f"{BASE_URL}/afugn-members"
SITE_DOMAINS = {"afugn.org", "www.afugn.org"}

# Hardcoded entry points: the top-level "afugn-members" page always links to
# these five regional hub pages. These URLs are stable navigational anchors
# for the whole site, so we start here rather than trying to auto-detect them
# (the five region tiles on the landing page use image icons, not obvious
# hrefs, which makes generic detection brittle).
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

# Polite delay between requests (seconds) so we don't hammer the site.
REQUEST_DELAY = 1.0

# Footer links that show up on every page and should never be treated as
# content (institution or drill-down links) even though they're internal.
FOOTER_HREF_BLOCKLIST = {
    "/become-a-member", "/benefits-of-membership", "/apply",
    "/application-resources", "/bestpractices", "/summit2026", "/lan",
    "/policy-statements", "/eresources", "/research", "/about-us",
    "/governance-structure", "/regional-leads", "/collaborators",
    "/age-friendly-ecosystem", "/principles", "/afugn-members",
    "/news-and-media", "/support-afugn", "/stay-connected", "/contact-us",
    "/cart", "/", "",
}


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


@dataclass
class ScrapeStats:
    pages_visited: list = field(default_factory=list)


def _is_internal_link(href: str) -> bool:
    """True if href points to another page on afugn.org (a drill-down link),
    False if it's external (a university's own site, i.e. an institution)."""
    if not href:
        return False
    if href.startswith("#") or href.startswith("mailto:"):
        return False
    parsed = urlparse(urljoin(BASE_URL, href))
    return parsed.netloc in SITE_DOMAINS


def _is_footer_or_nav_link(href: str) -> bool:
    """True only for known boilerplate nav/footer links on afugn.org itself.
    External links (a university's own domain) are never considered nav
    links here, even if their path is empty (e.g. https://www.asu.edu)."""
    if not _is_internal_link(href):
        return False
    parsed = urlparse(urljoin(BASE_URL, href))
    return parsed.path.rstrip("/") in {p.rstrip("/") for p in FOOTER_HREF_BLOCKLIST}


def _fetch(url: str) -> BeautifulSoup:
    logger.info("Fetching %s", url)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def _find_content_root(soup: BeautifulSoup) -> Tag:
    """Locate the block of the page that holds the actual member content,
    scoped between the 'Member Institution(s) in ...' heading and the site
    footer. Falls back to <body> if the heading can't be found."""
    heading = soup.find(
        lambda tag: tag.name in ("h1", "h2", "h3", "h4", "strong", "b")
        and tag.get_text(strip=True)
        and re.search(r"member institution", tag.get_text(), re.I)
    )
    if heading is None:
        return soup.body or soup

    # Walk up to a reasonably-sized container that holds the heading and the
    # content that follows it (Squarespace wraps each "block" in its own div,
    # so we climb until we find a parent that also contains later siblings).
    container = heading
    for _ in range(6):
        if container.parent is None:
            break
        container = container.parent
        # Stop climbing once this container holds more than just the heading
        if len(container.find_all(["strong", "b", "a", "p"])) > 3:
            break
    return container


def _iter_content_nodes(root: Tag):
    """Yield (kind, tag) pairs in document order for the tags we care about:
    bold group-labels, links, and paragraph/line text. Skips the footer."""
    for el in root.descendants:
        if not isinstance(el, Tag):
            continue
        if el.name == "footer":
            break
        if el.name in ("strong", "b"):
            yield ("label", el)
        elif el.name == "a":
            yield ("link", el)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _parse_group_page(url: str, region: str, country: Optional[str] = None):
    """Parse one page (region-hub or country page) and return:
        institutions: list[Institution]
        drill_down:   list[(label, url, is_country_level)]
    """
    soup = _fetch(url)
    root = _find_content_root(soup)

    institutions: list[Institution] = []
    drill_down: list[tuple] = []

    current_label = None
    seen_hrefs_under_label = set()

    nodes = list(_iter_content_nodes(root))

    consumed_label_indices: set = set()

    def _next_label_before_next_link(start_idx: int) -> Optional[str]:
        """Peek ahead from start_idx for a bold label that appears before
        the next link (handles the common Squarespace pattern of an image
        link immediately followed by its bold caption, e.g. a country
        icon linking to /canada followed by the text 'Canada'). Marks the
        found label index as "consumed" so it's treated as a one-off
        caption for this link only, and doesn't persist as current_label
        for whatever comes after it."""
        for j in range(start_idx + 1, len(nodes)):
            k2, t2 = nodes[j]
            if k2 == "link":
                return None
            if k2 == "label":
                text = _clean_text(t2.get_text())
                if text and not re.search(r"member institution", text, re.I):
                    consumed_label_indices.add(j)
                    return text
        return None

    for idx, (kind, tag) in enumerate(nodes):
        if kind == "label":
            if idx in consumed_label_indices:
                continue
            text = _clean_text(tag.get_text())
            if text and not re.search(r"member institution", text, re.I):
                current_label = text
                seen_hrefs_under_label = set()
            continue

        if kind == "link":
            href = tag.get("href", "")
            if not href or _is_footer_or_nav_link(href):
                continue
            full_url = urljoin(BASE_URL, href)
            if full_url in seen_hrefs_under_label:
                continue
            seen_hrefs_under_label.add(full_url)

            link_text = _clean_text(tag.get_text())
            if not link_text:
                # Image-only links (e.g. a country flag icon with no
                # caption text) fall back to the image's alt attribute.
                img = tag.find("img")
                if img and img.get("alt"):
                    link_text = _clean_text(img["alt"])

            if _is_internal_link(href):
                # A link back to afugn.org content => a deeper page
                # (region -> country page). Image-only country links carry
                # no useful label of their own (the alt text is a photo
                # description, not the country name) -- the real label is
                # the bold heading that follows/precedes it, so prefer
                # current_label whenever we have one.
                label = (
                    current_label
                    or _next_label_before_next_link(idx)
                    or link_text
                    or full_url.rsplit("/", 1)[-1]
                )
                drill_down.append((label, full_url))
                # Consume the label so it can't bleed into the next
                # drill-down link (each country tile on a region-hub page
                # has its own one-off caption, unlike state/country labels
                # on a leaf page which legitimately apply to several
                # institutions in a row).
                current_label = None
                continue

            if not link_text:
                continue

            institutions.append(
                    Institution(
                        name=link_text,
                        region=region,
                        country=country if country else current_label,
                        state_province=current_label if country else None,
                        url=full_url,
                    )
                )

    # Now also capture *plain-text* institution names that are not links at
    # all (e.g. Canada's "University of Calgary" has no href). These live as
    # NavigableStrings between the label and the next label/link.
    institutions.extend(
        _extract_plain_text_institutions(root, region, country, seen_labels=None)
    )

    return institutions, drill_down


def _extract_plain_text_institutions(root: Tag, region: str, country: Optional[str], seen_labels):
    """Walk paragraph-like blocks to pick up institution names that are plain
    text (no <a> tag at all), grouped under the nearest preceding bold label.
    """
    results: list[Institution] = []
    current_label = None
    label_seen = False
    already_captured_texts = set()

    # Collect the set of texts already captured as links, so we don't
    # duplicate them if a paragraph also contains the linked text.
    for a in root.find_all("a"):
        t = _clean_text(a.get_text())
        if t:
            already_captured_texts.add(t)

    for el in root.descendants:
        if isinstance(el, Tag):
            if el.name == "footer":
                break
            if el.name in ("strong", "b"):
                text = _clean_text(el.get_text())
                if text and not re.search(r"member institution", text, re.I):
                    current_label = text
                    label_seen = True
            continue
        if isinstance(el, NavigableString):
            if not label_seen:
                # Anything before the first bold group label is descriptive
                # intro text (e.g. "Select a country for a full list..."),
                # never an institution name.
                continue
            # Skip strings that are children of <strong>/<b>/<a> (already
            # handled) or of <script>/<style>
            parent_names = {p.name for p in el.parents if isinstance(p, Tag)}
            if parent_names & {"strong", "b", "a", "script", "style"}:
                continue
            for line in str(el).split("\n"):
                text = _clean_text(line)
                if not text or len(text) < 3:
                    continue
                if text in already_captured_texts:
                    continue
                if re.search(r"member institution", text, re.I):
                    continue
                results.append(
                    Institution(
                        name=text,
                        region=region,
                        country=country if country else current_label,
                        state_province=current_label if country else None,
                        url=None,
                    )
                )
                already_captured_texts.add(text)
    return results


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

    # De-duplicate (same institution can occasionally appear twice if the
    # site double-links it).
    seen = set()
    deduped = []
    for inst in all_institutions:
        key = (inst.name, inst.region, inst.country, inst.state_province)
        if key in seen:
            continue
        seen.add(key)
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
        # If we're on the region hub page, `label` is a country name.
        # If we're already inside a country page, `label` is a
        # state/province -- but since state/province level pages linking
        # further out are not expected on this site, we still pass it
        # through as `country` only when we don't already have one.
        next_country = country or label
        _crawl(sub_url, region, next_country, depth + 1, max_depth, out)


if __name__ == "__main__":
    import json
    import sys

    only = sys.argv[1:] or None
    data = scrape_all(regions=only)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\n--- Scraped {len(data)} institutions ---", file=sys.stderr)