# deal-radar

[![CI](https://github.com/brianwang/deal-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/brianwang/deal-radar/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/python-3.11+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

> AI 接单助手：聚合需求、智能打分、生成投标信。**半自动，人工审核后发送。**

做独立接单的人，大部分时间耗在两件事上：在多个平台之间翻找跟自己匹配的需求，以及给每条需求重复写投标信。deal-radar 把这两步自动化，但**保留最后的人工判断**——不自动投标、不自动发消息，既合规，也避免群发垃圾。

## 它做什么

1. **聚合需求** — 从 RSS 源导入，或手动粘贴任意平台的需求
2. **AI 打分** — 按你的技能画像给每条需求打 0-100 分，并给出理由和风险
3. **生成投标信** — 根据具体需求生成可直接发送的中文 proposal 草稿
4. **状态看板** — 跟踪 draft / sent / replied / won / lost，避免漏跟进

## 明确不做

- 不自动登录、不自动发消息、不绕过平台验证
- 不批量骚扰、不多账号
- 这些既违反平台规则，转化率也极低

## 快速开始

```bash
# 1. 安装
uv sync

# 2. 配置（默认走本机 Ollama 的 OpenAI 兼容接口）
cp .env.example .env
# 编辑 .env，填入你的 LLM 地址、key、模型、技能画像

# 3. 启动 Web 看板
uv run uvicorn deal_radar.web.app:app --reload --port 8000
# 打开 http://127.0.0.1:8000
```

也可以纯命令行用：

```bash
uv run deal-radar add --title "做一个 RAG 知识库" --desc "需要把 PDF 文档做成问答机器人" --budget "2-3 万"
uv run deal-radar list
uv run deal-radar score 1
uv run deal-radar proposal 1
```

## 配置项

| 变量 | 说明 | 默认 |
|---|---|---|
| `LLM_BASE_URL` | OpenAI 兼容接口地址 | `http://localhost:11434/v1` |
| `LLM_API_KEY` | API key（Ollama 填 `ollama` 即可） | `ollama` |
| `LLM_MODEL` | 模型名 | `deepseek-v4.1-flash:cloud` |
| `DEAL_RADAR_DB` | SQLite 路径 | `data/deal_radar.db` |
| `SKILL_PROFILE` | 你的技能画像，打分用的上下文 | 见 `.env.example` |

## 路线图

- [x] v0.1 需求导入（RSS / 手动）、AI 打分、投标信生成、状态看板
- [ ] v0.2 定时抓取多个 RSS 源，去重入库
- [ ] v0.3 Playwright 抓取需要登录的平台（Upwork / Freelancer）
- [ ] v0.4 案例库：把过往项目写成结构化案例，投标信自动引用
- [ ] v0.5 英文 proposal，面向海外平台
- [ ] v1.0 多用户 / 部署

## 技术栈

Python 3.11+ · FastAPI · SQLite · Jinja2 · 任意 OpenAI 兼容 LLM

## License

MIT
