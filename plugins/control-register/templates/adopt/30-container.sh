#!/usr/bin/env bash
#
# Stage 3 — the devcontainer.
#
# The failure this stage exists to catch is a surviving {{PLACEHOLDER}}. It is
# silent when you make it and fails a container build later at `sha256sum -c`,
# by which point nothing points back to the substitution that did not happen.

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_lib.sh"
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

# Register contract 39 holds these three in every repository, on either runtime.
# Their absence means the template came from a plugin older than 0.6.0 — usually
# a cache § 1's install left alone, because an install does not update.
missing=""
for file in bin/container-session.mjs package.json package-lock.json; do
  [ -f ".devcontainer/$file" ] || missing="$missing $file"
done
if [ -z "$missing" ]; then
  pass "the launcher and its pinned CLI are in place"
else
  fail "the template predates the launcher — missing:$missing" "4"
  detail "It was copied from an old plugin. § 1's update lines, then copy again."
fi

# --------------------------------------------------------------- substitutions

section "Nothing left to substitute (§ 4)"
# node_modules is the pinned CLI the Apple route installs, and its own code
# carries `{{`. It is installed, not substituted, so it is not read.
files_with_placeholders=$(grep -rl --exclude-dir=node_modules '{{' .devcontainer 2>/dev/null || true)
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
# Each runtime that answers is asked, so a container started on either is found
# (ADR 0065). The Apple launcher names the container after the folder.
asked=false
if installed docker && docker info >/dev/null 2>&1; then
  asked=true
  if grep -q "devcontainer.local_folder=$PWD" < <(docker ps --format '{{.Labels}}' 2>/dev/null); then
    pass "a devcontainer for this folder is running on Docker"
    running=true
  fi
fi
if installed container && container system status >/dev/null 2>&1; then
  asked=true
  apple_name="$(basename "$PWD")-dev"
  if container list --all --format json 2>/dev/null | node -e '
    let raw = "";
    process.stdin.on("data", (chunk) => { raw += chunk; });
    process.stdin.on("end", () => {
      const found = JSON.parse(raw || "[]").some(
        (c) => c.configuration?.id === process.argv[1] && c.status?.state === "running");
      process.exit(found ? 0 : 1);
    });' "$apple_name" 2>/dev/null; then
    pass "$apple_name is running on Apple container"
    running=true
  fi
fi

if [ "$asked" = false ]; then
  detail "No container runtime is answering, so whether the container exists cannot be read from here."
elif [ "${running:-false}" = false ]; then
  manual "no running container for this folder" "4"
  detail "Expected until the container has been started. It is not a failure."
fi

echo
detail "Everything after this stage runs INSIDE the container (§ 5)."
verdict 30-container.sh 40-adopt.sh
