from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from .browser import bootstrap_browser_context
from .client import BiliClient
from .config import CrawlConfig
from .targets import ParsedTarget, parse_target


VIDEO_HEADERS = [
    "sample_index",
    "bvid",
    "aid",
    "title",
    "description",
    "pubdate",
    "duration",
    "duration_minutes",
    "view",
    "like",
    "coin",
    "favorite",
    "share",
    "reply",
    "danmaku",
    "tname",
    "author",
    "tag_names",
]

COMMENT_HEADERS = [
    "video_bvid",
    "video_title",
    "rpid",
    "comment_like",
    "comment_reply_count",
    "member_mid",
    "member_name",
    "member_sex",
    "member_level",
    "member_vip_status",
    "member_official_type",
    "member_sign",
    "comment_message",
]


@dataclass(slots=True)
class CrawlExports:
    base_dir: Path
    raw_dir: Path
    processed_dir: Path
    account_snapshot_json: Path
    video_raw_jsonl: Path
    comment_raw_jsonl: Path
    videos_csv: Path
    comments_csv: Path
    summary_json: Path


@dataclass(slots=True)
class CrawlResult:
    target: ParsedTarget
    exports: CrawlExports
    account: dict[str, Any]
    videos: list[dict[str, Any]]
    comments: list[dict[str, Any]]


def _sanitize_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", str(value or "").strip())
    cleaned = cleaned.strip(". ")
    return cleaned or "untitled"


def _is_formal_video(item: dict[str, Any]) -> bool:
    text = f"{item.get('title', '')} {item.get('description', '')}"
    exclude_keywords = [
        "直播回放", "直播录播", "切片", "抽奖", "预告", "测试号", "置顶说明",
        "招募", "征集", "回顾直播", "活动预告",
    ]
    return not any(keyword in text for keyword in exclude_keywords)


def _build_exports(output_root: Path, account_name: str, mid: int) -> CrawlExports:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = _sanitize_name(account_name or f"mid_{mid}")
    base_dir = output_root / f"{safe_name}_{timestamp}"
    raw_dir = base_dir / "raw"
    processed_dir = base_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return CrawlExports(
        base_dir=base_dir,
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        account_snapshot_json=raw_dir / "account_snapshot.json",
        video_raw_jsonl=raw_dir / "video_raw.jsonl",
        comment_raw_jsonl=raw_dir / "comment_raw.jsonl",
        videos_csv=processed_dir / "videos.csv",
        comments_csv=processed_dir / "comments.csv",
        summary_json=base_dir / "summary.json",
    )


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def crawl_up(
    config: CrawlConfig,
    progress: callable | None = None,
) -> CrawlResult:
    def emit(message: str) -> None:
        if progress is not None:
            progress(message)

    target = parse_target(config.target)
    emit(f"Parsed target MID={target.mid}")
    emit("Bootstrapping browser context")
    context = bootstrap_browser_context(
        target.mid,
        headless=config.headless,
        edge_binary=config.edge_binary,
    )
    client = BiliClient(target.mid, context)

    emit("Fetching account snapshot")
    account = {
        "acc_info": client.acc_info(),
        "relation_stat": client.relation_stat(),
    }
    exports = _build_exports(config.output_root, account["acc_info"].get("name", ""), target.mid)

    collected: list[dict[str, Any]] = []
    raw_video_records: list[dict[str, Any]] = []
    videos: list[dict[str, Any]] = []
    page_number = 1

    emit("Fetching recent videos")
    while len(collected) < config.video_limit:
        payload = client.arc_search(page_number, ps=20)
        vlist = payload.get("list", {}).get("vlist", [])
        if not vlist:
            break
        for item in vlist:
            if _is_formal_video(item):
                collected.append(item)
            if len(collected) >= config.video_limit:
                break
        page_number += 1

    for index, item in enumerate(collected[: config.video_limit], start=1):
        detail = client.view(item["bvid"])
        tags = client.archive_tags(detail["aid"])
        stat = detail.get("stat", {})
        tag_names = [tag.get("tag_name", "") for tag in tags if tag.get("tag_name")]
        raw_video_records.append(
            {
                "sample_index": index,
                "list_item": item,
                "view_detail": detail,
                "archive_tags": tags,
            }
        )
        videos.append(
            {
                "sample_index": index,
                "bvid": detail.get("bvid"),
                "aid": detail.get("aid"),
                "title": detail.get("title"),
                "description": detail.get("desc"),
                "pubdate": datetime.fromtimestamp(detail.get("pubdate", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                "duration": detail.get("duration", 0),
                "duration_minutes": round((detail.get("duration", 0) or 0) / 60, 2),
                "view": stat.get("view", 0),
                "like": stat.get("like", 0),
                "coin": stat.get("coin", 0),
                "favorite": stat.get("favorite", 0),
                "share": stat.get("share", 0),
                "reply": stat.get("reply", 0),
                "danmaku": stat.get("danmaku", 0),
                "tname": detail.get("tname") or item.get("tname") or item.get("typeid"),
                "author": detail.get("owner", {}).get("name"),
                "tag_names": "、".join(tag_names[:8]),
            }
        )

    emit("Fetching hot comment samples")
    raw_comment_records: list[dict[str, Any]] = []
    comments: list[dict[str, Any]] = []
    comment_candidates = sorted(
        videos,
        key=lambda row: (row.get("like", 0) + row.get("coin", 0) + row.get("favorite", 0) + row.get("share", 0) + row.get("reply", 0), row.get("view", 0)),
        reverse=True,
    )[: config.comment_video_count]

    for video in comment_candidates:
        payload = client.reply_main(int(video["aid"]), ps=config.comment_page_size)
        replies = payload.get("replies") or []
        for reply in replies:
            member = reply.get("member") or {}
            level_info = member.get("level_info") or {}
            vip = member.get("vip") or {}
            official = member.get("official_verify") or {}
            comments.append(
                {
                    "video_bvid": video["bvid"],
                    "video_title": video["title"],
                    "rpid": reply.get("rpid"),
                    "comment_like": reply.get("like", 0),
                    "comment_reply_count": reply.get("count", 0),
                    "member_mid": member.get("mid"),
                    "member_name": member.get("uname"),
                    "member_sex": member.get("sex"),
                    "member_level": level_info.get("current_level"),
                    "member_vip_status": vip.get("vipStatus"),
                    "member_official_type": official.get("type"),
                    "member_sign": member.get("sign"),
                    "comment_message": (reply.get("content") or {}).get("message"),
                }
            )
            raw_comment_records.append({"video_bvid": video["bvid"], "reply": reply})

    _write_json(exports.account_snapshot_json, account)
    _write_jsonl(exports.video_raw_jsonl, raw_video_records)
    _write_jsonl(exports.comment_raw_jsonl, raw_comment_records)
    _write_csv(exports.videos_csv, videos, VIDEO_HEADERS)
    _write_csv(exports.comments_csv, comments, COMMENT_HEADERS)
    _write_json(
        exports.summary_json,
        {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mid": target.mid,
            "account_name": account["acc_info"].get("name"),
            "space_url": target.space_url,
            "video_count": len(videos),
            "comment_sample_count": len(comments),
            "files": {
                "account_snapshot_json": str(exports.account_snapshot_json),
                "video_raw_jsonl": str(exports.video_raw_jsonl),
                "comment_raw_jsonl": str(exports.comment_raw_jsonl),
                "videos_csv": str(exports.videos_csv),
                "comments_csv": str(exports.comments_csv),
            },
        },
    )

    emit(f"Done: {exports.base_dir}")
    return CrawlResult(target, exports, account, videos, comments)
