import { api } from "../api/client";

export function LoginPage() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--ds-bg)" }}>
      <div className="ds-card" style={{ width: 380, textAlign: "center" }}>
        <div style={{ background: "var(--dhl-red)", color: "#fff", fontWeight: 800, display: "inline-block", padding: "6px 12px", borderRadius: 4, marginBottom: 14 }}>
          DHL
        </div>
        <h1 style={{ fontSize: 20, margin: "0 0 6px" }}>Hosting Decision Advisor</h1>
        <p style={{ color: "var(--ds-text-secondary)", fontSize: 14, marginBottom: 20 }}>
          Decide, without bias, whether an application belongs on Public Cloud or Private Cloud / On-Prem — then land
          it in IPP to provision.
        </p>
        <a className="ds-btn ds-btn-primary" style={{ width: "100%", justifyContent: "center" }} href={api.loginUrl()}>
          Sign in
        </a>
      </div>
    </div>
  );
}
