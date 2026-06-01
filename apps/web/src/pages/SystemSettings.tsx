import { useTranslation } from "react-i18next";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";

export function SystemSettings() {
  const { t } = useTranslation();

  return (
    <div className="page-stack">
      <PageHeader
        description={t("systemSettings.description")}
        eyebrow={t("systemSettings.eyebrow")}
        title={t("systemSettings.title")}
      />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading">
            <h2>{t("systemSettings.runtime")}</h2>
            <StatusBadge label={t("header.localMode")} tone="success" />
          </div>
          <div className="settings-list">
            <div>
              <span>{t("systemSettings.dataDirectory")}</span>
              <strong>data/</strong>
            </div>
            <div>
              <span>{t("systemSettings.uploads")}</span>
              <strong>data/uploads</strong>
            </div>
            <div>
              <span>{t("systemSettings.reports")}</span>
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
            <h2>{t("systemSettings.securityPosture")}</h2>
          </div>
          <p className="muted">
            {t("systemSettings.securityPostureDescription")}
          </p>
        </article>
      </section>
    </div>
  );
}
