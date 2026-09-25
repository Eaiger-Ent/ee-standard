---
name: craft-install
description: >
  Install a Craft coding-standards profile: infer the stack, present what each
  level turns on and what it costs to satisfy, take an explicit yes, write the
  configuration your linter already runs, and hand back the half nothing can
  check. Triggers: 'install craft', 'choose a coding standard', '/craft-install'.
argument-hint: "[--repo <path>] [--profile <stack>/<level>]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /craft-install — choose a coding standard, and install it where it runs

You are running the **craft-install** skill. It writes a rule selection into the
configuration a repository's linter already reads, records what it wrote, and
hands back the properties no linter can decide — labelled unenforced.

**It is not a gate and it deploys no control.** The control register decides
whether a repository is *conformant*: whether ruff or ESLint is wired at the
editor, at pre-commit and in CI, pinned in a lockfile and unsuppressed. It says
nothing about **which rules are selected**, and a repository selecting one rule
passes it. That silence is what this fills. A craft rule is not a control, and
nothing here writes to `controls.yaml`.

**Three rules govern everything below.**

**The profiles decide, this skill copies.** Every byte of configuration you
write is already rendered, in `${CLAUDE_PLUGIN_ROOT}/profiles/`. You do not
assemble a rule list, reformat one, add a rule somebody asked for, or drop one
that looks noisy. A selection assembled in conversation is a selection nobody
can diff, and the rendered file is the reviewable artefact.

**Never write a loosening.** Lint configuration is gated by a control whose
variance is `narrowing-only`. Removing a selector somebody else put there, or
writing a lower level over a higher one, leaves the repository non-conformant —
so you refuse and report instead. There is no flag for this.

**Never fill in a stamp by hand.** The provenance line at the head of each
region is part of the rendered artefact. Copy it with the rest; never type one,
never edit a version in one, and never refresh one with no write behind it.

## Inputs

| Input | Where it comes from |
| --- | --- |
| `--repo <path>` | The repository to install into. Default: the working directory |
| `--profile <stack>/<level>` | Skip the question and install this. Still confirmed before any write |
| The pin | `.claude/skill-config.yaml`, key `craft-install`. Absent is not a default |
| The profiles | `${CLAUDE_PLUGIN_ROOT}/profiles/manifest.json` and the files beside it |

## Success criteria

- Every stack you claim to have installed has its configuration written, stamped
  and byte-identical to the shipped profile.
- The pin in `.claude/skill-config.yaml` names what you installed.
- The unenforced residue is written, and the report says what loads it.
- A second run over your own output changes nothing and says so.
- You wrote no key a control asserts, and no file you did not own.

## Pre-flight — read the manifest, then read the repository

**1. Read `${CLAUDE_PLUGIN_ROOT}/profiles/manifest.json`.** It carries the
profiles, their versions, how many rules each selects, how many of those declare
a fix, and the tool version those figures were read from. You present from this
file; you do not count rules yourself.

**2. Read the pin.** `.claude/skill-config.yaml`, key `craft-install`:

```yaml
craft-install:
  profiles:
    python/standard: 7
    react/standard: 4
  residue: CLAUDE.md
```

| What you find | What you do |
| --- | --- |
| No file, or no `craft-install` key | Nothing is pinned. Go on to inference and ask |
| A profile with no version | A first install of that profile. Install the current version and write the number |
| A profile the manifest does not define | **Stop.** A typo must not become a question: the run would install something other than what is written down |
| A version **ahead** of the manifest's | **Stop.** The plugin is older than the pin, and installing would move the repository down a profile |
| A version behind | Ordinary. Report what moved and go on |
| Two levels of one stack | **Stop.** Choosing between them is guessing at a level |
| Unparseable YAML | **Stop**, and write nothing. Falling back to the question would report that nobody had chosen, about a repository where somebody had |

Every *stop* above writes nothing at all. A half-installed profile is a state
nothing in this design can describe: the stamp would claim a profile the
configuration does not hold, and the next run would read that claim as truth.

**3. Read the repository, and never a self-declaration.** A stack is what the
files say:

| Stack | Applies when | Has somewhere to write when |
| --- | --- | --- |
| `python` | `pyproject.toml` exists at the root | The same condition |
| `react` | `package.json` declares `react` in `dependencies`, `devDependencies` or `peerDependencies` | `tsconfig.json` exists at the root |

The React row needs **both** and the reason is worth keeping: with no
`tsconfig.json` the control register gates no linter for this repository, so a
flat config written here is a file nothing runs; with react absent, the rules
are wrong for the code — 71 of the 93 rule bindings are React's own.

