import { useTranslation } from "react-i18next";

import { leadRows } from "../../data/mockDashboard";
import { StatusBadge } from "../common/StatusBadge";

export function LeadTable() {
  const { t } = useTranslation();

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
              <td>{row.country}</td>
              <td>{row.product}</td>
              <td>{row.value}</td>
              <td>{row.owner}</td>
              <td>
                <StatusBadge label={row.status} tone={row.status === "Overdue" ? "risk" : "info"} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
