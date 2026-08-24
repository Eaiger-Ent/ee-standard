# Phase 3 review — the remote locus

The evidence for Phase 3's criteria, so that
[`04-build-plan.md`](04-build-plan.md) can stay a list of outstanding work.
A criterion there is one checkable sentence; the reasoning for a tick is here.

**Scope of this record.** Five slices so far.

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

## The second slice — GOV-003 was already closed

### What this slice built

Nothing. It is a verification slice: the criterion *"GOV-003 fails on a control
past `review_by`"* was satisfied by `src/standard_check/meta.py` when the
checker was first built (`1e21364`, 2026-08-16), and the box had stayed
unticked because nobody had gone and looked. Recording that is cheaper than
re-deriving it a third time, and leaving it unticked would misreport what
Phase 3 has left.

The box sits in Phase 3 for the same reason GOV-002's does: the meta-control
set is listed together so the phase's coverage of it is legible. Neither reads
platform state, so neither ever depended on the remote locus.

### What GOV-003 actually checks, and why it is one check

`gov_003` compares two expiries against today, and returns a single verdict
over both: a control past its `review_by`, and a verify block whose `partial:`
declaration has expired. [ADR 0017](adr/0017-partial-verification-is-reported.md)
gives a partial declaration an expiry precisely so that *partial* cannot become
permanent, so the two are the same mechanism — an expiry that turns silence
into a build failure — and splitting them would have been two names for one
rule.

### Evidence

Against the register as it stands, both halves hold:

```console
$ uv run standard-check meta GOV-003
GOV-003: PASS — no control is past its review date, and no partial declaration
expired
exit 0
```

The failing direction was exercised end to end rather than only in the suite,
by running the real register with one date moved back. First a control past its
review date:

```console
$ uv run standard-check --register past-review.yaml meta GOV-003
GOV-003: FAIL — past their review date: SEC-001 (review_by 2001-01-01)
exit 1
```

Then the other half, with GOV-001's `partial:` expiry moved instead — the case
ADR 0017 wrote the expiry for:

```console
$ uv run standard-check --register expired-partial.yaml meta GOV-003
GOV-003: FAIL — past their review date: GOV-001 (partial declaration expired
2001-01-01: whether GitHub enforces the recorded ruleset — …)
exit 1
```

Neither probe register was committed; each was the tracked `controls.yaml` with
a single ISO date rewritten. The suite covers the same two directions at
`tests/test_meta.py::test_gov_003_fails_past_review_date`,
`::test_gov_003_passes_before_review_date` and — for the partial half —
`::test_gov_003_fails_an_expired_partial_declaration`, all passing.

### What this slice does not close

It says nothing about whether the `review_by` dates in the register are
*right*. GOV-003 enforces that a date is not in the past; it cannot know
whether a control was actually reviewed on the day someone moved its date
forward. That is the same limit ADR 0022 § requirement 4 states about token
kind versus token scope, and it is a property of what an expiry can mean rather
than a gap to close.

### Criteria this slice closes

| Criterion | State | Evidence |
| --- | --- | --- |
| GOV-003 fails on a control past `review_by` | **Closed** | § Evidence above — both halves, end to end and in the suite |

## The third slice — the register can see a platform token

### What this slice built

SEC-003 and `platform_credentials:`, at register contract 22 — requirements 1
and 2 of [ADR 0022](adr/0022-a-platform-token-ci-carries.md), which that ADR's
§ The precondition puts before any token rather than beside one. It closes no
criterion. It removes the reason the `--require-complete` flip cannot be worked
on: the flip is blocked on a token CI does not have, and the token is blocked on
these two, so this is the only end of the chain that could move.

### Why the control could be added before the credential

The finding ADR 0022 recorded independently of its decision is that **SEC-002
cannot see a platform token**: `no-static-cloud-keys` reads `cloud_credentials:`
and every name in it is a cloud provider key, so a `GH_ADMIN_TOKEN` repository
secret would have left SEC-002 reporting PASS over a standing administrative
credential. SEC-002 was not wrong; it was asked a different question.

SEC-003 asks the register's, and the direction is the opposite of SEC-002's:

| | `cloud_credentials:` | `platform_credentials:` |
| --- | --- | --- |
| What the list holds | what is forbidden | what is permitted |
| A name the list has not heard of | passes | **fails** |
| The section omitted | falls back to a built-in set | permits nothing |
| An empty list | a control looking for nothing | rejected — omitting the key says it already |

That asymmetry is what made this slice possible before any credential exists.
An allow-list introduced into a repository with no standing secret costs
nothing and fails closed; a deny-list introduced the same way would have had to
guess the name of the thing it was looking for, which is the failure § H4
recorded against SEC-002 itself.

### The trigger half, and what it is for

An entry names `triggers` — the events a workflow may reference that credential
under. This is the field that makes ADR 0022's Option 3 checkable rather than a
convention: the exfiltration path that ADR corrected its own first draft over is
a branch **adding** `pull_request:` to a workflow in order to self-trigger a job
with the secret attached, and a guard written in YAML is a guard the pull
request is editing. The register is not.

