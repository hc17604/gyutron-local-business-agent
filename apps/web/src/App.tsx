import { useEffect, useState } from "react";
import type { ReactElement } from "react";
import { useTranslation } from "react-i18next";

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

const pageMap: Record<PageKey, { titleKey: string; component: ReactElement }> = {
  overview: { titleKey: "nav.overview", component: <Overview /> },
  agent: { titleKey: "nav.agentChat", component: <AgentChatPage /> },
  ecommerce: { titleKey: "nav.ecommerceDashboard", component: <EcommerceDashboard /> },
  sources: { titleKey: "nav.dataSources", component: <DataSources /> },
  reports: { titleKey: "nav.reports", component: <Reports /> },
  automations: { titleKey: "nav.automations", component: <Automations /> },
  tasks: { titleKey: "nav.tasks", component: <Tasks /> },
  memory: { titleKey: "nav.memory", component: <Memory /> },
  rules: { titleKey: "nav.businessRules", component: <BusinessRules /> },
  audit: { titleKey: "nav.auditLogs", component: <AuditLogs /> },
  security: { titleKey: "nav.securityCenter", component: <SecurityCenter /> },
  backups: { titleKey: "nav.backupRestore", component: <BackupRestore /> },
  license: { titleKey: "nav.license", component: <License /> },
  health: { titleKey: "nav.systemHealth", component: <SystemHealth /> },
  users: { titleKey: "nav.users", component: <Users /> },
  models: { titleKey: "nav.modelSettings", component: <ModelSettings /> },
  system: { titleKey: "nav.systemSettings", component: <SystemSettings /> },
};

export function App() {
  const { t } = useTranslation();
  const [activePage, setActivePage] = useState<PageKey>("overview");
  const [setupState, setSetupState] = useState<"loading" | "needs_setup" | "ready" | "offline">("loading");
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
      // An unreachable API is NOT "needs setup" — showing the wizard against an
      // already-initialized backend dead-ends with "System is already initialized".
      .catch(() => setSetupState("offline"));
  }, []);

  if (setupState === "loading") {
    return <div className="loading-state">{t("common.loading")} GyuTron Local Agent...</div>;
  }

  if (setupState === "offline") {
    return (
      <div className="loading-state">
        <p>{t("app.apiOffline")}</p>
        <button className="button primary" onClick={() => window.location.reload()} type="button">{t("common.refresh")}</button>
      </div>
    );
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
        <Header title={t(page.titleKey)} onNavigate={setActivePage} />
        <div className="page-container">{page.component}</div>
      </div>
    </div>
  );
}
