# Craft — the plan

Coding standards for the code this organisation writes and the code its
assistants generate, for two stacks: **Python** and **React**.

**Status: proposed.** Nothing here is a decision, with one exception: the
workstream is named **Craft**, settled 2026-09-05 and recorded in the naming
standard below, because every file, identity and skill name downstream depends
on it. The decisions this work needs are listed under
[Decisions this workstream owes an ADR](#decisions-this-workstream-owes-an-adr), and each
lands in `docs/adr/` before the thing it governs is built.

Written 2026-09-05 as *Practice*; renamed to *Craft* the same day, before the
first commit, so the earlier word appears nowhere in this repository's history.

## What this is, and why it is not the register

The control register answers *is this repository conformant* — a gate runs at a
locus, a pinned tool exits non-zero, a merge is blocked. It is deliberately
silent about whether the code inside is any good. LNT-001 verifies that ruff is
wired at editor, pre-commit and CI, pinned in the lockfile, unsuppressed and
stamped. It says nothing about **which rules ruff selects**, and a repository
selecting `E501` alone passes it.

That silence is the gap. Craft asks a different question — what does
well-made Python or React look like, which parts of that can a machine decide,
and how does a team install the answer without being buried by it — and it is
not a continuation of the build plan. It has its own vocabulary, set out below,
so that nothing here reads as though it extends a phase that is finished.

The deliverable at the end is not a document. It is: someone opens a repository,
is helped to decide which standards they want, and gets them installed and
pinned at every locus — the model `lint-md` already uses for DOC-001.

## Scope

**In.** Python and React, because they are the two common stacks. Both the
enforceable half (tool configuration) and the judgment half (prose an assistant
loads), with the boundary between them stated rather than blurred.

**Out.** Bicep, .NET, Angular and likec4 — no consumer here. Fine-tuning a model
on a ruleset: the rules change faster than a tune, and a weight cannot be
diffed, which is the same objection this repository makes to enforcement by
Claude. Any rule that would claim enforcement it does not have.

## What the first look at `llm-toolkit` found

`https://github.com/EqualExperts/llm-toolkit` at `a46825d`, cloned to `temp/`
(gitignored). Surveyed 2026-09-05. It is **one input among several**, not the
basis of the work, and the reason is the first row below.

| Finding | Consequence |
| --- | --- |
| No Python ruleset and no React ruleset. The only frontend file is Angular v16+ (signals, `inject()`, standalone APIs); `typescript.rules.md` is generic TS and does transfer | Both stack layers must be researched from scratch. Research is the main event, not a preliminary |
| 174 numbered rules across 11 of 16 files. Five files carry no IDs at all; `typescript.rules.md` uses `TS-001`; emphasis differs three ways | A regex pass keyed on `RULE-0xx` silently drops a third of the corpus. Read per file, not in one sweep |
| `RULE-001` exists in ten different files — IDs are file-local | An upstream ID cannot be our key. See the identity row in the naming standard |
| `platform/bicep.rules.md` is a prompt for genaiscript annotation output, and half of `code-quality.md` is assistant-behaviour instruction ("never use apologies") | These are not rules about code. They need a bucket of their own or they corrupt the count that decides the investigation |
| No `LICENCE` file. `CODEOWNERS` names three owners | Equal Experts owns the repository and this work is Equal Experts', so the **ideas** are ours to use — confirmed 2026-09-05. That is not a grant to copy the prose: with no licence file there is still nothing to point at, so citing their rule IDs and writing our own tool bindings remains the work. The attribution posture is S4's, per decision 4 |
| Last commit 2026-04-22 | Quiet. An upstream conversation is cheap and unlikely to race us |

What survives for our two stacks is the language-neutral craft layer —
`clean-code`, `solid-principles`, `testing-principles`, `api-design`,
`git-rules`, and the enforceable half of `code-quality` — around 90 numbered
rules. Useful, and nowhere near sufficient.

`docs/control-planes/` in that repository is a separate methodology with its own
"control plane" vocabulary. It overlaps the word "control" and nothing else. Read
before either term is used loosely.

## The naming standard for this workstream

Deliberately unlike the register's. Nothing in this workstream should read as though
it continues `docs/00`–`17`, and nothing it produces should be mistaken for a
control.

| Thing | Standard | Why |
| --- | --- | --- |
| The workstream | **Craft** | The register says what *conformant* means; this says what *well-made* means. A different question earns a different word. **Craft** over the four names weighed on 2026-09-05 — *Practice*, which this plan was first written under, collides with the Equal Experts org unit and carries "best practice" baggage; *Idiom* reads too narrow for the architecture and testing rules; *Workmanship* is awkward as an adjective. `a craft rule is not a control` is the sentence the word has to survive, and it does |
| Documents | `docs/craft/<stage>.<slug>.md`, stage one of `survey`, `assess`, `review`, `design`, `build` | Named stages, no global number. This file is the plan rather than a stage, so it is `plan.md` |
| Rule identity | Lowercase, stack-scoped, dotted: `python.function-length`, `react.no-effect-for-derived-state` | **Not** `CRA-001`. Three letters, dash, three digits means *control* in this repository, and these are not controls. More practically: we merge many sources, upstream IDs collide, and keying on the property rather than the citation means no upstream renumbering can break us. Sources are cited **against** an identity, never used as one |
| Decisions | `docs/adr/`, continuing at 0051 | A deliberate exception to the separation. A second ADR sequence is two logs free to drift, which is the failure this repository exists to prevent |
| Controls | None minted until a rule has a locus, a tool and a verdict | A craft rule is not a control. Anything reaching `controls.yaml` has crossed a boundary that needs an ADR to cross |

## The stages

Each stage has one deliverable and one exit criterion. A stage is not finished
because its document exists; it is finished when the criterion is met.

### S1 — Survey

Build a **source register** before reading any rule: URL, licence, maintenance
signal, what authority it carries, and what it claims to cover. Sources are
assessed as sources first, so that a stale blog post and a language's own
documentation are never weighed the same.

Candidates to start from:

- **Python** — ruff's rule taxonomy, which already implements pycodestyle,
  pyflakes, pylint, bugbear and pyupgrade under stable IDs and is the single
  richest source of already-enforceable rules; PEP 8 and PEP 20; Google's Python
  style guide; `pytest` practice; OWASP ASVS for the security slice.
- **React** — the React documentation's own Rules of React and *You Might Not
  Need an Effect*; `eslint-plugin-react-hooks` including the compiler rules;
  `typescript-eslint` recommended-type-checked; `eslint-plugin-jsx-a11y` and
  WCAG; Testing Library's guiding principles; one opinionated style config read
  as a source rather than adopted.
- **Neutral** — the six transferable `llm-toolkit` files.

Also in S1: the licence and upstream-contact question, which is outward-facing
and needs a named yes before anyone acts on it.

**Deliverable:** `survey.sources.md`.
**Exit:** every source carries a licence answer and a maintenance signal, and
each of the two stacks has at least one source of first-party authority.

### S2 — Assess

One table, property-keyed, covering both stacks. Per property: what it asserts,
which sources assert it and whether they agree, the enforceability bucket, the
exact tool and rule ID where one exists, and a proposed default-on or
default-off.

The four buckets:

1. **Already a lint rule.** Needs configuring and pinning, not writing.
2. **A check could hold it.** Writable, at a cost that has to be named.
3. **Judgment only.** Architecture, naming quality, clarity. Prose is the only
   instrument, and a rule that pretends otherwise is worse than one admitting it
   has none.
4. **Assistant behaviour.** How a tool should respond, not how code should read.
   Tracked separately or discarded; never mixed into the three above.

Read per source and per file. One file hand-checked against the machine pass, so
the count that decides the next stage has been sanity-checked by a person.

**Deliverable:** `assess.rules.md`.
**Exit:** every property carries a bucket, contested classifications are marked
as contested rather than resolved silently, and bucket 1's share of buckets 1–3
is stated for each stack.

### S3 — Review, empirically

The stage that decides whether any of this improves someone's experience, and
the one most plans skip.

Take the candidate default-on set and run it unmodified over several real Python
and React repositories. Count. A profile that emits thousands of findings on
first install is switched off within a day and teaches a team to ignore the
tool — that is a worse outcome than shipping nothing. Acceptance criteria are
written **before** the run: a findings-per-KLOC ceiling and a tolerable
false-positive rate. The default-on set is then tuned until it clears them, and
what got demoted to default-off is recorded with the number that demoted it.

Contested classifications from S2 get a second reader here.

**Deliverable:** `review.noise.md` — criteria, measurements, what moved and why.
**Exit:** the default-on set clears the criteria on every trial repository, and
every demotion cites its measurement.

### S4 — Design

What gets built, decided before it is built.

- The **profile model**: what a profile is (stack, archetype, strictness), how
  someone chooses one, how it is versioned, what happens when it changes under a
  repository that already installed it.
- The **config surface**. For both stacks this is real tool configuration —
  `[tool.ruff.lint] select`, a flat ESLint config — generated and pinned. Not a
  new format, and not a second copy of one.
- The **craft/register boundary**: when, if ever, a craft rule becomes a
  control.
- The **attribution and licence posture** for every source S1 registered.

**Deliverable:** `design.profiles.md` plus the ADRs it requires.
**Exit:** every ADR it names is Accepted.

### S5 — Build the chooser and the installer

A skill in the `lint-md` model. It infers stack and archetype from the
repository, presents the profiles with what each turns on **and what S3 measured
it will cost**, takes an explicit yes, writes the pinned configuration at every
locus, records what it wrote, and hands back the judgment-only residue as prose
an assistant loads — labelled unenforced.

Versioned and published, so a consumer pins it the way `.claude/skill-config.yaml`
pins `lint-md` here.

**Deliverable:** the skill, its configuration contract, and `build.installer.md`.
**Exit:** a clean repository of each stack goes from nothing to a working,
pinned, locus-wired configuration in one run, and a second run over the result
changes nothing.

### S6 — Trial and review

Install on a real repository. Run for a stated period. Revise against what the
team reports, not against what the plan predicted.

**Deliverable:** `review.trial.md`.
**Exit:** criteria named in S3 still hold in use, or the gap is recorded and
the profile changed.

## Decisions this workstream owes an ADR

None of these is settled. Each is listed so that it is taken deliberately rather
than drifted into.

1. Whether a craft rule may ever become a control, and what it must have
   before it does.
2. What a profile is, and whether "archetype" (backend service, library,
   application) is a real axis or whether stack alone carries it. Deferred until
   S2 shows whether rules actually vary that way.
3. Where the enforceable mapping lives, given ADR 0018 — the register/checker
   boundary applies to anything this produces that a machine reads.
4. Attribution and licence, per source.

## Open questions

- Whether any Equal Experts repository already consumes these rules, and how.
  Answering it properly means a code search across the EqualExperts org, which
  is a scan of company repositories and has not been authorised. Open until that
  yes, or until a narrower route is found.

Two questions this plan was written with are now closed, kept here so the
closing is visible rather than silent:

- ~~Whether "Practice" is the right name for the workstream.~~ Settled
  2026-09-05: **Craft**. The reasoning is in the naming standard above.
- ~~Blocking, outward-facing: the `llm-toolkit` owners' view on machine
  enforcement, and the missing licence.~~ Closed 2026-09-05 without contact:
  Equal Experts owns `llm-toolkit` and this work is Equal Experts', so the ideas
  may be used. The licence file is still absent, which stays a **finding** the
  survey records rather than a blocker, and it still constrains copying prose.

## What this workstream will not do

- Fine-tune a model on a ruleset.
- Vendor another team's prose without a licence.
- Ship a rule that claims enforcement it does not have.
- Restate the register's status, or add a second list of outstanding work.
