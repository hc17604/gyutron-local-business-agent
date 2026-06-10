# Phase 4 — Commerce Data Model + 多源统一（取舍记录）

交付标准（达成）：官网数据源（真实）+ shop 行为事件源（真实埋点）+ CSV 订单源
（ACME mock 客户）→ 同一 adapter 接口 → 统一 commerce model → 同一套
metrics/rules/tasks/reports → 跨源日报 + 跨源规则 + source 过滤 API。
营收无双算、重复导入幂等、mock 数据隔离 —— 全部 pytest 实证（19 passed）。

## 关键取舍（为什么）

- **CSV 先行、Shopify/Stripe 只写纸面设计**：不为没在用的平台写代码（任务书硬规
  矩#3）；adapter 抽象已由 3 个真实实现证明。设计见 COMMERCE-MODEL.md 末节。
- **shop 埋点 = 行为事件 feed，刻意不叫 order connector**：shop 是静态站无真实订
  单；埋点走 Worker HTMLRewriter 注入（零改动生成的 shop 文件），严格最小化（无
  IP/会话/指纹/PII，匿名 handle 级信号）。弃购信号因此是 handle 级而非用户级——
  隐私换精度，故意的。
- **写回推迟**：中台严格只读（硬规矩#2）；"已付款未发货"任务的建议文案明确指向
  "去源系统操作"。
- **FX 静态表**：报表级精度够用；接真实交易量后换 provider 即可（单点替换
  `commerce_store.to_base`）。
- **文档合并**：CONNECTOR-SPEC 并入 COMMERCE-MODEL.md（接入规范章节），减少文
  档碎片；商用叙事不受影响。
- **驾驶舱**：后端 `GET /commerce/overview?source=&time_range=`（含 data_sources
  注册表、跨源汇总、对账、open tasks）已交付并可按 source 过滤；前端专页留待
  Phase 5 的 white-label 驾驶舱一并做（避免在现有 mock Dashboard 上做半套）。

## 新增规则（进现有引擎，可配置可启停）

`cart_abandonment`（加购 48h 无询价 → 日报弃购线索）、`paid_not_fulfilled`
（付款 N 天未发货 → 高优任务）、`high_views_no_inquiry`（高浏览零询盘 → 机会任
务）。日报新增 Commerce 板块（今日/7天订单、营收、AOV、Top 产品、商城行为）。

## 升级路径

source 级客户归并视图、FX provider、Shopify/Stripe connector（接口已定）、
refunds/inventory 启用、驾驶舱专页（Phase 5 white-label）。
