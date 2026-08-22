#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/apps/tiktok-content-factory}"
REPO_URL="${REPO_URL:-https://github.com/liamcloss/smallprojects.git}"
REPO_BRANCH="${REPO_BRANCH:-tiktok-content-factory}"

command -v docker >/dev/null 2>&1 || { echo "Docker is required on HEX." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is required on HEX." >&2; exit 1; }

if [ ! -d "$APP_DIR/.git" ]; then
  mkdir -p "$(dirname "$APP_DIR")"
  git clone --branch "$REPO_BRANCH" --single-branch "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" fetch origin "$REPO_BRANCH"
  git -C "$APP_DIR" checkout "$REPO_BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$REPO_BRANCH"
fi

cd "$APP_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "Created $APP_DIR/.env"
  echo "Add OPENAI_API_KEY plus APP_AUTH_USERNAME/APP_AUTH_PASSWORD, then rerun this script."
  exit 2
fi

if ! grep -Eq '^OPENAI_API_KEY=.+$' .env; then
  echo "OPENAI_API_KEY is missing from $APP_DIR/.env" >&2
  exit 2
fi

mkdir -p data output
docker compose up -d --build --remove-orphans
docker compose ps

echo
echo "TikTok Content Factory is running on HEX port 8787."
echo "Health: http://127.0.0.1:8787/health"
