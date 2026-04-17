# bili_up_crawler

一个独立的 B 站 UP 公开数据爬虫项目，支持抓取账号信息、近期正式视频、热门评论代理样本，并自动导出适合课程作业、案例分析、论文前期资料整理使用的学术写作导向报告。

这个仓库只保留通用爬取与报告代码，不包含论文正文、章节素材、Word 自动化脚本或其它私有研究资料。

## 功能概览

- 输入 `MID` 或 B 站空间链接即可抓取
- 使用 Edge + Selenium 建立浏览器上下文，兼容 B 站公开接口请求
- 导出账号快照、视频原始数据、评论原始数据
- 导出结构化 `CSV / JSON`
- 自动生成 `academic_report.md` 和 `academic_report.html`
- 报告内置样本说明、代理样本免责声明、代表性视频案例、可直接改写的学术写作参考段落

## 项目结构

```text
bili_up_crawler/
  src/bili_up_crawler/
    __init__.py
    __main__.py
    browser.py
    cli.py
    interactive.py
    client.py
    config.py
    crawler.py
    report.py
    signing.py
    targets.py
  start_crawler.bat
  tests/
  examples/
    sample_output/
  exports/
  LICENSE
  pyproject.toml
  README.md
```

## 环境要求

- Python `3.11+`
- 已安装 Microsoft Edge
- 本机可正常访问 B 站公开页面与接口

## 安装

### 推荐方式

```bash
pip install -e .
```

### 仅安装运行依赖

```bash
pip install -r requirements.txt
```

## 快速开始

安装完成后，直接执行：

```bash
python -m bili_up_crawler --target 946974
```

如果你更希望直接双击启动，在 Windows 下可以运行仓库根目录的：

```text
start_crawler.bat
```

双击后会自动提示你输入：

- UP 空间链接 / MID / UID
- 视频抓取数
- 评论采样视频数
- 每个视频抓取的热门评论数
- 是否显示浏览器窗口
- 导出目录

也可以输入空间链接：

```bash
python -m bili_up_crawler --target https://space.bilibili.com/546195
```

如果已经用 `pip install -e .` 安装过命令行入口，也可以这样运行：

```bash
bili-up-crawler --target 946974
```

或者进入交互模式：

```bash
bili-up-crawler --interactive
```

## 常用命令示例

抓取近 5 个视频，并从互动较高的 2 个视频里各取最多 10 条热门评论：

```bash
python -m bili_up_crawler --target 946974 --video-limit 5 --comment-video-count 2 --comment-page-size 10
```

显示 Edge 浏览器窗口，方便排查登录态或页面异常：

```bash
python -m bili_up_crawler --target 946974 --show-browser
```

指定自定义导出目录：

```bash
python -m bili_up_crawler --target 946974 --output-root E:\data\bili_exports
```

指定 Edge 可执行文件：

```bash
python -m bili_up_crawler --target 946974 --edge-binary "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

## 参数说明

- `--target`
  - 必填
  - 支持 `MID` 或空间链接
- `--video-limit`
  - 抓取最近多少期正式视频
  - 默认 `30`
- `--comment-video-count`
  - 选取多少个互动较高的视频抓热门评论
  - 默认 `10`
- `--comment-page-size`
  - 每个采样视频抓取多少条热门评论
  - 默认 `30`
- `--output-root`
  - 导出根目录
  - 默认当前目录下的 `exports/`
- `--show-browser`
  - 默认无头模式
  - 加上此参数后显示 Edge 窗口
- `--edge-binary`
  - 手动指定 `msedge.exe` 路径

## 输出内容

每次运行都会创建一个新的时间戳目录：

```text
exports/<账号名>_<时间戳>/
  raw/
    account_snapshot.json
    video_raw.jsonl
    comment_raw.jsonl
  processed/
    videos.csv
    comments.csv
  reports/
    academic_report.md
    academic_report.html
  summary.json
