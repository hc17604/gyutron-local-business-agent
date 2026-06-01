import { useTranslation } from "react-i18next";

import { leadRows } from "../../data/mockDashboard";
import { formatCountry } from "../../i18n/formatters";
import { StatusBadge } from "../common/StatusBadge";

export function LeadTable() {
  const { i18n, t } = useTranslation();
  const statusKeyByLabel: Record<string, string> = {
    Overdue: "dashboard.overdue",
    "Pending quote": "dashboard.pendingQuote",
    Negotiating: "dashboard.negotiating",
  };

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{t("dashboard.customer")}</th>
            <th>{t("dashboard.country")}</th>
            <th>{t("dashboard.product")}</th>
            <th>{t("dashboard.value")}</th>
            <th>{t("dashboard.owner")}</th>
            <th>{t("common.status")}</th>
          </tr>
        </thead>
        <tbody>
          {leadRows.map((row) => (
            <tr key={row.customer}>
              <td>{row.customer}</td>
              <td>{formatCountry(row.country, i18n.language)}</td>
              <td>{row.product}</td>
              <td>{row.value}</td>
              <td>{row.owner}</td>
              <td>
                <StatusBadge label={t(statusKeyByLabel[row.status] ?? row.status)} tone={row.status === "Overdue" ? "risk" : "info"} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
