import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { createUser, getUsers } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { formatStatus } from "../i18n/formatters";
import type { AuthUser } from "../types/api";

export function Users() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [message, setMessage] = useState<string>();

  async function refresh() {
    const response = await getUsers();
    setUsers(response.users);
  }

  useEffect(() => {
    refresh().catch((error: Error) => setMessage(error.message));
  }, []);

  async function addOperator() {
    await createUser({ name: "Operator", email: `operator${Date.now()}@gyutron.local`, password: "ChangeMe123!", role: "operator" });
    setMessage(t("users.addOperator"));
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader title={t("users.title")} eyebrow={t("users.eyebrow")} description={t("users.description")} actions={<button className="button primary" onClick={addOperator} type="button">{t("users.addOperator")}</button>} />
      {message ? <div className="inline-info">{message}</div> : null}
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead><tr><th>{t("users.name")}</th><th>{t("users.email")}</th><th>{t("users.role")}</th><th>{t("common.status")}</th></tr></thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>{user.role}</td>
                  <td><StatusBadge label={formatStatus(user.is_active ? "active" : "disabled", t)} tone={user.is_active ? "success" : "neutral"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
