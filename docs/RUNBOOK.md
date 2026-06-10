# RUNBOOK — 出事了翻这页（症状索引）

> 双读者：不懂代码的老板（看"症状→第一步"）+ 三个月后失忆的工程师（看命令）。
> 仓库：官网 `gyutron-website`（push=上线！）；工作台 `gyutron-local-business-agent`。

## 症状索引

**① 官网打不开 / 表单报错**
第一步：开 https://www.gyutron.com/api/v1/health 。返回 ok = Worker 活着，是页面问题；打不开 = Cloudflare 侧。
工程师：`npx wrangler deployments list`（website repo 根）→ 异常则 `npx wrangler rollback`。代码回滚：`git revert <commit>` + push。

**② 表单提交被拒（Anti-spam verification failed）**
真人也被拒 = Turnstile 配置问题。止血开关（立即恢复表单、暂失反垃圾）：
`npx wrangler secret delete TURNSTILE_SECRET_KEY` → 修好 widget 域名配置后再 put 回去。

**③ 日报没出 / 数据没同步**
第一步：打开工作台 Overview（决策中心）看系统健康；Data Sources 页看最近同步。
工程师：后端没跑？`apps\api> ..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`。
前端显示"后端 API 无法连接" = 先启动后端（不要进设置向导）。
同步红色 = 看 `GET /health-check?customer_id=gyutron` 的 critical 项（通常是 key 环境变量缺失——key 在 agent 仓库 `.env`）。

**④ 怀疑 API key 泄露（轮换流程，已演练）**
1. 生成新 key → SHA-256 入对应 D1 `api_keys` 表（status=active）——双 key 窗口开启，服务不中断；
2. agent `.env` 切到新 key → 同步验证 200；
3. `npx wrangler secret put DATA_API_KEY --config <该客户 toml>` 写入新值 = 旧 key 即刻 401；
4. 演练记录：2026-06-10 ACME 全程零中断（旧 200/新 200 → 切换 → 旧 401/新 200）。
ADMIN_PASSWORD / TURNSTILE_SECRET_KEY：直接 `wrangler secret put` 新值即可（无窗口需求）。

**⑤ 要恢复数据（备份在哪）**
- 自动：每日 02:00（北京）Worker Cron 导出全表 JSON → R2 `backups/daily/`（留 30 天，周日另存 weekly 留 12 周），含 manifest 行数校验。
- 手动恢复（已演练，行数一致）：
  `npx wrangler d1 export gyutron_db --remote --output backup.sql`
  `npx wrangler d1 create restore_drill_db` → `npx wrangler d1 execute restore_drill_db --remote --file backup.sql` → 对比行数 → 确认后切换/导回。
- agent 本地库：Backup & Restore 页一键备份（zip 到 data/backups/）。
- 恢复必须明确目标库名——绝不可对 `gyutron_db` 直接 execute 恢复文件（先临时库验证）。

**⑥ 要删除某客户数据（GDPR）**
agent：`delete_entity(source, external_id)` 级联删 commerce 表；website D1：/admin 删除（写审计事件）。Demo 整体重置：`POST /customers/acme_demo/demo-reset`（硬拒真实客户）。

**⑦ 收到异常告警（决策中心 Risk Watch / 健康红标）**
critical = 当天处理（key 缺失/源不可达/负金额订单）；warning = 本周处理（同步过期/数据缺字段）。每项 detail 已写明缺什么。

## 日常节奏（OPERATIONS）
- 每天：开 Overview 决策中心处理行动卡片（08:00 自动日报、15 分钟自动同步在跑）。
- 每周：ACME demo-reset（演示站公网保留决策见 PHASE5_RELEASE.md）；看一眼 R2 backups/daily/ 有新文件。
- 每季：①备份恢复演练 ②key 轮换演练（流程见上，均已有 2026-06-10 基线记录）。
- 自动化清单：website cron `0 18 * * *`（备份）；agent automations：Website auto-sync(15min)、Daily owner report(08:00)。

## 三套系统一页交接
| 系统 | 仓库/路径 | 资源 | secrets（名，无值） |
|---|---|---|---|
| 官网+API | hc17604/gyutron-website（Worker gyutron-website）| D1 gyutron_db · R2 gyutron-assets · KV RATE_LIMIT | DATA_API_KEY, ADMIN_PASSWORD, IP_HASH_SALT, TURNSTILE_SECRET_KEY |
| ACME 演示 | 同仓库 template/data-layer/deployments/acme-demo | Worker acme-demo-data-layer · D1 acme_demo_db | 同上三件（独立值） |
| 工作台 | hc17604/gyutron-local-business-agent（本机 :8000/:5173）| SQLite data/db/ | .env: GYUTRON_WEBSITE_API_KEY, ACME_DEMO_API_KEY |
文档索引：PHASE3-6.md（引擎/commerce/复制/加固）、COMMERCE-MODEL.md（模型+接入规范）、PHASE5_RELEASE.md（封版+演示链路）、website repo docs/（部署/契约/架构）。