```

### 文件说明

- `raw/account_snapshot.json`
  - 账号基础信息和粉丝/关注统计原始快照
- `raw/video_raw.jsonl`
  - 每个视频的原始接口结果与标签数据
- `raw/comment_raw.jsonl`
  - 热门评论原始返回
- `processed/videos.csv`
  - 视频指标表，适合继续做 Excel / pandas 分析
- `processed/comments.csv`
  - 评论代理样本表
- `reports/academic_report.md`
  - Markdown 版研究报告
- `reports/academic_report.html`
  - 可直接在浏览器里打开的 HTML 版研究报告
- `summary.json`
  - 运行摘要与导出文件索引

## 学术写作导向报告说明

自动生成的报告不是论文正文，而是“可直接改写的研究素材”。默认包含以下部分：

- 报告定位
- 账号概况
- 样本与方法
- 视频表现统计
- 代表性视频案例
- 热门评论代理样本观察
- 学术写作注意事项
- 学术写作参考段落
- 运行参数

### 报告适合用来做什么

- 课程论文前期材料整理
- 研究报告中的案例账号描述
- 某个 UP 主内容方向和传播表现的初步观察
- 给人工写作者提供第一版结构化草稿

### 报告不会替你做什么

- 不会替代正式论文写作
- 不会自动做严谨的因果分析
- 不会把热门评论样本等同于全体粉丝
- 不会生成任何论文私有章节内容

## 操作手册

### 1. 准备环境

1. 安装 Python 3.11 及以上版本。
2. 确认本机装有 Microsoft Edge。
3. 进入仓库目录执行 `pip install -e .`。

### 2. 运行抓取

1. 找到目标 UP 的 `MID` 或空间链接。
2. 执行命令，例如：

```bash
python -m bili_up_crawler --target 946974 --video-limit 10 --comment-video-count 3 --comment-page-size 10
```

3. 等待终端输出导出目录路径。

如果你不想敲命令，也可以直接双击 `start_crawler.bat`，然后按照界面提示输入 URL 或 UID。

### 3. 查看结果

1. 先打开 `summary.json`，确认本次实际导出的文件位置。
2. 用表格软件查看 `processed/videos.csv` 和 `processed/comments.csv`。
3. 直接打开 `reports/academic_report.html` 浏览完整报告。
4. 如果要复制到 Markdown 文档或笔记软件，使用 `reports/academic_report.md`。

### 4. 写作时建议这样用

1. 从“账号概况”和“样本与方法”部分直接整理研究对象说明。
2. 从“视频表现统计”和“代表性视频案例”中提取数据支撑。
3. 从“学术写作参考段落”里挑选适合的句子做人工改写。
4. 保留“代理样本”表述，不要把评论样本直接写成整体粉丝画像。
5. 正式提交前补充人工复核、交叉样本或其它研究材料。

## 示例输出

示例文件位于 [`examples/`](./examples)：

- [`examples/sample_output/summary.json`](./examples/sample_output/summary.json)
- [`examples/sample_output/videos.csv`](./examples/sample_output/videos.csv)
- [`examples/sample_output/comments.csv`](./examples/sample_output/comments.csv)
- [`examples/sample_output/academic_report.md`](./examples/sample_output/academic_report.md)
- [`examples/sample_output/academic_report.html`](./examples/sample_output/academic_report.html)

## 作为库调用

如果你希望在自己的 Python 项目里复用：

```python
from pathlib import Path

from bili_up_crawler import CrawlConfig, crawl_up

result = crawl_up(
    CrawlConfig(
        target="946974",
        video_limit=5,
        comment_video_count=2,
        comment_page_size=10,
        output_root=Path("exports"),
    )
)

print(result.exports.academic_report_md)
print(result.exports.academic_report_html)
```

## 测试

运行测试：

```bash
pytest -q
```

当前测试覆盖：

- `MID / 空间链接` 解析
- WBI 签名稳定性
- 爬虫导出链路
- CLI 无参数时自动进入交互模式
- 交互模式默认值与自定义输入
- 评论抓取关闭场景
- 学术报告生成在空样本场景下不崩溃

## 注意事项与局限

- 评论样本仅是热门评论代理样本，不代表全部粉丝。
- B 站接口、签名机制和页面参数可能随时间变化。
- Edge / Selenium 环境异常会导致初始化失败。
- 某些视频可能关闭评论或接口返回空数据，报告会降级生成。

## License

本项目采用 [MIT License](./LICENSE)。
