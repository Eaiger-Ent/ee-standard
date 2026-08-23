# ADR 0023: Choose the Smallest Model a Task Can Be Trusted To

**Status:** Accepted
**Date:** 2026-08-23

Nothing in this repository says which model an agent or sub-agent runs on. That
is not a gap between two rules — it is the absence of any rule, and the absence
has a default. Every sub-agent inherits the model of the session that spawned
it, so a repository-wide grep sweep and an adversarial review of a Tier-1
control run on the same model, and today that model is the most capable and
most expensive one available.

This ADR records what the classes are, where the rule lives so it cannot become
a second copy, and — the part that matters more than the classes — which half
of it this repository can actually verify.

## Background

### What exists today

An audit on 2026-08-23 found no control of any kind:

- `controls.yaml` — seventeen entries, no occurrence of `model`, `agent`,
  `subagent` or any model id.
- No `.claude/agents/` directory, and no `~/.claude/agents/` — so there is not
  one sub-agent definition file whose `model:` frontmatter could carry a pin.
- The seven skills under `plugins/ee-standard/skills/` declare `name`,
  `description` and `allowed-tools` only.
- `.claude/settings.json` carries the markdown-lint hook and nothing else;
  `.claude/settings.local.json` carries `outputStyle`.
- No ADR in `docs/adr/` touches model selection.

The nearest governing principle is the invariant that **enforcement is never
Claude**: gates are pinned binaries reading pinned configs. That keeps a
conformance *verdict* independent of model choice — a weaker model cannot
loosen a control, because no model decides one. It says nothing about which
model the skill that deploys the gate runs on, and that is the question here.

### The default is a choice nobody made

Omission is not neutrality. The documented resolution order when a sub-agent is
invoked is:

1. the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable,
2. the per-invocation `model` parameter,
3. the sub-agent definition's `model:` frontmatter,
4. the main conversation's model.

An omitted `model:` field defaults to `inherit`. With no definition files and no
environment variable, every sub-agent this repository has ever spawned resolved
at step 4. The repository is therefore already running a policy — *always use
the session model* — that no one wrote down and no one can see.

### What can select a model, and what that means for verification

The mechanisms are not equally visible to a checker, and the difference decides
the shape of the control rather than decorating it.

| Mechanism | Where it lives | Visible to a checker? |
| --- | --- | --- |
| `model:` frontmatter | `.claude/agents/*.md`, tracked | Yes — it is a file |
| Per-invocation `model` | The runtime call | No |
| `CLAUDE_CODE_SUBAGENT_MODEL` | The environment | Only if a tracked file sets it |
| Main-session model | `/model`, `--model`, `model` key | Partly |

Four consequences follow, and each is a constraint on the decision below:

- **A rule written only in prose is not a mechanism.** A paragraph in
  `CLAUDE.md` asking for a smaller model is read by an assistant that may or
  may not act on it, and by nothing else. The frontmatter field is read by the
  harness whether or not anyone is paying attention.
- **`CLAUDE_CODE_SUBAGENT_MODEL` outranks every per-agent floor.** Setting it
  to a small model in the devcontainer would silently demote the reviewers this
  decision exists to keep large. It is the one lever that can defeat the
  decision from outside it.
- **A fork inherits its parent's model unconditionally** — a `model` override
  is ignored for `subagent_type: "fork"`. A fork of an Opus session is Opus,
  and no floor can lower it.
- **Cloud review is not ours to select.** `/code-review ultra` is
  user-triggered and billed, and runs its own fleet. This decision does not
  reach it, and must not claim to.

### Why "smallest possible" is not simply a cost decision

Taken alone, "use the smallest model" optimises the wrong quantity. A model
that produces work which has to be redone costs more than the one that did it
once, and the cost lands on a human turn rather than a token budget.

This repository has a measured record on that point. Seven exit criteria have
been re-opened after being ticked, four of them by a single review — which
found GOV-001 passing a workflow that ran on neither push nor pull_request, a
tool compared only at filenames the checker itself named, and an ADR recorded
as implemented with one of its ratified moves never made. Every one of those is
a **false green**: work that looked finished and was not.

So the ladder is not "small everywhere, large where we feel nervous". The floor
is highest exactly where the job is to *disbelieve* a green result, and lowest
where the work is retrieval whose output the next agent re-derives anyway.

## Alternatives Considered

### Option 1: Write the policy in `CLAUDE.md`

Rejected as the *only* home, on this repository's own core invariant. A rule
restated in prose beside the artefact that implements it is the duplication —
"theme T-2" — this repo exists to prevent. `CLAUDE.md` would drift from the
frontmatter the moment either changed, and nothing would report it.

