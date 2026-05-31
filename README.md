# GyuTron Local Agent

本地部署的企业 AI 业务 Agent，面向跨境制造企业、跨境电商企业和工业品外贸公司。

第一阶段已经包含：

- FastAPI 后端。
- React + Vite + TypeScript 前端。
- SQLite 初始化。
- `GET /health`。
- Docker Compose。
- 本地数据目录：`data/uploads`、`data/reports`、`data/db`。

第三阶段前端产品化界面已经包含：

- 企业后台式 Sidebar + Header + 主内容区。
- Overview 经营驾驶舱。
- Agent Chat 本地业务 Agent 指令入口。
- Ecommerce Dashboard 跨平台经营分析页。
- Data Sources 数据源管理页。
- Reports 老板日报管理页。
- Tasks 任务中心。
- Memory 本地记忆页。
- Business Rules 业务规则页。
- Audit Logs 审计日志页。
- Model Settings 和 System Settings。

当前只有 `/health` 接入真实后端 API；上传、报告、任务、记忆、规则等页面先使用前端 mock data service，方便后续替换为真实 API。

## 本地开发启动

后端：

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r apps/api/requirements.txt
cd apps/api
../../.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd apps/web
npm.cmd install
npm.cmd run dev
```

打开：

- Web: http://localhost:5173
- API health: http://localhost:8000/health

## 演示路径

1. 打开 Overview，查看经营 KPI、Agent Summary、平台表现、异常提醒和下一步行动。
2. 进入 Agent Chat，查看本地业务 Agent 指令入口和右侧 Context Panel。
3. 进入 Ecommerce Dashboard，查看跨平台趋势、国家市场、产品排名和高优先级客户。
4. 进入 Data Sources，查看 Excel/CSV 当前可用和平台 API Coming Soon 入口。
5. 进入 Reports，查看老板日报列表和 Markdown 风格报告详情。
6. 进入 Model Settings，查看 OpenAI-compatible 模型配置入口。

## Docker Compose 启动

```bash
docker compose up --build
```

打开：

- Web: http://localhost:5173
- API health: http://localhost:8000/health

## 本地数据

运行时会自动创建：

```text
data/
  uploads/
  reports/
  db/
    gyutron.sqlite3
```

`data/` 默认不提交到 Git。客户业务数据、上传文件、字段映射、业务规则和历史报告都应默认保存在本地。

## 安全原则

- 不硬编码 API Key。
- 不在日志里打印 API Key。
- 不默认上传客户业务数据到云端。
- 第一版只读数据，不自动执行高风险动作。
