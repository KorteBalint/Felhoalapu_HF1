#!/usr/bin/env bash
set -euo pipefail

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

require_env APP_NAME

: "${POSTGRES_PVC_TIMEOUT_SECONDS:=300}"
: "${POSTGRES_DEPLOYMENT_TIMEOUT_SECONDS:=300}"

PVC_NAME="${APP_NAME}-postgres-data"
DEPLOYMENT_NAME="${APP_NAME}-postgres"
PVC_DEADLINE=$((SECONDS + POSTGRES_PVC_TIMEOUT_SECONDS))

while [ "${SECONDS}" -lt "${PVC_DEADLINE}" ]; do
  pvc_phase="$(oc get "pvc/${PVC_NAME}" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  if [ "${pvc_phase}" = "Bound" ]; then
    break
  fi
  sleep 5
done

if [ "${pvc_phase:-}" != "Bound" ]; then
  echo "PVC ${PVC_NAME} did not reach Bound within ${POSTGRES_PVC_TIMEOUT_SECONDS} seconds." >&2
  oc get "pvc/${PVC_NAME}" >&2 || true
  exit 1
fi

oc rollout status "deployment/${DEPLOYMENT_NAME}" \
  --watch=true \
  --timeout="${POSTGRES_DEPLOYMENT_TIMEOUT_SECONDS}s"
