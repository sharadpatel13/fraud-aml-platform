import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("../data/creditcard.csv")

X = df.drop("Class", axis=1)
y = df["Class"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training set shape:", X_train.shape)
print("Test set shape:", X_test.shape)
print("\nFraud count in training set:", y_train.sum())
print("Fraud count in test set:", y_test.sum())


from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.1,
    eval_metric="logloss",
    random_state=42,
)

model.fit(X_train, y_train)
print("\nModel trained.")


from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

y_pred = model.predict(X_test)

print("\n--- Naive accuracy (misleading, see explanation) ---")
print("Accuracy:", round(accuracy_score(y_test, y_pred), 5))

print("\n--- Confusion matrix ---")
print(confusion_matrix(y_test, y_pred))

print("\n--- Full classification report ---")
print(classification_report(y_test, y_pred, target_names=["Not Fraud", "Fraud"]))

import joblib

joblib.dump(model, "fraud_model.pkl")
print("\nModel saved to fraud_model.pkl")