export interface HealthResponse {
  status: string;
  service: string;
  data_dir: string;
  database_path: string;
}

export interface ModelSettingsResponse {
  id: number | null;
  provider: string;
  display_name: string;
  base_url: string;
  api_key: string;
  model_name: string;
  is_active: boolean;
  supports_streaming: boolean;
}

export interface ModelProvider {
  id: string;
  label: string;
  default_base_url: string;
  requires_api_key: boolean;
}

export interface AgentChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  mode: AgentMode;
  tools_called: string[];
  data_sources_used: string[];
  suggested_actions: string[];
  requires_confirmation: boolean;
}

export type AgentMode = "business" | "engineering" | "mixed";

export interface WorkspaceNode {
  name: string;
  path: string;
  type: "directory" | "file";
  size?: number;
  children?: WorkspaceNode[];
}

export interface WorkspaceTreeResponse {
  root: string;
  tree: WorkspaceNode;
}

export interface PatchProposalResponse {
  proposal_id: string;
  summary: string;
  risk_level: "low" | "medium" | "high";
  requires_confirmation: boolean;
  changes: Array<{
    path: string;
    change_type: string;
    diff: string;
    explanation: string;
  }>;
}

export interface ConnectorCatalogItem {
  connector_id: string;
  name: string;
  type: string;
  description: string;
  status: string;
  auth_type: string;
  supported_data_types: string[];
}

export interface DataConnector {
  id: number;
  connector_type: string;
  name: string;
  description?: string;
  status: string;
  config_json: Record<string, unknown>;
  last_sync_at?: string;
  last_sync_status?: string;
  created_at: string;
  updated_at: string;
}

export interface SyncJob {
  id: number;
  connector_id: number;
  status: string;
  sync_type: string;
  records_found: number;
  records_imported: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface AutomationRule {
  id: number;
  name: string;
  description?: string;
  trigger_type: string;
  schedule_cron?: string;
  action_type: string;
  action_config_json: Record<string, unknown>;
  status: "active" | "paused";
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AutomationRun {
  id: number;
  automation_rule_id: number;
  status: string;
  trigger_source: string;
  result_summary?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface LocalAlert {
  id: number;
  title: string;
  description: string;
  severity: "low" | "medium" | "high";
  status: "open" | "acknowledged" | "resolved";
  source_type?: string;
  source_id?: string;
  created_at: string;
}

export interface LocalReport {
  id: number;
  title: string;
  status: string;
  content_markdown?: string;
  summary_json?: string;
  created_at: string;
}

export interface OverviewResponse {
  latest_report: (LocalReport & { summary?: Record<string, unknown> }) | null;
  active_automations: AutomationRule[];
  recent_sync_jobs: SyncJob[];
  open_alerts: LocalAlert[];
}

export interface SetupStatus {
  is_initialized: boolean;
  company_name?: string;
  user_count: number;
}

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  role: "owner" | "admin" | "operator" | "viewer";
  is_active: number | boolean;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

export interface AuditLog {
  id: number;
  actor: string;
  action: string;
  target_type: string;
  target_id?: string;
  risk_level: string;
  input_summary?: string;
  output_summary?: string;
  created_at: string;
}

export interface BackupRecord {
  id: number;
  filename: string;
  size: number;
  include_uploads: number;
  created_by?: string;
  created_at: string;
  status: string;
}

export interface LicenseInfo {
  license_key?: string;
  customer_name?: string;
  plan: string;
  expires_at?: string;
  max_users: number;
  enabled_features: unknown;
  status: string;
}

export interface SystemHealth {
  backend: string;
  frontend: string;
  database: string;
  scheduler: string;
  last_backup?: BackupRecord | null;
  last_sync?: SyncJob | null;
  disk_usage: { total: number; used: number; free: number };
  active_automations: number;
  recent_errors: AuditLog[];
}
