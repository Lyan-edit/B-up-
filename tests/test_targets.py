from bili_up_crawler.targets import parse_target


def test_parse_mid() -> None:
    parsed = parse_target("946974")
    assert parsed.mid == 946974
    assert parsed.space_url == "https://space.bilibili.com/946974"


def test_parse_space_url() -> None:
    parsed = parse_target("https://space.bilibili.com/546195/video")
    assert parsed.mid == 546195
    assert parsed.space_url == "https://space.bilibili.com/546195"
