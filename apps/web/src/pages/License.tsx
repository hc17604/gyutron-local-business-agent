import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { activateLicense, getLicense } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { formatStatus } from "../i18n/formatters";
import type { LicenseInfo } from "../types/api";

export function License() {
  const { t } = useTranslation();
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
      <PageHeader title={t("license.title")} eyebrow={t("license.eyebrow")} description={t("license.description")} />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading"><h2>{t("license.currentLicense")}</h2><StatusBadge label={formatStatus(license?.status ?? "trial", t)} tone="info" /></div>
          <div className="settings-list">
            <div><span>{t("license.plan")}</span><strong>{license?.plan ?? "trial"}</strong></div>
            <div><span>{t("license.expires")}</span><strong>{license?.expires_at ?? "-"}</strong></div>
            <div><span>{t("license.maxUsers")}</span><strong>{license?.max_users ?? "-"}</strong></div>
          </div>
        </article>
        <article className="panel">
          <label>{t("license.licenseKey")}<input value={key} onChange={(event) => setKey(event.target.value)} /></label>
          <button className="button primary" onClick={activate} type="button">{t("license.activateLocally")}</button>
        </article>
      </section>
    </div>
  );
}
