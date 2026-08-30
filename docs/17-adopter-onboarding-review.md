# What a junior adopter cannot do today

A review of the adopter-facing surface against one reader: a developer who has
never seen this repository, has a Mac and nothing else, and has been told to make
their team's repository conformant.

**It is a review, not a fix.** Nothing below has been changed. § The doc plan is
what this recommends writing once the findings are agreed.

## How it was checked

Every documented command, path, secret name and URL was read against the source
it derives from rather than against its own prose — the register, `setup.sh`,
the workflows, the plugin's skills and the checker's CLI. Where a command could
be run in this container it was run. Nothing here was built: this container has
no Docker, so anything that only a macOS host with Docker can settle is marked
as such in § What no file check can close.

The surface reviewed is everything the reader touches and nothing else:
`README.md`, [`08-adopting.md`](08-adopting.md),
[`16-marketplace-readoption.md`](16-marketplace-readoption.md), the shipped
template at `plugins/control-register/templates/devcontainer/`, and the
human-facing prose inside the plugin — its `README.md` and each skill's.

## The reader this assumes

Stated because every finding below is relative to it, and a different reader
makes some of them disappear:

- **A Mac, and nothing else.** No Docker, no VS Code, no `gh`, no node, no
  Claude Code, no Homebrew. No GitHub token, no Claude subscription token, no
  admin on the repository they have been pointed at.
- **They arrive through the marketplace.** They never clone this repository, so
  anything true only inside a checkout of `ee-standard` is invisible to them.
- **They are junior.** They will not infer a missing prerequisite from a command
  that fails, and a passage that explains *why* before it says *what to type*
  costs them more than it costs a reviewer.

## A — The adopter route names no prerequisite at all

This is the largest **onboarding** gap and everything in § B, § C and § D is
downstream of it. The largest **conformance** gaps are § J to § M, which are not
about onboarding at all.

[`08-adopting.md`](08-adopting.md) opens at § 0.0 with
`claude plugin marketplace add`, and never states what must already be on the
machine. Grepping the whole guide for `Docker`, `brew`, `npm install -g`,
`VS Code`, an instruction to install Claude Code, or `gh auth login` returns
nothing that installs anything. The tools it goes on to use, in order of first
appearance:

| Tool | First used at | Where the guide says to install it |
| --- | --- | --- |
| `claude` | § 0.0, `claude plugin marketplace add` | Nowhere |
| `git`, `curl` | § 0.1, resolving the tag | Nowhere — present on a Mac, so harmless |
| `gh`, authenticated | § 1, four `gh api` calls | Nowhere. `gh auth login` appears in no adopter document |
| `docker` | § 2.0a, `devcontainer build` | Nowhere |
| `devcontainer` CLI | § 2.0, `devcontainer build --workspace-folder .` | Nowhere |
| `node`/`npm` | implied by the line above | Nowhere |
| VS Code | § 2.1, the whole editor locus | Nowhere |

The install command for the `devcontainer` CLI exists in exactly one place in
this repository — [`06-devcontainer-setup.md`](06-devcontainer-setup.md) § 1,
`npm i -g @devcontainers/cli` — which is the guide for **working on this
repository**, is not linked from the adopter route, and itself does not say
where `npm` comes from.

[`16-marketplace-readoption.md`](16-marketplace-readoption.md) § What the host
must have is the closest thing that exists to a prerequisites table, and it is
written for an operator closing a phase criterion: it lists five requirements
with a *check* for each and an install command for none, and it names a
credential for a private marketplace the adopter does not use.

So the junior's first failure is `claude: command not found`, before the first
fenced block in the guide, and no document tells them what to do about it.

## B — The macOS assumption arrives a quarter of the way in

The guide is macOS-only in fact. It says so at § 2.0, in the paragraph beginning
*"Those three commands are macOS"* — roughly line 470 of 1,963, after the reader
has installed a plugin, done the platform work in § 1, copied a template and
substituted four placeholders.

The passage itself is good and makes the right argument: the failure otherwise
*"arrives before there is a container to read the message in, which is the worst
place a platform assumption can surface"*. The finding is only that the document
does not take its own advice about *where* to say it. A junior on a
company-issued Windows laptop currently spends an hour before learning the route
does not serve them.

## C — § 0.1 asks for an instrument that does not exist yet

§ 0.1 fetches the register and then says, of the verification below it, *"this is
worth doing before anything else"*:

```bash
uv run register-check --repo . --register ./controls.yaml schema
```

At that point in the document the reader has no `uv` and no `register-check`.
§ 2.0a places `uv` inside the container — *"Everything after that goes inside:
`uv`, `register-check`, every gate"* — and § 2.3 is where the checker is
installed, 606 lines later. There is no container yet either; § 2.0 is what
creates one.

The command is correct and the check it makes is a good one (it is what tells a
reader whether they have fetched a register predating a field the skills need).
It is reachable only after § 2.3, and the guide does not say so.

This is the same class of mistake § 2.3 names in its own closing paragraph — *"a
guide that assumed the instrument was present is how the gap went unnoticed for
as long as it did"* — surviving one section above where it was diagnosed.

## D — Three credentials, described in three places, collected in none

The reader needs three distinct credentials, and the guide introduces each where
it is first used rather than where it must be obtained:

| Credential | Needed for | Where the guide mentions it | What it does not say |
| --- | --- | --- | --- |
| Claude Code OAuth token | `initializeCommand`; the container will not start without it | § 2.0, `claude setup-token` | Nothing missing — this one is complete |
| A GitHub token with `Administration: write` | § 1, creating the ruleset | § 1, *"The token you use matters"* | How to create one, or that it must be fine-grained |
| A GitHub token with `Administration: read` | § 4.3, the CI credential | § 4.3 | It is a **different** token from the one above |

The Keychain command in § 2.0 is `security add-generic-password … -w "ghp_..."`.
That prefix is a **classic** personal access token, and SEC-003's
`platform_token_is_not_classic` block fails on the header a classic token
returns. A junior copying the shape of the example is being shown the instrument
the register later rejects. The example is about the reader's own `gh`
convenience rather than about CI, so it is not wrong — but nothing marks the
distinction, and § 4.3 is 1,100 lines away.

