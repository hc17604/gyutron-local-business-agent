import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { createBackup, getBackups } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { formatStatus } from "../i18n/formatters";
import type { BackupRecord } from "../types/api";

export function BackupRestore() {
  const { t } = useTranslation();
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
    setMessage(`${t("backup.createBackup")}: ${result.filename}`);
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader title={t("backup.title")} eyebrow={t("backup.eyebrow")} description={t("backup.description")} actions={<button className="button primary" onClick={backup} type="button">{t("backup.createBackup")}</button>} />
      {message ? <div className="inline-info">{message}</div> : null}
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead><tr><th>{t("backup.filename")}</th><th>{t("backup.size")}</th><th>{t("backup.uploads")}</th><th>{t("common.status")}</th><th>{t("backup.created")}</th></tr></thead>
            <tbody>{backups.map((item) => <tr key={item.id}><td>{item.filename}</td><td>{item.size}</td><td>{item.include_uploads ? t("status.imported") : "-"}</td><td>{formatStatus(item.status, t)}</td><td>{item.created_at}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
