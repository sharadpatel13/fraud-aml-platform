from app.database import SessionLocal
from app.models import Transaction, FraudScore, AMLAlert
from sqlalchemy import func

db = SessionLocal()

print("Backfilling latest fraud scores...")
latest_scores = (
    db.query(FraudScore.TransactionId, FraudScore.FraudScore, FraudScore.ScoredAt)
    .order_by(FraudScore.TransactionId, FraudScore.ScoredAt.desc())
    .all()
)
seen = set()
score_map = {}
for txn_id, score, _ in latest_scores:
    if txn_id not in seen:
        score_map[txn_id] = score
        seen.add(txn_id)

print("Backfilling alert counts...")
alert_counts = (
    db.query(AMLAlert.TransactionId, func.count(AMLAlert.AlertId))
    .group_by(AMLAlert.TransactionId)
    .all()
)
count_map = {txn_id: count for txn_id, count in alert_counts}

print(f"Updating {len(score_map)} scores and {len(count_map)} alert counts...")
all_txns = db.query(Transaction).all()
for i, txn in enumerate(all_txns, start=1):
    txn.LatestFraudScore = score_map.get(txn.TransactionId)
    txn.AMLAlertCount = count_map.get(txn.TransactionId, 0)
    if i % 1000 == 0:
        db.commit()
        print(f"  {i}/{len(all_txns)} done")

db.commit()
print("Backfill complete.")