FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.prod.txt /app/backend/requirements.prod.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.prod.txt
COPY backend /app/backend
COPY data /app/data
COPY migrations /app/migrations
EXPOSE 8000
CMD ["sh", "-c", "cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
