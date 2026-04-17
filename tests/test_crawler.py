from __future__ import annotations

import json

from bili_up_crawler.config import CrawlConfig
from bili_up_crawler.crawler import crawl_up


class FakeClient:
    def __init__(self, mid: int, context) -> None:
        self.mid = mid

    def acc_info(self) -> dict:
        return {
            "mid": self.mid,
            "name": "测试账号",
            "sign": "测试签名",
        }

    def relation_stat(self) -> dict:
        return {
            "follower": 12345,
            "following": 67,
        }

    def arc_search(self, pn: int, ps: int = 20) -> dict:
        if pn > 1:
            return {"list": {"vlist": []}}
        return {
            "list": {
                "vlist": [
                    {"bvid": "BVTEST001", "title": "测试视频", "description": "测试描述", "tname": "科技"}
                ]
            }
        }

    def view(self, bvid: str) -> dict:
        return {
            "bvid": bvid,
            "aid": 1001,
            "title": "测试视频",
            "desc": "测试描述",
            "pubdate": 1710000000,
            "duration": 600,
            "tname": "科技",
            "owner": {"name": "测试账号"},
            "stat": {
                "view": 9999,
                "like": 500,
                "coin": 30,
                "favorite": 20,
                "share": 10,
                "reply": 5,
                "danmaku": 8,
            },
        }

    def archive_tags(self, aid: int) -> list[dict]:
        return [{"tag_name": "科技"}, {"tag_name": "数码"}]

    def reply_main(self, aid: int, ps: int) -> dict:
        return {
            "replies": [
                {
                    "rpid": 1,
                    "like": 2,
                    "count": 0,
                    "member": {
                        "mid": 2001,
                        "uname": "评论用户",
                        "sex": "男",
                        "sign": "hello",
                        "level_info": {"current_level": 5},
                        "vip": {"vipStatus": 1},
                        "official_verify": {"type": -1},
                    },
                    "content": {"message": "测试评论"},
                }
            ]
        }


def test_crawl_up_exports_expected_files(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("bili_up_crawler.crawler.bootstrap_browser_context", lambda *args, **kwargs: object())
    monkeypatch.setattr("bili_up_crawler.crawler.BiliClient", FakeClient)

    config = CrawlConfig(
        target="946974",
        video_limit=1,
        comment_video_count=1,
        comment_page_size=1,
        output_root=tmp_path,
    )
    result = crawl_up(config)

    assert result.target.mid == 946974
    assert len(result.videos) == 1
    assert len(result.comments) == 1
    assert result.exports.videos_csv.exists()
    assert result.exports.comments_csv.exists()
    assert result.exports.academic_report_md.exists()
    assert result.exports.academic_report_html.exists()
    assert result.exports.summary_json.exists()

    summary = json.loads(result.exports.summary_json.read_text(encoding="utf-8"))
    assert summary["account_name"] == "测试账号"
    assert summary["video_count"] == 1
    assert summary["comment_sample_count"] == 1
    assert summary["files"]["academic_report_md"] == "reports/academic_report.md"
    assert summary["files"]["academic_report_html"] == "reports/academic_report.html"

    report_text = result.exports.academic_report_md.read_text(encoding="utf-8")
    assert "学术写作参考段落" in report_text
    assert "评论样本仅代表热门评论中的活跃评论用户代理样本，不代表全体粉丝。" in report_text


def test_crawl_up_skips_comment_fetch_when_disabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("bili_up_crawler.crawler.bootstrap_browser_context", lambda *args, **kwargs: object())
    monkeypatch.setattr("bili_up_crawler.crawler.BiliClient", FakeClient)

    config = CrawlConfig(
        target="946974",
        video_limit=1,
        comment_video_count=0,
        comment_page_size=1,
        output_root=tmp_path,
    )
    result = crawl_up(config)

    assert len(result.videos) == 1
    assert len(result.comments) == 0
