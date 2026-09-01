# ADR 0047: A Plan Limit Is Recorded, Not Tolerated

**Status:** Accepted
**Date:** 2026-08-31
**Revision:** 2

## Background

Two of CI-001's and SEC-001's requirements are things GitHub sells rather than
things a repository configures. Repository rulesets on a **private** repository
are, in GitHub's own words, *"for customers on GitHub Team and GitHub Enterprise
plans"*; secret-scanning push protection on a private repository likewise needs
a paid tier.

A repository that is private on a plan without them cannot satisfy either
control. This ADR was written believing the checker's verdict in that state is
not *unverifiable* but **FAIL**. Half of that was wrong, and revision 2 records
the measurement that corrects it:

| Control | Block | Today | Why |
| --- | --- | --- | --- |
| CI-001 | `default_branch_ruleset_satisfies` | **UNCLASSIFIED** (see revision 2) | This ADR was written believing the effective-rules endpoint returns `[]` — a *list*, therefore an answer, therefore a failure. A live Free private repository **refuses the read with 403**, which is `Unreadable`. The correction, and what follows from it, is § Measured 2026-09-01 |
| SEC-001 | `github_push_protection_enabled` | **FAIL** | A reported status of `disabled` fails. Only an *absent* `security_and_analysis` is `Unreadable`, and that is the token-cannot-see case rather than the plan-does-not-offer case |

Either way the run cannot be green — `1` on the failure this assumed, `3` on the
refusal it actually meets — and either way a repository in that state is
indistinguishable, in the report, from one that could have protected its default
branch and did not. That is the problem this ADR addresses, and it survives the
correction intact.

**The cost is not the two controls.** It is the other thirteen. A conformance
run that can never be green is one people stop reading, and the standard's own
sweep design already names that failure — *"a red scheduled workflow is a
notification people learn to dismiss"*. A permanently-failing gate degrades every
control that does hold, which is a worse outcome than the two that do not.

Thirteen do hold, and they are not the trivial ones: the secret scanner at every
local locus, frozen lockfile installs, SHA-pinned actions, published-digest
reconciliation, lint, types, tests, the digest-pinned devcontainer, and
automated dependency proposals.

## Decision

**A repository records a platform limitation, and the checker reports it as
`UNAVAILABLE (plan)` rather than failing the control.** The record lives in
`deployment-decisions.yaml` under a new `platform_limits:` key, beside
`declined:`, because both are the same kind of fact: a dated statement of
something this repository does not have, read by `register-check`, going stale on
its own terms.

```yaml
platform_limits:
  - control: CI-001
    assert: default_branch_ruleset_satisfies
    plan: github-free-private
    lacks: repository rulesets are GitHub Team and Enterprise only
    review_by: 2026-11-30
```

Six rules make it a record rather than an opt-out, and every one is load-bearing.

**1. It downgrades to `UNAVAILABLE (plan)`, never to `PASS`.** The control does
not hold, and no arrangement of files makes it hold. A run carrying one exits
`3` at best. Nothing here is a claim that a branch is protected.

**2. It names a `kind: remote` block, never a control and never a file block.**
A file block asks what the repository contains, and a plan cannot stop a
repository containing a thing. CI-001's `ruleset_recorded_matches_register` must
still pass: the adopter still records the ruleset they would enforce, so the day
the plan changes it is one API call rather than a fresh decision.

**3. It expires**, and an expired entry **fails** the run rather than reverting
to reporting the limitation. A plan is a commercial state that changes on a
renewal date, and an entry with no expiry is a permanent exemption wearing a
record's clothes. This is GOV-003's rule and `deployment-decisions.yaml`'s,
applied to a third kind of staleness.

**4. `--require-complete` still promotes it to `1`.** The flag means *fail if
anything could not be verified*, and this is the case it was written for. A
repository in this state does not turn the flag on, and that is the visible cost
rather than a hole in it. The narrow exception already in the conformance
workflow — a fork pull request tolerating `3` and only `3` — is the shape a
repository may copy if it decides to, with the same requirement that a test
exercise both branches.

**5. Every run prints it.** Not a footnote in a summary line: the control's row
says `UNAVAILABLE (plan)`, the entry's `lacks` text is printed under it, and the
`review_by` date is shown. A limitation nobody sees is an exemption.

