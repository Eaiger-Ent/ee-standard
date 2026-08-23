# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A control register for Equal Experts repositories: `controls.yaml` defines what
"conformant" means, a family of Claude skills deploys the gates, and a checker
(`standard-check`, in `src/standard_check/`) audits them.

Current status: Phases 0, **0.5, 1 and 1.5 are all complete** as of 2026-08-18,
with no re-opened criteria outstanding. **Phase 2 is in progress**. Its first
slice landed 2026-08-19: the `plugins/ee-standard/` skeleton, `gate-secrets` as
the reference gate, and `standard-check run --control <ID>`, the one entry point
a gate verifies through. Its second landed 2026-08-21 at register contract 12:
`gate-quality`, the first gate owning more than one control (LNT-001, TYP-001,
TST-001 — three controls, two shared files), a `deploys.json` carrying one
contract **per gate** rather than per plugin, and `stacks:` invocations moved to
the form that reaches the artefact a lockfile pins. Its third landed the same
day at contract 13: `stack_tool_pinned_in_lockfile`, which closes
[ADR 0020](docs/adr/0020-a-locus-reaches-the-pinned-artefact.md)'s case C by
making the *existence* of a pin a verdict rather than only the invocation that
reaches it, and `ecosystems.<name>.add_dev_dependency`, without which a gate
could fail a control for an unpinned tool and not pin it.
Its fourth landed at contract 14: `gate-supply-chain`, whose three controls were
already green — and SUP-003 was green for the wrong reason, declaring
`locus: [pre-commit, ci]` with nothing reading either. Its fifth landed at
contract 15: `gate-build`, which closed the same defect in BLD-001 and DEV-001,
gave `.devcontainer/setup.sh` an owner per region, and replaced three near-copies
of one assert with `gate_wired_at_declared_loci`, which reads the control's own
`locus:` list. Its sixth landed at contract 16: `gate-iac`, closing the last of the four — and
finding two more ways a CI step could be credited as a locus without gating
anything, a suppressed step and the step that *installs* a tool rather than
running it. Its seventh landed at contract 17: `gate-repo`, the only gate whose
effect is not a file, which records the branch ruleset before applying it so
that something is verifiable before Phase 3 — as **intent**, never as
enforcement. Its eighth shipped the devcontainer template at
`plugins/ee-standard/templates/devcontainer/`, which pins its image and features
by digest and — checked by a grep rather than a reading — no tool version by
hand. Its ninth shipped `standard-adopt`, the
front door: it writes no gate configuration, owning the plan, the dispatch order
and the whole-register verify instead. `docs/10-phase-2-review.md` holds the
evidence for all nine, and § Where Phase 2 finished holds the closing audit —
run over the register rather than over the ledger, because a ledger is a claim
and the register is the thing. **Phase 2 is 11/12.** The one criterion still open
is that the devcontainer template *builds*: this container has no Docker, so
nothing here has run `devcontainer build`, and the commands for an operator are
in `docs/08-adopting.md` § 2.0. One question the audit raised is Phase 3's and is
recorded rather than fixed: SUP-002 verifies the dependency-update
*configuration*, and whether the bot is **enabled** is platform state nothing
checks.

