import {
  BarChart3,
  Bot,
  Brain,
  ClipboardList,
  Database,
  FileText,
  History,
  Home,
  KeyRound,
  ListChecks,
  PlaySquare,
  Shield,
  Settings,
  ShieldCheck,
  UserRound,
  ArchiveRestore,
  BadgeCheck,
  HeartPulse,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import type { NavigationItem, PageKey } from "../../types";
import { changeLanguage, getCurrentLanguage, type SupportedLanguage } from "../../i18n";

const navItems: NavigationItem[] = [
  { key: "overview", label: "nav.overview", icon: Home },
  { key: "agent", label: "nav.agentChat", icon: Bot },
  { key: "ecommerce", label: "nav.ecommerceDashboard", icon: BarChart3 },
  { key: "sources", label: "nav.dataSources", icon: Database },
  { key: "reports", label: "nav.reports", icon: FileText },
  { key: "automations", label: "nav.automations", icon: PlaySquare },
  { key: "tasks", label: "nav.tasks", icon: ClipboardList },
  { key: "memory", label: "nav.memory", icon: Brain },
  { key: "rules", label: "nav.businessRules", icon: ListChecks },
  { key: "audit", label: "nav.auditLogs", icon: History },
  { key: "security", label: "nav.securityCenter", icon: Shield },
  { key: "backups", label: "nav.backupRestore", icon: ArchiveRestore },
  { key: "license", label: "nav.license", icon: BadgeCheck },
  { key: "health", label: "nav.systemHealth", icon: HeartPulse },
  { key: "users", label: "nav.users", icon: UserRound },
  { key: "models", label: "nav.modelSettings", icon: KeyRound },
  { key: "system", label: "nav.systemSettings", icon: Settings },
];

interface SidebarProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  const { i18n, t } = useTranslation();
  const currentLanguage = getCurrentLanguage();

  function handleLanguageChange(language: SupportedLanguage) {
    void changeLanguage(language);
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <img alt="GyuTron" className="brand-mark" src="/gyutron-logo.ico" />
        <div>
          <strong>GyuTron</strong>
          <span>{t("brand.localAgent")}</span>
        </div>
      </div>

      <div className="language-switcher" aria-label={t("language.switchLanguage")}>
        {(["en", "zh-CN"] as SupportedLanguage[]).map((language) => (
          <button
            className={currentLanguage === language || i18n.language === language ? "active" : ""}
            key={language}
            onClick={() => handleLanguageChange(language)}
            type="button"
          >
            {language === "en" ? t("language.english") : t("language.chinese")}
          </button>
        ))}
      </div>

      <nav className="sidebar-nav" aria-label={t("nav.overview")}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              className={activePage === item.key ? "nav-item active" : "nav-item"}
              key={item.key}
              onClick={() => onNavigate(item.key)}
              type="button"
            >
              <Icon size={18} />
              <span>{t(item.label)}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-foot">
        <ShieldCheck size={18} />
        <div>
          <strong>{t("brand.localFirst")}</strong>
          <span>{t("brand.localFirstDescription")}</span>
        </div>
      </div>
    </aside>
  );
}
