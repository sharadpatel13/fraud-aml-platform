import { useNavigate, useLocation } from "react-router-dom";

function Layout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  const navItems = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Account Settings", path: "/reset-password" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: "240px",
          background: "var(--navy-900)",
          borderRight: "1px solid var(--border)",
          padding: "24px 16px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ marginBottom: "32px" }}>
          <div style={{ fontSize: "13px", color: "var(--text-muted)", letterSpacing: "0.05em" }}>
            COMPLIANCE PLATFORM
          </div>
          <div style={{ fontSize: "16px", fontWeight: 600, marginTop: "4px" }}>
            Fraud & AML Platform
          </div>
        </div>

        <nav style={{ flex: 1 }}>
          {navItems.map((item) => (
            <div
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                padding: "10px 12px",
                borderRadius: "6px",
                cursor: "pointer",
                marginBottom: "4px",
                fontSize: "14px",
                fontWeight: 500,
                background: location.pathname === item.path ? "var(--navy-700)" : "transparent",
                color: location.pathname === item.path ? "var(--text-primary)" : "var(--text-secondary)",
              }}
            >
              {item.label}
            </div>
          ))}
        </nav>

        <button className="secondary" onClick={handleLogout}>
          Log Out
        </button>
      </aside>

      <main style={{ flex: 1, padding: "32px", background: "var(--navy-950)" }}>
        {children}
      </main>
    </div>
  );
}

export default Layout;