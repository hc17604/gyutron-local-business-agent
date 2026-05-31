# GyuTron Local Agent API 文档

## `GET /health`

返回后端运行状态和本地存储路径。

响应示例：

```json
{
  "status": "ok",
  "service": "gyutron-local-agent-api",
  "data_dir": "/app/data",
  "database_path": "/app/data/db/gyutron.sqlite3"
}
```

后续接口将按 MVP 阶段逐步补充：

- 上传与预览。
- 字段映射。
- 模型配置。
- 业务规则。
- 老板日报生成。
- 历史报告。

