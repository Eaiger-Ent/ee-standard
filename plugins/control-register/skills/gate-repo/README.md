# gate-repo

Deploys CI-001 — *the default branch cannot be written to without a passing
check* — in whichever repository you point it at.

## What it writes

| Locus | Artefact | Contents |
| --- | --- | --- |
| — | `.github/rulesets/default-branch.json` | The ruleset the register requires, stamped for CI-001 |
| remote | the GitHub platform | The same ruleset, applied through the API after an explicit confirmation |

One template lives in `templates/` and carries the placeholders the skill fills:
`default-branch.json`.

## This gate is different from the other five

Every other gate writes files that a human reviews before they take effect. This
one calls the GitHub API, and **the ruleset is in force the moment the call
returns** — for everyone with access, not only for whoever ran the skill.

So it confirms explicitly before acting, regardless of any plan already
approved, including one approved in `register-adopt`. That plan covers what will
be written to files; none of these calls is a file. The confirmation is asked on
every run, including a re-run that would change nothing: a call whose effect is
invisible until it is wrong is not one to make silently.

**Three calls, three confirmations.** Creating a ruleset, replacing an existing
one, and removing classic branch protection are separate questions with separate
words, because they have different blast radii and two of them can *reduce* what
protects the branch — a `PUT` replaces a ruleset entire, and a `DELETE` takes the
classic rule away. An answer to one is never an answer to another. `SKILL.md`
§ Every call that changes platform state lists them, and a call not in that list
is one this gate does not make.

## A recorded ruleset is not a protected branch

`.github/rulesets/default-branch.json` is a **record**, not an enforcement.
GitHub does not read a path in your repository to decide what a ruleset says;
only the API call does that.

This distinction is the whole reason the file exists, and the whole reason it is
not enough. CI-001's only locus is `remote`, which made this the one gate with
no file to write, no stamp to leave, and nothing observable until `kind: remote`
existed. A gate that cannot be watched working is the shape this project's
review record keeps re-opening criteria over.

So the ruleset is recorded before it is applied, and
`ruleset_recorded_matches_register` reads it back. That assert verifies
**intent** and says so in its own message. Whether GitHub enforces it stays with
the `remote` block, which answers when the run carries a token that can read the
ruleset and reports `SKIPPED (no credentials)` when it does not — and that skip
is never reported as a pass.

So the exit code says which halves were verified. With credentials, exit `0`:
the repository records the ruleset the register requires and the platform is
enforcing it. Without, exit `3`, and only the first half is claimed.

## Why it takes no opinions

Which requirements a protected branch must carry are CI-001's `args:`, and the
recorded file and the remote check read the **same** `args:`. Two blocks would
be two definitions of "protected", free to drift from each other.

One mapping is stated rather than inferred: `allow_force_push: false` becomes
GitHub's `non_fast_forward` rule, because the register says what is *allowed*
and GitHub names what is *blocked*. Reading one as the other is how a control
ends up inverted.

## Three things the checker rejects

**`enforcement: evaluate`.** GitHub accepts it, and it reports what would have
happened while blocking nothing — a control declared and unreachable.

**A ruleset targeting a branch by name.** `~DEFAULT_BRANCH` follows the default;
`main` stops protecting it the day the default moves, silently.

**A ruleset git does not track.** An untracked record is not one anybody can
review, and this control's remote block cannot be reached without credentials
either — so nothing at all would have been verified.

## What it cannot do

**Grant itself permission.** Writing a ruleset needs `administration: write`,
which a human with admin grants
(`08-adopting.md` § 1). The skill stops
*before writing the record* when the token lacks it, rather than leaving a
repository that looks protected in a diff and is unprotected in fact.

**Weaken a ruleset to make the call succeed.** A ruleset accepted because it
required less is a control silently downgraded, and CI-001 is
`variance: forbidden` with `baseline: null`.

**Remove classic branch protection in the same breath.** A classic rule and a
ruleset both apply and the union of their requirements is enforced, so removing
the old one is a real reduction until the ruleset is confirmed active. The skill
confirms first, then asks.

## Invocation

Invoked by `register-adopt`, which dispatches it through the Skill tool — do
not add `disable-model-invocation: true` here. A dispatched skill carrying that
flag cannot be reached at all, which is preflight P9 and is what stopped the
front door at Step 0 in Phase 4. The reasoning, and what guards the platform
mutations instead, is
ADR 0035.
