# Build plan

Seven phases, each with exit criteria that can be checked rather than felt.

The ordering principle: **the checker is built before the template.** A template
without a checker produces repos that are conformant on the day they are created
and unmeasured thereafter — which is the predecessor's failure, reproduced
faster. With the checker first, every subsequent phase has an objective test, and
the template can be validated by generating a repo and running the checker
against it.

That principle governs the **shipped template**, which stays in Phase 2. It does
not govern **this repo's own environment**, which comes first — see Phase 0.5.
The two are different artefacts and conflating them is what put the devcontainer
in the wrong phase originally.

## Phase 0 — The register

**Done.** `controls.yaml` exists with 13 Tier-1 controls and 3 meta-controls,
every standard URL verified to resolve.

### Exit criteria — phase 0

- [x] Every control cites an external standard with a resolving URL
- [x] Every control has an owner, a `review_by`, and a variance policy
- [x] Tier-1 controls carry `baseline: null`
- [x] An ADR exists per control in `docs/adr/` — thirteen records,
      `0001`–`0013`, one per `rationale_adr` reference in `controls.yaml`.

## Phase 0.5 — This repo's own devcontainer

**Before any code is written.** All development on this repository happens
inside a container; nothing in Phase 1 is written against a host toolchain.

Operator instructions, including the macOS Keychain values that must be set on
the host first, are in
[`06-devcontainer-setup.md`](06-devcontainer-setup.md).

This is not the shipped template — that is still Phase 2's deliverable, and is
built by generalising this one. What Phase 2 gains is a working reference to
generalise from rather than a specification to implement blind.

Two reasons this cannot wait:

**Phase 1 is development work.** If `standard-check` is written on a host
toolchain, the first thing the standard repo does is violate the premise it
exists to enforce.

**Phase 1's own exit criteria already require it.** The last criterion — "the
checker's own repo passes every control it can verify locally", called "the real
gate" — includes DEV-001. A repo with no `.devcontainer/` cannot pass DEV-001,
so Phase 1 cannot close without one. Deferring the devcontainer to Phase 2 makes
Phase 1 unclosable by its own terms.

### Exit criteria — phase 0.5

- [x] The container builds from a clean clone on a host with only the required
      Keychain value set
- [x] `image` is pinned by `@sha256:` digest, and the digest matches what the
      registry serves
- [x] `devcontainer-lock.json` is committed and pins **every** feature named in
      `devcontainer.json` — a lock file covering three of four features reads as
      solved and is not
- [x] `.devcontainer/.env` is gitignored, and `git log --all -- .devcontainer/.env`
      is empty
- [ ] The container's final user is not root, stated explicitly rather than
      inherited from the base image — **re-opened**: `remoteUser` is stated in
      `devcontainer.json` but read by no assert, and BLD-001 needs a Dockerfile
      so it skips here. Ticked on a JSON key nothing verifies (Phase 1.5 § A)
- [ ] `setup.sh` is short enough not to need sectioning — anything longer is
      doing work that belongs in a feature — **re-opened**: 82 lines across
      seven sections (Phase 1.5 § Carried debt)
- [x] DEV-001's `enforces` text in `controls.yaml` covers the image digest as
      well as the lock file, matching what
      [`03-devcontainer.md`](03-devcontainer.md) already claims it verifies

The last one was register debt, not container work: as `controls.yaml`
originally stood, a repo with a complete lock file and a floating image tag
passed DEV-001 — theme **T-1** inside the register itself. Closed at register
`v0.2.0` (contract 2) by widening DEV-001's `enforces` text and adding the
`devcontainer_image_digest_pinned` assertion, so Phase 1 implements the control
against complete text.

## Phase 1 — The checker

Build `standard-check` as an ordinary executable. Python, installed from a
pinned version, no Claude anywhere near it — inside the Phase 0.5 container.

Implement in this order, because each stage is testable against the register that
already exists:

1. Schema validation (`standard-check schema`) — the register validates itself
2. `kind: command` verification — shell out, exit code is the verdict
3. `kind: file` assertions — the closed set named in `controls.yaml`
4. Predicate evaluation — `SKIPPED (predicate)` distinct from `PASS`
5. The three meta-controls
6. Report rendering, ordered by tier then rung

`kind: remote` is deliberately deferred to Phase 3. It needs credentials, network
and a live repository, and building it now would mean stubbing exactly the part
that must not be stubbed.

