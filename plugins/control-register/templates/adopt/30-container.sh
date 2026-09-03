#!/usr/bin/env bash
# Stage 3 — the devcontainer: copied, substituted, and built. A surviving
# placeholder is what fails a build later at sha256sum -c, with no clue why.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/_lib.sh"
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" || exit 1

head_ "The template is in place (§ 4)"
if [ -d .devcontainer ]; then
  ok ".devcontainer exists"
else
  bad "no .devcontainer — the template has not been copied" "4"
  verdict 30-container.sh ""; exit 1
fi
if [ -f .devcontainer/README.md ]; then
  bad ".devcontainer/README.md is still there — it explains the placeholders" "4"
  note "While it exists, the placeholder check below can never come back clean."
else
  ok "the template README is gone"
fi

head_ "Nothing left to substitute (§ 4)"
left=$(grep -rl '{{' .devcontainer 2>/dev/null || true)
if [ -z "$left" ]; then
  ok "no {{PLACEHOLDER}} survives"
else
  bad "a placeholder survived" "4"
  printf '%s\n' "$left" | while IFS= read -r f; do note "$f"; done
fi

for key in UV_VERSION UV_SHA256_X86_64 UV_SHA256_AARCH64 PROJECT_NAME; do
  if grep -q "{{${key}}}" .devcontainer/* 2>/dev/null; then
    bad "{{${key}}} was never substituted" "4"
  fi
done

if [ -f .devcontainer/setup.sh ]; then
  if grep -qE 'sha256sum|[0-9a-f]{64}' .devcontainer/setup.sh; then
    ok "setup.sh carries a 64-character digest"
  else
    bad "setup.sh has no digest in it — the extraction yielded nothing" "4"
  fi
fi

head_ "Built (§ 4)"
if ! have docker || ! docker info >/dev/null 2>&1; then
  note "Docker is not answering, so whether the container exists cannot be read from here."
elif docker ps --format '{{.Labels}}' 2>/dev/null | grep -q "devcontainer.local_folder=$PWD"; then
  ok "a devcontainer for this folder is running"
else
  wait_on "no running container for this folder" "4"
  note "Expected until the container has been started. It is not a failure."
fi

echo
note "Everything after this stage runs INSIDE the container (§ 5)."
verdict 30-container.sh 40-adopt.sh
