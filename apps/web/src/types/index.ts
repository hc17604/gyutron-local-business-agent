import type { LucideIcon } from "lucide-react";

export type PageKey =
  | "overview"
  | "agent"
  | "ecommerce"
  | "sources"
  | "reports"
  | "automations"
  | "tasks"
  | "memory"
  | "rules"
  | "audit"
  | "security"
  | "backups"
  | "license"
  | "health"
  | "users"
  | "models"
  | "system";

export type StatusTone = "neutral" | "success" | "warning" | "risk" | "info";

export interface NavigationItem {
  key: PageKey;
  label: string;
  icon: LucideIcon;
}

export interface Metric {
  label: string;
  value: string;
  delta: string;
  tone: StatusTone;
}

export interface PlatformPerformance {
  platform: string;
  revenue: string;
  orders: number;
  inquiries: number;
  conversion: string;
  trend: string;
  tone: StatusTone;
}

export interface AlertItem {
  title: string;
  summary: string;
  severity: "Low" | "Medium" | "High";
}

export interface ActionItem {
  title: string;
  owner: string;
  due: string;
  priority: "Normal" | "High";
}

export interface AgentMessage {
  role: "agent" | "user";
  title?: string;
  content: string;
  meta?: string;
}

export interface DataSourceRecord {
  fileName: string;
  dataType: string;
  platform: string;
  rows: number;
  uploadedAt: string;
  mappingStatus: "Mapped" | "Needs review" | "Coming soon";
}

export interface ReportRecord {
  title: string;
  type: string;
  sourceFiles: string;
  createdAt: string;
  status: "Ready" | "Draft" | "Failed";
}

export interface TaskRecord {
  title: string;
  mode: string;
  status: "Pending" | "Running" | "Completed" | "Failed" | "Cancelled";
  createdAt: string;
  completedAt: string;
  result: string;
}

export interface MemoryRecord {
  title: string;
  type: string;
  tags: string[];
  preview: string;
  createdAt: string;
  status: "Active" | "Disabled";
}

export interface BusinessRuleRecord {
  title: string;
  category: string;
  description: string;
  status: "Active" | "Disabled";
}

export interface AuditLogRecord {
  time: string;
  actor: string;
  action: string;
  target: string;
  risk: "Low" | "Medium" | "High";
  summary: string;
}
