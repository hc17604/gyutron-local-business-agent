# Phase 5 — 商用复制 / 第二客户模板化 / White-label 驾驶舱

> 文档合并说明：ONBOARDING-CHECKLIST / DEMO-MODE / WHITE-LABEL / REPLICATION-REPORT
> 的核心内容合并于此（单一入口，避免 7 份碎片文档失同步）；CONNECTOR-SPEC 已在
> COMMERCE-MODEL.md。隐私边界沿用 Phase 4（脱敏/零 PII 埋点/GDPR 删除，全部有测试）。

## customer_id 与 source 的关系（架构定案）

- **source = 数据来源**（gyutron-website / gyutron-shop / acme-website / acme-industrial-csv…），
  **customer_id = 隔离边界**（gyutron / acme_demo）。
- website 侧维持**每客户一套 Worker+D1**（template/data-layer，ACME 实例已实跑）；
  agent 侧 `workspace_customers` 注册表 + `data_sources.customer_id` 把 source 归属到客户，
  所有查询（metrics/rules/tasks/reports/overview API）按 customer→sources 解析过滤。
- 不做单库行级多租户、不做计费、不做客户自助注册（既定边界）。

## 配置模板（workspace_customers 行 = 一个客户）

customer_id / display_name / brand_name / logo_text / accent_color /
report_language / currency / timezone / footer_legal / is_demo /
config_json.rule_thresholds（每客户规则阈值覆盖，三层合并：代码默认 < rule_state < 客户）。
新客户 = 一行配置 + connector（base_url + api_key_env 指定环境变量名）。

## Demo Mode 边界

- acme_demo: is_demo=1，源标 is_mock=1；驾驶舱显示红色 DEMO 横幅；
- `POST /customers/{id}/demo-reset` **硬拒非 demo 客户**（ValueError，有测试）；
  只清 mock 源的 commerce/website/task 行，真实数据物理不可达；
- demo 数据与真实日报互不可见（pytest 双向断言 DemoCo/RealCo 不串）。

## White-label 驾驶舱（EcommerceDashboard 页重建）

客户切换下拉 + source + time_range 过滤；指标卡（询盘+RFQ/订单/营收/客单价/
待办/对账）边框色 = 客户 accent_color；标题 = logo_text，眉头 = brand_name，
页脚 = footer_legal；最新报告内嵌。消费 `GET /customers`、
`GET /commerce/overview?customer_id=&source=&time_range=`、`GET /reports?customer_id=`、
`GET /tasks?customer_id=`。

## 第二客户 Onboarding Checklist（实测路径，ACME 演练 = 活例）

1. **部署 data layer**（website repo `template/data-layer/README.md`，15 分钟）：
   复制 wrangler.toml.example → 建 D1 → migrations → 3 secrets → deploy → curl 验收。
2. **agent 接入**：把 DATA_API_KEY 放进 agent `.env`（自定义变量名，如 ACME_DEMO_API_KEY）→
   Data Sources 页建 gyutron_website 类 connector（config: base_url + api_key_env）→ Test → Sync。
3. **客户注册**：workspace_customers 加一行（或沿用 DEFAULT_CUSTOMERS 配置）+
   data_sources 绑 customer_id（connector 同步时自动注册源，ensure_customers 自动绑已知源）。
4. **阈值定制**：config_json.rule_thresholds 按客户调（如 {"rfq_followup":{"threshold_hours":12}}）。
5. **验收**：提交表单→sync→customer_id 过滤的日报/任务/驾驶舱各看一遍；demo-reset 守卫测一次。

## 复制演练记录（2026-06-10 实测）

ACME 演示站从零部署（独立 Worker+D1，workers.dev）→ 3 条真实表单提交 →
connector（同一类，不同 base_url/key env）Test+Sync 6/6 → 规则触发 5 任务
（含 Malaysia 重点国家提优 high）→ ACME 英文日报 / GYUTRON 中文日报按客户默认
→ 驾驶舱双客户隔离（sources/leads/orders 零串）→ GYUTRON 回归通过。
演练抓到并已修复 4 个真问题：thank-you 品牌硬编码、daily 端点漏传 customer_id、
connector 不注册 data_sources、**scoped 评估误关范围外任务（auto-close 越界）**。
距真实付费客户交付的诚实清单（Phase 6 输入）：模板 README 假设会用终端的工程师、
客户行配置还需手写 SQL/配置文件（无管理 UI）、FX 静态表、单操作员无权限体系、
无监控告警/备份自动化/秘钥轮换（= Phase 6 Enterprise Hardening 范围）。
