import { useState } from "react";
import { useTranslation } from "react-i18next";

import { AgentChat } from "../components/agent/AgentChat";
import { ContextPanel } from "../components/agent/ContextPanel";
import { PageHeader } from "../components/common/PageHeader";

export function AgentChatPage() {
  const { t } = useTranslation();
  const [selectedProjectPaths, setSelectedProjectPaths] = useState<string[]>([]);
  const [workspaceRoot, setWorkspaceRoot] = useState<string>();
  const [latestTools, setLatestTools] = useState<string[]>([]);

  return (
    <div className="page-stack">
      <PageHeader
        description={t("agentChat.description")}
        eyebrow={t("agentChat.commandCenter")}
        title={t("agentChat.localBusinessAgent")}
      />
      <div className="agent-layout">
        <AgentChat
          onSelectedProjectPathsChange={setSelectedProjectPaths}
          onToolsChange={setLatestTools}
          onWorkspaceRootChange={setWorkspaceRoot}
          selectedProjectPaths={selectedProjectPaths}
        />
        <ContextPanel latestTools={latestTools} selectedProjectPaths={selectedProjectPaths} workspaceRoot={workspaceRoot} />
      </div>
    </div>
  );
}
