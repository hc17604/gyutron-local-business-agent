# Claude Handoff Guide

本文档用于让 Claude Code 接手 `GyuTron Local Agent` 项目开发，避免和 Codex 或人工操作产生 Git 冲突。

## 1. 项目基本信息

- 项目名：GyuTron Local Agent
- GitHub 仓库：https://github.com/hc17604/gyutron-local-business-agent
- 本地仓库路径：`D:\Codex\gyutron-local-business-agent`
- 当前主分支：`main`
- 最近已推送提交：`0053c1b style: polish sidebar scrollbar`
- 本地数据目录：`D:\Codex\gyutron-local-business-agent\data`

重要约束：

- 不要把任何项目成果物、数据库、上传文件、运行文件放到 C 盘。
- 不要提交 `data/` 目录内容。
- 不要硬编码 API Key。
- 不要在日志里打印 API Key。
- 不要默认上传客户数据到云端。
- 第一版继续保持 local-first、read-only-first。

## 2. 接手前必须执行

Claude 开始改代码前，先在本地仓库执行：

```powershell
cd D:\Codex\gyutron-local-business-agent
git status
git pull origin main
git log --oneline -5
```

期望状态：

- `git status` 没有未提交改动。
- `git pull origin main` 后本地包含最新提交。
- 最新提交应至少包含：
  - `0053c1b style: polish sidebar scrollbar`
  - `bf0ee17 feat: update sidebar logo`
  - `0b1be8a feat: localize visible UI copy`
  - `13b445c feat: add bilingual i18n support`
  - `d5eab94 feat: polish enterprise UI`

如果工作区不是 clean，先停下来确认，不要直接 reset、checkout 或覆盖用户改动。

## 3. 多 Agent 协作规则

不要让 Codex 和 Claude 同时改同一个工作区、同一个分支。

推荐做法：

1. Claude 接手期间，Codex 不再修改仓库。
2. Claude 每次开始前先 `git pull origin main`。
3. 如果需要并行开发，创建独立分支：

```powershell
git checkout -b claude/<task-name>
```

4. 修改完成后再合并或提交 PR。
5. 不要直接覆盖别人刚改过的文件。

禁止事项：

- 不要执行 `git reset --hard`，除非用户明确要求。
- 不要删除用户未确认的本地文件。
- 不要把 runtime data 提交进 Git。

## 4. 本地启动方式

后端：

```powershell
cd D:\Codex\gyutron-local-business-agent
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
cd apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd D:\Codex\gyutron-local-business-agent\apps\web
npm.cmd install
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

访问：

- Web：http://127.0.0.1:5173
- API health：http://127.0.0.1:8000/health

## 5. 验证命令

每次改动后至少执行：

```powershell
cd D:\Codex\gyutron-local-business-agent\apps\web
npm.cmd run build
npm.cmd run check:i18n
```

```powershell
cd D:\Codex\gyutron-local-business-agent\apps\api
..\..\.venv\Scripts\python.exe -m pytest tests
```

当前验证基线：

- 前端 build 通过，但 Vite 会提示 chunk size warning，可暂时忽略。
- `npm.cmd run check:i18n` 应输出：`No obvious hardcoded English UI strings found.`
- 后端测试当前为：`1 passed`

## 6. 当前项目结构

```text
gyutron-local-business-agent/
  apps/
    api/
      app/
        main.py
        config.py
        database.py
        routers/
        services/
        connectors/
        llm/
        scheduler/
        workspace/
      tests/
      requirements.txt
    web/
      public/
        gyutron-logo.ico
      src/
        api/
        components/
        data/
        i18n/
        pages/
        styles/
        types/
      package.json
  data/
    imports/
    uploads/
    reports/
    db/
    backups/
  docs/
  scripts/
  docker-compose.yml
  README.md
  AGENTS.md
