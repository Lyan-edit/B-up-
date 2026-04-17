from __future__ import annotations

import time
from typing import Any

import requests

from .browser import BrowserContext
from .signing import enc_wbi, extract_img_key


class BiliClient:
    def __init__(self, mid: int, context: BrowserContext) -> None:
        self.mid = int(mid)
        self.session = requests.Session()
        for cookie in context.cookies:
            self.session.cookies.set(cookie["name"], cookie["value"])

        self.default_headers = {
            "User-Agent": context.user_agent,
            "Referer": f"https://space.bilibili.com/{self.mid}/video",
        }
        self.img_key = extract_img_key(context.wbi_img_url)
        self.sub_key = extract_img_key(context.wbi_sub_url)
        self.dm_params = {
            "dm_img_list": context.dm_img_list,
            "dm_img_str": context.dm_img_str,
            "dm_cover_img_str": context.dm_cover_img_str,
            "dm_img_inter": context.dm_img_inter,
        }

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        retries: int = 3,
        sleep_sec: float = 0.5,
    ) -> dict[str, Any]:
        merged_headers = dict(self.default_headers)
        if headers:
            merged_headers.update(headers)

        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    params=params,
                    headers=merged_headers,
                    timeout=30,
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("code") == 0:
                    time.sleep(sleep_sec)
                    return payload
                last_error = RuntimeError(f"{url} returned code={payload.get('code')}")
            except Exception as exc:
                last_error = exc
            time.sleep((attempt + 1) * 1.2)

        raise RuntimeError(f"Request failed for {url}: {last_error}")

    def relation_stat(self) -> dict[str, Any]:
        return self._request(
            "GET",
            "https://api.bilibili.com/x/relation/stat",
            params={"vmid": self.mid, "web_location": "333.1387"},
            sleep_sec=0.2,
        )["data"]

    def acc_info(self) -> dict[str, Any]:
        params = enc_wbi(
            {
                "mid": self.mid,
                "platform": "web",
                "web_location": 1550101,
                **self.dm_params,
            },
            self.img_key,
            self.sub_key,
        )
        return self._request(
            "GET",
            "https://api.bilibili.com/x/space/wbi/acc/info",
            params=params,
            sleep_sec=0.3,
        )["data"]

    def arc_search(self, pn: int, ps: int = 20) -> dict[str, Any]:
        params = enc_wbi(
            {
                "mid": self.mid,
                "pn": pn,
                "ps": ps,
                "tid": 0,
                "special_type": "",
                "order": "pubdate",
                "index": 0,
                "keyword": "",
                "order_avoided": "true",
                "platform": "web",
                **self.dm_params,
            },
            self.img_key,
            self.sub_key,
        )
        return self._request(
            "GET",
            "https://api.bilibili.com/x/space/wbi/arc/search",
            params=params,
        )["data"]

    def view(self, bvid: str) -> dict[str, Any]:
        return self._request(
            "GET",
            "https://api.bilibili.com/x/web-interface/view",
            params={"bvid": bvid},
            headers={"Referer": f"https://www.bilibili.com/video/{bvid}"},
        )["data"]

    def archive_tags(self, aid: int) -> list[dict[str, Any]]:
        payload = self._request(
            "GET",
            "https://api.bilibili.com/x/tag/archive/tags",
            params={"aid": aid},
            headers={"Referer": f"https://www.bilibili.com/video/av{aid}"},
            sleep_sec=0.2,
        )
        return payload.get("data") or []

    def reply_main(self, aid: int, ps: int) -> dict[str, Any]:
        payload = self._request(
            "GET",
            "https://api.bilibili.com/x/v2/reply/main",
            params={
                "oid": aid,
                "type": 1,
                "mode": 3,
                "next": 0,
                "ps": ps,
                **self.dm_params,
            },
            headers={"Referer": f"https://www.bilibili.com/video/av{aid}"},
        )
        return payload.get("data") or {}