A second review on 2026-08-21 found four more, recorded in
`docs/10-phase-2-review.md` § What the second review found, and all four are
closed. Contract 18: SEC-001's every block acted *after* a credential was
already a git object, and the `.gitignore` rule that acts before it was a
comment claiming the control depended on it — `secret_files_are_gitignored` now
reads that rule and requires git to track the file carrying it. Contract 19,
the serious one: `gate-repo`'s ruleset payload omitted the `parameters` GitHub's
API requires on **two** rules, so every apply call 422'd, and the
`required_status_checks` rule named no check at all — which
`ruleset_recorded_matches_register` could not see, testing only that a rule of
that *type* was present. `required_checks:` is now the register's and is held to
the workflows: a named context must come from a gating job that does not
suppress its own failure, so the list cannot become a second copy of the job ids.
`.github/rulesets/default-branch.json` was re-transcribed and matches the API
response exactly. GOV-001's partial **narrowed** rather than dropped — whether
the repository says a job is required is answered from a file now; whether
GitHub enforces it is Phase 3's, and letting the first stand in for the second
is the substitution the assert refuses in its own message. Two doc-drift
findings are fixed.
Read `docs/09-phase-1.5-review.md` before touching `src/standard_check/`:
it records what each assert was wrong about and why, and Phase 2 copies that
assert layer into six gate skills. Do not treat a ticked box in an earlier phase
as settled without checking it — **seven** boxes have been re-opened after being
ticked, four of them on 2026-08-18 by the review recorded as
`docs/09-phase-1.5-review.md` § H, which found GOV-001 passing a workflow that
ran on neither push nor pull_request, a tool compared only at filenames the
checker itself named, and ADR 0018 recorded as implemented with one of its
ratified moves never made.
**Phase 3 is in progress.** Its first slice landed 2026-08-22 and implements
`kind: remote`: `src/standard_check/remote.py` (transport, credential discovery,
the failure taxonomy), `asserts_remote.py` (the two asserts the register
declares), and `rulesets.py`, which gives the recorded ruleset and the platform
response **one** reading of what "protected" means. Reasoned in
[ADR 0021](docs/adr/0021-how-remote-verification-authenticates.md), which
ADR 0018 requires to exist. `docs/11-phase-3-review.md` holds the evidence and
the three criteria the slice deliberately left open.

Four outcomes, and only two are about the repository: **no token** is
`SKIPPED (no credentials)`; a token that was **rejected, under-scoped or shown
an answer that does not settle the control** is `UNCLASSIFIED`; only an actual
answer is `PASS`/`FAIL`. GitHub omits `security_and_analysis` for a caller
without admin, so reading its absence as "push protection is off" would report a
violation produced by not having looked — the asserts raise instead. The mirror
holds too: an effective-rules response of `[]` **is** an answer, and fails.
Tests must never depend on ambient auth — `tests/conftest.py` strips
`GITHUB_TOKEN`/`GH_TOKEN` autouse.

**One decision is open and blocks the `--require-complete` flip**, recorded at
[ADR 0022](docs/adr/0022-a-platform-token-ci-carries.md) (`Status: Proposed`):
the Actions `GITHUB_TOKEN` cannot read `security_and_analysis`, so SEC-001's
remote block is `UNCLASSIFIED` in CI while passing locally. **Do not add a
platform token to CI before requirements 1 and 2 of that ADR § What the register
must gain exist** — SEC-002 cannot see one today, because `no-static-cloud-keys`
reads `cloud_credentials:` and every name in it is a cloud provider key, so a
`GH_ADMIN_TOKEN` secret would leave SEC-002 green over a standing
administrative credential. Note also that a `pull_request` run receives repo
secrets unless the pull request comes from a fork.

Per [ADR 0014](docs/adr/0014-satisfying-remote-locus-controls.md) (**Accepted**
and implemented 2026-08-17), this repository **is public**: write nothing that
assumes privacy, and treat anything committed as publishable. CI-001 and SEC-001
stay Tier 1 — do not re-tier a control to make a report green.

Per [ADR 0016](docs/adr/0016-exit-codes-for-unverifiable-controls.md) and
[ADR 0017](docs/adr/0017-partial-verification-is-reported.md) (both **Accepted**
2026-08-17, neither implemented), the checker's verdict vocabulary is settled:
exit `3` means no violation was found but something could not be verified, `1`
means a verified violation, `0` means every applicable control was verified, and
`--require-complete` promotes `3` to `1`. A control whose tool is absent is
`UNCLASSIFIED`, not `FAIL`. A verification block declares its own partial
implementation **in the register**, with an expiry — never in the checker.

## Commands

