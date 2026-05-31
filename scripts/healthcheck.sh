#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
WEB_URL="${WEB_URL:-http://localhost:3000}"

curl -fsS "$API_URL/health"
echo
curl -fsS "$WEB_URL" >/dev/null
echo "GyuTron healthcheck passed."
