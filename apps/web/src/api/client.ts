import type {
  AgentChatResponse,
  CustomerInfo,
  AgentMode,
  AgentTask,
  AuditLog,
  BusinessRuleInfo,
  AuthResponse,
  AuthUser,
  AutomationRule,
  BackupRecord,
  ConnectorCatalogItem,
  DataConnector,
  HealthResponse,
  LocalAlert,
  LocalReport,
  LicenseInfo,
  ModelProvider,
  ModelSettingsResponse,
  OverviewResponse,
  PatchProposalResponse,
  SyncJob,
  SetupStatus,
  SystemHealth,
  WorkspaceTreeResponse,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = window.localStorage.getItem("gyutron_session_token");
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(token ? { "X-Session-Token": token } : {}), ...(options?.headers ?? {}) },
    ...options,
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // Keep HTTP status text when the response is not JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

export function getSetupStatus(): Promise<SetupStatus> {
  return request<SetupStatus>("/setup/status");
}

export function finishSetup(payload: Record<string, unknown>): Promise<AuthResponse> {
  return request<AuthResponse>("/setup/finish", { method: "POST", body: JSON.stringify(payload) });
}

export function login(payload: { email: string; password: string }): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function getMe(): Promise<{ user: AuthUser }> {
  return request<{ user: AuthUser }>("/auth/me");
}

export function getModelSettings(): Promise<ModelSettingsResponse> {
  return request<ModelSettingsResponse>("/settings/model");
}

