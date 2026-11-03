#!/usr/bin/env bash
# SessionStart: ask the assistant whether a stack has arrived that no installed
# Craft profile covers.
#
# **This script evaluates nothing, and that is the design.** Craft's stack
# conditions are a sentence the installer implements (`docs/craft/build.installer.md`
# § The predicate grammar cannot say *react is a dependency*), held once as the
# table in `craft-install`'s pre-flight step 3. A shell copy of *package.json
# declares react* would be a second implementation of that sentence, free to
# disagree with the first. So this script finds the pin and points at the table,
# and the assistant reads the table where it already lives.
#
# Why it exists: in Craft's first trial, React arrived three weeks after the
# install, 9,018 lines of TypeScript followed it, and nothing said a stack had
# arrived with no profile (`docs/craft/review.trial.md` § React arrived, and
# Craft did not notice).
#
# Silent unless `craft-install` has run here. A repository that never chose a
# profile is not owed a notice about one, and a notice in every session of
# every repository with the plugin installed is one people learn to skip.
# Always exits 0: this is a notice, never a gate.
set -u

config=".claude/skill-config.yaml"
[ -f "$config" ] || exit 0

# The `craft-install:` block, verbatim, up to the next top-level key. Printed
# rather than parsed: the assistant reads YAML better than this script would,
# and a parser here would be one more reader to keep in step with the format.
pin=$(awk '
  /^craft-install:/ { inside = 1; print; next }
  inside && /^[^[:space:]#]/ { exit }
  inside { print }
' "$config")
[ -n "$pin" ] || exit 0

skill="${CLAUDE_PLUGIN_ROOT:-}/skills/craft-install/SKILL.md"

cat <<EOF
Craft: this repository pins the profiles below, in $config.

$pin

Before your first reply in this session, check whether a stack has arrived that
no pinned profile covers. Apply the table in $skill under this heading:

  Read the repository, and never a self-declaration

A stack applies only when every condition in its row holds, read from the files
rather than from anything that declares a stack. If one applies and has no profile pinned, tell the user once, name the
condition that now holds, and suggest /craft-install. Install nothing yourself,
and say nothing if every applicable stack is pinned.
EOF
exit 0
