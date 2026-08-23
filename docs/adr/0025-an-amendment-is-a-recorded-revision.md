# ADR 0025: Record an Amendment as a Numbered Revision

**Status:** Accepted
**Date:** 2026-08-23
**Revision:** 1

## Background

[ADR 0024](0024-variance-vocabulary-is-direction-only.md) established that an
Accepted ADR whose decision stands but whose record went stale is **amended in
place**, and that supersession is for a decision that has been replaced. That
settled *when* to amend. It left *how an amendment is visible* undecided, and
the gap is not small.

Seven ADRs in this corpus are amended: 0005, 0006, 0012, 0016, 0018, 0019 and
0020. Not one of them says so in its header. ADR 0005 reads
`**Status:** Accepted` and `**Date:** 2026-08-16` — byte-identical to its
pre-amendment header — while a bold paragraph fourteen lines into § Decision
reverses the variance value it recorded. A reader scanning headers sees an
unamended 2026-08-16 decision. A reader who opens the file and skims to
§ Decision reads the original clause first and the amendment second.

That is how ADR 0016 came to state a bound that had not held for six days.
Phase 3 landed, the tolerance did not expire, and the ADR went on asserting
"expires by construction" until an `/adr-consistency` scan read it. The
amendment was eventually written by hand, by someone who happened to be
auditing. Nothing surfaced it, and nothing would have.

Three things are missing, and they are separable:

1. **Detection.** Whether an ADR has been amended at all, visible without
   reading it.
2. **Content.** What each amendment changed, as a summary rather than a diff.
3. **Ratification.** Who approved the amendment, and when. An in-place edit to
   an Accepted decision is a governance act; today it is indistinguishable from
   a typo fix.

The installed `adr-toolkit@0.1.11` supplies none of them.
`adr-structure-rules.md` fixes six required sections and two header fields;
`adr-lifecycle-rules.md` models an ADR as written once and thereafter only
changing status. There is no revision field, no history section, and no
approver field in any of the eight sub-skills. Amendment is absent from the
model rather than under-specified in it.

## Alternatives Considered

### Option 1: Rely on git

`git log --follow docs/adr/0005-pinned-ci-actions.md` already holds every
change, with author, date and diff. Add nothing.

**Pros:** Zero maintenance, zero drift, and it is already true. The history
cannot be wrong, because it is not a copy — it is the change itself. Any
hand-written summary of changes is a second account of what git already knows,
which is the duplication this repository exists to prevent.

**Cons:** Git records **commits**, not **decisions**, and the two do not
correspond. Commit `c79c943` amends nine ADRs at once; nothing in it lets a
reader ask "what changed in ADR 0005, and who ratified it" without reading a
diff spanning eight other files. It also records the author of an edit, never
the approver of a decision — on this repository those are the same person, and
on an adopting repository they must not be. Worst of all it is invisible at the
point of use: the failure this ADR addresses is a reader trusting a stale
clause in an open file, and no property of the git history reaches them there.

### Option 2: A `**Superseded by:**`-style header field only

Add one header line — `**Amended:** 2026-08-17, see § Decision` — and stop.
Detection solved; content and ratification left in the body prose that already
carries them.

**Pros:** Minimal. One line per amended ADR, greppable, no new section, nothing
for the toolkit to trip over, and no structure to maintain.

**Cons:** Solves one of the three problems. It cannot answer "what changed"
without the reader opening the file and finding the right paragraph, it records
no approver at all, and it does not compose: a second amendment either
overwrites the first date or turns the field into a list, at which point it is a
history table with worse formatting.

### Option 3: A numbered revision, with a history table

A `**Revision:** N` header field on every ADR, and — only where `N > 1` — a
`## Revision History` section holding one row per revision: number, date, what
changed, and who ratified it.

**Pros:** Answers all three questions in the order a reader needs them. The
header is greppable across the corpus, so "which ADRs have been amended" is one
command. The table carries a one-line summary and an approver per revision,
which git cannot supply. It composes: a fourth amendment is a fourth row. And
it is mechanically checkable — the revision number must equal the row count,
which makes a hand-edited header a build failure rather than a discrepancy
nobody notices.

**Cons:** Two places to update per amendment instead of zero, and a genuine
drift risk between the table and the body prose it summarises. It also adds a
seventh section to a six-section structure the toolkit owns, so this repository
carries a local extension until the toolkit accepts one.

### Option 4: Semantic versioning per ADR

Give each ADR its own `**Version:** 1.2.0`, with the same major/minor/patch
discipline the register uses for `meta.register_contract`.

**Pros:** Distinguishes a substantive reversal from a typo fix, which Option 3's
flat counter does not.

**Cons:** The distinction is exactly the judgement call that goes wrong under
deadline, and a wrong answer is silent. The register earns semver because a
consumer reads the contract number and changes behaviour on it; nothing reads an
ADR mechanically, so the extra precision buys a reader nothing and costs an
argument per amendment. A flat count of "how many times has this been revised"
is the question people actually ask.

## Decision

We will record every amendment as a numbered revision: a `**Revision:** N`
header field on every ADR, and a `## Revision History` table on every ADR where
`N > 1`, carrying one row per revision with its date, a one-line summary of what
changed, and who ratified it.

Option 3 is chosen because it is the only one that answers all three questions,
and because the count and the table check each other. Option 1 is right that git
is the authoritative history and wrong that the history is the artefact —
the artefact is a reader's confidence in an open file, and git does not reach
there. Option 2 solves detection and leaves ratification unrecorded, which is
the half this repository has least excuse for omitting. Option 4 prices a
judgement call this corpus has no consumer for.

