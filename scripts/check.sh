#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

cd "$repo_root"
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
PYTHONPATH=backend .venv/bin/pytest -c backend/pyproject.toml backend/tests

cd "$repo_root/frontend"
npm test
npm run typecheck
npm run build

cd "$repo_root"
git diff --check
