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

## The doc plan

The deferred question was whether to write something new or restructure
[`08-adopting.md`](08-adopting.md). The findings answer it: **write a new short
document and leave `08-adopting.md` as the reference it is.**

Restructuring it would be wrong. Its density is deliberate and every passage
carries the evidence for its claim — that is what makes it trustworthy for a
reviewer, and it is exactly what a junior cannot read on day one. Two readers,
two documents, one of them deriving from the other.

**Proposed: `docs/17-first-adoption.md`** — the happy path, and nothing else.

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

**And separately, four fixes in place**, which are defects rather than
onboarding:

| Fix | File |
| --- | --- |
| Replace the `grep -A4` extraction, add the `sed` step, align the variable names (§ E) | `plugins/control-register/templates/devcontainer/README.md` |
| Extend the placeholder test to execute the template README's commands, not only the guide's (§ E) | `tests/test_devcontainer_placeholders.py` |
| Drop the `register-check` row, add `register-install`, spell `uv run` (§ F, § G) | `plugins/control-register/README.md` |
| Bring § Status and the document table up to date (§ H) | `README.md` |
| Annotate the uv pin, and settle the spelling the annotation has to match (§ J) | `plugins/control-register/templates/devcontainer/setup.sh` |
| Ship a working `renovate.json` template, or have `gate-supply-chain` write one; replace § 1.1's fragment with a pointer to it (§ J) | the plugin, `08-adopting.md` § 1.1 |
| Write the `# renovate:` annotation beside the gitleaks install, as the CI template already does (§ L) | `gate-secrets` Step 3.5 |
| Ship a `.python-version`, or make § 2 a step that writes one (§ M) | the devcontainer template, `08-adopting.md` § 2 |
| Give the plugin-cache path beside the clone path (§ I) | `08-adopting.md` § 4.5 |

The second row is the one that keeps the first fixed.

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
change.

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
