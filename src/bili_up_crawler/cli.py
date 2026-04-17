from __future__ import annotations

import argparse
from pathlib import Path

from .config import CrawlConfig
from .crawler import crawl_up


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone Bilibili UP crawler")
    parser.add_argument("--target", required=True, help="MID or Bilibili space URL")
    parser.add_argument("--video-limit", type=int, default=30, help="Number of recent videos to fetch")
    parser.add_argument("--comment-video-count", type=int, default=10, help="How many videos to sample for hot comments")
    parser.add_argument("--comment-page-size", type=int, default=30, help="How many hot comments to fetch per sampled video")
    parser.add_argument("--output-root", default=str(Path.cwd() / "exports"), help="Export root")
    parser.add_argument("--show-browser", action="store_true", help="Show Edge instead of running headless")
    parser.add_argument("--edge-binary", default=None, help="Optional explicit path to msedge.exe")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = CrawlConfig(
        target=args.target,
        video_limit=args.video_limit,
        comment_video_count=args.comment_video_count,
        comment_page_size=args.comment_page_size,
        output_root=Path(args.output_root),
        headless=not args.show_browser,
        edge_binary=args.edge_binary,
    )
    result = crawl_up(config, progress=lambda message: print(f"[bili_up_crawler] {message}"))
    print(f"Export directory: {result.exports.base_dir}")
    print(f"Videos CSV: {result.exports.videos_csv}")
    print(f"Comments CSV: {result.exports.comments_csv}")
    print(f"Summary JSON: {result.exports.summary_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
