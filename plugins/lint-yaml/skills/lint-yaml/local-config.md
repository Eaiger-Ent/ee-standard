# Local configuration

Read at pre-flight, before Step 1. It exists so that a repository can pin **what
every locus runs** without forking the skill.

**Absent file, absent key, absent value — take the default below.** The default
changed in this version: it was the bare name `yamllint`, which resolves from
`PATH`, so nothing tied what the hook ran to the version the other loci used. It
is now a pinned invocation, resolved in Step 1.

## Where

`.claude/skill-config.yaml` in the target repository, keyed by skill name:

```yaml
lint-yaml:
  invocation: python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))"
```

Read it once at pre-flight. If the file is absent, unparseable, or has no
`lint-yaml` key, take the default and say so in one line — an unreadable
configuration is a fact worth reporting, not a reason to stop.

## What is read

| Key | Default | Used at |
| --- | --- | --- |
| `invocation` | `uv run yamllint` with a `pyproject.toml`, else `uvx --from yamllint==<version> yamllint` (Step 1) | Step 2.5a, the `LINT_INVOCATION` line of `.claude/hooks/yaml-lint.py`; Step 3, the pre-commit hook's `entry:`; Step 4, the CI step's `run:` |

Store it as `YAMLLINT_INVOCATION`.

**Write it verbatim.** A key that is present replaces the default entirely; a key
that is absent takes it.

One value, three loci. The hook, the pre-commit hook and the CI step all run
it, so a commit is checked by the same `yamllint` CI uses. Until this version
the pre-commit hook resolved through a `rev:`-pinned `adrienverge/yamllint`
mirror and CI ran `pip install yamllint`. That was three versions in three
places, and one of them pinned nothing.

## Why a repository would set it

A repository that wants feedback on every save but cannot take `yamllint` as a
dependency can point every locus at a command it already has. A
syntax-only `python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))"`
catches the class of error that actually breaks a build, without asserting a
style the repository never adopted — which is the honest option for a repository
with a large body of YAML written before any linter was chosen.

The alternative is not "configure nothing": it is a hook that reports a few
hundred pre-existing style violations on every save, which is a hook everybody
learns to ignore.

A configured value that is not `yamllint` still receives `-c .yamllint.yml` when
that file exists, because the hook passes the config through the same argument
list. A repository that sets both is asking for a command it did not mean; keep
one or the other.

## Report what you used

In the run's output, name the value when it came from configuration rather than
from the default — `invocation: python3 -c "…" (from .claude/skill-config.yaml)`.
The person approving a write sees a diff and nothing else, and a value that
differs from this skill's default is exactly the thing they need told.
