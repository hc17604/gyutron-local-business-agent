# Phase 5 Release Note（封版 2026-06-10）

## 版本基线
- website repo: `a65bd6a`（模板 + ACME 实例 + 品牌化）；agent repo: `6d39e3b`（客户隔离 + 白标驾驶舱 + demo mode）。
- 此后 Phase 5 范围冻结，新能力一律进 Phase 6+。

## GYUTRON 生产链路（handoff）
- 官网 https://www.gyutron.com（Worker `gyutron-website`，D1 `gyutron_db`，R2 `gyutron-assets`，KV 限流）。
- 四表单（contact/rfq/support/download）+ Turnstile 强制 + R2 三级下发 + /admin + /api/v1。
- agent 工作台 customer_id=`gyutron`（报告默认中文），自动同步 15 分钟，日报 08:00。

## ACME Demo 链路（handoff）
- 演示站：`https://acme-demo-data-layer.muddy-disk-1397.workers.dev`（Worker `acme-demo-data-layer`，D1 `acme_demo_db`，独立 secrets）。
- 部署方式：`template/data-layer/README.md`（15 分钟流程）；配置在 `template/data-layer/deployments/acme-demo/wrangler.toml`。
- 重置方式：agent `POST /customers/acme_demo/demo-reset`（仅 mock 源，硬拒真实客户）；演示站 D1 如需清空按 README 重跑 migrations。
- **公网暴露决策（Phase 6 P0②）**：保留运行用于销售演示——数据全虚构、admin 有独立密码、表单有校验；风险仅为垃圾行，按 OPERATIONS 节奏每周 demo-reset。5 分钟重建流程 = README 部署流程。

## Phase 5 演练 bug 复盘（4 个，全部已修）
1. thank-you 文案 GYUTRON 硬编码 → `dataSource(env).name` 品牌化（`a65bd6a`）。
2. daily 端点漏传 customer_id → 修复 + payload language 默认 None（客户语言偏好生效）。
3. website connector 不注册 data_sources → 同步时自动注册 + 绑定客户归属。
4. **scoped 评估 auto-close 越界**（可误关其他客户任务）→ close 范围限定本次评估的 sources（`6d39e3b`）。
