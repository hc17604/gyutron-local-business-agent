import { EyeOff, PlugZap } from "lucide-react";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";

export function ModelSettings() {
  return (
    <div className="page-stack">
      <PageHeader
        description="Configure customer-owned model credentials. The UI masks API keys and does not log them."
        eyebrow="Model provider"
        title="Model Settings"
      />
      <section className="settings-grid">
        <article className="panel">
          <div className="panel-heading">
            <h2>Active model</h2>
            <StatusBadge label="OpenAI-compatible" tone="info" />
          </div>
          <label>
            Provider
            <input defaultValue="OpenAI Compatible" />
          </label>
          <label>
            Base URL
            <input defaultValue="https://api.openai.com/v1" />
          </label>
          <label>
            API Key
            <div className="input-with-icon">
              <input defaultValue="sk-••••••••••••••••••••" type="password" />
              <EyeOff size={16} />
            </div>
          </label>
          <label>
            Model Name
            <input defaultValue="gpt-4.1-mini" />
          </label>
          <button className="button primary" type="button">
            <PlugZap size={16} />
            Test Connection
          </button>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>Local model</h2>
            <StatusBadge label="Coming soon" tone="neutral" />
          </div>
          <p className="muted">
            Ollama, LM Studio, Qwen, DeepSeek, Claude, and Gemini adapters will be added behind the same provider interface.
          </p>
        </article>
      </section>
    </div>
  );
}