```

## 7. 已完成能力概览

前端：

- React + Vite + TypeScript
- 企业级本地 Web 控制台
- Sidebar / Header / Overview / Agent Chat / Dashboard / Data Sources / Reports / Tasks / Memory / Business Rules / Audit Logs / Model Settings / System Settings
- 中文 / 英文 i18n
- 左上角 `EN / 中文` 语言切换
- 语言选择保存在 `localStorage: gyutron_lang`
- Sidebar logo 已改为 `apps/web/public/gyutron-logo.ico`
- Sidebar 滚动条已美化，滚动或鼠标移动时显示，停止后自动隐藏
- `scripts/check-hardcoded-english.js` 用于发现明显硬编码英文 UI 文案

后端：

- FastAPI
- SQLite 本地数据库
- 本地 setup/auth/users
- Model settings
- OpenAI-compatible LLM adapter
- Agent Chat
- Engineering patch proposal/apply/rollback
- Connector 系统
- Excel / CSV / Local Folder connector
- Automations + scheduler
- Reports
- Alerts
- Audit logs
- Security policies
- Backup / restore
- License trial structure

## 8. i18n 规则

语言文件：

```text
apps/web/src/i18n/locales/en.json
apps/web/src/i18n/locales/zh-CN.json
```

格式化工具：

```text
apps/web/src/i18n/formatters.ts
```

新增 UI 文案时：

1. 先添加英文 key。
2. 再添加中文 key。
3. 组件中使用 `useTranslation()` 和 `t("module.key")`。
4. 不要复制中文版页面。
5. 不要创建 `AgentChatZh.tsx`、`OverviewZh.tsx` 这类文件。
6. 后端返回 `completed / running / high / active` 等 code 时，前端必须用 formatter 显示本地化文案。

检查：

```powershell
cd D:\Codex\gyutron-local-business-agent\apps\web
npm.cmd run check:i18n
```

## 9. 模型接入说明

当前产品支持 OpenAI-compatible API 配置。

DeepSeek 可在 Model Settings 中这样填：

```text
Provider: OpenAI Compatible
Base URL: https://api.deepseek.com
API Key: 用户自己的 DeepSeek API Key
Model Name: deepseek-v4-flash
```

不要硬编码 API Key。

如果客户不希望数据发给外部模型，后续优先接 Ollama / LM Studio 本地模型。

## 10. 最近重要改动

- `0053c1b style: polish sidebar scrollbar`
  - 美化 Sidebar 滚动条。
  - 停止滚动后自动隐藏。

- `bf0ee17 feat: update sidebar logo`
  - 左上角 logo 改为 `gyutron-logo.ico`。

- `0b1be8a feat: localize visible UI copy`
  - 清理中文模式下大部分英文残留。
  - 新增 i18n formatter。
  - 新增硬编码英文检查脚本。

- `13b445c feat: add bilingual i18n support`
  - 接入 `react-i18next`。
  - 增加 `EN / 中文` 切换。
  - Agent Chat / Report 请求携带当前语言。

- `d5eab94 feat: polish enterprise UI`
  - 企业级 UI 打磨。
  - Agent Chat、Reports、Data Sources 等页面视觉升级。

## 11. 当前可继续方向

建议 Claude 下一阶段优先做：

1. 文件上传 / Excel CSV 预览的真实产品化流程。
2. 字段映射 UI。
3. 老板日报生成体验打磨。
4. Model Settings 中增加 DeepSeek 快捷预设。
5. 本地模型 Ollama / LM Studio 引导。
6. Demo 数据切换和演示模式优化。
7. 更细的 i18n 检查脚本，减少 false negative。

避免过早做：

- Alibaba / Shopee / Amazon / TikTok 真实 API。
- 多租户 SaaS 权限系统。
- 云端同步。
- 自动发邮件。
- 自动修改平台数据。

## 12. 提交规范

修改完成后：

```powershell
git status
git add <changed-files>
git commit -m "<type>: <short summary>"
git push origin main
```

推荐 commit 示例：

```text
feat: add file upload preview
feat: implement field mapping workflow
fix: localize report status labels
style: polish report layout
docs: update Claude handoff guide
```

如果 push 被拒绝：

```powershell
git pull --rebase origin main
```

如有冲突，先人工确认冲突内容，不要盲目覆盖。
