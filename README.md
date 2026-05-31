# GyuTron Local Agent

本地部署的企业 AI 业务 Agent，面向跨境制造企业、跨境电商企业和工业品外贸公司。

第一阶段已经包含：

- FastAPI 后端。
- React + Vite + TypeScript 前端。
- SQLite 初始化。
- `GET /health`。
- Docker Compose。
- 本地数据目录：`data/uploads`、`data/reports`、`data/db`。

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
