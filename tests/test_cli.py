from __future__ import annotations

from bili_up_crawler import cli


def test_cli_without_target_uses_interactive(monkeypatch) -> None:
    called: dict[str, bool] = {"interactive": False}

    def fake_interactive_main() -> int:
        called["interactive"] = True
        return 0

    monkeypatch.setattr(cli, "interactive_main", fake_interactive_main)

    exit_code = cli.main([])

    assert exit_code == 0
    assert called["interactive"] is True
