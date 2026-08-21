# Adopting the standard

For someone who did not author this repository and wants their own repository to
satisfy it. Start here; the other documents are specifications, and you should
not have to read a specification to get started.

**What this covers that nothing else does: the steps no tool can take for you.**
Most of conformance is machinery — a checker, a devcontainer, a family of gate
skills. But several Tier-1 controls rest on *account and platform state*: who
owns the repository, whether a bot is installed, whether a branch is protected.
No skill can install a GitHub App on your organisation. Those steps are the ones
that get discovered late and cost the most, so they come first here.

## Status — what exists today

Read this table before following anything below it. A guide that describes
tooling which does not exist is the failure this repository was written to
prevent, so the gaps are stated rather than glossed.

| Part | State | Where it is |
| --- | --- | --- |
| The register — what "conformant" means | **Exists** | `controls.yaml` |
| `standard-check` — the checker | **Exists** | `src/standard_check/`, run with `uv run standard-check` |
| Platform prerequisites (this document, § 1) | **Exists**, manual | Below |
| A devcontainer you can copy | **Exists** for this repo; the generalised template is Phase 2 | `.devcontainer/` |
| `gate-secrets` — deploys SEC-001, checks SEC-002 | **Exists** | `plugins/ee-standard/skills/gate-secrets/` |
| `gate-quality` — deploys LNT-001, TYP-001, TST-001 | **Exists** | `plugins/ee-standard/skills/gate-quality/` |
| The other four `gate-*` skills | **Phase 2 — not built** | `docs/02-skill-family.md` |
| `standard-adopt` — one command to deploy everything | **Phase 2 — not built** | `docs/02-skill-family.md` |
| `kind: remote` verification of platform state | **Phase 3 — not built** | Reports `SKIPPED (no credentials)` |

So today, adoption is: do § 1 by hand, copy the devcontainer, run
`/gate-secrets` for the secrets gate and `/gate-quality` for the lint, type and
test gates, wire the remaining gates by hand using this repository as the worked
example, and run the checker. When Phase 2 finishes, most of § 2 and § 3 becomes
one command.

## 0 — The front door

`/standard-adopt` is the only entry point you need. It reads the register, works
out which controls apply to **your** repository from its files, shows a plan,
dispatches the gates in dependency order, verifies through the checker, and
commits.

```bash
/standard-adopt --repo . --register ./controls.yaml
```

Everything in the sections below is either a step it takes for you, or a step it
tells you that you owe. Read § 1 first anyway: those are the acts no skill can
take, and a plan that reaches them is a plan waiting on you.

**What it will not do.** It writes no gate configuration itself — every artefact
is written by the gate that owns the control, which is what keeps one control's
config in one place. It will not commit on a failed verify. And it will not
report exit `3` as a pass: SEC-001's and CI-001's remote blocks report
`SKIPPED (no credentials)` until Phase 3, so `3` is the expected result today
and the skill names which blocks were skipped rather than rounding up.

**One confirmation, and one exception.** It asks once, covering the whole plan.
`gate-repo` asks **again** on its own, and that is right rather than redundant:
the plan covers what will be written to files, and a GitHub API call is not a
file. Its ruleset is in force the moment the call returns, for everyone with
access.

**A control is never silently absent from the plan.** Four rows cover every
control in the register — *deploy*, *dispatch elsewhere* (DOC-001 is `lint-md`'s,
in another plugin), *checked, not deployed* (SEC-002 is satisfied by a workflow
**not** referencing a static credential, so there is nothing to write), and
*manual*. A control missing from the plan would read as one that does not apply.

If you would rather deploy one gate at a time, each works standalone — § 3.1 to
§ 3.6. `standard-adopt` exists to save you knowing which.

## 1 — Platform state: what only a human with admin can do

None of this is code, none of it is in a pull request, and all of it is invisible
to a `git clone`. Each row names the control it satisfies, the act, and — the
part usually missing from instructions — **how you know it worked**.

