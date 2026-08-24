# ADR 0028: Raise the Support Floor to the Interpreter We Actually Run

**Status:** Accepted
**Date:** 2026-08-24
**Revision:** 1

## Background

`requires-python = ">=3.13"` says `standard-check` works on Python 3.13. It is
published in the package's wheel metadata, read by every installer, and adopters
install the checker as a dependency — so it is a promise made to people this
repository does not know.

Nobody made it. It was written when 3.13 was the version the devcontainer
happened to install, at a point where no other number existed to write. It has
never been a decision about which adopters to support, and until
[ADR 0027](0027-the-interpreter-is-a-pinned-tool.md) it was not even a
constraint — it was the *only* constraint, which is how the gates came to run on
3.13 locally and 3.14 in CI.

ADR 0027 fixed that by separating the environment from the claim, and then
raised the environment to 3.14. That left the claim standing alone for the first
time, and made its cost visible:

- **A second full test run on every pull request.** `support-floor.yml` exists
  because a claim tested nowhere is the shape this repository exists to catch.
  It runs the suite on 3.13 — around 35 seconds, plus an interpreter download —
  for a version nothing else uses.
- **A lockfile carrying artefacts no locus installs.** `uv.lock` held `cp313`
  wheels for `mypy`, `librt` and `pyyaml` alongside the `cp314` ones actually
  resolved. Relocking at `>=3.14` removed 34 lines of them.

Nothing in `src/standard_check/` needs 3.14. This is not a decision forced by
the code — it is a decision about a promise, taken now because ADR 0027 is what
made the promise legible as one.

## Alternatives Considered

### Option 1: Keep `>=3.13` and keep the floor job

Leave the claim and go on verifying it.

**Pros:** The widest set of adopters can install the checker, and the promise
stays honest because something tests it. Costs nothing but CI time.
**Cons:** It keeps a promise nobody chose to make. The set of adopters it serves
is unknown — not "small", *unknown*, which is a different thing and worse: there
is no evidence anyone needs it, and no way to notice if that changes. Paying a
duplicate test run to keep an unexamined commitment is the sort of cost that
never gets revisited because nothing forces the question.

### Option 2: Lower the pin to 3.13 instead

Close the gap from the other end: run the gates on the floor.

**Pros:** Also removes the duplicate job, and is the more conservative reading —
develop on the oldest thing you support, so incompatibilities surface where they
are written rather than where they are installed.
**Cons:** It gives up the current stable for a claim no adopter is known to
need, and it inverts the usual direction of travel: the project would be held
back by a promise rather than the promise being sized to the project. It would
also have to be undone the day 3.13 goes end-of-life, at which point the same
decision is taken under time pressure instead of deliberately.

### Option 3: Raise the floor to 3.14

Narrow the claim to what the project actually runs.

**Pros:** The promise becomes one that is kept by construction: every locus runs
the floor, so it is verified by the ordinary conformance run rather than by a
job that exists to verify it. The lockfile carries only interpreters something
uses. And the claim is now a decision with a record, which is the property it
has always lacked.
**Cons:** An adopter on 3.13 cannot install `standard-check`. That is a real
narrowing and the reason this is an ADR rather than a version bump.

## Decision

We will raise `requires-python` to `>=3.14`, matching the interpreter
`.python-version` pins.

The three facts ADR 0027 separated stay separate — this changes one of them, and
the other two follow or do not on their own terms:

| | Before | After | Because |
| --- | --- | --- | --- |
| `requires-python` — what we promise | `>=3.13` | **`>=3.14`** | this decision |
| `.python-version` — what runs the gates | 3.14 | 3.14 | unchanged |
| ruff's target — what the linter models | 3.13 | **3.14** | derived from the floor; it moved by itself |
| the devcontainer feature — what bootstraps | 3.13 | 3.13 | it runs `pip install uv` and no gate |

**Ruff moving on its own is the point.** It was `target-version = "py313"`
written out until ADR 0027 deleted it, and under this change a written-out value
would now be a third copy pointing at a floor that had moved. Nobody had to
remember it, because there was nothing to remember.

`support-floor.yml` is kept and made self-skipping rather than deleted. Its
subject is the *gap* between floor and pin, and there is no gap today — so it
reads both files, reports that, and does not run the suite a second time on the
same interpreter. The two values move independently and will diverge again:
pinning ahead of the floor is the ordinary case, and the job returns by itself
when it happens. Deleting it would mean re-deriving the same mechanism the next
time, from a commit message.

Option 3 was chosen over Option 1 because an unexamined promise is not made
better by testing it, and over Option 2 because a claim no adopter is known to
need should not decide what the project develops on.

## Consequences

**Positive outcomes:**

- The support claim is now verified by every ordinary run rather than by a job
  built to verify it. A promise the project keeps by construction cannot drift
  from what it does.
- `uv.lock` carries only wheels for an interpreter something runs.
- The claim has a record. Whatever is decided next about it starts from a stated
  reason rather than from an inherited default.

**Trade-offs and risks:**

- **An adopter on 3.13 can no longer install `standard-check`.** The failure is
  a clean resolver refusal naming the requirement, not a broken install — but it
  is a refusal, and this repository does not know whether anyone hits it. That
  is the cost, and it is accepted rather than argued away.
- Widening again is cheap and deliberately so: one line, `uv lock`, and
  `support-floor.yml` starts running again on its own. Nothing about this
  decision is hard to reverse, which is the main reason it is safe to take on
  the evidence available.
- The devcontainer's bootstrap interpreter (3.13) is now below the floor. It
  installs uv and answers `#!/usr/bin/env python3` for `.claude/hooks/md-lint.py`
  — neither is the package, and `requires-python` makes no claim about either.
  It is noted because the numbers now look inconsistent at a glance, and the
  reason they are not is worth being able to look up.
- The gap between floor and pin is where a 3.14-only construct could reach code
  an adopter compiles on 3.13. Closing the gap removes that risk rather than
  managing it, which is a benefit — but it removes it by narrowing who can
  install, not by making the code more portable.

## Related ADRs

- [ADR 0027: The Interpreter Is a Pinned Tool](0027-the-interpreter-is-a-pinned-tool.md)
  — separated the support claim from the environment, which is what made this
  decision possible to state. This ADR changes one of the three facts that ADR
  distinguished; it does not revise the distinction.
- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — the argument this reuses: a rule nobody decided is the failure, not an
  exception to it. A support claim nobody decided is the same shape.

## References

- [Python packaging — `requires-python`](https://packaging.python.org/en/latest/specifications/pyproject-toml/#requires-python)
  — the field as a claim published in package metadata.
- [Python 3.13 release schedule](https://peps.python.org/pep-0719/) — 3.13 is
  security-supported to 2029, so this is a narrowing by choice and not by
  necessity.
- [ruff — `target-version`](https://docs.astral.sh/ruff/settings/#target-version)
  — inference from `requires-python`, which is why the linter's target moved
  without an edit.