**If no profile applies, say which condition was false.** *No profile applies*
is not reviewable. *No profile applies because `package.json` declares no react
and there is no `pyproject.toml`* is, and it tells the reader what would change
the answer.

## Step 1 — Present what each level turns on, and what it costs

For each applicable stack, show both levels from the manifest. Per level:

- the number of properties it binds and the number of rules that comes to;
- how many of those rules **declare a fix**, and how many are hand-work;
- the tool version those figures were read from;
- how many properties it leaves unenforced.

Three things about the wording, and each has been paid for once:

**Say *declares a fix*, never *is cheap*.** A run of `--fix` over the violation
cases found the declarations overstated: the family declaring the most fixes
applied the fewest. The number is a floor on cheapness, not an estimate of it.

**Say what the rules cover.** The React profile names 88 rules and **enables
132**, because two presets are part of the profile: a team that consents to 88
and meets 132 was told the wrong number. The manifest carries the named count;
say that the presets are on top of it.

**Read the cost fresh where you can.** If the repository has the tool installed
and you can run it, read the fix availability from *that* version and report any
difference from the manifest. Where you cannot — a React repository before
`npm install` — present the manifest's figures and say which version they were
read at. A labelled approximation somebody can check beats a number presented as
current that was read on another machine.

Also name, before the question:

- **The six ESLint plugins** a React profile needs, because installing them
  changes the lockfile and the yes has to cover that.
- **The test globs** the React profile lints test files by —
  `*.test.ts(x)`, `*.spec.ts(x)` and `__tests__/`. They are fixed. A team that
  keeps tests elsewhere needs to know why theirs are unlinted.

## Step 2 — Take an explicit yes

Use `AskUserQuestion`, one question per applicable stack, options `standard` and
`strict`, plus *neither*. **There is no default level and you may not infer
one.** A profile is a decision about how much a team wants to be told, and
guessing it is the failure the whole design avoids.

If `--profile` was given, still show what Step 1 shows and confirm it. The flag
chooses; it does not consent.

**Say what each write will be, before making it**: the files you will create,
the sections you will write into, the dependencies you will add, and the pin you
will record. Then take the yes.

## Step 3 — Add the dependencies a React profile needs

Python needs none: ruff ships every rule the profile selects, and the control
register already requires ruff.

React needs six plugins. Add them with the command the **control register**
names for the lockfile this repository has — `ecosystems.node.add_dev_dependency`
in `controls.yaml`, keyed `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` or
`bun.lockb`. You choose no version and name no package manager; the resolver
picks the version and the lockfile records it.

**If they cannot be added, write nothing and say so.** A configuration importing
plugins the repository does not depend on fails on its first run, under the
control's name, for a reason that has nothing to do with the code.

## Step 4 — Write the configuration

Copy the rendered artefacts. Do not retype them.

| Stack | Artefact | Goes into |
| --- | --- | --- |
| `python` | `profiles/<slug>/pyproject-region.toml` | `pyproject.toml`, the first location `stacks.python` names |
| `python` | `profiles/<slug>/src-ruff.toml` | `src/ruff.toml` — the nested configuration two source-scoped properties need |
| `react` | `profiles/<slug>/eslint.config.mjs` | The repository root, written whole |

**Before you write anything: a configuration file later in the register's
search order wins at run time.** `stacks:` lists locations in the order the
*checker* reads them, and ruff reads the **nearest** file — a `ruff.toml` beside
a `pyproject.toml` replaces its `[tool.ruff]` entirely rather than merging with
it. So if any location after the first exists, **stop and report it**. Writing
the first leaves a repository where the audited configuration and the running
configuration are different files, and nothing warns: the first trial of this
skill installed a profile that applied to `src/` and not to `tests/`, and the
run looked like a success.

**Match a table header anchored to a line, never anywhere in the file.**
`[tool.ruff]` appears in comments — a `pyproject.toml` saying *no `[tool.ruff]`
section, and there will not be one* contains the string you are looking for, and
a search that finds it writes your span into a comment block. Look for the
header at the start of a line and nowhere else.

**A contribution is a span of lines, not a table.** The Python artefact is a
sequence of regions, each headed by the table it belongs in and delimited by
`# >>> ee-craft` and `# <<< ee-craft`:

- If the table exists, write the span **immediately after its header line** and
  leave everything else alone. Not at the end of the table: a table ends where
  the next header begins, so the comment block introducing the next section sits
  inside it, and a span written last lands under somebody else's explanation of
  a different table. The file still parses, so nothing catches it. The first
  trial did exactly this.
