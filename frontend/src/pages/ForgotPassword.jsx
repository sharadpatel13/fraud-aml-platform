import { useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";

function ForgotPassword() {
  const [username, setUsername] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const response = await client.post("/auth/forgot-password", { username });
      setResult(response.data);
    } catch (err) {
      setError("No account found with that username");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", alignItems: "center", justifyContent: "center", background: "var(--navy-950)" }}>
      <div className="card" style={{ width: "380px" }}>
        <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "4px" }}>Reset your password</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "20px" }}>
          Enter your username and we'll issue a temporary password.
        </p>

        {!result && (
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "16px" }}>
              <label>Username</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            {error && <p style={{ color: "var(--risk-high)", fontSize: "13px", marginBottom: "12px" }}>{error}</p>}
            <button type="submit" disabled={loading} style={{ width: "100%" }}>
              {loading ? "Generating..." : "Send Reset"}
            </button>
          </form>
        )}

        {result && (
          <div>
            <div className="badge badge-medium" style={{ marginBottom: "12px" }}>DEMO MODE — NOT EMAILED</div>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "12px" }}>{result.message}</p>
            <div style={{ background: "var(--navy-800)", border: "1px solid var(--border)", borderRadius: "6px", padding: "12px", fontFamily: "monospace", fontSize: "15px", textAlign: "center", marginBottom: "16px" }}>
              {result.temporary_password}
            </div>
            <Link to="/login"><button style={{ width: "100%" }}>Back to Login</button></Link>
          </div>
        )}

        {!result && (
          <div style={{ textAlign: "center", marginTop: "16px" }}>
            <Link to="/login" style={{ fontSize: "13px" }}>← Back to login</Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default ForgotPassword;