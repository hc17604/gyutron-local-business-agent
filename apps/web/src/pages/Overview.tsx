import { ActionList } from "../components/dashboard/ActionList";
import { AlertList } from "../components/dashboard/AlertList";
import { MetricCard } from "../components/dashboard/MetricCard";
import { PlatformCard } from "../components/dashboard/PlatformCard";
import { alerts, metrics, nextActions, platformPerformance } from "../data/mockDashboard";

export function Overview() {
  return (
    <div className="page-stack">
      <section className="metric-grid">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="grid two-columns">
        <article className="panel agent-summary">
          <div className="panel-heading">
            <h2>Agent Summary</h2>
            <span>Generated from local files</span>
          </div>
          <p>
            Today&apos;s key growth came from Brazil and Indonesia. 6 high-priority inquiries need follow-up. Inventory risk was detected for 2 products, with Industrial Camera IC-420 requiring owner attention.
          </p>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>Next Actions</h2>
            <span>Recommended</span>
          </div>
          <ActionList actions={nextActions} />
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Platform Performance</h2>
          <span>Mocked until platform APIs are connected</span>
        </div>
        <div className="platform-strip">
          {platformPerformance.map((platform) => (
            <PlatformCard key={platform.platform} platform={platform} />
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Alerts</h2>
          <span>Business rule scan</span>
        </div>
        <AlertList alerts={alerts} />
      </section>
    </div>
  );
}
