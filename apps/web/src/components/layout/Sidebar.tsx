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

import type { NavigationItem, PageKey } from "../../types";

const navItems: NavigationItem[] = [
  { key: "overview", label: "Overview", icon: Home },
  { key: "agent", label: "Agent Chat", icon: Bot },
  { key: "ecommerce", label: "Ecommerce Dashboard", icon: BarChart3 },
  { key: "sources", label: "Data Sources", icon: Database },
  { key: "reports", label: "Reports", icon: FileText },
  { key: "automations", label: "Automations", icon: PlaySquare },
  { key: "tasks", label: "Tasks", icon: ClipboardList },
  { key: "memory", label: "Memory", icon: Brain },
  { key: "rules", label: "Business Rules", icon: ListChecks },
  { key: "audit", label: "Audit Logs", icon: History },
  { key: "security", label: "Security Center", icon: Shield },
  { key: "backups", label: "Backup & Restore", icon: ArchiveRestore },
  { key: "license", label: "License", icon: BadgeCheck },
  { key: "health", label: "System Health", icon: HeartPulse },
  { key: "users", label: "Users", icon: UserRound },
  { key: "models", label: "Model Settings", icon: KeyRound },
  { key: "system", label: "System Settings", icon: Settings },
];

interface SidebarProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">GT</div>
        <div>
          <strong>GyuTron</strong>
          <span>Local Agent</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
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
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-foot">
        <ShieldCheck size={18} />
        <div>
          <strong>Local-first</strong>
          <span>Data, reports, rules, and memories stay on this machine by default.</span>
        </div>
      </div>
    </aside>
  );
}
