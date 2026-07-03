import numpy as np
import joblib
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "fraud_model.pkl"
model = joblib.load(MODEL_PATH)

FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]


def build_feature_vector(transaction_id: int, amount: float) -> np.ndarray:
    """Builds a 30-value feature vector matching what the model was trained on.

    Amount is real. Time and V1-V28 are deterministic placeholder values,
    seeded from the transaction ID — a stand-in for the real bank-internal
    PCA features we don't have access to, since Kaggle's V1-V28 came from
    a feature pipeline that isn't publicly available. Seeding by ID keeps
    scores reproducible rather than random on every call.
    """
    rng = np.random.default_rng(seed=transaction_id)
    v_features = rng.normal(loc=0, scale=1, size=28)
    time_value = 0.0
    return np.array([time_value, *v_features, amount]).reshape(1, -1)


def score_transaction(transaction_id: int, amount: float) -> dict:
    features = build_feature_vector(transaction_id, amount)
    probability = model.predict_proba(features)[0][1]
    fraud_score = round(float(probability) * 100, 2)

    importances = model.feature_importances_
    top_idx = importances.argsort()[-3:][::-1]
    top_features = ", ".join(FEATURE_COLUMNS[i] for i in top_idx)

    return {"fraud_score": fraud_score, "top_features": top_features}