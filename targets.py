from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True, slots=True)
class ParsedTarget:
    original: str
    mid: int
    space_url: str


def parse_target(target: str) -> ParsedTarget:
    cleaned = str(target or "").strip()
    if not cleaned:
        raise ValueError("Target cannot be empty.")

    if cleaned.isdigit():
        mid = int(cleaned)
        return ParsedTarget(cleaned, mid, f"https://space.bilibili.com/{mid}")

    parsed = urlparse(cleaned)
    if parsed.scheme and parsed.netloc and "bilibili.com" in parsed.netloc:
        path_match = re.search(r"/(\d+)(?:/|$)", parsed.path)
        if path_match:
            mid = int(path_match.group(1))
            return ParsedTarget(cleaned, mid, f"https://space.bilibili.com/{mid}")
        query_mid = parse_qs(parsed.query).get("mid")
        if query_mid and query_mid[0].isdigit():
            mid = int(query_mid[0])
            return ParsedTarget(cleaned, mid, f"https://space.bilibili.com/{mid}")

    match = re.search(r"(\d{3,})", cleaned)
    if match:
        mid = int(match.group(1))
        return ParsedTarget(cleaned, mid, f"https://space.bilibili.com/{mid}")

    raise ValueError(f"Could not parse MID from target: {target}")
