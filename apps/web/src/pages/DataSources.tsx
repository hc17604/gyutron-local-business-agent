import { FolderPlus, PlugZap, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { createConnector, getConnectors, syncConnector, testConnector } from "../api/client";
import { EmptyState } from "../components/common/EmptyState";
import { PageHeader } from "../components/common/PageHeader";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { ConnectorCatalogItem, DataConnector } from "../types/api";

const defaultFolder = "D:\\Codex\\gyutron-local-business-agent\\data\\imports";

export function DataSources() {
  const [catalog, setCatalog] = useState<ConnectorCatalogItem[]>([]);
  const [connectors, setConnectors] = useState<DataConnector[]>([]);
  const [folderPath, setFolderPath] = useState(defaultFolder);
  const [message, setMessage] = useState<string>();

  async function refresh() {
    const response = await getConnectors();
    setCatalog(response.catalog);
    setConnectors(response.connectors);
  }

  useEffect(() => {
    refresh().catch((error: Error) => setMessage(error.message));
  }, []);

  async function handleAddLocalFolder() {
    const connector = await createConnector({
      connector_type: "local_folder",
      name: "Local imports",
      description: "Scans local Excel and CSV exports.",
      config_json: { folder_path: folderPath, data_type: "order", platform_label: "Local folder", scan_interval: "manual" },
    });
    setConnectors((current) => [connector, ...current]);
    setMessage("Local Folder connector created.");
  }

  async function handleTest(id: number) {
    const result = await testConnector(id);
    setMessage(result.message);
  }

  async function handleSync(id: number) {
    const result = await syncConnector(id);
    setMessage(result.summary);
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" onClick={handleAddLocalFolder} type="button">
            <FolderPlus size={16} />
            Add Local Folder
          </button>
        }
        description="Manage local-first data connectors. Platform connectors are placeholders until real API integrations are intentionally added."
        eyebrow="Connector center"
        title="Data sources"
      />

      <section className="panel">
        <SectionHeader title="Create local folder connector" description="Use a watched local folder for Alibaba, ERP, Shopee, Amazon, or Shopify exports." meta="Local only" />
        <label>
          Folder path
          <input onChange={(event) => setFolderPath(event.target.value)} value={folderPath} />
        </label>
        {message ? <div className="inline-info">{message}</div> : null}
      </section>

      <section className="source-grid">
        {catalog.map((source) => (
          <article className="source-card" key={source.connector_id}>
            <strong>{source.name}</strong>
            <p className="muted">{source.description}</p>
            <StatusBadge label={source.status === "available" ? "Available" : "Mock / Coming soon"} tone={source.status === "available" ? "success" : "neutral"} />
          </article>
        ))}
      </section>

      <section className="panel">
        <SectionHeader title="Configured connectors" description="Sync jobs and imported file records are stored in the local SQLite database." />
        {connectors.length ? <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Last sync</th>
                <th>Last result</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {connectors.map((connector) => (
                <tr key={connector.id}>
                  <td>{connector.name}</td>
                  <td>{connector.connector_type}</td>
                  <td>
                    <StatusBadge label={connector.status} tone={connector.status === "active" ? "success" : "warning"} />
                  </td>
                  <td>{connector.last_sync_at ?? "-"}</td>
                  <td>{connector.last_sync_status ?? "-"}</td>
                  <td>
                    <div className="table-actions">
                      <button className="table-action" onClick={() => void handleTest(connector.id)} type="button">
                        <PlugZap size={14} />
                        Test
                      </button>
                      <button className="table-action" onClick={() => void handleSync(connector.id)} type="button">
                        <RefreshCw size={14} />
                        Sync
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div> : <EmptyState title="No connectors configured" description="Create a Local Folder connector to import the first Excel or CSV export." />}
      </section>
    </div>
  );
}
