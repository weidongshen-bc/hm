# 自然健美 AI · 私人训练站 MVP

本项目位于 `fitness-ai/`，独立于 hm 主项目；开发分支 `fitness-ai-private`。

## 安全
仅单用户账号密码登录，不开放注册；未登录无法读取训练数据。**不要将密码或 SESSION_SECRET 提交到仓库**。部署时配置环境变量 `ADMIN_USER`、`ADMIN_PASSWORD`（至少12字符）、`SESSION_SECRET`（至少32字符）和 `COOKIE_SECURE=true`，并启用 HTTPS。

## 启动
`pip install -r requirements.txt` 后设置环境变量，运行 `uvicorn main:app --host 0.0.0.0 --port 8000`。

当前为可运行的最小版本：登录、卧推历史数据、训练组记录、休息计时器。后续再接 PostgreSQL、AI 训练分析、ChatGPT 同步与正式云端部署。请勿把 SQLite 临时磁盘当作长期云端存储。