Nowhere does one list say: *here are the three credentials, here is where each is
created, here is which scope each needs, here is where each is stored.*

## E — The shipped template README carries the extraction the guide fixed

**This is a defect in a shipped artefact, not a documentation preference.**

[`08-adopting.md`](08-adopting.md) § 2.0 records that its first version of the
uv extraction used `grep -A4`, which *"never reached `version:` because the
register comments that block — so they returned empty, `sed` substituted
nothing, and the placeholders survived into a container that then failed at
`sha256sum -c`"*. The guide was fixed. The template's own README was not:

```text
plugins/control-register/templates/devcontainer/README.md:47
uv_version=$(grep -A4 '^  uv:' controls.yaml | sed -n 's/^ *version: *//p')
uv_sha=$(grep -A4 '^  uv:' controls.yaml | sed -n 's/^ *sha256: *//p')
```

Reproduced in this container against the current register: both assignments are
empty. `tools.uv` carries seven comment lines between `source:` and
`release_repo:`, so four lines of context reaches no value.

`tests/test_devcontainer_placeholders.py` was written for exactly this failure
and does not reach it. It executes § 2.0's commands from the guide — the shape
that makes a documented route a tested one — but its coverage of the template
README is `test_every_placeholder_is_named_in_the_readme`, which checks only
that each placeholder **name** appears in the prose.

Two smaller problems in the same file compound it: it extracts into `uv_sha`
where the guide uses `uv_sha_x86`, and it never shows the `sed` substitution at
all, so a reader who follows only the README has broken extraction and no
instruction to substitute with.

The template README is deleted at the start of § 2.0 (`rm .devcontainer/README.md`),
which limits the blast radius but does not close it: it is read before it is
deleted, and it is the file a reader browsing the plugin cache finds first.

## F — The plugin README names a skill that does not exist and omits one that does

`plugins/control-register/README.md` § Skills lists a `register-check` skill as
*"Phase 3"* and calls it *"the one unbuilt row"*. There is no such skill. The
directory holds nine, and the one that installs the checker is `register-install`
— built, shipped, dispatched by `register-adopt` before its own pre-flight
(ADR 0032), and **absent from that table**.

For the junior, the shipped README says the thing that installs their checker has
not been built yet.

## G — A shipped README reaches the checker off `PATH`

The same file, § Verification:

```text
plugins/control-register/README.md:55
register-check run --control SEC-001
```

§ 2.3 of the adopter guide states the rule and the reason: *"`uv run
register-check`, not `register-check`. A bare name resolves against `PATH` and
would report success against some other copy entirely"* (ADR 0020). The guide
records that this was found by checking its examples rather than only stating the
rule beside them, and `tests/test_adopter_guide.py::test_no_example_reaches_the_checker_off_path`
now holds it — scoped to `docs/08-adopting.md`.

The plugin's README is a shipped artefact, is read by the same person, and no
test reaches it. The rule was fixed in the document that was measured.

## H — The root README says the standard is half-built

`README.md` § Status is the first page a junior lands on. It reports Phase 2 at
*"11 criteria of 12"* and *"**Phase 3 is in progress**"*, and mentions no phase
after it. Every phase through 6 is complete.

Its document table stops at `09-phase-1.5-review.md` — `10` through `16` are
absent, including [`16-marketplace-readoption.md`](16-marketplace-readoption.md).

A reader deciding whether to invest a day in this standard is being shown a
project that stalled in Phase 3.

## I — Smaller inconsistencies

Recorded because they cost a junior confidence rather than time.

- `08-adopting.md` § 0.0 installs with `claude plugin install control-register@ee-standard`;
  `16-marketplace-readoption.md` uses the same command with `--scope user`.
  Neither says whether the scope matters.
- The template README says to regenerate the lock with
  `devcontainer upgrade --workspace-folder .`; `08-adopting.md` § 2.0 says the
  lock is regenerated by a build and gives
  `devcontainer up --workspace-folder . --remove-existing-container`. Both are
  true of different situations and neither says which.
- § 0.1 resolves the newest tag with `sort -V`. Whether the `sort` on a stock
  macOS supports `-V` was not verified here and should be, on a Mac, before it
  is relied on — a silent empty `$tag` produces a `curl` against a URL with an
  empty path segment.
- § 4.5 tells the adopter to copy the sweep from
  `plugins/control-register/templates/sweep/conformance-sweep.yml`. It ships, but
  that is the **authoring repository's** path — the same defect § 2.0 records and
  fixes for the devcontainer template, where both the plugin-cache path and the
  clone path are given. § 4.5 gives only the second.
- Nothing in the adopter route estimates how long any of it takes, or names the
  point at which the reader can stop and say they are done. § 5's checklist is
  the closest, and it is at the end of a 1,963-line document.

## J — Renovate is mandatory in fact and optional in every document

**This is the most severe finding here, and it is not an onboarding gap.** An
adopter who follows every document correctly ends up with a uv pin that nothing
will ever propose an upgrade for, and a green SUP-002 over it.

Five facts, each verified rather than read:

**1. The template guarantees a version literal in a shell script.** After the
§ 2.0 substitution, the adopter's `.devcontainer/setup.sh` line 102 reads
`uv_version="0.12.7"`. That is precisely the case § 1.1 names as the one
Dependabot cannot see: *"Dependabot cannot see a version literal embedded in a
shell script or a workflow step … It has no equivalent of a custom manager."*

**2. Every document presents Renovate as conditional.** § 1.1 opens *"What
satisfies it depends on what your repository pins"*, and § 5's checklist row 5
reads *"Renovate installed, **if** any version is a literal or a toolchain
file"*. The template makes that `if` unconditional for every adopter, and no
document says so. `gate-supply-chain` is the same: *"A repository **may** run
Dependabot for the ecosystems it understands and Renovate for what it cannot
reach"*.

**3. The shipped template carries no `# renovate:` annotation.** This
repository's own `.devcontainer/setup.sh` carries two — line 82 for uv, line 129
for gitleaks. `grep -c 'renovate:'` on the template's `setup.sh` returns `0`. So
an adopter who installs the Renovate app still gets zero matched sites, and
Renovate's Dependency Dashboard — which § 1.1 correctly identifies as *"the only
external evidence the annotations do anything"* — will report nothing missing,
because nothing is declared.