- Full conformance run: `uv run standard-check` (also: `schema`, `run --tier 1`,
  `meta GOV-001`, `assert <name>`, `explain <ID>`). CI runs it in
  `.github/workflows/standard-check.yml`.
- Quality gates: `uv run ruff check .`, `uv run mypy`, `uv run pytest` — all
  configured in `pyproject.toml`, the single definition every locus reads.
- Build-plan progress: `uv run python scripts/plan_progress.py` — a derived view
  of the exit criteria in `docs/04-build-plan.md`, which stays the single source.
  It stores nothing and infers no gating; it exits non-zero if a criterion is
  marked re-opened while still ticked. Never maintain a second list of this work.
- Lint markdown: `markdownlint-cli2 "**/*.md"` — also runs via a PostToolUse
  auto-fix hook on every file you write, a pre-commit hook, and
  `.github/workflows/lint.yml`.
- Run all pre-commit hooks: `uv run pre-commit run --all-files`
- Verify container auth/tools: `.devcontainer/check-auth.sh`
- `gh` for repos in the Eaiger-Ent org (ambient `GITHUB_TOKEN`); `gh-ee-skills`
  for repos in the EqualExperts org (ee-skills, ee-skills-incubator) — the
  wrapper scopes `EE_SKILLS_GITHUB_TOKEN` to a single invocation.

All development happens inside the devcontainer (`docs/06-devcontainer-setup.md`
is the operator guide). Host secrets arrive via `.devcontainer/fetch-secrets.sh`
(macOS Keychain → `.devcontainer/.env`, from which `.devcontainer/.env.docker`
is derived for `--env-file`; both are gitignored and must stay so — SEC-001
depends on those lines).

## The core invariant

A register entry in `controls.yaml` **is** the control, not documentation of
one. Every other artefact — CI workflow, pre-commit config, gate skill,
devcontainer, checker — derives from the register rather than restating it.
Never introduce a second copy of a rule (in prose, CI, or config) that could
drift from the register; that duplication ("theme T-2") is the failure this repo
exists to prevent.

**Python counts as a second copy.** Per
[ADR 0018](docs/adr/0018-register-checker-boundary.md) (**Accepted** 2026-08-17,
**implemented** over contracts 3, 5, 6 and 8), before writing a rule into
`src/standard_check/` ask: *could a reasonable Equal Experts repository need this
to differ without changing the checker?* If yes, it belongs in `controls.yaml` —
mandated tool names and their per-locus evidence live in `stacks:` — including which files a stack's gates must cover and where each
tool's allow-list lives — lockfile
ecosystems, test-command spellings and frozen-install idioms in `ecosystems:`,
tool versions **and the loci that repeat them** in `tools:`,
failure-suppression idioms in `suppression:`, the credential names SEC-002
forbids in `cloud_credentials:`, and anything specific to
one control in its verify block's `args:`. If no, the checker may hold it, but
the reason must be recorded in ADR 0018 — the predicate grammar, the ID pattern, semver
strictness, `rationale_adr` existence and the Tier-1 baseline rule are
properties of the register format, not of any repository. An unreasoned rule in
the checker is the failure, not an exception to it.

## Vocabulary you need before editing anything

Defined in `docs/00-concepts.md`; the schema is `docs/01-register-schema.md`.

- **Rung** (enforcement ladder): `advisory` → `warn` → `blocking` →
  `blocking (baselined)`. Promotion is only by explicit recorded decision.
- **Locus**: where a control runs — `editor`, `pre-commit`, `ci`, `remote`.
  Discipline is *pin once, reference many*: same tool version, same config, at
  every locus.
- **Predicates**: a control whose `applies_to` predicate the repo doesn't
  satisfy is SKIPPED, not failed. Predicates are evaluated against files, never
  self-declared.
- **Baseline**: shrink-only tolerated-violation list (GOV-002 fails if one
  grows). All Tier-1 controls carry `baseline: null` by design.
