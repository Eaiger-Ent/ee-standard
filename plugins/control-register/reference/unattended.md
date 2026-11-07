# Running without being asked the same question again

One home for this rule rather than a copy in each skill (ADR 0036, in the
standard's own repository).

Shared by the skills a person re-runs: `register-adopt` and `register-install`.

## `--yes` pre-answers the proceed question, and what the plan listed

An adoption is not one command. It is re-run — after a failure, after a token
arrives, after a control is added — and each re-run asks the same two questions
and gets the same two answers. A confirmation that is always answered the same
way is not consent; it is a keystroke, and it trains the reader to press it
without reading, which is the state the *other* questions here exist to avoid.

**`--yes` means: I have read the plan, proceed.** It pre-answers the plan
question, and with it every takeover, removal and choice the plan listed. It
never answers a plan that lists a platform call:

| Skill | Question | `--yes` answers |
| --- | --- | --- |
| `register-adopt` | The plan: Deploy all / Change an answer / Choose gates / Cancel | **Deploy all**, unless the plan lists a platform call |
| `register-install` | Install / Cancel | **Install** |

The plan is still **printed** before the work starts. `--yes` removes the
keystroke, not the disclosure — a reader who passes it and watches the output
sees the same plan, and can still stop the run.

## What it must never answer

Three kinds of question are never answered by the flag. Since ADR 0062 they can
be answered by **the plan**, which is a different thing: the plan lists each
one in plain English, file by file and call by call, and an answer to the plan
covers exactly what it listed. `reference/pre-answered.md` is that rule. What
stays true is that the *flag* answers none of them on its own.

**Anything that changes state outside this repository.** `gate-repo`'s ruleset
calls are the whole of this category today: a `POST` that creates one, a `PUT`
that replaces one entire — dropping whatever the live ruleset carries and the
record does not — and a `DELETE` that removes classic branch protection. A
ruleset is in force for everyone the moment the call returns. **So `--yes` does
not answer a plan that lists one of these calls.** The plan question is asked,
once, with the exact calls on screen, and that answer covers them.
`tests/test_gate_repo_confirmation.py` holds the shape.

**Anything that takes over what the skill did not write.** The
*Adopt and stamp / Leave and abort* question fires when a gate finds
configuration carrying no stamp of its own — a file a person wrote by hand, and
adopting it means rewriting it to the register's shape. The plan names each such
file before anything runs, which is what makes one answer to the plan an
informed one. A takeover the plan did not name is asked.

**Anything that removes.** *Remove / Keep* questions exist because the skill has
found something it believes is redundant and might be wrong. The plan names
each one. A removal the plan did not name is asked; an unattended run never
deletes on a guess.

## How a skill implements it

Accept `--yes` in the arguments table. Where the confirmation step says to ask,
say instead that `--yes` answers it, name the option it answers with, and keep
printing what the question would have shown. Do not add a second spelling —
`-y`, `--force` and `--non-interactive` all mean something subtly different to
somebody, and one flag with one meaning is the point.

**`--yes` is not `--dangerously-skip-permissions`.** It answers this skill's own
questions. Every file write still goes through the harness's permission prompts
unless the session was started with a permission mode that covers them, which is
what `--permission-mode acceptEdits` is for and is a separate decision the reader
makes when they start the session.
