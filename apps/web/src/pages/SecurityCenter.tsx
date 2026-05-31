import { useEffect, useState } from "react";

import { getSecurityPolicies, previewRedaction } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";

export function SecurityCenter() {
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
      <PageHeader title="Security Center" eyebrow="Local security policy" description="Review local mode, model data policy, engineering agent policy, automation policy, and audit settings." />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading"><h2>Local Mode</h2></div>
          <div className="settings-list">
            <div><span>Data directory</span><strong>{data?.local_mode.data_dir ?? "-"}</strong></div>
            <div><span>Workspace root</span><strong>{data?.local_mode.workspace_root ?? "-"}</strong></div>
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading"><h2>Redaction Preview</h2></div>
          <label>Sample text<input value={sample} onChange={(event) => setSample(event.target.value)} /></label>
          <button className="button primary" onClick={runPreview} type="button">Preview Redaction</button>
          {redacted ? <p className="muted">{redacted}</p> : null}
        </article>
      </section>
      <section className="panel">
        <div className="panel-heading"><h2>Policies</h2></div>
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
