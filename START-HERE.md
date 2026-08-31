# Start here

**You need a Mac with Docker.** By the end your repository will refuse commits
carrying secrets, install its dependencies frozen and get upgrade proposals for
them, run lint, types and tests at every locus that declares them, and have a
default branch whose protection is verified against what GitHub actually
enforces — with one command that tells you which of those hold.

**Two of those need a paid GitHub plan if your repository is private.** Check
before you start rather than at step 3 — § Is your repository private? is one
command and it decides what you can reach.

Most of this you do alone. Two steps wait on somebody else, and § What you are
about to do says which, so you can raise them today and carry on.

## How this works

`controls.yaml` — the **register** — holds fifteen entries. Each names a
property, like *a commit containing a secret cannot reach the remote*. Everything
that enforces it is generated from that entry rather than written beside it: the
CI workflow, the pre-commit hook, the editor setting, the devcontainer, the
branch ruleset. One definition, many derived artefacts, nothing to drift.

Each entry declares its **loci** — where it runs: editor, pre-commit, pre-push,
CI, and the platform itself. A control declaring three must be wired at all
three, with the same pinned tool version at each.

Deploying a gate is a Claude skill's job. **Enforcing is not.** What runs when
you commit is a pinned binary reading a pinned config; there is no model in CI.

A merge is blocked only when three things line up: the control is blocking, a CI
job runs it and can fail, and the platform enforces that job as a required check.
The third is the one that silently goes missing, so the checker reads it through
the GitHub API rather than trusting a file.

Fuller explanation: [`HOW-IT-WORKS.md`](HOW-IT-WORKS.md).

## Before you start

### What this assumes

macOS, with Docker running. The container's secrets are fetched from the macOS
Keychain by a script that runs *before* the container exists, so on Linux or
Windows that script is what you adapt first —
[`docs/08-adopting.md`](docs/08-adopting.md) § 2.0 states the contract a
replacement owes.

### Install these

| Tool | Install | You have it when |
| --- | --- | --- |
| Homebrew | <https://brew.sh> | `brew --version` |
| Docker Desktop | <https://www.docker.com/products/docker-desktop/> | `docker info` succeeds |
| Claude Code | <https://docs.claude.com/en/docs/claude-code/setup> | `claude --version` |
| node and npm | `brew install node` | `npm --version` |
| `devcontainer` CLI | `npm i -g @devcontainers/cli` | `devcontainer --version` |
| GitHub CLI | `brew install gh`, then `gh auth login` | `gh auth status` |
| VS Code | `brew install --cask visual-studio-code` | `code --version` |

Give Docker Desktop 8 GB of memory (Settings → Resources → Memory).

**And a repository to work on**, on GitHub and cloned locally. This standard
makes an existing repository conformant; it does not create one. § Where to run
these has the check and the one-liner if you are starting from nothing.

**Is it a Python project?** The checker installs as a Python dependency, and the
register declares the spelling for that ecosystem and no other. In a Python
repository you get the gates *and* `register-check`, which is what verifies them.
In any other, the gates deploy and enforce but the command that audits them
cannot be installed
([ADR 0032](docs/adr/0032-the-checker-is-installed-from-a-tagged-ref.md) records
this as known and unsolved). Worth knowing now rather than at the last step.

### Is your repository private?

If it is, run this before anything else. It decides whether two of the fifteen
controls are reachable at all, and finding that out at step 3 wastes the four
steps before it.

```bash
gh api "repos/{owner}/{repo}" --jq .visibility
gh api "repos/{owner}/{repo}/rulesets" >/dev/null && echo "rulesets: available" \
  || echo "rulesets: NOT available on this repository's plan"
```

**Public repository:** everything below applies. Skip to the credentials.

**Private, rulesets available** (GitHub Team or Enterprise): everything below
applies too.