**6. The register never carries one.** `platform_limits:` is posture — a fact
about one repository's billing — and ADR 0022 requirement 6 forbids posture in
`controls.yaml` or anything under `plugins/`. `tests/test_posture.py` should
grow this case.

## What this cannot verify, stated rather than implied

**The checker cannot confirm that the limitation is real.** A `403` carrying
*"Upgrade to GitHub Pro or make this repository public"* is evidence; an empty
effective-rules list is not, because that is also what a Team repository with no
ruleset configured looks like. So an entry claiming a plan limit that does not
exist would be accepted.

That is the honest boundary and it must not be papered over. What stands against
misuse is that the entry is **written down, dated, printed on every run, and
fails when it expires** — social rather than mechanical. Where this standard can
usually say *the checker refuses it by construction*, here it can only say *the
report will not let you forget*.

It follows that this mechanism is the weakest thing in the register, and its
narrowness is what keeps it safe: one block at a time, remote only, expiring,
never a pass.

## Alternatives considered

**A `baseline` entry.** Rejected. Baselines are shrink-only lists of tolerated
violations, and every Tier-1 control carries `baseline: null` *by design* — the
register's own phrase is *"birth conditions, true from the first commit, never
baselined"*. Opening that is the general opt-out this whole design refuses, and
it would apply to file blocks too.

**Re-tier the control, or lower its rung.** Rejected, and it is already refused
in as many words by `08-adopting.md`: *"do not re-tier a control to make a report
green."* It would also change the standard for every adopter to accommodate one
adopter's invoice.

**A predicate — `applies_to: [rulesets-available]`.** Rejected on two counts.
Predicates are evaluated against files and never self-declared, and a billing
tier is not a file. And a predicate makes a control **SKIP**, which is invisible:
the report would stop mentioning branch protection at all, which is the opposite
of what a repository running without it needs to see.

**Do nothing and let them run red.** Rejected as the worst option available. It
does not make the branch any safer, and it costs the thirteen controls that hold
their audience.

**Tell them to make the repository public.** Not a decision this standard gets to
take on somebody's behalf, and for most customers not a decision at all.

## Consequences

A private repository on a plan without rulesets can adopt this standard, get
thirteen of fifteen controls genuinely enforced, and see the remaining two named
in every report with a date attached — rather than choosing between a red build
and no standard at all.

**The risks that record stands for are real and should be written beside it.**
On such a repository the default branch is advisory: anyone with write access can
push to it directly, no review or passing check is required, and history can be
rewritten. The secret scanner still runs at pre-commit, pre-push and CI, but all
three are on the contributor's side of the boundary — `--no-verify` skips the
first two, a fresh clone has neither until `pre-commit install` runs, and CI
catches a secret only *after* it has reached the remote, by which point it is
disclosed and must be rotated. Push protection is the only stop that is not.

`docs/08-adopting.md` gains that paragraph, because a mechanism that makes a gap
comfortable without stating what is in the gap is worse than no mechanism.

**One question is open and it changes this ADR's scope.** GitHub Pro offers
classic branch protection on private repositories while rulesets remain Team and
above. Whether the effective-rules endpoint CI-001 reads also reports rules
originating from *classic* branch protection is **untested** — this repository is
public and ruleset-protected, so it cannot answer it. If it does, GitHub Pro
satisfies CI-001 and this mechanism is needed only on Free; if it does not, the
checker has a gap that should be closed on its own merits rather than waived
here. Test it on any Pro private repository before implementing this.

**Accepted 2026-08-31.** It was Proposed for two reasons and only one of them
is discharged: it is the first mechanism in the register that lets a Tier-1
control not hold, and it has now had its second reader.

**The open question is not discharged, and one guard follows from it.** A
`platform_limits:` entry may only name a capability the plan genuinely does not
offer — never one it offers by a route the checker fails to read. If the
effective-rules endpoint turns out not to report rules originating from classic
branch protection, a Pro private repository failing CI-001 is a **checker
defect** to fix, and waiving it here would hide the defect behind a record that
looks deliberate. Test the endpoint before writing an entry for any repository
that has classic branch protection configured.

