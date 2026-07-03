from datetime import timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app import models

# Simplified high-risk country list for this project — in a production
# system this would be sourced from OFAC/FATF data, not hardcoded.
HIGH_RISK_COUNTRIES = {"IR", "KP", "SY", "CU"}  # Iran, North Korea, Syria, Cuba

STRUCTURING_THRESHOLD = Decimal("10000.00")
STRUCTURING_WINDOW_HOURS = 24
STRUCTURING_MIN_COUNT = 2


def check_high_risk_country(transaction: models.Transaction) -> dict | None:
    """Flags a transaction if its country is on the high-risk list."""
    if transaction.CountryCode in HIGH_RISK_COUNTRIES:
        return {
            "rule": "high_risk_country",
            "severity": "HIGH",
            "reason": f"Transaction involves high-risk country: {transaction.CountryCode}",
        }
    return None

def check_structuring(db: Session, transaction: models.Transaction) -> dict | None:
    """Flags an account making multiple transactions, each individually
    under the reporting threshold, that add up suspiciously within a
    short window — a classic technique to evade reporting requirements."""

    window_start = transaction.Timestamp - timedelta(hours=STRUCTURING_WINDOW_HOURS)

    recent_txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.AccountId == transaction.AccountId,
            models.Transaction.Timestamp >= window_start,
            models.Transaction.Timestamp <= transaction.Timestamp,
            models.Transaction.Amount < STRUCTURING_THRESHOLD,
        )
        .all()
    )

    if len(recent_txns) >= STRUCTURING_MIN_COUNT:
        total = sum(t.Amount for t in recent_txns)
        return {
            "rule": "structuring",
            "severity": "HIGH",
            "reason": (
                f"{len(recent_txns)} transactions under ${STRUCTURING_THRESHOLD} "
                f"within {STRUCTURING_WINDOW_HOURS}h, totaling ${total}"
            ),
        }
    return None


VELOCITY_WINDOW_HOURS = 1
VELOCITY_MAX_COUNT = 3


def check_velocity(db: Session, transaction: models.Transaction) -> dict | None:
    """Flags an account making an unusually high number of transactions
    in a very short window — regardless of amount."""

    window_start = transaction.Timestamp - timedelta(hours=VELOCITY_WINDOW_HOURS)

    recent_count = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.AccountId == transaction.AccountId,
            models.Transaction.Timestamp >= window_start,
            models.Transaction.Timestamp <= transaction.Timestamp,
        )
        .count()
    )

    if recent_count >= VELOCITY_MAX_COUNT:
        return {
            "rule": "velocity",
            "severity": "MEDIUM",
            "reason": f"{recent_count} transactions from this account within {VELOCITY_WINDOW_HOURS}h",
        }
    return None


def run_all_rules(db: Session, transaction: models.Transaction) -> list[dict]:
    """Runs every AML rule against a transaction, returns all triggered alerts."""
    checks = [
        check_high_risk_country(transaction),
        check_structuring(db, transaction),
        check_velocity(db, transaction),
    ]
    return [alert for alert in checks if alert is not None]