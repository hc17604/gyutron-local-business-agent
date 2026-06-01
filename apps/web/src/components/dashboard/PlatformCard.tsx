import { useTranslation } from "react-i18next";

import type { PlatformPerformance } from "../../types";
import { StatusBadge } from "../common/StatusBadge";

interface PlatformCardProps {
  platform: PlatformPerformance;
}

export function PlatformCard({ platform }: PlatformCardProps) {
  const { t } = useTranslation();

  return (
    <article className="platform-card">
      <div className="card-row">
        <strong>{platform.platform}</strong>
        <StatusBadge label={platform.trend} tone={platform.tone} />
      </div>
      <div className="platform-grid">
        <span>{t("dashboard.revenue")}</span>
        <strong>{platform.revenue}</strong>
        <span>{t("dashboard.orders")}</span>
        <strong>{platform.orders}</strong>
        <span>{t("dashboard.inquiries")}</span>
        <strong>{platform.inquiries}</strong>
        <span>{t("dashboard.conversionRate")}</span>
        <strong>{platform.conversion}</strong>
      </div>
    </article>
  );
}