| Control | What you must do | How you know it worked |
| --- | --- | --- |
| CI-001, SEC-001 | The repository must be **public**, or on a plan whose rulesets and secret scanning are available to private repositories | `gh api repos/OWNER/REPO/rulesets` returns a list. A `403 "Upgrade to GitHub Pro or make this repository public"` means neither condition holds |
| CI-001 | Create a **default-branch ruleset** requiring a pull request and passing status checks, with no bypass actors | `gh api repos/OWNER/REPO/rulesets --jq '.[].name'` names it, and `gh api repos/OWNER/REPO/branches/BRANCH --jq .protected` is `true` — note that is the *branch* endpoint; the repository object has no such field. Then try a direct push to the default branch and watch it be refused: a ruleset nobody has seen refuse anything is not known to work |
| SEC-001 | Enable **secret scanning push protection** | `gh api repos/OWNER/REPO --jq '.security_and_analysis.secret_scanning_push_protection.status'` is `enabled`. A `null` `security_and_analysis` means the plan does not offer it, or your token cannot see it |
| SUP-002 | Install a bot that proposes dependency updates, and configure it — see § 1.1 | Its first proposal, or its dashboard. Not the presence of a config file |

**The token you use matters.** Creating a ruleset needs a token with
`Administration: write` on the repository. An ordinary `GITHUB_TOKEN`, and most
fine-grained PATs, do not have it — this repository's own ruleset was blocked on
exactly that for a day. Check before you plan around it:

```bash
gh api repos/OWNER/REPO/rulesets --method POST --input /dev/null 2>&1 | head -2
```

A `403` on write with a `200` on read is a permission problem, not a syntax one.

### 1.1 — Dependency updates need a bot, and possibly two

SUP-002 says dependency updates are proposed automatically. What satisfies it
depends on what your repository pins.

**Dependabot** covers package ecosystems it recognises — npm, pip/uv, Go
modules, GitHub Actions, devcontainer features. It is configured by committing
`.github/dependabot.yml`; no installation is required. Cover every ecosystem the
repository actually has, not just the obvious one.

**Dependabot cannot see a version literal embedded in a shell script or a
workflow step.** If you pin a tool with `TOOL_VERSION=1.2.3` in a setup script,
or `pip install uv==0.12.5` in a workflow, nothing proposes an upgrade for it and
the version quietly ages. It has no equivalent of a custom manager.

**Renovate** fills exactly that gap, via custom managers that read an annotation
above each literal:

```bash
# renovate: datasource=github-releases depName=gitleaks/gitleaks
GITLEAKS_VERSION=8.30.1
```

Renovate is a **GitHub App**, so it must be installed through the web at
<https://github.com/apps/renovate> — onto the organisation or the single
repository. No token can do this for you, which is why it belongs in this section
rather than in a script.

If you run both bots, narrow Renovate to the gap so they do not duplicate each
other:

```json
{ "enabledManagers": ["custom.regex"] }
```

Four things about Renovate cost this repository time. They are cheap to avoid
and expensive to rediscover:

1. **Renovate reads its config from the default branch.** While `renovate.json`
   sits on a feature branch, Renovate sees an unconfigured repository — your
   config is not merely inactive, it is invisible.
2. **It will open an onboarding pull request** titled *"Configure Renovate"*,
   carrying a **default** config that enables every manager. Merging it installs
   the opposite of a narrowed config. Leave it alone: once your real config
   reaches the default branch, Renovate closes that PR itself.
3. **Do not close the onboarding PR unmerged.** That is Renovate's signal to
   disable itself on the repository.
4. **Check the Dependency Dashboard issue it creates.** It lists how many sites
   each manager matched. That count is the only external evidence the
   annotations do anything, and it is worth deriving the expected number from
   your own config and asserting it in a test — this repository found a missing
   annotation, and behind it a genuine verification defect, purely because the
   dashboard said five where six was expected.

**A bot's config file is not a bot.** An annotation with no app installed, or a
`renovate.json` on an unmerged branch, is a mechanism that exists on paper and
not in fact. Verify by looking for a proposal or a dashboard, never by looking
for a file.

## 2 — The development environment

### 2.0 — Where the devcontainer comes from

A conformant `.devcontainer/` ships with the plugin, at
`plugins/ee-standard/templates/devcontainer/`. Copy it, replace the
double-brace placeholders — `grep -rl '{{' .devcontainer` lists them — and run
`/gate-build` to pin what you chose and stamp it.

**Why it ships here rather than as a template repository.** `project-init` has
one stated precondition: `.devcontainer/devcontainer.json` must already exist,
and its guidance when it does not is *"clone the template repo or add the file
manually"*. That template repo is private, so anyone whose access lapses loses
the ability to start a project. A directory in the plugin is obtainable by
anyone who can install the plugin.

