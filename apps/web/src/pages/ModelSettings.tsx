import { EyeOff, PlugZap, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getModelProviders, getModelSettings, saveModelSettings, testModelSettings } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { ModelProvider, ModelSettingsResponse } from "../types/api";

const fallbackSettings: ModelSettingsResponse = {
  id: null,
  provider: "openai_compatible",
  display_name: "OpenAI-compatible",
  base_url: "https://api.openai.com/v1",
  api_key: "",
  model_name: "gpt-4.1-mini",
  is_active: false,
  supports_streaming: false,
};

export function ModelSettings() {
  const { t } = useTranslation();
  const [settings, setSettings] = useState<ModelSettingsResponse>(fallbackSettings);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [status, setStatus] = useState<string>("notTested");
  const [error, setError] = useState<string>();
  const activeProvider = providers.find((provider) => provider.id === settings.provider);

  useEffect(() => {
    getModelSettings().then(setSettings).catch((caught: Error) => setError(caught.message));
    getModelProviders().then((response) => setProviders(response.providers)).catch((caught: Error) => setError(caught.message));
  }, []);

  function updateField<Key extends keyof ModelSettingsResponse>(key: Key, value: ModelSettingsResponse[Key]) {
    setSettings((current) => ({ ...current, [key]: value }));
  }

  async function handleSave() {
    setError(undefined);
    try {
      const saved = await saveModelSettings(settings);
      setSettings(saved);
      setStatus("saved");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed.");
    }
  }

  async function handleTest() {
    setError(undefined);
    setStatus("testing");
    try {
      await testModelSettings(settings);
      setStatus("connected");
    } catch (caught) {
      setStatus("failed");
      setError(caught instanceof Error ? caught.message : "Connection failed.");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        description={t("modelSettings.description")}
        eyebrow={t("modelSettings.eyebrow")}
        title={t("modelSettings.title")}
      />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading">
            <h2>{t("modelSettings.activeModel")}</h2>
            <StatusBadge label={t(`common.${status}`)} tone={status === "connected" ? "success" : status === "failed" ? "risk" : "info"} />
          </div>
          <label>
            {t("modelSettings.provider")}
            <select
              onChange={(event) => {
                const provider = providers.find((item) => item.id === event.target.value);
                updateField("provider", event.target.value);
                updateField("display_name", provider?.label ?? event.target.value);
                updateField("base_url", provider?.default_base_url ?? settings.base_url);
              }}
              value={settings.provider}
            >
              {providers.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t("modelSettings.baseUrl")}
            <input onChange={(event) => updateField("base_url", event.target.value)} value={settings.base_url} />
          </label>
          <label>
            {t("modelSettings.apiKey")}
            <div className="input-with-icon">
              <input onChange={(event) => updateField("api_key", event.target.value)} type="password" value={settings.api_key} />
              <EyeOff size={16} />
            </div>
          </label>
          <label>
            {t("modelSettings.modelName")}
            <input onChange={(event) => updateField("model_name", event.target.value)} value={settings.model_name} />
          </label>
          {error ? <div className="inline-error">{error}</div> : null}
          <div className="page-header-actions">
            <button className="button secondary" onClick={handleSave} type="button">
              <Save size={16} />
              {t("common.save")}
            </button>
            <button className="button primary" onClick={handleTest} type="button">
              <PlugZap size={16} />
              {t("modelSettings.testConnection")}
            </button>
          </div>
        </article>
        <article className="panel">
          <SectionHeader title={t("modelSettings.providerBehavior")} description={t("modelSettings.providerBehaviorDescription")} meta={activeProvider?.requires_api_key ? t("modelSettings.apiKeyRequired") : t("modelSettings.localEndpoint")} />
          <div className="provider-card-grid">
            {providers.map((provider) => (
              <button
                className={settings.provider === provider.id ? "provider-card active" : "provider-card"}
                key={provider.id}
                onClick={() => {
                  updateField("provider", provider.id);
                  updateField("display_name", provider.label);
                  updateField("base_url", provider.default_base_url);
                }}
                type="button"
              >
                <strong>{provider.label}</strong>
                <span>{provider.requires_api_key ? t("modelSettings.externalEndpoint") : t("modelSettings.localCompatibleEndpoint")}</span>
              </button>
            ))}
          </div>
          <div className="settings-list">
            <div>
              <strong>OpenAI-compatible</strong>
              <span>POST /chat/completions</span>
            </div>
            <div>
              <strong>Ollama default</strong>
              <span>http://localhost:11434/v1</span>
            </div>
            <div>
              <strong>LM Studio default</strong>
              <span>http://localhost:1234/v1</span>
            </div>
            <div>
              <strong>{t("modelSettings.security")}</strong>
              <span>{t("modelSettings.securityDescription")}</span>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
