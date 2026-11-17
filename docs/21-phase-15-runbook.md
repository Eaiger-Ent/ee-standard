# Phase 15 — Apple `container` for adopters: the run sheet

The runbook for the five evidence criteria at the head of
[`04-build-plan.md`](04-build-plan.md) § Phase 15. [ADR 0064](adr/0064-an-adopter-may-run-its-devcontainer-on-apple-container.md)
accepted offering the route to adopters on the spike's evidence alone, and gated
the release on these five runs. **None of the template, adopt-script or
adopter-document changes ships until every run below has a recorded result.** A
failure is a finding. It re-opens the ADR's question and is not edited away.

It is written for an operator on an Apple silicon Mac, a host this container is
not. It follows the shape of
[`16-marketplace-readoption.md`](16-marketplace-readoption.md): it says what the
host needs and what each step should produce, and it **does not restate the
adoption steps**, which live in [`08-adopting.md`](08-adopting.md). The launcher's
own commands are in [`06-devcontainer-setup.md`](06-devcontainer-setup.md) § 1.

## What these runs cannot yet test, and what stands in

Nothing under `plugins/control-register/templates/` has changed, so an adopter
has no launcher. Runs A–C copy it in by hand. That is a stand-in, and it is the
reason the criteria are about the **launcher**, not about the shipped template.
Three differences between the stand-in and the decision are findings to record,
not defects to fix during the run:

| The decision (ADR 0064) | What the stand-in does | Record |
| --- | --- | --- |
| The CLI pin is in `.devcontainer/package.json` | The launcher resolves the CLI at `<root>/node_modules/.bin/devcontainer`. The run puts `package.json` in the **root** | Whether the launcher needs a change to find `.devcontainer/node_modules`. It does, unless it already finds it |
| `adopt.sh` accepts either runtime | It does not yet, so Run D runs the **current** scripts to record their baseline | Which stage fails first, and with what message |
| `UPGRADING.md` carries the migration | It does not yet, so Run E *writes* the steps as you perform them | The steps, in order, as the text for `UPGRADING.md` |

## What the host must have

| Requirement | Verify with |
| --- | --- |
| Apple silicon Mac, macOS 26 or later | `sw_vers -productVersion` and `uname -m` |
| Apple `container` 1.7.1 or later, **installed before Run A** | `container --version`. Not installed? Paste the block in [`06-devcontainer-setup.md`](06-devcontainer-setup.md) § Installing Apple `container`. It downloads, checks the signature and installs, and needs an admin password once |
| Its services running | `container system status` reads `running`. If not, `container system start`, **once per login**. The first start offers to download a kernel: accept it |
| **Docker Desktop quit, and not installed for Run D** | `docker info` fails or `docker` is not on `PATH`. A run with Docker answering proves nothing |
| Node.js | `node --version` |
| `gh` authenticated to `Eaiger-Ent` | `gh auth status` |
| `claude setup-token` done, and the Keychain entries | [`08-adopting.md`](08-adopting.md) § 2.0a. `.devcontainer/fetch-secrets.sh` reads them |
| A checkout of this repository on the Mac, and `PATH_TO_EE_STANDARD_CHECKOUT` set to it | `ls "$PATH_TO_EE_STANDARD_CHECKOUT/.devcontainer/bin/container-session.mjs"` |

Runs A and D copy files from the standard's own checkout, which is the stand-in
for a release that ships them. Set the variable in **every** terminal you run
them from. The variable lasts only as long as the shell it was set in. Use a
checkout you already have, on the commit under test, or clone a fresh one:

```bash
gh repo clone Eaiger-Ent/ee-standard "$HOME/phase15/ee-standard"
export PATH_TO_EE_STANDARD_CHECKOUT="$HOME/phase15/ee-standard"
git -C "$PATH_TO_EE_STANDARD_CHECKOUT" rev-parse HEAD
```

The last line prints the commit to record with the versions. The commands below
write the variable as `${PATH_TO_EE_STANDARD_CHECKOUT:?…}`, so an unset variable
stops the command with the message rather than resolving to `/`.

