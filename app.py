from flask import Flask, request, render_template
import joblib
import os
import pytesseract
from PIL import Image
import tempfile
import re
from urllib.parse import urlparse

app = Flask(__name__)

# -----------------------------
# LOAD MODEL + VECTORIZER
# -----------------------------
model = joblib.load("spam_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# -----------------------------
# TESSERACT SETUP
# -----------------------------
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -----------------------------
# TRUSTED DOMAINS
# -----------------------------
trusted_domains = [
    "amazon.in", "amazon.com",
    "flipkart.com",
    "google.com",
    "youtube.com",
    "microsoft.com",
    "apple.com",
    "whatsapp.com",
    "irctc.co.in",
    "sbi.co.in",
    "hdfcbank.com",
    "icicibank.com"
]

# -----------------------------
# CLEAN TEXT
# -----------------------------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", " url ", text)
    text = re.sub(r"\d+", " number ", text)
    return text

# -----------------------------
# URL CHECK
# -----------------------------
def check_url_spam(original_text):
    urls = re.findall(r'https?://\S+|www\.\S+', original_text.lower())

    if not urls:
        return 0

    score = 0

    for url in urls:
        parsed = urlparse(url if url.startswith("http") else "http://" + url)
        domain = parsed.netloc.replace("www.", "")

        if not any(td in domain for td in trusted_domains):
            score += 3

        if re.search(r"[a-z]+[0-9]+[a-z]+", domain):
            score += 3

        if any(domain.endswith(tld) for tld in [".xyz", ".top", ".click", ".ru"]):
            score += 2

    return score

# -----------------------------
# RULE SCORE
# -----------------------------
def rule_based_score(msg):
    score = 0

    spam_keywords = [
        "win", "lottery", "free", "prize", "click",
        "urgent", "offer", "gift", "claim", "reward",
        "limited", "exclusive", "bonus"
    ]

    risky_keywords = [
        "bank", "kyc", "verify", "update",
        "account", "suspended", "blocked",
        "login", "password", "otp"
    ]

    for word in spam_keywords:
        if word in msg:
            score += 2

    for word in risky_keywords:
        if word in msg:
            score += 1

    if "url" in msg or "www" in msg:
        score += 2

    return score

# -----------------------------
# TRUST SCORE
# -----------------------------
def trusted_score(msg):
    score = 0

    trusted = [
        "jio", "airtel", "vi",
        "amazon", "flipkart",
        "google", "irctc",
        "sbi", "hdfc", "icici"
    ]

    for t in trusted:
        if t in msg:
            score += 1

    return score

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():

    message = ""

    # TEXT INPUT
    if "message" in request.form and request.form["message"].strip():
        message = request.form["message"]

    # IMAGE INPUT
    elif "image" in request.files:
        file = request.files["image"]

        if file.filename == "":
            return render_template("index.html", prediction_text="No file selected")

        filepath = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(filepath)

        try:
            image = Image.open(filepath)
            message = pytesseract.image_to_string(image)

            if not message.strip():
                message = "No readable text found"

        except:
            message = "OCR failed"

    else:
        return render_template("index.html", prediction_text="No input provided")

    cleaned_msg = clean_text(message)

    if "ocr failed" in cleaned_msg:
        return render_template("index.html",
                               prediction_text="Unknown",
                               probability=50,
                               extracted_text=message)

    # ML
    msg_vec = vectorizer.transform([cleaned_msg])
    ml_pred = model.predict(msg_vec)[0]
    ml_prob = model.predict_proba(msg_vec)[0][1]

    # SCORES
    rule_score = rule_based_score(cleaned_msg)
    t_score = trusted_score(cleaned_msg)
    url_score = check_url_spam(message)

    total_score = rule_score + url_score

    # FINAL DECISION
    if url_score >= 5:
        result = "Spam (Phishing URL)"
        probability = 0.95

    elif ml_prob > 0.90:
        result = "Spam"
        probability = ml_prob

    elif ml_prob < 0.20 and url_score == 0:
        result = "Not Spam"
        probability = ml_prob

    else:
        if total_score >= 5 and t_score == 0:
            result = "Spam"
            probability = max(ml_prob, 0.85)
        else:
            result = "Spam" if ml_pred == 1 else "Not Spam"
            probability = ml_prob

    return render_template("index.html",
                           prediction_text=result,
                           probability=round(probability * 100, 2),
                           extracted_text=message)

# ❌ REMOVE app.run (Gunicorn will handle it)