### Exit criteria — phase 1

- [x] `standard-check schema` passes against `controls.yaml`
- [ ] Running against this repo produces a report with no `UNCLASSIFIED` verdicts
      arising from checker bugs (as opposed to genuine ambiguity) — **re-opened**:
      vacuously true, because no code path can emit `UNCLASSIFIED`
      (Phase 1.5 § E)
- [x] A deliberately broken register fails schema validation with a message
      naming the field — exercised in `tests/test_schema.py`, one test per
      breakage class
- [x] An unknown `assert` name is a schema **error**, not a skipped check — the
      closed set is derived from the checker's assert registries, so it cannot
      drift from the implementation
- [ ] `SKIPPED (predicate)` and `SKIPPED (no credentials)` render distinctly and
      neither is counted as a pass in the exit code — **re-opened**: they render
      distinctly, but a no-credentials skip leaves the exit code at 0, so CI is
      green while two Tier-1 controls are unverified (Phase 1.5 § A)
- [x] The checker's own repo passes every control it can verify locally

The last one is the real gate. If the standard repo cannot satisfy its own
Tier-1 controls, they are not birth conditions.

Four of the boxes above and in phase 0.5 were re-opened by the review that
follows. They are listed unticked with a pointer rather than quietly left green:
a ledger that records only the optimistic reading is the thing this repo exists
to prevent.

## Phase 1.5 — Remediation

Phases 0, 0.5 and 1 closed their exit criteria. A review of the result found
that several were met in letter rather than in substance, and — more seriously —
that the checker's failure modes point the wrong way. In multiple places it
either **aborts without producing any verdict**, or **reports green for
something it never examined**. For a conformance tool those are the only two
failures that matter.

This phase exists because of one line in Phase 2: *"Gates and checker share one
assert implementation — verified by there being one copy."* Every defect below
would be copied into six `gate-*` skills and become six times more expensive to
correct. The principle that put the checker before the template applies again:
fix the checker before anything derives from it.

Nothing here is new scope. It is the distance between what Phase 1 claimed and
what Phase 1 delivered.

### A — Verdicts that overstate what was checked

| Defect | Now | Required |
| --- | --- | --- |
| GOV-002 cannot fail in CI. `_previous_content` falls back `origin/main` → `main` → `HEAD`, so once a growth is committed, "previous" *is* the grown file. Confirmed: growth uncommitted → FAIL; same growth committed → PASS | Catches dirty worktrees only | Compare against the default branch's merge-base, and fail closed when no comparison point exists |
| DOC-001 asserts only that a config file exists. Confirmed: `line_length: 100000` plus a 1600-character line passes; deleting the CI step, the pre-commit hook or the editor hook also passes | Existence check | A `doc_gate_wired_at_all_loci` assert mirroring LNT-001's, plus an assertion on the ceiling the register names |
| A control whose tool is missing reports FAIL. `hadolint`, `checkov` and `tflint` are absent from this container, so any repo with a `Dockerfile` or a `.tf` gets "command not found" | "Cannot verify" is indistinguishable from "violates" | `UNCLASSIFIED` — the verdict already exists for exactly this |
| GOV-001 derives reachability from a substring test, and any bare `standard-check` step short-circuits every control | `pip install standard-check` would mark all controls reachable | Match invocations, not substrings; see § Decisions for how loudly it should admit being partial |
| `SKIPPED (no credentials)` leaves the exit code at 0 | CI is green while SEC-001's remote half and all of CI-001 are unverified | See § Decisions |

### B — Runs that abort instead of reporting

A `kind: command` block that explodes degrades to FAIL. A `kind: file` assert
runs in-process, so one exception kills the run before anything is rendered.

Confirmed triggers: a tracked file deleted from the worktree (`git ls-files`
still lists it); `repos:` with nothing under it; `updates:` empty;
`"features": null`; `customizations.vscode: null`; a malformed `pyproject.toml`;
unparseable YAML; and — most likely to meet a real repo — **a `tsconfig.json`
containing a trailing comma**, which is legal JSONC that `tsc` accepts and
`strip_jsonc` does not handle. `YAMLError` is guarded in the register loader and
nowhere else.

Two more crashes: `words.index("install")` raises `ValueError` on
`npm install-ci-test` (a real npm command whose `\b` boundary the regex
matches), surfacing as a SUP-001 failure whose operator-facing message is a
Python traceback; and if `git` is absent from `PATH` the checker crashes rather
than reporting.

