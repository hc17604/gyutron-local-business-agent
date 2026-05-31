# AGENTS.md

本文件是 GYUTRON Local Business Agent 的长期开发指令，适用于 Codex、Claude Code 和其他 AI 编程 Agent。

## 1. 产品定位

GYUTRON Local Business Agent 是一个本地部署的企业 AI 经营 Agent，面向跨境制造企业、跨境电商企业和工业品外贸公司。它不是普通 SaaS 数据看板，也不是泛用聊天机器人。

第一版只做本地老板日报 Agent：

- 本地 Web 控制台。
- Excel/CSV 导入。
- 字段映射。
- 本地 SQLite 记忆。
- 用户自带 LLM API Key。
- 生成老板日报。
- 历史报告和业务规则。

## 2. 不可违背的产品边界

开发时必须遵守：

1. 不要把它做成默认云端 SaaS。
2. 不要默认上传客户业务数据到 GYUTRON 服务器。
3. 不要一开始做复杂多租户或复杂权限系统。
4. 不要一开始接 Alibaba、Amazon、Shopee、TikTok Shop、Shopify 等平台 API。
5. 不要自动修改平台数据、订单、库存、广告、客户资料。
6. 不要自动发邮件、企业微信、Slack 或 WhatsApp，除非后续版本明确要求。
7. 不要把完整大表直接塞给 LLM，必须先做结构化摘要。
8. 不要把演示做成玩具 demo，所有流程要接近真实商业落地。
9. 不允许把任何项目文件、文档、代码、数据库、上传数据、生成物放在 C 盘。项目必须放在非 C 盘路径，例如 `D:\Codex`，或放进明确指定的 GitHub 仓库。

## 3. 技术栈

推荐技术栈：

- Frontend: React + Vite + TypeScript
- Backend: Python FastAPI
- Database: SQLite
- ORM: SQLAlchemy
- Migration: Alembic
- File parsing: pandas, openpyxl
- AI adapter: OpenAI-compatible first
- Deployment: Docker Compose
- Local storage: `data/uploads`, `data/reports`

## 4. 目录原则

优先使用以下目录结构：

```text
backend/
  app/
    api/
    core/
    llm/
    models/
    repositories/
    schemas/
    services/
    prompts/
frontend/
  src/
    api/
    components/
    pages/
    styles/
    types/
docs/
data/
  uploads/
  reports/
samples/
scripts/
```

`data/` 存放客户本地数据，必须加入 `.gitignore`。

## 5. 后端开发规则

### 5.1 分层

- `api/`：HTTP endpoint，只处理请求、响应、依赖注入。
- `schemas/`：Pydantic request/response schema。
- `models/`：SQLAlchemy 数据模型。
- `repositories/`：数据库读写。
- `services/`：业务逻辑。
- `llm/`：模型 Provider adapter。
- `prompts/`：报告生成 prompt。

不要把文件解析、报告生成、LLM 调用等业务逻辑直接写在 endpoint 里。

### 5.2 文件解析

- 支持 CSV、XLSX，后续再考虑 XLS。
- 只预览表头和前 20 行。
- 大文件要避免一次性返回给前端。
- 解析失败时保存错误信息。

### 5.3 字段映射

- 字段自动识别先用确定性规则。
- 允许用户手动修正。
- 保存用户确认后的映射。
- 后续上传相似表头时复用历史映射。

### 5.4 LLM 调用

- 第一版只实现 OpenAI-compatible adapter。
- LLM 输入必须是后端整理后的摘要和规则，不是完整原始表格。
- 报告生成失败必须记录错误。
- 模型配置保存在本地 SQLite。
- API Key 在 MVP 可先本地保存，商用版本必须加密。

## 6. 前端开发规则

### 6.1 页面优先级

先实现以下页面：

1. Dashboard
2. Upload
3. Field Mapping
4. LLM Settings
5. Generate Report
6. Report History
7. Business Rules

### 6.2 UI 风格

- 这是经营工具，不是营销落地页。
- 首页直接进入工作台。
- 信息密度适中，适合老板和业务负责人扫读。
- 控件要清楚，不要让用户猜下一步。
- 涉及调用外部 LLM 时，要提示数据摘要会发送到用户配置的模型服务商。

## 7. 数据模型要求

MVP 至少包含：

- `llm_configs`
- `uploads`
- `field_mappings`
- `business_rules`
- `reports`

报告必须保存：

- 报告正文。
- 数据摘要快照。
- 使用的数据集快照。
- 使用的业务规则快照。
- 模型配置快照，不能保存完整 API Key 到报告快照中。

## 8. 报告质量要求

老板日报必须包含：

1. 今日经营结论。
2. 关键数字。
3. 异常提醒。
4. 重点客户。
5. 重点产品。
6. 国家/市场趋势。
7. 销售跟进任务。
8. 需要老板拍板的问题。

报告必须：

- 使用中文。
- 面向决策和行动。
- 不编造摘要中没有的数据。
- 对数据不足的地方明确说明。
- 体现用户启用的业务规则。

## 9. 测试要求

优先测试：

- CSV/XLSX 解析。
- 字段自动识别。
- 字段映射保存和读取。
- 数据摘要。
- 报告生成失败处理。
- LLM adapter 的 mock 调用。

不要依赖真实外部 LLM API 跑单元测试。

## 10. 文档要求

重要改动要同步更新：

- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `docs/MVP_ROADMAP.md`
- `docs/API.md`
- `README.md`

新增接口后更新 API 文档。新增部署方式后更新 README。

## 11. 开发顺序建议

按以下顺序推进：

1. 项目骨架。
2. 后端健康检查和 SQLite。
3. 前端工作台。
4. 上传和预览。
5. 字段识别和映射。
6. LLM 配置。
7. 数据摘要。
8. 老板日报生成。
9. 历史报告。
10. 业务规则。
11. Docker Compose、样例数据、README、测试。

## 12. 做决策时的优先级

当需求冲突时，优先级如下：

1. 客户数据本地化和安全边界。
2. MVP 简单可演示。
3. 老板日报的商业价值。
4. 代码可维护和可扩展。
5. UI 美观。

任何会显著推迟“本地老板日报可跑起来”的功能，都应推迟到后续版本。
