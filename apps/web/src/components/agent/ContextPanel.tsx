import { Activity, Code2, Database, FileText, ListChecks, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import { ToolCallList } from "./ToolCallList";

interface ContextPanelProps {
  workspaceRoot?: string;
  selectedProjectPaths?: string[];
  latestTools?: string[];
}

export function ContextPanel({ workspaceRoot, selectedProjectPaths = [], latestTools }: ContextPanelProps) {
  const { t } = useTranslation();
  return (
    <aside className="context-panel">
      <div className="context-panel-head">
        <div>
          <p className="eyebrow">{t("agentChat.agentContext")}</p>
          <h3>{t("agentChat.localWorkspace")}</h3>
        </div>
        <ShieldCheck size={18} />
      </div>
      <section>
        <h3>{t("agentChat.selectedFiles")}</h3>
        <p>
          <FileText size={15} />
          alibaba_inquiries_may.csv
        </p>
        <p>
          <FileText size={15} />
          erp_orders_week22.xlsx
        </p>
      </section>
      <section>
        <h3>{t("agentChat.selectedProjectFiles")}</h3>
        {selectedProjectPaths.length ? (
          selectedProjectPaths.map((path) => (
            <p key={path}>
              <Code2 size={15} />
              {path}
            </p>
          ))
        ) : (
          <p className="muted">{t("agentChat.noProjectFilesSelected")}</p>
        )}
        {workspaceRoot ? <p className="muted">{t("agentChat.root")}: {workspaceRoot}</p> : null}
      </section>
      <section>
        <h3>{t("agentChat.activeBusinessRules")}</h3>
        <p>
          <ListChecks size={15} />
          {t("agentChat.brazilPriority")}
        </p>
        <p>
          <ListChecks size={15} />
          {t("agentChat.noFollowupAlert")}
        </p>
      </section>
      <section>
        <h3>{t("agentChat.localMemoriesUsed")}</h3>
        <p>
          <Database size={15} />
          {t("agentChat.productFocus")}
        </p>
      </section>
      <section>
        <h3><Activity size={14} /> {t("agentChat.toolsAvailable")}</h3>
        <ToolCallList tools={latestTools} />
      </section>
    </aside>
  );
}