It is, however, exactly where a **pointer** belongs: one sentence naming the
register block and the directory, so a reader knows the rule exists and where
it is enforced. A pointer cannot drift, because it restates nothing.

### Option 2: Save it as a memory

Rejected. The memory directory is machine-local and user-local: it does not
reach a teammate, a pull request, CI, or an adopting repository. A standard
that only one laptop can see is not a standard. Worse, it would go stale
silently — a memory has no diff, no review and no expiry.

### Option 3: Pin the session with the `model` settings key

Rejected as insufficient rather than wrong. The `model` key sets what a session
*starts* on; sub-agents that inherit would follow it, but the whole point is
that different sub-agents should differ. It is one number where three are
needed.

### Option 4: Set `CLAUDE_CODE_SUBAGENT_MODEL` in the devcontainer

Rejected, and forbidden. It is the simplest way to make most sub-agents small,
and it is precedence 1: it would override every per-agent floor including the
review floor. Choosing it would make the rest of this decision unenforceable
while appearing to implement it.

### Option 5: Per-agent definition files, a register fact, and a file assert

Chosen. The definition files are the mechanism the harness reads; the register
holds the floors so they can differ per repository without changing the
checker; the assert reads the files back and fails when one drops below its
class floor.

## Decision

### Three classes, named by what the work does

Classification is by what the task *does*, not by what it is called — a name
can be borrowed, a behaviour cannot.

| Class | Definition | Model |
| --- | --- | --- |
| **R — review and diagnosis** | Reads work already done and tries to find it wrong | `opus`, floor **and** ceiling |
| **C — authoring** | Writes or edits a tracked file | `sonnet` floor, `opus` permitted |
| **S — retrieval and mechanics** | Writes no tracked file and makes no judgement a later agent will not re-derive | Smallest that can do it — `haiku` today |

The default for anything unclassified is **S**. That is safe only because
class C's boundary is mechanical: if the task ends with a tracked file
changed, it is C, whatever it was called at the start.

Known members, as of this ADR:

| Class | Members |
| --- | --- |
| R | `/code-review`, `/simplify`, `/security-review`, `/skill-doctor`, `/skill-preflight`, `/adr-review`, `/adr-consistency`, any agent asked to verify or refute a finding |
| C | Gate skills under `plugins/ee-standard/skills/`, `/adr-new`, `/adr-refine`, register edits, checker edits, any agent with `Write` or `Edit` |
| S | `Explore`, grep and file-sweep fan-out, `statusline-setup`, `/devcontainer-check`, formatting fixes, any read-only search |

`/simplify` sits in R rather than C although it applies fixes, because its
value is the judgement about what is redundant; the edit is a transcription of
that judgement. `/adr-check` is mechanical section-presence and sits in S,
where `/adr-review` — which judges content — does not.

`/doctor` is in no class. It is the built-in health check, it is run by hand,
and it selects no model, so there is nothing for a floor to apply to. The
diagnostic skills that *do* select one — `/skill-doctor`, `/skill-preflight`,
`/security-review` — are in R because they satisfy R's definition, not because
they share a name with it.

The ladder this ADR recognises is `haiku` < `sonnet` < `opus`. A model not on
that ladder — `fable`, or anything later — has no floor until an explicit
decision places it, and may not be used for R or C work before then. Guessing
a rank is the failure mode this whole register is built against.

### Where each copy lives

Three homes, one source, no restatement:

1. **`controls.yaml`** — a new `agent_models:` fact block holds the classes,
   their floors and each known member's class. It is the source, by
   [ADR 0018](0018-register-checker-boundary.md)'s test: a reasonable Equal
   Experts repository could need different floors — a data-science repo, or one
   with no authoring agents at all — without any change to the checker.
2. **`.claude/agents/*.md`** — the `model:` frontmatter is the mechanism. It is
   the only copy the harness reads, and it is derived from the register rather
   than authored beside it.
3. **`CLAUDE.md`** — one sentence pointing at both. Not the rule.

**Nothing goes in memory.** It is invisible to everyone but this machine.

### What is verified, and what is only recorded

Verifiable from files, and therefore the control's content:

- every file in `.claude/agents/` declares a `model:`,
- the declared model is at or above its class floor, and equals `opus` for R,
- no class R or C definition declares `inherit`, and
- no tracked file sets `CLAUDE_CODE_SUBAGENT_MODEL`.

Not verifiable from this repository, and therefore declared rather than
claimed: a per-invocation `model` argument, a `Workflow` script's `opts.model`,
a fork's inherited model, and anything `/code-review ultra` runs in the cloud.

That asymmetry is not a defect to be engineered away — it is the same shape as
`gate-repo`, whose recorded ruleset is **intent** and never enforcement, and it
is handled the same way: the verify block declares its own partial with an
expiry, per [ADR 0017](0017-partial-verification-is-reported.md), so the run
cannot exit `0` while pretending the runtime half was checked.

