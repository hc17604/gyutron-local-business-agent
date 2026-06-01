import { useTranslation } from "react-i18next";

import { memories } from "../../data/mockDashboard";
import { formatDataType, formatStatus } from "../../i18n/formatters";
import { StatusBadge } from "../common/StatusBadge";

export function MemoryList() {
  const { t } = useTranslation();

  return (
    <div className="list-stack">
      {memories.map((memory) => (
        <article className="memory-card" key={memory.titleKey}>
          <div>
            <strong>{t(memory.titleKey)}</strong>
            <p>{t(memory.previewKey)}</p>
            <div className="tag-row">
              {memory.tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>
          </div>
          <div className="memory-meta">
            <span>{formatDataType(memory.type, t)}</span>
            <span>{memory.createdAt}</span>
            <StatusBadge label={formatStatus(memory.status, t)} tone={memory.status === "active" ? "success" : "neutral"} />
          </div>
        </article>
      ))}
    </div>
  );
}
