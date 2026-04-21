#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEMPLATE_PATH="${REPO_ROOT}/openshift/app-template.yaml"

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Environment variable ${name} is required." >&2
    exit 1
  fi
}

command -v oc >/dev/null 2>&1 || {
  echo "The oc CLI is required." >&2
  exit 1
}

[ -f "${TEMPLATE_PATH}" ] || {
  echo "OpenShift template not found at ${TEMPLATE_PATH}." >&2
  exit 1
}

required_env_vars=(
  APP_NAME
  GIT_REPO_URL
  GIT_REF
  SECRET_KEY
  POSTGRES_DB
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_IMAGE
  ALLOWED_HOSTS
)

for env_var in "${required_env_vars[@]}"; do
  require_env "${env_var}"
done

: "${CSRF_TRUSTED_ORIGINS:=}"
: "${GUNICORN_WORKERS:=2}"
: "${POSTGRES_CONN_MAX_AGE:=120}"
: "${CPU_REQUEST:=50m}"
: "${CPU_LIMIT:=250m}"
: "${MEMORY_REQUEST:=256Mi}"
: "${MEMORY_LIMIT:=512Mi}"
: "${POSTGRES_STORAGE_SIZE:=1Gi}"
: "${POSTGRES_CPU_REQUEST:=50m}"
: "${POSTGRES_CPU_LIMIT:=250m}"
: "${POSTGRES_MEMORY_REQUEST:=256Mi}"
: "${POSTGRES_MEMORY_LIMIT:=512Mi}"

oc process -f "${TEMPLATE_PATH}" \
  -p "APP_NAME=${APP_NAME}" \
  -p "GIT_REPO_URL=${GIT_REPO_URL}" \
  -p "GIT_REF=${GIT_REF}" \
  -p "SECRET_KEY=${SECRET_KEY}" \
  -p "POSTGRES_DB=${POSTGRES_DB}" \
  -p "POSTGRES_USER=${POSTGRES_USER}" \
  -p "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" \
  -p "POSTGRES_IMAGE=${POSTGRES_IMAGE}" \
  -p "POSTGRES_STORAGE_SIZE=${POSTGRES_STORAGE_SIZE}" \
  -p "ALLOWED_HOSTS=${ALLOWED_HOSTS}" \
  -p "CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}" \
  -p "GUNICORN_WORKERS=${GUNICORN_WORKERS}" \
  -p "POSTGRES_CONN_MAX_AGE=${POSTGRES_CONN_MAX_AGE}" \
  -p "CPU_REQUEST=${CPU_REQUEST}" \
  -p "CPU_LIMIT=${CPU_LIMIT}" \
  -p "MEMORY_REQUEST=${MEMORY_REQUEST}" \
  -p "MEMORY_LIMIT=${MEMORY_LIMIT}" \
  -p "POSTGRES_CPU_REQUEST=${POSTGRES_CPU_REQUEST}" \
  -p "POSTGRES_CPU_LIMIT=${POSTGRES_CPU_LIMIT}" \
  -p "POSTGRES_MEMORY_REQUEST=${POSTGRES_MEMORY_REQUEST}" \
  -p "POSTGRES_MEMORY_LIMIT=${POSTGRES_MEMORY_LIMIT}" \
  | oc apply -f -
