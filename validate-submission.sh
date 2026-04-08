#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if ! command -v openenv >/dev/null 2>&1; then
  echo "openenv CLI not found"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl not found"
  exit 1
fi

if [[ -z "${HF_SPACE_URL:-}" ]]; then
  echo "HF_SPACE_URL is required"
  exit 1
fi

openenv validate
docker build -t operational-risk-triage:latest .
status_code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "${HF_SPACE_URL%/}/reset")"
if [[ "$status_code" != "200" ]]; then
  echo "HF Space /reset check failed with HTTP ${status_code}"
  exit 1
fi