`GITHUB_TOKEN` carries `triggers: any`, which is a statement and not a default —
GitHub creates it at the start of each job and expires it with the job, so the
event cannot change what it reaches. A standing credential will name its events
explicitly, and that is the whole point of the field.

### Evidence

```console
$ uv run standard-check schema
schema: OK — register v0.20.0 (contract 22), 14 controls, 3 meta-controls

$ uv run standard-check run --control SEC-003
  SEC-003  PASS   CI carries no platform credential the register does not name
exit 0
```

The full run is 13 passed, 1 skipped (predicate: IAC-001), 3/3 meta-controls —
GOV-001 included, which matters because SEC-003 is `rung: blocking` at the `ci`
locus and so has to be reachable from a step that can fail. It is, by the same
full-register step every other blocking control is reached from; nothing new was
wired.

Four ways to fail it are covered in `tests/test_asserts_command.py`: a secret
the register does not name, `secrets: inherit` (a reference to every secret at
once, which no allow-list can enumerate), a named credential under an event its
entry does not permit, and — the test that proves the assert holds no list of
its own — the register's `platform_credentials:` block deleted, after which this
repository's own workflows fail on `${{ github.token }}`.

That last spelling is why the assert reads more than `secrets.`: every workflow
here reaches the platform token as `${{ github.token }}`, so an assert matching
only the `secrets.` context would have reported PASS without looking at the one
reference there is.

### What this slice deliberately left open

Requirements 3 and 4 — a verified expiry read from the
`github-authentication-token-expiration` response header, and a classic token
refused by the presence of `X-OAuth-Scopes`. Both are `kind: remote` work, and
both land before a standing credential does, not after. `max_lifetime_hours` is
recorded in the register now and read by nothing, which is the honest state: it
is a promise until requirement 3 makes it a verdict.

Requirement 6 — a test that this repository's Option 1 posture cannot appear
under `plugins/` — is also open. Nothing breaks when it is skipped, which ADR
0022 says is exactly what makes it worth writing down.

### Criteria this slice closes

None. It is recorded because the flip's criterion names ADR 0022 as its blocker,
and two of that ADR's seven requirements are now closed rather than pending.

## The fourth slice — the expiry becomes a verdict, and answers nowhere yet

### What this slice built

SEC-003's `kind: remote` block, at register contract 23 — ADR 0022 requirement
3. `max_lifetime_hours` had been in the register since contract 22 and nothing
read it, which is the shape of a promise rather than a control.

`platform_token_expires_within` reads the
`github-authentication-token-expiration` header GitHub returns for the
credential the run is authenticated with, and fails one that outlives the
largest lifetime `platform_credentials:` permits.

### The finding: the Actions token does not report an expiry

This slice predicted nothing and observed one thing. ADR 0022 confirmed the
header live for a fine-grained PAT while it was being written; nobody had asked
what the **Actions** `GITHUB_TOKEN` returns. This pull request's own CI run is
the first time this repository asked:

```text
SEC-003  UNCLASSIFIED   CI carries no platform credential the register does not name
  ? remote: platform_token_expires_within — GitHub returned no
    github-authentication-token-expiration header for this token, and it is not
    the instrument whose silence means 'never expires' — what CI carries was not
    read, and nothing here claims it was
```

**The design decision this vindicates is the one that cost the most to argue
for.** Requirement 3 says, in as many words, that *a token with no expiry
fails*. Had the block been written to that letter, this CI run would be **red**
— for a credential that certainly expires, within the hour, and that no
adopter could do anything about. Separating "the instrument said it never
expires" from "the instrument does not report expiry at all" is what kept a
false violation out of a gate, and it is the same separation
`github_push_protection_enabled` makes about `security_and_analysis`.

### Is a block that answers nowhere a declared-but-unreachable control?

Theme T-3 is worth asking about here rather than waving away, because the block
is silent at both places this repository runs today: `UNCLASSIFIED` locally
because a developer's token is not the credential CI carries, and `UNCLASSIFIED`
in CI because the platform-minted token reports no expiry.

It is not T-3, and the reason is what the control is *for*. SEC-003 governs a
**standing** platform credential in CI — the one ADR 0022 decided this
repository would carry and has not yet introduced. A fine-grained PAT does
report its expiry, as the ADR observed and as this repository's own local token
demonstrates. So the block is silent for the credential that needs no policing
and live for the one that does, from the moment it exists. A control that
answers only when the thing it governs is present is a control that applies,
not one that is unreachable.

What would be T-3 is leaving it here without saying so, which is what this
section exists to prevent.

### What it costs, stated rather than hidden

A local `standard-check` run now exits `3` rather than `0` — 12 passed, 1
skipped (predicate), 1 unclassified. That is not a regression to repair: a
control the run cannot answer is one it must not claim.

**In CI the count of unclassified blocks goes from one to two.** SEC-001's
remote block was already `UNCLASSIFIED` there, because the Actions token cannot
read `security_and_analysis`; SEC-003's now joins it. The
`--require-complete` flip was blocked before this slice and is blocked by one
more thing after it, so the two resolutions belong together rather than
separately:

