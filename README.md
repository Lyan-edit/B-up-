# bili_up_crawler

这是从原项目里单独摘出来的“B 站 UP 抓取代码”版本，只保留爬虫能力，不包含论文材料、论文脚本、分析面板和论文专用文案。

## 功能

- 输入 `MID` 或 B 站空间链接
- 自动启动 Edge + Selenium 获取 WBI / 风控参数
- 抓取账号概况
- 抓取最近 N 期正式视频
- 抓取热门评论代理样本
- 导出原始 JSONL 和结构化 CSV

## 目录

| 文件 | 说明 |
| --- | --- |
| `config.py` | 抓取参数配置 |
| `targets.py` | 目标账号解析 |
| `signing.py` | WBI 签名 |
| `browser.py` | Edge 上下文引导 |
| `client.py` | B 站接口客户端 |
| `crawler.py` | 主抓取逻辑与导出 |
| `cli.py` | 命令行入口 |

## 安装依赖

```bash
pip install requests selenium
```

## 使用

```bash
python -m bili_up_crawler --target 946974
python -m bili_up_crawler --target https://space.bilibili.com/546195 --video-limit 5 --comment-video-count 2
```

## 输出

每次运行会在 `exports/<账号名>_<时间戳>/` 下生成：

- `raw/account_snapshot.json`
- `raw/video_raw.jsonl`
- `raw/comment_raw.jsonl`
- `processed/videos.csv`
- `processed/comments.csv`
- `summary.json`

## 说明

- 评论样本来自热门评论，不代表全体粉丝。
- 只保留抓取代码，不包含论文内容和论文导出逻辑。
- 如果要公开上传 GitHub，推荐只上传这个目录。
