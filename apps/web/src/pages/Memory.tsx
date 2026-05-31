import { Search } from "lucide-react";

import { PageHeader } from "../components/common/PageHeader";
import { MemoryList } from "../components/memory/MemoryList";

const categories = ["Business Rules", "Report Summaries", "Field Mappings", "User Preferences", "Product Notes", "Customer Notes"];

export function Memory() {
  return (
    <div className="page-stack">
      <PageHeader
        description="Review local business memory used by reports and agent reasoning."
        eyebrow="Local knowledge"
        title="Memory"
      />
      <section className="toolbar-panel">
        <div className="search-box">
          <Search size={16} />
          <input aria-label="Search memory" placeholder="Search local memory..." />
        </div>
        <div className="prompt-row">
          {categories.map((category) => (
            <button className="chip-button" key={category} type="button">
              {category}
            </button>
          ))}
        </div>
      </section>
      <MemoryList />
    </div>
  );
}
