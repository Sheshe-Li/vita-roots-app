#!/usr/bin/env bash
# Kill all FamilyWellness dev services

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT/.logs"

GREEN='\033[0;32m'; NC='\033[0m'

for service in backend frontend phoenix langflow; do
  pid_file="$LOG_DIR/${service}.pid"
  if [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
      echo -e "${GREEN}[✓]${NC} Stopped $service (PID $pid)"
    fi
    rm -f "$pid_file"
  fi
done

echo "All services stopped."
