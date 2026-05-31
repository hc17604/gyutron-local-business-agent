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
      {message.title ? <strong>{message.title}</strong> : null}
      <p>{message.content}</p>
      {message.tools?.length ? <small>Tools: {message.tools.join(", ")}</small> : null}
      {message.dataSources?.length ? <small>Sources: {message.dataSources.join(", ")}</small> : null}
      {message.meta ? <small>{message.meta}</small> : null}
    </article>
  );
}
