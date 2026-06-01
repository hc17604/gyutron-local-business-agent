import { TrendingDown, TrendingUp } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { Metric } from "../../types";

interface MetricCardProps {
  metric: Metric;
}

export function MetricCard({ metric }: MetricCardProps) {
  const { t } = useTranslation();
  const positive = !metric.delta.startsWith("-");

  return (
    <article className="metric-card">
      <span>{t(metric.labelKey)}</span>
      <strong>{metric.value}</strong>
      <small className={metric.tone}>
        {positive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {metric.deltaKey ? t(metric.deltaKey, metric.deltaParams) : metric.delta}
      </small>
    </article>
  );
}
