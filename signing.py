from __future__ import annotations

import hashlib
import re
import time
import urllib.parse
from typing import Any


MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43,
    5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16,
    24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59,
    6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def extract_img_key(url: str) -> str:
    return url.rsplit("/", 1)[1].split(".", 1)[0]


def get_mixin_key(raw: str) -> str:
    return "".join(raw[index] for index in MIXIN_KEY_ENC_TAB if index < len(raw))[:32]


def enc_wbi(params: dict[str, Any], img_key: str, sub_key: str) -> dict[str, Any]:
    mixin_key = get_mixin_key(img_key + sub_key)
    normalized = {key: "" if value is None else value for key, value in params.items()}
    normalized["wts"] = str(int(time.time()))
    ordered = dict(sorted(normalized.items()))

    query_parts: list[str] = []
    for key, value in ordered.items():
        safe_value = re.sub(r"[!'()*]", "", str(value))
        query_parts.append(
            f"{urllib.parse.quote(str(key), safe='')}="
            f"{urllib.parse.quote(safe_value, safe='')}"
        )
    query = "&".join(query_parts)
    ordered["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return ordered