**Required:** every assert returns a verdict. A read or parse failure is a FAIL
naming the file and the reason, and the run continues to the next control.

### C — Environments that silently look conformant

| Defect | Confirmed behaviour |
| --- | --- |
| `_git_ls` swallows any non-zero `git` exit and returns an empty set, so every file predicate goes false | A non-git directory holding a root-running `Dockerfile`, an `AWS_SECRET_ACCESS_KEY` in a workflow and a `pyproject.toml` reports eight predicate skips and exits 0. The reason given — "predicate not satisfied" — is false; the files are on disk. A typo'd `--repo` path behaves identically. This is also the path taken when git refuses a repo for dubious ownership |
| `gitleaks detect` is git-history-only | In a non-git directory it prints "0 commits scanned … no leaks found" and exits 0, so SEC-001 shows a green tick for a scan that examined nothing |
| The `container` predicate is an exact basename match; `repo.dockerfiles()` accepts `Dockerfile.*` and `*.Dockerfile` | A repo whose only container file is `Dockerfile.prod` ending in `USER root` reports `BLD-001 SKIPPED (predicate)`, while the assert called directly returns FAIL. A skip hides a violation the checker can already detect |
| `runner.py` uses `shlex.split` with no shell | `run: "true && false"` becomes `['true', '&&', 'false']` and exits 0. The schema accepts such strings, so a future `pytest && mypy` would silently check only pytest |

### D — Assert precision

False negatives — the assert passes while the control's `enforces` does not hold:

| Control | Input that passes |
| --- | --- |
| SEC-002 | `aws-access-key-id: ${{ secrets.PROD_KEY }}` — the scan is a case-sensitive substring match over seven uppercase names |
| TST-001 | `pip install pytest==8.0.0` with no test invocation; and a `workflow_dispatch`-only workflow, because `on:` is never read (theme T-3) |
| SUP-003 | A job-level reusable workflow `uses: owner/repo/.github/workflows/x.yml@main` — only `jobs.*.steps` is walked |
| LNT-001, TST-001 | `continue-on-error: "true"` as a string, and the `\|\| :` idiom, both outside the suppression set |
| TYP-001 | `strict = true` alongside `[[tool.mypy.overrides]] module=["*"] ignore_errors=true` |
| SUP-002 | `renovate.json` containing `{"enabled": false}` — any renovate filename is accepted unparsed |
| SUP-001 | An unpinned `requirements.txt` counted as a lockfile; a TS repo with no workflows at all passing the frozen-install check vacuously; `pip3`, `poetry`, `pdm` unmatched |
| BLD-001 | `ARG USERNAME=root` with `USER ${USERNAME}` — the literal token is compared, never expanded |

False positives — conformant repos that fail:

| Input | Cause |
| --- | --- |
| `pip install \` with the pinned package on a continuation line | Physical lines are iterated |
| CI that lints via `pre-commit run --all-files` | A literal `ruff check` string is required |
| mypy configured in `mypy.ini` | Only `[tool.mypy]` is read |
| An editor locus via `.vscode/extensions.json`, no devcontainer | The check demands a devcontainer extension entry, inventing a hidden LNT-001 dependency on DEV-001's artefact |
| `npm run test`, `make test`, `tox`, `gradle`, `rspec` | The test-command regex lists six spellings |
| A devcontainer using `build.dockerfile` instead of `image` | DEV-001 demands an `image` key; the Dockerfile's own `FROM` pin is never checked |
| `uses: docker://alpine@sha256:<64 hex>` | 40 hex characters are required |

### E — Register and schema gaps

**No tool version exists anywhere in the register**, while four documents state
that one does — `03-devcontainer.md`, `06-devcontainer-setup.md`,
`00-concepts.md` and a comment in `setup.sh` all describe pinning "from the
version recorded in the register". The consequence is pin-many-and-hope:
`markdownlint-cli2@0.23.2` in four places, gitleaks `8.30.1` and its checksum in
two each, `uv==0.12.5` in two, none authoritative. A comment in `lint.yml`
instructs humans to "change all three together" where there are four. Separately,
`02-skill-family.md` § Version policy describes a per-control
`pinned`/`floating-minor`/`latest` field that exists in neither the schema doc
nor the register — and because the validator accepts unknown keys, adding it
would be silently ignored rather than rejected.

