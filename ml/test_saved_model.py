import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

model = joblib.load("fraud_model.pkl")

df = pd.read_csv("../data/creditcard.csv")
X = df.drop("Class", axis=1)
y = df["Class"]

_, X_test, _, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

sample = X_test.iloc[[0]]
prediction = model.predict(sample)[0]
probability = model.predict_proba(sample)[0][1]

print("Sample transaction prediction:", "FRAUD" if prediction == 1 else "NOT FRAUD")
print("Fraud probability:", round(probability * 100, 2), "%")
print("Actual label:", "FRAUD" if y_test.iloc[0] == 1 else "NOT FRAUD")