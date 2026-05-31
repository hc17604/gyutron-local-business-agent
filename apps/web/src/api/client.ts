import type {
  AgentChatResponse,
  AgentMode,
  HealthResponse,
  ModelProvider,
  ModelSettingsResponse,
  PatchProposalResponse,
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