**`variance` is read by no code path**, and one of its four values cannot be
implemented as specified: SUP-003 and IAC-001 are `tier: 1` with
`variance: justified` and `baseline: null`, but `00-concepts.md` says a justified
weakening *is* a baseline entry, and the validator rejects any Tier-1 control
carrying a baseline. The mechanism that stops `justified` becoming a loophole is
structurally unreachable for both controls that use it. `CLAUDE.md` compounds it
by listing only two of the four values. `UNCLASSIFIED` is likewise unreachable
from every code path.

**The `kind: command` / `kind: file` taxonomy has been subverted.** **All eight**
`standard-check assert …` blocks are file-shape assertions declared as commands —
not five of seven, as this section previously recorded; the count was re-measured
on 2026-08-17 against the register's own loader. ADR 0002 even describes SEC-002
as "a file-shaped assertion" while the register calls it a command.

This is not cosmetic — GOV-001 derives reachability from `kind: command` blocks
and ignores `kind: file` ones, so the miscategorisation decides that control's
verdict. Measured against the register as it stands, GOV-001 sees:

| What GOV-001 sees | Controls | Consequence |
| --- | --- | --- |
| The bare token `standard-check` | SEC-002, SUP-001, SUP-003, LNT-001, TYP-001, TST-001 | Six blocking controls collapse to one indistinguishable token; any CI step containing that substring marks all six reachable |
| No `kind: command` block at all | SUP-002, DEV-001 | Blocking, `ci`, verified only by file asserts. `commands` is empty, so `reached` is always false and they can pass only via the bare-invocation short-circuit |
| A distinct tool token | SEC-001, BLD-001, IAC-001, DOC-001 | The only four where the reachability test measures anything |

So neither branch of GOV-001 measures reachability: with a bare `standard-check`
step every control passes vacuously, and without one SUP-002 and DEV-001 fail
however well they are wired. This is the control the register calls its
highest-value one, and the guard against theme **T-3**.

**The checker has become a second source of truth** for rules recorded nowhere
in the register: ruff/eslint/mypy/pytest as the mandated tools, the
`charliermarsh.ruff` extension ID, the test-command spellings, a Python-and-Node
lockfile map that lets Go, Rust and Java repos pass SUP-001 with no lockfile, the
Dependabot ecosystem spellings, the seven-name cloud-key list, the suppression
patterns, the predicate grammar, the `GOV-\d{3}` pattern, `rationale_adr` file
existence, strict semver, and the Tier-1 baseline rule. Phase 2's shared assert
implementation inherits all of it, so the boundary needs deciding here: what
belongs in the register, and what is legitimately the checker's business.

The lockfile map is the measured harm: it knows Python and Node, so a Go, Rust or
Java repository with no lockfile passes SUP-001. That exemption was never
decided — it is which dictionary keys someone wrote — and because the register
does not record it, no review and no `review_by` date will ever surface it.
Recorded as [ADR 0018](adr/0018-register-checker-boundary.md).

### F — Deployment and provenance

`lint-md` owns both `.pre-commit-config.yaml` and `.github/workflows/lint.yml`,
and both were hand-edited in Phase 1. Its own templates write
`actions/checkout@v6` (a floating tag, failing SUP-003) and an unversioned
`npm install -g markdownlint-cli2`, so a re-run reverts the pins and turns
SUP-003 red. That implies a **fourth promotion submission** — an amend against
`lint-md` — which [`05-promotion.md`](05-promotion.md) § Submission order does
not list.

Three of the four `lint-md`-deployed artefacts carry no `ee-control:` stamp,
though `CLAUDE.md` states as fact that they do. The one that has a stamp reads
`register: v0.1.0` against a v0.2.0 register, making the repo's only deployed
artefact stale by the definition in `00-concepts.md` — and the stamp format
carries no contract number, so the documented noise control cannot be evaluated
from a stamp at all.

That last clause is a **Phase 5 dependency, not a cosmetic one**. Phase 5's first
two exit criteria — a version bump must produce no redeployment recommendation, a
contract bump must — are the whole noise argument expressed as a test, and
neither can be evaluated against a stamp that does not carry the contract number.
Fixing the format here is what makes Phase 5 testable; deferring it means
discovering the gap in the phase that depends on it.

