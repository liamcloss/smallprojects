#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p backups data/backups

# SQLite online backup while the app remains running.
docker compose exec -T content-factory python - "$STAMP" <<'PY'
import sqlite3
import sys
from pathlib import Path
stamp = sys.argv[1]
src = Path('/app/data/content_factory.sqlite3')
dst = Path('/app/data/backups') / f'content_factory-{stamp}.sqlite3'
dst.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(src) as source, sqlite3.connect(dst) as target:
    source.backup(target)
print(dst)
PY

tar -czf "backups/content-factory-$STAMP.tar.gz" \
  "data/backups/content_factory-$STAMP.sqlite3" output 2>/dev/null || \
  tar -czf "backups/content-factory-$STAMP.tar.gz" "data/backups" output

echo "Backup created: backups/content-factory-$STAMP.tar.gz"
