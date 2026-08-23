# Phase 3 review — the remote locus

The evidence for Phase 3's criteria, so that
[`04-build-plan.md`](04-build-plan.md) can stay a list of outstanding work.
A criterion there is one checkable sentence; the reasoning for a tick is here.

**Scope of this record.** One slice so far.

The first implements `kind: remote` itself — the transport, the two asserts the
register declares, and the taxonomy that decides what a non-answer is worth. It
is recorded in § The first slice below. It ticks exactly one criterion, and the
list of what it deliberately did **not** touch is in § What this slice left
open, because three of the remaining criteria depend on this one and would have
been guesses before it.

## The first slice — `kind: remote` becomes a verdict

### What was there before

`run_block` returned `SKIPPED (no credentials)` for every `kind: remote` block,
unconditionally, whatever the environment held. The two assert names were in the
schema's closed set from Phase 1 — so a typo was a schema error rather than a
check that silently never ran — but nothing stood behind them.

That was the right stub. [ADR 0014](adr/0014-satisfying-remote-locus-controls.md)
had already named the cost precisely: *"the repo passes every control the
checker can verify locally precisely because the two it cannot verify are the
two it would fail"*. The gap was an audit gap, not a protection gap — CI-001 and
SEC-001 both held **in fact** from 2026-08-17 — but a checker that cannot see
the controls a repository would fail is not evidence of much.

### The four decisions, and where they are recorded

Implementing this puts rules into `src/standard_check/`, which
[ADR 0018](adr/0018-register-checker-boundary.md) does not allow to happen
unreasoned. The reasoning is
[ADR 0021](adr/0021-how-remote-verification-authenticates.md), and it settles:

| Decision | What was chosen | The alternative it beat |
| --- | --- | --- |
| Transport | `urllib` + a bearer token | Shelling out to `gh`, which makes a binary a dependency of Tier-1 verification |
| Repository identity | The `origin` remote, with `--github-repo` to override | Configuration, which is a second copy of what git already records |
| Failure taxonomy | Absent token is a skip; a *rejected* token is `UNCLASSIFIED` | Collapsing both into "no credentials", which tells an operator to supply a token they already supplied |
| Where the reasoning lives | A new ADR | Extending ADR 0018, which would cover two eras in one file |

### The endpoint choice is the substance of the control

CI-001's remote block reads
`GET /repos/{owner}/{repo}/rules/branches/{branch}` — the rules **in effect** on
a branch — rather than `GET /repos/{owner}/{repo}/rulesets`, the list of
rulesets that exist.

This is not a convenience. Three of the ways a recorded ruleset can protect
nothing are answered by that endpoint *for free*, because a rule only appears in
its response when all three already hold:

1. A ruleset in `evaluate` or `disabled` mode contributes nothing to it.
2. A ruleset whose `conditions` do not match the branch contributes nothing.
3. A payload GitHub rejected with a 422 was never applied, so it contributes
   nothing.

The third is the defect register contract 19 closed on the file side, where
`gate-repo`'s payload omitted the `parameters` the API requires on two rules and
every apply call 422'd. Reading the effective rules means the remote block would
have caught that from the other direction: the file said the branch was
protected, and GitHub would have reported no rules at all.

**A rule appearing in that response is a rule being enforced**, which is the
whole of what this block was written to establish.

### One reading, two readers

CI-001 now asks the same question twice — of the artefact the repository
records, and of the platform. The register already guarded against those two
blocks carrying different `args:`
(`tests/test_gate_repo_deploy.py`, since contract 17). Nothing guarded against
the *checker* holding two different readings of the same args, which is theme
**T-2** arriving one layer down: the file half could go on passing while the
remote half read the same rules differently, and no test compares two copies of
a rule to each other.

So the reading moved to `src/standard_check/rulesets.py` and both asserts call
it. `test_there_is_no_second_copy_of_the_rule_vocabulary` holds them to it by
identity, and `test_the_recorded_ruleset_and_the_platform_are_judged_by_one_function`
takes this repository's own recorded `rules:` array, hands it to the **remote**
assert exactly as the platform would report it, and requires the same verdict.

What is deliberately *not* shared: the recorded artefact is additionally checked
for `enforcement`, for `conditions` naming a branch by name, for a payload the
API would reject, and for a required check no gating workflow produces. None of
those apply to a platform response — the platform answers the first three by
responding at all, and the fourth is a fact about workflow files that the file
block already owns. Running it twice would make the remote block fail for file
reasons, which muddies what "the platform says" means.

### The refusal that matters most

`security_and_analysis` is **omitted** from GitHub's answer for a caller without
repository administration access. It is not returned as `disabled`; the object
is not there.