**4. The only config the guide offers matches nothing by construction.** § 1.1
gives one fragment:

```json
{ "enabledManagers": ["custom.regex"] }
```

There is no `customManagers` array in it, so a repository applying exactly that
enables the custom-regex manager and defines no custom manager for it to run.
The plugin ships no `renovate.json` template either — `find plugins -iname
'*renovate*'` returns nothing. The one working example is this repository's own
`renovate.json`, which no adopter is pointed at.

**And copying that file verbatim would still not work.** The two pin sites are
spelled differently, and the difference is load-bearing:

| | Annotation | Pin |
| --- | --- | --- |
| This repository | `# renovate: datasource=pypi depName=uv` | `UV_VERSION=0.12.7` |
| The shipped template | none | `uv_version="{{UV_VERSION}}"` |

This repository's matcher for a pypi literal is
`…depName=(?<depName>\S+)\s+[A-Z_]+=(?<currentValue>\d+\.\d+\.\d+)`. Run
against the template's substituted output it fails three ways: no annotation,
`[A-Z_]+` does not match a lowercase `uv_version`, and the quote sits where the
first digit is expected. Adding the annotation alone is **not** enough —
confirmed by running the expression against all three spellings.

That asymmetry is a second copy that has already drifted. Two consumers read
that pin site — `tool_versions_match_register` and Renovate's regex — and only
the first was taught to tolerate a quote (2026-08-29, per the template's quoted
placeholder). The second was not.

**5. SUP-002 passes throughout.** `dependency_update_config_covers_all_ecosystems`
resolves a Renovate config first, finds a custom-managers-only one does not cover
ecosystems, falls through to `.github/dependabot.yml`, and compares
`package-ecosystem` entries against the ecosystems present. It never asks whether
a `source: literal` tool's `pinned_at` sites are covered by anything.
`gate-supply-chain` writes `.github/dependabot.yml` and stamps it, and the
control is green.

SUP-004 does not catch it either: it checks that each pinned digest is the one
the project published **for that release**, so a pin three versions stale has a
perfectly valid digest.

So the end state for a correct adopter is a repository where the tool *every
verification in this standard runs on* is pinned at whatever version they adopted
at, with nothing proposing a move and two supply-chain controls reporting PASS.
That is theme **T-1** — a stated standard that nothing enforces — on the artefact
this repository ships, and § 1.1's own closing line is the diagnosis: *"A bot's
config file is not a bot. An annotation with no app installed … is a mechanism
that exists on paper and not in fact."* The template has neither.

This repository has already paid for this once. [ADR 0041](adr/0041-a-pinned-digest-is-checked-against-what-was-published.md)
exists because Renovate's uv bump moved the version at all four sites and left
all three digests behind while everything passed. That was the bot working and
the check being wrong; this is the bot never running at all.

## K — `pinned_at` is an allow-list, and the adopter is told to extend it by hand

Both halves of the pin reconciliation iterate **declared** sites and nothing
else:

- `tool_versions_match_register` (SUP-001) —
  `for tool in literal: for path in tool.pinned_at:`
- `tool_digests_match_register` (SUP-004) —
  `files = sorted({path for tool in register.tools.values() for path in tool.pinned_at})`

SUP-004's second direction catches a **stray digest inside a declared site** —
one the register does not name. Neither assert catches a **site the register
does not name at all**. A file that installs a register-pinned tool and is
missing from `pinned_at` is compared by nothing, in either direction, and
reports no verdict.

For this repository that is nearly harmless: the register and the files were
written together. For an adopter it is a live hole, because they are explicitly
instructed to close it by hand. The instruction is a comment inside a shipped
template, `gate-secrets/templates/ci-steps.yaml`:

```text
The version appears twice in the repository once this is written — here and in
the developer environment — which is why the register records those sites in
`tools.{{TOOL}}.pinned_at` and `tool_versions_match_register` fails the build
when one drifts. Add this workflow's path there if it is not already listed.
```

An adopter's gating workflow is not named `register-check.yml`, so the path
almost never *is* already listed. If they miss that line — it is a comment in a
file the gate writes, not a step the gate performs or a prompt they answer —
their gitleaks pin drifts uncompared while SUP-001 and SUP-004 both pass.

This is ADR 0019's own argument, unapplied one level up. That ADR is about
exemptions: *"a map is an allow-list, and what an allow-list leaves out is
invisible."* `pinned_at` is an allow-list with the same property and no
equivalent check. `docs/14-file-map.md` earned a test in **both directions** for
exactly this reason; `pinned_at` has one direction.

Worth noting what the missing direction would have caught here. The comment in
`tool_versions_match_register` records that gitleaks was compared at **no**
locus while the assert reported a pass, and that *"Renovate's own dashboard found
it, by listing five managed sites where the register implies six."* The
instrument that found this repository's version of this bug is the one § J shows
an adopter does not have.

## L — The annotation pattern is applied at one site of three

The standard knows the right shape and writes it in one place. Every site where
an adopter ends up with a version literal, and whether the thing that puts it
there also writes the `# renovate:` annotation that makes it visible to a bot:

| Site | Written by | Literal | Annotation |
| --- | --- | --- | --- |
| the gating workflow, gitleaks | `gate-secrets/templates/ci-steps.yaml` | yes | **yes** |
| `.devcontainer/setup.sh`, uv | the devcontainer template, § 2.0 substitution | yes | **no** |
| `.devcontainer/setup.sh`, gitleaks | `gate-secrets` Step 3.5 | yes | **no** |

Step 3.5 is prose with no template behind it, and it says to *"append an install
block using the same pinned version and checksum Step 1 used"* — version and
checksum, not annotation. So the one gate that demonstrably knows to write an
annotation writes it into the workflow and omits it from the file next door.

