"""Check the built website (site/) for broken internal links, anchors and images.

Usage: python tools/check_site.py [site]
Exits with status 1 if anything is broken, so the publishing workflow stops.
"""

import os
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse

SITE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "site")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "img" and a.get("src"):
            self.links.append(a["src"])


def target_file(path):
    full = os.path.join(SITE, path.lstrip("/"))
    if path.endswith("/") or os.path.isdir(full):
        full = os.path.join(full, "index.html")
    return full


pages = {}
for directory, _, names in os.walk(SITE):
    for name in names:
        if name.endswith(".html"):
            full = os.path.join(directory, name)
            parser = Page()
            with open(full, encoding="utf-8") as f:
                parser.feed(f.read())
            pages[full] = parser

errors = 0
for full, page in sorted(pages.items()):
    if os.path.basename(full) == "404.html":
        continue
    url = "/" + os.path.relpath(full, SITE).replace(os.sep, "/")
    for link in page.links:
        parsed = urlparse(urljoin(url, link))
        if parsed.scheme or parsed.netloc:
            continue  # external link
        path, anchor = unquote(parsed.path), unquote(parsed.fragment)
        dest = target_file(path)
        if not os.path.exists(dest):
            print(f"{url}: missing {link}")
            errors += 1
        elif anchor and dest in pages and anchor not in pages[dest].ids:
            print(f"{url}: missing anchor {link}")
            errors += 1

print(f"{len(pages)} pages checked, {errors} problem(s)")
sys.exit(1 if errors else 0)
