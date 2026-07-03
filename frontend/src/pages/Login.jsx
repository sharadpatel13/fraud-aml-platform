import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import client from "../api/client";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    try {
      const response = await client.post("/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("token", response.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError("Invalid username or password");
    }
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <div
        style={{
          flex: 1,
          background: "linear-gradient(160deg, var(--navy-900) 0%, var(--navy-950) 60%, #0c1f3d 100%)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: "48px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "radial-gradient(circle at 20% 20%, rgba(59,130,246,0.15), transparent 40%), radial-gradient(circle at 80% 70%, rgba(59,130,246,0.1), transparent 40%)",
          }}
        />
        <svg width="120" height="120" viewBox="0 0 24 24" fill="none" style={{ zIndex: 1, marginBottom: "24px" }}>
          <path d="M12 2L4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5l-8-3z" stroke="var(--accent)" strokeWidth="1.2" fill="rgba(59,130,246,0.08)" />
          <path d="M9 12l2 2 4-4" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <h1 style={{ color: "var(--text-primary)", fontSize: "28px", fontWeight: 600, textAlign: "center", zIndex: 1, margin: 0 }}>
          AI Fraud & AML Platform
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "15px", textAlign: "center", maxWidth: "360px", marginTop: "12px", zIndex: 1 }}>
          Real-time transaction monitoring, machine learning fraud detection, and
          AI-assisted AML investigation - running on your own infrastructure.
        </p>
      </div>

      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", background: "var(--navy-950)" }}>
        <div style={{ width: "320px" }}>
          <h2 style={{ fontSize: "20px", fontWeight: 600, marginBottom: "4px" }}>Welcome back</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px" }}>
            Sign in to access the compliance dashboard
          </p>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "16px" }}>
              <label>Username</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div style={{ marginBottom: "8px" }}>
              <label>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div style={{ textAlign: "right", marginBottom: "16px" }}>
              <Link to="/forgot-password" style={{ fontSize: "13px" }}>Forgot password?</Link>
            </div>
            {error && <p style={{ color: "var(--risk-high)", fontSize: "13px", marginBottom: "12px" }}>{error}</p>}
            <button type="submit" style={{ width: "100%" }}>Log In</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login;