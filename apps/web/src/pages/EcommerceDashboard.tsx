import { BarChart3 } from "lucide-react";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { CountryRanking } from "../components/ecommerce/CountryRanking";
import { LeadTable } from "../components/ecommerce/LeadTable";
import { ProductRanking } from "../components/ecommerce/ProductRanking";
import { RevenueChart } from "../components/ecommerce/RevenueChart";
import { metrics } from "../data/mockDashboard";

const filters = ["Today", "7 days", "30 days", "Custom"];
const platforms = ["All Platforms", "Alibaba", "Shopee", "Amazon", "TikTok Shop", "Shopify", "ERP"];

export function EcommerceDashboard() {
  return (
    <div className="page-stack">
      <PageHeader
        actions={<StatusBadge label="Mock data" tone="warning" />}
        description="Cross-platform view for revenue, orders, inquiries, conversion, margin, ads, and follow-up status."
        eyebrow="Cross-platform operations"
        title="Ecommerce performance"
      />

      <section className="filter-row">
        {filters.map((filter) => (
          <button className={filter === "7 days" ? "chip-button active" : "chip-button"} key={filter} type="button">
            {filter}
          </button>
        ))}
        <span className="filter-divider" />
        {platforms.map((platform) => (
          <button className={platform === "All Platforms" ? "chip-button active" : "chip-button"} key={platform} type="button">
            {platform}
          </button>
        ))}
      </section>

      <section className="metric-grid compact">
        {metrics.slice(0, 6).map((metric) => (
          <article className="mini-metric" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="grid dashboard-grid">
        <article className="panel wide">
          <div className="panel-heading">
            <h2>
              <BarChart3 size={18} />
              Revenue trend
            </h2>
            <span>Last 7 days</span>
          </div>
          <RevenueChart />
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>Inquiries by country</h2>
            <span>Top markets</span>
          </div>
          <CountryRanking />
        </article>
      </section>

      <section className="grid two-columns">
        <article className="panel">
          <div className="panel-heading">
            <h2>Product performance ranking</h2>
          </div>
          <ProductRanking />
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>High priority leads</h2>
          </div>
          <LeadTable />
        </article>
      </section>
    </div>
  );
}
