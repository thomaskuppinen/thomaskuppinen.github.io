#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "data" / "news.json"

USER_AGENT = "Mozilla/5.0 (compatible; MattKuppinenSiteBot/1.0)"
MAX_SUMMARY_WORDS = 25
PARAGRAPH_PATTERN = re.compile(r"<p\b[^>]*>(.*?)</p>", re.I | re.S)
TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")
META_DESCRIPTION_PATTERNS = (
    re.compile(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', re.I),
)
BLOCKED_PHRASES = (
    "cookie",
    "privacy policy",
    "terms of use",
    "all rights reserved",
    "sign up",
    "log in",
    "watch full replay",
)

SECTIONS: dict[str, dict[str, Any]] = {
    "maxpreps": {
        "source": "MaxPreps",
        "items": [
            {
                "date": "Feb. 18, 2026",
                "title": "Game report: Rolesville",
                "url": "https://www.maxpreps.com/news/fynkaPXnJEW-eoJP7ieE0Q/matt-kuppinen-game-report-vs-rolesville--how-to-watch.htm",
                "cta": "Read article",
            },
            {
                "date": "Feb. 17, 2026",
                "title": "Season-best vs. Corinth Holders",
                "url": "https://www.maxpreps.com/news/auQDMdXfsEWOm0J43jt5qw/matt-kuppinen-game-report-vs-corinth-holders--how-to-watch.htm",
                "cta": "Read article",
            },
            {
                "date": "Feb. 9, 2026",
                "title": "Hot shooting run",
                "url": "https://www.maxpreps.com/news/P-oNxLK1qEmsSea46llQLw/matt-kuppinen-game-report-%40-enloe.htm",
                "cta": "Read article",
            },
        ],
    },
    "prephoops": {
        "source": "Prep Hoops",
        "items": [
            {
                "date": "Jan. 13, 2026",
                "title": "Day Four John Wall Holiday Invitational Standouts (Part One)",
                "url": "https://prephoops.com/2026/01/day-four-john-wall-holiday-invitational-standouts-part-one/",
                "cta": "Read at Prep Hoops",
            },
            {
                "date": "Nov. 28, 2025",
                "title": "919 PG's Making Early Noise",
                "url": "https://prephoops.com/2025/11/919-pgs-making-early-noise/",
                "cta": "Read at Prep Hoops",
            },
            {
                "date": "Sept. 6, 2025",
                "title": "Film Room: Summer in Review (Part 6)",
                "url": "https://prephoops.com/2025/09/film-room-summer-in-review-part-6/",
                "cta": "Read at Prep Hoops",
            },
            {
                "date": "June 30, 2025",
                "title": "Incoming Sophomore Guards at East Coast Invitational",
                "url": "https://prephoops.com/2025/06/incoming-sophomore-guards-at-east-coast-invitational/",
                "cta": "Read at Prep Hoops",
            },
        ],
    },
}


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def normalize_text(value: str) -> str:
    value = unescape(value)
    value = TAG_PATTERN.sub(" ", value)
    value = WHITESPACE_PATTERN.sub(" ", value)
    return value.strip()


def first_25_words(value: str) -> str:
    return " ".join(normalize_text(value).split()[:MAX_SUMMARY_WORDS])


def should_skip_paragraph(candidate: str) -> bool:
    if len(candidate.split()) < 12:
        return True

    lowered = candidate.lower()
    return any(blocked in lowered for blocked in BLOCKED_PHRASES)


def extract_summary(html: str) -> str:
    for match in PARAGRAPH_PATTERN.finditer(html):
        candidate = normalize_text(match.group(1))
        if should_skip_paragraph(candidate):
            continue
        return first_25_words(candidate)

    for pattern in META_DESCRIPTION_PATTERNS:
        match = pattern.search(html)
        if match:
            return first_25_words(match.group(1))

    raise RuntimeError("Could not extract summary from article HTML.")


def hydrate_item(item: dict[str, Any]) -> dict[str, Any]:
    html = fetch_html(item["url"])
    return {
        **item,
        "summary": extract_summary(html),
    }


def build_payload() -> dict[str, Any]:
    sections: dict[str, Any] = {}

    for key, section in SECTIONS.items():
        with ThreadPoolExecutor(max_workers=min(4, len(section["items"]))) as executor:
            hydrated_items = list(executor.map(hydrate_item, section["items"]))

        sections[key] = {
            "source": section["source"],
            "items": hydrated_items,
        }

    return {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sections": sections,
    }


def main() -> None:
    payload = build_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
