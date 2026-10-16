import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Domain, Role, UserAccount } from "../../api/types";

const ROLES: Role[] = ["admin", "assessor", "approver", "viewer"];

export function UsersPage() {
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [grant, setGrant] = useState<Record<number, { role: Role; domain_id: string }>>({});

  const load = () => {
    api.users().then(setUsers);
    api.domains().then(setDomains);
  };
  useEffect(load, []);

  const addRole = async (userId: number) => {
    const g = grant[userId] ?? { role: "assessor" as Role, domain_id: "" };
    await api.addRole(userId, g.role, g.domain_id ? Number(g.domain_id) : null);
    load();
  };

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <h1 style={{ fontSize: 22, margin: 0 }}>Users &amp; roles</h1>
      <div className="ds-card">
        <table className="ds-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Home domain</th>
              <th>Role grants</th>
              <th>Add grant</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>
                  {u.display_name}
                  <div style={{ color: "var(--ds-text-secondary)", fontSize: 12 }}>{u.email}</div>
                </td>
                <td>{u.domain?.name ?? "—"}</td>
                <td>
                  {u.roles.map((r, i) => (
                    <span key={i} className="ds-pill" style={{ background: "var(--ds-chip-neutral-bg)", color: "var(--ds-chip-neutral-fg)", marginRight: 4, marginBottom: 4 }}>
                      {r.role}
                      {r.domain_id ? ` (${domains.find((d) => d.id === r.domain_id)?.name ?? r.domain_id})` : " (global)"}
                    </span>
                  ))}
                </td>
                <td>
                  <div style={{ display: "flex", gap: 6 }}>
                    <select
                      className="ds-select"
                      style={{ maxWidth: 110 }}
                      value={grant[u.id]?.role ?? "assessor"}
                      onChange={(e) => setGrant((p) => ({ ...p, [u.id]: { role: e.target.value as Role, domain_id: p[u.id]?.domain_id ?? "" } }))}
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                    <select
                      className="ds-select"
                      style={{ maxWidth: 140 }}
                      value={grant[u.id]?.domain_id ?? ""}
                      onChange={(e) => setGrant((p) => ({ ...p, [u.id]: { role: p[u.id]?.role ?? "assessor", domain_id: e.target.value } }))}
                    >
                      <option value="">Global</option>
                      {domains.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                    <button className="ds-btn" onClick={() => addRole(u.id)}>
                      Add
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
