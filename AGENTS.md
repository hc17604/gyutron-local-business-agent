# AGENTS.md

本文件是 GyuTron Local Agent 的长期开发指令，适用于 Codex、Claude Code 和其他 AI 编程 Agent。

## 1. 硬性约束

1. 不允许把任何项目文件、文档、代码、数据库、上传数据、生成物放在 C 盘。
2. 项目必须放在非 C 盘路径，例如 `D:\Codex`，或放进明确指定的 GitHub 仓库。
3. 所有工作成果物必须提交到 GitHub。
4. 不要把产品做成默认云端 SaaS。
5. 不要默认上传客户业务数据到 GyuTron 云端。
6. 不要一开始接 Alibaba、Shopee、Amazon、TikTok Shop 等平台 API。
7. 第一版只读数据，不自动发邮件，不自动修改平台数据，不自动执行高风险动作。
8. 不要硬编码 API Key。
9. 不要在日志、报告快照或错误信息中打印完整 API Key。
10. 不要把完整原始大表直接发送给 LLM，必须先做结构化摘要。

## 2. 产品定位

GyuTron Local Agent 是面向跨境制造企业、跨境电商企业、工业品外贸公司的本地业务自动化 AI Agent。

它不是：

- 普通数据看板。
- SaaS 云平台。
- 简单聊天机器人。
- 通用开发者工具。
- 复杂工作流搭建平台。

第一版只做本地老板日报 Agent。

## 3. MVP 范围

MVP 包含：

- 本地 Web 控制台。
- Excel/CSV 上传。
- 字段自动猜测。
- 用户手动字段映射。
- SQLite 本地存储。
- OpenAI-compatible 模型配置。
- 自然语言业务规则。
- 老板日报生成。
- 历史报告查看。

MVP 不包含：

- 平台 API。
- 多租户。
- 复杂权限。
- 自动通知。
- 自动修改业务系统数据。

## 4. 技术栈

- Frontend: React + Vite + TypeScript
- Backend: Python FastAPI
- Database: SQLite
- File parsing: pandas + openpyxl
- Deployment: Docker Compose
- Local storage:
  - `data/uploads`
  - `data/reports`
  - `data/db`

## 5. 推荐目录

```text
apps/
  api/
    app/
      main.py
      config.py
      database.py
      models/
      schemas/
      routers/
      services/
      parsers/
      llm/
      report/
    tests/
    requirements.txt
    Dockerfile
  web/
    src/
      pages/
      components/
      api/
      types/
    package.json
    Dockerfile
data/
  uploads/
  reports/
  db/
docs/
  PRD.md
  ARCHITECTURE.md
  API.md
  MVP_ROADMAP.md
docker-compose.yml
README.md
AGENTS.md
```

## 6. 后端规则

- 路由放在 `routers/`。
- 业务逻辑放在 `services/`。
- 文件解析放在 `parsers/`。
- 模型调用放在 `llm/`。
- 报告生成放在 `report/`。
- 不要把复杂业务逻辑直接写在 `main.py`。
- 所有本地目录由启动流程自动创建。

## 7. 前端规则

- 首页直接进入工作台，不做营销落地页。
- UI 面向老板和业务负责人。
- 涉及外部模型调用时，必须提示会把摘要发送到用户配置的模型服务商。
- 第一阶段页面只需清晰展示服务状态和后续功能入口。

## 8. 报告质量要求

老板日报必须包含：

- 老板摘要。
- 核心数据变化。
- 异常提醒。
- 高优先级客户。
- 产品机会。
- 国家/市场趋势。
- 销售跟进任务。
- 风险点。
- 下一步建议。

报告必须中文输出，不编造数据，不把建议伪装成事实。

## 9. 开发顺序

1. 0.1 项目能启动。
2. 0.2 文件上传和预览。
3. 0.3 字段映射。
4. 0.4 模型设置。
5. 0.5 业务规则本地记忆。
6. 0.6 老板日报生成。
7. 0.7 历史报告查看。
