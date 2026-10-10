FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE
ENV GOOGLE_CLOUD_PROJECT=your-project-id
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV GROCERY_DB_SERVICE_URL=https://grocery-db-service-<PROJECT_HASH>.run.app

EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