**Private, rulesets not available:** you can still adopt this, and **thirteen of
the fifteen controls will hold** — the secret scanner at every local locus,
frozen lockfile installs, SHA-pinned actions, published-digest checks, lint,
types, tests, the pinned devcontainer, dependency proposals. Two cannot, and
you should know exactly which and what they cost before you begin:
§ If your plan has no rulesets, at the end.

### Get these credentials

| Credential | Where to create it | Scope | Where it goes |
| --- | --- | --- | --- |
| Claude Code OAuth token | `claude setup-token` | — | Keychain, `CLAUDE_OAUTH_TOKEN` |
| A token for `gh` | <https://github.com/settings/personal-access-tokens> | read on the repository | Keychain, `GITHUB_TOKEN` |
| An admin token | <https://github.com/settings/personal-access-tokens> | `Administration: write` | used once, not stored |
| The CI token | <https://github.com/settings/personal-access-tokens> | `Administration: read` | an environment secret, at step 6 |

**Make the last two fine-grained, not classic.** A classic token in CI is a
verified violation — SEC-003 fails on a header only classic tokens return. The
`gh` row may be classic; it never reaches CI.

## What you are about to do

| # | Step | Rights needed |
| --- | --- | --- |
| 1 | Install the plugin | Yours |
| 2 | Get the register | Yours |
| 3 | The platform steps | **Admin on the repository** |
| 4 | The container | Yours |
| 5 | Run the adoption | Yours |
| 6 | Turn the bots on | **Owner on the organisation**, to install Renovate |

**You can stop after any of them.** Each step leaves the repository in a working
state, so a first sitting that ends at step 4 has cost nothing — pick it up
later from where you stopped.

## Where to run these

**Step 1 runs anywhere. Everything from step 2 runs in your repository's root.**

Installing the plugin is a change to your machine, not to any project — it lands
in `~/.claude/` and writes nothing into a repository. Step 2 onward writes files
where you are standing: `controls.yaml`, `.devcontainer/`, `renovate.json`. Run
them in the wrong directory and you get a stray register in your home folder and
a container config nothing will use.

```bash
cd /path/to/your-repository
git rev-parse --show-toplevel   # the repository root — cd here if it differs
git remote get-url origin       # the GitHub repository these controls will protect
```

**If the first command says `fatal: not a git repository`, stop here** — you are
in an ordinary folder, and there is nothing for this standard to make conformant
yet. Almost everything below needs a repository *and* a GitHub remote: step 2
commits a file, step 3 calls `gh api repos/{owner}/{repo}/...`, and the secrets and
branch-protection controls read what git tracks and what GitHub enforces.

### If you do not have a repository yet

```bash
# A new project: create it locally, then create it on GitHub and push.
mkdir -p my-project && cd my-project
git init -b main
git commit -q --allow-empty -m "Initial commit"
gh repo create my-project --private --source=. --remote=origin --push
```

```bash
# An existing GitHub repository somebody else set up: clone it.
gh repo clone <owner>/<repo> && cd <repo>   # angle brackets: replace these
```

**Done when:** both commands at the top of this section print something — a path
and a URL.

## 1 — Install the plugin

Everything below arrives in it, including the devcontainer you copy at step 4.

```bash
claude plugin marketplace add Eaiger-Ent/ee-standard
claude plugin install control-register@ee-standard
```

**Done when:** `claude plugin list | grep control-register` prints a row, and
`ls ~/.claude/plugins/cache/ee-standard/control-register/*/templates/devcontainer`
lists files.

**If it fails:** `claude: command not found` means Claude Code is not installed —
see the table above.

**Why this exists:** [`docs/08-adopting.md`](docs/08-adopting.md) § 0.0

## 2 — Get the register

The plugin ships no register. The register is what you adopt, and it becomes
yours the moment you edit it.

