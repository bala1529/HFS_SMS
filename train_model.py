import pandas as pd
import re
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# -----------------------------
# LOAD DATASET (SAFE ENCODING)
# -----------------------------
try:
    df = pd.read_csv("spam.csv", encoding="utf-8")
except:
    df = pd.read_csv("spam.csv", encoding="latin-1")

# -----------------------------
# FIX COLUMN NAMES
# -----------------------------
# Kaggle dataset la usually v1, v2 irukum
if "v1" in df.columns and "v2" in df.columns:
    df = df.rename(columns={"v1": "label", "v2": "message"})

# Keep only required columns
df = df[["label", "message"]]

# -----------------------------
# CLEAN DATA
# -----------------------------
df["label"] = df["label"].map({"ham": 0, "spam": 1})

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", " url ", text)
    text = re.sub(r"\d+", " number ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    return text

df["message"] = df["message"].apply(clean_text)

# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    df["message"], df["label"], test_size=0.2, random_state=42
)

# -----------------------------
# VECTORIZER
# -----------------------------
vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# -----------------------------
# MODEL TRAIN
# -----------------------------
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# -----------------------------
# EVALUATE
# -----------------------------
y_pred = model.predict(X_test_vec)
accuracy = accuracy_score(y_test, y_pred)

print("🔥 Model Accuracy:", accuracy * 100, "%")

# -----------------------------
# SAVE MODEL
# -----------------------------
joblib.dump(model, "spam_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("✅ Model & Vectorizer saved successfully!")