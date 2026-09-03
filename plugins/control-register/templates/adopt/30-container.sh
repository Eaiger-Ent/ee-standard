#!/usr/bin/env bash
#
# Stage 3 — the devcontainer.
#
# The failure this stage exists to catch is a surviving {{PLACEHOLDER}}. It is
# silent when you make it and fails a container build later at `sha256sum -c`,
# by which point nothing points back to the substitution that did not happen.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
. ./_lib.sh
cd "$(repository_root)" || exit 1

# ------------------------------------------------------------- template copied

section "The template is in place (§ 4)"
if [ ! -d .devcontainer ]; then
  fail "no .devcontainer — the template has not been copied" "4"
  verdict 30-container.sh ""
  exit 1
fi
pass ".devcontainer exists"

if [ -f .devcontainer/README.md ]; then
  fail ".devcontainer/README.md is still there — it explains the placeholders" "4"
  detail "While it exists, the placeholder check below can never come back clean."
else
  pass "the template README is gone"
fi

# --------------------------------------------------------------- substitutions

section "Nothing left to substitute (§ 4)"
files_with_placeholders=$(grep -rl '{{' .devcontainer 2>/dev/null || true)
if [ -z "$files_with_placeholders" ]; then
  pass "no {{PLACEHOLDER}} survives"
else
  fail "a placeholder survived" "4"
  printf '%s\n' "$files_with_placeholders" | while IFS= read -r file; do
    detail "$file"
  done
fi

for placeholder in UV_VERSION UV_SHA256_X86_64 UV_SHA256_AARCH64 PROJECT_NAME; do
  if grep -q "{{${placeholder}}}" .devcontainer/* 2>/dev/null; then
    fail "{{${placeholder}}} was never substituted" "4"
  fi
done

# A digest is 64 hex characters. Its absence means the extraction yielded
# nothing and the substitution wrote emptiness over the placeholder.
if [ -f .devcontainer/setup.sh ]; then
  if grep -qE '[0-9a-f]{64}' .devcontainer/setup.sh; then
    pass "setup.sh carries a 64-character digest"
  else
    fail "setup.sh has no digest in it — the extraction yielded nothing" "4"
  fi
fi

# ---------------------------------------------------------------------- built

section "Built (§ 4)"
if ! installed docker || ! docker info >/dev/null 2>&1; then
  detail "Docker is not answering, so whether the container exists cannot be read from here."
elif docker ps --format '{{.Labels}}' 2>/dev/null | grep -q "devcontainer.local_folder=$PWD"; then
  pass "a devcontainer for this folder is running"
else
  manual "no running container for this folder" "4"
  detail "Expected until the container has been started. It is not a failure."
fi

echo
detail "Everything after this stage runs INSIDE the container (§ 5)."
verdict 30-container.sh 40-adopt.sh
