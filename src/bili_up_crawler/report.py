from __future__ import annotations

from collections import Counter
from datetime import datetime
import html
import re
from statistics import median
from typing import Any

from .config import CrawlConfig
from .targets import ParsedTarget


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _format_number(value: int | None) -> str:
    if value is None:
        return "暂无"
    return f"{value:,}"


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "暂无"
    return f"{value:.2%}"


def _parse_pubdate(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _engagement_total(video: dict[str, Any]) -> int:
    return sum(
        _to_int(video.get(field))
        for field in ("like", "coin", "favorite", "share", "reply")
    )


def _engagement_rate(video: dict[str, Any]) -> float:
    view = _to_int(video.get("view"))
    if view <= 0:
        return 0.0
    return _engagement_total(video) / view


def _split_tags(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r"[、,，/|]+", text) if item.strip()]


def _top_tags(videos: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for video in videos:
        tags = _split_tags(video.get("tag_names"))
        if tags:
            counter.update(tags)
        elif video.get("tname"):
            counter.update([str(video["tname"]).strip()])
    return [{"tag": tag, "count": count} for tag, count in counter.most_common(limit)]


def _top_categories(videos: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for video in videos:
        label = str(video.get("tname") or "未分类").strip() or "未分类"
        counter.update([label])
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def _summarize_counter(counter: Counter[str], empty_text: str, limit: int = 5) -> str:
    total = sum(counter.values())
    if total <= 0:
        return empty_text
    parts = []
    for label, count in counter.most_common(limit):
        parts.append(f"{label} {count}（{count / total:.1%}）")
    return "；".join(parts)


def _build_comment_summary(comments: list[dict[str, Any]]) -> dict[str, Any]:
    if not comments:
        return {
            "count": 0,
            "sampled_video_count": 0,
            "gender_text": "未获取到评论代理样本。",
            "level_text": "未获取到评论代理样本。",
            "vip_text": "未获取到评论代理样本。",
        }

    gender_counter: Counter[str] = Counter()
    level_counter: Counter[str] = Counter()
    vip_counter: Counter[str] = Counter()
    sampled_videos: set[str] = set()

    for comment in comments:
        sampled_videos.add(str(comment.get("video_bvid") or "").strip())
        gender = str(comment.get("member_sex") or "").strip() or "未填写"
        gender_counter.update([gender])

        level = comment.get("member_level")
        level_label = f"Lv{level}" if level not in (None, "") else "未知等级"
        level_counter.update([level_label])

        vip_label = "大会员" if _to_int(comment.get("member_vip_status")) > 0 else "非大会员"
        vip_counter.update([vip_label])

    return {
        "count": len(comments),
        "sampled_video_count": len([item for item in sampled_videos if item]),
        "gender_text": _summarize_counter(gender_counter, "未获取到评论代理样本。"),
        "level_text": _summarize_counter(level_counter, "未获取到评论代理样本。"),
        "vip_text": _summarize_counter(vip_counter, "未获取到评论代理样本。"),
    }


def _build_case_videos(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not videos:
        return []

    ordered: list[dict[str, Any]] = []
    merged: dict[str, dict[str, Any]] = {}

    def add_case(case_label: str, video: dict[str, Any] | None) -> None:
        if not video:
            return
        key = str(video.get("bvid") or f"sample_{video.get('sample_index', len(ordered) + 1)}")
        if key not in merged:
            row = dict(video)
            row["case_types"] = [case_label]
            row["engagement_rate"] = _engagement_rate(video)
            merged[key] = row
            ordered.append(merged[key])
            return
        merged[key]["case_types"].append(case_label)

    add_case("高播放样本", max(videos, key=lambda row: (_to_int(row.get("view")), _engagement_total(row))))
    add_case("高互动样本", max(videos, key=lambda row: (_engagement_rate(row), _to_int(row.get("view")))))
    add_case(
        "最新样本",
        max(
            videos,
            key=lambda row: (
                _parse_pubdate(row.get("pubdate")) or datetime.min,
                _to_int(row.get("sample_index")),
            ),
        ),
    )

    cases: list[dict[str, Any]] = []
    for row in ordered:
        cases.append(
            {
                "case_type": " / ".join(row.pop("case_types")),
                "bvid": row.get("bvid") or "未知",
                "title": row.get("title") or "未命名视频",
                "pubdate": row.get("pubdate") or "暂无",
                "view": _to_int(row.get("view")),
                "like": _to_int(row.get("like")),
                "coin": _to_int(row.get("coin")),
                "favorite": _to_int(row.get("favorite")),
                "share": _to_int(row.get("share")),
                "reply": _to_int(row.get("reply")),
                "engagement_rate": row.get("engagement_rate", 0.0),
                "tname": row.get("tname") or "未分类",
                "tag_names": row.get("tag_names") or "暂无",
            }
        )
    return cases


def _build_observation_text(tags: list[dict[str, Any]], categories: list[dict[str, Any]]) -> str:
    tag_text = "、".join(item["tag"] for item in tags[:5]) if tags else ""
    category_text = "、".join(
        f"{item['name']}（{item['count']}）" for item in categories[:4]
    ) if categories else ""

    if tag_text and category_text:
        return f"样本内容主要围绕 {tag_text} 展开，分区上以 {category_text} 为主。"
    if tag_text:
        return f"从标签分布看，样本内容主要聚焦于 {tag_text}。"
    if category_text:
        return f"从分区分布看，样本内容主要集中在 {category_text}。"
    return "当前样本不足，暂时无法稳定概括账号的内容方向。"


def _build_writing_paragraphs(
    account_name: str,
    mid: int,
    generated_at: str,
    sample_scope: str,
    avg_view: int | None,
    median_view_value: int | None,
    avg_engagement_rate: float | None,
    highest_view_case: dict[str, Any] | None,
    observation_text: str,
    comment_summary: dict[str, Any],
) -> list[dict[str, str]]:
    object_paragraph = (
        f"本次观察对象为 B 站 UP 主 {account_name}（MID：{mid}）。"
        f"数据抓取时间为 {generated_at}，研究样本覆盖 {sample_scope}。"
        "本报告适合作为课程作业、案例分析或论文前期资料整理的初稿，正式写作前仍需结合人工复核。"
    )

    if avg_view is None:
        performance_paragraph = (
            "本次运行未能获取到足够的视频样本，因此暂时无法形成稳定的视频表现统计结论。"
            "建议在网络状态正常或提高抓取样本量后重新运行。"
        )
    else:
        highest_part = ""
        if highest_view_case:
            highest_part = (
                f"其中播放表现最突出的样本为《{highest_view_case['title']}》"
                f"（{highest_view_case['bvid']}），播放量约为 {_format_number(highest_view_case['view'])}。"
            )
        performance_paragraph = (
            f"从视频表现看，样本视频平均播放量为 {_format_number(avg_view)}，"
            f"中位播放量为 {_format_number(median_view_value)}，"
            f"平均综合互动率为 {_format_ratio(avg_engagement_rate)}。"
            f"{observation_text}{highest_part}"
        )

    if comment_summary["count"] <= 0:
        proxy_paragraph = (
            "本次运行未获取到热门评论代理样本，因此不能补充活跃评论用户的结构性观察。"
            "如需相关描述，可提高评论采样视频数或在评论开放的视频上重新抓取。"
        )
    else:
        proxy_paragraph = (
            f"在热门评论代理样本层面，本次共抓取 {comment_summary['count']} 条评论，"
            f"覆盖 {comment_summary['sampled_video_count']} 个样本视频。"
            f"性别结构表现为：{comment_summary['gender_text']}；"
            f"等级结构表现为：{comment_summary['level_text']}；"
            f"大会员结构表现为：{comment_summary['vip_text']}。"
            "需要强调的是，这部分结论仅对应活跃评论用户代理样本，不能直接外推为全体粉丝画像。"
        )

    return [
        {"title": "研究对象与样本", "text": object_paragraph},
        {"title": "视频表现分析", "text": performance_paragraph},
        {"title": "评论代理样本说明", "text": proxy_paragraph},
    ]


def build_academic_report_payload(
    account: dict[str, Any],
    videos: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    target: ParsedTarget,
    config: CrawlConfig,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now()
    acc_info = account.get("acc_info") or {}
    relation_stat = account.get("relation_stat") or {}

    account_name = str(acc_info.get("name") or f"mid_{target.mid}")
    fans = _to_int(relation_stat.get("follower"))
    following = _to_int(relation_stat.get("following") or relation_stat.get("attention"))
    official = acc_info.get("official") or acc_info.get("official_verify") or {}
    official_title = str(official.get("title") or official.get("desc") or "").strip()

    pubdates = [
        parsed
        for parsed in (_parse_pubdate(video.get("pubdate")) for video in videos)
        if parsed is not None
    ]
    views = [_to_int(video.get("view")) for video in videos]
    rates = [_engagement_rate(video) for video in videos if _to_int(video.get("view")) > 0]

    avg_view = round(sum(views) / len(views)) if views else None
    median_view_value = round(median(views)) if views else None
    avg_engagement_rate = sum(rates) / len(rates) if rates else None

    top_tags = _top_tags(videos)
    top_categories = _top_categories(videos)
    case_videos = _build_case_videos(videos)
    highest_view_case = max(case_videos, key=lambda row: row["view"]) if case_videos else None
    comment_summary = _build_comment_summary(comments)

    sample_scope = (
        f"近 {len(videos)} 期正式视频样本"
        if videos
        else "未获取到正式视频样本"
    )
    if config.comment_video_count > 0:
        sample_scope += (
            f"，并从互动较高的最多 {config.comment_video_count} 个视频中抓取"
            f" 每个视频最多 {config.comment_page_size} 条热门评论代理样本"
        )

    observation_text = _build_observation_text(top_tags, top_categories)
    writing_paragraphs = _build_writing_paragraphs(
        account_name=account_name,
        mid=target.mid,
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        sample_scope=sample_scope,
        avg_view=avg_view,
        median_view_value=median_view_value,
        avg_engagement_rate=avg_engagement_rate,
        highest_view_case=highest_view_case,
        observation_text=observation_text,
        comment_summary=comment_summary,
    )

    return {
        "report_title": f"{account_name} B站公开数据研究报告",
        "generated_at": generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "account_name": account_name,
        "mid": target.mid,
        "space_url": target.space_url,
        "sign": str(acc_info.get("sign") or "").strip(),
        "fans": fans,
        "following": following,
        "official_title": official_title,
        "video_count": len(videos),
        "comment_sample_count": len(comments),
        "sample_scope": sample_scope,
        "date_min": min(pubdates).strftime("%Y-%m-%d %H:%M:%S") if pubdates else "",
        "date_max": max(pubdates).strftime("%Y-%m-%d %H:%M:%S") if pubdates else "",
        "avg_view": avg_view,
        "median_view": median_view_value,
        "avg_engagement_rate": avg_engagement_rate,
        "top_tags": top_tags,
        "top_categories": top_categories,
        "content_direction_observation": observation_text,
        "case_videos": case_videos,
        "comment_summary": comment_summary,
        "method_notes": [
            "视频样本来自目标账号最近发布且未命中直播回放、预告、招募等过滤词的正式视频。",
            "评论部分抓取的是热门评论代理样本，仅反映活跃评论用户特征，不代表全体粉丝。",
            "本报告为单次抓取快照，平台接口、账号数据和评论热度会随时间变化。",
        ],
        "writing_notes": [
            "建议在论文或研究报告中注明抓取时间、样本量与接口公开性。",
            "建议将本报告中的“代理样本”表述保留，不要替换为“粉丝画像”或“受众总体结构”。",
            "如用于正式发表，请结合人工内容分析、交叉样本或补充访谈材料进行校正。",
        ],
        "writing_paragraphs": writing_paragraphs,
        "run_parameters": {
            "target": config.target,
            "video_limit": config.video_limit,
            "comment_video_count": config.comment_video_count,
            "comment_page_size": config.comment_page_size,
            "headless": config.headless,
        },
    }


def build_academic_report_markdown(payload: dict[str, Any]) -> str:
    tag_text = "、".join(item["tag"] for item in payload["top_tags"]) if payload["top_tags"] else "暂无"
    category_text = (
        "、".join(f"{item['name']}（{item['count']}）" for item in payload["top_categories"])
        if payload["top_categories"]
        else "暂无"
    )

    lines = [
        f"# {payload['report_title']}",
        "",
        "## 报告定位",
        "- 本报告适用于课程作业、案例研究、学术写作前期资料整理等场景。",
        "- 数据来源为 B 站公开可见账号信息、近期视频样本与热门评论代理样本。",
        "- 评论样本仅代表热门评论中的活跃评论用户代理样本，不代表全体粉丝。",
        "",
        "## 账号概况",
        f"- 账号名称：{payload['account_name']}",
        f"- MID：{payload['mid']}",
        f"- 空间链接：{payload['space_url']}",
        f"- 粉丝数：{_format_number(payload['fans'])}",
        f"- 关注数：{_format_number(payload['following'])}",
        f"- 账号签名：{payload['sign'] or '暂无'}",
        f"- 官方认证：{payload['official_title'] or '暂无'}",
        "",
        "## 样本与方法",
        f"- 抓取时间：{payload['generated_at']}",
        f"- 样本范围：{payload['sample_scope']}",
        f"- 视频时间范围：{payload['date_min'] or '暂无'} 至 {payload['date_max'] or '暂无'}",
    ]

    for note in payload["method_notes"]:
        lines.append(f"- 方法说明：{note}")

    lines.extend(
        [
            "",
            "## 视频表现统计",
            f"- 样本视频数：{payload['video_count']}",
            f"- 平均播放量：{_format_number(payload['avg_view'])}",
            f"- 中位播放量：{_format_number(payload['median_view'])}",
            f"- 平均综合互动率：{_format_ratio(payload['avg_engagement_rate'])}",
            f"- 高频标签：{tag_text}",
            f"- 高频分区：{category_text}",
            f"- 内容方向观察：{payload['content_direction_observation']}",
            "",
            "## 代表性视频案例",
        ]
    )

    if not payload["case_videos"]:
        lines.append("- 未获取到可分析的视频样本。")
    else:
        for item in payload["case_videos"]:
            lines.append(
                f"- {item['case_type']}：[{item['bvid']}] {item['title']}，发布时间 {item['pubdate']}，"
                f"播放 {_format_number(item['view'])}，点赞 {_format_number(item['like'])}，"
                f"投币 {_format_number(item['coin'])}，收藏 {_format_number(item['favorite'])}，"
                f"评论 {_format_number(item['reply'])}，综合互动率 {_format_ratio(item['engagement_rate'])}，"
                f"分区 {item['tname']}，标签 {item['tag_names']}。"
            )

    lines.extend(
        [
            "",
            "## 热门评论代理样本观察",
            f"- 评论样本数：{payload['comment_summary']['count']}",
            f"- 覆盖视频数：{payload['comment_summary']['sampled_video_count']}",
            f"- 性别结构：{payload['comment_summary']['gender_text']}",
            f"- 等级结构：{payload['comment_summary']['level_text']}",
            f"- 大会员结构：{payload['comment_summary']['vip_text']}",
            "- 解释边界：评论样本仅代表热门评论中的活跃评论用户代理样本，不代表全体粉丝。",
            "",
            "## 学术写作注意事项",
        ]
    )

    for note in payload["writing_notes"]:
        lines.append(f"- {note}")

    lines.extend(["", "## 学术写作参考段落"])
    for section in payload["writing_paragraphs"]:
        lines.extend(["", f"### {section['title']}", section["text"]])

    lines.extend(
        [
            "",
            "## 运行参数",
            f"- target：{payload['run_parameters']['target']}",
            f"- video_limit：{payload['run_parameters']['video_limit']}",
            f"- comment_video_count：{payload['run_parameters']['comment_video_count']}",
            f"- comment_page_size：{payload['run_parameters']['comment_page_size']}",
            f"- headless：{payload['run_parameters']['headless']}",
            "",
        ]
    )

    return "\n".join(lines)


def build_academic_report_html(payload: dict[str, Any]) -> str:
    def render_list(items: list[str]) -> str:
        return "".join(f"<li>{html.escape(item)}</li>" for item in items)

    tag_text = "、".join(item["tag"] for item in payload["top_tags"]) if payload["top_tags"] else "暂无"
    category_text = (
        "、".join(f"{item['name']}（{item['count']}）" for item in payload["top_categories"])
        if payload["top_categories"]
        else "暂无"
    )

    case_rows = []
    for item in payload["case_videos"]:
        case_rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_type'])}</td>"
            f"<td>{html.escape(item['bvid'])}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(item['pubdate'])}</td>"
            f"<td>{_format_number(item['view'])}</td>"
            f"<td>{_format_ratio(item['engagement_rate'])}</td>"
            f"<td>{html.escape(item['tname'])}</td>"
            "</tr>"
        )
    if not case_rows:
        case_table = "<p>未获取到可分析的视频样本。</p>"
    else:
        case_table = (
            "<table><thead><tr>"
            "<th>案例类型</th><th>BVID</th><th>标题</th><th>发布时间</th>"
            "<th>播放量</th><th>综合互动率</th><th>分区</th>"
            "</tr></thead><tbody>"
            + "".join(case_rows)
            + "</tbody></table>"
        )

    paragraph_html = "".join(
        f"<h3>{html.escape(section['title'])}</h3><p>{html.escape(section['text'])}</p>"
        for section in payload["writing_paragraphs"]
    )

    method_items = [
        f"抓取时间：{payload['generated_at']}",
        f"样本范围：{payload['sample_scope']}",
        f"视频时间范围：{payload['date_min'] or '暂无'} 至 {payload['date_max'] or '暂无'}",
        *payload["method_notes"],
    ]
    writing_items = payload["writing_notes"]
    parameter_items = [
        f"target：{payload['run_parameters']['target']}",
        f"video_limit：{payload['run_parameters']['video_limit']}",
        f"comment_video_count：{payload['run_parameters']['comment_video_count']}",
        f"comment_page_size：{payload['run_parameters']['comment_page_size']}",
        f"headless：{payload['run_parameters']['headless']}",
    ]

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(payload['report_title'])}</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --card: #fffdfa;
      --text: #23313f;
      --muted: #5d6773;
      --accent: #0f766e;
      --line: #e5dbc9;
    }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      background: linear-gradient(180deg, #efe7d8 0%, #f8f4ec 100%);
      color: var(--text);
    }}
    main {{
      max-width: 980px;
      margin: 0 auto;
      padding: 28px 18px 52px;
    }}
    section {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 22px;
      margin-bottom: 18px;
      box-shadow: 0 12px 28px rgba(35, 49, 63, 0.06);
    }}
    h1, h2, h3 {{
      margin-top: 0;
    }}
    p, li {{
      color: var(--muted);
      line-height: 1.72;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .meta-card {{
      background: #eef8f6;
      border-radius: 14px;
      padding: 14px 16px;
    }}
    .meta-card span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
    }}
    .meta-card strong {{
      display: block;
      color: var(--accent);
      font-size: 24px;
      margin-top: 8px;
    }}
    ul {{
      padding-left: 18px;
      margin: 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: white;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 10px 12px;
      font-size: 14px;
    }}
    code {{
      padding: 2px 6px;
      border-radius: 8px;
      background: #eef8f6;
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>{html.escape(payload['report_title'])}</h1>
      <p>本报告基于 B 站公开数据接口生成，面向课程作业、案例研究与学术写作前期资料整理使用。评论样本仅代表热门评论中的活跃评论用户代理样本，不代表全体粉丝。</p>
      <div class="meta">
        <div class="meta-card"><span>粉丝数</span><strong>{_format_number(payload['fans'])}</strong></div>
        <div class="meta-card"><span>关注数</span><strong>{_format_number(payload['following'])}</strong></div>
        <div class="meta-card"><span>样本视频数</span><strong>{payload['video_count']}</strong></div>
        <div class="meta-card"><span>评论样本数</span><strong>{payload['comment_sample_count']}</strong></div>
      </div>
    </section>

    <section>
      <h2>账号概况</h2>
      <ul>
        <li>账号名称：{html.escape(payload['account_name'])}</li>
        <li>MID：{payload['mid']}</li>
        <li>空间链接：{html.escape(payload['space_url'])}</li>
        <li>账号签名：{html.escape(payload['sign'] or '暂无')}</li>
        <li>官方认证：{html.escape(payload['official_title'] or '暂无')}</li>
      </ul>
    </section>

    <section>
      <h2>样本与方法</h2>
      <ul>{render_list(method_items)}</ul>
    </section>

    <section>
      <h2>视频表现统计</h2>
      <ul>
        <li>平均播放量：{_format_number(payload['avg_view'])}</li>
        <li>中位播放量：{_format_number(payload['median_view'])}</li>
        <li>平均综合互动率：{_format_ratio(payload['avg_engagement_rate'])}</li>
        <li>高频标签：{html.escape(tag_text)}</li>
        <li>高频分区：{html.escape(category_text)}</li>
        <li>内容方向观察：{html.escape(payload['content_direction_observation'])}</li>
      </ul>
    </section>

    <section>
      <h2>代表性视频案例</h2>
      {case_table}
    </section>

    <section>
      <h2>热门评论代理样本观察</h2>
      <ul>
        <li>评论样本数：{payload['comment_summary']['count']}</li>
        <li>覆盖视频数：{payload['comment_summary']['sampled_video_count']}</li>
        <li>性别结构：{html.escape(payload['comment_summary']['gender_text'])}</li>
        <li>等级结构：{html.escape(payload['comment_summary']['level_text'])}</li>
        <li>大会员结构：{html.escape(payload['comment_summary']['vip_text'])}</li>
        <li>解释边界：评论样本仅代表热门评论中的活跃评论用户代理样本，不代表全体粉丝。</li>
      </ul>
    </section>

    <section>
      <h2>学术写作注意事项</h2>
      <ul>{render_list(writing_items)}</ul>
    </section>

    <section>
      <h2>学术写作参考段落</h2>
      {paragraph_html}
    </section>

    <section>
      <h2>运行参数</h2>
      <ul>{render_list(parameter_items)}</ul>
    </section>
  </main>
</body>
</html>
"""
