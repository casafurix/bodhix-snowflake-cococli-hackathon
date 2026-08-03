FROM node:22-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ATLAS_DATA_BACKEND=snowflake \
    ATLAS_STATIC_DIR=/app/static \
    SNOWFLAKE_WAREHOUSE=CTOPS_WH \
    SNOWFLAKE_DATABASE=CTOPS_HACKATHON \
    SNOWFLAKE_SCHEMA=APP \
    PORT=8000

WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/app/ ./app/
RUN pip install --no-cache-dir .
COPY --from=frontend-build /build/frontend/dist ./static/

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