And per § J the one that **is** written is inert anyway: `depName={{TOOL_REPO}}`
resolves correctly and matches nothing, because no `renovate.json` an adopter
has defines a custom manager to read it. The standard ships an annotation with
no config and a config fragment with no managers.

## M — The template ships no `.python-version`, and no step creates one

ADR 0027 makes `.python-version` the interpreter's authority, and `tools.python`
declares `source: toolchain` with `toolchain: .python-version`.
`tool_versions_match_register` fails a toolchain-sourced tool whose file git does
not track — *"an untracked one is worse than a drifted pin: every locus falls
back to whatever it would have resolved anyway."*

The shipped template's directory is `.gitignore`, `README.md`, `check-auth.sh`,
`devcontainer-lock.json`, `devcontainer.json`, `fetch-secrets.sh`, `setup.sh`.
There is no `.python-version`, and `setup.sh` runs `uv sync --frozen` without
one.

So every Python adopter fails SUP-001 until they create a file that appears in
no step of the guide. It is not undocumented — checklist row 5a names the
property, and § 2.2 and § 3.7 mention the file in passing — but § 2 never says
*create this file, put this in it*.

This is the **least** severe of the four, and deliberately so: the failure is
loud and immediate rather than a green control over a false property. It is
listed because a junior meets it as a control failing on a file nobody told them
to write, at the point they were expecting their first green run.

## N — The quickstart would not be found by the person it is for

The plan below originally proposed `docs/18-first-adoption.md`. That is the
wrong home, and the reason generalises past this one file.

**A new reader opens `README.md`, and then at most one more file.** They do not
browse a folder, and they do not scan a numbered list for the number that means
*start*. A high number reads as *the eighteenth thing*, which is what somebody
who already knows the repository reaches for.

Three facts, and each is independently enough:

**1. The README routes at line 47.** Before it does, the junior reads
§ The problem — a retrospective on `generate-ee-slides` and a five-row table of
failure themes T-1 to T-5 — and § The approach. That is the argument for the
standard, and it is the right first section for the reader deciding whether to
adopt it. It is the wrong first section for the reader who has already been told
to.

**2. What it routes to is the 1,963-line reference.** The routing line itself is
good — *"**Adopting the standard for your own repository** → `docs/08-adopting.md`"*
— and it points at a specification. Adding a quickstart under `docs/` fixes the
destination and leaves the discovery problem exactly where it was.

**3. The adopter may never see the repository root at all.** They arrive through
`claude plugin install`, and the plugin ships `LICENSE`, `README.md`,
`reference/`, `skills/` and `templates/` — **no `docs/`**. So the only entry
point a marketplace adopter has is `plugins/control-register/README.md`, which
§ F and § G already show is stale and off-`PATH`, and which links to no adoption
route at all. Any link it carries to a quickstart must be an **absolute URL** to
the public repository: a relative one resolves in this tree and dangles in every
installation, which is the constraint [ADR 0036](adr/0036-shared-skill-prose-has-one-home.md)
already records for the shared reference files.

So the quickstart needs three things rather than one: a home a stranger finds, a
first screen in `README.md` that points at it above the argument, and a link
from inside the plugin for the reader who never sees the repository.

## O — There is no synopsis, and no single document to point at

Two questions worth asking of the entry point, and both currently answer *no*.

**Does anything give a working synopsis of how this operates?** `README.md`
explains *why* — § The problem's retrospective and the five failure themes — and
*what* — fifteen controls in a table. It does not explain *how*. Nothing in it
says what a locus is, what runs at commit, at push and in CI, how a gate reaches
a repository, or that everything runs through `uv` inside a container. § The
approach is three bullets of principle, which is the argument rather than the
mechanism.

**Is there a single document that explains it in more detail?** No. There is a
**twelve-row table**, which is the opposite of a single pointer, and its two
"start here" lines route by *audience* rather than by *depth*. A reader who
wants to understand the machine has no row addressed to them.

The closest candidate is [`00-concepts.md`](00-concepts.md), and it declares
itself something else in its second line — *"The vocabulary every other document
in this repo uses"* — then defines nine terms. A glossary is what you consult
once you have a model, not what gives you one.

**The only artefact that synthesises the whole mechanism end to end is
`CLAUDE.md`.** It is 1,014 lines, it is addressed to an agent, and `README.md`
does not link it. `docs/14-file-map.md` is the only file that names it, as
*"the same ground for an agent, plus every decision in force"*. So the most
complete explanation of how this repository works is written for a machine and
is unreachable from the page a person lands on.

**This also breaks the template above, and the fault is mine.** Rule 2 says
*never explain in place — every "because" is a link*. That rule assumes a
destination. With none, it produces a junior executing six steps with no model
of what they are building, which is cargo-culting with good evidence lines. The
rule needs a bounded exception rather than removal, and the template below now
carries one.

**Recommended, in order of value:**

1. **`START-HERE.md` opens with one `## How this works` section**, before the
   steps — around 200 words: the register is one file, everything derives from
   it, a control is verified at every locus it names, a gate is a pinned binary
   and never a model, and the whole thing runs through `uv` in a container. One
   section, explicitly the single exception to rule 2.
2. **README's triage gains a third line** — *Want to understand how it works? →*
   — pointing at whatever answers question two.
3. **`00-concepts.md` gains a short synopsis above its definitions**, and becomes
   the named destination. Not a new numbered document: that would repeat exactly
   the mistake § N diagnoses.

The third is a decision rather than an edit. Turning the vocabulary file into the
explanation changes what that document is for, and every other document opens by
telling the reader to read it first.

## P — Nothing states the benefit, at any of the three doors

§ N asked where the reader arrives. This asks what they read when they get
there, and the answer at all three doors is the mechanism rather than the offer.

**Door 1 — the marketplace listing.** These are the first words about this
project that an adopter ever sees, in a list where they are deciding whether to
install anything at all:

```text
Deploys and verifies the Equal Experts control standard. The register in
controls.yaml defines what conformant means; the gate skills write the
artefacts, and register-check audits them.
```

Three internal nouns — `controls.yaml`, gate skills, `register-check` — and no
benefit. It describes the machine to somebody who does not yet know the machine
exists, and gives no reason to want it.

