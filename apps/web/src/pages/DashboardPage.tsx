import { AlertTriangle, CheckCircle2, Database, FileSpreadsheet, KeyRound, ListChecks } from "lucide-react";
import { useEffect, useState } from "react";

import { getHealth } from "../api/client";
import type { HealthResponse } from "../types/api";

const nextSteps = [
  { label: "上传 Excel / CSV", icon: FileSpreadsheet },
  { label: "修正字段映射", icon: ListChecks },
  { label: "配置模型 API", icon: KeyRound },
  { label: "生成老板日报", icon: Database },
];

export function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Local-first business agent</p>
          <h1>GyuTron Local Agent</h1>
        </div>
        <span className={health ? "status status-ok" : "status status-warn"}>
          {health ? "API 在线" : "等待 API"}
        </span>
      </section>

      <section className="status-panel">
        <div className="status-heading">
          {health ? <CheckCircle2 size={22} /> : <AlertTriangle size={22} />}
          <h2>本地服务状态</h2>
        </div>
        {health ? (
          <dl className="status-grid">
            <div>
              <dt>服务</dt>
              <dd>{health.service}</dd>
            </div>
            <div>
              <dt>数据目录</dt>
              <dd>{health.data_dir}</dd>
            </div>
            <div>
              <dt>SQLite</dt>
              <dd>{health.database_path}</dd>
            </div>
          </dl>
        ) : (
          <p className="muted">{error ?? "正在连接本地 FastAPI 后端..."}</p>
        )}
      </section>

      <section className="privacy-band">
        <h2>本地优先</h2>
        <p>
          客户上传文件、字段映射、业务规则和历史报告默认保存在本地。后续生成报告时，只把整理后的摘要发送到用户自己配置的模型服务商。
        </p>
      </section>

      <section className="module-grid" aria-label="MVP modules">
        {nextSteps.map((item) => {
          const Icon = item.icon;
          return (
            <article className="module-card" key={item.label}>
              <Icon size={22} />
              <span>{item.label}</span>
            </article>
          );
        })}
      </section>
    </main>
  );
}

