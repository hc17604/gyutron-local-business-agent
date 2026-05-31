import type {
  AgentChatResponse,
  AgentMode,
  AutomationRule,
  ConnectorCatalogItem,
  DataConnector,
  HealthResponse,
  LocalAlert,
  LocalReport,
  ModelProvider,
  ModelSettingsResponse,
  OverviewResponse,
  PatchProposalResponse,
  SyncJob,
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
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
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

export function getReports(): Promise<{ reports: LocalReport[] }> {
  return request<{ reports: LocalReport[] }>("/reports");
}

export function generateOwnerReport(): Promise<{ report_id: number; title: string; summary: string }> {
  return request<{ report_id: number; title: string; summary: string }>("/reports/generate-owner-report", { method: "POST" });
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