Phase 1 also introduced an unrecorded weakening: `extend-exclude = [".claude"]`
in `pyproject.toml` and `.claude/**` in the markdownlint config are what
`00-concepts.md` names as weakening ("adding an ignore path"), applied to
`narrowing-only` controls whose `baseline: null` the schema doc says means no
exemptions are possible.

### Decisions required before Phase 2

These are not code, and they are not the author's to settle alone. Each is
recorded as an ADR — the ADR holds the options, the recommendation and the
consequences, so this table stays an index and does not become a second copy of
the reasoning. Ratifying one means moving it to `Accepted` via `/adr-approve`.
All four are now settled; none is yet fully implemented, and the exit criteria
below — not this table — track that.

| Decision | Recorded in | Why it cannot be deferred |
| --- | --- | --- |
| This repository cannot satisfy CI-001 or SEC-001's remote half. `GET /rulesets` returned 403 ("Upgrade to GitHub Pro or make this repository public"), `security_and_analysis` was null, and `main` reported `protected: false` | [ADR 0014](adr/0014-satisfying-remote-locus-controls.md) — **Accepted and implemented** 2026-08-17 | Settled: the repository is public and both controls stay Tier 1. The capability is confirmed live (`GET /rulesets` now returns `[]`). Two follow-on acts remain — create the ruleset, enable push protection — both blocked on a PAT lacking `Administration: write`, not on any decision |
| `main` was unprotected, so every blocking gate was bypassable | [ADR 0015](adr/0015-interim-branch-discipline.md) — **Superseded** by [ADR 0008](adr/0008-protected-default-branch.md) 2026-08-17, never ratified | Closed by enforcement rather than by convention: the ruleset makes CI-001 mechanical, so the proposed stopgap was redundant before it was decided |
| Whether `SKIPPED (no credentials)` should leave a non-zero exit, a distinct exit code, or a warning | [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md) — **Accepted** 2026-08-17, not yet implemented | Decided: exit `3` for a run with no violation but something it could not verify, `1` for a verified violation, `0` only when every applicable control was verified, and `--require-complete` promotes `3` to `1`. Predicate skips stay `0`. Phase 2's gates inherit these semantics, so the code follows before they are written |
| How a partially-implemented control reports its own incompleteness | [ADR 0017](adr/0017-partial-verification-is-reported.md) — **Accepted** 2026-08-17, not yet implemented | Decided: the register — not the checker — declares a verification block partially implemented with an expiry, and the report renders the computed verdict plus a `partial:` line. The schema addition carries a `register_contract` bump, so it lands before Phase 2's skills read that contract |
| Which verdict-deciding rules belong in the register and which are legitimately the checker's business | [ADR 0018](adr/0018-register-checker-boundary.md) — `Status: Proposed` | About a dozen rules decide verdicts from Python alone (§ E). Phase 2 copies the assert layer into six gate skills, so a rule on the wrong side of the line gets six more copies — the argument that created this phase. Measured harm already: SUP-001 exempts Go, Rust and Java by accident |

### Carried debt — recorded, not gating

- ADR 0013's unsupported line-length passage — **closed**: git history shows
  DOC-001 was introduced already at 250, the commit message said "from the
  previous 80", and the ADR said 120. Three numbers for one event, cited as the
  register's canonical precedent. The passage is removed.
- `standard-check --tier 1` is documented in `02-skill-family.md`, `CLAUDE.md`
  and the CLI's own docstring, but only `run --tier 1` works; `--repo` must
  precede the subcommand; `standard-check drift` is documented — including in
  `.markdownlint.yaml`'s header — and does not exist.
- `setup.sh` is 82 lines across seven sections. `uv` and `gitleaks` belong in
  pinned features, which would also bring them under `devcontainer-lock.json`.
- No repo-root `LICENSE`, though `pyproject.toml` declares Apache-2.0 and
  `05-promotion.md` requires every plugin to ship a copy of it. **Not gating for
  this phase, but gating for Phase 6** — `check_plugin_license.py` fails without
  it, so it now carries a Phase 6 exit criterion rather than sitting here alone.
- `.devcontainer/.env` is mode `0644` while holding a live OAuth token and two
  PATs. A `chmod 600` in `fetch-secrets.sh` costs nothing, and the docs present
  that file as the credential boundary (theme T-5).
