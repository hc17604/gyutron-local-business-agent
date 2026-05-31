import { useState } from "react";
import type { ReactElement } from "react";

import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { AgentChatPage } from "./pages/AgentChatPage";
import { AuditLogs } from "./pages/AuditLogs";
import { BusinessRules } from "./pages/BusinessRules";
import { DataSources } from "./pages/DataSources";
import { EcommerceDashboard } from "./pages/EcommerceDashboard";
import { Memory } from "./pages/Memory";
import { ModelSettings } from "./pages/ModelSettings";
import { Overview } from "./pages/Overview";
import { Reports } from "./pages/Reports";
import { SystemSettings } from "./pages/SystemSettings";
import { Tasks } from "./pages/Tasks";
import type { PageKey } from "./types";

const pageMap: Record<PageKey, { title: string; component: ReactElement }> = {
  overview: { title: "Overview", component: <Overview /> },
  agent: { title: "Agent Chat", component: <AgentChatPage /> },
  ecommerce: { title: "Ecommerce Dashboard", component: <EcommerceDashboard /> },
  sources: { title: "Data Sources", component: <DataSources /> },
  reports: { title: "Reports", component: <Reports /> },
  tasks: { title: "Tasks", component: <Tasks /> },
  memory: { title: "Memory", component: <Memory /> },
  rules: { title: "Business Rules", component: <BusinessRules /> },
  audit: { title: "Audit Logs", component: <AuditLogs /> },
  models: { title: "Model Settings", component: <ModelSettings /> },
  system: { title: "System Settings", component: <SystemSettings /> },
};

export function App() {
  const [activePage, setActivePage] = useState<PageKey>("overview");
  const page = pageMap[activePage];

  return (
    <div className="app-frame">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <div className="app-main">
        <Header title={page.title} onNavigate={setActivePage} />
        <div className="page-container">{page.component}</div>
      </div>
    </div>
  );
}
