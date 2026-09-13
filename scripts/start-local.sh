#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID=""
EXISTING_BACKEND_PID=""
FRONTEND_PID=""
EXISTING_FRONTEND_PID=""
PU_API_PID=""

cleanup() {
  trap - EXIT INT TERM
  for pid in "$PU_API_PID" "$FRONTEND_PID" "$BACKEND_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$ROOT_DIR"

if ! command -v bun >/dev/null 2>&1; then
  echo "Error: bun is required. Install dependencies with bun install." >&2
  exit 1
fi

if [[ ! -x "$ROOT_DIR/backend/.venv/bin/uvicorn" ]]; then
  echo "Error: backend/.venv is missing or incomplete." >&2
  echo "Run: python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

mkdir -p "${CASE_STORAGE_ROOT:-$ROOT_DIR/backend/runtime/cases}"

EXISTING_BACKEND_PID="$(lsof -tiTCP:8001 -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [[ -n "$EXISTING_BACKEND_PID" ]]; then
  if ! "$ROOT_DIR/backend/.venv/bin/python" - <<'PY'
import json
from urllib.request import urlopen

with urlopen("http://127.0.0.1:8001/health", timeout=2) as response:
    payload = json.load(response)
if payload.get("product") != "RedFlags":
    raise SystemExit(1)
PY
  then
    echo "Error: port 8001 is already in use by a different service." >&2
    exit 1
  fi
  echo "Backend already running on http://localhost:8001; reusing PID $EXISTING_BACKEND_PID."
else
  "$ROOT_DIR/backend/.venv/bin/uvicorn" backend.app.main:app --host 127.0.0.1 --port 8001 &
  BACKEND_PID=$!
fi

EXISTING_FRONTEND_PID="$(lsof -tiTCP:3000 -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [[ -n "$EXISTING_FRONTEND_PID" ]]; then
  echo "Frontend already running on http://localhost:3000; reusing PID $EXISTING_FRONTEND_PID."
else
  bun dev &
  FRONTEND_PID=$!
fi

if [[ "${1:-}" == "--with-pu-api" ]]; then
  PU_PYTHON="$ROOT_DIR/PU-HackMTY/.venv/bin/python"
  if [[ ! -x "$PU_PYTHON" ]]; then
    echo "Error: PU-HackMTY/.venv is missing or incomplete." >&2
    echo "Create it with: python3 -m venv PU-HackMTY/.venv && PU-HackMTY/.venv/bin/pip install -r PU-HackMTY/requirements.txt" >&2
    exit 1
  fi
  (
    cd "$ROOT_DIR/PU-HackMTY"
    "$PU_PYTHON" -m api.server --host 127.0.0.1 --port 8765 --runs runs --out-root data_estate/out/live
  ) &
  PU_API_PID=$!
fi

echo "RedFlags is running at http://localhost:3000/dashboard"
echo "Backend API: http://localhost:8001/health"
if [[ -n "$PU_API_PID" ]]; then
  echo "PU evaluation API: http://localhost:8765/health"
fi
echo "Press Ctrl-C to stop all services."

while true; do
  if [[ -n "$BACKEND_PID" ]] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    exit 1
  fi
  if [[ -n "$EXISTING_BACKEND_PID" ]] && ! kill -0 "$EXISTING_BACKEND_PID" 2>/dev/null; then
    exit 1
  fi
  if [[ -n "$FRONTEND_PID" ]] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    exit 1
  fi
  if [[ -n "$EXISTING_FRONTEND_PID" ]] && ! kill -0 "$EXISTING_FRONTEND_PID" 2>/dev/null; then
    exit 1
  fi
  if [[ -n "$PU_API_PID" ]] && ! kill -0 "$PU_API_PID" 2>/dev/null; then
    exit 1
  fi
  sleep 1
done
