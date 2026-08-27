# ADR 0039: A Push Is a Locus

**Status:** Accepted
**Date:** 2026-08-27
**Revision:** 1

## Background

A developer in this repository cannot run what CI runs before pushing, and
`CLAUDE.md` § Commands closes the gap by asking a person to remember four
commands:

```bash
uv run pre-commit run --all-files   # ruff, mypy, gitleaks, markdown, 3 controls
uv run pytest                       # TST-001 — ci is its only declared locus
uv run register-check               # the whole register; pre-commit runs three
uv sync --frozen                    # SUP-001 — the lockfile is current
```

Only the first is wired. The other three run because somebody remembers them,
and the gap is not evenly spread: the pre-commit hooks reach ruff, mypy,
gitleaks, markdownlint and three controls of fourteen, while the test suite and
the audit — the two checks most likely to fail a pull request — have no local
moment at all. A green commit is silent about exactly the things a reviewer will
see fail.

That is theme T-2 in its most ordinary dress. The four commands are a second
copy of the CI definition, held in prose, free to drift from
`.github/workflows/register-check.yml` the moment a step is added there. It was
added to the build plan on 2026-08-26 after a pull request's failures turned out
to be hosted-runner acquisition rather than the change — a different problem,
which made the absence of a local equivalent the expensive part of the day.

The obvious repair is the wrong one. A script in `scripts/` listing CI's steps
is the same second copy with a shebang on it: it would be free to drift from the
workflow it mirrors, and nothing would compare them. The register already has a
vocabulary for *where a control runs*, and the honest observation is that this
vocabulary is missing a value. `pre-commit` and `ci` are two moments; a push is
a third, and it is the one where a check too slow for every commit is still
cheap enough to run before a reviewer's time is spent.

## Decision

**`locus:` gains a fourth value, `pre-push`.**

It sits between `pre-commit` and `ci` on the same ladder and obeys the same
discipline — *pin once, reference many*. A control declaring it says: something
must enforce this before a push leaves the machine.

Four things follow.

**1. A pre-push locus is a hook in `.pre-commit-config.yaml` whose `stages:`
name `pre-push`.** pre-commit already models stages, and
`pre-commit install --hook-type pre-push` writes `.git/hooks/pre-push`. Nothing
new is installed, no second runner appears, and the file that already holds this
repository's local gates holds this one too.

**2. Stages are read in both directions.** Until now `_precommit_hooks` returned
every hook in the file and no caller asked which stage it ran at, which was
harmless while `pre-commit` was the only local locus and is not harmless now: a
hook staged `[pre-push]` would have satisfied a `pre-commit` locus, and a
control that runs only before a push would have reported itself as running
before every commit. The checker resolves a hook's stages the way pre-commit
does — the hook's own `stages`, else the file's `default_stages`, else every
stage — so a locus is credited to the moment the hook actually runs at.

**3. The controls that gain the locus are the ones whose only locus was `ci`
and whose verification a developer's machine can complete**: TST-001, SUP-001
and SUP-002. TST-001 is the criterion's own judge — delete a passing test and
the push refuses. SUP-001 and SUP-002 are read by the checker, and the hook that
reaches them names them: `register-check run --control SUP-001 --control
SUP-002`, the shape SUP-003's hook already uses.

**4. The pre-push run is selective, and that is forced rather than chosen.** A
full `uv run register-check` on a developer's machine exits `3`, permanently and
by design: SEC-003's two `kind: remote` blocks answer only inside a GitHub
Actions job, so outside one they are `UNCLASSIFIED` and the run is incomplete.
A hook running the full audit would therefore refuse every push, and the only
ways out are worse than the problem — a shell wrapper mapping `3` to `0` is a
tolerance nobody reads, and a flag that skips `kind: remote` blocks would report
SEC-003 as `PASS` on its file block alone, which is the substitution ADR 0016
exists to refuse. So the locus asks each control its own question, which is what
a locus has always been.

## Alternatives considered

**A `scripts/pre-push.sh` that runs the four commands.** Rejected by name in the
exit criterion, and rightly: it is a second copy of the CI definition. Nothing
would fail when a step was added to the workflow and not to the script, and the
failure mode is silence.

**Reuse the `pre-commit` locus and let the hooks be slow.** The test suite and
the audit on every commit is the fast feedback loop destroyed to save a
vocabulary word. Engineers respond by passing `--no-verify`, after which no
locus runs at all — which is worse than the state this ADR is fixing.

**Give the checker an `--allow-incomplete` flag so the full audit can run at
pre-push.** Rejected. It is a third exit-code posture alongside the default and
`--require-complete`, and its only user would be a locus that could get the same
answer by naming its controls. Worse, it would let any locus buy a `0` from a
run that verified nothing, which is the promotion `--require-complete` was added
to take away.

**Make SEC-003's remote blocks skip outside CI rather than report
`UNCLASSIFIED`.** This would let the full audit run green at pre-push, and it is
re-tiering a control to make a report green. ADR 0016 settled it: a control whose
verification could not be performed is `UNCLASSIFIED`, not a pass.

## Consequences

`git push` now runs the test suite and the two supply-chain controls, on top of
everything the pre-commit hooks already run. A push that would have failed CI on
a deleted test fails locally instead, which is the whole point.

**A wired locus is still not an installed hook.** `.pre-commit-config.yaml`
states intent and `.git/hooks/pre-push` is whether anything runs — the same
split this repository already records for `pre-commit`, with the same boundary:
`.git/hooks/` is untracked, so no control can check it. `setup.sh` installs both
hook types and `check-auth.sh` reports a missing one, reported and never
repaired.

**Three of the four remembered commands are now wired and one is not.**
`uv sync --frozen` stays in `CLAUDE.md` § Commands as a command a person runs,
and this ADR deliberately does not wire it. At the pre-push locus it would
verify the wrong thing: every hook above it invokes `uv run`, which re-locks on
disk before `--frozen` is ever reached, so the check would pass on a machine
whose `uv.lock` has been rewritten and not committed — the exact state that
fails CI. What SUP-001 gains here is its *control* being verified before a push,
which is a different and honest claim.

**The full audit still runs only in CI.** SEC-002 keeps `locus: [ci]` because no
gate deploys it — a locus nothing writes is a locus nobody installs — and the
three meta-controls declare no locus at all by construction. So a green push is
not a promise that `register-check` will exit `0` on the runner; it is a promise
about the controls that name this locus. Reading it as more than that is the
substitution this register spends most of its asserts refusing.
