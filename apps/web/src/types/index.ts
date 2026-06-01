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
  labelKey: string;
  value: string;
  delta: string;
  deltaKey?: string;
  deltaParams?: Record<string, string | number>;
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
  titleKey: string;
  summaryKey: string;
  summaryParams?: Record<string, string | number>;
  severity: "low" | "medium" | "high";
}

export interface ActionItem {
  titleKey: string;
  ownerKey: string;
  dueKey: string;
  priority: "normal" | "high";
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
  mappingStatus: "mapped" | "needs_review" | "coming_soon";
}

export interface ReportRecord {
  titleKey: string;
  type: string;
  sourceFiles: string;
  createdAt: string;
  status: "ready" | "draft" | "failed";
}

export interface TaskRecord {
  titleKey: string;
  mode: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  createdAt: string;
  completedAt: string;
  resultKey: string;
}

export interface MemoryRecord {
  titleKey: string;
  type: string;
  tags: string[];
  previewKey: string;
  createdAt: string;
  status: "active" | "disabled";
}

export interface BusinessRuleRecord {
  titleKey: string;
  category: string;
  descriptionKey: string;
  status: "active" | "disabled";
}

export interface AuditLogRecord {
  time: string;
  actor: string;
  action: string;
  target: string;
  risk: "low" | "medium" | "high";
  summary: string;
}
