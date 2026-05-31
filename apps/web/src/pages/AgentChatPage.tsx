import { useState } from "react";

import { AgentChat } from "../components/agent/AgentChat";
import { ContextPanel } from "../components/agent/ContextPanel";
import { PageHeader } from "../components/common/PageHeader";

export function AgentChatPage() {
  const [selectedProjectPaths, setSelectedProjectPaths] = useState<string[]>([]);
  const [workspaceRoot, setWorkspaceRoot] = useState<string>();
  const [latestTools, setLatestTools] = useState<string[]>([]);

  return (
    <div className="page-stack">
      <PageHeader
        description="Ask the local business agent to analyze uploaded files, business rules, local memories, and report history."
        eyebrow="Command center"
        title="Local business agent"
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
