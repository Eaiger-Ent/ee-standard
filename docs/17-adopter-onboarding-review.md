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

This is the largest gap and everything in § B, § C and § D is downstream of it.

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
- Nothing in the adopter route estimates how long any of it takes, or names the
  point at which the reader can stop and say they are done. § 5's checklist is
  the closest, and it is at the end of a 1,963-line document.

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
4. **When you are done**, and what a `3` means versus a `0`.
5. **When it goes wrong**, pointing at the three failures Phase 4 actually hit.

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

The second row is the one that keeps the first fixed.

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
