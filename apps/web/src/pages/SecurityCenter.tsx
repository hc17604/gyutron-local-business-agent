import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getSecurityPolicies, previewRedaction } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";

export function SecurityCenter() {
  const { t } = useTranslation();
  const [data, setData] = useState<{ local_mode: Record<string, string>; policies: Array<{ key: string; value_json: Record<string, unknown> }> }>();
  const [sample, setSample] = useState("Customer: Matriz Auto Parts, email buyer@example.com, phone +55 11 99999-0000, amount $18,000");
  const [redacted, setRedacted] = useState<string>();

  useEffect(() => {
    getSecurityPolicies().then(setData).catch(() => undefined);
  }, []);

  async function runPreview() {
    const response = await previewRedaction(sample);
    setRedacted(response.redacted);
  }

  return (
    <div className="page-stack">
      <PageHeader title={t("securityCenter.title")} eyebrow={t("securityCenter.eyebrow")} description={t("securityCenter.description")} />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading"><h2>{t("header.localMode")}</h2></div>
          <div className="settings-list">
            <div><span>{t("systemSettings.dataDirectory")}</span><strong>{data?.local_mode.data_dir ?? "-"}</strong></div>
            <div><span>{t("securityCenter.workspaceRoot")}</span><strong>{data?.local_mode.workspace_root ?? "-"}</strong></div>
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading"><h2>{t("securityCenter.redactionPreview")}</h2></div>
          <label>{t("securityCenter.sampleText")}<input value={sample} onChange={(event) => setSample(event.target.value)} /></label>
          <button className="button primary" onClick={runPreview} type="button">{t("securityCenter.previewRedaction")}</button>
          {redacted ? <p className="muted">{redacted}</p> : null}
        </article>
      </section>
      <section className="panel">
        <div className="panel-heading"><h2>{t("securityCenter.policies")}</h2></div>
        <div className="list-stack">
          {data?.policies.map((policy) => (
            <article className="list-item" key={policy.key}>
              <div><strong>{policy.key}</strong><span>{JSON.stringify(policy.value_json)}</span></div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
