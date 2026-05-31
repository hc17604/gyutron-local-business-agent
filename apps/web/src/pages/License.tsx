import { useEffect, useState } from "react";

import { activateLicense, getLicense } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { LicenseInfo } from "../types/api";

export function License() {
  const [license, setLicense] = useState<LicenseInfo>();
  const [key, setKey] = useState("GYUTRON-DEMO-LICENSE");

  async function refresh() {
    setLicense(await getLicense());
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function activate() {
    setLicense(await activateLicense({ license_key: key, customer_name: "GyuTron Customer", plan: "professional", max_users: 10, enabled_features: ["connectors", "automations", "reports"] }));
  }

  return (
    <div className="page-stack">
      <PageHeader title="License" eyebrow="Local commercial controls" description="Local trial and license structure for future commercial delivery." />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading"><h2>Current license</h2><StatusBadge label={license?.status ?? "trial"} tone="info" /></div>
          <div className="settings-list">
            <div><span>Plan</span><strong>{license?.plan ?? "trial"}</strong></div>
            <div><span>Expires</span><strong>{license?.expires_at ?? "-"}</strong></div>
            <div><span>Max users</span><strong>{license?.max_users ?? "-"}</strong></div>
          </div>
        </article>
        <article className="panel">
          <label>License key<input value={key} onChange={(event) => setKey(event.target.value)} /></label>
          <button className="button primary" onClick={activate} type="button">Activate Locally</button>
        </article>
      </section>
    </div>
  );
}