**What the template pins**: the image by digest, and every feature by digest in
`devcontainer-lock.json`. **What it refuses to pin**: any tool version inside
`setup.sh`. That is Phase 2's own exit criterion — *the template pins no tool
version by hand; every tool it installs is either sourced from a lockfile the
consumer repo already commits, or from a single toolchain file*. A template
scattering pins through a shell script reproduces that problem in every
repository that adopts the standard, and you have no
`tool_versions_match_register` of your own until you adopt the register too.

So `setup.sh` installs only from lockfiles you commit. Scanners, linters and
analysers are installed by the gates that own their controls, each writing its
own stamped region into that file.

**Two lines that must survive the copy.** The template's own `.gitignore` names
`.env` and `.env.docker`, and SEC-001 depends on them. Deleting it does not fail
a build; it fails quietly, later, in someone else's clone — and a secret that
reaches a remote is not undone by removing it.

**How you know it worked**, in this order:

```bash
grep -rl '{{' .devcontainer          # expect no output
devcontainer build --workspace-folder .
standard-check run --control BLD-001 --control DEV-001
```

A fresh copy fails the loci and stamp blocks of both controls, which is correct:
`gate-build` has not run yet. It should pass `devcontainer_user_is_non_root`,
`devcontainer_image_digest_pinned` and `devcontainer_lock_covers_all_features`
from the first line.

Copy `.devcontainer/` from this repository as the worked example. Its operator
guide is [`06-devcontainer-setup.md`](06-devcontainer-setup.md); the
specification the shipped template will meet is
[`03-devcontainer.md`](03-devcontainer.md).

What matters when you adapt it:

- **Pin the image by `@sha256:` digest**, not by tag. A tag moves.
- **Commit `devcontainer-lock.json`, covering every feature.** A lock file that
  covers three of four features reads as solved and is not.
- **State the user.** `remoteUser` or `containerUser`, and not root. A
  devcontainer naming neither runs as whatever its base image happens to use,
  which may change under you on any digest bump (BLD-001).
- **Install nothing unpinned and nothing unverified.** A version-pinned download
  whose checksum you verify beats a devcontainer feature that fetches a release
  without verifying it — and most community features do not verify. See the
  preference ladder in [`03-devcontainer.md`](03-devcontainer.md), which was
  corrected for exactly this reason: a lock file pins the *installer's* digest,
  not the artefact that installer fetches.
- **Keep secrets out of the repository.** This repo's `.env` — and the
  `.env.docker` derived from it for `--env-file` — are gitignored and populated
  from the host keychain by `fetch-secrets.sh`. SEC-001 depends on those lines
  staying in `.gitignore`, so a second secrets file means a second line.

## 3 — The gates

All six gates are built — see § 3.1 to § 3.6. For the rest, until Phase 2
ships them, wire the gates by copying this repository's own artefacts, which are
the reference implementation:

| Locus | File here | What it gives you |
| --- | --- | --- |
| editor | `.devcontainer/devcontainer.json` → `customizations.vscode.extensions` | The same rules while you type |
| editor | `.claude/hooks/md-lint.py` | Lint on write, via a PostToolUse hook |
| pre-commit | `.pre-commit-config.yaml` | The same rules before a commit |
| ci | `.github/workflows/lint.yml`, `.github/workflows/standard-check.yml` | The same rules before a merge |

The discipline is **pin once, reference many**: the same tool version and the
same configuration at every locus. Where a package manager can own a version, let
it — `package-lock.json` pins `markdownlint-cli2` here, so there is no version to
keep in step.

**Invoke the artefact, not the name.** Every locus here runs
`node_modules/.bin/markdownlint-cli2`, because `npx --no-install` does *not* mean
"resolve locally" — with no local install it falls through to `PATH` and runs
whatever global it finds, which makes the lockfile an authority in name only
([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)). The register
records that path as `tools.<tool>.invocation` and the checker holds every locus
to it. A missing local install is then `UNCLASSIFIED — cannot verify`, which is
the honest answer, rather than a pass earned by a binary nobody pinned.

### 3.1 — `gate-secrets`, and what it needs from you first

`/gate-secrets` wires SEC-001 at both its local loci and checks SEC-002. It
takes `--repo` and `--register`, the same two flags as `standard-check`, so a
deployment and its audit cannot be pointed at different things by accident.

**Three prerequisites, and how you know each is met.**

