import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import Layout from "../components/Layout";

function parseReport(text) {
  const sections = {};
  const parts = text.split(/\n(?=[A-Z ]+:)/);
  for (const part of parts) {
    const match = part.match(/^([A-Z ]+):\s*([\s\S]*)/);
    if (match) {
      sections[match[1].trim()] = match[2].trim();
    }
  }
  return sections;
}

function Investigate() {
  const { transactionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function runInvestigation() {
      try {
        const response = await client.post(`/agent/investigate/${transactionId}`);
        setReport(parseReport(response.data.case_summary));
      } catch (err) {
        setError("Investigation failed. Confirm the backend and Ollama are both running.");
      } finally {
        setLoading(false);
      }
    }
    runInvestigation();
  }, [transactionId]);

  const sectionOrder = ["OVERVIEW", "FRAUD RISK ASSESSMENT", "AML FINDINGS", "ACCOUNT CONTEXT", "RECOMMENDATION"];

  return (
    <Layout>
      <button className="secondary" onClick={() => navigate("/dashboard")} style={{ marginBottom: "20px" }}>
        ← Back to Dashboard
      </button>

      <h1 style={{ fontSize: "22px", fontWeight: 600, margin: "0 0 4px" }}>
        AI Investigation — Transaction #{transactionId}
      </h1>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px" }}>
        Generated locally by an AI agent reasoning over live case data
      </p>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "48px" }}>
          <div style={{ fontSize: "15px", marginBottom: "8px" }}>Agent is investigating...</div>
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            Gathering transaction data, fraud score, AML alerts, and account history.
            This runs on a local model and may take up to a minute.
          </div>
        </div>
      )}

      {error && (
        <div className="card" style={{ borderColor: "var(--risk-high)" }}>
          <span style={{ color: "var(--risk-high)" }}>{error}</span>
        </div>
      )}

      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {sectionOrder.map((key) => {
            if (!report[key]) return null;
            const isRecommendation = key === "RECOMMENDATION";
            const isEscalate = isRecommendation && /escalate/i.test(report[key]);
            const isClear = isRecommendation && /^clear/i.test(report[key]);

            return (
              <div
                key={key}
                className="card"
                style={
                  isRecommendation
                    ? {
                        borderColor: isEscalate ? "var(--risk-high)" : isClear ? "var(--risk-low)" : "var(--risk-medium)",
                        borderWidth: "2px",
                      }
                    : {}
                }
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
                  <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--accent)", letterSpacing: "0.05em" }}>
                    {key}
                  </span>
                  {isRecommendation && (
                    <span className={`badge ${isEscalate ? "badge-high" : isClear ? "badge-low" : "badge-medium"}`}>
                      {isEscalate ? "ESCALATE" : isClear ? "CLEAR" : "REVIEW"}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: "14px", lineHeight: 1.6, color: "var(--text-primary)" }}>
                  {report[key]}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Layout>
  );
}

export default Investigate;