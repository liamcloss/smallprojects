FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .

RUN mkdir -p /app/output /app/data

EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
