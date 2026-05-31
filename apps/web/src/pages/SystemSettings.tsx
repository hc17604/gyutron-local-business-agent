import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";

export function SystemSettings() {
  return (
    <div className="page-stack">
      <PageHeader
        description="Local deployment settings for data storage, runtime mode, and future workspace options."
        eyebrow="Local runtime"
        title="System Settings"
      />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading">
            <h2>Runtime</h2>
            <StatusBadge label="Local Mode" tone="success" />
          </div>
          <div className="settings-list">
            <div>
              <span>Data directory</span>
              <strong>data/</strong>
            </div>
            <div>
              <span>Uploads</span>
              <strong>data/uploads</strong>
            </div>
            <div>
              <span>Reports</span>
              <strong>data/reports</strong>
            </div>
            <div>
              <span>SQLite</span>
              <strong>data/db/gyutron.sqlite3</strong>
            </div>
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>Security posture</h2>
          </div>
          <p className="muted">
            First version is read-only: no platform writes, no automatic emails, no payment features, and no multi-tenant SaaS behavior.
          </p>
        </article>
      </section>
    </div>
  );
}
