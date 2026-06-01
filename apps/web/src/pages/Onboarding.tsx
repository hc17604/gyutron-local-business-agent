import { useState } from "react";
import { useTranslation } from "react-i18next";

import { finishSetup, loadDemoData } from "../api/client";
import type { AuthResponse } from "../types/api";

export function Onboarding({ onDone }: { onDone: (auth: AuthResponse) => void }) {
  const { t } = useTranslation();
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
      setError(caught instanceof Error ? caught.message : t("onboarding.failed"));
    }
  }

  return (
    <main className="onboarding-shell">
      <section className="onboarding-card">
        <div>
          <p className="eyebrow">{t("onboarding.eyebrow")}</p>
          <h1>GyuTron Local Agent</h1>
          <p className="muted">{t("onboarding.description")}</p>
        </div>

        {step === 1 ? (
          <div className="wizard-step">
            <h2>{t("onboarding.welcome")}</h2>
            <p>{t("onboarding.welcomeDescription")}</p>
          </div>
        ) : null}
        {step === 2 ? (
          <div className="wizard-step">
            <h2>{t("onboarding.createAdmin")}</h2>
            <label>{t("onboarding.name")}<input value={form.admin_name} onChange={(event) => update("admin_name", event.target.value)} /></label>
            <label>{t("login.email")}<input value={form.admin_email} onChange={(event) => update("admin_email", event.target.value)} /></label>
            <label>{t("login.password")}<input type="password" value={form.admin_password} onChange={(event) => update("admin_password", event.target.value)} /></label>
          </div>
        ) : null}
        {step === 3 ? (
          <div className="wizard-step">
            <h2>{t("onboarding.configureWorkspace")}</h2>
            <label>{t("onboarding.companyName")}<input value={form.company_name} onChange={(event) => update("company_name", event.target.value)} /></label>
            <label>{t("onboarding.industry")}<input value={form.industry} onChange={(event) => update("industry", event.target.value)} /></label>
            <label>{t("onboarding.defaultLanguage")}<input value={form.default_language} onChange={(event) => update("default_language", event.target.value)} /></label>
          </div>
        ) : null}
        {step === 4 ? (
          <div className="wizard-step">
            <h2>{t("onboarding.configureModel")}</h2>
            <label>{t("onboarding.provider")}<select value={form.provider} onChange={(event) => update("provider", event.target.value)}>
              <option value="skip">{t("onboarding.skipForNow")}</option>
              <option value="openai_compatible">OpenAI-compatible</option>
              <option value="deepseek">DeepSeek</option>
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama</option>
              <option value="lm_studio">LM Studio</option>
            </select></label>
            <label>{t("modelSettings.baseUrl")}<input value={form.base_url} onChange={(event) => update("base_url", event.target.value)} /></label>
            <label>{t("modelSettings.apiKey")}<input type="password" value={form.api_key} onChange={(event) => update("api_key", event.target.value)} /></label>
            <label>{t("onboarding.modelName")}<input value={form.model_name} onChange={(event) => update("model_name", event.target.value)} /></label>
          </div>
        ) : null}
        {step === 5 ? (
          <div className="wizard-step">
            <h2>{t("onboarding.demoData")}</h2>
            <label className="checkbox-row"><input type="checkbox" checked={form.use_demo_data} onChange={(event) => update("use_demo_data", event.target.checked)} />{t("onboarding.loadDemoData")}</label>
            <label className="checkbox-row"><input type="checkbox" checked={form.create_daily_report} onChange={(event) => update("create_daily_report", event.target.checked)} />{t("onboarding.createDailyReport")}</label>
          </div>
        ) : null}

        {error ? <div className="inline-error">{error}</div> : null}
        <div className="page-header-actions">
          <button className="button secondary" disabled={step === 1} onClick={() => setStep((current) => current - 1)} type="button">{t("onboarding.back")}</button>
          {step < 5 ? (
            <button className="button primary" onClick={() => setStep((current) => current + 1)} type="button">{t("onboarding.next")}</button>
          ) : (
            <button className="button primary" onClick={submit} type="button">{t("onboarding.finish")}</button>
          )}
        </div>
      </section>
    </main>
  );
}
