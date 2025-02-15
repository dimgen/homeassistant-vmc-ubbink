FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