The code blocks in this document carry **no `#` comments**. macOS's default
shell is zsh, which passes a `#` typed at its prompt to the command as an
argument unless `setopt interactivecomments` is set. What a comment would have
said is in the prose around each block.

**Record, for every run:** the date, the macOS version, `container --version`,
`node_modules/.bin/devcontainer --version`, the standard checkout's commit, and
the Mac's model. A run without its versions is not evidence.

`scripts/phase15-evidence.sh` records those observations and the ones the runs
below ask for, and decides nothing: `host` on the Mac, `inside` from a shell in
the Apple container, and `run -- COMMAND` around a launcher command (Run C's
refusal, its exit code and whether a container appeared). It writes to
`~/phase15`, holds no secret and no username, and is a recorder, not a
substitute for this document. Paste what it wrote under the run's heading.

Run `host` from the adopted clone, because it reads `.devcontainer/.env` there.
The container cannot see the standard's checkout, so `inside` needs a copy in
the clone's `.git/`. The container sees that folder, and `git status` does not
list it. Keep the record with `tee`, because the `written to:` path it prints
is inside the container:

```bash
cp "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/scripts/phase15-evidence.sh" .git/
node .devcontainer/bin/container-session.mjs exec -- bash .git/phase15-evidence.sh inside | tee "$HOME/phase15/evidence-inside.txt"
```

## Run A — Criterion 1: an adopted repository, not this one

**Question:** does the launcher, copied into a repository adopted from the
template, reach a `claude` session where `check-auth.sh` passes?

**Use** `Eaiger-Ent/ee-standard-consumer`, which Phase 4 adopted. It is a real
adoption, with a `devcontainer.json` the template produced and an adopter edited.
Work in a **fresh clone**, not a checkout you use.

```bash
mkdir -p "$HOME/phase15" && cd "$HOME/phase15"
gh repo clone Eaiger-Ent/ee-standard-consumer
cd ee-standard-consumer
git switch -c phase15-apple-container
```

Copy the launcher in. This is the stand-in for the template shipping it:

```bash
mkdir -p .devcontainer/bin
cp "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/.devcontainer/bin/container-session.mjs" .devcontainer/bin/
```

Put the CLI pin where the launcher looks. The version comes from
`package.json` in the standard's checkout, never from memory, and the first line
reads it from there and prints it. The `npm init` line creates a `package.json`
only if the repository has none:

```bash
DEVCONTAINER_CLI_VERSION="$(node -p 'require(process.argv[1]).devDependencies["@devcontainers/cli"]' "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/package.json")" && echo "$DEVCONTAINER_CLI_VERSION"
[ -f package.json ] || npm init -y >/dev/null
npm install --save-dev --save-exact --no-audit --no-fund "@devcontainers/cli@${DEVCONTAINER_CLI_VERSION:?the first line did not read a version}"
node_modules/.bin/devcontainer --version
```

The last line must print the same version as the first. `ee-standard-consumer`
already has a `package.json`, so `npm init` is skipped, and the install modifies
that file and its `package-lock.json`. That is the stand-in's known side effect
(§ What these runs cannot yet test), not a mistake in the run.

Then start the services and open a session:

```bash
container system start
node .devcontainer/bin/container-session.mjs claude -n "${PWD:h:t}: ${PWD:t}"
```

`-n` names the session after the parent folder and the clone, here
`phase15: ee-standard-consumer`. `:h` and `:t` are zsh modifiers, and
[`06-devcontainer-setup.md`](06-devcontainer-setup.md) § 1 says why.

**Expected:** a first build of a few minutes. `up` ends with `check-auth.sh`'s
table, every line ✓. Inside `claude`, `/status` shows
`Session name: phase15: ee-standard-consumer`,
`Auth token: CLAUDE_CODE_OAUTH_TOKEN`, and `! id` shows `uid=1000(vscode)`. From
another terminal:

```bash
cd "$HOME/phase15/ee-standard-consumer"
container list
( set -a; . .devcontainer/.env; set +a; : "${GITHUB_TOKEN:?not in .devcontainer/.env}"
  ps -axww -o args | grep -c -F -f <(printf '%s\n' "$(printf '%s' "$GITHUB_TOKEN" | head -c 12)") )
```