| Prerequisite | Why | How you know it worked |
| --- | --- | --- |
| A register the skill can read | Every value it writes — the scanner's name, version, checksum and release repository — comes from `controls.yaml`. There is no default, because a default is a decision nobody recorded | `standard-check --repo . --register <path> explain SEC-001` prints the control |
| `tools.<scanner>.release_repo` set in your register | The skill downloads a pinned release and needs `owner/name`. Before Phase 2 this value existed only inside a `# renovate: depName=` comment, which is an annotation for a bot rather than a field anything can read | `standard-check schema` accepts the register; a malformed value is rejected as *must be an owner/name repository reference* |
| A workflow that runs on `push` or `pull_request` | A workflow triggered only by `workflow_dispatch` runs when a human clicks it, and a control reachable only that way is declared and unreachable | The verify step reports `ci locus — no gating step runs '<scanner>'` if you have none |

**Expect exit `3`, not `0`, and read it as a result rather than a problem.**
SEC-001's remote block — GitHub secret scanning push protection — reports
`SKIPPED (no credentials)` until Phase 3. The two local loci are verified; the
remote one is not, and is not claimed. Enabling push protection is the platform
act in § 1 that only an admin can take.

**Two ways an adopter who already had SEC-001 passing can now fail it.**

1. **The CI locus is checked.** SEC-001 declares three loci and, before Phase 2,
   only the pre-commit hook was read — a repository could delete its
   secret-scanning job and stay green. If your scanner runs only at pre-commit,
   SEC-001 now fails naming the ci locus. That is the check working.
2. **Your ignore file is judged by what it hides.** An entry whose fingerprint
   names a file **git tracks** hides authored content from a control with
   `variance: forbidden` and `baseline: null`, and fails
   ([ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md)). An entry
   naming a path git does not track — a vendored directory, a fixture outside
   the repository's own content — scopes the scanner and is fine. Deal with what
   the first kind was hiding; do not move it somewhere quieter.

**Wiring by hand instead?** Then stamp what you write. SEC-001's verify reads
back a provenance stamp naming SEC-001 and the gate that deploys it, so a
hand-wired hook with no stamp fails. Say in the stamp's comment that it was adopted rather than
deployed — this repository's own two artefacts do exactly that, because they
were written in Phase 0.5 before there was a gate to write them, and a stamp
claiming otherwise would be a record of something that did not happen.

### 3.2 — `gate-quality`, and the three controls it deploys together

`/gate-quality` wires LNT-001, TYP-001 and TST-001. Three controls and one skill
because they share two files: a pre-commit config and a gating workflow. Three
separate skills writing those in turn would each rewrite what the last one
wrote, which is why gates are grouped by the artefact they write.

**Five prerequisites, and how you know each is met.**

| Prerequisite | Why | How you know it worked |
| --- | --- | --- |
| A `stacks:` entry for every stack you are in | The linter, the type checker, their config locations, the strictness key and the editor extension all come from there. There is no default | `standard-check explain LNT-001` prints the control; `standard-check run --control LNT-001` names your stack in its message |
| Each gate's `invocation` reaches the artefact your lockfile pins | That string is what the skill writes at every locus. A bare tool name resolves from `PATH`, so the deployed gate runs whatever global is installed rather than the pinned version ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)) | The skill stops before writing anything and says which invocation is bare |
| A CI job that installs from the lockfile before these steps | Lint, type check and tests run the tools that install placed. A lint step before the install lints against nothing | SUP-001 passing, and the three steps sitting after the install step in the same job |
| A test command the register accepts for your ecosystem | `ecosystems.<name>.test_commands` bounds the set; your repository picks the member. The skill asks rather than choosing | `standard-check run --control TST-001` reports the command runs and its exit code is the verdict |
| An `ecosystem:` on your stack, and an `add_dev_dependency` for the lockfile you use | The gate has to be able to create a pin that is missing. `uv add --dev` and `poetry add --group dev` are both python, so the register says which one your repository uses | The schema rejects a register whose stack names an ecosystem that does not cover every lockfile it declares — `standard-check schema` names the field |

**Expect exit `0` here, unlike `gate-secrets`.** All three controls verify from
files and none declares a `remote` locus, so nothing is waiting on Phase 3. A
`3` means a block declared itself partial — read which, rather than rounding up.

**Four ways an adopter who already had these controls passing can now fail
them.** Each is the check working, not a new rule:

1. **Strictness is read, not assumed.** TYP-001 carries `baseline: null`. If
   turning the strictness key on surfaces existing type errors, there is nowhere
   to record them — the skill reports the count and stops rather than weakening
   the setting it was asked to deploy.
