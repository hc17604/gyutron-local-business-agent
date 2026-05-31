import { Send } from "lucide-react";

import { agentMessages } from "../../data/mockDashboard";
import { AgentMessage } from "./AgentMessage";

const prompts = [
  "Generate today's owner report",
  "Analyze latest Alibaba inquiries",
  "Find overdue follow-ups",
  "Summarize product opportunities",
  "Check market risks",
  "Suggest business rules",
];

export function AgentChat() {
  return (
    <section className="chat-panel">
      <div className="prompt-row">
        {prompts.map((prompt) => (
          <button className="chip-button" key={prompt} type="button">
            {prompt}
          </button>
        ))}
      </div>
      <div className="message-list">
        {agentMessages.map((message, index) => (
          <AgentMessage key={`${message.role}-${index}`} message={message} />
        ))}
      </div>
      <div className="composer">
        <input aria-label="Agent instruction" placeholder="Ask the local business agent to analyze files, rules, reports, or follow-ups..." />
        <button className="button primary" type="button">
          <Send size={16} />
          Send
        </button>
      </div>
    </section>
  );
}