`container list` should show the repository's `-dev` container, running. The
last command counts matches and never prints a value. **The count must be `0`.**
It sources `.env` in a subshell, so the token does not stay in your shell, and
it stops if the token is empty. An empty pattern matches every line, so the
count would be the number of processes. The prefix reaches `grep` through
`-f <(…)`, not its arguments, so `grep` does not count itself.
`scripts/phase15-evidence.sh host` makes the same check.

| Check | Result |
| --- | --- |
| `up` completes with the lock file unchanged (`git status` clean for `.devcontainer/devcontainer-lock.json`) | |
| `check-auth.sh` table, every line ✓ | |
| `claude` starts as `vscode`, token source `CLAUDE_CODE_OAUTH_TOKEN` | |
| Secrets in the host process list | |
| `uv run register-check` inside the container exits `3`. If not, which control and which check | |
| What the launcher refused, if anything, quoted | |
| Anything that needed a flag or step not named here | |

`3` assumes that every remote check either passes or cannot be read. Whether one
can be read depends on the token, not on the runtime. A token that can read
the adopted repository's settings turns a disabled setting into a `FAIL` and an
exit of `1`, while CI or a narrower token reports the same repository as `3`.
That is a finding about the repository, not about the launcher. Quote the
failing check, and do not tick the row until it is settled.

`ee-standard-consumer` has been **archived since 2026-09-03**. It is read-only,
and its settings cannot change without unarchiving it. A token that can read
them gets SEC-001's push-protection block as `disabled`, so expect the `1`
described above. Record it. Do not unarchive the repository to clear it.

Finish with `node .devcontainer/bin/container-session.mjs stop`.

### Run A — 2026-11-09, first pass

| Version | Value |
| --- | --- |
| Mac | `Mac14,9` (Apple M2 Pro), arm64 |
| macOS | 27.2 (`26B123`) |
| `container --version` | `container CLI version 1.7.1 (build: release, commit: a15b460)` |
| `node_modules/.bin/devcontainer --version` | `0.90.0` |
| Node.js | `v26.13.0` |
| Docker | Not on `PATH` |
| Clone | `ee-standard-consumer` at `2b89221`, a fresh clone on branch `phase15-apple-container` |

Claude Code ran this pass on the author's Mac. `up` and every check below went
through the launcher's `exec`. The interactive `claude` session and its
`/status` line were **not observed** in this pass. The 2026-11-17 pass below
observed them.

| Check | Result |
| --- | --- |
| `up` completes with the lock file unchanged | ✓ exit `0`. `devcontainer-lock.json` unchanged |
| `check-auth.sh` table, every line ✓ | ✓ six lines, all ✓ |
| `claude` starts as `vscode`, token source `CLAUDE_CODE_OAUTH_TOKEN` | `id` is `uid=1000(vscode)`. `CLAUDE_CODE_OAUTH_TOKEN` is set and `ANTHROPIC_API_KEY` is not. `claude -p` answered. The interactive session's `/status` was not observed |
| Secrets in the host process list | `0` for `GITHUB_TOKEN`, `0` for `CLAUDE_CODE_OAUTH_TOKEN` |
| `uv run register-check` inside the container exits `3` | **✗ exit `1`.** SEC-001 fails on `github_push_protection_enabled`, because push protection is `disabled` on `Eaiger-Ent/ee-standard-consumer`, which is archived (above). SEC-003 is unclassified, as expected. The cause is a repository setting, and Docker would see the same verdict |
| What the launcher refused, if anything, quoted | Nothing |
| Anything that needed a flag or step not named here | The findings and questions below |

Findings:

- **The CLI pin had to go into the adopter's own `package.json`.** The consumer
  already has a root `package.json` (for `markdownlint-cli2`), so the stand-in
  modified both it and `package-lock.json`. This is the change ADR 0064's
  `.devcontainer/package.json` avoids. The launcher resolves the CLI only at
  `<root>/node_modules/.bin/devcontainer`, so it needs that change too.
