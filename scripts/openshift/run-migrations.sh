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

: "${MIGRATION_POD_TIMEOUT_SECONDS:=300}"
: "${MIGRATION_CONTAINER:=web}"

LATEST_VERSION=""
POD_NAME=""
DEADLINE=$((SECONDS + MIGRATION_POD_TIMEOUT_SECONDS))

while [ "${SECONDS}" -lt "${DEADLINE}" ]; do
  LATEST_VERSION="$(oc get "dc/${APP_NAME}" -o jsonpath='{.status.latestVersion}' 2>/dev/null || true)"

  if [ -n "${LATEST_VERSION}" ] && [ "${LATEST_VERSION}" != "0" ]; then
    POD_NAME="$({
      oc get pods \
        -l "deployment=${APP_NAME}-${LATEST_VERSION}" \
        --field-selector=status.phase=Running \
        --sort-by=.metadata.creationTimestamp \
        -o name 2>/dev/null \
        | tail -n 1 \
        | cut -d/ -f2
    } || true)"

    if [ -z "${POD_NAME}" ]; then
      POD_NAME="$({
        oc get pods \
          --field-selector=status.phase=Running \
          --sort-by=.metadata.creationTimestamp \
          -o name 2>/dev/null \
          | grep -E "^pod/${APP_NAME}-${LATEST_VERSION}-" \
          | grep -v -- "-deploy$" \
          | tail -n 1 \
          | cut -d/ -f2
      } || true)"
    fi

    if [ -n "${POD_NAME}" ]; then
      break
    fi
  fi

  sleep 5
done

if [ -z "${POD_NAME}" ]; then
  echo "No running pod found for dc/${APP_NAME} latestVersion=${LATEST_VERSION:-unknown} within ${MIGRATION_POD_TIMEOUT_SECONDS} seconds." >&2
  oc get "dc/${APP_NAME}" >&2 || true
  oc get pods -l "deploymentconfig=${APP_NAME}" -o wide >&2 || true
  exit 1
fi

oc exec "pod/${POD_NAME}" -c "${MIGRATION_CONTAINER}" -- python manage.py migrate --noinput
