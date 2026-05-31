import { useEffect, useState } from "react";

import { createBackup, getBackups } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import type { BackupRecord } from "../types/api";

export function BackupRestore() {
  const [backups, setBackups] = useState<BackupRecord[]>([]);
  const [message, setMessage] = useState<string>();

  async function refresh() {
    const response = await getBackups();
    setBackups(response.backups);
  }

  useEffect(() => {
    refresh().catch((error: Error) => setMessage(error.message));
  }, []);

  async function backup() {
    const result = await createBackup(false);
    setMessage(`Backup created: ${result.filename}`);
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader title="Backup & Restore" eyebrow="Local recovery" description="Create local recoverable snapshots. Restore is owner-only and requires confirmation through the API." actions={<button className="button primary" onClick={backup} type="button">Create Backup</button>} />
      {message ? <div className="inline-info">{message}</div> : null}
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Filename</th><th>Size</th><th>Uploads</th><th>Status</th><th>Created</th></tr></thead>
            <tbody>{backups.map((item) => <tr key={item.id}><td>{item.filename}</td><td>{item.size}</td><td>{item.include_uploads ? "included" : "excluded"}</td><td>{item.status}</td><td>{item.created_at}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
