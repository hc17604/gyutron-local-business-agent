import { BarChart3 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { CountryRanking } from "../components/ecommerce/CountryRanking";
import { LeadTable } from "../components/ecommerce/LeadTable";
import { ProductRanking } from "../components/ecommerce/ProductRanking";
import { RevenueChart } from "../components/ecommerce/RevenueChart";
import { metrics } from "../data/mockDashboard";

const filterKeys = ["dashboard.today", "dashboard.sevenDays", "dashboard.thirtyDays", "dashboard.custom"];
const platforms = ["dashboard.allPlatforms", "Alibaba", "Shopee", "Amazon", "TikTok Shop", "Shopify", "ERP"];

export function EcommerceDashboard() {
  const { t } = useTranslation();

  return (
    <div className="page-stack">
      <PageHeader
        actions={<StatusBadge label={t("dashboard.mockData")} tone="warning" />}
        description={t("dashboard.description")}
        eyebrow={t("dashboard.eyebrow")}
        title={t("dashboard.pageTitle")}
      />

      <section className="filter-row">
        {filterKeys.map((filterKey) => (
          <button className={filterKey === "dashboard.sevenDays" ? "chip-button active" : "chip-button"} key={filterKey} type="button">
            {t(filterKey)}
          </button>
        ))}
        <span className="filter-divider" />
        {platforms.map((platform) => (
          <button className={platform === "dashboard.allPlatforms" ? "chip-button active" : "chip-button"} key={platform} type="button">
            {platform.startsWith("dashboard.") ? t(platform) : platform}
          </button>
        ))}
      </section>

      <section className="metric-grid compact">
        {metrics.slice(0, 6).map((metric) => (
          <article className="mini-metric" key={metric.labelKey}>
            <span>{t(metric.labelKey)}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="grid dashboard-grid">
        <article className="panel wide">
          <div className="panel-heading">
            <h2>
              <BarChart3 size={18} />
              {t("dashboard.revenueTrend")}
            </h2>
            <span>{t("dashboard.lastSevenDays")}</span>
          </div>
          <RevenueChart />
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>{t("dashboard.inquiriesByCountry")}</h2>
            <span>{t("dashboard.topMarkets")}</span>
          </div>
          <CountryRanking />
        </article>
      </section>

      <section className="grid two-columns">
        <article className="panel">
          <div className="panel-heading">
            <h2>{t("dashboard.productRanking")}</h2>
          </div>
          <ProductRanking />
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>{t("dashboard.highPriorityLeads")}</h2>
          </div>
          <LeadTable />
        </article>
      </section>
    </div>
  );
}
