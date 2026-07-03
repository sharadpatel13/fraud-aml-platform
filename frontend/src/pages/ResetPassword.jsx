import { useState } from "react";
import client from "../api/client";
import Layout from "../components/Layout";

function ResetPassword() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage(null);
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match");
      return;
    }
    try {
      const response = await client.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMessage(response.data.message);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update password");
    }
  }

  return (
    <Layout>
      <h1 style={{ fontSize: "22px", fontWeight: 600, marginBottom: "20px" }}>Account Settings</h1>
      <div className="card" style={{ maxWidth: "360px" }}>
        <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "16px" }}>Change Password</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "14px" }}>
            <label>Current Password</label>
            <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div style={{ marginBottom: "14px" }}>
            <label>New Password</label>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div style={{ marginBottom: "14px" }}>
            <label>Confirm New Password</label>
            <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          {error && <p style={{ color: "var(--risk-high)", fontSize: "13px", marginBottom: "12px" }}>{error}</p>}
          {message && <p style={{ color: "var(--risk-low)", fontSize: "13px", marginBottom: "12px" }}>{message}</p>}
          <button type="submit" style={{ width: "100%" }}>Update Password</button>
        </form>
      </div>
    </Layout>
  );
}

export default ResetPassword;