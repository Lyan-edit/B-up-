# bili_up_crawler

A standalone crawler for public Bilibili UP account data.

This repository only contains the crawler code extracted from a larger local project. It does not include thesis material, Word automation scripts, or report-generation logic tied to academic writing.

## Features

- Accept a Bilibili `MID` or space URL as input
- Bootstrap a browser context with Edge + Selenium
- Fetch account profile data
- Fetch recent formal videos from the UP space
- Fetch hot-comment proxy samples from top videos
- Export raw JSONL and structured CSV outputs

## Project Layout

```text
bili_up_crawler/
  src/bili_up_crawler/
    __init__.py
    __main__.py
    browser.py
    cli.py
    client.py
    config.py
    crawler.py
    signing.py
    targets.py
  tests/
  examples/
    sample_output/
  exports/
  LICENSE
  pyproject.toml
  README.md
```

## Installation

### Recommended

```bash
pip install -e .
```

### Minimal runtime dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Module entrypoint

After `pip install -e .`:

```bash
python -m bili_up_crawler --target 946974
python -m bili_up_crawler --target https://space.bilibili.com/546195 --video-limit 5 --comment-video-count 2
```

### Console script

After `pip install -e .`:

```bash
bili-up-crawler --target 946974
```

### Options

- `--target`: MID or Bilibili space URL
- `--video-limit`: number of recent videos to fetch
- `--comment-video-count`: how many videos to sample for hot comments
- `--comment-page-size`: how many hot comments to fetch per sampled video
- `--output-root`: export directory root
- `--show-browser`: disable headless mode and show Edge
- `--edge-binary`: explicit path to `msedge.exe`

## Output

Each run creates a new timestamped directory under `exports/`:

```text
exports/<account_name>_<timestamp>/
  raw/
    account_snapshot.json
    video_raw.jsonl
    comment_raw.jsonl
  processed/
    videos.csv
    comments.csv
  summary.json
```

## Example Output

See [`examples/`](./examples) for a small sample of exported files:

- [`examples/sample_output/summary.json`](./examples/sample_output/summary.json)
- [`examples/sample_output/videos.csv`](./examples/sample_output/videos.csv)
- [`examples/sample_output/comments.csv`](./examples/sample_output/comments.csv)

## Development

### Run tests

```bash
pytest -q
```

### Current test coverage

- target parsing
- WBI signing stability with a fixed timestamp
- crawler export flow with mocked client/browser dependencies
- disabled comment sampling behavior

## Notes and Limitations

- Hot comments are only a proxy sample and do not represent all followers.
- The crawler depends on a working Microsoft Edge installation.
- Some Bilibili endpoints may change over time.
- This repository intentionally excludes thesis-only code and content.

## License

This project is licensed under the [MIT License](./LICENSE).
