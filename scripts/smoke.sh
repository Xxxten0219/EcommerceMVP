#!/usr/bin/env bash

set -euo pipefail

frontend_url=${FRONTEND_URL:-http://localhost:8080}
api_url=${API_URL:-http://localhost:8000}

health=$(curl --fail --silent --show-error "$api_url/api/v1/health")
HEALTH_PAYLOAD="$health" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["HEALTH_PAYLOAD"])
assert payload["status"] == "ok", payload
assert payload["database"] == "ok", payload
assert payload["mock_mode"] is True, payload
PY

departments=$(curl --fail --silent --show-error "$api_url/api/v1/departments")
DEPARTMENT_PAYLOAD="$departments" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["DEPARTMENT_PAYLOAD"])
assert {item["code"] for item in payload} == {"artwork", "sales", "selection"}, payload
PY

homepage=$(curl --fail --silent --show-error "$frontend_url/")
case "$homepage" in
  *EcommerceMVP*) ;;
  *) echo "Frontend response does not contain EcommerceMVP" >&2; exit 1 ;;
esac

echo "Smoke check passed: frontend=$frontend_url api=$api_url"