```bash
repo=https://github.com/Eaiger-Ent/ee-standard
tag=$(git ls-remote --tags --refs "$repo" | awk -F/ '{print $NF}' | sort -V | tail -1)
echo "${tag:?}"
curl -fsSL -o controls.yaml "https://raw.githubusercontent.com/Eaiger-Ent/ee-standard/${tag}/controls.yaml"
git add controls.yaml
```

**Done when:** `grep -A2 '^    install:' controls.yaml` shows a `ref:` naming the
tag you just fetched. The register a tag ships names that same tag.

**If it fails:** an empty `$tag` means the tag list did not resolve — the `echo`
above stops you before `curl` builds a URL with a hole in it. The fuller schema
check needs the checker, which does not exist until step 5.

**Why this exists:** [`docs/08-adopting.md`](docs/08-adopting.md) § 0.1

## 3 — The platform steps

**Private repository without rulesets? This step is one command, and then you go
to step 4.** § Is your repository private? is where you found that out. Run this
to record what your plan gives you, and skip the rest of this step:

```bash
gh api "repos/{owner}/{repo}/rulesets" 2>&1 | tail -2
```

Expect a `403` saying *"Upgrade to GitHub Pro or make this repository public"*.
Secret scanning is a paid feature on private repositories too, so Settings →
Code security will not offer push protection either — **there is no setting to
find, and nothing here you have failed to do.** Read § If your plan has no
rulesets for what that costs and how to record it, then **go to step 4**.

Everyone else, continue.

---

None of this is code and none of it is visible to a `git clone`. It needs the
admin token.

```bash
default=$(gh api "repos/{owner}/{repo}" --jq .default_branch)
gh api "repos/{owner}/{repo}/rulesets" --jq '.[].name'
gh api "repos/{owner}/{repo}/branches/$default" --jq .protected
gh api "repos/{owner}/{repo}/rules/branches/$default" --jq '[.[].type] | unique'
gh api "repos/{owner}/{repo}" --jq '.security_and_analysis.secret_scanning_push_protection.status'
```

`{owner}` and `{repo}` are **not placeholders to fill in** — `gh` replaces them
from the repository you are standing in, so this block runs as written.

**The default branch is looked up rather than assumed, and that matters.** `gh`
also accepts `{branch}`, but it resolves to the branch you are *on* — so running
these from a feature branch reports an unprotected branch and an empty rule
list, which looks like a real answer and is not.

That block only *reads*. One thing here you must do by hand, because no gate
does it: **enable secret-scanning push protection**, in the repository's
Settings → Code security. It is the only stop that is not on a contributor's
machine.

**You do not create the ruleset here.** Step 5 does, through `gate-repo`, which
asks its own confirmation before the call — the ruleset is in force for everyone
the moment it returns, so it is not something to do twice or by accident.

**Done when:** the last command prints `enabled`. The rest are a baseline to
compare against after step 5 — expect the ruleset list to be empty and
`.protected` to be `false` now, and both to change then.

**If it fails:** a `403` on write with a `200` on read is a token scope problem,
not a syntax one. A `403` on the *listing* means you should have taken the
branch at the top of this step.

**Why this exists:** [`docs/08-adopting.md`](docs/08-adopting.md) § 1

## 4 — The container

Copy the template, delete its README **first**, then substitute.

Copy it, and delete its README before anything else — it explains the
placeholders, so while it is there the "any placeholders left?" check can never
come back clean:

```bash
cp -R ~/.claude/plugins/cache/ee-standard/control-register/*/templates/devcontainer .devcontainer
rm .devcontainer/README.md
```

Read the version and the x86_64 digest out of the register, and fetch the
aarch64 one from the release. **Check all three are non-empty** — an extraction
that quietly yields nothing is worse than one that errors:

