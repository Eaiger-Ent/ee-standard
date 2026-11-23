# Phase 15 — Apple `container` for adopters: the run sheet

The runbook for the five evidence criteria at the head of
[`04-build-plan.md`](04-build-plan.md) § Phase 15. [ADR 0064](adr/archive/0064-an-adopter-may-run-its-devcontainer-on-apple-container.md)
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

**Since 2026-11-23, [ADR 0065](adr/archive/0065-the-adopt-route-accepts-either-runtime-now.md)
ships the launcher in the template and the runtime-aware scripts**, and
[ADR 0066](adr/0066-apple-container-is-a-first-class-engine.md) makes Apple `container` a
first-class engine and waives Run B. The
runs below are evidence rather than a gate. A run made from a checkout at or
after that change tests the shipped files, not a stand-in. The paragraphs below
describe the runs made before it. Before then nothing under
`plugins/control-register/templates/` had changed, so an adopter had no
launcher. Runs A–C copy it in by hand. That is a stand-in, and it is the
reason the criteria are about the **launcher**, not about the shipped template.
Three differences between the stand-in and the decision are findings to record,
not defects to fix during the run:

| The decision (ADR 0064) | What the stand-in does | Record |
| --- | --- | --- |
| The CLI pin is in `.devcontainer/package.json` | The same, put there by hand. The launcher finds the CLI under `.devcontainer/` or the root, and refuses when both are installed (Run A's finding, fixed after it) | Nothing, unless the launcher refuses the pin |
| `adopt.sh` accepts either runtime | It does not yet, so Run D runs the **current** scripts to record their baseline | Which stage fails first, and with what message |
| `UPGRADING.md` carries the migration | It does not yet, so Run E *writes* the steps as you perform them | The steps, in order, as the text for `UPGRADING.md` |

## What the host must have

| Requirement | Verify with |
| --- | --- |
| Apple silicon Mac, macOS 26 or later | `sw_vers -productVersion` and `uname -m` |
| Apple `container` 1.7.1 or later | `container --version`, and `container system start` has run |
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
the pinned CLI's `--version` with the path it was run from
(`.devcontainer/node_modules/.bin/devcontainer`, or `node_modules/.bin/devcontainer`
in a clone pinned at the root), the standard checkout's commit, and the Mac's
model. A run without its versions is not evidence.

`scripts/phase15-evidence.sh` records those observations and the ones the runs
below ask for, and decides nothing: `host` on the Mac, `inside` from a shell in
the Apple container, and `run -- COMMAND` around a launcher command (Run C's
refusal, its exit code and whether a container appeared). It writes to
`~/phase15`, holds no secret and no username, and is a recorder, not a
substitute for this document. Paste what it wrote under the run's heading.

Both modes run **from the adopted clone**, once a run has one, so they belong
after Run A's clone exists and its container is up. Set `PHASE15_RUN` to the
run's letter first, such as `PHASE15_RUN=a`, so each run keeps its own record
rather than overwriting the last. `host` reads `.devcontainer/.env` in the
clone:

```bash
bash "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/scripts/phase15-evidence.sh" host | tee "$HOME/phase15/evidence-host-${PHASE15_RUN:?set it to the run letter}.txt"
```

The container cannot see the standard's checkout, so `inside` needs a copy in
the clone's `.git/`. The container sees that folder, and `git status` does not
list it. Keep the record with `tee`, because the `written to:` path it prints
is inside the container:

```bash
cp "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/scripts/phase15-evidence.sh" .git/
node .devcontainer/bin/container-session.mjs exec -- bash .git/phase15-evidence.sh inside | tee "$HOME/phase15/evidence-inside-${PHASE15_RUN:?set it to the run letter}.txt"
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

Put the CLI pin in `.devcontainer/`, where ADR 0064 puts it, so the
adopter's own root `package.json` is untouched. The version comes from
`.devcontainer/package.json` in the standard's checkout, never from memory (it
was the root `package.json` before ADR 0066), and the first line
reads it from there and prints it. The second line creates
`.devcontainer/package.json` only if there is none:

```bash
DEVCONTAINER_CLI_VERSION="$(node -p 'require(process.argv[1]).devDependencies["@devcontainers/cli"]' "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/.devcontainer/package.json")" && echo "$DEVCONTAINER_CLI_VERSION"
[ -f .devcontainer/package.json ] || ( cd .devcontainer && npm init -y >/dev/null )
npm install --prefix .devcontainer --save-dev --save-exact --no-audit --no-fund "@devcontainers/cli@${DEVCONTAINER_CLI_VERSION:?the first line did not read a version}"
.devcontainer/node_modules/.bin/devcontainer --version
```

The last line must print the same version as the first. A clone set up before
this step changed has its pin in the **root** instead. The launcher still finds
it there, but refuses if a second pin is installed under `.devcontainer/`, so
use one or the other.

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

### Run B, waived 2026-11-23

**Not run.** No second person with a second Mac was available, and none is
expected. [ADR 0066](adr/0066-apple-container-is-a-first-class-engine.md) point
6 waives this run, on the owner's report that Apple `container` is in daily use
and working well. Criterion 2 is ticked as **waived**, which is not a pass. The
gap it leaves is that no second operator has followed this document, so any
step that only the author knows has not been found. Runs C, D and E still stand.
If someone becomes available, run it as written above and record the result
here. A failure re-opens ADR 0066.

## Run C — Criterion 3: the refusal rule against an adopter-shaped file

**Question:** when an adopter's `devcontainer.json` holds a key the launcher does
not handle, does it refuse by name, and not run a container that differs from
Docker's?

Work in Run A's clone, with the launcher **copied in again** from the checkout
under test. The copy Run A made is older than the launcher this run tests: it
refuses even an empty `forwardPorts`, and cannot find a pin under
`.devcontainer/`. The last line prints the commit to record:

```bash
cd "$HOME/phase15/ee-standard-consumer"
cp "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/.devcontainer/bin/container-session.mjs" .devcontainer/bin/
git -C "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}" rev-parse HEAD
```

A clone pinned at the root in Run A keeps that pin. Do not add a second one
under `.devcontainer/`, because the launcher refuses two.

Add one key the launcher's closed sets do not contain. The sets
are `CONFIG_KEYS`, `LABEL_KEYS`, `RUN_ARG_FLAGS` and `BUILD_VALUE_FLAGS` at the
head of `container-session.mjs`; read them rather than trusting a list here.
There are three runs, one change each, in `.devcontainer/devcontainer.json`:

1. `"forwardPorts": [3000]`. It must name a port: the launcher accepts an empty
   list, because the CLI publishes nothing from it, and refuses one that names a
   port, because no editor is there to forward it.
2. `"postAttachCommand": "echo attached"`.
3. `"--cap-add", "SYS_PTRACE"` appended to the existing `runArgs` array. A flag
   outside `--env-file`, `--cpus` and `--memory` takes a different refusal path
   from a key.

Before each, check that `git stash list` holds nothing you want to lose, and
restore the file:

```bash
git stash list
git checkout -- .devcontainer/devcontainer.json
```

Make the one change, then run `up` under the recorder. Its `run` mode takes a
`container list` snapshot before and after, so a container created by the run
shows as a difference even while Run A's container still exists:

```bash
bash "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/scripts/phase15-evidence.sh" run -- node .devcontainer/bin/container-session.mjs up
```

**Expected:** `container-session: refused:` followed by the key's or flag's
name, a non-zero exit, and the two snapshots the same. Restore the file after
the third run.

| Change | Refused by name? (quote it) | Snapshots the same? | Exit code |
| --- | --- | --- | --- |
| `forwardPorts: [3000]` | | | |
| `postAttachCommand` | | | |
| `runArgs` `--cap-add` | | | |

**A key that runs without a refusal and is silently dropped is the finding this
run exists to catch.** Record it exactly and stop; do not continue past it.

## Run D — Criterion 4: `adopt.sh` on a host with `container` and no Docker

**Question:** how does the guided route behave on a Mac with no Docker?

Today it fails, by design of the present scripts: `00-tools.sh` demands
`docker` and a `docker info` that answers, and `30-container.sh` looks for the
container with `docker ps`. This run records the **baseline**, so the change has
a measurable before and after, and then it is repeated once the scripts are
changed.

**Run the stage scripts from the checkout under test, not through `adopt.sh`.**
`adopt.sh` clones the newest **tag** and runs that copy, so it would test the
released scripts, and the re-run below would test them again rather than the
change. `status.sh` runs every stage with its output discarded, so it shows a
verdict per stage but none of the messages this table quotes. The stages are
therefore run one at a time, and `status.sh` once for its summary. None of
them changes a tracked file.

Use Run A's clone, with its container **running**. In an empty folder, stage 3
stops at "no `.devcontainer`" and never reaches the container check. Run each
command on its own. The first must print `no docker on PATH`:

```bash
command -v docker || echo "no docker on PATH"
```

```bash
cd "$HOME/phase15/ee-standard-consumer"
node .devcontainer/bin/container-session.mjs up
ADOPT_ROUTE="${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/plugins/control-register/templates/adopt"
```

```bash
bash "$ADOPT_ROUTE/00-tools.sh"; echo "exit $?"
```

```bash
bash "$ADOPT_ROUTE/30-container.sh"; echo "exit $?"
```

```bash
bash "$ADOPT_ROUTE/status.sh"; echo "exit $?"
```

| Stage | Verdict | The message, quoted |
| --- | --- | --- |
| `00-tools.sh`: the `Docker` tool | | |
| `00-tools.sh`: the `devcontainer CLI` tool. The launcher uses the pinned CLI, not one on `PATH` | | |
| `00-tools.sh`: "Docker is running" | | |
| `00-tools.sh`: exit code | | |
| Where the clone's CLI pin is: `.devcontainer/` or the root | | |
| `30-container.sh`: "Nothing left to substitute". In a clone pinned under `.devcontainer/` it reports "a placeholder survived", naming files under `.devcontainer/node_modules/`. The scan reads every file there, and the CLI's own code contains `{{`. That is a finding for criterion 7, not a fault in the run. Quote the first file it names | | |
| `30-container.sh`: the "Built" section. With Docker absent it may print a note and fail nothing, which would pass the stage without checking the container | | |
| `30-container.sh`: exit code | | |
| `status.sh`: "on the host" or "inside the container", and each stage's verdict | | |
| Any other line that mentions Docker | | |

**Inside the container.** `inside_container()` is the one check that cannot be
read from the scripts. The container cannot see the standard's checkout, so copy
the route into the clone's `.git/` as the recorder is (§ What the host must
have), then run the recorder's `inside` mode and `status.sh` there. The first
line removes an earlier copy, because on the re-run `cp -R` would otherwise copy
the new route **inside** the old one and `status.sh` would run the old scripts:

```bash
rm -rf .git/phase15-adopt
cp -R "$ADOPT_ROUTE" .git/phase15-adopt
cp "${PATH_TO_EE_STANDARD_CHECKOUT:?set it first, see What the host must have}/scripts/phase15-evidence.sh" .git/
node .devcontainer/bin/container-session.mjs exec -- bash .git/phase15-evidence.sh inside | tee "$HOME/phase15/evidence-inside-d.txt"
node .devcontainer/bin/container-session.mjs exec -- bash .git/phase15-adopt/status.sh; echo "exit $?"
```

| Signal or verdict | Inside the Apple container |
| --- | --- |
| `/.dockerenv` | |
| `REMOTE_CONTAINERS` | |
| `CODESPACES` | |
| `/proc/cmdline` `init=` | |
| `status.sh`: "on the host" or "inside the container" | |
| `status.sh`: the verdict for `00-tools.sh` and for `40-adopt.sh` | |

If none is present, `inside_container()` returns false there, and stage 0 would
run inside the container it should refuse to run in. That is a finding for
criterion 7, and the replacement signal belongs in the record.

**Recorded 2026-11-17, from Run A's container** (`phase15-evidence.sh inside`).
`/.dockerenv` is absent, `REMOTE_CONTAINERS` is empty, and `CODESPACES` is
empty. **None is present**, so the finding above stands for criterion 7. Run D's
baseline of the scripts themselves has not been run.

**The replacement signal, chosen 2026-11-18:** the kernel's boot line names
Apple's init. In an Apple container `/proc/cmdline` holds
`init=/sbin/vminitd`, the init of the Containerization framework that
`container` boots each container's VM with. The runtime sets it, not the
launcher, so it holds however the container was started, and any user can read
it. For criterion 7, `inside_container()` gains one check:

```bash
grep -q 'init=/sbin/vminitd' /proc/cmdline 2>/dev/null && return 0
```

It was observed in `ee-standard-dev`, started by the launcher (`container`
1.7.1, kernel 6.18.56 aarch64), where the three existing signals were again
absent. PID 1 there is the launcher's keep-alive command, which is close to the
CLI's own on Docker and so names no runtime, and the cgroup is `0::/`. Its risk
is that `vminitd` is Apple's implementation detail, so a `container` release
could rename it. `phase15-evidence.sh inside` now records the `init=` token, so
Runs B and D confirm it on another Mac and in an adopted repository, and a
release that changes it shows up there.

**Re-run after the scripts change**, with the same commands and tables, from a
checkout that holds the change. Expect stage 0 and stage 3 to pass with
`container` answering and `docker` absent, and to say which runtime they used.
Inside the container, expect `status.sh` to say "inside the container", with
`00-tools.sh` marked `n/a here`. Record the second run beside the first.

## Run E — Criterion 5: the migration, followed literally

**Question:** can a repository adopted at the **previous release** move to Apple
`container` by the written steps alone?

**Since ADR 0066 the step exists.** It is `UPGRADING.md` § 3, *Moving past
register contract 38*, and it changes two of the files the tables below say it
must not: `.devcontainer/.gitignore` gains `node_modules/`, and `runArgs` gains
the resource floor if the repository will run on Apple `container`. E1 now
follows that step and corrects it, rather than writing one from nothing. Its
draft below replaces the step's text if they differ, and E2 follows the
corrected step.

**Use** a fresh clone of `Eaiger-Ent/ee-standard-consumer`, made for this run.
Its adoption predates the newest tag, so it is at "the previous release", and
Docker was its runtime. It is archived, and that does not matter here, because
the move pushes nothing. No release ships the launcher yet, so the files the
move adds come from the checkout under test, as in Run A. That is the stand-in
for "the tag you upgraded to".

The run has two halves and needs two people.

### E1: the author writes the step

There is no written migration yet, so the first operator **produces** it. The
starting point is Run A's two copying steps and its `claude` line. Those are the
steps for a repository with nothing on Apple `container` yet, which is what a
Docker adopter has.

**Start clean.** The launcher names the container and image after the clone's
folder, and the volumes come from the adopter's `devcontainer.json`. So any
clone named `ee-standard-consumer` on a Mac that ran Run A would reuse Run A's
container, image and volumes, and the move would not start from what a Docker
adopter has. Remove all three. This deletes Run A's container state, which is
already recorded above. The commands need no clone, and on a Mac that never ran
Run A they report that nothing was found, which is fine:

```bash
container stop ee-standard-consumer-dev
container delete ee-standard-consumer-dev
container image delete ee-standard-consumer-dev:local
container volume list
```

Delete each listed volume whose name is a `source=` value in the consumer's
`.devcontainer/devcontainer.json`, one `container volume delete` per name. The
pulled base image and the builder's cache are left in place, so the build that
follows can be faster than an adopter's first one. Record its time, but not as
a first-build figure.

Then make the clone, in a folder of this half's own, and record the release it
was adopted at, which is the tag its `register-check` dependency names:

```bash
mkdir -p "$HOME/phase15/run-e1" && cd "$HOME/phase15/run-e1"
gh repo clone Eaiger-Ent/ee-standard-consumer
cd ee-standard-consumer
git rev-parse HEAD
grep -n 'register-check' pyproject.toml
```

Make the move. Write each action into this table **as you take it**, with its
exact command and what you saw, including anything you had to work out:

| # | Action | Command | Observed |
| --- | --- | --- | --- |
| 1 | | | |

Put the table's steps, as prose and commands an adopter can follow, under a
`### Run E draft step` heading at the end of this section. That draft is the
text that goes into `UPGRADING.md` with criterion 8. It must say:

- what the move **adds**: the launcher, `.devcontainer/package.json` and its lock
  file, and nothing else;
- what it does **not** touch: the adopter's `devcontainer.json`, its
  `devcontainer-lock.json`, and the stamps on their gates;
- what to do when the launcher **refuses**: stay on Docker, and keep the refusal,
  because it names what the launcher could not reproduce.

### E2: a second person follows the draft literally

A second person, not the author, on **their own Mac** where they can, runs
**Start clean**, then the clone commands with `run-e2` in place of `run-e1` in
both places, then follows the draft step **and nothing else**. On the author's
Mac, `run-e2` keeps the two clones apart and **Start clean** removes E1's
container. Say which Mac it was. No step may be done from
memory, and no question may be answered outside the text. A question is a
finding, and its answer goes into the draft. The run passes only when they reach
Run A's table with every line ✓.

### After the move, both halves

From inside the Apple container:

```bash
git status --short
uv run register-check deployments; echo "exit $?"
```

`git status` must list only the files the draft names. A stamp lives in a
tracked file, so a stamped file missing from that list is a stamp unchanged.
`register-check deployments` is not a conformance run. It exits non-zero only
for a stamp ahead of its gate or a record that has stopped describing reality,
so a non-zero exit here is a finding. Quote its output either way.

| Check | E1 | E2 |
| --- | --- | --- |
| Files added, exactly. If `.devcontainer/node_modules/` is listed, the repository's `.devcontainer/.gitignore` does not ignore it, which is a finding for the draft | | |
| Files changed, which must be none | | |
| `register-check deployments`: exit code, and no stamped file in `git status` | | |
| The draft says what a refused repository does, and that it stays on Docker | | |
| Run A's table, every line ✓ | | |
| Steps the second person got wrong, and what the text lacked | n/a | |

## Where the results go

Under each run's heading in **this file**, with the versions it ran on, as
[`20-apple-container-spike.md`](20-apple-container-spike.md) does. Then tick the
criterion in [`04-build-plan.md`](04-build-plan.md) § Phase 15, and run
`uv run python scripts/plan_progress.py` to confirm the count moved. Never tick
one for a run that was not done, and never from a run whose versions went
unrecorded. The one exception is a run an ADR waives, as ADR 0066 waived Run B.
It is ticked with the word **Waived** and its reason, and recorded as not run.
A criterion that failed is left unticked, with the finding written under it,
and ADR 0066 is re-read against it.

**A run that needed a flag, a step or a file not named here is not a pass with a
footnote.** Record it, and put it in the document before the next person runs it.
