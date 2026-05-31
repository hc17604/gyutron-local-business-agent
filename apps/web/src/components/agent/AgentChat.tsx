import { Bot, Check, Code2, FileCode2, Loader2, Send, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { applyPatch, getWorkspaceTree, proposePatch, sendAgentMessage } from "../../api/client";
import type { AgentMode, PatchProposalResponse, WorkspaceNode } from "../../types/api";
import { AgentMessage } from "./AgentMessage";

const businessPrompts = [
  "Generate today's owner report",
  "Analyze latest Alibaba inquiries",
  "Find overdue follow-ups",
  "Summarize product opportunities",
];

const engineeringPrompts = [
  "Improve this Agent Chat page",
  "Review frontend architecture",
  "Add a new dashboard card",
  "Make UI more enterprise-grade",
  "Find unused components",
  "Propose refactor plan",
];

interface LocalMessage {
  role: "agent" | "user";
  title?: string;
  content: string;
  meta?: string;
  tools?: string[];
  dataSources?: string[];
}

interface AgentChatProps {
  selectedProjectPaths: string[];
  onSelectedProjectPathsChange: (paths: string[]) => void;
  onWorkspaceRootChange: (root: string) => void;
  onToolsChange: (tools: string[]) => void;
}

function flattenFiles(node: WorkspaceNode): WorkspaceNode[] {
  if (node.type === "file") {
    return [node];
  }
  return (node.children ?? []).flatMap(flattenFiles);
}

export function AgentChat({
  selectedProjectPaths,
  onSelectedProjectPathsChange,
  onWorkspaceRootChange,
  onToolsChange,
}: AgentChatProps) {
  const [mode, setMode] = useState<AgentMode>("business");
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<LocalMessage[]>([
    {
      role: "agent",
      title: "Owner report summary",
      content:
        "I can now call your configured model and, in engineering mode, use selected project files as local context before proposing changes.",
      meta: "Configure a model first, then send a message.",
      tools: ["llm.chat", "workspace_tree_tool", "patch_proposal_tool"],
    },
  ]);
  const [workspaceTree, setWorkspaceTree] = useState<WorkspaceNode>();
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string>();
  const [proposal, setProposal] = useState<PatchProposalResponse>();
  const [isProposing, setIsProposing] = useState(false);

  useEffect(() => {
    getWorkspaceTree()
      .then((response) => {
        setWorkspaceTree(response.tree);
        onWorkspaceRootChange(response.root);
      })
      .catch((caught: Error) => setError(caught.message));
  }, [onWorkspaceRootChange]);

  const fileOptions = useMemo(() => flattenFiles(workspaceTree ?? { name: "", path: "", type: "directory", children: [] }).slice(0, 80), [workspaceTree]);
  const prompts = mode === "engineering" ? engineeringPrompts : [...businessPrompts, "Check market risks", "Suggest business rules"];

  function toggleProjectFile(path: string) {
    const next = selectedProjectPaths.includes(path)
      ? selectedProjectPaths.filter((item) => item !== path)
      : [...selectedProjectPaths, path].slice(0, 8);
    onSelectedProjectPathsChange(next);
  }

  async function handleSend(message = input) {
    const trimmed = message.trim();
    if (!trimmed || isSending) {
      return;
    }
    setError(undefined);
    setInput("");
    setIsSending(true);
    setMessages((current) => [...current, { role: "user", content: trimmed }]);

    try {
      const response = await sendAgentMessage({
        message: trimmed,
        mode,
        conversation_id: conversationId,
        context: {
          selected_file_ids: [],
          selected_project_paths: selectedProjectPaths,
          use_memory: true,
          use_business_rules: true,
        },
      });
      setConversationId(response.conversation_id);
      onToolsChange(response.tools_called);
      setMessages((current) => [
        ...current,
        {
          role: "agent",
          title: mode === "engineering" ? "Engineering agent" : "Business agent",
          content: response.answer,
          tools: response.tools_called,
          dataSources: response.data_sources_used,
        },
      ]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Agent request failed.");
    } finally {
      setIsSending(false);
    }
  }

  async function handleProposePatch() {
    if (!input.trim() || isProposing) {
      return;
    }
    setError(undefined);
    setProposal(undefined);
    setIsProposing(true);
    try {
      const response = await proposePatch({ instruction: input, selected_paths: selectedProjectPaths });
      setProposal(response);
      onToolsChange(["patch_proposal_tool"]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Patch proposal failed.");
    } finally {
      setIsProposing(false);
    }
  }

  async function handleApplyPatch() {
    if (!proposal) {
      return;
    }
    const confirmed = window.confirm("Apply this patch to local files? A rollback record will be saved.");
    if (!confirmed) {
      return;
    }
    try {
      await applyPatch(proposal.proposal_id);
      setMessages((current) => [
        ...current,
        {
          role: "agent",
          title: "Patch applied",
          content: `${proposal.changes.length} file change(s) were written locally and recorded for rollback.`,
          tools: ["patch_apply_tool"],
        },
      ]);
      setProposal(undefined);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Apply patch failed.");
    }
  }

  return (
    <section className="chat-panel">
      <div className="agent-toolbar">
        <div className="segmented-control" aria-label="Agent mode">
          {(["business", "engineering", "mixed"] as AgentMode[]).map((item) => (
            <button className={mode === item ? "active" : ""} key={item} onClick={() => setMode(item)} type="button">
              {item === "business" ? <Bot size={15} /> : <Code2 size={15} />}
              {item === "business" ? "Business Agent" : item === "engineering" ? "Engineering Agent" : "Mixed"}
            </button>
          ))}
        </div>
      </div>

      <div className="prompt-row">
        {prompts.map((prompt) => (
          <button className="chip-button" key={prompt} onClick={() => setInput(prompt)} type="button">
            {prompt}
          </button>
        ))}
      </div>

      <div className="workspace-picker">
        <strong>Project files</strong>
        <div>
          {fileOptions.slice(0, 18).map((file) => (
            <button
              className={selectedProjectPaths.includes(file.path) ? "chip-button active" : "chip-button"}
              key={file.path}
              onClick={() => toggleProjectFile(file.path)}
              type="button"
            >
              <FileCode2 size={14} />
              {file.path}
            </button>
          ))}
        </div>
      </div>

      <div className="message-list">
        {messages.map((message, index) => (
          <AgentMessage key={`${message.role}-${index}-${message.content.slice(0, 12)}`} message={message} />
        ))}
        {error ? <div className="inline-error">{error}</div> : null}
      </div>

      {proposal ? (
        <div className="diff-panel">
          <div className="panel-heading">
            <div>
              <h2>{proposal.summary}</h2>
              <span>Risk: {proposal.risk_level}. Requires confirmation before writing files.</span>
            </div>
            <div className="page-header-actions">
              <button className="button secondary" onClick={() => setProposal(undefined)} type="button">
                <X size={16} />
                Reject
              </button>
              <button className="button primary" onClick={handleApplyPatch} type="button">
                <Check size={16} />
                Apply Changes
              </button>
            </div>
          </div>
          {proposal.changes.map((change) => (
            <article key={change.path}>
              <strong>{change.path}</strong>
              <p className="muted">{change.explanation}</p>
              <pre>{change.diff || "No textual diff returned."}</pre>
            </article>
          ))}
        </div>
      ) : null}

      <div className="composer">
        <input
          aria-label="Agent instruction"
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") void handleSend();
          }}
          placeholder="Ask the local agent, use @file references, or request an engineering patch..."
          value={input}
        />
        {mode !== "business" ? (
          <button className="button secondary" disabled={isProposing || !selectedProjectPaths.length} onClick={handleProposePatch} type="button">
            {isProposing ? <Loader2 size={16} /> : <FileCode2 size={16} />}
            Propose Patch
          </button>
        ) : null}
        <button className="button primary" disabled={isSending} onClick={() => void handleSend()} type="button">
          {isSending ? <Loader2 size={16} /> : <Send size={16} />}
          Send
        </button>
      </div>
    </section>
  );
}
