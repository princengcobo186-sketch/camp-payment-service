#!/usr/bin/env bash
# Chart checks using only helm (no plugins): lint, security posture of the rendered
# Deployment, and that the schema rejects unsafe values. Run by `make chart-check` and CI.
set -euo pipefail

chart="chart/payment-service"
good=(--set image.repository=camp/payment-service --set image.tag=abc1234 --set env.APP_ENV=dev)

helm lint "${chart}" "${good[@]}"

rendered="$(helm template t "${chart}" "${good[@]}")"

expect() { # description, fixed string that must appear in the rendered manifest
  grep -qF -- "$2" <<< "${rendered}" || { echo "FAIL: $1 (missing: $2)" >&2; exit 1; }
  echo "ok: $1"
}
expect "runs as non-root" "runAsNonRoot: true"
expect "root filesystem is read-only" "readOnlyRootFilesystem: true"
expect "privilege escalation disabled" "allowPrivilegeEscalation: false"
expect "all capabilities dropped" "drop: [ALL]"
expect "image uses the given immutable tag" "image: \"camp/payment-service:abc1234\""
expect "no service account token mounted" "automountServiceAccountToken: false"

reject() { # description, helm args that must make rendering fail
  local desc="$1"; shift
  if helm template t "${chart}" "$@" > /dev/null 2>&1; then
    echo "FAIL: ${desc} was accepted" >&2; exit 1
  fi
  echo "ok: rejects ${desc}"
}
reject "the latest tag" --set image.repository=x --set image.tag=latest --set env.APP_ENV=dev
reject "a missing APP_ENV" --set image.repository=x --set image.tag=abc
reject "an unknown APP_ENV" --set image.repository=x --set image.tag=abc --set env.APP_ENV=qa
reject "a missing image repository" --set image.tag=abc --set env.APP_ENV=dev
