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
  return (
    <article className={`agent-message ${message.role}`}>
      <div className="message-title-row">
        {message.title ? <strong>{message.title}</strong> : <strong>{message.role === "agent" ? "Agent" : "You"}</strong>}
        <span>{message.role === "agent" ? "local agent" : "request"}</span>
      </div>
      <p>{message.content}</p>
      {(message.tools?.length || message.dataSources?.length || message.meta) ? (
        <div className="message-meta-grid">
          {message.tools?.length ? <small>Tools: {message.tools.join(", ")}</small> : null}
          {message.dataSources?.length ? <small>Sources: {message.dataSources.join(", ")}</small> : null}
          {message.meta ? <small>{message.meta}</small> : null}
        </div>
      ) : null}
    </article>
  );
}
