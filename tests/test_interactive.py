from __future__ import annotations

from pathlib import Path

from bili_up_crawler.interactive import build_interactive_config


def test_build_interactive_config_uses_defaults(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    answers = iter([
        "https://space.bilibili.com/946974",
        "",
        "",
        "",
        "",
        "",
    ])
    outputs: list[str] = []

    config = build_interactive_config(
        input_fn=lambda prompt: next(answers),
        output_fn=outputs.append,
    )

    assert config.target == "https://space.bilibili.com/946974"
    assert config.video_limit == 30
    assert config.comment_video_count == 10
    assert config.comment_page_size == 30
    assert config.headless is True
    assert config.output_root == Path.cwd() / "exports"


def test_build_interactive_config_accepts_custom_values(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    answers = iter([
        "946974",
        "5",
        "2",
        "8",
        "y",
        str(tmp_path / "custom_exports"),
    ])

    config = build_interactive_config(
        input_fn=lambda prompt: next(answers),
        output_fn=lambda message: None,
    )

    assert config.target == "946974"
    assert config.video_limit == 5
    assert config.comment_video_count == 2
    assert config.comment_page_size == 8
    assert config.headless is False
    assert config.output_root == tmp_path / "custom_exports"