- Title-versus-mechanism drift: DEV-001's title says features only; LNT-001's
  says "lint **and format**" while nothing checks formatting; TYP-001 enforces
  "no per-file opt-out" without reading `[[tool.mypy.overrides]]`; SUP-002's
  title is broader than what passes, since the npm and curl pins are precisely
  the two Dependabot cannot propose.
- Doc sweep: the schema doc's rung enum omits `blocking (baselined)`;
  "validated by `standard-check schema` on every commit" is scoped to commits
  touching the register; "every URL in the register is verified to resolve" has
  no mechanism (all thirteen do resolve today); `03-devcontainer.md` lists a
  `claude-user-settings.json` that does not exist; CLAUDE.md's "sixteen
  controls" miscount is **closed**, corrected when its § Documents gained a full
  index; the README drops "third-party" from SUP-003, which the owner-exemption
  depends on;
  `06-devcontainer-setup.md`'s description of `setup.sh` omits three of its jobs;
  and the README's "remote *halves* report SKIPPED" understates the report, which
  renders the whole of SEC-001 as `SKIPPED (no credentials)` because a control's
  verdict is the worst of its blocks.

### Exit criteria — phase 1.5

- [x] GOV-002 fails on a baseline grown in a **commit**, not only in a dirty
      worktree — it now compares against the merge-base with the default branch
      on a branch, and the parent commit on the default branch itself, and names
      which reference it used
- [x] No assert can abort the run: a read or parse failure is a verdict naming
      the file, and later controls are still evaluated. The confirmed triggers
      are fixed at source too — trailing commas in JSONC, `None`-valued config
      sections, and `npm install-ci-test`
- [x] A target that is not a git repository is an error, never a page of
      `SKIPPED (predicate)` verdicts. `schema` and `explain` are exempt: they
      read the register, not the repository
- [ ] A control whose tool is absent reports `UNCLASSIFIED`, distinct from FAIL
- [ ] A register `run:` string containing a shell operator is either rejected at
      schema time or executed correctly — never silently truncated
- [ ] The `container` predicate and BLD-001's assert agree on what a Dockerfile is
- [ ] DOC-001 verifies its three loci and the ceiling its `enforces` names
- [ ] The exit code distinguishes "no credentials" from "all clear", per
      [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md) — `3` for
      unverified-but-no-violation, `1` for a verified violation, `0` only for a
      fully verified run, and `--require-complete` promotes `3` to `1`. The
      `Standard` workflow passes that flag
- [ ] GOV-001 matches **invocations, not substrings**: a step is evidence for a
      control only if it actually runs that control's verification. The two
      degenerate readings in § E are gone — six controls no longer collapse to
      the bare token `standard-check`, and a bare invocation no longer marks
      every control reachable at once
- [ ] Every verification block declares the `kind` it actually is. No file-shape
      assertion is declared `kind: command`, and GOV-001 can find a blocking `ci`
      control reachable through its `kind: file` blocks — otherwise SUP-002 and
      DEV-001 remain permanently unreachable by construction
- [ ] Every row in § D has a test that fails before its fix and passes after
- [ ] The tool-version question is settled in the register, and no version
      string exists in more than one place
- [ ] `variance: justified` is implementable or removed from the vocabulary, and
      `CLAUDE.md` lists whatever survives
- [ ] Every `lint-md`-deployed artefact this repo has edited carries a
      provenance stamp, and the amend submission against `lint-md` is raised
- [ ] The stamp format carries the **register contract number**, not only the
      register version, so Phase 5's first two criteria are evaluable from a
      stamp. The one existing stamp reads `register: v0.1.0` against a v0.2.0
      register and is corrected
- [ ] The unrecorded weakening is closed: `extend-exclude = [".claude"]` in
      `pyproject.toml` and `.claude/**` in the markdownlint config are either
      removed, or recorded in the register as the variance they are. A
      `narrowing-only` control with `baseline: null` admits no exemptions, so
      leaving them undeclared is the repository that authored the variance rule
      breaking it
- [ ] The register rejects unknown keys
- [x] ADRs 0014–0017 are ratified — each moved from `Proposed` to `Accepted`, or
      superseded by a recorded alternative. 4 of 4 done: 0014 Accepted and
      implemented, 0015 Superseded by 0008 without ever being ratified, 0016 and
      0017 Accepted 2026-08-17 and not yet implemented. Ratification is not
      implementation — the criteria above and below carry that