2. **A coverage allow-list is judged by what it leaves out.** `files = [...]` in
   a type checker's config excludes everything it does not name, so a tracked
   module nothing imports is unchecked while the control claims all first-party
   source. The gate lists every such file and extends the list
   ([ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md), applied to an
   allow-list rather than an exemption list).
3. **A suppressed step is not a gate.** Nothing the gate writes may carry
   `continue-on-error` or end in an idiom from the register's `suppression:`
   list. LNT-001 and TST-001 both verify through `no-failure-suppression`, and
   `|| true` on the lint step fails both of them at once.
4. **A wired tool your lockfile does not pin.** From register contract 13,
   LNT-001 and TYP-001 verify that the tool exists in a lockfile you commit as
   well as that every locus invokes it. A repository that lints with a globally
   installed linter — one nobody pinned, and which can differ between your
   machine and CI — now fails, naming the tool and the lockfile. The gate adds
   the dependency for you and reports every one it added by name: a tool your
   repository did not previously depend on is a change to what it builds, not
   only to how it is checked
   ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md), case C).

**Wiring by hand instead?** Stamp what you write, as § 3.1 says for the secrets
gate — and stamp **each control's own artefacts**. All three read back a stamp
naming themselves, so recording your CI steps and forgetting the editor locus
fails LNT-001 even though TST-001 passes. This repository's own six
quality-gate stamps say *adopted rather than deployed*, because the artefacts
were hand-written in Phase 0.5 before there was a gate to write them.

### 3.3 — `gate-supply-chain`, and the locus that was never checked

`/gate-supply-chain` wires SUP-001 (*dependencies resolve from a committed
lockfile*), SUP-002 (*dependency updates are proposed automatically*) and
SUP-003 (*third-party CI actions are pinned to a commit SHA*). Three controls
and one skill because they are one property split three ways — what a build
resolves, how it stays current, and what it is allowed to fetch — and because
SUP-001's install step has to sit **above** every other gate's steps in the
gating workflow. Every one of them runs the tools that install places.

**Four prerequisites, and how you know each is met.**

| Prerequisite | Why | How you know it worked |
| --- | --- | --- |
| A tracked lockfile for every ecosystem you are in | The gate stops rather than generating one. A lockfile a skill produces pins a resolution nobody reviewed | `standard-check run --control SUP-001` names the ecosystem and the lockfile it expected |
| A `frozen_install_command` for the lockfile you use | `uv sync --frozen` and `poetry install --sync` are both python. Which is right is a fact about your repository | The schema rejects a register whose command matches none of its own ecosystem's `frozen_install` patterns — so a gate cannot write a step the checker then refuses |
| A `tools.standard-check` entry with an `invocation` | SUP-003's pre-commit gate is the checker itself, and a locus running a bare name resolves from `PATH` — what answered would be auditing your repository ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)) | The gate stops before writing anything and says the invocation is missing |
| A gating workflow — one that runs on `push` or `pull_request` | A workflow only a human can trigger is not the ci locus | GOV-001 reports every blocking control reachable from a step that can fail |

**Expect exit `0`.** None of these three declares a `remote` locus, so nothing
is waiting on Phase 3. A `3` means a block declared itself partial.

**Two ways a repository that already had SUP-003 passing can now fail it.**

1. **A declared locus with nothing at it.** Until register contract 14, SUP-003
   verified neither of the two loci it declares. `actions-pinned-to-sha` reads
   the *property* — every `uses:` is a commit SHA — out of the files on disk,
   which is a different claim from *something enforces this before a commit
   lands and before a merge does*. This repository reported SUP-003 PASS with no
   pre-commit hook for it of any kind. If yours does too, the gate writes one;
   the property and the loci now fail independently, and the report says which.
2. **Running the checker where you meant to audit with it.** A hook or step
   invoking `standard-check schema`, `meta`, `assert` or `explain` reaches no
   control at all. This repository's own pre-commit config ran
   `standard-check schema` and would otherwise have been credited with a SUP-003
   gate that could never have failed it.

**The config is not the bot.** A `.github/dependabot.yml` is inert until
Dependabot is enabled on the repository, and a `renovate.json` is inert until
the Renovate app is installed and its onboarding pull request is left open
rather than closed — both platform acts, both in § 1.1. The gate writes the
file and says which act you now owe it. **A pin nothing updates rots at a known
version**, which is a different failure from an unpinned one and not a better
one, so SUP-002 exists to keep SUP-003's SHAs and DEV-001's digests current
rather than merely fixed.

