from app.database import SessionLocal
from app.models import Transaction, FraudScore, AMLAlert
from app import ml_utils, aml_rules

db = SessionLocal()

all_txns = db.query(Transaction).order_by(Transaction.TransactionId).all()
print(f"Scoring {len(all_txns)} transactions...")

for i, txn in enumerate(all_txns, start=1):
    result = ml_utils.score_transaction(txn.TransactionId, float(txn.Amount), txn.MLFeatures)
    db.add(FraudScore(
        TransactionId=txn.TransactionId,
        FraudScore=result["fraud_score"],
        TopFeatures=result["top_features"],
    ))

    alerts = aml_rules.run_all_rules(db, txn)
    for alert in alerts:
        db.add(AMLAlert(
            TransactionId=txn.TransactionId,
            RuleTriggered=alert["rule"],
            Severity=alert["severity"],
        ))

    if i % 500 == 0:
        db.commit()
        print(f"  {i}/{len(all_txns)} done")

db.commit()
print("All transactions scored.")