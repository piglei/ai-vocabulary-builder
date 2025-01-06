# ============================ Stage 1: Build Frontend ============================ #
FROM node:22-alpine3.20 AS frontend-builder
WORKDIR /app/voc_frontend
COPY voc_frontend/package*.json ./
RUN npm install
COPY voc_frontend/ ./
RUN VITE_AIVOC_API_ENDPOINT='' npm run build-only
# ================= Stage 2: Build Python Dependencies with Poetry ================ #
FROM python:3.10-slim AS builder
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi
COPY --from=frontend-builder /app/voc_frontend/dist ./voc_builder/notepad/dist
COPY voc_builder ./voc_builder
# ========================== Stage 3: Final Runtime Image ========================= #
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /app/voc_builder ./voc_builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
EXPOSE 16093
CMD ["python", "-m", "voc_builder.main", "notebook", "--host", "0.0.0.0"]