**Wiring by hand instead?** Stamp what you write, and stamp **each control's
own artefacts**. All three read back a stamp naming themselves, so recording
your install step and forgetting `dependabot.yml` fails SUP-002 while the other
two pass. This repository's own four supply-chain stamps say *adopted rather
than deployed*, because the artefacts were hand-written in Phase 0.5 before
there was a gate to write them.

### 3.4 — `gate-build`, and what it pins rather than chooses

`/gate-build` wires BLD-001 (*every container image stage ends as a non-root
user*) and DEV-001 (*devcontainer features are version-pinned*). Two controls
and one skill because they read the same file: BLD-001 wants a user, DEV-001
wants two pins, and both are keys in `devcontainer.json`.

**It pins what it finds; it does not choose.** Deciding *which* image and which
features your repository uses is `project-init`'s, or your own. This gate
insists that whichever were chosen are pinned. Inventing an image or a user here
produces a container that does not start, which is a worse failure than the one
being fixed.

**Three prerequisites, and how you know each is met.**

| Prerequisite | Why | How you know it worked |
| --- | --- | --- |
| A base image that defines a non-root user | The gate writes the user the image provides, not one it invents | `docker run --rm <image> id -un` names a user; `standard-check run --control BLD-001` then reports it |
| A `tools.standard-check` entry with an `invocation` | Both controls' pre-commit gate is the checker, and a locus running a bare name resolves from `PATH` — what answered would be auditing your repository ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)) | The gate stops before writing anything and says the invocation is missing |
| A `tools.hadolint` entry, **if you have a Dockerfile** | BLD-001's container half runs the linter. An absent linter is `UNCLASSIFIED — cannot verify`, not a pass ([ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md)) | `standard-check run --control BLD-001` stops reporting UNCLASSIFIED for that block |

That last row is § 3.7 in miniature — *your register records your own files*.
This standard's register pins no `hadolint`, because this repository has no
Dockerfile to lint, and a `pinned_at` naming a site that does not exist is a
failure rather than a placeholder. A repository that does have one adds the
entry, naming the loci **it** installs the linter at.

**Two half-states this gate exists to catch.** Each reads as solved and is not:

1. **A lock file covering some features.** This project's own Phase 0.5 exit
   criterion was re-opened over exactly that — a lock file pinning three of four
   features.
2. **A complete lock file over a floating image tag.** The more dangerous of the
   two, for the same reason. Both halves or neither.

And one that is not a half-state at all: **a devcontainer naming neither
`containerUser` nor `remoteUser`** runs as whatever its base image uses, which
may be root today and may become root on any digest bump. Non-root by luck is
not the property BLD-001 states.

**A shared file, and who owns which part of it.** `gate-build` owns
`.devcontainer/setup.sh` and creates it when absent. It does not own what other
gates install there: `gate-secrets` writes and stamps the scanner's install
block, and `gate-supply-chain` the package manager's — exactly as four gates
write their own hooks into one `.pre-commit-config.yaml`. `gate-build` writes no
stamp of its own in that file, because neither of its controls has a locus
there, and a stamp naming a control whose locus the file is not is a claim
rather than a record.

**Wiring by hand instead?** One hook can enforce both controls — the command is
the same — but it needs **two** stamps. The read-back matches on the control
being evaluated, so a hook stamped for BLD-001 alone leaves DEV-001's pre-commit
locus unrecorded even though the same command enforces it.

### 3.5 — `gate-iac`, and the verdict that is not a pass

`/gate-iac` wires IAC-001 (*infrastructure code is statically analysed before
apply*). It applies only if you have `*.tf` files: the predicate is evaluated
against files and never self-declared, so a repository without them skips the
control and there is nothing to deploy.

**One hook runs both analysers.** IAC-001's verify blocks are
`checkov --directory . --compact --quiet` and `tflint --recursive`, and the hook
runs the *control* — `standard-check run --control IAC-001` executes both
through the same path the audit uses. Two hooks each invoking one analyser would
be two statements of what "analysed" means, free to drift from each other and
from the register.

**Two prerequisites, and how you know each is met.**

| Prerequisite | Why | How you know it worked |
| --- | --- | --- |
| A `tools.checkov` and `tools.tflint` entry in your register | Without them the analysers are unpinned, and an absent analyser is `UNCLASSIFIED — cannot verify`, not a pass | `standard-check run --control IAC-001` stops reporting UNCLASSIFIED for those blocks |
| A `tools.standard-check` entry with an `invocation` | The pre-commit gate is the checker, and a locus running a bare name resolves from `PATH` ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)) | The gate stops before writing anything and says the invocation is missing |