- [ ] [ADR 0018](adr/0018-register-checker-boundary.md) is ratified, and the
      rules its test moves are in the register while the rules that stay have a
      recorded reason. SUP-001's lockfile ecosystems are register facts, so a
      Go, Rust or Java repo no longer passes it with no lockfile
- [ ] ADR 0017 is **implemented**, not merely accepted — the register can
      declare a verification block partially implemented, with an expiry date
      and a named unverified property; GOV-001 carries that declaration instead
      of an unqualified `PASS`; and a declaration past its expiry fails the way
      GOV-003's `review_by` does
- [x] ADR 0014 is **implemented**, not merely accepted — the repository is
      public as of 2026-08-17, confirmed by the rulesets API returning `[]` where
      it returned `403 Upgrade to GitHub Pro or make this repository public`
- [x] The default-branch ruleset exists and secret scanning push protection is
      enabled, so CI-001 and SEC-001 hold *in fact* — ruleset
      `default-branch-protection` (id `20937135`, `active`, no bypass actors)
      created 2026-08-17, `main` now reports `"protected": true`, and a direct
      push to `main` was observed being refused

The second criterion stops at the platform state being *correct*. Whether the
checker can *verify* it is Phase 3's `kind: remote` work and belongs to Phase 3's
exit criteria — requiring it here would make Phase 1.5 unclosable by its own
terms, which is the error this plan already made once by putting the devcontainer
in Phase 2.

The § D criterion is the real gate this time. Phase 1's suite passed 48 checks
while GOV-002 could not fail, a trailing comma could abort the run, and a
non-git directory reported clean — it exercised the paths the author had in mind
rather than the paths an adversary would take, which is the same critique this
repo levels at its predecessor.

## Phase 2 — The gates and the template

Build the `gate-*` skills and the devcontainer template together, because the
gates are what make the template's output verifiable.

Order within the phase: `gate-secrets` first, as the reference implementation.
It exercises every locus (`pre-commit`, `ci`, and `remote` in Phase 3), so
whatever shape works for it works for the rest. The others follow it.

Alongside them, the `.devcontainer/` **template** per
[`03-devcontainer.md`](03-devcontainer.md) — image digest-pinned,
`devcontainer-lock.json` present, `setup.sh` short.

The template is a generalisation of this repo's own container from Phase 0.5,
not a fresh implementation: strip the ee-standard-specific parts (the Python
version, the volume name, `markdownlint-cli2` as a hard dependency), keep the
structure. Anything the generalisation cannot carry across is a sign the
original was wired to this repo in a way the spec did not intend, and should be
fixed in both.

### Exit criteria — phase 2

- [ ] `gate-secrets` deploys onto a repo with none of its config, and
      `standard-check` then reports SEC-001 PASS for its local loci
- [ ] Every gate writes a provenance stamp its own verify step reads back
- [ ] Gates and checker share one assert implementation — verified by there
      being one copy, not by comparing two
- [ ] The devcontainer template builds, and DEV-001 passes against it
- [ ] Every SKILL.md passes preflight P1–P11
- [ ] `standard-adopt` end-to-end on a scratch repo: plan → confirm → deploy →
      verify → commit, with the verify step genuinely able to fail

That last clause matters. A verify step that has never been observed failing is
not known to work — deliberately break a deployed config and confirm the run
reports it.

## Phase 3 — Remote controls and meta-controls

The locus that gets forgotten, done deliberately.

Implement `kind: remote`: GitHub push protection state, branch ruleset shape,
and the presence of a workflow that can actually fail. Build `gate-repo` to
create the ruleset via the API.

Then GOV-001, which is the highest-value control in the register and cannot be
finished before this phase: proving a `blocking` control is *reachable from a CI
step that can fail* requires reading platform state, not files. A workflow file
that exists but is not a required check is precisely theme **T-3** — declared but
unreachable — and only a remote check catches it.

### Exit criteria — phase 3

- [ ] Remote verification passes against a real repository
- [ ] With no credentials, remote checks report `SKIPPED (no credentials)` and
      the run does **not** exit 0 on that basis alone
- [ ] GOV-001 correctly fails a repo whose lint workflow exists but is not a
      required status check
- [x] GOV-002 fails when a baseline file grows by one line — **already
      satisfied** by Phase 1.5's first criterion, which made GOV-002 compare
      against the default branch's merge-base. GOV-002 reads the register, not
      platform state, so nothing here is deferred to this phase; the box is
      listed for completeness of the meta-control set
