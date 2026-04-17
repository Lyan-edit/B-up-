from bili_up_crawler.signing import enc_wbi


def test_enc_wbi_with_fixed_timestamp(monkeypatch) -> None:
    monkeypatch.setattr("time.time", lambda: 1710000000)
    result = enc_wbi(
        {"mid": 946974, "platform": "web"},
        "abcdef0123456789abcdef0123456789",
        "0123456789abcdef0123456789abcdef",
    )
    assert result["wts"] == "1710000000"
    assert result["w_rid"] == "d00cb46b04450c2f8a23c15630d9c58d"
