import { TrendingDown, TrendingUp } from "lucide-react";

import type { Metric } from "../../types";

interface MetricCardProps {
  metric: Metric;
}

export function MetricCard({ metric }: MetricCardProps) {
  const positive = !metric.delta.startsWith("-");

  return (
    <article className="metric-card">
      <span>{metric.label}</span>
      <strong>{metric.value}</strong>
      <small className={metric.tone}>
        {positive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {metric.delta}
      </small>
    </article>
  );
}
