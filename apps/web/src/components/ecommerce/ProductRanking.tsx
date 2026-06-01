import { useTranslation } from "react-i18next";

import { productRanking } from "../../data/mockDashboard";
import { StatusBadge } from "../common/StatusBadge";

export function ProductRanking() {
  const { t } = useTranslation();

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{t("dashboard.product")}</th>
            <th>{t("dashboard.revenue")}</th>
            <th>{t("dashboard.margin")}</th>
            <th>{t("common.status")}</th>
          </tr>
        </thead>
        <tbody>
          {productRanking.map((row) => (
            <tr key={row.product}>
              <td>{row.product}</td>
              <td>{row.revenue}</td>
              <td>{row.margin}</td>
              <td>
                <StatusBadge label={row.status} tone={row.status.includes("risk") || row.status.includes("Low") ? "warning" : "success"} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
