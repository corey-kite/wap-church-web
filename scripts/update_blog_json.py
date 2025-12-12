#!/usr/bin/env python3
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

FEED_URL = "https://www.firstbaptistchurchwapato.com/blog-feed.xml"
OUT_FILE = "blog.json"
MAX_ITEMS = 6

def strip_html(s: str) -> str:
    if not s:
        return ""
    # remove tags
    s = re.sub(r"<[^>]+>", "", s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def safe_text(el, tag):
    child = el.find(tag)
    return (child.text or "").strip() if child is not None and child.text else ""

def parse_date(pub_date: str) -> str:
    if not pub_date:
        return ""
    try:
        dt = parsedate_to_datetime(pub_date)
        # ISO format for consistency
        return dt.astimezone().isoformat()
    except Exception:
        try:
            # fallback: try generic parse
            return datetime.fromisoformat(pub_date).isoformat()
        except Exception:
            return ""

def main():
    with urllib.request.urlopen(FEED_URL) as resp:
        xml_bytes = resp.read()

    root = ET.fromstring(xml_bytes)

    # RSS usually: <rss><channel><item>...</item></channel></rss>
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("RSS channel not found")

    items = channel.findall("item")[:MAX_ITEMS]
    out_items = []

    for item in items:
        title = safe_text(item, "title") or "Blog Post"
        link = safe_text(item, "link") or "https://www.firstbaptistchurchwapato.com/blog"
        pub_date = parse_date(safe_text(item, "pubDate"))

        # description may contain HTML
        desc = safe_text(item, "description")
        excerpt = strip_html(desc)
        if len(excerpt) > 220:
            excerpt = excerpt[:220].rstrip() + "…"

        out_items.append({
            "title": title,
            "link": link,
            "pubDate": pub_date,
            "excerpt": excerpt
        })

    payload = {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "source": FEED_URL,
        "items": out_items
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT_FILE} with {len(out_items)} items.")

if __name__ == "__main__":
    main()
