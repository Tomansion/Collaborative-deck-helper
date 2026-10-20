# syntax=docker/dockerfile:1

# ---------- 1. Build the Vue frontend ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- 2. Backend runtime (serves the API + the built frontend) ----------
FROM python:3.11-slim AS runtime

# DejaVu Sans is used to render the card overlays (rank/suit text).
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY default_description.md ./default_description.md
COPY --from=frontend-builder /src/frontend/dist ./frontend_dist

ENV DECK_DATA_DIR=/data \
    DECK_DEFAULT_DESCRIPTIONS=/app/default_description.md \
    DECK_FRONTEND_DIST=/app/frontend_dist \
    PYTHONUNBUFFERED=1

VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