**Expect `UNCLASSIFIED` on the first run, and do not treat it as a pass.** This
standard's register pins neither analyser, because this repository has no `*.tf`
to analyse. The gate will **not** make the report green by installing an
unpinned tool — that leaves the version unrecorded, which is exactly the
condition `tool_versions_match_register` exists to fail.

**Exit `1` has two causes and they are not the same.** A failing wiring or stamp
block is a failed deployment. A failing `checkov` or `tflint` block is a
*successful* deployment finding real problems in your Terraform — the gate
working on its first run. Conflating them is how a working gate gets rolled
back, so the skill reports which and quotes the block.

**What it leaves alone.** `terraform validate` checks syntax and provider
schema, which neither analyser does — a different check, not a predecessor. A
second analyser such as `tfsec` is not a violation, but two analysers means two
suppression files and only one of them is a place this standard checks
([ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md)); the skill shows
what each is configured to do and asks.

**A suppressed step is not a locus.** From register contract 16, a CI step
carrying `continue-on-error: true` does not satisfy any control's ci locus. The
tool runs, the job succeeds whatever it reports, and the merge is not gated on
it. The same tightening applies to every gate, not only this one.

### 3.6 — `gate-repo`, the one that changes something outside your repository

`/gate-repo` wires CI-001 (*the default branch cannot be written to without a
passing check*). It is the only gate whose effect is not a file you review
before it takes effect: it calls the GitHub API, and **the ruleset is in force
the moment the call returns**, for everyone with access.

So it confirms explicitly before acting, on every run, regardless of any plan
already approved — including one approved in `standard-adopt`. That plan covers
what will be written to files; this call is not a file. A re-run that would
change nothing still asks, because a call whose effect is invisible until it is
wrong is not one to make silently.

**Two prerequisites, and how you know each is met.**

| Prerequisite | Why | How you know it worked |
| --- | --- | --- |
| A token with `administration: write` on the repository | Writing a ruleset needs it, and it is granted by a human with admin (§ 1) | `gh api repos/<owner>/<name>/rulesets` returns rather than 403 |
| Agreement that the default branch stops accepting direct pushes | It applies to **everyone**, including administrators, unless a bypass is configured | The gate states the blast radius before asking, and names who it affects |

The gate stops **before writing anything** when the token lacks the permission.
A skill that writes the record and cannot apply it leaves a repository looking
protected in a diff and unprotected in fact.

**A recorded ruleset is not a protected branch.** `gate-repo` writes
`.github/rulesets/default-branch.json` and then applies it. GitHub does not read
a path in your repository to decide what protects your default branch; only the
API call does. The file is a record, and the checker verifies it as one:
`ruleset_recorded_matches_register` says *intent only* in its own message.

**Expect exit `3`.** CI-001's `remote` block reports `SKIPPED (no credentials)`
until Phase 3 implements platform verification. What is verified is that you
record the ruleset the register requires. What is not verified — by anything,
yet — is that GitHub is enforcing it. Both get said, and neither stands in for
the other.

**Three things the checker rejects in a recorded ruleset**, each of which GitHub
itself would accept:

1. **`enforcement: evaluate`.** It reports what would have happened and blocks
   nothing — a control declared and unreachable.
2. **A ruleset targeting a branch by name.** `~DEFAULT_BRANCH` follows the
   default; `refs/heads/main` stops protecting it the day your default moves,
   silently.
3. **A ruleset git does not track.** Nobody can review it, and the remote block
   cannot be reached without credentials either — so nothing at all about the
   control would have been verified.

**Already have branch protection?** Say so and let the gate transcribe it. This
repository's own record was adopted rather than deployed: the ruleset was
created by hand in Phase 0.5, and the file is what the API returns today,
including a `deletion` rule the register does not ask for. An extra rule adds a
restriction; a record that disagrees with what is enforced is worse than one
carrying more than the register requires.

**Classic branch protection and a ruleset both apply**, and the union of their
requirements is enforced. Removing the classic rule is a real reduction until
the ruleset is confirmed active, so the gate confirms first and asks second.

### 3.7 — Your register records your own files

Two things in `controls.yaml` describe **the repository being checked**, not this
one, and are the first edits an adopter makes to their copy:

