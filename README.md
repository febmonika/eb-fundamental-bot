# 苯乙烯基本面研究员 — 钉钉机器人

每日自动推送 EB 行情、持仓、上下游基本面到钉钉群。

## 定时推送

| 时间 (北京时间) | 内容 |
|---|---|
| 08:40 | 盘前速报 |
| 15:15 | 收盘日报 |
| 23:05 | 夜盘小结 |
| 周五 16:00 | 周度复盘 |

## 部署

1. 在 GitHub Settings → Secrets → Actions 添加 DINGTALK_WEBHOOK
2. GitHub Actions 自动按 cron 运行
3. 也可手动触发: Actions → EB Fundamental Bot → Run workflow