```bash
uv_block() { sed -n '/^  uv:/,/^  [a-z-]*:$/p' controls.yaml; }
uv_version=$(uv_block | sed -n 's/^ *version: *"\{0,1\}\([0-9][^"]*\)"\{0,1\} *$/\1/p')
uv_sha_x86=$(uv_block | sed -n 's/^ *sha256: *//p')
uv_sha_arm=$(curl -fsSL "https://github.com/astral-sh/uv/releases/download/${uv_version}/uv-aarch64-unknown-linux-gnu.tar.gz.sha256" | cut -d' ' -f1)
echo "${uv_version:?} ${uv_sha_x86:?} ${uv_sha_arm:?}"
```

Substitute them exactly as they are — do not unquote them and do not change the
case. Then put the Claude Code token in the Keychain, because the container will
not start without it:

```bash
sed -i.bak -e "s/{{PROJECT_NAME}}/$(basename "$PWD")/g" .devcontainer/devcontainer.json
sed -i.bak -e "s/{{UV_VERSION}}/${uv_version}/g" -e "s/{{UV_SHA256_X86_64}}/${uv_sha_x86}/g" -e "s/{{UV_SHA256_AARCH64}}/${uv_sha_arm}/g" .devcontainer/setup.sh
rm .devcontainer/*.bak
grep -rl '{{' .devcontainer
```

**That `grep` must print nothing.** A surviving placeholder is what fails the
build later, at `sha256sum -c`, with no clue why.

**Check before you write.** The Keychain service names carry no project prefix
by design — one credential serves every ee project on the machine — so if you
have set one up before, the entry is already there and you need do nothing:

```bash
security find-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" -w >/dev/null \
  && echo "already set — nothing to do" \
  || echo "not set — add it below"
```

`add-generic-password` **will not overwrite**: on an existing entry it fails with
*"The specified item already exists in the keychain."* To replace one, delete it
first.

```bash
claude setup-token   # prints the token; copy it
security delete-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" 2>/dev/null
security add-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" -w "<paste it here>"
```

Then build:

```bash
devcontainer up --workspace-folder . --remove-existing-container
```

**Done when:** the `grep` prints nothing, the build ends with
`"outcome":"success"`, and the environment report at the end shows `uv` at the
version you substituted, built for your architecture.

**One `✗` is expected here** if you skipped the optional `gh` credential:

```text
✗ GitHub CLI — not authenticated.
```

That report never blocks the build, and the container is fine. It matters at
step 5 — `gate-repo` and the remote checks talk to GitHub — so fix it on the
**host** rather than inside:

```bash
security add-generic-password -a "$USER" -s "GITHUB_TOKEN" -w "<a token>"
devcontainer up --workspace-folder . --remove-existing-container
```

`gh auth login` inside the container works too and does not survive a rebuild:
the only persistent volume is `/home/vscode/.claude`, and `gh` keeps its
credentials in `~/.config/gh`.

**If it fails:** an empty value from the extraction is caught by the `echo` — do
not skip it. A container that starts with no uv in it means the substitution
silently did nothing. `initializeCommand` exiting `1` means the Keychain has no
Claude Code token yet.

**Why this exists:** [`docs/08-adopting.md`](docs/08-adopting.md) § 2.0

## 5 — Run the adoption

One command deploys every gate. Run it interactively.

```bash
claude --permission-mode acceptEdits
# then, in the session:
/register-adopt --repo . --register ./controls.yaml
```

**Done when:** it reports every control planned and verified, and commits.

**If it fails:** it will still prompt for `.devcontainer/devcontainer.json` —
that is a sensitive file and no permission mode silences it. `gate-repo` asks its
own question before each platform change; that is the skill's, not the harness's,
and it is meant to be there.

**Why this exists:** [`docs/08-adopting.md`](docs/08-adopting.md) § 0

## 6 — Turn the bots on

**Not optional.** Step 4 put a version literal in a shell script, and no
Dependabot manager can see one — so without this, uv is pinned at whatever
version you adopted at, for ever, with the supply-chain controls green over it.

```bash
cp ~/.claude/plugins/cache/ee-standard/control-register/*/templates/renovate/renovate.json .
git add renovate.json .github/dependabot.yml
```