That distinction is the difference between this mechanism and an opt-out, and it
is the one thing a reviewer of an entry should check first: *is the platform
refusing, or is the checker not looking?*

## Measured 2026-08-31 — the open question narrows

The endpoint's own refusal names a different tier from the documentation:

```text
% gh api repos/{owner}/{repo}/rulesets
{"message": "Upgrade to GitHub Pro or make this repository public to enable
 this feature.", "status": "403"}
```

GitHub's ruleset documentation says rulesets are *"for customers on GitHub Team
and GitHub Enterprise plans"*; the API says **Pro**. Taking the API as the
authority on its own behaviour, the tier at which this mechanism is needed is
**Free**, not everything below Team, and the population it serves is smaller than
this ADR assumed when it was written.

That does not change the decision — a repository on Free still cannot buy the
control, and still should not run permanently red — but it changes who should be
told about it, and it makes the § What this cannot verify guard sharper rather
than softer: an entry recorded by a **Pro** repository would very likely be
waiving a capability the plan does offer.

It also does not settle the other half. Whether the effective-rules endpoint
reports rules originating from *classic* branch protection is still untested, and
still decides whether a Pro repository that uses classic protection instead of a
ruleset passes CI-001 honestly or fails it through a checker gap.

## Measured 2026-09-01 — the premise was wrong, and it made the mechanism inert

The first adopter to run this on a Free private repository produced the answer
the § Measured 2026-08-31 section could not:

```text
? remote: default_branch_ruleset_satisfies — /repos/<owner>/<repo>/rules/branches/main
  answered 403 — "Upgrade to GitHub Pro or make this repository public to enable
  this feature."
```

**The effective-rules endpoint refuses, it does not answer `[]`.** So the block
raises `Unreadable`, `_run_remote_block` returns `UNCLASSIFIED`, and
`_waived_or_failed` — the only function that reads a recorded limit — is never
reached. An adopter could write a correct `platform_limits:` entry and go on
reading `UNCLASSIFIED` for ever, with nothing in the report acknowledging that
they had recorded anything at all.

The mechanism was inert for the exact case it was built for, and for the six
weeks between Accepted and this measurement nobody could have known: this
repository is public, and `tests/test_platform_limits.py` proved rule 1 by
calling `_waived_or_failed` directly, with a comment explaining that a live run
would have needed somebody else's misconfigured repository. Constructing the
input a mechanism expects cannot discover that reality supplies a different one.

**The decision is unchanged** — recorded, dated, printed, expiring, never a pass
— so this is an amendment rather than a superseding ADR
([ADR 0025](0025-an-amendment-is-a-recorded-revision.md)). What changes is which
outcome a record covers.

**A recorded limit now also covers a `403` on the block it names.** Three
constraints keep it the same narrow thing rule 1 described:

* **Only `403`.** A `401`, a `404`, a timeout, a name that will not resolve and
  a body that is not JSON stay `UNCLASSIFIED`. A dated billing record must never
  absorb an expired token or a bad afternoon's network — that would be the
  checker reporting a commercial fact it has not established, which is precisely
  the misuse § What this cannot verify describes. `403` earns the exception
  because GitHub's own body says *"Upgrade to GitHub Pro"*, which that section
  already names as the evidence an operator records.
* **An expired entry reports `UNCLASSIFIED`, not `FAIL`.** Rule 3 says an
  expired record stops covering, and it does. But this path never received an
  answer, and failing a control on the strength of not having looked is what
  [ADR 0021](0021-how-remote-verification-authenticates.md) forbids everywhere
  else. Not covering means reverting to what the run actually knows. Both
  outcomes exit non-zero and `--require-complete` promotes both to `1`, so rule
  4 is untouched.
* **SEC-001's block is not covered, and this is not an oversight.** A Free
  private repository answers `github_push_protection_enabled` with a `200` whose
  `security_and_analysis` is simply absent — the same shape an under-permissioned
  token gets on a paid repository. There is no `403` to key on and nothing else
  distinguishes the two, so covering it would mean guessing. It stays
  `UNCLASSIFIED`, and an adopter on Free sees one block covered and one not.