- **Verification kinds**: `command` (an external tool; exit code is the verdict),
  `file` (an in-process assertion over repository files), `remote` (platform API
  state). The kind names what performs the verification, not which module
  implements it — declaring an in-process assertion as `kind: command` is a
  schema error, because GOV-001 reads `kind: command` blocks and the
  miscategorisation decided its verdict. **One exception, bounded by the
  validator**: a meta-control verifies itself with
  `run: standard-check meta GOV-NNN`, which runs in-process. The shape is forced
  — a meta-control returns a three-valued `Verdict` and a `kind: file` assert
  returns a boolean — and it decides nothing, since GOV-001 never reads
  `meta_controls`. A control using that spelling, or a meta-control naming
  another's id, is rejected (`docs/01-register-schema.md` § The one exception).
- **Partial**: any verify block may declare itself not fully implemented, naming
  the unverified property and an expiry date. GOV-003 fails an expired one, and
  a partial block denies the run a `0` exit.
- **Variance**: `forbidden` or `narrowing-only`. Deployed artefacts may tighten
  a narrowing-only control but never loosen it; loosening requires updating the
  control's entry in the register first (as was done for DOC-001's 250-char
  line ceiling).

## Rules for editing `controls.yaml`

- Bump `meta.register_contract` when a control's `rung`, `verify`, `variance` or
  `applies_to` changes, or when the register gains a field a skill reading it
  must understand — skills read it to detect stale deployments.
- Every control must cite an external, resolving standard URL; verify URLs
  before committing them.
- An unknown `assert` name is a schema error, not a skipped check (Phase 1 exit
  criterion — keep the closed set in sync with the checker when it exists).
- Meta-controls (GOV-001/002/003) check the register itself, not the code.

## Deployed artefacts and skills

Files deployed by ee-skills plugins carry an `ee-control:` provenance header
naming the control, the deploying skill and version, the register version **and
the register contract** — `docs/00-concepts.md` § The provenance stamp has the
format, one parser lives at `src/standard_check/provenance.py` (never write a
second), and `tests/test_provenance_stamps.py` checks every stamp parses and
names a real control. Eleven files carry one: `.markdownlint.yaml`,
`.markdownlint-cli2.yaml`, `.github/workflows/lint.yml`,
`.claude/hooks/md-lint.py`, `.github/workflows/standard-check.yml`,
`.devcontainer/devcontainer.json`, `.github/dependabot.yml` — the one file whose
stamp sits at the top, because every line of it belongs to SUP-002 —
`.devcontainer/setup.sh`, whose every stamp belongs to a gate other than the
`gate-build` that owns the file, `.github/rulesets/default-branch.json` — the
one artefact that enforces nothing by existing, being a record of what the
platform is asked to enforce — and, with one stamp per hook it owns rather than
one at the top of the file, `.pre-commit-config.yaml`, and — from contract 18,
stamped per region for the same reason — `.gitignore`, whose two credential
lines are the only stamped artefact that runs nothing and installs nothing.
A control whose artefacts a gate writes names it in
`deployed_by`, and `provenance_stamp_present` reads back a stamp naming **that
control** — not merely one naming its gate, which credited a gate's three
controls for any stamp it had written anywhere. The control's id reaches the
assert from the runner, and the schema rejects a register that writes it into
`args:` itself, or one where `deployed_by` and the stamp block disagree. Keep the header when editing such
files, note the edit in it, and respect the control's variance direction.

A stamp *behind* the register is staleness, which is never enforced and — until
Phase 5's sweep exists — is not reported either: `gate-secrets`' and
`gate-quality`'s older stamps read contracts 11 and 12 against a register at 19,
deliberately, because nothing they wrote here needs rewriting and doing it by
hand would record a redeployment that did not happen. Nothing in the checker says
so, and that is Phase 5's job rather than a defect. A stamp *ahead* of the
register is a defect, and fails. An exemption
in a deployed config is judged by what it hides
([ADR 0019](docs/adr/0019-exemptions-cannot-hide-tracked-files.md)): excluding a
path git does not track scopes the tool, excluding a path git tracks weakens the
control, and no `narrowing-only` control with `baseline: null` — which is all of
them — admits the second. `markdown_gate_wired_at_all_loci` checks it, so it is
a build failure rather than something to remember. `lint-md` owns the whole DOC-001
lifecycle — this repo does not write its own markdown gate, and `lint-md`'s
shape (pre-flight → install → write config → wire every locus → migrate →
verify) is the template every future gate skill copies (`docs/02-skill-family.md`).

