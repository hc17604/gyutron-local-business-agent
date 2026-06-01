import { AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";

import { formatCountry, formatSeverity } from "../../i18n/formatters";
import type { AlertItem } from "../../types";
import { StatusBadge } from "../common/StatusBadge";

interface AlertListProps {
  alerts: AlertItem[];
}

export function AlertList({ alerts }: AlertListProps) {
  const { i18n, t } = useTranslation();

  return (
    <div className="list-stack">
      {alerts.map((alert) => (
        <article className="list-item" key={alert.titleKey}>
          <AlertTriangle size={18} />
          <div>
            <strong>{t(alert.titleKey)}</strong>
            <span>
              {t(alert.summaryKey, {
                ...alert.summaryParams,
                country: formatCountry(String(alert.summaryParams?.country ?? ""), i18n.language),
                product: alert.summaryParams?.product === "Industrial camera SKU IC-420" ? t("products.industrialCameraSku") : alert.summaryParams?.product,
              })}
            </span>
          </div>
          <StatusBadge label={formatSeverity(alert.severity, t)} tone={alert.severity === "high" ? "risk" : "warning"} />
        </article>
      ))}
    </div>
  );
}