| What | Where | Why it is yours and not ours |
| --- | --- | --- |
| Every file that repeats a pinned tool version | `tools.<tool>.pinned_at` | `tool_versions_match_register` compares exactly these paths. A path listed here that does not exist is a failure, and so is one that exists and holds no pin — which is how a renamed workflow is caught rather than silently dropped from comparison |
| Which package ecosystems you are in, and what a frozen install looks like in them | `ecosystems:` | Detected from your manifests. If your CI installs with an idiom the register has not heard of, add it there rather than working around it in the checker |
| Where a literal-pinned tool's release comes from | `tools.<tool>.release_repo` | A fork or an internal mirror is a reasonable thing to differ on. A gate skill downloads from exactly this repository, so a wrong value fails at the checksum rather than installing something else |

Get the first one wrong and SUP-001 tells you so by name — *"recorded as pinned
at X, which does not exist"*. That message is the check working: this repository
carried four of its own filenames inside `standard-check` until contract 8, so an
adopter was told their tools were "pinned at no known locus" against a list of
paths they had never had ([§ H2](09-phase-1.5-review.md#h--what-a-review-of-the-closed-phase-found)).

Files this repository's gates deploy carry a provenance stamp naming the control,
the deploying skill and the register contract; see
[`00-concepts.md`](00-concepts.md) § The provenance stamp.

## 4 — Run the checker

```bash
uv run standard-check                    # the whole register
uv run standard-check run --tier 1       # Tier 1 only — note the `run`
uv run standard-check run --control SEC-001   # one control — what a gate verifies through
uv run standard-check explain SEC-001    # why a control exists, and what it checks
uv run standard-check schema             # validate the register itself
uv run standard-check --repo ../other    # `--repo` goes before the subcommand

# Checking a repository that has no register of its own — every adopter, until
# they commit one. Without `--register`, the checker looks for
# `../other/controls.yaml` and reports that it cannot read it.
uv run standard-check --repo ../other --register ./controls.yaml
```

Read the exit code, not just the report
([ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md)):

| Code | Meaning |
| --- | --- |
| `0` | Every applicable control was verified and none failed |
| `1` | A verified violation |
| `3` | No violation found, but something could not be verified |
| — | `--require-complete` promotes `3` to `1` |

**`3` is the code that matters.** It is the difference between "clean" and
"nothing looked". A run with no credentials for the remote checks exits `3`, and
treating that as success is the mistake the code exists to stop.

Verdicts to read carefully:

- `SKIPPED (predicate)` — the control does not apply to this repository. A
  legitimate pass.
- `SKIPPED (no credentials)` — a remote check could not run. **Not** a pass.
- `UNCLASSIFIED` — the tool that would decide is absent, so the answer is
  unknown. Not a failure, and not a pass.

## 5 — Checklist

Each row is done when its evidence exists, not when the step has been performed.

| # | Step | Evidence |
| --- | --- | --- |
| 1 | Repository visibility or plan allows rulesets | `gh api repos/O/R/rulesets` returns a list |
| 2 | Default-branch ruleset created | `repos/O/R/branches/BRANCH --jq .protected` is `true`, and a direct push is refused |
| 3 | Secret scanning push protection on | `.security_and_analysis.secret_scanning_push_protection.status` is `enabled` |
| 4 | `.github/dependabot.yml` covers every ecosystem present | A Dependabot pull request appears |
| 5 | Renovate installed, if any version is a literal | Its Dependency Dashboard lists the expected number of sites |
| 6 | Devcontainer image digest-pinned, lock file complete, user stated | `uv run standard-check` reports DEV-001 and BLD-001 passing |
| 7 | Gates wired at every locus the control declares | LNT-001, TYP-001, DOC-001, TST-001 passing |
| 7b | Quality gates wired at every locus **and** stamped | `standard-check run --control LNT-001 --control TYP-001 --control TST-001` exits `0` — every block ✓, nothing skipped |
| 7a | Secrets gate wired at pre-commit **and** CI, and stamped | `standard-check run --control SEC-001` shows both local blocks ✓ and exits `3` — the remote block is Phase 3, not a failure |
| 8 | The conformance run is a required status check | GOV-001 passing without its partial declaration (Phase 3) |

## When something is wrong with the standard itself

If a control cannot be satisfied for a reason that is about the control rather
than about your repository, that is a finding, not a workaround. Raise it. Do not
re-tier the control, and do not exclude your own files to make a report green.
An exemption may scope a gate to what git tracks — it may never hide a file git
is tracking, and the checker fails you if it does
([ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md)). The repository
that authored that rule broke it once already and had to
[record the fix](04-build-plan.md).