**Do not re-run `/lint-md` here.** The stamps read `lint-md@1.0.6` and the
installed skill is 1.0.7, so the deployment is stale — which is reported and
never enforced. 1.0.7 shipped most of the amend at
[#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530) but still
writes `npx --no-install` at every locus, which ADR 0020 measured falling
through to `PATH`, and still writes `.claude/**` into `ignores`, which ADR 0019
forbids. Its presence checks mean a re-run would skip four of the five artefacts
today rather than revert them — but that is idempotency rather than agreement,
one of the four greps matches only a comment, and the fifth
(`.markdownlint.yaml`) prompts to overwrite rather than skipping. Refresh the
deployment only once those two rows ship
(`docs/09-phase-1.5-review.md` § F, Update 2026-08-20).

Enforcement is never Claude: gates are pinned binaries reading pinned configs;
a skill may install or explain a gate but cannot be one.

## Documents

Read `docs/00-concepts.md` first for the vocabulary, then:

| Document | What it is for |
| --- | --- |
| `docs/00-concepts.md` | The vocabulary every other document assumes |
| `docs/01-register-schema.md` | Field-by-field specification of `controls.yaml` |
| `docs/02-skill-family.md` | How the standard reaches a repo, and stays current |
| `docs/03-devcontainer.md` | What the shipped devcontainer template must be |
| `docs/04-build-plan.md` | The phase exit criteria that define "done" for any implementation work, and the only list of outstanding work |
| `docs/08-adopting.md` | What a repository that did not author the standard must do to satisfy it. **Every phase owes this file the adopter-facing steps it introduces** — see `04-build-plan.md` § A standing requirement |
| `docs/05-promotion.md` | The route to the `ee-skills` marketplace |
| `docs/06-devcontainer-setup.md` | Operator guide for this repo's own container |
| `docs/07-inherited-conventions.md` | What the predecessor repo knew, sorted by whether it transfers — including what must **not** be copied |
| `docs/09-phase-1.5-review.md` | Record of the Phase 1.5 review, and of § H, the review of the closed phase that re-opened four of its criteria. **`§ A`–`§ H` anywhere in this repo — asserts, tests, ADRs — refer to this file**, not to the build plan |
| `docs/10-phase-2-review.md` | Record of Phase 2 slice by slice, and the evidence behind every criterion it ticks |
| `docs/11-phase-3-review.md` | Record of Phase 3 slice by slice, including what each slice deliberately left open |
| `docs/adr/` | One ADR per control, plus the open decisions at `Status: Proposed` |

`README.md` § "The register at a glance" lists the thirteen Tier-1 controls, with
the three meta-controls described below the table.

Gate skills live in `plugins/ee-standard/skills/` — `gate-secrets`,
`gate-quality`, `gate-supply-chain`, `gate-build`, `gate-iac` and `gate-repo`,
the whole family, plus `standard-adopt`, the dispatcher that ships no templates
because it writes no artefacts of its own. A gate verifies itself with
`standard-check run --control <ID>` and never by reading its own files back —
that command runs the control's verify blocks through the same `run_control` the
full audit calls, which is what makes "one assert implementation" true rather
than intended. A gate holds **no** pinned version of its own; templates carry
placeholders and `tests/test_plugin.py` fails if any value the register pins
appears anywhere under `plugins/`. `.claude-plugin/deploys.json` carries one
`contractVersion` **per gate**, not per plugin — a shared number would
recommend redeploying every gate whenever any one of them changed, which is the
noise Phase 5's first two criteria exist to prevent.