## What the register must gain

Ordered, because the ordering is the part that can be got wrong.

### 1. The register fact lands before any definition file

An `agent_models:` block in `controls.yaml` first. If a `.claude/agents/*.md`
file lands first, the frontmatter becomes the source and the register
documents it — which is the inversion this repository exists to prevent, and
which is invisible once it has happened.

### 2. A control, at `warn`

`AGT-001`, Tier 2, `variance: narrowing-only`, `baseline: null`, `rung: warn`.
Narrowing means *raising* a floor; a repository may require opus where the
register asks for sonnet, never the reverse. It starts at `warn` because no
definition files exist yet and a `blocking` control would fail every repository
including this one on the day it lands; promotion to `blocking` is a separate
recorded decision, not a follow-up commit.

Tier 2 rather than Tier 1: no Tier-1 control today concerns how work is
produced, only what the repository contains, and re-tiering to make a point is
the move this repository refuses.

### 3. One assert, added to the closed set

`agent_definitions_declare_model_floor`, `kind: file`, reading the four
verifiable properties above. An unknown assert name is a schema error, so the
closed set and the checker move together.

### 4. The partial, with an expiry

The verify block declares the unverified property — runtime model selection —
with an expiry no later than **2027-02-28**. GOV-003 fails an expired partial,
which is what stops "we will check that later" from becoming permanent.

### 5. A contract bump

The register gains a field a skill reading it must understand, so
`meta.register_contract` goes to 20.

### 6. The adopter-facing steps

`docs/08-adopting.md` owes a section, per the standing requirement in
`docs/04-build-plan.md` — including the one instruction that is not about
floors at all: do not set `CLAUDE_CODE_SUBAGENT_MODEL`.

## Consequences

**What this buys:**

- The repository's actual policy becomes visible. Today it has one and cannot
  state it.
- The expensive model is spent where a missed defect is expensive, and not on
  finding a filename.
- The rule is deployable. An adopting repository gets floors it can tighten,
  through the same register every other control comes from.

**Trade-offs and risks:**

- **The saving is unmeasured.** This ADR asserts that most sub-agent turns are
  retrieval, and it has no measurement. If the mix is mostly authoring, the
  saving is small and the cost of the machinery is not. Nothing here should be
  read as a measured economy until someone measures it.
- **Class S's failure mode is silent.** A review that misses a defect produces
  a green that a later review can catch. A search that misses a file produces
  an answer that looks complete, and nothing downstream disagrees with it. The
  floor for S is therefore the row most likely to be wrong, and the one to
  revisit first.
- **The control checks declarations, not behaviour.** It reads what a file
  says a sub-agent will use. Over-reading it as "the register verifies which
  model ran" would be exactly the substitution this repository keeps catching —
  the same one GOV-001's message refuses about required checks.
- **Four of the classes' members are skills this repository does not own.**
  `/code-review`, `/simplify` and the rest are installed, not authored here,
  and a definition file cannot pin a skill's model. For those, the floor is
  guidance to whoever invokes them until the harness offers a per-skill pin —
  which is a real hole, and is why the partial exists rather than a footnote.
- **A `warn` rung enforces nothing on day one.** That is deliberate, and it is
  also how a control quietly stays advisory for a year. The promotion decision
  should be dated when this is accepted, not deferred to whenever someone
  notices.

## Related ADRs

- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — the test that puts the floors in the register rather than in Python.
- [ADR 0017: Report a Partially Implemented Control as Partial](0017-partial-verification-is-reported.md)
  — the machinery that lets a control admit the half it cannot see.
- [ADR 0016: Give "Could Not Verify" Its Own Exit Code](0016-exit-codes-for-unverifiable-controls.md)
  — why the unverified half is `UNCLASSIFIED` rather than a pass.
- [ADR 0022: What Must Be True Before CI Carries a Platform Token](0022-a-platform-token-ci-carries.md)
  — the precedent for recording a requirement's ordering rather than trusting
  it, and for keeping a local posture out of what an adopter installs.

## References

- [Subagents](https://code.claude.com/docs/en/sub-agents) — the frontmatter
  fields, the `model` values, and the resolution order quoted above.
- [Settings reference](https://code.claude.com/docs/en/settings-reference) —
  `model`, `availableModels`, `modelOverrides`, `fallbackModel`.
- [Claude Code settings](https://code.claude.com/docs/en/settings) — the
  precedence stack, and which environment variables override a settings key.
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
  — the external standard `AGT-001` would cite.
- [NIST AI 100-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf) —
  § MAP and § MEASURE, on recording the model a system uses and the basis for
  choosing it.
