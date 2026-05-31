import { Plus } from "lucide-react";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { businessRules } from "../data/mockDashboard";

export function BusinessRules() {
  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" type="button">
            <Plus size={16} />
            New Rule
          </button>
        }
        description="Maintain natural-language business rules that affect prioritization and report generation."
        eyebrow="Configurable local rules"
        title="Business Rules"
      />
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Rule</th>
                <th>Category</th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {businessRules.map((rule) => (
                <tr key={rule.title}>
                  <td>{rule.title}</td>
                  <td>{rule.category}</td>
                  <td>{rule.description}</td>
                  <td>
                    <StatusBadge label={rule.status} tone={rule.status === "Active" ? "success" : "neutral"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
