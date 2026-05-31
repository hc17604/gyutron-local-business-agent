# GyuTron Local Agent MVP 开发路线图

## 0.1 项目能启动

目标：建立最小可运行原型。

范围：

- FastAPI 后端。
- React + Vite + TypeScript 前端。
- SQLite 初始化。
- `GET /health`。
- Docker Compose。
- README 本地运行说明。

验收：

- 后端可本地启动。
- 前端可本地启动。
- Docker Compose 可启动。
- 打开前端可以看到后端健康状态。
- SQLite 文件创建到 `data/db/gyutron.sqlite3`。

## 0.2 文件上传和预览

目标：用户可以上传 Excel/CSV 并看到表头和前 20 行。

范围：

- 上传接口。
- 文件保存到 `data/uploads`。
- pandas/openpyxl 解析。
- 前端上传页面。
- 解析错误提示。

验收：

- CSV/XLSX 可上传。
- 用户可选择数据类型。
- 页面显示表头和前 20 行。
- 上传记录写入 SQLite。

## 0.3 字段映射

目标：系统自动猜测字段，用户可以手动修正。

范围：

- 标准字段字典。
- 字段自动猜测规则。
- 字段映射保存。
- 字段映射页面。

验收：

- 常见字段如客户名、国家、产品、金额、时间、状态、销售员可自动猜测。
- 用户可以修改映射。
- 用户可以忽略字段。
- 映射保存到 SQLite。

## 0.4 模型设置

目标：用户配置自己的 OpenAI-compatible 模型。

范围：

- 模型配置页面。
- Base URL、API Key、Model Name 保存。
- 测试连接接口。
- OpenAI-compatible adapter。

验收：

- API Key 不硬编码。
- API Key 不打印到日志。
- 可以保存和读取模型配置。
- 可以测试模型连接。

## 0.5 业务规则本地记忆

目标：用户添加自然语言业务规则。

范围：

- 业务规则 CRUD。
- 规则启用/停用。
- 规则按数据类型适用。
- 报告生成时加载启用规则。

验收：

- 用户可以添加“巴西客户优先级提高”等规则。
- 规则保存到 SQLite。
- 停用规则后不影响新报告。

## 0.6 老板日报生成

目标：基于上传数据、字段映射、业务规则和模型配置生成报告。

范围：

- 数据摘要服务。
- 老板日报 Prompt。
- LLM 调用。
- 报告保存。

验收：

- 报告包含老板摘要、核心数据变化、异常提醒、高优先级客户、产品机会、国家/市场趋势、销售跟进任务、风险点、下一步建议。
- 不把完整原始表格直接发给 LLM。
- 生成失败时保存错误信息。

## 0.7 历史报告查看

目标：用户可以查看历史报告。

范围：

- 报告列表。
- 报告详情。
- 报告 Markdown 渲染。

验收：

- 历史报告可查看。
- 报告保存在 SQLite。
- 可追溯使用的数据摘要和规则快照。

## 优先级原则

1. Local-first。
2. Security-first。
3. Model-agnostic。
4. Read-only first。
5. Business-first。
6. MVP-first。
7. Configurable。