**Door 2 — the plugin README.** Its first substantive line is *"The authority is
not here."* An accurate and important statement about where the register lives,
and it opens by telling the reader where the thing is not.

**Door 3 — the repository README.** It opens with § The problem: a retrospective
on `generate-ee-slides`, a repository the reader has never heard of, and a
five-row table of failure themes. That is the authors' reason for building this.
It is not the reader's reason for adopting it.

**The benefit already exists in the repository, written well, and filed as an
inventory.** § The register at a glance lists fifteen controls as *properties* —
*"A commit containing a secret cannot reach the remote"*, *"The default branch
requires review and passing checks"*, *"A failing test fails the build"*. Those
are outcomes, and they are the offer. They sit at line 75 under a heading that
presents them as a catalogue of the register's contents.

So this is not a writing job so much as a promotion: the answer is in the file,
below the argument for it.

### The answer, drafted

Offered so the question is settled rather than delegated. Four parts, and the
fourth is what makes the first three credible:

```markdown
**What you get.** Fifteen security and quality properties that actually hold in
your repository, and one command that proves which ones do.

- Secrets cannot reach the remote, and CI carries no long-lived cloud credential
- Dependencies install frozen, updates arrive as reviewable proposals, actions
  are pinned to a SHA, and every pinned digest is checked against what the
  project published
- Lint, types and tests block in the editor, at commit, at push and in CI — the
  same pinned versions at every one
- The default branch requires review and passing checks, verified against what
  GitHub *actually enforces* rather than what a file claims

**Why not a policy document.** A lint workflow can exist, be believed in, and
not be a required check — and nothing about the repository on disk reveals it.
Here one file is the control and everything else derives from it, so the chain
from a rule to a blocked merge is read end to end rather than in pieces nothing
joins.

**What it costs.** A Mac with Docker, admin on the repository, and a plan where
rulesets are available — public, or paid. Most of it you do alone in one
sitting; two steps wait on somebody else, and the document says which and where
to stop.

**Start:** `START-HERE.md`
```

The cost paragraph is not a disclaimer. This repository's whole style is stating
what a thing costs beside what it gives, and an adoption pitch with no cost
reads as one that has not been done.

**It states blocking rather than duration, deliberately.** An earlier draft of
this section said *"a first adoption takes about `<n>`"*, and that number should
not be written. It is dominated by what the document cannot control — waiting
on an org owner to install the Renovate app, a token approval, a first image
pull, whether the repository is already public — so it ranges from a morning to
several days and an average would be true of nobody. Worse, it is a claim with
no check behind it: nothing would re-measure it, and it would rot the way
§ H's status section did. What the reader actually needs is *can I finish this
now, and if not where do I stop* — which is structural, stable, and answerable.

## The doc plan

The deferred question was whether to write something new or restructure
[`08-adopting.md`](08-adopting.md). The findings answer it: **write a new short
document and leave `08-adopting.md` as the reference it is.**

Restructuring it would be wrong. Its density is deliberate and every passage
carries the evidence for its claim — that is what makes it trustworthy for a
reviewer, and it is exactly what a junior cannot read on day one. Two readers,
two documents, one of them deriving from the other.

**Proposed: `START-HERE.md`, at the repository root** — the happy path, and
nothing else. At the root rather than in `docs/`, and named rather than
numbered, for § N's reasons: a stranger finds a root file with an unambiguous
name, and finds nothing by counting to eighteen.

It costs one thing worth knowing in advance. `tests/test_file_map.py` fails a
tracked root entry that `docs/14-file-map.md` does not name, in both directions,
so adding it means adding a row to the map. That is the repository's own
machinery working, not an obstacle — but it is the kind of surprise that stops
an implementation mid-change.

1. **Before you start.** The Mac statement in the first sentence. Every tool in
   § A's table with an install command, and the one check that proves each
   landed. The three credentials from § D in one list, with how to create each
   and which scope it needs.
2. **The five things you will do**, named up front with a rough cost, so the
   reader can see the shape before they are inside it.
3. **The steps**, each one command and one piece of evidence, linking into
   `08-adopting.md` for the reasoning rather than restating it. No passage
   explains a decision; every explanation is a link.
4. **The bots**, as a step rather than a conditional aside — with the
   annotation, a working `renovate.json`, and the Dependency Dashboard count to
   check against. § J is why this cannot be a footnote.
5. **When you are done**, and what a `3` means versus a `0`.
6. **When it goes wrong**, pointing at the three failures Phase 4 actually hit.

It must restate no rule, no version and no path that another file owns — a
quickstart that copies is theme **T-2** with a friendlier tone. Where it needs a
value, it derives it the way § 2.0 does, and the commands it prints should be
executed by a test the way `tests/test_devcontainer_placeholders.py` executes
§ 2.0's.

§ The template below is that plan as a skeleton, so writing it is assembly
rather than discovery.

**And separately, four fixes in place**, which are defects rather than
onboarding:

| Fix | File |
| --- | --- |
| Add a § 0 prerequisites section: both tables from § The template (§ A) | `08-adopting.md` |
| Move the macOS statement to the first screen (§ B) | `08-adopting.md` § 0 |
| Say the schema check waits for § 2.3, or move it there (§ C) | `08-adopting.md` § 0.1 |
| Collect the four credentials in one table where they are obtained (§ D) | `08-adopting.md` § 0 |
| Replace the `grep -A4` extraction, add the `sed` step, align the variable names (§ E) | `plugins/control-register/templates/devcontainer/README.md` |
| Extend the placeholder test to execute the template README's commands, not only the guide's (§ E) | `tests/test_devcontainer_placeholders.py` |
| Drop the `register-check` row, add `register-install`, spell `uv run` (§ F, § G) | `plugins/control-register/README.md` |
| Bring § Status and the document table up to date (§ H) | `README.md` |
| Annotate the uv pin, and settle the spelling the annotation has to match (§ J) | `plugins/control-register/templates/devcontainer/setup.sh` |
| Ship a working `renovate.json` template, or have `gate-supply-chain` write one; replace § 1.1's fragment with a pointer to it (§ J) | the plugin, `08-adopting.md` § 1.1 |
| Write the `# renovate:` annotation beside the gitleaks install, as the CI template already does (§ L) | `gate-secrets` Step 3.5 |
| Make § 2 a step that writes `.python-version`, conditional on the ecosystem (§ M) | `08-adopting.md` § 2 |
| Give the plugin-cache path beside the clone path (§ I) | `08-adopting.md` § 4.5 |
| Lead with what you get, and move § The problem below it (§ P) | `README.md` |
| Replace both descriptions with the offer rather than the mechanism (§ P) | `.claude-plugin/marketplace.json` |
| Put the three-line triage above § The problem (§ N) | `README.md` |
| Link the adoption route absolutely, from the first screen (§ N) | `plugins/control-register/README.md` |

