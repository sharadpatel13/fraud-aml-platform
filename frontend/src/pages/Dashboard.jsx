import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(null);
  const [report, setReport] = useState(null);
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

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  async function handleInvestigate(transactionId) {
    setInvestigating(transactionId);
    setReport(null);
    try {
      const response = await client.post(`/agent/investigate/${transactionId}`);
      setReport(response.data.case_summary);
    } catch (err) {
      setReport("Investigation failed. Check that the backend and Ollama are running.");
    } finally {
      setInvestigating(null);
    }
  }

  return (
    <div style={{ padding: "24px", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2>AI Fraud & AML Platform — Dashboard</h2>
        <button onClick={handleLogout}>Log Out</button>
      </div>

      {loading ? (
        <p>Loading transactions...</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "2px solid #444" }}>
              <th style={{ padding: "8px" }}>ID</th>
              <th style={{ padding: "8px" }}>Account</th>
              <th style={{ padding: "8px" }}>Amount</th>
              <th style={{ padding: "8px" }}>Country</th>
              <th style={{ padding: "8px" }}>Fraud Score</th>
              <th style={{ padding: "8px" }}>AML Alerts</th>
              <th style={{ padding: "8px" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr key={t.transaction_id} style={{ borderBottom: "1px solid #333" }}>
                <td style={{ padding: "8px" }}>{t.transaction_id}</td>
                <td style={{ padding: "8px" }}>{t.account_id}</td>
                <td style={{ padding: "8px" }}>${t.amount.toFixed(2)}</td>
                <td style={{ padding: "8px" }}>{t.country_code}</td>
                <td style={{ padding: "8px" }}>{t.fraud_score !== null ? `${t.fraud_score}%` : "—"}</td>
                <td style={{ padding: "8px", color: t.aml_alert_count > 0 ? "#e74c3c" : "inherit" }}>
                  {t.aml_alert_count > 0 ? `⚠ ${t.aml_alert_count}` : "—"}
                </td>
                <td style={{ padding: "8px" }}>
                  {t.aml_alert_count > 0 && (
                    <button
                      onClick={() => handleInvestigate(t.transaction_id)}
                      disabled={investigating === t.transaction_id}
                    >
                      {investigating === t.transaction_id ? "Investigating..." : "Investigate with AI"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {report && (
        <div style={{ marginTop: "24px", padding: "16px", border: "1px solid #444", borderRadius: "6px", whiteSpace: "pre-wrap" }}>
          <h3>AI Investigation Report</h3>
          {report}
        </div>
      )}
    </div>
  );
}

export default Dashboard;