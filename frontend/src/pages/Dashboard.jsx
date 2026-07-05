import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import Layout from "../components/Layout";

function riskBadge(fraudScore, alertCount) {
  if (alertCount > 0) return <span className="badge badge-high">● High Risk</span>;
  if (fraudScore !== null && fraudScore >= 30) return <span className="badge badge-medium">● Medium Risk</span>;
  if (fraudScore !== null) return <span className="badge badge-low">● Low Risk</span>;
  return <span className="badge badge-neutral">Not Scored</span>;
}

const FILTERS = [
  { key: null, label: "All" },
  { key: "high", label: "High Risk" },
  { key: "medium", label: "Medium Risk" },
  { key: "low", label: "Low Risk" },
  { key: "not_scored", label: "Not Scored" },
];

const PAGE_SIZE = 300;

function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState({ total: 0, scored: 0, flagged: 0 });
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState(null);
  const navigate = useNavigate();

  const fetchTransactions = useCallback(
    async (filter, pageNum) => {
      setLoading(true);
      try {
        const params = { page: pageNum, page_size: PAGE_SIZE };
        if (filter) params.risk_level = filter;
        const response = await client.get("/transactions", { params });
        setTransactions(response.data.items);
        setTotal(response.data.total);
      } catch (err) {
        if (err.response?.status === 401) navigate("/login");
      } finally {
        setLoading(false);
      }
    },
    [navigate]
  );

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await client.get("/transactions/stats");
        setStats(response.data);
      } catch (err) {
        if (err.response?.status === 401) navigate("/login");
      }
    }
    fetchStats();
    fetchTransactions(null, 1);
  }, [fetchTransactions, navigate]);

  function handleFilterClick(filterKey) {
    setActiveFilter(filterKey);
    setPage(1);
    fetchTransactions(filterKey, 1);
  }

  function handlePageChange(newPage) {
    setPage(newPage);
    fetchTransactions(activeFilter, newPage);
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <Layout>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "22px", fontWeight: 600, margin: 0 }}>Transaction Monitoring</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "4px" }}>
          Real-time fraud detection and AML compliance overview
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "20px" }}>
        <div className="card">
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>Total Transactions</div>
          <div style={{ fontSize: "28px", fontWeight: 600, marginTop: "8px" }}>{stats.total.toLocaleString()}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>Scored by ML Model</div>
          <div style={{ fontSize: "28px", fontWeight: 600, marginTop: "8px" }}>{stats.scored.toLocaleString()}</div>
        </div>
        <div className="card">
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>Flagged for AML Review</div>
          <div
            style={{
              fontSize: "28px",
              fontWeight: 600,
              marginTop: "8px",
              color: stats.flagged > 0 ? "var(--risk-high)" : "inherit",
            }}
          >
            {stats.flagged.toLocaleString()}
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        {FILTERS.map((f) => (
          <button
            key={f.label}
            className={activeFilter === f.key ? "" : "secondary"}
            onClick={() => handleFilterClick(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: "20px" }}>Loading transactions...</div>
        ) : transactions.length === 0 ? (
          <div style={{ padding: "20px", color: "var(--text-secondary)" }}>No transactions match this filter.</div>
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
                    <button onClick={() => navigate(`/investigate/${t.transaction_id}`)}>
                      Investigate with AI
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {!loading && transactions.length > 0 && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px" }}>
          <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Page {page} of {totalPages} — {total.toLocaleString()} total
          </span>
          <div style={{ display: "flex", gap: "8px" }}>
            <button className="secondary" disabled={page <= 1} onClick={() => handlePageChange(page - 1)}>
              ← Previous
            </button>
            <button className="secondary" disabled={page >= totalPages} onClick={() => handlePageChange(page + 1)}>
              Next →
            </button>
          </div>
        </div>
      )}
    </Layout>
  );
}

export default Dashboard;