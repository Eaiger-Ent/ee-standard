# ADR 0062: An Adoption Is Answered Once, From Its Plan

**Status:** Accepted
**Date:** 2026-11-07
**Revision:** 1

## Background

**The problem.** `/register-adopt` asks one question about its plan, then
dispatches six gates, and the gates ask their own questions one at a time.
On a first deployment every answer is *yes*. Each question arrives in the
middle of a gate's output, with less context than the plan had, and the
person answering has already agreed to the whole adoption. The questions add
time, not value.

An adopter asked for this on 2026-11-07, from a real run: list every change
in plain English, take one answer, then make them all.

**What asks today.** The plan question, then these, in dispatch order:

| Kind | Asked by | When it fires on a first deployment |
| --- | --- | --- |
| **Takeover** — *Adopt and stamp / Leave and abort* | all five file-writing gates | Every artefact the gate did not stamp. `guided.sh` copies `.devcontainer/` in from a template, so `gate-build` always asks |
| **Choice** — which package manager, which test command, which container user | `gate-supply-chain`, `gate-quality`, `gate-build` | Two lockfiles; no test step yet (always, on a new repository); an image with no user |
| **Removal** — *Remove / Keep* | `gate-quality`, `gate-secrets`, `gate-iac` | A superseded linter, a hand-written git hook, `tfsec` or `terrascan` |
| **Platform** — one per API call | `gate-repo` | One `POST` to create the ruleset, and a `DELETE` if classic branch protection exists |

**What the current rule says.** `reference/unattended.md` lets `--yes` answer
the plan and nothing else. It names three kinds of question that may never be
answered in advance: anything that changes state outside the repository,
anything that takes over what the skill did not write, and anything that
removes. `gate-repo/SKILL.md` adds that none of its confirmations "is waivable
by an earlier approval, including a plan approved in `register-adopt`".
Phase 3's criterion *gate-repo confirms before every remote mutation,
independently of the plan-level confirmation* is held by
`tests/test_gate_repo_confirmation.py`.

**Why that rule exists.** The fear was a blanket *yes*. An answer to "proceed
with the plan" should not be read as an answer to "rewrite the Dockerfile you
wrote by hand", because the plan never said it would. The defect is not
answering early. The defect is answering something that was never shown.

## Alternatives Considered

### Option 1: Keep asking

Rejected. It is the state the adopter reported, and the questions it keeps are
answered the same way every time on a first deployment.

### Option 2: Let `--yes` reach the gates

Rejected. A flag would answer questions nobody saw. That is exactly the blanket
*yes* the current rule was written against, and it still would not tell the
adopter what is about to change.

### Option 3: The gates report their questions before anything runs, and the plan answers them

Chosen. Each gate is dispatched once in a mode that reads and writes nothing,
and reports every question it would ask, in plain English, with the answer it
proposes. The plan lists them all. One answer to the plan answers every
question it listed, and only those.

## Decision

**Option 3.** A question shown in the plan is answered by the plan. A question
the plan did not show is still asked.

### How it works

1. **`--plan`.** Each gate accepts `--plan`. It runs its pre-flight and its own
   "report the plan" step, writes nothing, and asks nothing. It ends with one
   block that lists each question it would ask: the kind, the exact subject (a
   file path, or an API method and route), one plain-English sentence saying
   what the answer will do, and the proposed answer.
2. **The plan.** `register-adopt` dispatches every applicable gate with
   `--plan` during its pre-flight. Step 2 prints a **What will change** list
   below the plan table, one sentence per change, grouped by gate. It includes
   every proposed answer to a choice, such as *tests run with
   `uv run pytest`*.
3. **One answer.** Step 3's question gains a fourth option. The options are
   **Deploy all** / **Change an answer** / **Choose gates** / **Cancel**.
   **Deploy all** accepts every listed change. **Change an answer** asks only
   about the ones the person wants to change.
