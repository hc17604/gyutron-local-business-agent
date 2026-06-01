import { Search } from "lucide-react";
import { useTranslation } from "react-i18next";

import { PageHeader } from "../components/common/PageHeader";
import { MemoryList } from "../components/memory/MemoryList";

const categoryKeys = ["memory.businessRules", "memory.reportSummaries", "memory.fieldMappings", "memory.userPreferences", "memory.productNotes", "memory.customerNotes"];

export function Memory() {
  const { t } = useTranslation();
  return (
    <div className="page-stack">
      <PageHeader
        description={t("memory.description")}
        eyebrow={t("memory.eyebrow")}
        title={t("memory.title")}
      />
      <section className="toolbar-panel">
        <div className="search-box">
          <Search size={16} />
          <input aria-label={t("memory.searchPlaceholder")} placeholder={t("memory.searchPlaceholder")} />
        </div>
        <div className="prompt-row">
          {categoryKeys.map((categoryKey) => (
            <button className="chip-button" key={categoryKey} type="button">
              {t(categoryKey)}
            </button>
          ))}
        </div>
      </section>
      <MemoryList />
    </div>
  );
}
