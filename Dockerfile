FROM python:3.10

WORKDIR /app

COPY . .

# Install tesseract (for OCR)
RUN apt-get update && apt-get install -y tesseract-ocr

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 🔥 IMPORTANT FIX (PORT issue solved)
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