- **Memory is 1024 MB.** Apple `container` gives a container 1 GB unless told
  otherwise. This repository sets `--memory 8g` in `runArgs`, and the template
  does not. `up` and `uv sync` completed within that 1 GB, but no test suite ran
  in it. `06-devcontainer-setup.md` asks for 8 GB, so whether the template
  should carry `--cpus` and `--memory` is a decision for criterion 6.
- **Every `exec` re-runs `initializeCommand`**, and so reads the Keychain again.
  This is harmless, but it is noise at the head of every command.

Questions the author had to ask during this pass, each now answered in this
document:

1. Run A's `cp "$PATH_TO_EE_STANDARD_CHECKOUT/..."` failed, because the document
   used the variable and never said to set it. § What the host must have now
   sets it, and every use stops with a message when it is unset.
1. In the CLI-pin block, should `<that version>` be the first line's output?
   Yes, but a block pasted whole cannot carry a placeholder. The block now reads
   the version itself, and runs `npm init` only when no `package.json` exists.
1. When is `container` installed? The host table named it as a requirement but
   not how to meet it. `06-devcontainer-setup.md` § Installing Apple `container`
   is now a block that pastes whole. It downloads, checks the signature,
   installs, and stops on a signature that does not match.

### Run A, 2026-11-17