- If prose in or above the table describes its contents — *this section is
  empty*, *ruff's defaults* — your span makes it false, and it is not yours to
  edit. Name the line in the report and leave it. A stamped writer's comment
  belongs to that writer, and the fix is the team's.
- If it does not, write the header and the span together.
- Never write a table header a second time. Two `[tool.mypy]` headers is not a
  merge, it is a file that no longer parses.

**A key somebody else owns is a refusal.** If `[tool.ruff.lint]` already carries
a `select` outside your markers, you cannot add yours — two `select` keys in one
table is the same broken document. Report the union you would have written, say
which line to remove, and stop. Do not absorb their values into your span: that
deletes a line the team wrote and re-publishes their decision under this
profile's name, where the next run would carry it forever.

**The React config is written whole or not at all.** A flat config is a module;
no span of one means anything alone. If `eslint.config.*` exists and was not
written by this skill, report and stop. The file you write is
`eslint.config.mjs`: it does not depend on a `"type": "module"` this skill would
otherwise have to put in somebody's manifest.

## Step 5 — Write the residue, and say what loads it

Copy `profiles/<combination>/unenforced.md` — the directory named for **every**
profile installed, because a level binds properties the level below leaves
unenforced.

Write it to the path the pin's `residue:` names, or to `craft/unenforced.md`
when nothing names one, and add a marked span to the repository's assistant
context file pointing at it. Then say plainly, in the report: **Craft can write
a file; it cannot make a harness load one.** If nothing in this repository reads
that path, the residue is a document rather than context, and the team should
know which it is.

## Step 6 — Write the pin

Write `craft-install` into `.claude/skill-config.yaml` — your own key, with the
profiles and versions you installed, and nothing else in that file. Another
skill's key is not yours to touch.

The pin is what a later run compares against. Without it, the choice is re-asked
every time and *nothing changes under a repository that is not looking* becomes
unverifiable.

## Step 7 — Verify, by running the tools rather than by reading

- **Python:** `uv run ruff check .` resolves the configuration and reports
  findings. Findings are expected and are not a failure of this install — a
  configuration error is.
- **React:** `npx eslint --print-config <a source file>` resolves without error,
  and the rules you expect are enabled.
- **Both:** if `register-check` is installed, run it. Craft must not have broken
  a control. An exit of `3` is *no violation found, something unverified*, and
  is not a failure.

If verification fails, say so with the output. Do not repair the artefact by
hand: it is rendered, and a hand-repaired copy is no longer the profile.

## Output

Report, in this order:

1. What was inferred, and from which file.
2. The profile installed per stack, with its version, and where each value came
   from — the pin, or the answer just given.
3. Every file written, and for each the section and the number of rules.
4. The dependencies added, if any.
5. The residue: where it went, and what loads it.
6. What is **not** enforced: the count, and the one-line reason it is not.
7. The verification output.

## Idempotency

A second run compares three things and writes nothing when all three agree:

1. **The pinned version against the manifest's.** Report the difference; install
   only with a fresh yes.
2. **The file as it stands against the rendered artefact.** Byte-for-byte inside
   the markers. A difference is a hand edit, and reporting it is the point — a
   re-run that silently overwrote a deliberate change would be worse than one
   that refused.
3. **The stack inference now against the stamp's.** A `tsconfig.json` that did
   not exist at install time changes what applies, and it should be a reported
   change rather than a surprise.

## Error handling

| Condition | What to do |
| --- | --- |
| No applicable stack | Name the predicate that was false. Write nothing |
| A pin that is malformed, ahead, or names two levels of one stack | Stop, write nothing, say which |
| A `select` or a config file somebody else owns | Report the union, or the file, and stop |
| Dependencies cannot be added | Write nothing for that stack; the other stack may still proceed |
| The rendered artefact is missing | Stop. Do not reconstruct it — a hand-built selection is not the profile |

## What this skill does not do

- **It does not mint a control.** A craft rule that blocks a merge through a
  mandated tool is still a craft rule; the stamp is what stops it being an
  anonymous one.
- **It does not write a key a control asserts** — `strict`, the coverage key, or
  a blanket override table. The rendered artefacts contain none, and that is
  checked where they are rendered rather than trusted here.
- **It does not wire a locus.** The linter is wired by the control register's
  own gate; this writes the configuration all three loci already read.
- **It does not edit the Craft register.** The register lives in the standard's
  repository; this installs what was published from it.
