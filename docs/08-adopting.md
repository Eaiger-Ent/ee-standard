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
| The other five `gate-*` skills | **Phase 2 — not built** | `docs/02-skill-family.md` |
| `standard-adopt` — one command to deploy everything | **Phase 2 — not built** | `docs/02-skill-family.md` |
| `kind: remote` verification of platform state | **Phase 3 — not built** | Reports `SKIPPED (no credentials)` |

So today, adoption is: do § 1 by hand, copy the devcontainer, run
`/gate-secrets` for the secrets gate, wire the remaining gates by hand using
this repository as the worked example, and run the checker. When Phase 2
finishes, most of § 2 and § 3 becomes one command.

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

One gate is built — see § 3.1. For the rest, until Phase 2 ships them, wire the
gates by copying this repository's own artefacts, which are the reference
implementation:

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
back a provenance stamp naming the gate that deploys it, so a hand-wired hook
with no stamp fails. Say in the stamp's comment that it was adopted rather than
deployed — this repository's own two artefacts do exactly that, because they
were written in Phase 0.5 before there was a gate to write them, and a stamp
claiming otherwise would be a record of something that did not happen.

### 3.2 — Your register records your own files

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