The first four rows are the ones a reader of this review is most likely to
assume `START-HERE.md` makes unnecessary. It does not: `08-adopting.md` stays
the reference, `README.md` links it, every step of the quickstart links into it,
and a reader who lands there directly still meets § C's ordering trap and § B's
buried platform assumption. A quickstart routes around a defect; it does not
repair one.

The row after them is the one that keeps § E fixed.

**§ M's row got narrower once the template was read properly.** It said *ship a
`.python-version`, or make § 2 a step*. Only the second survives: `setup.sh`
branches on `package-lock.json`, `uv.lock` and `poetry.lock`, so the template is
language-agnostic and shipping a `.python-version` would assert a Python
toolchain for a node-only adopter. The step is conditional on the ecosystem.

**§ L's row is a gate release, not an edit.** Annotating the gitleaks install
changes what `gate-secrets` writes, so it bumps
`gates.gate-secrets.contractVersion` from 6 — and by
[ADR 0038](adr/0038-the-stamp-records-the-deployment-contract.md) every existing
`gate-secrets` stamp then reads stale until the gate is re-run. That is the
machinery working rather than a cost to avoid, but it is not in the same class
as correcting a README and should not be bundled with one.

**Two of these are decisions rather than edits**, and neither should be taken
here.

**§ J** — whether SUP-002 ought to fail a repository whose `source: literal`
tools have `pinned_at` sites that no custom manager covers. It would make the
control read a second file, it would fail repositories that are conformant
today, and the alternative — leaving it as guidance — is what produced the
finding.

**§ K** — whether `pinned_at` should be checked in both directions, failing a
repository that installs a register-pinned tool at a site the register does not
name. It is the same fix `docs/14-file-map.md` already has and for the same
reason, and it would fail repositories that are conformant today. Until it
exists, `gate-secrets` telling an adopter to edit their register in a code
comment is the weakest link in the supply-chain chain.

Both have an ADR's shape. Raise them; do not decide either in a documentation
change. § The four decisions states them, and the other two, with the options
and what each costs.

## The template

The skeleton for `START-HERE.md`, with the research from § A, § D and § J
already filled in. Everything in angle brackets is a blank to fill;
everything else is the shape to keep.

### The five rules it is written to

Stated first because they are what makes it short, and a reviewer should be able
to reject a passage by pointing at one of them.

1. **One reader.** The junior in § The reader this assumes. Anyone who wants to
   know *why* is a different reader and is served by a link.
2. **Never explain in place, with one exception.** Every "because" is a link
   into [`08-adopting.md`](08-adopting.md); if a passage cannot be replaced by
   a link, it is a step and belongs in a step block. The exception is
   § How this works, once, at the top — § O is why it exists and why it is
   bounded to one section. A second explanatory section is the rule failing.
3. **No value that another file owns.** No version, no digest, no tag, no
   ruleset name. Derive it or link to it. A quickstart that copies is theme
   **T-2** with a friendlier tone.
4. **Every step ends in evidence.** Not "run this" — "run this, and you should
   see that". A step with no observable outcome is a step a junior cannot tell
   they have finished.
5. **Nothing is conditional that the template makes unconditional.** § J is the
   whole reason this rule is here.

### The repeating unit

Every numbered step is exactly this, and a step that needs more than this is two
steps:

````markdown
### N — <imperative, five words or fewer>

<One sentence. What this does, not why.>

```bash
<the commands, copy-pasteable as a block, no placeholders to think about>
```

**Done when:** <the one observable thing. A verdict, a file, a returned list.>

**If it fails:** <only failures that have actually happened. Each one sentence.>

