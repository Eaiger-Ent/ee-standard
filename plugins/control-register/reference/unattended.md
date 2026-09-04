# Running without being asked the same question again

One home for this rule rather than a copy in each skill (ADR 0036, in the
standard's own repository).

Shared by the skills a person re-runs: `register-adopt` and `register-install`.

## `--yes` pre-answers the proceed question, and nothing else

An adoption is not one command. It is re-run — after a failure, after a token
arrives, after a control is added — and each re-run asks the same two questions
and gets the same two answers. A confirmation that is always answered the same
way is not consent; it is a keystroke, and it trains the reader to press it
without reading, which is the state the *other* questions here exist to avoid.

**`--yes` means: I have read the plan, proceed.** It pre-answers exactly the
questions whose only effect is writing configuration inside this repository:

| Skill | Question | `--yes` answers |
| --- | --- | --- |
| `register-adopt` | The plan: Deploy all / Choose gates | **Deploy all** |
| `register-install` | Install / Cancel | **Install** |

The plan is still **printed** before the work starts. `--yes` removes the
keystroke, not the disclosure — a reader who passes it and watches the output
sees the same plan, and can still stop the run.

## What it must never answer

Three kinds of question stay, and a skill that suppresses one of them under
`--yes` is a defect rather than a convenience.

**Anything that changes state outside this repository.** `gate-repo`'s ruleset
calls are the whole of this category today: a `POST` that creates one, a `PUT`
that replaces one entire — dropping whatever the live ruleset carries and the
record does not — and a `DELETE` that removes classic branch protection. Each
asks for itself, every time, and `tests/test_gate_repo_confirmation.py` holds
that shape. A ruleset is in force for everyone the moment the call returns, and
"I have read the plan" is not an answer to "may I change what your colleagues
can push".

**Anything that takes over what the skill did not write.** The
*Adopt and stamp / Leave and abort* question fires when a gate finds
configuration carrying no stamp of its own — a file a person wrote by hand, and
adopting it means rewriting it to the register's shape. This one does not recur:
once stamped, the gate recognises its own work and stops asking. So suppressing
it would buy a re-runner nothing and cost a first-timer their file.

**Anything that removes.** *Remove / Keep* questions exist because the skill has
found something it believes is redundant and might be wrong. An unattended run
that deletes on a guess is the failure this whole standard is about.

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