Then install the Renovate app at <https://github.com/apps/renovate>, onto the
organisation or the single repository. Merge your config to the **default
branch** — Renovate reads its config from there and sees an unconfigured
repository until you do.

**Done when:** Renovate's Dependency Dashboard issue appears and lists the number
of matched sites you expect. Derive that number from your own pinned tools; the
dashboard is the only external evidence the annotations do anything.

**If it fails:** leave the "Configure Renovate" onboarding pull request alone —
it carries a default config that enables every manager, and closing it unmerged
tells Renovate to disable itself. It closes itself once your config lands.

**Why this exists:** [`docs/08-adopting.md`](docs/08-adopting.md) § 1.1

## What a Claude Code session adds to your repository

Running Claude Code here creates a little project state, and one file of it
should not be committed.

| File | What it is | Commit it? |
| --- | --- | --- |
| `.claude/settings.local.json` | **Your own** permission grants, model and output style — and the format allows an `env` block, so it is a plausible place for somebody to put a token | **No** — add it to `.gitignore` |
| `.claude/settings.json` | The project's shared settings: hooks, and anything the team agrees on | Yes |
| `CLAUDE.md` | Only created if you run `/init`. Guidance for future sessions | Yes, if you want one |

Add the one line before your first commit:

```bash
echo '.claude/settings.local.json' >> .gitignore
```

Neither file breaks the deployment — no control reads `.claude/` — but two
things are worth knowing:

**A committed `settings.local.json` puts one developer's preferences in
everybody's diff**, and if anyone ever adds an `env` block to it, a credential
goes with them. If you would rather the register enforced that rather than your
memory, add the path to `secret_files_are_gitignored`'s `paths:` in your own
`controls.yaml` — that block is a list of *your* files, and
[`docs/08-adopting.md`](docs/08-adopting.md) § 3.7 is where the register starts
recording them.

**A `CLAUDE.md` is linted.** DOC-001 covers every tracked Markdown file, so one
generated by `/init` is in scope like any other — expect to fix a few long lines
the first time the hook runs.

## You are done when

**Step 5 is what put the checker there.** `register-check` does not exist before
it: `/register-adopt` dispatches `/register-install`, which adds it to your
project as a dependency pinned to a tagged release. Two things follow, and both
have caught people out:

- **It is a command, not a slash command.** There is no `/register-check` in
  Claude Code. Run it in a terminal.
- **Run it inside the container.** Everything after step 4 goes inside —
  `devcontainer exec --workspace-folder . uv run register-check`, or open a
  shell in the container and run it there.

```bash
uv run register-check
```

**If it says the command is not found**, one of three things is true, and they
are quick to tell apart:

```bash
ls pyproject.toml                                  # a Python project at all?
grep -c register-check pyproject.toml uv.lock      # the dependency, and the pin
```

| What you see | What it means |
| --- | --- |
| No `pyproject.toml` | Your repository is not a Python project — see the note below |
| It exists, no `register-check` in it | Step 5 did not get as far as installing the checker. Re-run `/register-adopt` |
| Both present, still not found | You are on the host rather than in the container |

**The checker is installed as a Python dependency, and today only a Python
project can hold one.** The register declares the `git+` spelling for `python`
and for no other ecosystem, so `/register-install` stops rather than inventing
one — [ADR 0032](docs/adr/0032-the-checker-is-installed-from-a-tagged-ref.md)
§ The non-Python adopter is not solved records that as known. The gates still
deploy and still enforce; what you do not get is the command that verifies them.
If your repository is not Python, say so when you raise this — you are the
adopter that ADR says reopens the question.

**Exit `3` is the expected first success, not a failure.** It means nothing was
found in violation but something could not be verified — some controls read
platform state and only answer inside a GitHub Actions job. Exit `1` is a real
violation.

