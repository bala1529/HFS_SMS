FROM python:3.10

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y tesseract-ocr

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]