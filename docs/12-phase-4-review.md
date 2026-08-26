# Phase 4 — the consumer repository

The record of the first adoption performed by a repository that did not author
the standard: `Eaiger-Ent/ee-standard-consumer`, public, created 2026-08-25.

[`04-build-plan.md`](04-build-plan.md) is the list of outstanding work; this is
where the evidence behind every criterion it ticks lives, and where what the
phase found is written down whether or not a criterion covers it.

**The phase's purpose, in the plan's own words:** *"The genuine risk is Phase 4
revealing something Phases 1–3 assumed."* It revealed twenty-six such things. Three
of them made the published route impossible to follow rather than awkward, one
put a wired-but-unreachable locus inside the artefact the standard itself
deploys, and none of them could have been found from inside this repository,
because each is a consequence of not being it.

## What the phase had that no earlier phase did

A **macOS host with Docker**, the devcontainer CLI and `gh` — the machine
Phase 2's template-build criterion was deferred here to wait for. Docker 29.7.2,
`devcontainer` 0.88.0.

The other thing it had was a repository with **no history of this project in
it**, which is the instrument. Every finding below is a thing that works in
`ee-standard` and does not work anywhere else.

## The findings, in the order they were met

### 1 — The template's install path is not a path an adopter has

`08-adopting.md` § 2.0 said the template ships at
`plugins/control-register/templates/devcontainer/`. That is where it lives in
*this* repository. An adopter who installed the plugin has it at
`~/.claude/plugins/cache/<marketplace>/control-register/<version>/templates/devcontainer/`,
and the guide gave no way to find it.

**Closed** — § 2.0 now gives both paths.

### 2 — The placeholder check could never come back clean

