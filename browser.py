from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class BrowserContext:
    user_agent: str
    cookies: list[dict[str, Any]]
    wbi_img_url: str
    wbi_sub_url: str
    dm_img_list: str
    dm_img_str: str
    dm_cover_img_str: str
    dm_img_inter: str


DEFAULT_EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def resolve_edge_binary(explicit_path: str | None = None) -> str | None:
    if explicit_path:
        path = Path(explicit_path)
        if path.exists():
            return str(path)
        raise FileNotFoundError(f"Edge binary not found: {explicit_path}")

    edge_on_path = shutil.which("msedge")
    if edge_on_path:
        return edge_on_path

    for candidate in DEFAULT_EDGE_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return None


def bootstrap_browser_context(
    mid: int,
    *,
    headless: bool = True,
    edge_binary: str | None = None,
) -> BrowserContext:
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1600,2200")

    resolved_edge = resolve_edge_binary(edge_binary)
    if resolved_edge:
        options.binary_location = resolved_edge

    driver = webdriver.Edge(options=options)
    try:
        driver.get(f"https://space.bilibili.com/{mid}/video")
        time.sleep(2)

        env: dict[str, str] | None = None
        for _ in range(8):
            env = driver.execute_script(
                """
                const userLog = window.__biliUserFp__?.queryUserLog?.({ target: 'web' }) || [];
                const [dm_img_list, dm_img_str, dm_cover_img_str, dm_img_inter] = userLog;
                const wbi = localStorage.getItem('wbi_img_urls') || '';
                const [wbi_img_url, wbi_sub_url] = wbi.split('-');
                return {
                  user_agent: navigator.userAgent || '',
                  dm_img_list: dm_img_list || '',
                  dm_img_str: dm_img_str || '',
                  dm_cover_img_str: dm_cover_img_str || '',
                  dm_img_inter: dm_img_inter || '',
                  wbi_img_url: wbi_img_url || '',
                  wbi_sub_url: wbi_sub_url || ''
                };
                """
            )
            if env and env.get("wbi_img_url") and env.get("wbi_sub_url"):
                break
            time.sleep(1.5)

        if not env or not env.get("wbi_img_url") or not env.get("wbi_sub_url"):
            raise RuntimeError("Failed to get Bilibili browser context.")

        return BrowserContext(
            user_agent=env.get("user_agent", ""),
            cookies=driver.get_cookies(),
            wbi_img_url=env.get("wbi_img_url", ""),
            wbi_sub_url=env.get("wbi_sub_url", ""),
            dm_img_list=env.get("dm_img_list", ""),
            dm_img_str=env.get("dm_img_str", ""),
            dm_cover_img_str=env.get("dm_cover_img_str", ""),
            dm_img_inter=env.get("dm_img_inter", ""),
        )
    finally:
        driver.quit()
