import { EyeOff, PlugZap, Save } from "lucide-react";
import { useEffect, useState } from "react";

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
  const [settings, setSettings] = useState<ModelSettingsResponse>(fallbackSettings);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [status, setStatus] = useState<string>("Not tested");
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
      setStatus("Saved");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed.");
    }
  }

  async function handleTest() {
    setError(undefined);
    setStatus("Testing...");
    try {
      await testModelSettings(settings);
      setStatus("Connected");
    } catch (caught) {
      setStatus("Failed");
      setError(caught instanceof Error ? caught.message : "Connection failed.");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        description="Configure customer-owned model credentials. API keys are stored locally, masked in the UI, and never printed by the app."
        eyebrow="Model provider"
        title="Model Settings"
      />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading">
            <h2>Active model</h2>
            <StatusBadge label={status} tone={status === "Connected" ? "success" : status === "Failed" ? "risk" : "info"} />
          </div>
          <label>
            Provider
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
            Base URL
            <input onChange={(event) => updateField("base_url", event.target.value)} value={settings.base_url} />
          </label>
          <label>
            API Key
            <div className="input-with-icon">
              <input onChange={(event) => updateField("api_key", event.target.value)} type="password" value={settings.api_key} />
              <EyeOff size={16} />
            </div>
          </label>
          <label>
            Model Name
            <input onChange={(event) => updateField("model_name", event.target.value)} value={settings.model_name} />
          </label>
          {error ? <div className="inline-error">{error}</div> : null}
          <div className="page-header-actions">
            <button className="button secondary" onClick={handleSave} type="button">
              <Save size={16} />
              Save
            </button>
            <button className="button primary" onClick={handleTest} type="button">
              <PlugZap size={16} />
              Test Connection
            </button>
          </div>
        </article>
        <article className="panel">
          <SectionHeader title="Provider behavior" description="Use Ollama or LM Studio for fully local inference. External API providers should follow your security policy." meta={activeProvider?.requires_api_key ? "API key required" : "Local endpoint"} />
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
                <span>{provider.requires_api_key ? "External or hosted endpoint" : "Local OpenAI-compatible endpoint"}</span>
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
              <strong>Security</strong>
              <span>Local save, masked return, no key logging</span>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