The guide's verification is `grep -rl '{{' .devcontainer`, *expect no output*.
Two files quote the pattern while explaining it: `devcontainer.json`'s own
header comment, and the template README. So a copy with every placeholder
substituted still listed a file, for ever.

**Closed** — the header no longer spells the pattern, and both the template
README and § 2.0 say to delete `README.md` from the copy first, with the reason.

### 3 — The container had no Claude Code, and could not get one

`check-auth.sh` probed for `claude` and printed *"re-run: bash
.devcontainer/setup.sh"* when it was missing. Nothing in the template installs
Claude Code, so that remedy could never work. It mattered rather than being
untidy: the entire published route into this standard is `/register-adopt`, a
Claude Code skill.

Adding the feature exposed the next layer. `claude-code` declares node a **soft**
dependency, so the CLI logged *"Soft-dependency 'node' is not required. Removing
from installation order"* and the feature's own apt fallback failed on trixie:

```text
Failed to install Node.js and npm
ERROR: Node.js and npm are required but could not be installed!
```

**Closed** — the template declares `claude-code` and `node:2`, both digest-pinned
in `devcontainer-lock.json`, and the reasoning is in the file: neither is a
language choice, which is the rule they look like they break.

### 4 — `devcontainer up` on an existing container leaves the lock file behind

Adding a feature and running `up` reused the container, so the lock was not
regenerated and covered one of two features — the exact partial lock DEV-001
fails and the exact shape that re-opened a Phase 0.5 criterion.

**Closed** — `--remove-existing-container` is in the template README and in
§ 2.0, with the reason rather than as an incantation.

### 5 — The container had no uv, and no gate could give it one

The finding of the phase, measured inside a freshly built container:

```text
uv       MISSING
poetry   MISSING
python3  Python 3.13.5
```

The template's own `setup.sh` calls `uv sync --frozen`. § 2.3 tells the adopter
to run `uv run register-install`. Every gate verifies itself with `uv run
register-check`. None of it can run, and no gate can fix it, because a gate that
installed uv would be running its own verification on the tool it had not
installed yet.

The interpreter answering `python3` is the base image's `python3-minimal`, below
the floor [ADR 0028](adr/0028-the-support-floor-is-what-we-run.md) sets and
missing `venv`, `ctypes`, `sqlite3` and `http` — so the container also had no
interpreter anything here could run on.

**Closed** by [ADR 0034](adr/0034-the-template-bootstraps-uv.md): the template
installs uv from the pinned release tarball against the published sha256, with
the three values as placeholders substituted out of the register. A pinned
community feature was considered and rejected on measurement — its `install.sh`
curls the tarball with no checksum, which is the trade Phase 0.5 already refused.

After the fix, in the rebuilt container:

```text
✓ claude — 2.1.241 (Claude Code)
✓ uv — uv 0.12.5 (aarch64-unknown-linux-gnu)
```

And with `.python-version` committed, `uv run python -V` reports **3.14.7**: uv
downloaded the interpreter the file names. Without the file the same container
answers 3.13.5.

### 6 — The register had no published route at all

`/register-adopt --register ./controls.yaml` names a file the plugin does not
ship and the guide never told anyone how to obtain. § 3.7 spoke of *"their
copy"*; nothing said where a copy comes from.

**Closed** — § 0.1: fetch it from the same tagged ref the checker is pinned to,
commit it, and check it with `register-check schema` before anything else.

### 7 — The only tag that existed could not install the checker

`v0.1.0` was cut on a commit whose register is contract **28**.
`tools.register-check.install` arrived at contract 29. So an adopter who fetched
the only obtainable register got `register-install` stopping — correctly, and
naming the contract it needed — on an address that genuinely was not there.

The general rule this settles: **the register a tag ships must name that same
tag.** `install.ref` and `pyproject.toml`'s version are set in the commit the tag
names, so the checker and the register an adopter installs are one artefact.
`v0.2.0` was cut that way, and `v0.3.0` and `v0.4.0` after it.

### 8 — `rationale_adr` made a fetched register unloadable

Every one of the fourteen controls failed schema validation in the consumer
repository:

```text
controls[0] (SEC-001).rationale_adr: file does not exist: docs/adr/0001-secrets-never-reach-the-remote.md
```

The field resolves against the register's own directory, which is the authoring
repository. A register that travels cannot carry paths into a `docs/` tree the
adopter was never going to have.

**Closed at register contract 30.** The schema accepts a path **or** an `http(s)`
citation, and the shipped register uses one. The renamed-ADR check the path form
bought moves to `tests/test_rationale_citations.py`, which holds every citation
to the address `tools.register-check.install.repository` names *and* to a file in
this working tree — stricter than what it replaces, because a URL can name
someone else's repository and a path could not. The path form still loads, so an
adopter whose ADRs sit beside their register keeps using it.

### 9 — Both skills probed a flag the checker did not have

`register-adopt` Step 0 and `register-install` Step 4 both run
`uv run register-check --version`. There was no such flag. The install had
*worked* — right artefact, right tag, recorded in the lockfile — and there was no
way to ask whether it was there.

**Closed** — `--version` reads the installed distribution's version, and
`tests/test_register_install.py` derives the probe from the skill's own text, so
a skill that changes its probe fails here rather than in an adopter's repository.

### 10 — The front door could dispatch nothing

`register-adopt` exists to dispatch seven skills and carries `Skill` in its
`allowed-tools` to do it. All eight skills carried
`disable-model-invocation: true`:

```text
Skill control-register:register-install cannot be used with Skill tool due to
disable-model-invocation.
```

So the documented one-command entry point had never been able to take its first
step, and could not have taken any later one.

**Two things had to line up for this to survive Phase 2.**
`tests/test_register_adopt.py` drives the dispatch order in Python, which is the
pipeline rather than the dispatch — a limit
[`10-phase-2-review.md`](10-phase-2-review.md) states plainly. And preflight
**P9 is exactly this check**, with exactly this fix, and reported
`{"skill": "register-adopt", "overall": "PASS", "fails": 0}`: the dispatch
targets are named in prose, not in a field a checker resolves. **The criterion
was ticked on a check that could not see the defect** — the eighth box in this
project to be ticked and later found false, and the first found from outside.

**Closed** by [ADR 0035](adr/0035-a-dispatched-skill-is-reachable.md).
`register-adopt` keeps the flag; the seven it dispatches drop it and each says so
in its `README.md`. What guards `gate-repo`'s platform mutations is its own
per-call confirmation, which Phase 3 made a build failure to omit — not a
frontmatter key that made the skill unreachable.

### 11 — The adoption ran on the host, and the report did not say so

The first deployment run was driven from the macOS host: all 372 entries of that
session carry `cwd: /Users/nathan/git/ee-standard-consumer`, and all 58 shell
calls with them. It reached almost-conformance, and three things were wrong that
no verdict showed.

**The host's uv was 0.8.13; the register pins 0.12.5.** The container has the
pinned one, installed from the verified tarball. `tool_versions_match_register`
compares the pin recorded in `setup.sh`, not the binary doing the work, so the
run was green about a version it was not using.

**The `.venv` thrashes.** It is bind-mounted, so it is host-built or
container-built and never both. Running the checker inside afterwards printed
`Removed virtual environment` and rebuilt it. The host venv was a Homebrew
CPython rather than the interpreter `.python-version` names — 3.14.7 by luck.

**The pre-commit hook was never installed.** `.pre-commit-config.yaml` deployed
and stamped, every gate reporting its `pre-commit` locus wired, and
`.git/hooks/pre-commit` absent — so every commit in the repository, including
the gates' own, ran nothing. Declared and unreachable, theme **T-3**, inside the
artefact the standard itself had just deployed. See § 13.

The file-level verdicts are identical host and container — they were diffed, not
assumed. The three that differ (SEC-001, SEC-003, GOV-001) differ on
credentials: the container carries `GITHUB_TOKEN` from `.env.docker`, so inside
it GOV-001 is a true `FAIL` — GitHub enforces no required check yet — where the
host reports `SKIPPED (no credentials)`.

**Why it happened is a finding, not a preference.** The plugin was installed
from a **directory marketplace at a host path**, which does not exist inside the
consumer container, so `control-register` could not be installed there at all.
Until the plugin is in a marketplace the container can reach, an adopter's
container cannot install the gates either.

**Closed** — `08-adopting.md` § 2.0a is the host/container split as a table, with
the four host-only steps and the one-line check for which side you are on.

### 12 — `lint-md` is in a private marketplace

DOC-001 is *dispatch elsewhere* in every plan this repository produces, and
elsewhere is `EqualExperts/ee-skills`, which is **private**. An adopter outside
Equal Experts cannot install it, so DOC-001 has no route through the guide at
all.

Phase 4 resolved it by **copying** the skill into the consumer repository's
`.claude/skills/lint-md/` — a copy of someone else's skill, in the adopter's
repository, going stale silently. That is the duplication this standard exists
to prevent, and it is recorded as what happened rather than as a recommendation.

It is the same access-shaped single point of failure the devcontainer template
was moved into this plugin to escape, and **no criterion covers it**.
`08-adopting.md` § 3 now names DOC-001 as the one control an outside adopter may
have to satisfy by hand, and says what that means. Solving it is Phase 6's, with
the other `lint-md` business.

### 13 — A wired locus with no installed hook

The one worth more than its fix. `.pre-commit-config.yaml` is a statement of
intent; `.git/hooks/pre-commit` is whether anything runs. Every gate that
declares a `pre-commit` locus reads the first.

The template installed the hook on the tail of the `uv.lock` arm, so a
repository that gained a lockfile *after* its container was created never got
one — which is every repository that adopts the standard before it has a
lockfile, and was the consumer repo exactly.

**Closed in two places, and neither is a control.** The install now hangs off
`.pre-commit-config.yaml`'s own presence, reaching `pre-commit` the way its
locus does. And `check-auth.sh` **reports** a missing hook on every container
start — reported rather than repaired, which is that script's stated rule, since
a start-up hook that silently fixed state would hide which locus stopped working
and when.

It cannot be a control: `.git/hooks/` is untracked, and CI has no hooks
installed and should not. That is the honest boundary of what a register can
check, and it is worth stating where somebody will look for it.

Both halves are held by tests that were **watched failing** before the fix
(`tests/test_devcontainer_template.py`), and the new report was run against the
live consumer container, where it says:

```text
✗ pre-commit hook — .pre-commit-config.yaml is present and
    .git/hooks/pre-commit is not. Nothing runs at the pre-commit locus.
```

### 14 — git refused the workspace inside the container

Found on the **second** run, which is the one that does everything inside the
container — so the first run could not have found it, having done everything
outside.

```text
fatal: detected dubious ownership in repository at '/workspaces/ee-standard-consumer'
```

The workspace is a bind mount from a macOS host, and git refuses it even though
the directory and `.git` both stat as `1000:1000`, the container user.

**The failure is partial, which is worse than total.** `git status` and
`git add` work; `git commit` and `git log` do not. So the first commands an
adopter tries are the ones that succeed, and the diagnosis arrives several steps
after the cause. It also explains a message from the first run that had been
written off as transient: `register-check` reporting *"is not a git repository —
predicates are evaluated against git-visible files, so any report here would
describe nothing"*. It was this, and it means **a repository git will not open
reports nothing rather than reporting a violation**.

**Closed** — `setup.sh` marks the workspace safe, scoped to `$PWD` and never
`*`, because the check exists to stop hooks running out of somebody else's
repository and the one directory the container was created for is exactly the
one to trust. `tests/test_devcontainer_template.py` fails a missing line and a
wildcard alike.

### 15 — Two of the guide's own commands did not work

Both written by Phase 4 itself, in the fixes for findings 5 and 6, and both
found by running them rather than by reading them.

The uv extraction in § 2.0 used `grep -A4 '^  uv:'`, which never reaches
`version:` because the register comments that block — so it returned empty,
`sed` substituted nothing, and the placeholders would have survived into a
container that fails at `sha256sum -c`. **An extraction that quietly yields
nothing is worse than one that errors**, and the guide now prints both values
and says to check them.

And `test_every_placeholder_is_named_in_the_readme` matched `\{\{([A-Z_]+)\}\}`,
so it silently skipped `{{UV_SHA256_X86_64}}` and `{{UV_SHA256_AARCH64}}` —
the two placeholders most likely to be left unsubstituted were the two the check
could not see. A one-character class fix, and the same shape as § 10: a check
reporting a pass over something it never looked at.

### 16 — `register-install` read the register with a tool the container does not have

```text
(eval):1: command not found: yq
```

The skill's pre-flight read `tools.register-check.install` with `yq`, twice.
Nothing in the template installs one, and **nothing should**: `yq` would be a
tool a skill needs and no control names, so no register would pin it and nothing
would keep it in step — the second-copy problem arriving through a convenience.

**Closed** — it reads through
`uv run --no-project --with pyyaml python -c`. uv is the one tool the whole
standard already depends on, `--with` fetches the parser for the length of one
command, and `--no-project` reads the register without touching an environment
the checker is not yet installed into. Verified in the consumer's own container.
A `grep` fallback was rejected in the skill's own text, because Phase 4 had
already written one into the adoption guide and had to correct it (§ 15).

### 17 — `claude update` could not run, and the container was pinned to what the feature shipped

Claude Code stuck at 2.1.241 mid-adoption. The `claude-code` feature runs
`npm install -g` as **root**, so the package tree it writes is root-owned while
the container's user is `vscode` — which BLD-001 requires — and `claude update`
fails with *"Insufficient permissions to install update"* on a release cadence
of roughly one a day.

This repository's own `setup.sh` has carried the fix since Phase 0.5; the
generalised template dropped it, which is the failure mode the build plan
predicted for the generalisation in the first place: *"anything the
generalisation cannot carry across is a sign the original was wired to this repo
in a way the spec did not intend"*. Here it was the opposite — something the
original had right and the copy lost.

**Closed** — the template hands `vscode` the one package the feature owns, as a
loop over the glob so a container without the feature is a no-op rather than an
error.

### 18 — The fix for § 13 could abort container create

Found by running it, one commit after writing it. `uv run pre-commit install`
was guarded by `uv.lock` **existing**, not by pre-commit being *in* it — and
every adopting repository is in that state for a while, between the gate that
writes `.pre-commit-config.yaml` and the gate that adds the dependency. Under
`set -euo pipefail` the non-zero exit aborts `setup.sh`, so the container fails
to build.

**A devcontainer that fails to build because a hook is not installed yet is a
worse failure than the missing hook**, and the fix that caused it was one day
old. Each arm now asks whether the tool is reachable *that way* before using it,
and the else-branch reports rather than failing:

```text
note: .pre-commit-config.yaml exists and pre-commit is not installed,
      so nothing runs at the pre-commit locus.
```

`tests/test_devcontainer_template.py` reads the arms out of the script and fails
any that installs without probing first — watched failing against the previous
version.

### 19 — Every write arrived as a diff with no reason attached

The operator, mid-run: *"lots of requests to accept a change to
`.pre-commit-config.yaml`, `setup.sh`, etc., but nothing is explaining what test
has passed or failed or why the update is needed."*

That is exactly right, and the first half of the answer is that **nothing had
failed and nothing had passed**. A gate deploys first and verifies last — Step 5
is `register-check run --control <ID>` — so at the moment of the prompt there is
no test result to quote, by design. What was missing is the *forward* reason:
which control this serves, which step of how many, and what will check it.

The provenance stamp does name the control. It arrives buried in the middle of
the diff it is explaining, twenty lines in, which is not where somebody deciding
whether to accept a change is looking.

**Closed** — every gate, and `register-install`, now carries a *Say what each
write is for* rule with a fixed shape:

```text
SEC-001 · step 1/6 · .devcontainer/setup.sh
  what it does:  installs the scanner at the version the register pins
  why now:       the pre-commit hook this gate writes next has nothing to run
  verified by:   register-check run --control SEC-001, at the verify step
```

`register-adopt` is exempt, because it writes no artefacts of its own — the same
reason it ships no templates. `tests/test_plugin.py` fails a skill that can
write files and does not carry the rule, so a ninth skill inherits it rather
than rediscovering the complaint.

**The gap this does not close** is the one the operator's phrasing points at: a
gate cannot tell you a control *passes* until every artefact for it exists, so
an incremental "this write made SEC-001 go green" report is not available
without running the checker between writes. That would be a different design —
verify-as-you-go rather than deploy-then-verify — and it is not obviously better:
a control half-deployed fails for a reason that is not a defect, and reporting
that failure at each step would train an operator to ignore it.

### 20 — DOC-001 was satisfied by hand, and § 3 had no procedure for it

`gate-repo` reached its ruleset step and stopped, correctly:

```text
REQUIRED_CHECKS from the register:
  register-check   ✓ produced by the job above
  lint-md          ✗ no gating job produces this
```

It offered three resolutions and refused to choose: apply with both contexts and
every merge blocks forever on a check nothing reports; drop `lint-md` and a
control that is `variance: forbidden` with `baseline: null` is silently
downgraded; or record without applying. **Record-only is the only one that does
not lie**, and it is what was taken.

The underlying problem is § 12 — the plugin that deploys DOC-001 is in a private
marketplace. § 3 said, in prose, that an outside adopter may have to satisfy the
control by hand. It gave no procedure, which made it the one part of this guide
asserting something nobody had done.

**Done now, and it works.** The step that turned out to matter is that
**DOC-001 asks for no provenance stamp** — its verify blocks are the tool itself
and `markdown_gate_wired_at_all_loci`, with no `provenance_stamp_present` — so a
hand-wired deployment passes the control *completely*, rather than passing it in
part and failing on a gate that was never involved. `deployed_by: lint-md` only
matters where a stamp is read. The artefacts carry a comment saying nothing
deployed them and why no stamp is written, because a stamp naming `lint-md`
would record a deployment that did not happen.

§ 3 now carries the six steps, and DOC-001 reports `PASS` in the consumer
repository with no plugin installed and no private marketplace reached.

### 21 — `gitignore: true` is only as good as the `.gitignore`

The consumer repository had **no root `.gitignore` at all**, and nothing in this
standard writes one — the template ships `.devcontainer/.gitignore`, which
carries SEC-001's two credential lines and nothing else. Run 1 did not hit this
because `project-init` writes one at its Step 7b; run 2 does not run
`project-init`, so the gap showed.

Two consequences, one loud and one quiet. `git add -A` staged **1,542** files
from `node_modules`. And DOC-001 failed on markdown that is not this
repository's:

```text
node_modules/to-regex-range/README.md:295:1 error MD033/no-inline-html
```

`.markdownlint-cli2.yaml` sets `gitignore: true` precisely so the tool is scoped
to what git does not ignore — which is a scoping rather than an exemption, and
therefore permitted under ADR 0019 where an `ignores:` entry would not be. But
it is a scoping *by reference*, and the thing it refers to did not exist.

**Closed** in the guide rather than in code: § 3's DOC-001 procedure now names
the root `.gitignore` as a step with the reason, since neither the template nor
any gate can write a file whose contents are the adopter's own.

### 22 — The register's `pinned_at` named a file only the author has

Exactly as § 3.7 predicts, and worth recording because it is the check working:

```text
✗ tool_versions_match_register — uv is recorded as pinned at
  .github/workflows/support-floor.yml, which does not exist
```

`support-floor.yml` is a workflow this repository has and an adopter does not.
`pinned_at` is compared path by path, so a listed path that is absent is a
failure — which is the property that stops a renamed workflow leaving comparison
silently. The consumer removed the line from **its own** register, with a
comment recording that it did so and why, and SUP-001 passes.

This is the first edit § 3.7 says an adopter makes, and the first time anybody
has made it. It is also the moment the register stops being ours and starts
being theirs.

### 23 — The chain from a control to a refused merge, proven end to end

§ 4.2 says a green report about a ruleset is a claim about a file until a merge
is actually blocked, and that the last step is one no report can take. Taken, on
the consumer repository, with the ruleset live and enforcing both contexts:

```text
lint-md         fail
register-check  pass
mergeable: MERGEABLE   state: BLOCKED
```

and the attempt itself:

```text
X Pull request #3 is not mergeable: the base branch policy prohibits the merge.
```

A pull request adding markdown DOC-001 refuses (MD026, MD034), the required
check failing, and GitHub refusing the merge. The PR was closed afterwards; it
had done its job.

Alongside it, evidence nobody asked for: **Dependabot had already opened two
pull requests** of its own, so SUP-002 holds in fact and not only in
configuration.

### 24 — Nothing ran the pre-commit hooks, and every gate said the locus was wired

The finding of the second run, and it was found by trying to prove something
else.

The plan was to show the `pre-commit` locus refusing a bad markdown file before
CI ever saw it. It did not refuse. It committed:

```text
[prove-the-gate 5373f04] test: a markdown file DOC-001 must refuse
 1 file changed, 3 insertions(+)
```

`.pre-commit-config.yaml` carried five gates' hooks, and **`pre-commit` was not a
dependency of the repository at all** — `uv run pre-commit --version` failed, so
`.git/hooks/pre-commit` had never been installed. The consumer had finished a
full adoption, reported 12 controls passing, and had nothing running at a locus
five controls declare.

This is § 13 again, one layer down and worse. That fix made the template install
the hook *when the runner is reachable*, and report when it is not — and it did
report, on every container start. What nothing did was **make the runner
reachable**: five gates write into that config file and none of them added
`pre-commit` to the project, though `gate-quality` already uses
`ecosystems.<eco>.add_dev_dependency` for ruff, mypy and pytest.

The checker reported the locus wired throughout, and was right to: it reads the
config file, which is the claim the register makes. *A hook exists* and *a hook
runs* are different claims, and only the first is in a tracked file.

**Closed** in the five gates that write hooks: before writing one, each makes
sure `pre-commit` is a dev dependency — through the register's own
`add_dev_dependency` spelling — and that the git hook is installed, idempotently,
so whichever gate runs first does it and the rest find it done.
`tests/test_plugin.py` fails a skill that writes into `.pre-commit-config.yaml`
without doing so.

**Proved by re-running the same commit.** After `uv add --dev pre-commit` and
`pre-commit install`, the file that had sailed through was refused:

```text
markdownlint-cli2 (DOC-001)..............................................Failed
docs-probe.md:1:38 error MD026/no-trailing-punctuation
```

Which makes the whole chain, in one repository: the pre-commit locus refuses it,
a deliberate bypass gets it as far as CI, CI refuses it, and the merge is
refused.

**What is still not verified is step 2**, and that is a stated boundary. Whether
`.git/hooks/pre-commit` exists cannot be a control — `.git/hooks/` is untracked
and CI legitimately has no hooks installed. Whether the *runner* is present can
be, being a line in a lockfile, and whether the register should say so is left
open rather than decided here.

### 25 — Applying the ruleset before committing locks the branch against the adoption

`gate-repo` runs at `register-adopt`'s Step 4; the commit is Step 6. The ruleset
requires a pull request for the default branch from the moment the call returns,
so everything the five earlier gates wrote — still uncommitted — is locked out
by the gate that is meant to protect it. The result would be a conformant
working tree, a protected branch, and no route from one to the other except a
pull request nobody set up.

Phase 4 landed its work **twenty-one seconds** before the ruleset applied — the
commit at 11:02:05 and the ruleset at 11:02:26 — and only because the operator
was told to reorder. The skill's own step order would have produced the trap.

**Closed** in both places: `register-adopt` Step 4 says to commit and push
before dispatching `gate-repo`, and `gate-repo` gained a Step 2.0 that runs
`git status --porcelain` and `git log --branches --not --remotes` before asking
to apply, and stops to say what is outstanding. It does not commit on the
operator's behalf — a gate that started committing other gates' work would be
the wrong lesson to draw from this.

### 26 — § 4.3's own arrangement fails every pull request

Preparing § 4.3 for the consumer found that the section does not work as
written, in three layers, each uncovered by fixing the one before it.

**The environment refuses the job.** `environment: conformance` on the gating
job, with the branch policy § 4.3 prescribes:

```text
Branch "refs/pull/5/merge" is not allowed to deploy to conformance
due to environment protection rules.
```

In about a second, before any step runs. A `pull_request` ref cannot match a
policy naming the default branch — and a policy loose enough to match would
admit a **fork's** pull request too, since that produces the same ref in the
base repository. So the guard cannot be relaxed; it is doing its job.

**Keying on the event is not enough.** Taking the environment only when
`github.event_name == 'push'` still asks for it on a *branch* push, which the
same policy refuses. It has to be keyed on the ref being the default branch,
read from `github.event.repository.default_branch` rather than typed.

**And then the real one.** With the job finally running, the step failed with
**exit 3**. `--require-complete` was not even passed: exit `3` is non-zero, so a
bare `run:` fails on it regardless. A pull request has no platform credential by
design, so SEC-001's and SEC-003's remote blocks cannot answer, and every pull
request fails for a reason no contributor can act on — which is the exact
failure § 4.3 was written to prevent.

**So under Option 3 the fork carve-out is not an edge case; it is the normal
path.** § 4.3 said the opposite — *"If your repository takes no fork pull
requests, do not write this"* — and it said so because **this repository has
never met any of it**: Option 1 puts the secret where same-repo pull request
runs can read it, and ADR 0022's requirement 6 is precisely that this
repository's posture must not be read as the standard's.

The arrangement that works, measured green on both events with the pull request
reporting `CLEAN`: the environment is taken only on the default branch, the
strict `--require-complete` run is the default-branch run, and a pull request
runs the same audit with the job token and tolerates exit `3` and only `3`.

**The cost is real and is now stated in the guide rather than buried**: an
adopter's pull request is gated by the audit that *can* run, so a change leaving
a control unverifiable merges and the default branch goes red afterwards, rather
than the pull request going red before.

**A decision is owed, and the guide says so rather than making it.** This
narrows *a run that cannot verify fails* — [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md)'s
property — to the default branch for every adopter. That is a choice with
alternatives (loosen the policy; take Option 1; require reviewers; run the
strict audit on a schedule), it weakens a stated guarantee, and it crosses two
ADRs, so amending either alone would leave the other's reader with a wrong
picture. It needs its own ADR, plus a numbered revision to ADR 0016, whose
revision 5 bounds the exit-3 tolerance to fork pull requests — right that the
bound is a fact about the platform, wrong that the fact stops at forks.

`tests/test_adopter_guide.py` caught the first draft of the fix, which split the
secret and its `environment:` line into two fenced blocks: a reader copies an
example, not a section, so the line that reaches the secret and the line that
gates it have to be in front of the same reader.

## What the two skills did when they could run

### `project-init` and `register-adopt` do fight over `devcontainer.json`

The composition criterion, answered. `project-init` Step 4 was refused by the
harness's sensitive-file guard, and its own report says what it would have done:

- replace the digest-pinned image with `mcr.microsoft.com/devcontainers/python:3.12`
  — a **floating tag**, which fails DEV-001's `devcontainer_image_digest_pinned`,
  and a version below the register's floor;
- add `ghcr.io/devcontainers/features/node:1` because its skip-check tests for
  `node:1` and the template declares `node:2` — two conflicting node features in
  one block, and a lock file covering neither.

The order is forced: `project-init` requires `devcontainer.json` to exist, so the
template must be copied first, and Step 4 then overwrites the two things the
template exists to pin. They do not compose today. Nothing in this repository can
fix `project-init`, so this is a Phase 6 submission with a measurement behind it
rather than an opinion.

### `register-install` works

```text
- register-check==0.2.0 (git+…@83d3f3cd…)
+ register-check==0.3.0 (git+…@5f4ec86b…)
```

Address and ref from `tools.register-check.install`, the spelling from
`ecosystems.python.git_dependency`, the upgrade recognised as an upgrade rather
than a fresh install, and no `ee-control:` stamp written — which is the decision
ADR 0032 records, not an omission.

### The plan, and the starting state it measured

With `GITHUB_TOKEN` exported, `register-adopt` computed the plan and ran the
starting-state audit against register v0.24.0 (contract 30), exit `1`:

| Control | Starting verdict |
| --- | --- |
| BLD-001, DEV-001 | FAIL — both property blocks **pass**; loci unwired, unstamped |
| SEC-001 | FAIL — `gitleaks` clean and push protection **PASS remotely**; loci unwired |
| CI-001 | FAIL — no recorded ruleset, and remotely `main` has no `pull_request`, `required_status_checks` or `non_fast_forward` rule |
| SUP-001, SUP-002 | FAIL — no frozen CI install, no update config |
| LNT-001, TYP-001, TST-001 | FAIL — no config, no pin, no locus |
| DOC-001 | FAIL — no config; `markdownlint-cli2` UNCLASSIFIED, not installed |
| SEC-002, SEC-003, SUP-003 | SKIPPED (predicate: `github-actions` — no workflows yet) |
| IAC-001 | SKIPPED (predicate: `terraform`) |
| GOV-001 | FAIL — nine blocking controls with no reachable CI step |
| GOV-002, GOV-003 | PASS |

That table is worth more than a green one. Every FAIL names something absent, no
FAIL is a checker artefact, and the two SKIPPED groups are skipped for reasons a
reader can check. The remote blocks **answered** rather than skipping, which is
Phase 3's work holding in a repository it was not developed against.

## What is not closed

**The gates have not been deployed.** `register-adopt` reached Step 4 and
`gate-build` was refused by the harness's sensitive-file guard on
`.devcontainer/devcontainer.json` — a file Claude Code protects, whose prompt a
headless run has nobody to answer, and which a `permissions.allow` entry does not
lift. This is a property of the harness rather than of the standard: an operator
running the skill interactively answers the prompt and continues. It is recorded
in § 0 of the adoption guide, because losing two runs to it is a cost worth
warning about.

So these criteria remain open, and none of them is known to fail:

- the consumer repo reaching full Tier-1 conformance
- `project-init` and `register-adopt` composing — **answered as a finding**, but
  the fix is upstream and not yet made
- weakening a `narrowing-only` control and watching the checker catch it

## The criteria this phase closes, and how

### The interpreter is pinned, and a control says so

The criterion asked whether `gate-build` writes `.python-version` or the guide is
enough, *judged by what the consumer repo actually has*. Neither, and the answer
was already in the checker: `tool_versions_match_register` fails a
`source: toolchain` tool whose file is absent or untracked. Demonstrated on the
consumer rather than reasoned about — the file removed, and the verdict gains a
line:

```text
python is sourced from .python-version, which is not tracked
```

That is the right shape. The register holds no interpreter version — by
[ADR 0027](adr/0027-the-interpreter-is-a-pinned-tool.md) the file is the
authority — so the standard cannot choose an adopter's interpreter and does not
try. It insists there is one. And a gate writing the file from whatever the
container resolved would have written **3.13.5** here, which is precisely the
accident ADR 0028 raised the floor to stop.

### The devcontainer template builds

Phase 2's last open criterion, and the reason this work happened here. The
template was copied out of the plugin's install cache, substituted, and built:

```text
{"outcome":"success","imageName":["vsc-ee-standard-consumer-…-features"]}
```

then run, with `--no-cache` and then from clean, ending in a container reporting
`remoteUser: vscode` and every probe green. DEV-001's and BLD-001's property
blocks pass against it — `devcontainer_user_is_non_root`,
`devcontainer_image_digest_pinned`, `devcontainer_lock_covers_all_features` —
while their locus and stamp blocks fail, which is correct for a copy no gate has
touched yet.

**It did not build first time, and that is the evidence.** Three defects had to
be fixed before it came up, and every one of them is a thing
`tests/test_devcontainer_template.py` could not have caught, because a file test
cannot notice that a container has no uv in it.

### The template is obtainable without access to a private repo

`ee-skills-incubator` is private; the template is a directory in the plugin, and
Phase 4 obtained it from a plugin install cache with no access to any private
repository. Closed by construction, and now exercised.
