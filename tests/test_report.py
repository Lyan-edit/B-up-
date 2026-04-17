from __future__ import annotations

from datetime import datetime

from bili_up_crawler.config import CrawlConfig
from bili_up_crawler.report import (
    build_academic_report_html,
    build_academic_report_markdown,
    build_academic_report_payload,
)
from bili_up_crawler.targets import parse_target


def test_report_builders_handle_empty_samples() -> None:
    payload = build_academic_report_payload(
        account={
            "acc_info": {"name": "空样本账号", "sign": ""},
            "relation_stat": {"follower": 0, "following": 0},
        },
        videos=[],
        comments=[],
        target=parse_target("946974"),
        config=CrawlConfig(target="946974", video_limit=1, comment_video_count=0),
        generated_at=datetime(2026, 4, 17, 13, 30, 0),
    )

    markdown = build_academic_report_markdown(payload)
    html = build_academic_report_html(payload)

    assert "未获取到正式视频样本" in markdown
    assert "评论样本仅代表热门评论中的活跃评论用户代理样本，不代表全体粉丝。" in markdown
    assert "学术写作参考段落" in markdown
    assert "<html" in html.lower()
    assert "空样本账号" in html