export function saveModelSettings(payload: Partial<ModelSettingsResponse>): Promise<ModelSettingsResponse> {
  return request<ModelSettingsResponse>("/settings/model", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function testModelSettings(payload: Partial<ModelSettingsResponse>) {
  return request<{ status: string; reply: string }>("/settings/model/test", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getModelProviders(): Promise<{ providers: ModelProvider[] }> {
  return request<{ providers: ModelProvider[] }>("/settings/model/providers");
}

export function sendAgentMessage(payload: {
  message: string;
  mode: AgentMode;
  language?: string;
  conversation_id?: string;
  context: {
    selected_file_ids: string[];
    selected_project_paths: string[];
    use_memory: boolean;
    use_business_rules: boolean;
  };
}): Promise<AgentChatResponse> {
  return request<AgentChatResponse>("/agent/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getWorkspaceTree(): Promise<WorkspaceTreeResponse> {
  return request<WorkspaceTreeResponse>("/workspace/tree");
}

export function proposePatch(payload: {
  instruction: string;
  selected_paths: string[];
  additional_context?: string;
}): Promise<PatchProposalResponse> {
  return request<PatchProposalResponse>("/agent/engineering/propose-patch", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function applyPatch(proposalId: string): Promise<{ status: string }> {
  return request<{ status: string }>("/agent/engineering/apply-patch", {
    method: "POST",
    body: JSON.stringify({ proposal_id: proposalId, confirmed: true }),
  });
}

export function getConnectors(): Promise<{ connectors: DataConnector[]; catalog: ConnectorCatalogItem[] }> {
  return request<{ connectors: DataConnector[]; catalog: ConnectorCatalogItem[] }>("/connectors");
}

export function createConnector(payload: {
  connector_type: string;
  name: string;
  description?: string;
  config_json: Record<string, unknown>;
}): Promise<DataConnector> {
  return request<DataConnector>("/connectors", { method: "POST", body: JSON.stringify(payload) });
}

export function testConnector(connectorId: number): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>(`/connectors/${connectorId}/test`, { method: "POST" });
}

export function syncConnector(connectorId: number): Promise<{ status: string; summary: string; records_found: number; records_imported: number }> {
  return request<{ status: string; summary: string; records_found: number; records_imported: number }>(`/connectors/${connectorId}/sync`, { method: "POST" });
}

export function getSyncJobs(connectorId: number): Promise<{ sync_jobs: SyncJob[] }> {
  return request<{ sync_jobs: SyncJob[] }>(`/connectors/${connectorId}/sync-jobs`);
}

export function getAutomations(): Promise<{ automations: AutomationRule[] }> {
  return request<{ automations: AutomationRule[] }>("/automations");
}

export function createAutomation(payload: {
  name: string;
  description?: string;
  trigger_type: string;
  schedule_cron?: string;
  action_type: string;
  action_config_json: Record<string, unknown>;
}): Promise<AutomationRule> {
  return request<AutomationRule>("/automations", { method: "POST", body: JSON.stringify(payload) });
}

export function runAutomation(id: number): Promise<{ status: string; summary?: string; report_id?: number }> {
  return request<{ status: string; summary?: string; report_id?: number }>(`/automations/${id}/run`, { method: "POST" });
}

export function pauseAutomation(id: number): Promise<AutomationRule> {
  return request<AutomationRule>(`/automations/${id}/pause`, { method: "POST" });
}

export function resumeAutomation(id: number): Promise<AutomationRule> {
  return request<AutomationRule>(`/automations/${id}/resume`, { method: "POST" });
}

export function getAutomationRuns(id: number): Promise<{ runs: Array<Record<string, unknown>> }> {
  return request<{ runs: Array<Record<string, unknown>> }>(`/automations/${id}/runs`);
}

export function getReports(customerId?: string): Promise<{ reports: LocalReport[] }> {
  const qs = customerId ? `?customer_id=${encodeURIComponent(customerId)}` : "";
  return request<{ reports: LocalReport[] }>(`/reports${qs}`);
}

export function getDecisionCenter(customerId: string, language?: string): Promise<Record<string, unknown>> {
  const qs = new URLSearchParams({ customer_id: customerId });
  if (language) qs.set("language", language);
  return request<Record<string, unknown>>(`/decision-center?${qs.toString()}`);
}

export function getCustomers(): Promise<{ customers: CustomerInfo[] }> {
  return request<{ customers: CustomerInfo[] }>("/customers");
}

export function getCommerceOverview(params: { customer_id?: string; source?: string; time_range?: string }): Promise<Record<string, unknown>> {
  const qs = new URLSearchParams();
  if (params.customer_id) qs.set("customer_id", params.customer_id);
  if (params.source) qs.set("source", params.source);
  if (params.time_range) qs.set("time_range", params.time_range);
  return request<Record<string, unknown>>(`/commerce/overview?${qs.toString()}`);
}

export function generateOwnerReport(language?: string): Promise<{ report_id: number; title: string; summary: string; language?: string }> {
  return request<{ report_id: number; title: string; summary: string; language?: string }>("/reports/generate-owner-report", {
    method: "POST",
    body: JSON.stringify({ language }),
  });
}

export function generateWebsiteLeadsSummary(payload: { connector_id?: number; language?: string; time_range?: string }): Promise<{ report_id: number; title: string; summary: string; language?: string }> {
  return request<{ report_id: number; title: string; summary: string; language?: string }>("/reports/website-leads-summary", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function generateNamedReport(kind: "daily-owner" | "weekly-pipeline" | "opportunities", payload: { language?: string; connector_id?: number }): Promise<{ report_id: number; title: string; summary: string }> {
  return request<{ report_id: number; title: string; summary: string }>(`/reports/${kind}`, { method: "POST", body: JSON.stringify(payload) });
}

export function getTasks(filters?: { status?: string; priority?: string }): Promise<{ tasks: AgentTask[]; counts: Record<string, number> }> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.priority) params.set("priority", filters.priority);
  const qs = params.toString();
  return request<{ tasks: AgentTask[]; counts: Record<string, number> }>(`/tasks${qs ? `?${qs}` : ""}`);
}

export function updateTask(taskId: number, status: string): Promise<AgentTask> {
  return request<AgentTask>(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify({ status }) });
}

export function evaluateRulesNow(): Promise<{ tasks_created: number; tasks_auto_closed: number }> {
  return request<{ tasks_created: number; tasks_auto_closed: number }>("/tasks/evaluate", { method: "POST" });
}

export function getBusinessRules(): Promise<{ rules: BusinessRuleInfo[] }> {
  return request<{ rules: BusinessRuleInfo[] }>("/business-rules");
}

export function toggleBusinessRule(ruleId: string, enabled: boolean): Promise<{ rule_id: string; enabled: boolean }> {
  return request<{ rule_id: string; enabled: boolean }>(`/business-rules/${ruleId}/toggle`, { method: "POST", body: JSON.stringify({ enabled }) });
}

export function getAlerts(): Promise<{ alerts: LocalAlert[] }> {
  return request<{ alerts: LocalAlert[] }>("/alerts");
}

export function acknowledgeAlert(id: number): Promise<LocalAlert> {
  return request<LocalAlert>(`/alerts/${id}/acknowledge`, { method: "POST" });
}

export function resolveAlert(id: number): Promise<LocalAlert> {
  return request<LocalAlert>(`/alerts/${id}/resolve`, { method: "POST" });
}

export function getOverview(): Promise<OverviewResponse> {
  return request<OverviewResponse>("/overview");
}

export function getUsers(): Promise<{ users: AuthUser[] }> {
  return request<{ users: AuthUser[] }>("/users");
}

export function createUser(payload: Record<string, unknown>): Promise<AuthUser> {
  return request<AuthUser>("/users", { method: "POST", body: JSON.stringify(payload) });
}

export function getAuditLogs(): Promise<{ audit_logs: AuditLog[] }> {
  return request<{ audit_logs: AuditLog[] }>("/audit-logs");
}

export function getSecurityPolicies(): Promise<{ local_mode: Record<string, string>; policies: Array<{ key: string; value_json: Record<string, unknown> }> }> {
  return request<{ local_mode: Record<string, string>; policies: Array<{ key: string; value_json: Record<string, unknown> }> }>("/security/policies");
}

export function previewRedaction(text: string, policy?: Record<string, unknown>): Promise<{ redacted: string }> {
  return request<{ redacted: string }>("/security/redaction/preview", { method: "POST", body: JSON.stringify({ text, policy }) });
}

export function getBackups(): Promise<{ backups: BackupRecord[] }> {
  return request<{ backups: BackupRecord[] }>("/backups");
}

export function createBackup(includeUploads = false): Promise<BackupRecord> {
  return request<BackupRecord>("/backups/create", { method: "POST", body: JSON.stringify({ include_uploads: includeUploads }) });
}

export function getLicense(): Promise<LicenseInfo> {
  return request<LicenseInfo>("/license");
}

export function activateLicense(payload: Record<string, unknown>): Promise<LicenseInfo> {
  return request<LicenseInfo>("/license/activate", { method: "POST", body: JSON.stringify(payload) });
}

export function loadDemoData(): Promise<{ status: string; report: unknown }> {
  return request<{ status: string; report: unknown }>("/demo/load", { method: "POST" });
}

export function resetDemoData(): Promise<{ status: string }> {
  return request<{ status: string }>("/demo/reset", { method: "POST" });
}

export function getSystemHealth(): Promise<SystemHealth> {
  return request<SystemHealth>("/system/health");
}