Reading that absence as "push protection is off" would report a violation on a
repository where the control holds, manufactured entirely by not having looked —
the exact substitution `ruleset_recorded_matches_register` refuses in the other
direction when it declines to let a recorded ruleset stand in for an enforced
one. So the assert raises rather than returning `False`, and the block reports
`UNCLASSIFIED`.

The mirror of that rule is stated in the same place, because it is just as easy
to get wrong: an effective-rules response of `[]` **is** an answer. The platform
said nothing is in force on the branch. That is a `FAIL`, and reporting it as
unverified would be the same error pointing the other way.

### Evidence — remote verification passes against a real repository

Run in this container against `Eaiger-Ent/ee-standard`, with a token in the
environment:

```text
$ uv run standard-check run --control SEC-001 --control CI-001
ee-standard conformance report — register v0.19.0 (contract 19)

Tier 1
  CI-001   PASS   The default branch cannot be written to without a passing check
  SEC-001  PASS   A commit containing a secret cannot reach the remote

Summary: 2 passed, 0 failed, 0 skipped (predicate), 0 skipped (no credentials),
0 unclassified
exit 0
```

These are the first `0` exits either control has produced. Both were `SKIPPED
(no credentials)` in every run since the register was written.

The four refusals, each exercised against the live API rather than a fixture:

| Invocation | Verdict | Message |
| --- | --- | --- |
| `env -u GITHUB_TOKEN -u GH_TOKEN …` | `SKIPPED (no credentials)` | *no GitHub token in the environment* — exit `3` |
| `GITHUB_TOKEN=ghp_notreal…` | `UNCLASSIFIED` | *the token was rejected … (401) — this is a token to fix rather than one to supply* |
| `--github-repo Eaiger-Ent/no-such-repo-xyz` | `UNCLASSIFIED` | *not visible to this token (404) … neither says anything about the control* |
| `--github-repo "not a slug"` | `UNCLASSIFIED` | *is not a GitHub owner/name — a malformed target would send this repository's question to some other URL* |

### One thing the tests were getting for free, and should not have been

Adding remote verification exposed a hidden input in the suite itself. Both this
devcontainer and GitHub Actions set `GITHUB_TOKEN`, so the moment remote blocks
became real, four existing tests changed verdict depending on **who was logged
in** — reporting `SKIPPED (no credentials)` on a laptop and reaching the network
in CI.

`tests/conftest.py` now strips both token variables from the environment for
every test, autouse. A test that wants credentials passes them explicitly. A
suite whose results depend on ambient authentication is precisely the kind of
unstated input the checker exists to refuse, so it should not be one the checker
relies on.

## What this slice left open

Three of Phase 3's remaining criteria depend on this one and are deliberately
untouched. Recording them here rather than attempting them keeps the plan a list
of outstanding work rather than a list of half-finished ones.

**GOV-001's remote half.** Its `partial:` block, narrowed at contract 19, names
exactly what is left: *whether GitHub enforces the recorded ruleset*. That is
now answerable — this slice built the thing that answers it — but GOV-001 reads
`kind: command` blocks and deciding how a meta-control consumes a remote verdict
is its own piece of work, not a rider on this one.

**The `--require-complete` flip**, and with it the workflow half of the
no-credentials criterion. [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md)
§ Ratified tolerance defers the flip to this phase because *the tolerance exists
only because remote verification does not*. It cannot be flipped yet, and the
reason is recorded in ADR 0021 § Trade-offs: **the default Actions `GITHUB_TOKEN`
cannot read `security_and_analysis`**, so SEC-001's remote block will report
`UNCLASSIFIED` in CI even though it passes here. Flipping `--require-complete`
before that is resolved would turn every CI run red for a control that holds.
Resolving it means either granting the workflow a token that can see the setting
or recording why that block is not answerable from CI — a decision, not an
oversight. It is now written up as
[ADR 0022](adr/0022-a-platform-token-ci-carries.md), **Accepted** 2026-08-23, which
records four options, the requirements the register would need before any token
is introduced, the threat model that makes this repository's own posture simpler
than an adopter's, and one finding that stands whatever is decided: **SEC-002 cannot
see a platform token**, because `no-static-cloud-keys` reads
`cloud_credentials:` and every name in it is a cloud provider key. A secret
called `GH_ADMIN_TOKEN` would leave SEC-002 reporting `PASS` over a standing
administrative credential.

**GOV-003 on `review_by`, and `gate-repo`'s per-mutation confirmation.** Neither
depends on this slice; both are simply not in it.

## Criteria this slice closes

| Criterion | State | Evidence |
| --- | --- | --- |
| Remote verification passes against a real repository | **Closed** | § Evidence above |
| Adopter-facing steps in `08-adopting.md` | Open | § 4.1 covers the credentials and the scopes; the *required status check* half is GOV-001's, and the criterion covers the whole phase |
| No-credentials reporting | Half | The reporting half is closed and tested; the workflow half waits on the flip above |
