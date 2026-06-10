# Phase 6 — Enterprise Hardening + Boss Decision Center（终阶段）

> 文档合并说明：HEALTH-CHECK / MONITORING / AUDIT-LOG / BOSS-DECISION-CENTER /
> AI-ANALYST-LAYER / BACKUP-RESTORE / SECRET-ROTATION 的运维面合并进 RUNBOOK.md
>（症状索引式，双读者），设计面在本文。COST：当前用量远低于 Cloudflare 免费档
>（D1 <1MB、R2 <1MB、Workers 请求量个位数/分钟），升级触发指标 = D1 5GB/R2 10GB/
> 请求 100k/天 的 50%（届时再核 dashboard 实数）。

## 交付物与设计

- **备份**：website Worker cron（每日 02:00 北京）全表 JSON→R2 backups/（30 天日备
  +12 周周备，manifest 含行数），emit backup.created 审计事件；agent 本地 zip 备份
  （Backup 页）。恢复主路径 = `wrangler d1 export` → 临时库验证（RUNBOOK ⑤）。
- **健康检查**（services/health.py，`GET /health-check?customer_id=`）：connector 存
  在/key 配置（只报有无，绝不读值）/源站可达/同步新鲜度(2h)/报告新鲜度/高优积压 +
  **9 类数据质量检查**（负金额·缺币种·缺时间戳·非法状态·支付无主单·源未绑客户·
  任务缺上下文·空报告·记录缺时间）→ healthy/warning/critical。
- **审计**：agent 既有 write_audit_log 全覆盖（connector/report/task/rule/demo-reset/
  backup/customer），website 补 admin.login.succeeded|failed（仅国家）/
  admin.record_deleted/状态变更 → events 流，Audit Logs 页可查。
- **密钥**：api_keys 表激活（多 key/双 key 窗口），Data API 每 key 限流 120/min
 （KV，key 哈希做限流键），轮换流程+演练见 RUNBOOK ④。
- **Boss Decision Center**（`GET /decision-center` + Overview 页重建）：Today Brief /
  Priority Queue / Opportunity Radar / Risk Watch / **Action Cards**（what·why·
  evidence·action·priority·source + 一键复制中英邮件/WhatsApp 草稿）。
- **AI Analyst Layer**（services/analyst.py）：规则解释（7 类模板，中英）、日报
  Executive Summary、跟进草稿——**确定性实现，无模型依赖**（Phase 3 原则）；LLM
  仅可作可选润色（hook=app/llm），**永不自动发送/写回**。
- **登录 bug 修复**：后端不可达不再误入设置向导（offline 状态+可读提示）。

## 四场演练记录（2026-06-10，全部通过）

1. **灾难恢复**：gyutron_db export(14.8KB) → restore_drill_db 导入 → 五表行数完全
   一致 + 抽样核对 → 临时库删除。
2. **故障告警**：ACME connector 指向不存在的 key 变量 → health critical（指明缺
   MISSING_KEY_VAR，不泄值）→ 还原 → 恢复 warning 基线。
3. **密钥轮换**：ACME 双 key 窗口（新旧同时 200）→ agent 切换 → 旧 key 撤销即 401、
   新 key 200 —— 全程 connector 零中断。
4. **交接**：RUNBOOK 症状索引（7 症状 + 日常节奏 + 三系统一页交接表）。

## 边界（不做，与任务书一致）
SaaS 计费/RBAC/移动端/真实写回（Shopify/Stripe/物流）/自动发邮件/自动 WhatsApp/
高风险自主 agent 操作——全部不做；connector spec 与告警渠道（Email Routing/Slack/
飞书）作为预留接口写明。

## Phase 7 方向（仅建议）
真实第二付费客户上线（用 ONBOARDING 流程实战）、Email Routing 告警邮件接通、
客户管理写操作 UI、Shopify 只读 connector 实装、报告 LLM 润色开关。
