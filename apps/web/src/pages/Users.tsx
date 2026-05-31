import { useEffect, useState } from "react";

import { createUser, getUsers } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { AuthUser } from "../types/api";

export function Users() {
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
    setMessage("Operator user created.");
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader title="Users" eyebrow="Local accounts" description="Manage local users and lightweight roles." actions={<button className="button primary" onClick={addOperator} type="button">Add Operator</button>} />
      {message ? <div className="inline-info">{message}</div> : null}
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th></tr></thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>{user.role}</td>
                  <td><StatusBadge label={user.is_active ? "active" : "disabled"} tone={user.is_active ? "success" : "neutral"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