**Why this exists:** [`08-adopting.md` § <n>](08-adopting.md#<anchor>)
````

Four lines of scaffolding around one block of commands. A step whose **Done
when** cannot be written in one line is not understood well enough to be written
at all.

### The skeleton

```markdown
# Start here

<One paragraph: who this is for, and what they will have at the end **named
concretely** — not "a conformant repository" but the four outcomes from § P.
State the macOS assumption in the first sentence — § B. No duration — § P.>

## How this works

<Around 200 words, and the only explanatory section in the file — § O. It needs
to leave the reader able to answer: what is the register, why does everything
else derive from it, what is a locus, what actually blocks a merge, and what
runs where. Ends with one link to the fuller explanation. No history, no
retrospective, no failure themes — the argument for the standard is README's
job and this reader has already been sent here.>

## Before you start

### What this assumes

<macOS + Docker, said plainly. One sentence on what a Linux or Windows reader
should do instead, linking to 08-adopting.md § 2.0's contract for a replacement
fetch-secrets.sh. Do not restate that contract.>

### Install these

| Tool | Install | You have it when |
| --- | --- | --- |
| Homebrew | <brew.sh> | `brew --version` |
| Docker Desktop | <cask or download> | `docker info` succeeds |
| VS Code | <cask> | `code --version` |
| node and npm | <cask or brew> | `npm --version` |
| `devcontainer` CLI | `npm i -g @devcontainers/cli` | `devcontainer --version` |
| GitHub CLI | <brew>, then `gh auth login` | `gh auth status` |
| Claude Code | <https://docs.claude.com/en/docs/claude-code/setup> | `claude --version` |

### Get these credentials

| What | Where you make it | Scope it needs | Where it goes |
| --- | --- | --- | --- |
| Claude Code OAuth token | `claude setup-token` | — | Keychain, `CLAUDE_OAUTH_TOKEN` |
| A token for `gh` (optional) | <settings page> | read on the repo | Keychain, `GITHUB_TOKEN` |
| An admin token | <settings page> | `Administration: write` | used once, not stored |
| The CI token | <settings page> | `Administration: read` | an environment secret — 08 § 4.3 |

<One line on the classic-vs-fine-grained trap from § D: the `ghp_` shape in the
Keychain example is a classic token, and SEC-003 rejects one in CI. Say which of
the four rows may be classic and which may not.>

## What you are about to do

<A six-row table: the step, whether it needs anyone but you, and whether you can
stop after it. Not how long — see § P. Two rows need somebody else (an admin for
the ruleset, an org owner for the Renovate app) and saying so up front is what
lets a reader start today instead of discovering it at step 3.>

## 1 — Install the plugin
## 2 — Get the register
## 3 — The steps only you can do
## 4 — The container
## 5 — Run the adoption
## 6 — Turn the bots on

<Each one is the repeating unit above. Nothing else.>

## You are done when

<The checklist, but only the rows a first adoption reaches. Say plainly that
exit 3 without a platform token is the expected first success and not a
failure, and that turning on --require-complete is a second sitting with its
own order — link 08 § 4.2 and § 4.3, do not restate the order.>

## When it goes wrong

<Only failures that have actually happened. The three from Phase 4, plus the
uv-placeholder one from § E. Each: symptom, one-line cause, fix.>
```

### What each step must contain

The parts the writer would otherwise have to rediscover. This is the output of
the review, not a suggestion:

| Step | Must contain | From |
| --- | --- | --- |
| Before you start | Every row of both tables above, each with a check that proves it | § A, § D |
| 1 — the plugin | The marketplace add and install, and the cache path, since step 4 copies out of it | § I on `--scope` |
| 2 — the register | The tag resolution, and **a note that the schema check waits until step 5** | § C |
| 3 — platform | Visibility, ruleset, push protection. Each with its `gh` verification | § 1 |
| 4 — the container | Copy, delete the README **first**, substitute, build. The substitution commands must be the working ones | § E |
| 5 — the adoption | `claude --permission-mode acceptEdits`, then `/register-adopt`. Say the sensitive-file prompt is expected | § 0 |
| 6 — the bots | Dependabot **and** Renovate, as a step and never a conditional. The annotation, a working config, the dashboard count | § J, § L |
| You are done when | Exit `3` is the expected first success | § 0 |

Step 6 is the one most likely to be written as an aside, and § J is what happens
when it is. It is a numbered step with the same weight as the container.

### How it is reached

Three edits, and the document is worth nothing without them — § N.

| Edit | What it says |
| --- | --- |
| `README.md`, above § The problem | Three lines. *Adopting this into your repository? → `START-HERE.md`. Working on this repository? → `docs/06-devcontainer-setup.md`. Want to know how it works? → `docs/00-concepts.md`.* Nothing else moves — § N, § O |
| `plugins/control-register/README.md` | An **absolute** link to `START-HERE.md` on the public repository, in the first screen. Relative dangles in every installation |
| `docs/14-file-map.md` | A row for the new root entry, or `tests/test_file_map.py` fails the build |

The README edit is three lines and is the highest-value change in this review. It
is worth doing whether or not `START-HERE.md` is ever written, pointed at
`docs/08-adopting.md` in the meantime.

### What must be executed, not typed

The guide has a working pattern for this and the new document should use it from
the first commit rather than earning it later. `tests/test_devcontainer_placeholders.py`
extracts the fenced commands from `08-adopting.md` § 2.0 and **runs them**,
because a reimplementation in a test is a second copy free to keep working after
the documented commands have stopped.

At minimum, a `tests/test_start_here.py` should hold:

- Every fenced `bash` block that extracts a value from the register runs, and
  yields a non-empty result. This is § E's defect, and the reason it is first.
- No fenced block reaches the checker off `PATH` — the check
  `tests/test_adopter_guide.py` already has, pointed at the new file. Both files
  should share it rather than each carrying a copy.
- Every tool named in the prerequisites table has both an install cell and a
  check cell, neither empty. A table with a blank is how § A happened.
- The document names no version, digest or tag literally. The inverse of
  `tests/test_plugin.py`'s rule for `plugins/`.

### Link, never restate, another project's install

The prerequisites table gives a `brew` line where one is short and stable, and a
**link** for Claude Code and Docker Desktop. That is not laziness about the two
hardest rows — it is the same rule as everything else here. An install command
copied out of another project's documentation is a second copy of a fact that
project owns, free to drift the day they change it, and it would sit in a table
nobody re-checks. Theme **T-2**, with the drift outside this repository's control
entirely.

So the row says *what they need* and *where the instructions live*, and never
*how*. `https://docs.claude.com/en/docs/claude-code/setup` resolves, as does
`claude.com/claude-code`; both were checked on 2026-08-30, which is the standard
the register already holds every citation to.

### What the writer cannot settle from here

One item, down from two. Whether `sort -V` behaves on a stock macOS (§ I) is a
fact about a machine this container is not. It is also avoidable rather than
merely unverified: § 0.1 uses it to pick the newest tag, and the newest tag can
be read without sorting at all. Note that
`https://api.github.com/repos/Eaiger-Ent/ee-standard/releases/latest` returns
**404** — this repository has tags and no GitHub *Releases* — so `gh release
view` and any "latest release" idiom fail here and are not the replacement.
Either verify `sort -V` on a Mac or replace the resolution with something that
does not sort.

## The four decisions

Written out because a fix table row saying *settle the spelling* is not something
anybody can answer. Each is: what is true now, what is broken, the question, and
what each answer costs.

### Decision 1 — how the uv pin is spelled in the shipped template

**Today.** Two files pin uv and they are spelled differently:

| File | Line |
| --- | --- |
| this repository's `.devcontainer/setup.sh` | `UV_VERSION=0.12.7`, under a `# renovate:` annotation |
| the shipped template's `setup.sh` | `uv_version="{{UV_VERSION}}"`, with no annotation |

Renovate finds a version literal by regex, and this repository's requires
`[A-Z_]+=` followed immediately by a digit. The template's line matches on
neither count — lowercase, and a quote where the digit is expected — so it is
invisible to the bot (§ J).

**The quotes are not in play.** They arrived in an upstream `shellcheck-clean`
commit, and `tool_versions_match_register` was taught to accept an optional quote
on 2026-08-29 rather than the template being unquoted. Removing them now would
regress a lint fix to satisfy a regex.

**So the question is only the case**, and there are two ways to close it:

| Option | Change | Cost |
| --- | --- | --- |
| **A** — uppercase the template | `UV_VERSION="{{UV_VERSION}}"` in the template's `setup.sh` | A shipped artefact changes. One repository has already adopted the old spelling and would drift from the template until re-copied |
| **B** — widen the regex | `[A-Za-z_]+` in the `renovate.json` this repository ships as an example | Every adopter's config carries a looser pattern, matching more things than intended. Harder to read, and it is a config nobody ships yet |

**Recommendation: A.** The template is the thing being fixed, one adopter is a
cheap migration, and B widens a pattern in a file that does not exist yet to
accommodate a spelling we control.

**Question: A or B?**

### Decision 2 — should SUP-002 fail a pin that no bot covers?

**Today.** SUP-002 says *dependency updates are proposed automatically*. Its
check reads `.github/dependabot.yml` and asks whether it covers the package
ecosystems present. It never asks whether a version literal in a shell script is
covered by a Renovate custom manager, because nothing in the register connects
`source: literal` tools to a bot.

**What that permits.** An adopter with a correct `dependabot.yml` passes SUP-002
while the uv their entire toolchain runs on is pinned forever, unproposed. That
is § J's end state, and it is the theme this repository exists to prevent —
enforcement claimed, not performed.

| Option | Behaviour | Cost |
| --- | --- | --- |
| **A** — fail it | SUP-002 fails when a `source: literal` tool has a `pinned_at` site no custom manager matches | Repositories conformant today start failing, including this one until the template and `renovate.json` land. The check must parse `renovate.json` and match regexes against files — real machinery, and a `blocking` Tier-1 control is a hard place to put it |
| **B** — report it | `register-check deployments` lists uncovered literal pins; no control fails | Nothing breaks, the report has a natural home, and it is a recommendation people can ignore — which is what staleness reporting already accepts |
| **C** — leave it | Guidance in `08-adopting.md` § 1.1 only | § J recurs for every adopter, and the guidance is already there and already did not work |

**Recommendation: B, then A later.** B closes the invisibility without a flag day
and gives the evidence for whether A is worth its machinery. C is what produced
the finding.

**Question: A, B or C?**

### Decision 3 — is `pinned_at` checked in both directions?

**Today.** `tools.<tool>.pinned_at` lists the files that repeat a tool's version.
Both reconciliation checks iterate that list. A file that installs a
register-pinned tool and is **not** in the list is compared by nothing (§ K).

**Why it bites an adopter and not this repository.** Here the register and the
files were written together. An adopter is told to add their own workflow's path
by hand — in a comment inside a template `gate-secrets` writes — and their
workflow is not named `register-check.yml`, so it is never already listed.

| Option | Behaviour | Cost |
| --- | --- | --- |
| **A** — scan for strays | The checker looks for files that install a register-pinned tool and are not in `pinned_at`, and fails them | Needs a heuristic for *installs this tool*, and a heuristic false-positives: a changelog quoting `gitleaks 8.30.1` is not a pin. A false failure on a Tier-1 blocking control is expensive |
| **B** — make the gate do it | `gate-secrets` **edits the register's `pinned_at`** when it writes an install into a new file, instead of leaving a comment asking the human to | No heuristic and no false positives; the gate knows exactly which file it just wrote. But a gate writing into `controls.yaml` is new — gates write artefacts, and the register is the thing they read |
| **C** — leave it | The comment stays | The allow-list keeps the invisibility [ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md) names, one level up from exemptions |

**Recommendation: B.** It removes the human step that fails rather than making a
checker guess at what a human meant. Whether a gate may write to the register is
the real question inside it, and that is an ADR.

**Question: A, B or C — and if B, is a gate allowed to edit `controls.yaml`?**

### Decision 4 — where the "how it works" explanation lives

**Today.** No single document explains the mechanism. `00-concepts.md` calls
itself a vocabulary in its second line and defines nine terms. The only end-to-end
synthesis is `CLAUDE.md` — 1,014 lines, addressed to an agent, unlinked from
`README.md` (§ O).

| Option | Change | Cost |
| --- | --- | --- |
| **A** — a synopsis atop `00-concepts.md` | Add a short *how this fits together* section above the definitions; README's third triage line points there | Changes what that document is for. Every other document opens by telling the reader to read it first *for vocabulary* |
| **B** — a new document | A short `HOW-IT-WORKS.md`, at the root beside `START-HERE.md` | A tenth root-level entry and another file to keep true. § N's objection to numbering does not apply at the root |
| **C** — `START-HERE.md` only | Its one `## How this works` section is the whole answer; deeper readers get `00-concepts.md` as it is | Cheapest. A reader who wants the model but is not adopting has nowhere addressed to them |

**Recommendation: A.** The content mostly exists and is in the right file; what
is missing is a paragraph above it saying how the nine terms relate. B adds a
file that would drift from the concepts it summarises.

**Question: A, B or C?**

## What no file check can close

This container has no Docker, so three things in this review are read rather
than run, and a macOS host with Docker is what settles them:

- Whether the prerequisites in § A are **complete** — the only proof is a Mac
  with none of them installed, following the new document to a container that
  creates.
- Whether `sort -V` behaves on a stock macOS (§ I).
- Whether the corrected template README extraction produces a container that
  passes `sha256sum -c`. The commands can be executed by a test; the build
  cannot, which is the same boundary
  [`16-marketplace-readoption.md`](16-marketplace-readoption.md) draws for the
  template itself.
