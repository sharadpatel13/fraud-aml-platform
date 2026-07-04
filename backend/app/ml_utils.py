import numpy as np
import joblib
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "fraud_model.pkl"
model = joblib.load(MODEL_PATH)

FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]


def build_feature_vector(transaction_id: int, amount: float, ml_features: str | None = None) -> np.ndarray:
    """Builds the 30-value feature vector the model expects.

    If real engineered features are available (ml_features, sourced from
    the Kaggle dataset via MLFeatures column), use them - this is genuine
    scoring. Otherwise fall back to a deterministic placeholder, seeded by
    transaction ID, for any transaction that never had real features
    attached (e.g. manually typed test rows)."""
    if ml_features:
        values = [float(x) for x in ml_features.split(",")]
        return np.array(values + [amount]).reshape(1, -1)

    rng = np.random.default_rng(seed=transaction_id)
    v_features = rng.normal(loc=0, scale=1, size=28)
    time_value = 0.0
    return np.array([time_value, *v_features, amount]).reshape(1, -1)


def score_transaction(transaction_id: int, amount: float, ml_features: str | None = None) -> dict:
    features = build_feature_vector(transaction_id, amount, ml_features)
    probability = model.predict_proba(features)[0][1]
    fraud_score = round(float(probability) * 100, 2)

    importances = model.feature_importances_
    top_idx = importances.argsort()[-3:][::-1]
    top_features = ", ".join(FEATURE_COLUMNS[i] for i in top_idx)

    return {"fraud_score": fraud_score, "top_features": top_features}