import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import Layout from "../components/Layout";

function riskBadge(fraudScore, alertCount) {
  if (alertCount > 0) return <span className="badge badge-high">● High Risk</span>;
  if (fraudScore !== null && fraudScore >= 30) return <span className="badge badge-medium">● Medium Risk</span>;
  if (fraudScore !== null) return <span className="badge badge-low">● Low Risk</span>;
  return <span className="badge badge-neutral">Not Scored</span>;
}

function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchTransactions() {
      try {
        const response = await client.get("/transactions");
        setTransactions(response.data);
      } catch (err) {
        if (err.response?.status === 401) navigate("/login");
      } finally {
        setLoading(false);
      }
    }
    fetchTransactions();
  }, [navigate]);

  const flaggedCount = transactions.filter((t) => t.aml_alert_count > 0).length;
  const scoredCount = transactions.filter((t) => t.fraud_score !== null).length;

  return (
    <Layout>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "22px", fontWeight: 600, margin: 0 }}>Transaction Monitoring</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "4px" }}>
          Real-time fraud detection and AML compliance overview
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "28px" }}>
        <div className="card">
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>Total Transactions</div>
          <div style={{ fontSize: "28px", fontWeight: 600, marginTop: "8px" }}>{transactions.length}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>Scored by ML Model</div>
          <div style={{ fontSize: "28px", fontWeight: 600, marginTop: "8px" }}>{scoredCount}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>Flagged for AML Review</div>
          <div style={{ fontSize: "28px", fontWeight: 600, marginTop: "8px", color: flaggedCount > 0 ? "var(--risk-high)" : "inherit" }}>
            {flaggedCount}
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: "20px" }}>Loading transactions...</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", background: "var(--navy-800)" }}>
                <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)" }}>ID</th>
                <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)" }}>Account</th>
                <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)" }}>Amount</th>
                <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)" }}>Country</th>
                <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)" }}>Risk Level</th>
                <th style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-muted)" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((t) => (
                <tr key={t.transaction_id} style={{ borderTop: "1px solid var(--border)" }}>
                  <td style={{ padding: "12px 16px", fontSize: "14px" }}>#{t.transaction_id}</td>
                  <td style={{ padding: "12px 16px", fontSize: "14px" }}>{t.account_id}</td>
                  <td style={{ padding: "12px 16px", fontSize: "14px" }}>${t.amount.toFixed(2)}</td>
                  <td style={{ padding: "12px 16px", fontSize: "14px" }}>{t.country_code}</td>
                  <td style={{ padding: "12px 16px" }}>{riskBadge(t.fraud_score, t.aml_alert_count)}</td>
                  <td style={{ padding: "12px 16px" }}>
                    {t.aml_alert_count > 0 && (
                      <button onClick={() => navigate(`/investigate/${t.transaction_id}`)}>
                        Investigate with AI
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}

export default Dashboard;