1. **The token ADR 0022 chose.** A fine-grained `Administration: read` token
   would answer SEC-001's block *and* report its own expiry, closing both at
   once. It is what requirements 3 and 4 were written to precede.
2. **Or a `partial:` declaration on SEC-003's remote block for the CI locus**,
   naming the platform-minted token as the case that cannot be answered and
   carrying an expiry. ADR 0017's machinery exists for exactly this, and it does
   not unblock the flip on its own — a partial denies a `0` exit by design,
   which ADR 0022 § Option 4 already refused for SEC-001.

The first is the route; the second is what to write down if the first is
deferred again.

### Evidence

| Property | How it was checked |
| --- | --- |
| A token expiring inside the maximum passes | `tests/test_remote.py::test_a_token_expiring_inside_the_registers_maximum_passes` |
| One outliving it fails | `::test_a_token_outliving_the_registers_maximum_fails` |
| The number is the register's, not the checker's | `::test_the_maximum_moves_with_the_register` — the same token, two registers, two verdicts |
| A classic token with no expiry set fails | `::test_a_classic_token_with_no_expiry_set_fails` |
| An absent header on another instrument is not a violation | `::test_an_absent_header_on_another_instrument_is_not_a_violation` |
| An unparseable expiry is not guessed at | `::test_an_expiry_that_cannot_be_placed_in_time_is_unreadable` |
| Outside Actions the block declines | `::test_outside_actions_the_block_declines_rather_than_answering` |
| A register naming no credential has no maximum | `::test_a_register_naming_no_platform_credential_has_no_maximum` |
| What CI actually answers | The CI run quoted above, not a prediction |

`GITHUB_ACTIONS` joined the token variables `tests/conftest.py` strips autouse.
A block that branches on it would otherwise take one path on a laptop and the
other in CI — the same hidden input the suite already refuses for credentials,
wearing a different name.

### Criteria this slice closes

None. It closes ADR 0022 requirement 3, and adds one observation the flip's
criterion has to account for.

## The fifth slice — the instrument is read, and answers

### What this slice built

SEC-003's second `kind: remote` block, at register contract 24 — ADR 0022
requirement 4. `platform_token_is_not_classic` fails on the **presence** of
`X-OAuth-Scopes`, the header GitHub returns for a classic personal access token
and for no other kind.

Presence rather than value, and the distinction is the whole check: a classic
token with **no scopes** returns the header empty, so a condition written
against the value would pass the one credential that reaches everything its
owner can reach. `tests/test_remote.py::test_a_scopeless_classic_token_is_refused_too`
is that case.

### Why two blocks where the ADR permitted one

ADR 0022 wrote that *"the same remote assert can fail a classic token
outright"*. That was a permission rather than a requirement, and the fourth
slice produced the reason not to take it: in CI the expiry question has **no**
answer, because the Actions token reports no expiry at all, while the instrument
question does. One assert holding both would have thrown the answer away with
the non-answer.

The split earns its keep immediately. This is the first `PASS` SEC-003's remote
half has produced anywhere:

```text
SEC-003  UNCLASSIFIED   CI carries no platform credential the register does not name
  ✓ remote: platform_token_is_not_classic — the token CI carries returned no
    x-oauth-scopes, so it is not a classic personal access token — it is
    fine-grained or platform-minted
```

The control is still `UNCLASSIFIED` overall, because the expiry block beside it
cannot answer — which is the honest report of a control that is half answered,
and precisely what a single merged assert would have hidden.

### What it reads, and what it does not

The **kind** of credential, never its scope. No API lets a fine-grained token
enumerate its own permissions, so *scoped to this repository,
`Administration: read` only* stays a human act recorded when the token is
issued. ADR 0022 § What the register must gain stated that limit before there
was any code to misread, and it is repeated here because the substitution —
reading requirement 4 as *the register verifies the token is minimal* — is the
one this repository keeps catching in other forms.

### Where ADR 0022 now stands

| Requirement | State |
| --- | --- |
| 1. A control that can see a platform token | Closed, contract 22 |
| 2. A register fact naming what may be carried | Closed, contract 22 |
| 3. Expiry verified rather than promised | Closed, contract 23 |
| 4. A classic token refused | **Closed, contract 24** |
| 5. The environment gate is itself platform state | Not applicable — Option 1 here |
| 6. The posture difference must not reach an adopter | **Open** |
| 7. The adopter-facing consequence | Partly — `08-adopting.md` § 3.1 carries SEC-003, the allow-list direction, the expiry block and the instrument check |

Requirement 6 is the last one that precedes the token, and ADR 0022 says it is
the one most likely to be skipped because nothing breaks when it is.

### Criteria this slice closes

None. Phase 3's open criteria are unchanged: the `--require-complete` flip and
its no-credentials half, GOV-001 against a non-required check, `gate-repo`'s
per-mutation confirmation, and the adopter criterion covering the whole phase.
