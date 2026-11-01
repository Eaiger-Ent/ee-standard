# Local configuration

Read at pre-flight, before Step 1. It exists so that a repository can pin **what
this skill writes** without forking the skill or arguing a value upstream.

**Absent file, absent key, absent value — behave exactly as this skill always
has.** Every default below is what the skill did before local configuration
existed, so a repository that has never heard of this gets what it got before.

## Where

`.claude/skill-config.yaml` in the target repository, keyed by skill name:

```yaml
lint-md:
  invocation: node_modules/.bin/markdownlint-cli2
  ignores: []
```

Read it once at pre-flight. If the file is absent, unparseable, or has no
`lint-md` key, take every default and say so in one line — an unreadable
configuration is a fact worth reporting, not a reason to stop.

## What is read

| Key | Default | Used at |
| --- | --- | --- |
| `invocation` | `npx --no-install markdownlint-cli2` | every locus: the pre-commit hook, the CI step, the DevContainer check, the PostToolUse hook and every verification command |
| `ignores` | `["**/node_modules/**", "**/.venv/**", "**/.terraform/**", "**/.pnpm-store/**"]` | Step 2b, `.markdownlint-cli2.yaml` |

Store them as `CLI2_INVOCATION` and `CLI2_IGNORES`.

**Write them verbatim.** Do not append the defaults to a configured value, and
do not merge the two lists: a repository that sets `ignores: []` means *ignore
nothing*, and a merge would hand back the entries it removed. A key that is
present replaces the default entirely; a key that is absent takes it.

## Why a repository would set either

**`invocation`** — `npx --no-install` does not mean *resolve locally*. With no
local install it falls through to `PATH` and runs whichever global copy it
finds, which makes a lockfile an authority in name only. A repository that pins
`markdownlint-cli2` in `package-lock.json` and wants every locus to reach *that*
binary sets `node_modules/.bin/markdownlint-cli2`.

**`ignores`** — the default no longer includes `.claude/**`, and the four
entries that remain are all build or dependency directories nobody authors.
`.claude/**` was aimed at Claude's auto-memory, but those files live under
`$HOME`, outside the repository, so a repo-root `**/*.md` glob never reaches
them: the entry could only ever hide what the repository itself authors under
`.claude/` — hooks, agent definitions, skills, commands — which is tracked,
authored Markdown in any repository that keeps them. An exemption that cannot
reach its target and does reach tracked files is not a scope, it is a silence.

A repository that genuinely wants Claude's own files unlinted can still add the
entry back; what it can no longer do is inherit it without deciding. The four
remaining entries are safe to default because they name directories the
repository does not write — and a repository that gitignores them can set
`ignores: []` and let `gitignore: true` do the scoping instead.

Neither value is this skill's to decide for every repository, which is the whole
reason they are inputs.

## Report what you used

In the run's output, name any value that came from configuration rather than
from the default — `invocation: node_modules/.bin/markdownlint-cli2 (from
.claude/skill-config.yaml)`. The person approving a write sees a diff and
nothing else, and a value that differs from this skill's default is exactly the
thing they need told.