### The header field is on every ADR, including unamended ones

`**Revision:** 1` on a never-amended ADR is a positive assertion, not padding.
An absent field is ambiguous between "never amended" and "amended by someone who
did not know the convention", and this repository has already been bitten by
reading an absence as an answer — GitHub omitting `security_and_analysis` is
[ADR 0021](0021-how-remote-verification-authenticates.md)'s whole subject. It
also makes the corpus greppable in one direction: `grep -L '\*\*Revision:\*\* 1'`
lists exactly the amended ADRs.

### The history table appears only where there is history

An 18-row corpus of one-row tables each reading "1 — original decision" is a
second copy of the `**Date:**` and `**Status:**` fields, restating them in a
form that can drift from them. Where `N = 1` the header already says everything
the table would.

### Revision is orthogonal to status, and does not enter the enum

`**Status:**` answers where an ADR sits in its lifecycle; `**Revision:**`
answers how many times its content has been ratified. An `Amended` status value
would conflate them, break the toolkit's five-value enum, and force the question
"is an amended-then-superseded ADR `Amended` or `Superseded`" — which has an
obvious answer only because the two axes are independent. An ADR at
`**Status:** Superseded` with `**Revision:** 3` is well-formed and means
something precise.

### What "ratified by" means here, and what it must mean for an adopter

On this repository the author and the approver are the same person, and
pretending otherwise would be theatre. The column records who ratified the
revision — for now, the repository owner — and its value is that it is
**recorded**, so that an adopter whose approver is not their author inherits a
field with somewhere to put them. This is the same posture difference ADR 0022
§ 6 draws: the arrangement is this repository's, the requirement is the
standard's.

### Enforced by a test, not by a register control

`tests/test_adr_revisions.py` checks the form. This is deliberately the same
mechanism as `tests/test_provenance_stamps.py`, which holds the stamp format
without a control of its own, and for the same reason: the rule governs a
document this repository authors about its own decisions, not a property of a
conformant Equal Experts repository. Making it a control would put an
authoring convention into `controls.yaml`, where every adopter would inherit
it — the move ADR 0022 requirement 6 rules out. TST-001 is already blocking, so
the test is a merge gate without a new control, a new tier or a contract bump.

A convention with nothing checking it is theme **T-1**, and this ADR would
otherwise be an instance of the failure it describes.

## Consequences

**Positive outcomes:**

- "Which ADRs have been amended, and what changed" becomes one command over the
  corpus, where today it requires reading seven files to the middle.
- An amendment acquires a ratifier. An in-place edit to an Accepted decision is
  no longer indistinguishable from a typo fix, which is the property that makes
  amend-in-place defensible against ADR 0024's rejected supersede-instead route.
- The revision count and the table check each other, so the common failure —
  editing the body and forgetting the record — fails the build rather than
  surviving until an audit.
- A future amendment lands in a structure that exists, rather than being
  improvised by whoever is holding the pen, which is how the seven current
  amendments came to use four different spellings.

**Trade-offs and risks:**

- Two places to update per amendment, and the summary can drift from the body it
  summarises. The test checks that a revision claiming an amendment has one in
  the body; it cannot check that the one-line summary is **accurate**, and a
  wrong summary is worse than none because it is trusted. This is the residual
  risk and it is not engineered away.
- A seventh section is a local extension to a structure `adr-toolkit` owns.
  `/adr-check` and `/adr-consistency` will not check these fields and will not
  object to them, so the convention is enforced here and nowhere else until the
  toolkit accepts an amend — the same position `lint-md` was in at
  [#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530).
- Backfilling the seven amended ADRs means writing summaries of changes made
  before the convention existed, reconstructed from their body prose and from
  git. They are honest to the best of the record; they were not written at the
  time, and the table marks them as backfilled rather than implying otherwise.
- Recording the repository owner as ratifier of their own amendment is a weak
  approval signal. It is the true one, and the field's worth is that an adopter
  with real separation has a place to record it.

## Related ADRs

- [ADR 0024: Keep Only Direction Values in the Variance Vocabulary](0024-variance-vocabulary-is-direction-only.md)
  — settled that an Accepted ADR is amended in place rather than superseded;
  this ADR makes that amendment visible.
- [ADR 0021: How Remote Verification Authenticates](0021-how-remote-verification-authenticates.md)
  — the principle that an absent field must not be read as an answer, which is
  why `**Revision:** 1` is stated rather than implied.
- [ADR 0022: What Must Be True Before CI Carries a Platform Token](0022-a-platform-token-ci-carries.md)
  — requirement 6, the rule that this repository's own arrangements must not
  reach an adopter through the register or the plugins.
- [ADR 0016: Give "Could Not Verify" Its Own Exit Code](0016-exit-codes-for-unverifiable-controls.md)
  — the amendment that went unwritten for six days, and the case this ADR is
  built from.

## References

- [`adr-toolkit@0.1.11`](https://github.com/EqualExperts/ee-skills-incubator)
  — `adr-structure-rules.md` and `adr-status/adr-lifecycle-rules.md`, which
  between them define the six sections and five status values this extends.
- [`00-concepts.md`](../00-concepts.md) § The provenance stamp — the other
  format convention in this repository held by a test rather than a control.
- [Michael Nygard, *Documenting Architecture Decisions*](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
  — the original ADR pattern, which treats a decision record as immutable once
  accepted and is the assumption this ADR departs from.
