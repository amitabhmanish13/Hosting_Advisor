import { NavLink, Outlet } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const linkStyle = ({ isActive }: { isActive: boolean }) => ({
  padding: "8px 12px",
  borderRadius: 6,
  fontSize: 14,
  fontWeight: 500,
  textDecoration: "none",
  color: isActive ? "var(--ds-text-on-accent)" : "var(--ds-text-primary)",
  background: isActive ? "var(--dhl-red)" : "transparent",
});

export function Layout() {
  const { user, hasRole } = useAuth();

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          background: "var(--ds-surface)",
          borderBottom: `3px solid var(--dhl-yellow)`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <img src="/dhl-logo.svg" alt="DHL" style={{ height: 30, display: "block" }} />
          <strong style={{ fontSize: 15 }}>Hosting Decision Advisor</strong>
        </div>
        <nav style={{ display: "flex", gap: 4, alignItems: "center" }}>
          <NavLink to="/" style={linkStyle} end>
            Dashboards
          </NavLink>
          {hasRole("assessor", "admin") && (
            <NavLink to="/assessments" style={linkStyle}>
              My Assessments
            </NavLink>
          )}
          {hasRole("assessor", "admin") && (
            <NavLink
              to="/assessments/new"
              style={({ isActive }) => ({ ...linkStyle({ isActive }), background: "var(--dhl-red)", color: "#fff" })}
            >
              + New Assessment
            </NavLink>
          )}
          {hasRole("approver", "admin") && (
            <NavLink to="/approvals" style={linkStyle}>
              Approvals
            </NavLink>
          )}
          {hasRole("admin") && (
            <NavLink to="/admin/questions" style={linkStyle}>
              Questions
            </NavLink>
          )}
          {hasRole("admin") && (
            <NavLink to="/admin/users" style={linkStyle}>
              Users
            </NavLink>
          )}
          <span style={{ marginLeft: 12, fontSize: 13, color: "var(--ds-text-secondary)" }}>
            {user?.display_name} {user?.domain ? `· ${user.domain}` : ""}
          </span>
          <button
            className="ds-btn"
            onClick={async () => {
              await api.logout();
              window.location.href = "/";
            }}
          >
            Sign out
          </button>
        </nav>
      </header>
      <main style={{ flex: 1, padding: 24, maxWidth: 1100, width: "100%", margin: "0 auto" }}>
        <Outlet />
      </main>
    </div>
  );
}
