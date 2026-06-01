import { useTranslation } from "react-i18next";

interface AgentMessageProps {
  message: {
    role: "agent" | "user";
    title?: string;
    content: string;
    meta?: string;
    tools?: string[];
    dataSources?: string[];
  };
}

export function AgentMessage({ message }: AgentMessageProps) {
  const { t } = useTranslation();
  return (
    <article className={`agent-message ${message.role}`}>
      <div className="message-title-row">
        {message.title ? <strong>{message.title}</strong> : <strong>{message.role === "agent" ? t("agentChat.agent") : t("agentChat.you")}</strong>}
        <span>{message.role === "agent" ? t("agentChat.localAgent") : t("agentChat.request")}</span>
      </div>
      <p>{message.content}</p>
      {(message.tools?.length || message.dataSources?.length || message.meta) ? (
        <div className="message-meta-grid">
          {message.tools?.length ? <small>{t("agentChat.toolsCalled")}: {message.tools.join(", ")}</small> : null}
          {message.dataSources?.length ? <small>{t("agentChat.sources")}: {message.dataSources.join(", ")}</small> : null}
          {message.meta ? <small>{message.meta}</small> : null}
        </div>
      ) : null}
    </article>
  );
}
