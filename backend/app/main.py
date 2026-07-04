import csv
import io
import secrets
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas, auth, ml_utils, aml_rules, agent 
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Fraud Detection & AML Analytics Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/auth/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.Username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = models.User(
        Username=user.username,
        PasswordHash=auth.hash_password(user.password),
        Role="analyst",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.Username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = auth.create_access_token(data={"sub": user.Username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/transactions/upload", response_model=schemas.UploadSummary)
def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    accepted = 0
    rejected = 0
    errors = []

    required_columns = {"AccountId", "Amount", "Currency", "CountryCode", "TransactionType", "Timestamp"}
    if not required_columns.issubset(reader.fieldnames or []):
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns. Expected: {sorted(required_columns)}",
        )

    for i, row in enumerate(reader, start=1):
        try:
            txn = models.Transaction(
                AccountId=row["AccountId"],
                Amount=float(row["Amount"]),
                Currency=row["Currency"],
                CountryCode=row["CountryCode"],
                TransactionType=row["TransactionType"],
                Timestamp=datetime.fromisoformat(row["Timestamp"]),
                UploadedBy=current_user.UserId,
                MLFeatures=row.get("MLFeatures") or None,
                TrueLabel=int(row["TrueLabel"]) if row.get("TrueLabel") not in (None, "") else None,
            )
            db.add(txn)
            accepted += 1
        except (ValueError, KeyError) as e:
            rejected += 1
            errors.append(f"row {i}: {e}")

    db.commit()
    return {"accepted": accepted, "rejected": rejected, "errors": errors}


@app.post("/predict/{transaction_id}", response_model=schemas.PredictionResponse)
def predict_fraud(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    txn = db.query(models.Transaction).filter(models.Transaction.TransactionId == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    result = ml_utils.score_transaction(transaction_id, float(txn.Amount), txn.MLFeatures)

    score_record = models.FraudScore(
        TransactionId=transaction_id,
        FraudScore=result["fraud_score"],
        TopFeatures=result["top_features"],
    )
    db.add(score_record)
    db.commit()

    return {
        "transaction_id": transaction_id,
        "fraud_score": result["fraud_score"],
        "top_features": result["top_features"],
    }

@app.post("/aml/check/{transaction_id}")
def check_aml_rules(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    txn = db.query(models.Transaction).filter(models.Transaction.TransactionId == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    alerts = aml_rules.run_all_rules(db, txn)

    for alert in alerts:
        db.add(models.AMLAlert(
            TransactionId=transaction_id,
            RuleTriggered=alert["rule"],
            Severity=alert["severity"],
        ))
    db.commit()

    return {"transaction_id": transaction_id, "alerts_triggered": len(alerts), "alerts": alerts}




@app.post("/agent/investigate/{transaction_id}")
def investigate_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = agent.investigate(db, transaction_id)
    return {
        "transaction_id": transaction_id,
        "case_summary": result["report"],
        "jira_ticket": result["jira_ticket"],
    }


@app.get("/transactions")
def list_transactions(
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    latest_scores = {}
    for s in db.query(models.FraudScore).order_by(models.FraudScore.ScoredAt.desc()).all():
        if s.TransactionId not in latest_scores:
            latest_scores[s.TransactionId] = float(s.FraudScore)

    alert_counts = {}
    for txn_id, count in (
        db.query(models.AMLAlert.TransactionId, func.count(models.AMLAlert.AlertId))
        .group_by(models.AMLAlert.TransactionId)
        .all()
    ):
        alert_counts[txn_id] = count

    scored_or_flagged_ids = set(latest_scores.keys()) | set(alert_counts.keys())

    priority_txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.TransactionId.in_(scored_or_flagged_ids))
        .all()
    )
    remaining = max(0, limit - len(priority_txns))
    other_txns = (
        db.query(models.Transaction)
        .filter(~models.Transaction.TransactionId.in_(scored_or_flagged_ids))
        .order_by(models.Transaction.TransactionId)
        .limit(remaining)
        .all()
        if remaining > 0 else []
    )

    result = []
    for t in priority_txns + other_txns:
        result.append({
            "transaction_id": t.TransactionId,
            "account_id": t.AccountId,
            "amount": float(t.Amount),
            "country_code": t.CountryCode,
            "fraud_score": latest_scores.get(t.TransactionId),
            "aml_alert_count": alert_counts.get(t.TransactionId, 0),
        })

    result.sort(key=lambda r: (-r["aml_alert_count"], -(r["fraud_score"] or -1)))
    return result


@app.post("/auth/forgot-password", response_model=schemas.ForgotPasswordResponse)
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.Username == payload.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with that username")

    temp_password = secrets.token_urlsafe(9)
    user.PasswordHash = auth.hash_password(temp_password)
    db.commit()

    return {
        "message": "In production this would be emailed to the account holder. For this demo, it is shown directly.",
        "temporary_password": temp_password,
    }


@app.post("/auth/change-password")
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not auth.verify_password(payload.current_password, current_user.PasswordHash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.PasswordHash = auth.hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}