**And the checker was lying about the cause.** `_http_explanation` reported every
`403` as *"the token lacks the scope … needs a token with repository
administration read access"*, discarding GitHub's body. The adopter who found
this spent a cycle on a token that was already correct, and so did the assistant
helping them. The 403 explanation now quotes GitHub and names both causes. That
is a plain defect fixed rather than a decision, but it belongs in this record:
the evidence this ADR asks an operator to act on was being thrown away before
they could read it.

### The refusal names the permission it wanted, and it is not administration

The same request, with headers:

```text
% gh api "repos/{owner}/{repo}/rules/branches/main" -i
HTTP/2.0 403 Forbidden
X-Accepted-GitHub-Permissions: metadata=read
{"message": "Upgrade to GitHub Pro or make this repository public to enable
 this feature.", "status": "403"}
```

**`metadata=read` is a permission every token holds** — GitHub says it cannot be
turned off. So this `403` is provably not a scope problem, and the disproof was
in a header on the very response `_http_explanation` was reading when it
announced *"reading this repository's protection state needs a token with
repository administration read access"*. That claim was wrong twice: wrong that
the cause was scope, and wrong about which permission, for an endpoint that had
just said.

This is the same header `08-adopting.md` § 1 derives the whole permissions table
from — *"established by measurement rather than by reading prose"* — applied to a
refusal rather than to a success. The checker now quotes it: given the accepted
permission, an operator knows what their own token holds and can settle the
question without the checker speculating about their billing.

**Half the open question is closed.** On GitHub Free, a private repository's
effective-rules endpoint refuses on the **plan**, with no scope confusion
available to hide behind, which is what a `platform_limits:` entry may record.
The other half stands: whether that endpoint, once it answers, reports rules
originating from *classic* branch protection still decides whether a **Pro**
private repository passes CI-001 honestly or fails through a checker gap. Only a
Pro private repository can answer it, and this one is not.

## Applied — pass 2

Implemented 2026-09-01. `Unreadable` carries the HTTP `status` where there was
one; `runner._unreadable_or_unavailable` is the new counterpart to
`_waived_or_failed`, holding the three constraints above.

`tests/test_platform_limits.py` gains a section that runs through `run_block` —
the entry point a real conformance run uses — rather than calling the waiver
directly, because the bypass is what hid this for six weeks. Each guard was
mutation-tested: reverting the widening kills two tests, covering any status
kills three, and letting an expired record keep covering kills one.

## Applied — pass 1

Implemented 2026-08-31. `src/register_check/platform_limits.py` reads
`platform_limits:` from `deployment-decisions.yaml`; `runner.py` gains
`Verdict.UNAVAILABLE_PLAN`, placed between `SKIPPED (no credentials)` and
`UNCLASSIFIED` in severity, and `_waived_or_failed` is the one function that
turns a failing remote block into a waiver.

Each of the four mechanical rules is held by a test in
`tests/test_platform_limits.py`: it never passes, it matches on the
control-and-assert pair so a control's other blocks are untouched, an expired
entry fails with the date in the message, and `--require-complete` promotes it
to `1`. `tests/test_posture.py` holds rule 6 — the string may not appear in
`controls.yaml` or under `plugins/`.

Two things are deliberately not implemented, both because they would be false
comfort. The checker still cannot confirm a claimed limit is real, and nothing
here tries to; and no entry exists in this repository, which
`test_this_repository_records_none` holds, because this repository is public and
ruleset-protected and an entry would be exactly the misuse § What this cannot
verify describes.

The `08-adopting.md` and `START-HERE.md` prose describing the risks a constrained
repository takes landed before this, on the branch that proposed the ADR, and
says the mechanism is unbuilt. That wording is now stale and is corrected in the
same change as this note.

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-31 | Original decision: a repository records a platform limitation in `deployment-decisions.yaml` and the checker reports `UNAVAILABLE (plan)` rather than failing, under six rules. | Nathan Carney |
| 2 | 2026-09-01 | Premise corrected against a live Free private repository; the refusal's `x-accepted-github-permissions: metadata=read` proves the cause is the plan, not scope: the effective-rules endpoint answers `403`, not `[]`, so the recorded limit was never reached and the mechanism was inert. A record now also covers a `403` on the block it names — only `403`, expiring to `UNCLASSIFIED` rather than `FAIL`, and not SEC-001's absent-field case. The decision itself is unchanged. | Nathan Carney |