**Versions.** macOS 27.2.1, `Mac14,9`, arm64. `container` 1.7.1 (build:
release, commit `a15b460`). `devcontainer` 0.90.0 from `./node_modules/.bin`.
Node v26.13.1. The standard's checkout was at
[`ef81d61`](https://github.com/Eaiger-Ent/ee-standard/commit/ef81d61e492b8e1b667dd1d91fb0b70a4e527e86).
The launcher was copied from `f09e715`, and the launcher is identical at both
commits. `ee-standard-consumer` was at `2b89221`, on branch
`phase15-apple-container`. Inside the container: Linux 6.18.56 aarch64, `uv`
0.12.5, and `claude` 2.1.326 by `check-auth.sh`. `/status` in the session opened
minutes earlier showed 2.1.319. Docker was not on `PATH`. Two other Apple
containers were running on the host, `ee-standard-dev` and `ste-cc-dev`, and
the runbook assumed neither.

| Check | Result |
| --- | --- |
| `up` completes with the lock file unchanged | ✓ `.devcontainer/devcontainer-lock.json` is absent from `git status`. The tree changes are the stand-in's own: `package.json`, `package-lock.json` and `.devcontainer/bin/` |
| `check-auth.sh` table, every line ✓ | ✓ all six: GitHub CLI, Claude Code token, `claude`, `uv`, pre-commit hook, git |
| `claude` starts as `vscode`, token source `CLAUDE_CODE_OAUTH_TOKEN` | ✓ `/status` shows `Auth token: CLAUDE_CODE_OAUTH_TOKEN`, and `! id` shows `uid=1000(vscode) gid=1000(vscode) groups=1000(vscode),999(nvm)` |
| Secrets in the host process list | ✓ `0`, counted for `GITHUB_TOKEN` by `phase15-evidence.sh host` |
| `uv run register-check` inside the container exits `3`. If not, which control and which check | **✗ `1`, open.** SEC-001 `github_push_protection_enabled`: *"secret scanning push protection is 'disabled', not 'enabled'"*. Every local block of SEC-001 passed, and 11 controls passed, with SEC-003 unclassified as usual. The repository is archived (above). The same tree on a token that cannot read the setting exits `3` |
| What the launcher refused, if anything, quoted | Nothing was reported |
| Anything that needed a flag or step not named here | Six, listed below. Each is now in this document |

**Steps the document lacked.** Faults 1 to 4 were fixed in `723c41e`, fault 5 in
`a4575f8`, and fault 6 with this record.

1. `PATH_TO_EE_STANDARD_CHECKOUT` was used but never set, so `cp` read from `/`.
2. `#` comments in the code blocks: zsh passed them to `git` as arguments.
3. `<that version>` in a pasted block: zsh read it as a redirect, and the whole
   block failed to parse.
4. The secrets count read `742`. In the operator's shell `GITHUB_TOKEN` was empty,
   and an empty pattern matched every process. With the token set, `grep` would
   still have matched its own arguments.
5. `npm install --save-exact` without `--save-dev` put the CLI under
   `dependencies`.
6. The recorder's `inside` mode had no instructions. The container cannot see
   the standard's checkout, and the recorder's `written to:` path is inside the
   container.

**For the stand-in table.** The launcher resolves the CLI at
`<root>/node_modules/.bin/devcontainer` (`container-session.mjs`, `const CLI`),
so it needs a change before the pin can live in `.devcontainer/package.json`.
The stand-in also had to edit the adopter's own root `package.json`, because
this repository already had one. A shipped route that adds a file, and changes
none of the adopter's, avoids that.

**Not ticked.** Criterion 1 stays open on the `register-check` row.

### Recorded: `ste-cc`, 2026-11-10 (first attempt, partial record)

**Not evidence for criterion 1.** The operator reports the launcher reached a
working session, but the record below is missing the versions and the check
table this document says make a run count. It is kept because it is the only
attempt against a second adopted repository.

| What | Recorded |
| --- | --- |
| Repository | `ste-cc`, an adopted repository that is not this one, at `v0.11.1`, the newest tag. Docker was its runtime |
| Clone | A working checkout, **not** a fresh clone as Run A asks, on branch `apple-container-trial` |
| Operator | The author, not a second person |
| Launcher source | `container-session.mjs` fetched from this repository by commit SHA (`e16be9b`), sha256 starting `ddfd60e8b9d8f546`, because it is in no release tag |
| macOS, `container` and `devcontainer` versions, Mac model | **Not recorded** |
| `check-auth.sh` table, every line ✓ | **Not recorded** (operator reports it worked) |
| `devcontainer-lock.json` unchanged | **Not recorded** |
| Secrets in the host process list (must be `0`) | **Not recorded** |
| What the launcher refused | **Not recorded** (operator reports nothing blocked the run) |

Findings:

1. **The launcher is in no release.** Run A says to copy it from
   `$PATH_TO_EE_STANDARD_CHECKOUT`. An adopter has no such checkout and
   upgrading does not bring the file, so the first attempt failed with
   `Cannot find module .../container-session.mjs`. It is the first thing the
   shipped template must carry (Phase 15 criterion 6).
2. **The CLI pin went into the adopter's own `package.json`**, as in both Run A
   passes above. `ste-cc` had a root `package.json` with 89 packages and no
   `@devcontainers/cli`, so `npm ci` succeeded and left no
   `node_modules/.bin/devcontainer`. The open question, whether the launcher
   must change to find a pin under `.devcontainer/`, is the one the 2026-11-17
   pass records.

## Run B — Criterion 2: a second Mac, a second person

Run A again, from "a fresh clone", by **someone other than the author**, on a
**different Mac**. They follow this document and nothing else; if they need to
ask a question, that question is a finding, and the answer goes into the
document. The result table is Run A's, with these two lines added:

| Check | Result |
| --- | --- |
| Questions the operator had to ask | |
| Differences from Run A: hardware, macOS, `container` version, network | |

A second Mac on the **same** account and network is a weaker run than a second
person on their own. Say which this was.

## Run C — Criterion 3: the refusal rule against an adopter-shaped file

**Question:** when an adopter's `devcontainer.json` holds a key the launcher does
not handle, does it refuse by name, and not run a container that differs from
Docker's?

In Run A's clone, add one key the launcher's closed sets do not contain. The sets
are `CONFIG_KEYS`, `LABEL_KEYS`, `RUN_ARG_FLAGS` and `BUILD_VALUE_FLAGS` at the
head of `container-session.mjs`; read them rather than trusting a list here.
`forwardPorts` and `postAttachCommand` are the two an adopter is most likely to
write. Take each as its own run, and restore the file between them. Check that
`git stash list` holds nothing you want to lose, restore the file, add **one**
key, then run `up`:

```bash
git stash list
git checkout -- .devcontainer/devcontainer.json
```

```bash
node .devcontainer/bin/container-session.mjs up
```

**Expected:** `container-session: refused:` followed by the key's name, and a
non-zero exit, **before** any container is created. `container list` must not
show a new one.

| Key added | Refused by name? | Container created? | Exit code |
| --- | --- | --- | --- |
| | | | |
| | | | |

Also try one **runArgs** flag outside `--env-file`, `--cpus` and `--memory`
(`--cap-add` is the realistic one), since that is a different refusal path.
**A key that runs without a refusal and is silently dropped is the finding this
run exists to catch.** Record it exactly and stop; do not continue past it.

### Run C — 2026-11-09

The versions are Run A's 2026-11-09 pass, in Run A's clone, with Run A's
container present throughout. Each key was added on its own, and the file was
restored with `git checkout` between keys. `container list -a` was compared
before and after each `up`.

| Key added | Refused by name? | Container created? | Exit code |
| --- | --- | --- | --- |
| `"forwardPorts": [8000]` | Yes: `devcontainer.json: forwardPorts is not handled by this launcher` | No | `2` |
| `"postAttachCommand": "echo attached"` | Yes: `devcontainer.json: postAttachCommand is not handled by this launcher` | No | `2` |
| `runArgs` gains `"--cap-add", "SYS_PTRACE"` | Yes: `runArgs: --cap-add is not handled` | No | `2` |

No key ran without a refusal.

## Run D — Criterion 4: `adopt.sh` on a host with `container` and no Docker

**Question:** how does the guided route behave on a Mac with no Docker?

Today it fails, by design of the present scripts: `00-tools.sh` demands
`docker` and a `docker info` that answers, and `30-container.sh` looks for the
container with `docker ps`. This run records the **baseline**, so the change has
a measurable before and after, and then it is repeated once the scripts are
changed. The first line must print `no docker on PATH`:

```bash
command -v docker || echo "no docker on PATH"
cd "$HOME/phase15" && mkdir -p adopt-baseline && cd adopt-baseline
git init -q . && bash "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/adopt.sh" status
```

| Stage | Verdict | The message, quoted |
| --- | --- | --- |
| `00-tools.sh` — `docker` required | | |
| `00-tools.sh` — "Docker is running" | | |
| `30-container.sh` — the container-running check | | |
| Any other stage that mentions Docker | | |

**`inside_container()`** is the one check that cannot be read from the
scripts. From a shell **inside** the running Apple container from Run A:

```bash
ls -la /.dockerenv; echo "REMOTE_CONTAINERS=${REMOTE_CONTAINERS:-} CODESPACES=${CODESPACES:-}"
```

| Signal | Present in an Apple container? |
| --- | --- |
| `/.dockerenv` | |
| `REMOTE_CONTAINERS` | |
| `CODESPACES` | |

If none is present, `inside_container()` returns false there, and stage 0 would
run inside the container it should refuse to run in. That is a finding for
criterion 7, and the replacement signal belongs in the record.

**Re-run after the scripts change**, with the same table, expecting stage 0 and
stage 3 to pass with `container` answering and `docker` absent, and to say which
runtime they used. Record the second run beside the first.

### Run D, baseline — 2026-11-09

The versions are Run A's 2026-11-09 pass. `command -v docker` printed nothing,
so Docker was absent. `adopt.sh status` resolved `v0.11.1` and ran its scripts.

| Stage | Verdict | The message, quoted |
| --- | --- | --- |
| `00-tools.sh` — `docker` required | ✗ blocked | `✗ Docker — not on PATH  → START-HERE.md § B` |
| `00-tools.sh` — "Docker is running" | ✗ blocked | `✗ docker info fails — Docker Desktop is not running  → START-HERE.md § A` |
| `30-container.sh` — the container-running check | Passes (exit `0`) without looking | `Docker is not answering, so whether the container exists cannot be read from here.` Run in Run A's clone, with its Apple container **running** |
| Any other stage that mentions Docker | None | `_lib.sh` mentions `/.dockerenv` only in `inside_container()` |

Stage 0's other checks passed. The two Docker lines are its only failures, so
those are the whole of the change stage 0 needs. Stage 3 does not fail. It
cannot see an Apple container, says so, and moves on.

| Signal | Present in an Apple container? |
| --- | --- |
| `/.dockerenv` | No |
| `REMOTE_CONTAINERS` | No |
| `CODESPACES` | No |

The 2026-11-17 Run A container (`phase15-evidence.sh inside`) showed the same:
all three absent.

**Finding for criterion 7:** `inside_container()` returns false inside an Apple
container. Stage 0, run inside Run A's container, ran the host checks rather
than refusing. It reported Homebrew, Docker and the devcontainer CLI missing,
and `docker info` failing. Two replacement signals were present. The checks
cannot make the choice between them:

- `uname -s` is `Linux` inside the container. The guided route's host is a Mac,
  so this signal does not depend on which runtime is in use.
- `/proc/cmdline` holds `init=/sbin/vminitd`, Apple `container`'s guest init.
  This is specific to the runtime, and it is an implementation detail that
  could change.

There is no `/run/.containerenv`, and the container's environment holds only
what `--env-file` and the image set.

## Run E — Criterion 5: the migration, followed literally

**Question:** can a repository adopted at the **previous release** move to Apple
`container` by the written steps alone?

There is no written migration yet, so this run produces it. Take a clone adopted
at the release before the one you are testing, with Docker as its runtime, and
make the move **with `UPGRADING.md` open and nothing else**. Write each action as
you take it, in order, with its command and its observed result:

| # | Action | Command | Observed |
| --- | --- | --- | --- |
| 1 | | | |

**A first draft, from the `ste-cc` attempt under Run A**, to be replaced by a
run that follows `UPGRADING.md` with nothing else open. It is what an operator
did, not yet what the document should say, and it uses the stand-in for the
launcher:

| # | Action | Command | Observed |
| --- | --- | --- | --- |
| 1 | Branch off | `git switch -c apple-container-trial` | |
| 2 | Add the launcher | `curl -fsSL <raw URL at a pinned SHA> -o .devcontainer/bin/container-session.mjs` | Absent from the repository until now; `Cannot find module` without it |
| 3 | Check it is the tested file | `shasum -a 256 .devcontainer/bin/container-session.mjs` | Starts `ddfd60e8b9d8f546` |
| 4 | Add the CLI pin | `npm install --save-exact --no-audit --no-fund @devcontainers/cli@0.90.0` | `npm ci` alone left no `node_modules/.bin/devcontainer` |
| 5 | Start the runtime | `container system start` | |
| 6 | Open a session | `node .devcontainer/bin/container-session.mjs claude` | Operator reports it worked |

Steps 2 to 4 become one copy from the release tag once the template carries
the launcher and its pin. Step 4 edits files the adopter owns, the root
`package.json` and its lock file, so the text must either name them or put the
pin in `.devcontainer/`, whichever the open launcher question settles. Run A's
own block now adds `--save-dev`, which step 4 lacked.

**The steps become the text of `UPGRADING.md`'s optional step.** Then a second
person follows that text *literally*, on a second clone, and the run is ticked
only when they reach Run A's table with every line ✓ and no step performed from
memory. Say what the file set is that the move adds (the launcher, the CLI pin
and its lock file) and what it does **not** touch: the adopter's
`devcontainer.json`, the lock file, and the stamps on their gates. After the
move, from inside the Apple container:

```bash
uv run register-check deployments
git status --short
```

The first is not a conformance run, and the stamps it reports must be
unchanged. The second must list only the files the step named.

| Check | Result |
| --- | --- |
| Files added, exactly | |
| Files changed (must be none outside the named set) | |
| `register-check deployments` — stamps unchanged | |
| A repository the launcher **refuses** stays on Docker, and the refusal names why | |
| Steps the second person got wrong, and what the text lacked | |

## Where the results go

Under each run's heading in **this file**, with the versions it ran on, as
[`20-apple-container-spike.md`](20-apple-container-spike.md) does. Then tick the
criterion in [`04-build-plan.md`](04-build-plan.md) § Phase 15, and run
`uv run python scripts/plan_progress.py` to confirm the count moved. Never tick
one for a run that was not done, and never from a run whose versions went
unrecorded. A criterion that failed is left unticked, with the finding written
under it, and ADR 0064 is re-read against it.

**A run that needed a flag, a step or a file not named here is not a pass with a
footnote.** Record it, and put it in the document before the next person runs it.
