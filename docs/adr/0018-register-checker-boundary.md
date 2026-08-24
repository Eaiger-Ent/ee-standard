# ADR 0018: Draw the Boundary Between Register and Checker

**Status:** Accepted
**Date:** 2026-08-17
**Revision:** 8

Ratified decision from
[`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § Decisions required.

**Implemented** over four passes, at register contracts 3, 5, 6 and 8 — see the
*Applied* sections below. Every rule the test moves is now in `controls.yaml`,
and every rule that stayed carries its reason here.

The fourth pass exists because the third claimed a completion it did not have.
`cloud-key names` are named in the Decision below and were moved in none of the
first three passes, while the exit criterion recording this ADR as implemented
was ticked over them. That is the failure this record names in its own
Decision — *an unreasoned omission is the failure this record exists to stop* —
so it is recorded here rather than quietly corrected. See
[`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § H4. Acceptance settled the test
and what it classifies; these sections record what was actually moved, which is
the part a reader can check.

## Background

The core invariant is that a register entry **is** the control, and that every
other artefact derives from the register rather than restating it. § E of the
build plan found that `standard-check` breaks this in about a dozen places. Each
of the following decides a verdict and is recorded only in Python:

- ruff, eslint, mypy and pytest as *the* mandated tools
- the `charliermarsh.ruff` extension ID as proof of an editor locus
- the six accepted spellings of a test command
- a lockfile map covering Python and Node only
- the Dependabot ecosystem spellings
- the seven-name, case-sensitive cloud-key list
- the failure-suppression patterns
- the predicate grammar
- the `GOV-\d{3}` ID pattern, `rationale_adr` file existence, strict semver, and
  the Tier-1 baseline rule

This is theme **T-2** — a second copy of a rule that can drift from the
register — with the aggravation that the second copy is in a different language
and therefore invisible to anyone reviewing `controls.yaml`.

The harm is not hypothetical. SUP-001's lockfile map knows Python and Node, so a
Go, Rust or Java repository with no lockfile at all passes a Tier-1 control. The
decision to scope SUP-001 to two ecosystems was never taken; it is an artefact of
which dictionary keys someone wrote. Nothing in the register records it, so
nothing can review it and no `review_by` date will ever surface it.

The converse error exists too. GOV-001 reads `kind: command` blocks and ignores
`kind: file` ones, so SUP-002 and DEV-001 — blocking, `ci`, and verified only by
file asserts — have no command token at all and can never be found reachable.
Six further controls collapse to the single token `standard-check`. Whether that
is a checker bug or a register modelling error cannot be answered without
knowing where the boundary is.

Phase 2 copies the assert layer into six `gate-*` skills. Whatever is on the
wrong side of this line gets six more copies, which is the same argument that
created Phase 1.5.

Not everything belongs in the register. How to parse a YAML workflow, what
counts as a step, how to walk a `pyproject.toml` — these are implementation, and
moving them into the register would make it a program. The question is not
*whether* the checker holds knowledge but *which* knowledge it may hold.

## Alternatives Considered

### Option 1: Leave the boundary where it is

The register records intent; the checker records how intent is detected.

**Pros:** No work, and no `register_contract` bump. Arguably the boundary most
tools draw.
**Cons:** Does not survive its own example. "A lockfile is required" is intent;
"only Python and Node repos need one" is also intent, and it lives in the
checker. The distinction between intent and detection is not observable from
either artefact, so in practice every disputed rule lands wherever it was first
written.

### Option 2: Move every verdict-deciding rule into the register

If a rule can change a verdict, it is a control detail and belongs in
`controls.yaml`.

**Pros:** Maximally faithful to the core invariant, and trivially decidable.
**Cons:** The predicate grammar and the YAML-walking rules can change verdicts
too, and expressing them in the register turns it into a policy language — a
real project, and one this plan explicitly excludes. It also makes the register
version-lock to the checker's internals, which is the coupling `register_contract`
exists to avoid.

### Option 3: Classify by whether a consumer would vary it

A rule belongs in the register if a reasonable Equal Experts repository might
need it to differ **without** a checker change. Everything else is the checker's
business.

Applied to the list above: mandated tools, lockfile ecosystems, test-command
spellings, cloud-key names, Dependabot ecosystems and suppression patterns move
to the register — a consumer repo could legitimately need any of them to differ.
The predicate grammar, the ID pattern, semver strictness, `rationale_adr`
existence and the Tier-1 baseline rule stay in the checker: they are properties
of the register format, not of any consumer, and a repo needing them to differ is
a repo asking for a different standard.

**Pros:** One test, answerable per rule, and it produces a defensible answer for
every item § E lists. It also names *why* something stays — being a fact about
the format rather than about a repo — so future additions can be classified the
same way rather than by precedent.
**Cons:** "Might reasonably need" requires judgement, and the boundary will be
argued at the margin. The move is a schema addition and therefore a
`register_contract` bump; done late it invalidates deployed artefacts twice.

## Decision

We will classify every rule that decides a verdict by a single test — *could a
reasonable Equal Experts repository need this to differ without changing the
checker?* — move the rules that answer yes into `controls.yaml`, and record in
this ADR the rules that answer no together with the reason they are properties of
the register format rather than of any repository.

The move lands in the same pass that bumps `register_contract` to 3, alongside
[ADR 0017](0017-partial-verification-is-reported.md)'s partial-declaration field
and the unknown-key rejection. Batching them is deliberate: each bump marks every
deployed artefact stale, and three bumps for one phase's work would train
consumers to ignore the signal that staleness is supposed to carry.

Option 2 was rejected because expressing the predicate grammar in the register
makes the register a program, which the build plan excludes by name. Option 1 was
rejected because it has already failed in the one case that was measured: SUP-001
silently exempts three major ecosystems, and no reading of "the register records
intent" would have caught it.

Ratified on 2026-08-17. The classification above is the ratified part; the list
is not closed, and a rule discovered later is classified by the same test rather
than by where it happens to have been written. A rule that stays in the checker
must carry its reason in this ADR — an unreasoned omission is the failure this
record exists to stop, not an application of it.

### Applied — first pass, register contract 3

| Rule | Where it lives now | Why |
| --- | --- | --- |
| Package ecosystems: manifests, lockfiles, Dependabot spellings | Register, `ecosystems:` | The measured harm. A repo may legitimately use a lockfile spelling the checker has not heard of, and the checker-side map exempted Go, Rust and Java from SUP-001 entirely |
| Pinned tool versions and the gitleaks checksum | Register, `tools:` | Four documents already claimed the register held these. A repo pinning a different markdownlint-cli2 is an ordinary variance, not a checker change |
| `requirements.txt` as a lockfile | Removed | It pins nothing. Accepting it was a false negative (§ D), not a policy |

Asserts now take the register as well as the repository. An assert that cannot
read the register has nowhere to read a register-owned rule from, which is how
the checker became a second source of truth in the first place.

### Applied — second pass, register contract 5

| Rule | Where it lives now | Why |
| --- | --- | --- |
| DOC-001's 250-character ceiling, its tool name, and its editor extension id | Register, in the verify block's `args:` | All three answer *yes*: a repo may tighten the ceiling under `narrowing-only`, and neither the tool nor the editor is a property of the register format |

This pass also establishes **where** a per-control tool fact goes: the verify
block's `args:`, beside the assert that reads it, rather than a new top-level
section. The assert keeps only the shape — that the ceiling may narrow and never
widen, and that every locus the control declares must be wired — which is a
property of the control, not of any repository.

It is the smallest instance of the *Not yet applied* item below, and deliberately
so. DOC-001 has one tool and one extension, so it needed no per-stack model to
move; taking it first gives the larger move a worked precedent to copy instead of
a design argued in the abstract.

### Applied — fourth pass, register contract 8

Three rules: the ratified list's last unmoved item, and two found by applying the
same test to code written after ratification. The Decision says a rule discovered
later is classified by the same test rather than by where it happens to have been
written, and these are the first exercise of that clause.

| Rule | Where it lives now | Why |
| --- | --- | --- |
| The static cloud credentials SEC-002 forbids | Register, `cloud_credentials:` | Named in the Decision above and moved in none of the first three passes. A repository on a cloud the list has not heard of is one where SEC-002 passes for want of a name, and no `review_by` could surface that while the names were in Python |
| Which loci repeat a `literal` tool's version | Register, `tools.<tool>.pinned_at` | Four of *this repository's* filenames, in a checker applied to every repository. Renaming a workflow removed it from comparison silently, and an adopting repository was told its tools were "pinned at no known locus" against a list of paths it had never had |
| What installing from the lockfile looks like, per ecosystem | Register, `ecosystems.<name>.frozen_install` | The same two-key map — python and node — that this ADR's Background calls the measured harm, surviving inside `ci-installs-frozen` after being moved out of `lockfile_present_and_tracked`. A repository with a `go.mod` was told every CI install was frozen, with none checked |

The same pass widens SUP-001's `applies_to` from `[python, typescript]` to
`[always]`, because naming two stacks re-created in the register the exemption
this ADR moved out of the checker. Which ecosystems a repository is in is
detected from `ecosystems:`, and a repository with no package manager at all
passes on that finding rather than on a predicate that never looked.

### Staying in the checker — with reasons

| Rule | Why it is not a register fact |
| --- | --- |
| `github-actions`, `devcontainers`, `docker`, `terraform` Dependabot spellings | Not package ecosystems with manifests and lockfiles but repository features, detected by predicates the register already owns. The spellings are GitHub's, not ours, so no repo could reasonably need them to differ |
| The predicate grammar | Expressing it in the register makes the register a program — excluded by name in the build plan |
| `AAA-NNN` / `GOV-NNN` ID patterns, semver strictness, `rationale_adr` existence, the Tier-1 baseline rule | Properties of the register *format*, not of any repository. A repo needing them to differ is asking for a different standard |
| Reading YAML, walking workflow steps, parsing `pyproject.toml` | Implementation of detection, not the rule being detected |
| Which commands *re-resolve* a dependency graph — `npm install` with unpinned arguments, `uv sync` without `--frozen` | Answering it means parsing a package manager's argument grammar, and argument grammars in the register make the register a program, which is Option 2 above and rejected by name. The positive half — what a frozen install looks like — is a pattern match and moved |
| That `AWS_ACCESS_KEY_ID` and `aws-access-key-id:` name the same credential | A spelling equivalence between an env var and an action input, not a choice any repository makes. *Which* credentials to look for is the register's |

### Applied — third pass, register contract 6

The item this section previously listed as *not yet applied* — the mandated tool
names and their per-locus evidence — is done. It needed a model, and the model
is a `stacks:` section keyed by predicate, each stack carrying `gates:` keyed by
role:

| Rule | Where it lives now | Why |
| --- | --- | --- |
| Which linter and type checker are mandated (`ruff`, `eslint`, `mypy`, `tsc`) | Register, `stacks.<stack>.gates.<role>.tool` | The plainest *yes* on the list. A repository mandating `flake8` is exercising an ordinary variance, not asking for a different checker |
| How CI invokes each | `…gates.<role>.invocation` | Same argument; `ruff check` and `ruff` are different commands and either could be a house choice |
| Where each tool's configuration may live | `…gates.<role>.config`, as `{file, section}` | `mypy.ini` versus `[tool.mypy]` is a repository's choice. `section` exists because a file being present is not the tool being configured in it — `pyproject.toml` is in every Python repository and says nothing about ruff until `[tool.ruff]` is |
| Which key turns strictness on | `…gates.<role>.strict_key` | Belongs to the tool, and the tool is now a register fact, so it travels with it |
| The editor extension id and the pre-commit hook id | `…gates.<role>.editor_extension`, `…pre_commit` | The `charliermarsh.ruff` id this section previously named. A repository on a different editor needs a different id and no new checker |
| What counts as swallowing a failure | Register, `suppression:` | A house idiom the checker has not heard of is a suppression that goes undetected, and adding a pattern strengthens detection. The set has to be reviewable |

Two consequences worth stating, because both are load-bearing.

**A stack is keyed by the predicate that detects it.** `applies_to: [python,
typescript]` on a control and the two stacks are then the same statement made
once, evaluated against files and never self-declared. A stack keyed on an
unknown predicate is a schema error: a stack nothing can detect never applies,
which is theme T-3 inside the register.

**The validator cross-checks loci against gates.** If a control declares an
`editor` locus and an applicable stack's gate names no `editor_extension`, the
register is rejected. Without that, a control could claim a locus its gate had
no way to verify, and whether that failed every repository or was quietly
skipped would depend on how the assert happened to be written — which is the
class of defect this ADR exists to remove, not an instance of it to tolerate.

### Still staying in the checker — the second-pass and third-pass additions

| Rule | Why it is not a register fact |
| --- | --- |
| Reading a boolean at a section path in TOML, INI, JSON or YAML | Detection implementation. The register says *where* and *which key*; how a `.ini` is parsed is not a repository's business |
| `[[tool.mypy.overrides]]` blanket-override detection | The shape of one tool's own configuration format. It is keyed on the register's tool name rather than assumed, so a repository mandating a different checker has no such table read against it |
| The closed set of gate roles (`lint`, `typecheck`) | A property of the register format: a role the checker has no assert for could not be verified however well it were declared |

### Still staying in the checker — the platform-credential additions

Register contract 23 gave SEC-003 a `kind: remote` block reading the expiry of
the credential the run carries ([ADR 0022](0022-a-platform-token-ci-carries.md)
requirement 3). The number it compares against is the register's —
`platform_credentials.<entry>.max_lifetime_hours`, moved there at contract 22 —
and three rules beside it are not.

| Rule | Why it is not a register fact |
| --- | --- |
| The `github-authentication-token-expiration` header, and its `YYYY-MM-DD HH:MM:SS UTC` shape | GitHub's spelling of GitHub's answer. A repository needing a different header name is not exercising a variance; it is talking to a different platform |
| `GITHUB_ACTIONS=true` as how a run knows it is a CI job | The platform's own variable, set by the platform. SEC-003's locus is `ci`, so the block has to know whether this run *is* CI — and no repository could reasonably need that announced differently while still running on Actions |
| `/rate_limit` as the endpoint asked when the question is about the credential rather than the repository | Detection implementation, chosen because it answers for any valid token and needs no permission on the repository. Which endpoint carries a header is not a rule a repository sets |
| That the presence of `X-OAuth-Scopes` identifies a **classic** personal access token | GitHub's own signalling, added at contract 24. What the two instruments *are* is the platform's; that a classic one is refused is the standard's, and is [ADR 0022](0022-a-platform-token-ci-carries.md)'s decision rather than a number in the register |

The boundary holds in the direction that matters: **widen the register's
maximum and the same token changes verdict**, with no checker change, which is
the test the third pass introduced for `stacks:` and the fourth for
`cloud_credentials:`.

### Applied — fifth pass, register contract 12

One rule, and it moves *into* the checker rather than out of it — the direction
this ADR's test also has to answer, or "record the reason" becomes a rule for
one direction only.

`provenance_stamp_present` reads back the stamp of the control whose verify
block is running. The control's id therefore has to reach the assert, and there
were two places it could come from.

| Rule | Where it lives | Why |
| --- | --- | --- |
| Which control a stamp read-back is about | Checker: the runner supplies `args[CONTROL_ARG]` from the block's own position | *No.* A control's own id, written into that control's own entry, is a second copy of it — in the one file this repository maintains to prevent second copies. Worse than redundant: the copy is free to name a *different* control from the one it sits under, so a stamp read-back could report on somebody else's deployment. There is exactly one right answer and the block's position already gives it |

The schema rejects a register that supplies the key itself, so the two sources
cannot both exist. That rejection is the same shape as the `deployed_by` rule
recorded at contract 11: two fields naming one fact, held equal by the
validator rather than by care.

**What forced it.** Matching stamps by *skill* was correct while a gate owned
one control, and became a false green the moment one owned three:
`gate-quality` deploys LNT-001, TYP-001 and TST-001, and a stamp naming any of
them satisfied the read-back of all three. A gate that wrote every artefact and
recorded only the CI steps passed with the editor locus unstamped. The rule did
not change; the number of controls behind it did, which is the same way § H
found four ticked criteria that were not met.

**What it still does not check**, stated because a half-closed hole reads as a
closed one: *how many* artefacts a gate should have stamped, and at which loci.
That list is the plugin's `deploys.json`, not the register's, and reading a
plugin from the checker is Phase 5's sweep. Each control now proves its own
deployment was recorded. No control proves the deployment was complete.

## Consequences

**Positive outcomes:**

- Every rule that can change a verdict is either in the register or has a
  recorded reason for not being, so § E's list stops being open-ended.
- SUP-001's ecosystem scope becomes reviewable, and gains a `review_by` date like
  everything else in the register.
- Phase 2's six gate skills inherit a boundary rather than a habit, which is the
  whole reason to settle it before they are written.

**Trade-offs and risks:**

- A `register_contract` bump and a schema addition, on top of ADR 0017's.
  Batching limits it to one bump but not to zero.
- The classification is a judgement, and a rule placed wrongly is harder to move
  after Phase 2 than before it.
- Moving tool names into the register makes the register longer and more
  opinionated. That is the intended effect — an opinion nobody can find is not a
  standard — but it raises the cost of every future review.

## Related ADRs

- [ADR 0017: Report a Partially Implemented Control as Partial](0017-partial-verification-is-reported.md)
  — the other schema addition in the same `register_contract` bump.
- [ADR 0016: Give "Could Not Verify" Its Own Exit Code](0016-exit-codes-for-unverifiable-controls.md)
  — a rule moved into the register can be declared partially implemented rather
  than silently absent.
- [ADR 0009: Lint From One Pinned Definition at Every Locus](0009-single-lint-definition.md)
  — the same argument applied to a tool's configuration rather than to the
  register.
- [ADR 0021: How Remote Verification Authenticates](0021-how-remote-verification-authenticates.md)
  — the reason the transport, the repository identity and the failure taxonomy
  for `kind: remote` are held in the checker, recorded because this ADR requires
  such a reason to exist.
- [ADR 0019: Verify Exemptions Against the Files a Repository Tracks](0019-exemptions-cannot-hide-tracked-files.md)
  — classified under this ADR's test as a rule that stays in the checker.
- [ADR 0020: Invoke a Pinned Tool by the Path Its Lockfile Owns](0020-a-locus-reaches-the-pinned-artefact.md)
  — made `source: lockfile` mean what this ADR's third pass said it meant.
- [ADR 0023: Choose the Smallest Model a Task Can Be Trusted To](0023-smallest-model-a-task-can-be-trusted-to.md)
  — `agent_models:` is a register fact under this ADR's test.
- [ADR 0024: Keep Only Direction Values in the Variance Vocabulary](0024-variance-vocabulary-is-direction-only.md)
  — the variance vocabulary is a register-format property, so the closed set
  stays in the checker under this ADR's test.

## References

- [OpenSSF Baseline](https://baseline.openssf.org/)
- [Open Policy Agent — policy language](https://www.openpolicyagent.org/docs/policy-language)

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-17 | Original decision: classify every verdict-deciding rule by whether a reasonable Equal Experts repository could need it to differ without changing the checker. | Nathan Carney |
| 2 | 2026-08-17 | § Applied — first pass, register contract 3. Package ecosystems, pinned tool versions and the gitleaks checksum moved to the register; `requirements.txt` removed as a lockfile. | Nathan Carney |
| 3 | 2026-08-17 | § Applied — second pass, register contract 5. DOC-001's 250-character ceiling, tool name and editor extension id moved into the verify block's `args:`, establishing where a per-control tool fact goes. | Nathan Carney |
| 4 | 2026-08-18 | § Applied — third pass, register contract 6. Mandated tool names and their per-locus evidence moved to a `stacks:` section keyed by predicate. | Nathan Carney |
| 5 | 2026-08-18 | § Applied — fourth pass, register contract 8. SEC-002's credential names, `tools.<tool>.pinned_at` and `ecosystems.<name>.frozen_install` moved; SUP-001's `applies_to` widened to `[always]`. | Nathan Carney |
| 6 | 2026-08-20 | § Applied — fifth pass, register contract 12. | Nathan Carney |
| 7 | 2026-08-24 | § Still staying in the checker — the platform-credential additions. Records why the token-expiry header, the Actions variable and the credential-probe endpoint are the checker's, while the maximum they are compared against is the register's. | Nathan Carney |
| 8 | 2026-08-24 | Same section, one row: the presence of `X-OAuth-Scopes` identifying a classic personal access token, added with register contract 24. | Nathan Carney |

Revisions before 2026-08-23 are backfilled from the amendments in the body and from git, per [ADR 0025](0025-an-amendment-is-a-recorded-revision.md); they were not recorded at the time.
