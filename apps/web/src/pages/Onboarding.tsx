import { useState } from "react";

import { finishSetup, loadDemoData } from "../api/client";
import type { AuthResponse } from "../types/api";

export function Onboarding({ onDone }: { onDone: (auth: AuthResponse) => void }) {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    admin_name: "Owner",
    admin_email: "owner@gyutron.local",
    admin_password: "ChangeMe123!",
    company_name: "GyuTron Demo Company",
    industry: "Cross-border manufacturing",
    default_language: "en",
    provider: "skip",
    base_url: "",
    api_key: "",
    model_name: "",
    use_demo_data: true,
    create_daily_report: true,
  });
  const [error, setError] = useState<string>();

  function update(key: string, value: string | boolean) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit() {
    try {
      const auth = await finishSetup({
        ...form,
        model:
          form.provider === "skip"
            ? { provider: "skip" }
            : { provider: form.provider, base_url: form.base_url, api_key: form.api_key, model_name: form.model_name },
      });
      window.localStorage.setItem("gyutron_session_token", auth.token);
      if (form.use_demo_data) {
        await loadDemoData();
      }
      onDone(auth);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Setup failed.");
    }
  }

  return (
    <main className="onboarding-shell">
      <section className="onboarding-card">
        <div>
          <p className="eyebrow">Local-first setup</p>
          <h1>GyuTron Local Agent</h1>
          <p className="muted">Data stays on this machine by default. Complete the first-run setup to enter the workspace.</p>
        </div>

        {step === 1 ? (
          <div className="wizard-step">
            <h2>Welcome</h2>
            <p>Set up a local admin, workspace, model option, demo data, and first automation.</p>
          </div>
        ) : null}
        {step === 2 ? (
          <div className="wizard-step">
            <h2>Create Admin Account</h2>
            <label>Name<input value={form.admin_name} onChange={(event) => update("admin_name", event.target.value)} /></label>
            <label>Email<input value={form.admin_email} onChange={(event) => update("admin_email", event.target.value)} /></label>
            <label>Password<input type="password" value={form.admin_password} onChange={(event) => update("admin_password", event.target.value)} /></label>
          </div>
        ) : null}
        {step === 3 ? (
          <div className="wizard-step">
            <h2>Configure Workspace</h2>
            <label>Company name<input value={form.company_name} onChange={(event) => update("company_name", event.target.value)} /></label>
            <label>Industry<input value={form.industry} onChange={(event) => update("industry", event.target.value)} /></label>
            <label>Default language<input value={form.default_language} onChange={(event) => update("default_language", event.target.value)} /></label>
          </div>
        ) : null}
        {step === 4 ? (
          <div className="wizard-step">
            <h2>Configure Model</h2>
            <label>Provider<select value={form.provider} onChange={(event) => update("provider", event.target.value)}>
              <option value="skip">Skip for now</option>
              <option value="openai_compatible">OpenAI-compatible</option>
              <option value="deepseek">DeepSeek</option>
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama</option>
              <option value="lm_studio">LM Studio</option>
            </select></label>
            <label>Base URL<input value={form.base_url} onChange={(event) => update("base_url", event.target.value)} /></label>
            <label>API Key<input type="password" value={form.api_key} onChange={(event) => update("api_key", event.target.value)} /></label>
            <label>Model name<input value={form.model_name} onChange={(event) => update("model_name", event.target.value)} /></label>
          </div>
        ) : null}
        {step === 5 ? (
          <div className="wizard-step">
            <h2>Demo Data</h2>
            <label className="checkbox-row"><input type="checkbox" checked={form.use_demo_data} onChange={(event) => update("use_demo_data", event.target.checked)} />Load cross-border manufacturing demo data</label>
            <label className="checkbox-row"><input type="checkbox" checked={form.create_daily_report} onChange={(event) => update("create_daily_report", event.target.checked)} />Create Daily Owner Report automation at 09:00</label>
          </div>
        ) : null}

        {error ? <div className="inline-error">{error}</div> : null}
        <div className="page-header-actions">
          <button className="button secondary" disabled={step === 1} onClick={() => setStep((current) => current - 1)} type="button">Back</button>
          {step < 5 ? (
            <button className="button primary" onClick={() => setStep((current) => current + 1)} type="button">Next</button>
          ) : (
            <button className="button primary" onClick={submit} type="button">Finish Setup</button>
          )}
        </div>
      </section>
    </main>
  );
}
