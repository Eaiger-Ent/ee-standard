# Register schema

Field-by-field specification for `controls.yaml`. Concepts behind these fields
are in [`00-concepts.md`](00-concepts.md).

The register is validated by `standard-check schema` on every commit. A malformed
register is a build failure, not a warning — everything downstream derives from
it, so an unparseable register means no control is enforced.

## Top level

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `version` | yes | semver string | The register's own version. Bump per [SemVer](https://semver.org/spec/v2.0.0.html). |
| `meta.owner` | yes | string | Team accountable for the register as a whole. |
| `meta.register_contract` | yes | integer | Bumped **only** when a change alters what gets deployed. Drives staleness detection. |
| `predicates` | yes | map | Stack predicates, evaluated against the repo. |
| `controls` | yes | list | The controls. |
| `meta_controls` | yes | list | Controls that check the register itself. |

### `meta.register_contract`

This integer is the noise control for the whole system. It is bumped when a
control's `rung`, `verify`, or `variance` changes — never for a typo fix, a
reworded `title`, or a new `also_see` link.

Downstream skills recommend redeployment when the installed contract is ahead of
the one stamped in the repo. Bumping it for cosmetic edits trains people to
ignore the recommendation, which costs more than the edit saved.

## Control fields

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `id` | yes | `AAA-NNN` | Stable forever. Never reused, never renumbered. |
| `title` | yes | string | What is true when the control passes. Written as an assertion, not an instruction. |
| `enforces` | yes | string | The mechanical statement of what is checked. |
| `standard` | yes | object | `name` + `url` of the external standard. |
| `also_see` | no | list | Further `name`/`url` pairs — tool docs, internal playbooks. |
| `tier` | yes | 1-3 | See § Tiering in concepts. |
| `rung` | yes | enum | `advisory` / `warn` / `blocking`. |
| `locus` | yes | list | `editor` / `pre-commit` / `ci` / `remote`. |
| `applies_to` | yes | list | Predicate names. Unsatisfied predicate → control is **skipped**, not failed. |
| `deployed_by` | no | string | The gate skill that writes this control's artefacts. |
| `verify` | yes | list | One or more verification blocks. See below. |
| `owner` | yes | string | Team accountable for *this* control. |
| `variance` | yes | enum | `forbidden` / `narrowing-only` / `justified` / `free`. |
| `baseline` | yes | path or `null` | Path to the baseline artefact, or `null` for no exemptions ever. |
| `review_by` | yes | ISO date | GOV-003 fails the build after this date. |
| `rationale_adr` | yes | path | The ADR recording why this control exists. |

### `id`

The identifier is the join key between the register, the provenance stamps in
deployed artefacts, the CI job names, and the ADRs. Renumbering breaks every one
of those links silently, so an ID is permanent even if the control is later
removed — a retired ID is simply never reissued.

### `title` versus `enforces`

`title` states the property in terms a reviewer can agree or disagree with:
*"A commit containing a secret cannot reach the remote."*

`enforces` states the mechanism: *"gitleaks runs as a pre-commit hook and as a
CI job, and push protection is enabled."*

Keeping them separate is what lets you notice that the mechanism no longer
achieves the property — the most common way a control becomes theatre.

### `standard`

Must be an external, citable definition with a resolving URL. "Because we said
so" is not a standard; if no external standard applies, that is a signal the
control is a local convention and belongs in a linter config rather than the
register.

Every URL in the register is verified to resolve before it is committed.

### `verify`

A list of blocks, each with a `kind`:

```yaml
verify:
  - kind: command          # exit code is the verdict
    run: gitleaks detect --no-banner --redact
  - kind: file             # a file exists and matches a shape
    assert: precommit_hook_present
    args: { id: gitleaks }
  - kind: remote           # platform API state
    assert: github_push_protection_enabled
```

All blocks must pass for the control to pass. The `assert` names are implemented
in the checker and are a closed set — an unknown assert name is a schema error,
not a skipped check, so a typo cannot silently disable a control.

`remote` verifications need credentials and network, so they are skipped with an
explicit `SKIPPED (no credentials)` verdict rather than passing by default. A
skipped remote check never counts as a pass.

### `variance`

| Value | Local config may | Requires |
| --- | --- | --- |
| `forbidden` | nothing | — |
| `narrowing-only` | add rules, tighten thresholds | — |
| `justified` | any change | reason, owner, expiry |
| `free` | anything | — |

Under `justified`, a weakening is recorded as a baseline entry and inherits the
may-only-shrink rule. Under `narrowing-only`, the checker classifies the delta's
direction and fails on any weakening.

Direction classification fails in three known cases, all of which the checker
reports as `UNCLASSIFIED` rather than guessing: a rule replaced by a differently
named rule covering overlapping ground; a threshold whose direction depends on
the metric's polarity; and a config expressed as executable code rather than
declarative data.

### `baseline`

`null` means no exemptions are possible — the control passes everywhere or fails.
A path means the file at that path lists tolerated existing violations, and
GOV-002 enforces that it only ever shrinks.

Setting `baseline` from `null` to a path is a weakening and requires the same
recorded decision as a rung demotion.

### `review_by`

The date after which GOV-003 fails. This is not a reminder — it is an expiry.
Reviewing a control means re-reading the linked standard, confirming the
mechanism still achieves the property, and either extending the date or changing
the control.

An expiring control forces a re-decision rather than letting silence stand in for
agreement.

## Meta-control fields

Meta-controls take `id`, `title`, `enforces`, `rationale`, and `verify`. They
carry no `tier`, `rung`, `locus`, or `baseline` — they are unconditionally
blocking wherever the checker runs, and they cannot be baselined.

## Adding a control

1. Write the ADR first (`docs/adr/`). If the rationale will not survive being
   written down, the control is not ready.
2. Add the entry with `rung: advisory` and a `review_by` no more than a year out.
3. Verify every URL resolves.
4. Implement the `verify` blocks in the checker. An entry whose asserts do not
   exist fails schema validation, so this cannot be deferred.
5. Land it. Observe. Promote to `blocking` as a separate, deliberate change with
   its own commit, so the promotion is reviewable on its own merits.

Do **not** bump `meta.register_contract` in step 2 — advisory additions deploy
nothing. Bump it in step 5.
