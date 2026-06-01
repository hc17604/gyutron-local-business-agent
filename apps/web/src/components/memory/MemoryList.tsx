import { useTranslation } from "react-i18next";

import { memories } from "../../data/mockDashboard";
import { StatusBadge } from "../common/StatusBadge";

export function MemoryList() {
  const { t } = useTranslation();

  return (
    <div className="list-stack">
      {memories.map((memory) => (
        <article className="memory-card" key={memory.title}>
          <div>
            <strong>{memory.title}</strong>
            <p>{memory.preview}</p>
            <div className="tag-row">
              {memory.tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>
          </div>
          <div className="memory-meta">
            <span>{memory.type}</span>
            <span>{memory.createdAt}</span>
            <StatusBadge label={memory.status === "Active" ? t("common.active") : memory.status} tone={memory.status === "Active" ? "success" : "neutral"} />
          </div>
        </article>
      ))}
    </div>
  );
}
