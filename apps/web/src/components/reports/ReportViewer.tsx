import { useTranslation } from "react-i18next";

export function ReportViewer() {
  const { t } = useTranslation();

  return (
    <article className="report-viewer">
      <h3>{t("reports.demoTitle")}</h3>
      <h4>{t("reports.executiveSummary")}</h4>
      <p>{t("reports.demoSummary")}</p>
      <h4>{t("reports.keyFindings")}</h4>
      <ul>
        <li>{t("reports.demoFindingRevenue")}</li>
        <li>{t("reports.demoFindingFollowup")}</li>
        <li>{t("reports.demoFindingInventory")}</li>
      </ul>
      <h4>{t("reports.actionItems")}</h4>
      <p>{t("reports.demoSuggestion")}</p>
    </article>
  );
}
