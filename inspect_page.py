"""
inspect_page.py
---------------
Diagnostic tool: fetches a real page and prints the ACTUAL tag structure
(tag names, classes, and a short text preview) between the "Member
Institution(s)" heading and the footer.

Run this locally (it needs real network access to afugn.org, which the
assistant's sandbox does not have) and paste the output back so the parser
in scraper.py can be fixed against the real markup instead of guesses:

    python inspect_page.py https://www.afugn.org/canada
    python inspect_page.py https://www.afugn.org/european-members
    python inspect_page.py https://www.afugn.org/united-states-members

Tip: if the output is very long, redirect to a file and share a snippet:
    python inspect_page.py https://www.afugn.org/european-members > europe_dump.txt
"""

import sys
import re

import requests
from bs4 import BeautifulSoup, Tag, NavigableString

HEADING_RE = re.compile(r"(?=.*\bmember)(?=.*\binstitution)", re.I)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AFUGN-Directory-Bot/1.0)"}


def dump(node: Tag, depth: int = 0, started: bool = False, max_text: int = 60):
    for child in node.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if started and text:
                print("  " * depth + f'TEXT: "{text[:max_text]}"')
            continue
        if not isinstance(child, Tag):
            continue
        if child.name in ("script", "style"):
            continue
        if child.name == "footer":
            print("  " * depth + "<footer> -- stopping dump here")
            return started
        if not started:
            if child.name in ("h1", "h2", "h3", "h4", "strong", "b") and HEADING_RE.search(
                child.get_text()
            ):
                print("  " * depth + f"<{child.name}> HEADING FOUND: {child.get_text().strip()!r}")
                started = True
                continue
            started = dump(child, depth, started, max_text)
            continue

        attrs = ""
        if child.get("class"):
            attrs += f" class={child.get('class')}"
        if child.get("style"):
            attrs += f" style={child.get('style')!r}"
        if child.get("href"):
            attrs += f" href={child.get('href')!r}"
        own_text_preview = ""
        direct_strings = [str(s).strip() for s in child.contents if isinstance(s, NavigableString) and str(s).strip()]
        if direct_strings:
            own_text_preview = f'  own_text="{" ".join(direct_strings)[:max_text]}"'
        print("  " * depth + f"<{child.name}{attrs}>{own_text_preview}")
        started = dump(child, depth + 1, started, max_text)
    return started


def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_page.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    print(f"Fetching {url} ...\n", file=sys.stderr)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    started = dump(soup.body or soup)
    if not started:
        print("\n!!! Never found the 'Member Institution(s)' heading on this page. "
              "The heading text/tag may not match what the parser expects.")


if __name__ == "__main__":
    main()