# Concepts

The vocabulary every other document in this repo uses. Read this first; the rest
assume it.

These ideas were derived from a retrospective on `generate-ee-slides`, where the
tooling was individually good and collectively leaky. The failures were not
missing tools — they were missing *relationships between* tools. Each concept
below names one of those relationships.

## The control register

`controls.yaml` is the single source of truth for what conformant means. Every
other artefact — CI workflow, pre-commit config, gate skill, devcontainer,
conformance checker — **derives from it rather than restating it**.

This is the keystone. The predecessor's most expensive defects came from the
same rule existing in three places and drifting between them: one lint config
for the editor, another for pre-commit, a third inlined in CI. When a rule has
one definition and many references, drift becomes impossible rather than merely
discouraged.

A register entry is not documentation of a control. It **is** the control.
Deleting the entry removes the enforcement; weakening the entry weakens the
enforcement. That property is what makes the register auditable.

## The enforcement ladder

Every control sits on exactly one rung:

| Rung | Meaning |
| --- | --- |
| `advisory` | Reported. Never fails anything. |
| `warn` | Surfaced prominently, still does not fail the build. |
| `blocking` | Non-zero exit fails the build. |
| `blocking (baselined)` | Blocking for new code; a recorded set of existing violations is tolerated. |

Movement up the ladder is **only** by explicit decision, recorded with a named
owner and a date. Nothing is promoted because it happened to start passing.

The rung matters more than the tool. A linter at `advisory` is a suggestion box.
The predecessor had several excellent tools permanently parked at `advisory`
because no one had decided to promote them, and no mechanism ever asked.

## Locus discipline

A control's **locus** is where it runs: `editor`, `pre-commit`, `ci`, `remote`.

The rule is *pin once, reference many*. The same version of the same tool
reading the same configuration at every locus. When the editor and CI disagree,
engineers learn to distrust the editor, and the fast feedback loop — the one
that is actually cheap — stops being used.

`remote` is the locus most often forgotten. It covers platform state that no
file in the repository can express: branch protection, push protection,
scheduled triggers. See *Three kinds of verification* below.

## Baseline and burndown

A baseline is a recorded list of existing violations tolerated at the moment a
control was promoted to blocking. It exists so that a control can start blocking
*today* on new code without a repo-wide cleanup first.

Two properties make it a migration rather than an exemption list:

1. **It may only shrink.** `GOV-002` fails the build if any baseline grows.
2. **Its size is the burndown metric.** No separate tracking is needed — the
   artefact is the measure.

Tier-1 controls carry `baseline: null` deliberately. A greenfield repo has no
legacy to exempt, and a control that cannot be met at birth does not belong in
Tier 1.

## Three kinds of verification

| Kind | Verdict comes from | Example |
| --- | --- | --- |
| `command` | Process exit code | `gitleaks detect` |
| `file` | A file exists and matches a shape | Dockerfile's final `USER` is non-root |
| `remote` | Platform API state | Branch protection requires a passing check |

Most conformance tooling implements the first two and omits the third — which is
precisely where a large share of real drift lives. Branch protection silently
relaxed, push protection disabled during an incident and never re-enabled, a
scheduled scan whose trigger was removed: none of these change a single tracked
file, so a repo can be fully conformant on disk and unprotected in fact.

## Meta-controls

Three controls check the register rather than the code:

- **GOV-001** — every control declared `blocking` is reachable from a CI step
  that can actually fail.
- **GOV-002** — no baseline grew.
- **GOV-003** — no control is past its `review_by` date.

Without these the register rots quietly. GOV-001 in particular targets the
predecessor's most dangerous failure mode: a gate that was configured, believed
in, and unreachable.

## Tiering

| Tier | When it applies | Baselines |
| --- | --- | --- |
| 1 | Birth conditions — true from the first commit | Never |
| 2 | Adopted within the first quarter, often via an advisory window | Permitted |
| 3 | As earned — depends on the project's maturity or domain | Permitted |

