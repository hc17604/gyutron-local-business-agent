import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getBusinessRules, toggleBusinessRule } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { BusinessRuleInfo } from "../types/api";

export function BusinessRules() {
  const { t, i18n } = useTranslation();
  const [rules, setRules] = useState<BusinessRuleInfo[]>([]);
  const [message, setMessage] = useState<string>();
  const zh = i18n.language.toLowerCase().startsWith("zh");

  async function refresh() {
    const response = await getBusinessRules();
    setRules(response.rules);
  }

  useEffect(() => {
    refresh().catch((error: Error) => setMessage(error.message));
  }, []);

  async function handleToggle(rule: BusinessRuleInfo) {
    await toggleBusinessRule(rule.rule_id, !rule.enabled);
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader description={t("businessRules.description")} eyebrow={t("businessRules.eyebrow")} title={t("businessRules.title")} />
      {message ? <div className="inline-info">{message}</div> : null}
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t("businessRules.rule")}</th>
                <th>{t("businessRules.descriptionColumn")}</th>
                <th>{t("common.status")}</th>
                <th>{t("businessRules.lastTriggered")}</th>
                <th>{t("businessRules.triggerCount")}</th>
                <th>{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.rule_id}>
                  <td>
                    <strong>{zh ? rule.name.zh : rule.name.en}</strong>
                    <div className="muted">{rule.rule_id}</div>
                  </td>
                  <td>{zh ? rule.description.zh : rule.description.en}</td>
                  <td>
                    <StatusBadge
                      label={rule.enabled ? t("businessRules.enabled") : t("businessRules.disabled")}
                      tone={rule.enabled ? "success" : "neutral"}
                    />
                  </td>
                  <td>{rule.last_triggered_at ?? "-"}</td>
                  <td>{rule.triggered_count}</td>
                  <td>
                    <button className="table-action" onClick={() => void handleToggle(rule).catch((error: Error) => setMessage(error.message))} type="button">
                      {rule.enabled ? t("businessRules.disable") : t("businessRules.enable")}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
