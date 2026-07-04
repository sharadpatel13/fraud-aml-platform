import ollama
from sqlalchemy.orm import Session
import requests
from requests.auth import HTTPBasicAuth
from app.config import settings

from app import models


def get_transaction(db: Session, transaction_id: int) -> dict:
    t = db.query(models.Transaction).filter(models.Transaction.TransactionId == transaction_id).first()
    if not t:
        return {"error": "transaction not found"}
    return {
        "transaction_id": t.TransactionId,
        "account_id": t.AccountId,
        "amount": float(t.Amount),
        "currency": t.Currency,
        "country_code": t.CountryCode,
        "type": t.TransactionType,
        "timestamp": str(t.Timestamp),
    }


def get_fraud_score(db: Session, transaction_id: int) -> dict:
    s = (
        db.query(models.FraudScore)
        .filter(models.FraudScore.TransactionId == transaction_id)
        .order_by(models.FraudScore.ScoredAt.desc())
        .first()
    )
    if not s:
        return {"error": "no fraud score found for this transaction"}
    return {"fraud_score": float(s.FraudScore), "top_features": s.TopFeatures}


def get_aml_alerts(db: Session, transaction_id: int) -> dict:
    alerts = db.query(models.AMLAlert).filter(models.AMLAlert.TransactionId == transaction_id).all()
    return {
        "alerts": [
            {"rule": a.RuleTriggered, "severity": a.Severity, "created_at": str(a.CreatedAt)}
            for a in alerts
        ]
    }


def get_account_history(db: Session, account_id: str, limit: int = 10) -> dict:
    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.AccountId == account_id)
        .order_by(models.Transaction.Timestamp.desc())
        .limit(limit)
        .all()
    )
    return {
        "recent_transactions": [
            {"amount": float(t.Amount), "country": t.CountryCode, "timestamp": str(t.Timestamp)}
            for t in txns
        ]
    }


def classify_score(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def determine_recommendation(alerts: list, score_classification: str) -> str:
    high_alerts = [a for a in alerts if a["severity"] == "HIGH"]
    if high_alerts:
        return "escalate for manual review"
    if not alerts and score_classification == "LOW":
        return "clear"
    return "flag for further review"


def create_jira_ticket(summary: str, description: str) -> dict:
    if not settings.jira_base_url or not settings.jira_api_token:
        return {"error": "Jira not configured"}

    url = f"{settings.jira_base_url}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": settings.jira_project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            },
            "issuetype": {"name": "Task"},
        }
    }
    response = requests.post(
        url, json=payload,
        auth=HTTPBasicAuth(settings.jira_email, settings.jira_api_token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=10,
    )
    if response.status_code >= 300:
        return {"error": f"Jira API error {response.status_code}"}
    key = response.json()["key"]
    return {"ticket_key": key, "url": f"{settings.jira_base_url}/browse/{key}"}

def find_existing_ticket(transaction_id: int) -> dict | None:
    """Checks whether a Jira ticket already exists for this transaction,
    to avoid filing duplicates on repeated investigations."""
    if not settings.jira_base_url or not settings.jira_api_token:
        return None

    jql = f'project = {settings.jira_project_key} AND summary ~ "Transaction #{transaction_id} "'
    url = f"{settings.jira_base_url}/rest/api/3/search/jql"
    response = requests.get(
        url,
        params={"jql": jql, "maxResults": 1, "fields": "summary"},
        auth=HTTPBasicAuth(settings.jira_email, settings.jira_api_token),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    if response.status_code == 200 and response.json().get("issues"):
        issue = response.json()["issues"][0]
        return {"ticket_key": issue["key"], "url": f"{settings.jira_base_url}/browse/{issue['key']}"}
    return None

def investigate(db: Session, transaction_id: int) -> str:
    """Gathers facts deterministically (Python decides what happened and what
    should happen next), then asks a local LLM only to phrase it as prose.
    This split exists because small local models are reliable at writing
    clear sentences but not reliable at multi-step decision logic — so we
    don't ask them to do the second thing."""

    txn = get_transaction(db, transaction_id)
    score_data = get_fraud_score(db, transaction_id)
    alert_data = get_aml_alerts(db, transaction_id)
    history = get_account_history(db, txn["account_id"])

    score_classification = classify_score(score_data.get("fraud_score", 0))
    recommendation = determine_recommendation(alert_data["alerts"], score_classification)

    jira_ticket = None
    if recommendation == "escalate for manual review":
        jira_ticket = find_existing_ticket(transaction_id)
        if not jira_ticket:
            jira_ticket = create_jira_ticket(
                summary=f"AML Escalation — Transaction #{transaction_id} ({txn['account_id']})",
                description=(
                    f"Auto-filed by AI agent.\n\nAmount: ${txn['amount']}\nCountry: {txn['country_code']}\n"
                    f"Fraud score: {score_data.get('fraud_score')} ({score_classification})\n"
                    f"AML alerts: {alert_data['alerts']}"
                ),
            )

    facts = f"""
Transaction: {txn}
Fraud score: {score_data.get('fraud_score')} ({score_classification})
AML alerts: {alert_data['alerts']}
Recent account history: {history['recent_transactions']}
Required recommendation (do not change this): {recommendation}
"""

    response = ollama.chat(
        model="llama3.1:8b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are writing a formal case investigation report for a bank's AML/fraud "
                    "compliance team. Using ONLY the facts provided, write a well-structured report "
                    "with these exact section headers:\n\n"
                    "OVERVIEW: 2-3 sentences summarizing the transaction in plain English — who, "
                    "how much, where, and when.\n\n"
                    "FRAUD RISK ASSESSMENT: State the fraud score, its classification, and what the "
                    "top contributing features suggest, in a full sentence or two — not just numbers.\n\n"
                    "AML FINDINGS: For each alert, explain in plain English what the rule means and "
                    "why it matters (e.g. what 'structuring' is, why the country is high-risk) — "
                    "don't just list the rule names.\n\n"
                    "ACCOUNT CONTEXT: Briefly describe the pattern visible in the account's recent "
                    "transaction history and how it relates to the findings above.\n\n"
                    "RECOMMENDATION: State the required recommendation exactly as given, followed by "
                    "1-2 sentences justifying it based on the findings above. Do not change or "
                    "second-guess the recommendation itself.\n\n"
                    "Write in full sentences, professional tone, as if this will be read by a human "
                    "analyst deciding whether to escalate a real case. Aim for 200-300 words total."
                ),
            },
            {"role": "user", "content": facts},
        ],
    )

    return {"report": response["message"]["content"], "jira_ticket": jira_ticket}