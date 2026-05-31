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
