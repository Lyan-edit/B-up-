from __future__ import annotations

from pathlib import Path
from typing import Callable

from .config import CrawlConfig
from .crawler import crawl_up
from .targets import parse_target


InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


def _prompt_target(input_fn: InputFn, output_fn: OutputFn) -> str:
    output_fn("请输入 B 站 UP 的空间链接、MID 或 UID。")
    output_fn("示例：https://space.bilibili.com/946974  或  946974")
    while True:
        value = input_fn("目标 UP：").strip()
        try:
            parsed = parse_target(value)
        except ValueError:
            output_fn("输入无法识别，请重新输入有效的空间链接或纯数字 UID。")
            continue
        output_fn(f"已识别 MID：{parsed.mid}")
        return value


def _prompt_int(
    input_fn: InputFn,
    output_fn: OutputFn,
    label: str,
    default: int,
    minimum: int = 0,
) -> int:
    while True:
        raw = input_fn(f"{label} [{default}]：").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            output_fn("请输入整数。")
            continue
        if value < minimum:
            output_fn(f"请输入不小于 {minimum} 的整数。")
            continue
        return value


def _prompt_yes_no(
    input_fn: InputFn,
    output_fn: OutputFn,
    label: str,
    default: bool,
) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input_fn(f"{label} [{suffix}]：").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes", "1"}:
            return True
        if raw in {"n", "no", "0"}:
            return False
        output_fn("请输入 y 或 n。")


def build_interactive_config(
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> CrawlConfig:
    output_fn("")
    output_fn("=== B 站 UP 一键抓取 ===")
    output_fn("")
    target = _prompt_target(input_fn, output_fn)
    video_limit = _prompt_int(input_fn, output_fn, "抓取最近多少期正式视频", 30, minimum=1)
    comment_video_count = _prompt_int(input_fn, output_fn, "采样多少个视频抓热门评论", 10, minimum=0)
    comment_page_size = _prompt_int(input_fn, output_fn, "每个视频抓多少条热门评论", 30, minimum=1)
    show_browser = _prompt_yes_no(input_fn, output_fn, "是否显示浏览器窗口", default=False)

    output_root_text = input_fn("导出目录 [exports]：").strip()
    output_root = Path(output_root_text) if output_root_text else Path.cwd() / "exports"

    return CrawlConfig(
        target=target,
        video_limit=video_limit,
        comment_video_count=comment_video_count,
        comment_page_size=comment_page_size,
        output_root=output_root,
        headless=not show_browser,
        edge_binary=None,
    )


def main() -> int:
    try:
        config = build_interactive_config()
        print("")
        print("开始抓取，请稍候...")
        result = crawl_up(config, progress=lambda message: print(f"[bili_up_crawler] {message}"))
    except KeyboardInterrupt:
        print("")
        print("已取消。")
        return 130
    except Exception as exc:
        print("")
        print(f"运行失败：{exc}")
        return 1

    print("")
    print("抓取完成。")
    print(f"导出目录：{result.exports.base_dir}")
    print(f"视频表：{result.exports.videos_csv}")
    print(f"评论表：{result.exports.comments_csv}")
    print(f"学术报告 Markdown：{result.exports.academic_report_md}")
    print(f"学术报告 HTML：{result.exports.academic_report_html}")
    print(f"摘要文件：{result.exports.summary_json}")
    return 0
