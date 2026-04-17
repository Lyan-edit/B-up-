from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXPORT_ROOT = Path.cwd() / "exports"


@dataclass(slots=True)
class CrawlConfig:
    target: str
    video_limit: int = 30
    comment_video_count: int = 10
    comment_page_size: int = 30
    output_root: Path = DEFAULT_EXPORT_ROOT
    headless: bool = True
    edge_binary: str | None = None

    def __post_init__(self) -> None:
        self.target = str(self.target).strip()
        self.video_limit = max(1, int(self.video_limit))
        self.comment_video_count = max(0, min(int(self.comment_video_count), self.video_limit))
        self.comment_page_size = max(1, int(self.comment_page_size))
        self.output_root = Path(self.output_root)
