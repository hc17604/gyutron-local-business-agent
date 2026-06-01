import { useTranslation } from "react-i18next";

import { PageHeader } from "../components/common/PageHeader";
import { TaskTable } from "../components/tasks/TaskTable";

export function Tasks() {
  const { t } = useTranslation();
  return (
    <div className="page-stack">
      <PageHeader
        description={t("tasks.description")}
        eyebrow={t("tasks.eyebrow")}
        title={t("tasks.title")}
      />
      <section className="panel">
        <div className="panel-heading">
          <h2>{t("tasks.taskHistory")}</h2>
          <span>{t("tasks.mocked")}</span>
        </div>
        <TaskTable />
      </section>
    </div>
  );
}
