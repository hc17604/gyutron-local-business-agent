import { Bot, Check, Code2, FileCode2, Loader2, MessagesSquare, Send, ShieldCheck, Sparkles, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { applyPatch, getWorkspaceTree, proposePatch, sendAgentMessage } from "../../api/client";
import type { AgentMode, PatchProposalResponse, WorkspaceNode } from "../../types/api";
import { CommandButton } from "../common/CommandButton";
import { ErrorState } from "../common/ErrorState";
import { AgentMessage } from "./AgentMessage";

const businessPromptKeys = [
  "agentChat.quick.generateOwnerReport",
  "agentChat.quick.createDailyAutomation",
  "agentChat.quick.scanLocalFolder",
  "agentChat.quick.generateLatestSyncedReport",
  "agentChat.quick.checkOpenAlerts",
  "agentChat.quick.summarizeAutomationRuns",
  "agentChat.quick.analyzeAlibaba",
  "agentChat.quick.findOverdueFollowups",
  "agentChat.quick.summarizeProductOpportunities",
];

const engineeringPromptKeys = [
  "agentChat.quick.improveChatPage",
  "agentChat.quick.reviewFrontendArchitecture",
  "agentChat.quick.addDashboardCard",
  "agentChat.quick.makeEnterpriseUi",
  "agentChat.quick.findUnusedComponents",
  "agentChat.quick.proposeRefactorPlan",
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
  const { i18n, t } = useTranslation();
  const [mode, setMode] = useState<AgentMode>("business");
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<LocalMessage[]>([
    {
      role: "agent",
      title: t("agentChat.ownerReportSummary"),
      content: t("agentChat.ownerReportIntro"),
      meta: t("agentChat.configureModelFirst"),
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

  useEffect(() => {
    if (conversationId) {
      return;
    }
    setMessages([
      {
        role: "agent",
        title: t("agentChat.ownerReportSummary"),
        content: t("agentChat.ownerReportIntro"),
        meta: t("agentChat.configureModelFirst"),
        tools: ["llm.chat", "workspace_tree_tool", "patch_proposal_tool"],
      },
    ]);
  }, [conversationId, i18n.language, t]);

  const fileOptions = useMemo(() => flattenFiles(workspaceTree ?? { name: "", path: "", type: "directory", children: [] }).slice(0, 80), [workspaceTree]);
  const promptKeys = mode === "engineering" ? engineeringPromptKeys : [...businessPromptKeys, "agentChat.quick.checkMarketRisks", "agentChat.quick.suggestBusinessRules"];

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
        language: i18n.language,
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
          title: mode === "engineering" ? t("agentChat.engineeringAgentTitle") : t("agentChat.businessAgentTitle"),
          content: response.answer,
          tools: response.tools_called,
          dataSources: response.data_sources_used,
        },
      ]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("agentChat.requestFailed"));
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
      setError(caught instanceof Error ? caught.message : t("agentChat.patchProposalFailed"));
    } finally {
      setIsProposing(false);
    }
  }

  async function handleApplyPatch() {
    if (!proposal) {
      return;
    }
    const confirmed = window.confirm(t("agentChat.applyPatchConfirm"));
    if (!confirmed) {
      return;
    }
    try {
      await applyPatch(proposal.proposal_id);
      setMessages((current) => [
        ...current,
        {
          role: "agent",
          title: t("agentChat.patchApplied"),
          content: t("agentChat.patchAppliedContent", { count: proposal.changes.length }),
          tools: ["patch_apply_tool"],
        },
      ]);
      setProposal(undefined);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("agentChat.patchProposalFailed"));
    }
  }

  return (
    <section className="chat-panel">
      <div className="agent-command-center">
        <div>
          <p className="eyebrow">{t("agentChat.commandCenter")}</p>
          <h2>{t("agentChat.localBusinessAgentConsole")}</h2>
          <p>{t("agentChat.consoleDescription")}</p>
        </div>
        <span><ShieldCheck size={15} /> {t("agentChat.readFirstMode")}</span>
      </div>
      <div className="agent-toolbar">
        <div className="segmented-control" aria-label={t("agentChat.title")}>
          {(["business", "engineering", "mixed"] as AgentMode[]).map((item) => (
            <button className={mode === item ? "active" : ""} key={item} onClick={() => setMode(item)} type="button">
              {item === "business" ? <Bot size={15} /> : <Code2 size={15} />}
              {item === "business" ? t("agentChat.businessAgent") : item === "engineering" ? t("agentChat.engineeringAgent") : t("agentChat.mixed")}
            </button>
          ))}
        </div>
      </div>

      <div className="prompt-row">
        {promptKeys.map((promptKey) => {
          const prompt = t(promptKey);
          return (
            <CommandButton
              icon={promptKey.includes("Report") || promptKey.includes("report") ? Sparkles : promptKey.includes("Folder") || promptKey.includes("folder") ? FileCode2 : MessagesSquare}
              key={promptKey}
              label={prompt}
              onClick={() => setInput(prompt)}
            />
          );
        })}
      </div>

      <div className="workspace-picker">
        <strong>{t("agentChat.projectFiles")}</strong>
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
        {isSending ? (
          <div className="agent-thinking">
            <Loader2 size={16} />
            <span>{t("agentChat.agentThinking")}</span>
          </div>
        ) : null}
        {error ? <ErrorState message={error} /> : null}
      </div>

      {proposal ? (
        <div className="diff-panel">
          <div className="panel-heading">
            <div>
              <h2>{proposal.summary}</h2>
              <span>{t("agentChat.risk")}: {proposal.risk_level}. {t("agentChat.requiresConfirmation")}</span>
            </div>
            <div className="page-header-actions">
              <button className="button secondary" onClick={() => setProposal(undefined)} type="button">
                <X size={16} />
                {t("common.reject")}
              </button>
              <button className="button primary" onClick={handleApplyPatch} type="button">
                <Check size={16} />
                {t("common.applyChanges")}
              </button>
            </div>
          </div>
          {proposal.changes.map((change) => (
            <article key={change.path}>
              <strong>{change.path}</strong>
              <p className="muted">{change.explanation}</p>
              <pre>{change.diff || t("agentChat.noTextualDiff")}</pre>
            </article>
          ))}
        </div>
      ) : null}

      <div className="composer">
        <input
          aria-label={t("agentChat.inputPlaceholder")}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") void handleSend();
          }}
          placeholder={t("agentChat.inputPlaceholder")}
          value={input}
        />
        {mode !== "business" ? (
          <button className="button secondary" disabled={isProposing || !selectedProjectPaths.length} onClick={handleProposePatch} type="button">
            {isProposing ? <Loader2 size={16} /> : <FileCode2 size={16} />}
            {t("agentChat.proposePatch")}
          </button>
        ) : null}
        <button className="button primary" disabled={isSending} onClick={() => void handleSend()} type="button">
          {isSending ? <Loader2 size={16} /> : <Send size={16} />}
          {t("common.send")}
        </button>
      </div>
    </section>
  );
}
