import type { AgentMessage as AgentMessageType } from "../../types";

interface AgentMessageProps {
  message: AgentMessageType;
}

export function AgentMessage({ message }: AgentMessageProps) {
  return (
    <article className={`agent-message ${message.role}`}>
      {message.title ? <strong>{message.title}</strong> : null}
      <p>{message.content}</p>
      {message.meta ? <small>{message.meta}</small> : null}
    </article>
  );
}