**On a private repository without rulesets you will get `1`, and it is real.**
CI-001 and SEC-001's remote block fail rather than skip. See the next section.

Two things are a second sitting, and their order matters — giving CI a
credential comes *before* making the run fail on anything unverified, or every
run fails on controls that actually hold:
[`docs/08-adopting.md`](docs/08-adopting.md) § 4.2 then § 4.3.

## When it goes wrong

| Symptom | Cause | Fix |
| --- | --- | --- |
| Container starts, `uv: command not found` | The uv placeholders substituted to nothing | Re-run step 4's extraction and check the `echo` is non-empty |
| Every gate says its pre-commit locus is wired, nothing runs on commit | A wired locus is not an installed hook | `ls -l .git/hooks/pre-commit`; `uv run pre-commit install` |
| A gate is green about a tool version you are not running | You ran it on the host, not in the container | Everything after step 4 goes inside |
| `sha256sum -c` fails during container create | A placeholder survived, or an architecture digest is wrong | `grep -rl '{{' .devcontainer` should print nothing |

## If your plan has no rulesets

Repository rulesets on a **private** repository are, in GitHub's words, *"for
customers on GitHub Team and GitHub Enterprise plans"*, and secret-scanning push
protection on a private repository likewise needs a paid tier. If you have
neither, two controls cannot hold and **the checker fails them rather than
skipping them** — `uv run register-check` exits `1`, and it is telling the truth.

**Adopt anyway.** Thirteen of fifteen controls hold, and they are not the
trivial ones. What you do not get is the *server-side boundary*, and it is worth
being exact about what that leaves open:

| Risk | What it means in practice |
| --- | --- |
| **Your default branch is advisory** | Anyone with write access can push straight to it. No review, no passing check. Every gate still runs; nothing makes a red one stop a merge |
| **History can be rewritten** | Force-push to the default branch is possible, which removes the audit trail everything else here relies on |
| **A secret that reaches a commit reaches the remote** | The scanner runs at pre-commit, pre-push and CI — but all three are on the contributor's side. `--no-verify` skips two, a fresh clone has neither until `pre-commit install` runs, and CI catches it *after* the push, by which point it is disclosed and must be rotated |
| **No alerts on what is already there** | A credential committed before you adopted is never flagged |

The first two are one thing said twice, and it is the one this standard exists
to prevent: a check that runs and blocks nothing is theme **T-3**.

**What to do about it, honestly:**

- **The cheapest fix is the plan.** Two of fifteen controls, and both are the
  boundary ones. If the repository holds anything you would mind being pushed to
  unreviewed, that is what you are buying.
- **Until then, install the hooks and mean it.** `uv run pre-commit install`
  after every clone, by every contributor. It is bypassable and per-machine —
  that is precisely why it is not a control — but it is what you have.
- **Keep the conformance workflow red-if-broken and read it.** It cannot block a
  merge, but it can tell you, and a report nobody reads is the failure after
  this one.

**You can record this rather than run permanently red**
([ADR 0047](docs/adr/0047-a-plan-limit-is-recorded-not-tolerated.md)). Add an
entry to `deployment-decisions.yaml` naming the control, the block, your plan and
what it lacks, with a review date:

```yaml
platform_limits:
  - control: CI-001
    assert: default_branch_ruleset_satisfies
    plan: github-free-private
    lacks: rulesets on a private repository are GitHub Team and Enterprise only
    review_by: 2026-11-30
```

The block then reports `UNAVAILABLE (plan)` instead of failing, and the run exits
`3` rather than `1`. **It is a record, not a pass** — the control does not hold,
the reason and the date print on every run, and an entry past its `review_by`
fails the build rather than going on covering. `--require-complete` still turns
it into a failure, so a repository in this state does not turn that flag on.

Only record a capability your plan genuinely does not offer. If GitHub offers it
by some route the checker fails to read, that is a defect to report rather than
something to waive.
