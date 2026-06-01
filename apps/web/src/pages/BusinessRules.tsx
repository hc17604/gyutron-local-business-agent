import { Plus } from "lucide-react";
import { useTranslation } from "react-i18next";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { businessRules } from "../data/mockDashboard";

export function BusinessRules() {
  const { t } = useTranslation();
  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" type="button">
            <Plus size={16} />
            {t("businessRules.addRule")}
          </button>
        }
        description={t("businessRules.description")}
        eyebrow={t("businessRules.eyebrow")}
        title={t("businessRules.title")}
      />
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t("businessRules.rule")}</th>
                <th>{t("businessRules.category")}</th>
                <th>{t("businessRules.descriptionColumn")}</th>
                <th>{t("common.status")}</th>
              </tr>
            </thead>
            <tbody>
              {businessRules.map((rule) => (
                <tr key={rule.title}>
                  <td>{rule.title}</td>
                  <td>{rule.category}</td>
                  <td>{rule.description}</td>
                  <td>
                    <StatusBadge label={rule.status} tone={rule.status === "Active" ? "success" : "neutral"} />
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