- [ ] GOV-003 fails on a control past `review_by`
- [ ] `gate-repo` confirms before every remote mutation, independently of the
      plan-level confirmation

## Phase 4 — The consumer repo

The actual test. A second repository that did not author the standard, set up
end to end by following only the published instructions.

Sequence, per [`03-devcontainer.md`](03-devcontainer.md):

1. Create the repo with the `.devcontainer/` template
2. Run `/project-init` — it configures the devcontainer for the stack
3. Run `/standard-adopt` — it deploys the gates
4. Run `standard-check` — it passes
5. Deliberately weaken something. Confirm the checker catches it, and that
   `standard-variance` classifies the direction correctly.

### Exit criteria — phase 4

- [ ] The consumer repo reaches full Tier-1 conformance
- [ ] No step required knowledge held only by the author
- [ ] `project-init` and `standard-adopt` compose without fighting over
      `devcontainer.json`
- [ ] Weakening a `narrowing-only` control is caught and classified
- [ ] The three known `UNCLASSIFIED` cases report as `UNCLASSIFIED`, not as a
      guess in either direction
- [ ] **The devcontainer template is obtainable without access to a private
      repo.** `ee-skills-incubator` is private and not a GitHub template; if that
      is the only source, the plan has an access-shaped single point of failure.
      Resolve by a public template repo or a `templates/devcontainer/` directory
      in the plugin.

## Phase 5 — Staleness and the sweep

Wire the mechanism that keeps deployments current.

- `deploys.json` sidecars, with contract versions
- The `skill-update` widening (submission 2 in
  [`05-promotion.md`](05-promotion.md))
- A scheduled sweep running `standard-check` across repos, reporting rather than
  fixing

### Exit criteria — phase 5

- [ ] Bumping a gate's version *without* changing its output produces **no**
      redeployment recommendation
- [ ] Bumping its contract version *does*
- [ ] `skill-update` reports an owed deployment where every plugin is current,
      and does not print *Already done* over it
- [ ] The sweep runs unattended and produces a report nobody has to ask for
- [ ] A repo that has never deployed is distinguishable from one deployed and
      current, and from one deployed and stale

The first two criteria are the whole noise argument, expressed as a test. If a
documentation-only release triggers a recommendation, the mechanism will be
ignored within a month and the phase has failed regardless of what else passes.

## Phase 6 — Promotion

Per [`05-promotion.md`](05-promotion.md), in the order given there: the
`CONTRIBUTING.md` corrections first (small, independent, establishes contact),
then `ee-standard` plus the `governance` category, then the `skill-update`
amendment — plus the `lint-md` amendment identified in Phase 1.5 § F, which
makes four.

### Exit criteria — phase 6

- [ ] A repo-root `LICENSE` exists and is copied into the plugin —
      `check_plugin_license.py` fails without it, and `pyproject.toml` already
      declares Apache-2.0. Carried as debt since Phase 1.5, gating here
- [ ] All four submissions raised (the three in `05-promotion.md`, plus the
      `lint-md` amendment from Phase 1.5 § F)
- [ ] `ee-standard` installable from the marketplace
- [ ] The consumer repo re-adopts from the *marketplace* copy and still passes —
      proving the plugin works when installed, not only when developed

## What is deliberately not in scope

| Excluded | Why |
| --- | --- |
| Tier 2 and Tier 3 controls | Tier 1 must be proven end to end first. Adding controls is cheap once the machinery works and expensive before. |
| Auto-fix | Notify, never redeploy. Proposed fixes are a Phase 5+ conversation, and only ever as a PR. |
| Non-GitHub platforms | `remote` verification is GitHub-shaped. Another platform means another assert set, which is a real project, not a flag. |
| Replacing `lint-md`, `project-init`, `devcontainer-check` | They work. The standard composes with them. |

## Sequencing risk

The plan's dependencies are strict in three places and loose everywhere else:
Phase 0.5 gates Phase 1, Phase 1.5 gates Phase 2 (because Phase 2 copies the
assert layer into six skills), Phase 1 gates everything after it, and Phase 4
gates Phase 6. Phases 2 and 3 can overlap once the checker's assert interface is
settled.

The genuine risk is Phase 4 revealing something Phases 1–3 assumed. That is the
purpose of Phase 4, and discovering it there costs a rework; discovering it after
promotion costs a marketplace amendment and everyone who already installed it.
