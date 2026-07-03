import pandas as pd

df = pd.read_csv("../data/creditcard.csv")

print("Shape:", df.shape)
print("\nColumns:", list(df.columns))
print("\nFirst 3 rows:")
print(df.head(3))
print("\nClass balance (0 = normal, 1 = fraud):")
print(df["Class"].value_counts())
print("\nFraud percentage:", round(df["Class"].mean() * 100, 4), "%")