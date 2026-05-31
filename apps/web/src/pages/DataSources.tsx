import { Upload } from "lucide-react";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { dataSources } from "../data/mockDashboard";

const sourceTypes = ["Excel / CSV", "Alibaba.com", "Shopee", "Amazon", "TikTok Shop", "Shopify", "ERP", "Email", "CRM"];

export function DataSources() {
  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" type="button">
            <Upload size={16} />
            Upload Data
          </button>
        }
        description="Manage local uploaded files now and reserve entries for future platform connectors."
        eyebrow="Local files and connectors"
        title="Data sources"
      />

      <section className="source-grid">
        {sourceTypes.map((source, index) => (
          <article className="source-card" key={source}>
            <strong>{source}</strong>
            <StatusBadge label={index === 0 || source === "ERP" ? "Available" : "Coming soon"} tone={index === 0 || source === "ERP" ? "success" : "neutral"} />
          </article>
        ))}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Uploaded files</h2>
          <span>Connected to local storage roadmap</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>File name</th>
                <th>Data type</th>
                <th>Platform</th>
                <th>Rows</th>
                <th>Uploaded time</th>
                <th>Mapping status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {dataSources.map((source) => (
                <tr key={source.fileName}>
                  <td>{source.fileName}</td>
                  <td>{source.dataType}</td>
                  <td>{source.platform}</td>
                  <td>{source.rows.toLocaleString()}</td>
                  <td>{source.uploadedAt}</td>
                  <td>
                    <StatusBadge label={source.mappingStatus} tone={source.mappingStatus === "Mapped" ? "success" : "warning"} />
                  </td>
                  <td>
                    <button className="table-action" type="button">
                      Review
                    </button>
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