Modelled on the [OpenSSF Baseline](https://baseline.openssf.org/) approach:
a small non-negotiable core, then graduated expectations. Tier 1 is deliberately
short. A long list of birth conditions gets negotiated down at the worst possible
moment — the day someone is trying to ship.

## Variance

A repo may need to differ from the standard. The question is never *whether*
variance happens; it is whether variance is **visible and directional**.

| Value | Meaning |
| --- | --- |
| `forbidden` | No local deviation. Change the register instead. |
| `narrowing-only` | Local config may add rules or tighten thresholds, never remove or loosen. |

Because configs are typed and declarative, a delta usually has a knowable
direction — adding a lint rule strengthens, raising a coverage floor
strengthens, adding an ignore path weakens. A permitted weakening **is** a
baseline entry: it inherits the owner, the expiry, and the may-only-shrink rule.

**`justified` and `free` were removed at register contract 3.** `justified`
allowed any direction given a recorded reason, owner and expiry — and the
mechanism that kept it from being a loophole was that the weakening became a
baseline entry. But every Tier-1 control carries `baseline: null` by design and
the validator rejects any Tier-1 baseline, so for both controls that used it
(SUP-003 and IAC-001) that mechanism was structurally unreachable: the value
permitted weakenings it had no way to record. Both moved to `narrowing-only`,
which is stricter, so no control was loosened by the removal. `free` asserted
only that a control exists and had no users.

## The provenance stamp

Every artefact a gate skill deploys carries a comment identifying what wrote it,
which control it serves, and from which register version **and contract**:

```text
# .markdownlint.yaml — written by the gate skill
# ee-control: DOC-001  ee-skill: lint-md@1.0.6  register: v0.5.0  register-contract: 5
```

`register-contract` is not decoration. The register's *version* moves for any
change including a typo in a comment; the *contract* moves only when a control's
`rung`, `verify` or `variance` changes — that is, only when what gets deployed
could differ. Recording only the version means every stamp goes stale on every
release, which is the noise this design exists to avoid, and a reader comparing
`v0.5.0` against `v0.5.1` cannot tell whether anything they hold is affected.
With the contract in the stamp, they can.

A file a skill owns **in part** carries the stamp above the section it owns,
not at the top of the file. `.pre-commit-config.yaml` holds hooks for five
controls, only one of them `lint-md`'s; a whole-file stamp would claim the other
four.

This makes "deployed but stale" **computable** rather than a matter of memory.
Three distinct states become distinguishable:

| State | Detected by |
| --- | --- |
| Never deployed | No stamp, no artefact |
| Deployed and current | Stamp matches installed skill and register contract |
| Deployed and stale | Stamp is behind the installed skill's deployment contract or the register contract |

Staleness is **reported, never enforced** — see § Notify, never redeploy below.
A stale stamp is a recommendation to redeploy, so nothing in the checker fails a
build over one. What is checked is that a stamp is *well-formed*: that it parses
and names a control the register defines. A stamp naming `DOC-002` where no such
control exists is a defect in the deployment, not a staleness signal.

## Notify, never redeploy

Nothing in this design rewrites a repo's CI configuration automatically.
Deployment is always a deliberate act that produces a reviewable pull request.

What the tooling owes you is not a silent update — it is *knowing a deployment
is owed*, at the moment that becomes true. Recommendation is keyed to a
**deployment contract version** that changes only when the written output
changes, so a documentation-only release of a gate skill stays silent. See
[`02-skill-family.md`](02-skill-family.md) § Staleness.

## The plugin boundary

Determinism is the dividing line. Plugins run only inside Claude Code; CI has no
Claude in it. So:

> A plugin can **install** a gate, **explain** a gate, and **propose fixes for**
> a gate. It cannot **be** the gate.

The gate itself is always a pinned binary reading a pinned config, invoked
identically at every locus. This is why the skill family and the conformance
checker are separate things: the checker is an ordinary executable that runs in
CI, and the skills are how it gets installed and kept current.

## Cross-area themes

The five recurring failure patterns from the predecessor retrospective. Each
Tier-1 control exists to close at least one of them.

| Theme | Pattern |
| --- | --- |
| T-1 | A stated standard that nothing enforces |
| T-2 | One definition copied, then diverged |
| T-3 | Declared but unreachable |
| T-4 | Failures absorbed rather than surfaced |
| T-5 | The credential boundary least defended |
