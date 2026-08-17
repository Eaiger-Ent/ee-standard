# Inherited conventions

What the predecessor repository already knew, sorted by whether it transfers.

## Provenance

`generate-ee-slides` is the repo whose retrospective produced this register. Its
`CLAUDE.md`, its nine path-scoped rules in `.claude/rules/`, and the session
memory accumulated against it encode several years of working practice — most of
it never written down as a standard, some of it arrived at independently and
stated better than the register states it.

This document sorts those statements into four groups: what transfers as-is,
what is design input for the checker, what conflicts and must be resolved rather
than carried, and what is local to that project and must **not** be copied.

The last group is the point. This register exists partly because of theme
**T-2**, one definition copied and then diverged. A repo that adopts the
standard by copying its predecessor's conventions wholesale reproduces the
failure the standard was written to prevent.

Captured 2026-08-17, from `generate-ee-slides` at commit `cb8110e`: its
`CLAUDE.md`, the nine files in `.claude/rules/`, and the two session memories
held against that project. The memories contributed the credential-shadowing
finding in § B and confirmed the organisation override in § C; nothing else in
them was general enough to carry.

Written against this repo at **Phase 1.5**. The Phase 1.5 review in
[`04-build-plan.md`](04-build-plan.md) independently reached two of the four
findings in § B, from the checker's behaviour rather than from the predecessor's
rules — noted inline where it did, because agreement reached by two routes is a
stronger claim than either alone.

## A — Transfers as-is

General engineering discipline with nothing project-specific in it. Candidates
for this repo's own working instructions, and in several cases for Tier-2 or
Tier-3 controls once Tier 1 is proven.