4. **`--answers`.** After the answer, `register-adopt` writes the accepted list
   to `$(git rev-parse --git-dir)/register-adopt/answers.json`, inside `.git`,
   so it is never tracked or committed. It dispatches each gate with
   `--answers <that path>`.
5. **At each question.** Before asking, a gate looks for an entry with the
   same gate, kind and subject. If it finds one, it uses that answer and prints
   one line, `Answered in the adoption plan: <the sentence> → <the answer>`. If
   it finds none, it asks, exactly as today.

### What counts as the same question

| Kind | Matches when |
| --- | --- |
| Takeover | Same file |
| Removal | Same file or hook |
| Choice | Same question, and the proposed answer is still one the register accepts |
| Platform | Same method and route, **and the same SHA-256 of the request body** |

The platform row is stricter for a reason. If the live state moved between plan
and dispatch, the call changes. For example, a ruleset appeared, so the `POST`
became a `PUT`. A `PUT` replaces a ruleset entire, so it is a different call
and it is asked. The `DELETE` of classic protection still runs only after the
ruleset reads back as active, which is a `GET` and needs no answer.

### What `--yes` answers now

| Question | Before | After |
| --- | --- | --- |
| The plan, with no platform call in it | `--yes` answers it | `--yes` answers it, which covers every listed takeover, removal and choice |
| The plan, when it lists a platform call | `--yes` answers it; `gate-repo` asks each call | **`--yes` does not answer it.** The plan question is asked once, and that answer covers the listed calls |
| A takeover, removal or choice the plan listed | Asked by the gate | Answered by the plan |
| A platform call the plan listed | Asked by `gate-repo` | Answered by the plan |
| Anything the plan did not list | Asked | Asked |

So a change to platform state always has a person's answer behind it, given
while the exact call was on screen. It no longer needs a second answer, given
later with less on screen.

### What this does not reach

- **`lint-md` and `lint-yaml`** belong to another plugin and know nothing of
  `--plan`. The plan says that they ask their own questions.
- **`register-install` at Step 0** runs before there is a plan to answer from.
  Its one question stays, and `--yes` still answers it.
- **The harness's permission prompts** are not questions any skill asks.
  `--permission-mode acceptEdits` is still how a session avoids them.

## Consequences

**What this buys:**

- A first deployment is one read and one answer. Every change is listed in
  plain English, so the answer is informed rather than habitual.
- A takeover is now shown in the plan, file by file. Before this, the person
  saw it only mid-run.

**Trade-offs and risks:**

- **The plan can be wrong.** `--plan` predicts what a gate will ask. If the
  repository changes between plan and dispatch, the prediction misses. The
  matching rule turns a miss into a question rather than an assumption, which
  is the right direction to fail in.
- **Phase 3's confirmation criterion changes meaning.** A platform call is
  still confirmed, every time, by an answer naming that exact call. The answer
  may now come from the plan. The criterion is annotated rather than re-opened,
  and `tests/test_gate_repo_confirmation.py` holds the new rule.
- **Every gate's skill changes.** The rule lives once, in
  `reference/pre-answered.md` ([ADR 0036](0036-shared-skill-prose-has-one-home.md)).
  Each gate points at it rather than restating it. All of it is owed upstream.
- **No test can prove a model obeys a skill.** The tests hold the shape of
  the instruction, not the behaviour.

## Related ADRs

- [ADR 0036: Prose Several Skills Must Follow Is Shipped Once and Read at Runtime](0036-shared-skill-prose-has-one-home.md)
  — why the rule is one reference file and not six paragraphs.
- [ADR 0049: The Adoption Route Is Executable, And Detects Rather Than Instructs](0049-the-adoption-route-is-executable.md)
  — the host-side route that ends by handing over to `/register-adopt`.
- [ADR 0057: `register-install` Writes the Conformance Step](0057-register-install-writes-the-conformance-step.md)
  — `register-install`'s second dispatch, which this leaves unchanged.

## References

- [Claude Code skills](https://code.claude.com/docs/en/skills) — how a skill
  receives its arguments.
