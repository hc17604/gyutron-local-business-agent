import { useEffect, useState } from "react";
import type { ReactElement } from "react";

import { getMe, getSetupStatus } from "./api/client";
import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { AgentChatPage } from "./pages/AgentChatPage";
import { AuditLogs } from "./pages/AuditLogs";
import { Automations } from "./pages/Automations";
import { BackupRestore } from "./pages/BackupRestore";
import { BusinessRules } from "./pages/BusinessRules";
import { DataSources } from "./pages/DataSources";
import { EcommerceDashboard } from "./pages/EcommerceDashboard";
import { License } from "./pages/License";
import { Login } from "./pages/Login";
import { Memory } from "./pages/Memory";
import { ModelSettings } from "./pages/ModelSettings";
import { Onboarding } from "./pages/Onboarding";
import { Overview } from "./pages/Overview";
import { Reports } from "./pages/Reports";
import { SecurityCenter } from "./pages/SecurityCenter";
import { SystemHealth } from "./pages/SystemHealth";
import { SystemSettings } from "./pages/SystemSettings";
import { Tasks } from "./pages/Tasks";
import { Users } from "./pages/Users";
import type { AuthUser } from "./types/api";
import type { PageKey } from "./types";

const pageMap: Record<PageKey, { title: string; component: ReactElement }> = {
  overview: { title: "Overview", component: <Overview /> },
  agent: { title: "Agent Chat", component: <AgentChatPage /> },
  ecommerce: { title: "Ecommerce Dashboard", component: <EcommerceDashboard /> },
  sources: { title: "Data Sources", component: <DataSources /> },
  reports: { title: "Reports", component: <Reports /> },
  automations: { title: "Automations", component: <Automations /> },
  tasks: { title: "Tasks", component: <Tasks /> },
  memory: { title: "Memory", component: <Memory /> },
  rules: { title: "Business Rules", component: <BusinessRules /> },
  audit: { title: "Audit Logs", component: <AuditLogs /> },
  security: { title: "Security Center", component: <SecurityCenter /> },
  backups: { title: "Backup & Restore", component: <BackupRestore /> },
  license: { title: "License", component: <License /> },
  health: { title: "System Health", component: <SystemHealth /> },
  users: { title: "Users", component: <Users /> },
  models: { title: "Model Settings", component: <ModelSettings /> },
  system: { title: "System Settings", component: <SystemSettings /> },
};

export function App() {
  const [activePage, setActivePage] = useState<PageKey>("overview");
  const [setupState, setSetupState] = useState<"loading" | "needs_setup" | "ready">("loading");
  const [user, setUser] = useState<AuthUser>();
  const page = pageMap[activePage];

  useEffect(() => {
    getSetupStatus()
      .then(async (status) => {
        if (!status.is_initialized) {
          setSetupState("needs_setup");
          return;
        }
        setSetupState("ready");
        const token = window.localStorage.getItem("gyutron_session_token");
        if (token) {
          try {
            const response = await getMe();
            setUser(response.user);
          } catch {
            window.localStorage.removeItem("gyutron_session_token");
          }
        }
      })
      .catch(() => setSetupState("needs_setup"));
  }, []);

  if (setupState === "loading") {
    return <div className="loading-state">Loading GyuTron Local Agent...</div>;
  }

  if (setupState === "needs_setup") {
    return <Onboarding onDone={(auth) => { setUser(auth.user); setSetupState("ready"); }} />;
  }

  if (!user) {
    return <Login onLogin={(auth) => setUser(auth.user)} />;
  }

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
