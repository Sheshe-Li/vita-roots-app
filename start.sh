#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# FamilyWellness — local dev startup (no Docker)
# Starts: Phoenix Arize · Langflow · FastAPI backend · Next.js frontend
#
# Usage:
#   ./start.sh          # start everything
#   ./start.sh backend  # backend only
#   ./start.sh frontend # frontend only
#   ./start.sh phoenix  # phoenix only
#   ./start.sh langflow # langflow only
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOG_DIR="$ROOT/.logs"
mkdir -p "$LOG_DIR"

# ── colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*"; }
heading() { echo -e "\n${GREEN}━━━ $* ━━━${NC}"; }

# ── preflight checks ──────────────────────────────────────────────────────────
check_command() {
  if ! command -v "$1" &>/dev/null; then
    error "$1 is not installed. $2"
    exit 1
  fi
}

check_command python3 "Install Python 3.11+ from https://python.org"
check_command node    "Install Node.js 18+ from https://nodejs.org"
check_command npm     "Install Node.js 18+ from https://nodejs.org"

# ── .env setup ────────────────────────────────────────────────────────────────
if [ ! -f "$BACKEND/.env" ]; then
  warn "No backend/.env found — copying from .env.example"
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  warn "⚠  Open backend/.env and set your ANTHROPIC_API_KEY before continuing."
  echo ""
  read -rp "Press Enter once you've set ANTHROPIC_API_KEY in backend/.env, or Ctrl+C to abort... "
fi

# Validate API key is set
API_KEY=$(grep ANTHROPIC_API_KEY "$BACKEND/.env" | cut -d= -f2 | xargs)
if [[ -z "$API_KEY" || "$API_KEY" == "your_key_here" ]]; then
  error "ANTHROPIC_API_KEY is not set in backend/.env"
  error "Get your key at https://console.anthropic.com and add it to backend/.env"
  exit 1
fi

# ── Python venv ───────────────────────────────────────────────────────────────
VENV="$BACKEND/.venv"
if [ ! -d "$VENV" ]; then
  heading "Creating Python virtual environment"
  python3 -m venv "$VENV"
fi

PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"

heading "Installing Python dependencies"
"$PIP" install --quiet --upgrade pip
"$PIP" install --quiet -r "$BACKEND/requirements.txt"
info "Python dependencies installed"

# ── Node deps ─────────────────────────────────────────────────────────────────
if [ ! -d "$FRONTEND/node_modules" ]; then
  heading "Installing Node.js dependencies"
  cd "$FRONTEND" && npm install --silent
  info "Node dependencies installed"
fi

# ── helper: start a process in background ────────────────────────────────────
start_service() {
  local name="$1"
  local log="$LOG_DIR/${name}.log"
  local pid_file="$LOG_DIR/${name}.pid"
  shift

  # Kill existing if running
  if [ -f "$pid_file" ]; then
    local old_pid
    old_pid=$(cat "$pid_file")
    if kill -0 "$old_pid" 2>/dev/null; then
      warn "$name already running (PID $old_pid) — restarting"
      kill "$old_pid" 2>/dev/null || true
      sleep 1
    fi
  fi

  info "Starting $name → logs at .logs/${name}.log"
  "$@" > "$log" 2>&1 &
  echo $! > "$pid_file"
}

# ── determine what to start ───────────────────────────────────────────────────
TARGET="${1:-all}"

# ── Phoenix Arize ─────────────────────────────────────────────────────────────
start_phoenix() {
  heading "Phoenix Arize  →  http://localhost:6006"
  if "$PYTHON" -c "import phoenix" 2>/dev/null; then
    start_service "phoenix" \
      "$PYTHON" -m phoenix.server.main \
        --host 0.0.0.0 \
        --port 6006 \
        --no-internet
    sleep 2
    info "Phoenix running at http://localhost:6006"
  else
    warn "Phoenix not importable — it may still be installing. Check .logs/phoenix.log"
  fi
}

# ── Langflow ──────────────────────────────────────────────────────────────────
start_langflow() {
  heading "Langflow  →  http://localhost:7860"
  # Langflow is a separate pip package — install if missing
  if ! "$PYTHON" -c "import langflow" 2>/dev/null; then
    warn "Langflow not found — installing (this takes ~2 min the first time)..."
    "$PIP" install --quiet langflow
  fi
  start_service "langflow" \
    "$PYTHON" -m langflow run \
      --host 0.0.0.0 \
      --port 7860 \
      --no-open-browser
  sleep 3
  info "Langflow running at http://localhost:7860"
  info "Import the flow: Langflow → + New Flow → Import → langflow/wellness_agent_flow.json"
}

# ── FastAPI backend ───────────────────────────────────────────────────────────
start_backend() {
  heading "FastAPI Backend  →  http://localhost:8000"
  start_service "backend" \
    "$VENV/bin/uvicorn" main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --reload \
      --app-dir "$BACKEND" \
      --log-level info
  sleep 2
  # Quick health check
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    info "Backend healthy at http://localhost:8000"
  else
    warn "Backend may still be starting — check .logs/backend.log"
  fi
}

# ── Next.js frontend ──────────────────────────────────────────────────────────
start_frontend() {
  heading "Next.js Frontend  →  http://localhost:3000"
  cd "$FRONTEND"
  start_service "frontend" npm run dev
  sleep 3
  info "Frontend running at http://localhost:3000"
  info "Demo route: http://localhost:3000/demo"
}

# ── run targets ───────────────────────────────────────────────────────────────
case "$TARGET" in
  all)
    start_phoenix
    start_langflow
    start_backend
    start_frontend
    ;;
  phoenix)  start_phoenix  ;;
  langflow) start_langflow ;;
  backend)  start_backend  ;;
  frontend) start_frontend ;;
  *)
    error "Unknown target: $TARGET"
    echo "Usage: ./start.sh [all|backend|frontend|phoenix|langflow]"
    exit 1
    ;;
esac

# ── summary ───────────────────────────────────────────────────────────────────
if [[ "$TARGET" == "all" ]]; then
  heading "All services started"
  echo ""
  echo -e "  ${GREEN}Frontend${NC}  →  http://localhost:3000"
  echo -e "  ${GREEN}Demo${NC}      →  http://localhost:3000/demo"
  echo -e "  ${GREEN}Backend${NC}   →  http://localhost:8000"
  echo -e "  ${GREEN}API docs${NC}  →  http://localhost:8000/docs"
  echo -e "  ${GREEN}Phoenix${NC}   →  http://localhost:6006"
  echo -e "  ${GREEN}Langflow${NC}  →  http://localhost:7860"
  echo ""
  echo -e "  Logs →  .logs/  (backend.log · frontend.log · phoenix.log · langflow.log)"
  echo ""
  warn "Press Ctrl+C to stop watching logs, then run ./stop.sh to kill all services"
  echo ""
  # Tail all logs so you can see what's happening
  tail -f "$LOG_DIR"/*.log
fi