| Statement | Source | Why it lands here |
| --- | --- | --- |
| "Verify fixes propagate to ALL relevant locations (e.g. all duplicated config files)" | § Root Cause Discipline | This *is* theme T-2, stated as a working habit before the register named it |
| "Prefer integration tests that exercise the real client over unit tests that mock it — **mocks drift silently** when the API changes" | § Testing | The same drift argument the register is built on, applied one level down |
| "This rubric applies to every test file, **with no directory-based carve-out**… exclusion from CI is a decision about *where* a test runs, not about the quality bar it must meet" | § Testing | The sharpest governance statement in the source, and it has a live instance here. See [§ Scope exemption is not standard exemption](#scope-exemption-is-not-standard-exemption) |
| "Do not propose workarounds or fallbacks unless explicitly requested" | § Root Cause Discipline | |
| "Prefer apt-based installs over `curl` scripts" | § Devcontainer | Independently reaches [`03-devcontainer.md`](03-devcontainer.md)'s preference order — level 2 over level 4 |
| "Verify availability with `which <tool>` before relying on it" | § Devcontainer | The shape [`check-auth.sh`](../.devcontainer/check-auth.sh) already implements |
| "`infra/` is the single source of truth… never create ad-hoc provisioning scripts" | § Infrastructure | This register's own premise, one domain over |
| edit → validate → plan → **review** → apply; changes require explicit approval before apply | § Infrastructure | The confirm-before-mutate rule Phase 3 needs for `gate-repo` |
| "Never rename resources without checking if it triggers destroy/recreate; use `moved` blocks" | § Infrastructure | Generic to any infrastructure-as-code |
| "Reuse an existing service account if its scope already covers the need, rather than minting a new one by default" | § Devcontainer | Least-privilege without proliferation |
| "Before deleting any config file, verify it is not depended on elsewhere and confirm with the user" | § Safety / Destructive Changes | |
| "Complete all verification checks before signalling completion"; "if a phase fails, surface the error — do not attempt to fix the mechanism" | § Ralph Loop | Theme T-4 as a working rule. The second clause is the one people break |
| "Confirm the suspected file is the actual culprit before editing" | § Debugging | |
| File a GitHub issue before the first file edit | § Issues | This repo has an issue tracker with nothing open; Phase 1.5's backlog lives in a document instead |
| One question at a time, and wait for the answer | § Clarification Protocol | Harness-level, project-neutral |
| Conventional commits; type-annotate public functions; comments explain *why* not *what*; no dead code, no compatibility shims | § Conventions, § Code style | Already partly enforced here by ruff and mypy; the rest are Tier-2/3 candidates |
| Path-scoped rules that load only when a session touches matching files | § Markdown tables | A delivery mechanism worth reusing — see [§ B](#b--design-input-for-the-checker) |

### Scope exemption is not standard exemption

One statement deserves more than a table row, because it names a distinction the
register does not yet make:

> **This rubric applies to every test file in the repository, with no
> directory-based carve-out** — including `scripts/*.test.js`, `tests/dev/`, and
> any other test location. `tests/dev/`'s exclusion from CI is a separate,
> narrower decision about *where* a test runs, not about the quality bar it must
> meet.

Two different things are routinely conflated: *this artefact is out of scope for
this run* and *this artefact is held to a lower bar*. The first is a practical
routing decision and is usually fine. The second is a variance and must be
declared, owned, and dated.

This repo has a live instance. `.markdownlint-cli2.yaml` ignores `.claude/**`
and `pyproject.toml` carries `extend-exclude = [".claude"]`. Phase 1.5 § F
correctly records both as unrecorded weakenings of `narrowing-only` controls
whose `baseline: null` means no exemptions are possible. But it records them as
a *defect to remove*, and the missing vocabulary is what would let the other
answer be stated: that the hook directory is legitimately out of scope for the
gate, which is not the same as being held to a lower standard, and which the
register currently has no field to express.

Until it does, every scope decision has to be laundered through either a
baseline (which Tier 1 forbids) or a config-file glob the checker reads as
authoritative rather than as a claim. That second route is theme **T-1** with
the standard's own machinery holding the door open.

Resolve it in [`01-register-schema.md`](01-register-schema.md) alongside Phase
1.5's `variance` work, since both are about the same question: which weakenings
are sayable.

## B — Design input for the checker

Four rules in the predecessor are not conventions at all. They are findings
about what a gate can and cannot do.

### The register has no vocabulary for the unverifiable

Three of the path-scoped rules argue explicitly for their own existence as prose
rather than as CI gates:

> A linter cannot decide whether an error *code* is the right one for a given
> context… These patterns are therefore encoded as written rules rather than CI
> gates.
>
> — `error-taxonomy-at-tool-boundary.md`

And, on the standard the register would most obviously want to mechanise:

> `CLAUDE.md` § Code style bans comments that explain *what*, but a tool cannot
> judge whether a reader *could* infer the *why* without assistance.
>
> — `comments-explain-why.md`

This register has nowhere to put that. Every control in `controls.yaml` carries
a `verify` block, so everything in the register is mechanically checkable by
construction. The complement — standards genuinely held, and structurally
unverifiable — has no home.

The enforcement ladder already starts at `advisory`, so the vocabulary is half
present. What is missing is the statement that an `advisory` control **may carry
no `verify` block at all**, rather than a weak one. That is the whole decision,
and it is one schema sentence.

It matters because of the failure mode. Such standards do not get forgotten;
they get written **as controls with weak assertions**, because the register is
the only place with authority. Phase 1.5 § D is a catalogue of exactly that
outcome arrived at by a different route — SEC-002 matching seven uppercase
substrings, TST-001 never reading `on:`, SUP-002 accepting a `renovate.json`
that says `{"enabled": false}`. A control whose assertion cannot fail is worse
than no control, because the report says PASS.

This is the same class of problem as two items already in Phase 1.5 § E:
`UNCLASSIFIED` unreachable from every code path, and `variance: justified`
structurally unimplementable. In all three the vocabulary exists and the
mechanism behind it does not.

### A checker that parses nothing passes

> A test that scans a config file or checks cross-artefact consistency can pass
> while parsing nothing, which silently defeats the test's purpose.
>
> — `cross-artefact-guards.md`

Phase 1.5 § C found this independently, and in a sharper form than the
predecessor states it: `_git_ls` swallows a non-zero `git` exit and returns an
empty set, so a non-git directory reports eight predicate skips and exits 0, and
`gitleaks detect` prints "0 commits scanned … no leaks found" for a scan that
examined nothing. Two exit criteria now cover the target-repo half.

The **register** half is still open. `standard-check` parses `controls.yaml` and
reports on what it finds; a glob change, a schema regression, or a
silently-caught parse error that yields zero controls produces a green run,
because nothing failed. Phase 1.5's criteria cover unknown keys and asserts that
abort, but not a register that parses to nothing.

The guard belongs in the checker, not only in its tests: assert the register
parsed to a known-nonzero shape — every tier represented, a pinned minimum
count — before evaluating anything, and report `no controls evaluated` as an
error verdict rather than a clean exit.

That is the same bug as GOV-001, one level up. GOV-001 asks whether a blocking
control is reachable from a CI step that can fail; this asks whether the checker
itself is reachable from any control that can fail.

### Skips that are not skips

> `pytest.skip` guards environmental preconditions that the test cannot create.
> A test that skips because of a fixture the test itself set up has not asserted
> the fixture's behaviour — it has silently disabled the test instead.
>
> — `test-skip-guards.md`

Phase 1.5 fixes several individual skips: the `container` predicate hiding a
`Dockerfile.prod` that BLD-001's assert would fail, and `SKIPPED (no
credentials)` leaving the exit code at 0. What it does not yet have is a
**criterion** for which skips are legitimate, so the next one has to be argued
from scratch.

The predecessor supplies one: **ownership of the precondition**. If the run
controls the condition and still skips, the skip is a disabled check. Applied
here, `SKIPPED (predicate)` is legitimate only when the predicate depends on
repository facts the checker does not itself create — which immediately
classifies the `_git_ls` case as illegitimate without needing to enumerate it,
because the emptiness was the checker's own doing.

That two people reached the same distinction from different problems — one from
tests, one from controls — is itself the argument for putting it in the schema
rather than leaving it as this author's preference.

### The markdown auto-fixer silently corrupts content

Two of the predecessor's rules record markdownlint behaviours that are
properties of the tool, not of that project. Both reproduce under **this repo's
exact config**, and one of them is live in a way the predecessor's setup was
not: `.claude/hooks/md-lint.py` runs `markdownlint-cli2 --fix` on every `Write`
and `Edit`, then re-lints and reports OK if the re-check is clean.

Confirmed on 2026-08-17 against `.markdownlint.yaml` as committed:

```text
before  →  # Package layout
           The module __init__.py lives at the package root

after   →  # Package layout
           The module **init**.py lives at the package root

post-fix lint: 0 issues, exit 0
```

`MD050: style: asterisk` treats the correctly-flanked underscores as strong
emphasis and rewrites them. The filename is destroyed, no rule reports it, and
the hook prints `markdownlint [c.md]: OK`. Every dunder identifier written into
any document in this repo is subject to this.

`MD018` behaves the same way on a line beginning with an issue reference —
`#430 tracks the regression` becomes an H1 — though in a document that already
has a title the corruption usually surfaces as MD025 or MD026. The predecessor's
note is that it is *sometimes* silent, which matches: the follow-on error is
incidental, not a guarantee.

An auto-fixer that silently corrupts content is theme **T-4** inside a tool this
register mandates, and the hook makes it unattended. Three things follow:

- The correct fix for both is a code span, which is never parsed for emphasis —
  a root-cause fix rather than a rule suppression.
- DOC-001 should state whether `--fix` is in scope at all, and if so which rules
  are excluded from it. Phase 1.5 already requires DOC-001 to verify its three
  loci and its ceiling; the auto-fix hook is a fourth locus that no control
  currently describes.
- A gate that can modify the artefact it is checking needs its own rule: report,
  or repair, but never repair silently. This is the one finding here that is a
  candidate control rather than a note.

### An injected credential shadows a better one

This finding is not in `CLAUDE.md` or the rules. It is in session memory,
recorded 2026-08-16 while pushing to this very repository.

A devcontainer that injects a read-scoped `GITHUB_TOKEN` silently overrides any
credential the operator establishes afterwards: both `gh` and git's credential
helper prefer the environment variable over `gh auth login`. The failure is that
the error text points somewhere else entirely — the observed progression was
`404 Not Found` then `403 Write access to repository not granted`, both of which
read as *this repo does not exist* or *you lack organisation permissions*, when
the actual cause was the wrong identity. The working route is
`env -u GITHUB_TOKEN <command>`; supplying a better token inline is not an
option, because an agent sandbox refuses a command line containing a literal
secret.

This has since been largely addressed — the two-token split, the `gh-ee-skills`
wrapper that scopes `EE_SKILLS_GITHUB_TOKEN` to a single invocation, and
`check-auth.sh` naming the organisation on each line. One residual remains, and
it is the register's own kind of bug: `check-auth.sh` prints
`authenticated (Eaiger-Ent via GITHUB_TOKEN)` as a **fixed string**. It reports
which variable was consulted, not which identity answered. If the Keychain entry
holds a token for a different account, the banner asserts a fact it never
checked — theme T-1, in the file whose whole job is to make the credential
boundary legible.

The general form is worth stating in [`03-devcontainer.md`](03-devcontainer.md)
as a named T-5 instance: **a control that mandates credential injection must say
what the injected credential displaces.** SEC-001 currently says where secrets
may live, not what they outrank.

## C — Conflicts to resolve, not carry

### SEC-002 against the devcontainer guidance

The predecessor requires that non-interactive callers authenticate via a scoped
service account key — a long-lived JSON file on disk. SEC-002 requires that no
long-lived cloud credential exists in CI.

A developer machine is not CI, so these may not collide. But the register does
not say where the line falls, and a control whose scope is inferred means
something different in every repo that adopts it. Phase 1.5 § D shows the
ambiguity has already reached the implementation: SEC-002's assert is a
case-sensitive substring match over seven uppercase names, which is a guess at
scope encoded as a regex.

State it in SEC-002's `enforces` text: whether the control covers the CI
execution environment specifically or any automated caller including local ones,
and what the sanctioned alternative is — workload identity federation,
short-lived tokens, or an explicit variance for developer machines.

### The default GitHub organisation — resolved

The predecessor's instructions name `EqualExperts`; this repo lives under
`Eaiger-Ent`. When this document was drafted that override existed only in
session memory, which is attached to the *predecessor's* project directory and
would not be present in a session started here — theme **T-3**, declared but
unreachable, in the most literal sense.

`CLAUDE.md` now states it, along with which wrapper reaches which organisation.
Recorded here because the resolution is the pattern worth keeping: an override
that lives only outside the artefact it overrides is not an override.

## D — Does not transfer

Listed so that adoption is a decision rather than a copy.

| Local to the predecessor | Note |
| --- | --- |
| Python 3.14, `uv sync`, `.venv/bin/pytest` paths | This repo pins 3.13 via a devcontainer feature and runs `uv run` |
| GCP project `ee-slides`, region `europe-west2`, the `--account`/`--region` rule | Real and hard-won, and entirely specific to that project's estate |
| The dev → latest → prod deployment vocabulary | Including that prod is data-only there |
| EE template IDs, the `@equalexperts.com` account requirement | Domain-specific |
| Kuat UI standards, React 19 Playwright locator rules | Stack-specific; this repo has no frontend |
| The ralph loop, `prompts/`, the phase corpus | A development mechanism, not a standard |
| Firestore emulator seeding, ADC setup | |

### The markdownlint config is the instructive case

An earlier draft of this document listed the markdownlint configuration as the
headline non-transferable item, on the grounds that the predecessor used a
250-character line ceiling against this repo's 80 — same tool, same rule names,
opposite values.

That is no longer true. `.markdownlint.yaml` here reads `line_length: 250`, and
`CLAUDE.md` records the register entry being updated to match. The two repos
converged by decision rather than by drift, which is the correct outcome.

It is worth keeping the row for what it now demonstrates instead. Phase 1.5's
carried debt records that DOC-001's ceiling was, at one point, **three numbers
for one event**: 250 in the register, "from the previous 80" in the commit
message, and 120 in ADR 0013 — the ADR having been cited as the canonical
precedent. That is theme T-2 with no copying between repos involved at all,
which is the more general lesson: a value stated in more than one artefact will
diverge whether or not anyone copies it across a boundary.

The distinction that survives is between a **setting** and a **finding**. The
line ceiling is a setting: local, negotiable, and correctly re-decided per repo.
The two markdownlint behaviours in § B are findings: properties of the tool that
hold wherever it runs, and therefore real input to DOC-001 regardless of what
either repo sets.

## What to do with this

| Section | Destination | When |
| --- | --- | --- |
| A | This repo's working instructions; Tier-2/3 candidates | After Tier 1 is proven end to end |
| A, scope-exemption vocabulary | [`01-register-schema.md`](01-register-schema.md), with Phase 1.5's `variance` work | Phase 1.5 — same question, same field |
| B, `advisory` may carry no `verify` | [`01-register-schema.md`](01-register-schema.md) | Phase 1.5 — one sentence, and § E is already reworking the vocabulary |
| B, register-level vacuity guard | `standard-check` — the half Phase 1.5 § C does not cover | Phase 1.5 |
| B, skip legitimacy = ownership of the precondition | Schema, as the criterion behind Phase 1.5's individual skip fixes | Phase 1.5 |
| B, auto-fix corrupts silently | DOC-001 `enforces` text; `.claude/hooks/md-lint.py` | **Now** — it is unattended on every write |
| B, repair-vs-report | A candidate control, not a note | Phase 2, with the gate skills |
| B, credential shadowing residual | [`03-devcontainer.md`](03-devcontainer.md) as a named T-5 instance; `check-auth.sh` | Phase 2 |
| C, SEC-002 scope | SEC-002 `enforces` text | Before Phase 2 — `gate-secrets` is the reference implementation |
| C, organisation default | Done | — |
| D | Nothing. It is a guard list | — |
