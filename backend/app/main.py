import csv
import io
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
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

    result = ml_utils.score_transaction(transaction_id, float(txn.Amount))

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
    summary = agent.investigate(db, transaction_id)
    return {"transaction_id": transaction_id, "case_summary": summary}