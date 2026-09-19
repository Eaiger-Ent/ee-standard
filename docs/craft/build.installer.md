# Craft — the installer

Stage **S5** of [`plan.md`](plan.md). The chooser and the installer: the skill
that infers a repository's stack, presents the profiles with what each costs,
takes an explicit yes, and writes the pinned configuration at every locus the
control register declares.

**Written in slices, like [`design.profiles.md`](design.profiles.md) before it.**
Each section lands with the work that produced it, and [§ What this document
still owes](#what-this-document-still-owes) is the list of what has not been
written. S4 is the design this reads; nothing it settled is restated here, and
every section below cites where its premise came from.

Started **2026-09-19**.

## The configuration contract

**What the skill is called, what a repository may tell it, and what happens when
that file is absent, partial or wrong.** [ADR
0042](../adr/0042-a-deploying-skill-reads-local-configuration.md) is the
contract this joins; `design.profiles.md` § What a consumer pins settled that
Craft's pin lives in it and that an absent pin is not a default. What that
section left — and what a skill cannot be built without — is the rest of the
file's behaviour: which keys exist, which deliberately do not, and which of
*absent*, *partial* and *malformed* is an error.

### The skill is `craft-install`, and the key is its name

ADR 0042 part 2 keys the file by skill name, so the name is the contract's first
term rather than a later detail. `craft-install` is the parallel to
`register-install`, which installs the checker the same way: a verb that says
what the run does to the repository it is pointed at.

[ADR 0031](../adr/0031-the-plugin-is-named-for-the-register.md) does not reach it. That
naming rule governs the control-register family — the checker, the `register-*`
skills, the gates that keep their names — and Craft is deliberately a different
question, with a naming standard of its own in [`plan.md`](plan.md) § The naming
standard for this workstream. That table gains one row for skills with this
slice; the row is the standard, and this paragraph is not a second copy of it.

**Which plugin ships it is not settled here** and does not need to be: the key is
the skill's name, not its publisher, and a skill that moved between plugins would
keep both.

### Two values, and the three that were considered and refused

```yaml
# .claude/skill-config.yaml
craft-install:
  profile: python/standard    # <stack>/<level>, ADR 0052's two axes
  version: 7                  # the profile version installed, a counter
  residue: CLAUDE.md          # optional; where the unenforced prose is written
```

`profile` and `version` are ADR 0052's, and `design.profiles.md` § What a
consumer pins and § The version is a counter are why each has the shape it has.
`residue` is this slice's addition, and the reason is that **the file an
assistant loads is a property of the repository, not of the profile**: one team
loads `CLAUDE.md`, another an `AGENTS.md`, another a directory of context files,
and the judgment-only residue is worth nothing written somewhere nothing reads.
Its default is the residue slice's to settle, not this one's.

Three more keys were considered. Each is refused, and the refusals are more
informative than the acceptances:

| Refused key | Why it is not in the contract |
| --- | --- |
| A per-rule `ignore:` or `exclude:` | Removing selectors from LNT-001's gated configuration is a **loosening of a narrowing-only control**, and `design.profiles.md` § The installer never writes a loosening is why the installer refuses that write. A key whose only use is to request a write the skill declines is worse than no key: it invites the request, then answers no. A team wanting fewer rules edits the configuration itself and answers for it through the variance machinery the register already has |
| A `config_path:` — which file to write | `controls.yaml`'s `stacks:` block names the tool and the ordered config locations per stack, so **Craft chooses what goes into a configuration and not where it lives** (`design.profiles.md` § The config surface). A key here would be a second statement of the register's answer, free to drift from it, which is theme T-2 by the most ordinary route available |
| A tool version or invocation | The lockfile is the version pin (§ What pins the tool version) and `tools.<tool>.invocation` is the register's (ADR 0020). Neither is Craft's to take as input |

### Absent, partial and malformed are three different things

ADR 0042 part 3 says absent file, absent key and absent value all get today's
behaviour. Craft departs from it for *absent* — there is no sensible default
level, and guessing one is the declared-archetype failure ADR 0052 rejected
wearing different clothes — and that departure is already recorded. What it left
is the middle case, which a skill meets on real repositories and a design
document can miss: a pin that exists and is incomplete.

| The file says | The installer does | Why |
| --- | --- | --- |
| No file, or no `craft-install:` key | Infers the stack, presents the levels with what each rule costs, takes an explicit yes | `design.profiles.md` § What a consumer pins. An absent pin is a decision not yet taken, and the skill's job is to take it with somebody |
| `profile`, no `version` | Treats it as a **first install of that profile** — installs the current version and writes the number | The version's only job is to answer *what moved since*. With no number there is nothing to compare, and inferring the version the team meant would fabricate exactly the fact a re-run reports |
| `version`, no `profile` | Fails | A version is a position in one profile's history. Without the profile it names nothing, and the nearest guess — the stack inferred from the repository — would silently pick a level |
| A `profile` the register does not define | Fails, writes nothing | A typo must not quietly become an interactive prompt: the run would install a profile other than the one written down, and the file would still say the wrong thing afterwards |
| A `version` ahead of the register's current one | Fails, writes nothing | The same shape as a provenance stamp ahead of the register, which this repository treats as a defect rather than as staleness. It means the installer is older than the pin, and installing would move the repository **down** a profile — the loosening the installer never writes |
| A `version` behind the current one | Proceeds, and reports the `changes` entries between the two with their directions | The ordinary case, and ADR 0052's requirement |
| Unparseable YAML, or a value of the wrong type | Fails, writes nothing | ADR 0042's own rule for a malformed file, taken as written. Silently falling back to the interactive path would report the opposite of the truth — that nobody had chosen — about a repository where somebody had |

**Failing means writing nothing**, not writing what it could and reporting the
rest. A half-installed profile is the state nothing in the design can describe:
the stamp would claim a profile the configuration does not hold, and the next
run would read that claim as the truth.

### The pin, the stamp and the register are three records, and none is a copy

`design.profiles.md` § What a re-run does names three comparisons. Building them
means naming what is being compared, and the answer is three records that look
alike enough to be mistaken for the duplication this repository exists to
prevent:

| Record | Where | What it asserts | Written by |
| --- | --- | --- | --- |
| The **pin** | `.claude/skill-config.yaml` | Which profile this team chose, at which version | `craft-install`, on an explicit yes |
| The **stamp** | The header of each gated configuration file (ADR 0055 rule 2) | What was written into *this file*, and which evidence gates were open when | `craft-install`, in the same run |
| The **register** | `craft/` | What the profile is **now** | Craft, as rules change |

They are not three copies of one fact, because **they are expected to differ and
the differences are the report**. The pin is intent; the stamp is what happened;
the register is the present. It is the shape this repository already relies on
twice — `.pre-commit-config.yaml` states intent where `.git/hooks/pre-commit` is
whether anything runs, and `controls.yaml` is the register where a provenance
stamp is what was deployed against it.

The doctrine that comes with that shape comes with this one, and it resolves the
pairs the design left implicit:

- **Stamp behind pin**: the install did not complete, or somebody edited the pin
  by hand. Staleness, reported and offered a re-run.
- **Stamp ahead of pin**: the pin was lowered by hand after an install. The
  installer will not write down to it — writing down is the loosening it refuses
  — so it reports the pair and leaves both as they are.
- **Pin behind the register**: the ordinary delta. The `changes` entries between
  the two numbers, each with its direction.
- **Pin ahead of the register**: the defect row above.

### `craft_contract` is the register's number, not the team's

`meta.craft_contract` is 1, and the installer declares the highest value it
understands. A register above that is refused **whole** — not read as far as the
unknown field and installed for the rest — because a field the installer does
not understand is one it will ignore or misapply, and ignoring one silently is
how a rule stops being installed without anybody noticing.

**A consumer does not pin it**, and this is the one number in the picture that
does not appear in the file above. A repository has an opinion about which rules
it runs; it has no opinion about the schema those rules are written in, and a key
that let it express one would let a team ask for a format. The two numbers move
for different reasons — `design.profiles.md` § `craft_contract` is needed — and
only one of them is a choice.

### The installer writes the pin, and only its own key

ADR 0042 describes `.claude/skill-config.yaml` as written once, by hand. For
`lint-md` that is exact: the file is input, and the skill only reads it. Craft's
pin is input *and* the record of a choice made interactively, so somebody has to
write it after the choice, and the alternatives are worse:

- **Leave it to the team.** A choice nobody wrote down is re-asked on every run.
  Worse, it makes ADR 0052's guarantee unverifiable: *nothing changes under a
  repository that is not looking* needs something to compare against, and with no
  pin there is nothing.
- **Write it into the stamp only.** The stamp is in the gated configuration file,
  which is exactly the file a re-run needs to check the stamp *against*. A record
  that is only ever read from the artefact it describes cannot detect a hand edit
  to that artefact.

So `craft-install` writes `craft-install:` — its own key, with the values it was
given or chosen — and nothing else in that file. Another skill's key is not
Craft's to touch, and records that are not values the skill reads back are not
the file's at all: ADR 0042 excluded `deployment-decisions.yaml` from it for that
reason, and the exclusion binds the skill that would benefit from breaking it.

On every later run, a value that came from the file is reported as coming from
the file (ADR 0042 part 4). *`profile: python/strict` (from
`.claude/skill-config.yaml`)* and *`profile: python/strict` (chosen just now)*
are different facts, and the person approving the write has to be able to tell
them apart.

### What this section does not settle

- **The `residue` key's default**, and whether there is one. The residue slice's,
  with the wording.
- **Whether the installer may refuse to run at all** on a repository whose stamp
  shows hand edits, or only report them. Handed here by `design.profiles.md`
  § What a re-run does, and it belongs with the re-run behaviour rather than with
  the file format.
- **Whether the Craft register travels inside the installer or is read from a
  pinned ref.** `craft_contract`'s refusal can only fire in the second case, and
  which case it is, is the packaging slice's.

## What this document still owes

Named so that a reader can tell a gap from an omission. Every row is work rather
than an open question — S4 closed the design questions, and
`design.profiles.md` § What this document still owes is empty because of it.

| Owed | Which box in [`todo.md`](todo.md) |
| --- | --- |
| How the stack is inferred, and what a repository with two of them gets | Infer the stack from the repository |
| What the chooser shows: each level's rules, and what S3 measured each costs to satisfy | Present each applicable profile with what it enables |
| The shape of the explicit yes, and what is shown before it | Require an explicit confirmation |
| What is written, per locus, and the stamp line at each | Write the pinned configuration; record what was written |
| The residue: its file, its default, its wording, and the unenforced label | Emit the judgment-only residue |
| A second run over the installer's own output changing nothing, and what "nothing" covers when a gate has opened since | Make a second run change nothing |
| Packaging, versioning and publication, and where the register sits in it | Version and publish it |
