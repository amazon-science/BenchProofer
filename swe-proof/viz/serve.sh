#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Serve the review site, bound to 127.0.0.1 ONLY. The site renders unpublished
# artifacts and accepts comments with no authentication of its own, so SSH is the
# access perimeter: to read it from elsewhere, forward the port (connect.sh).
#
#   bash viz/serve.sh            # ONE site, every benchmark x backend cell,
#                                # port 9000: /{benchmark}/{backend}/...
#
# Nothing here depends on an activated environment, so it is safe to launch from
# any shell. Point VIZ_PYTHON at the interpreter holding the `viz` extra if it is
# not the one on PATH.
#
# RESTART IS WHAT DEPLOYS. One process serves the whole site and is pinned to the
# code, the templates and the app.css fingerprint it started with (see
# backend/app.py:_pin_templates), so an edit under viz/ shows up when this script
# is run again and not before.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

HOST="${VIZ_HOST:-127.0.0.1}"
PORT="${VIZ_PORT:-9000}"

# refuse to bind a non-loopback interface unless explicitly forced (safety)
if [[ "$HOST" != "127.0.0.1" && "$HOST" != "localhost" && "${VIZ_ALLOW_PUBLIC:-0}" != "1" ]]; then
  echo "REFUSING to bind $HOST (not loopback). Set VIZ_ALLOW_PUBLIC=1 to override." >&2
  exit 1
fi

# fail early if the port is taken, rather than after the import cost
if command -v ss >/dev/null && ss -tlnp 2>/dev/null | grep -q ":${PORT}\b"; then
  echo "Port ${PORT} is already in use. Set VIZ_PORT to a free port." >&2
  exit 1
fi

PYBIN="${VIZ_PYTHON:-}"
if [[ -z "$PYBIN" ]]; then
  PYBIN="$(command -v python3 || command -v python || true)"
fi
if [[ ! -x "$PYBIN" ]]; then
  echo "No python found. Set VIZ_PYTHON=/path/to/python (the one with the viz extra)." >&2
  exit 1
fi
if ! "$PYBIN" -c 'import uvicorn' 2>/dev/null; then
  echo "$PYBIN cannot import uvicorn. Install the extra: pip install -e '.[viz]'" >&2
  echo "or set VIZ_PYTHON to an interpreter that has it." >&2
  exit 1
fi
if [[ ! -f "$REPO_ROOT/viz/static/vendor/htmx.min.js" || ! -f "$REPO_ROOT/viz/static/vendor/pygments.css" ]]; then
  echo "warning: viz/static/vendor/ is missing htmx or the Pygments stylesheet;" >&2
  echo "run: bash scripts/fetch_vendor.sh viz" >&2
fi

echo "Review site: http://${HOST}:${PORT}  (loopback only; tunnel in via connect.sh)"
exec nice -n 10 "$PYBIN" -m uvicorn backend.app:app \
  --app-dir "$REPO_ROOT/viz" --host "$HOST" --port "$PORT" --no-access-log
