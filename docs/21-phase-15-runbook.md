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
| Apple `container` 1.7.1 or later | `container --version`, and `container system start` has run |
| **Docker Desktop quit, and not installed for Run D** | `docker info` fails or `docker` is not on `PATH`. A run with Docker answering proves nothing |
| Node.js | `node --version` |
| `gh` authenticated to `Eaiger-Ent` | `gh auth status` |
| `claude setup-token` done, and the Keychain entries | [`08-adopting.md`](08-adopting.md) § 2.0a. `.devcontainer/fetch-secrets.sh` reads them |

**Record, for every run:** the date, the macOS version, `container --version`,
`node_modules/.bin/devcontainer --version`, and the Mac's model. A run without
its versions is not evidence.

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

# The stand-in for the template shipping the launcher.
mkdir -p .devcontainer/bin
cp "$PATH_TO_EE_STANDARD_CHECKOUT/.devcontainer/bin/container-session.mjs" .devcontainer/bin/
```

Put the CLI pin where the launcher looks. The version comes from
`package.json` in the standard's checkout, never from memory:

```bash
grep '"@devcontainers/cli"' "$PATH_TO_EE_STANDARD_CHECKOUT/package.json"
npm init -y >/dev/null          # only if the repository has no package.json
npm install --save-exact --no-audit --no-fund @devcontainers/cli@<that version>
node_modules/.bin/devcontainer --version
```

Then start the services and open a session:

```bash
container system start
node .devcontainer/bin/container-session.mjs claude
```

**Expected:** a first build of a few minutes. `up` ends with `check-auth.sh`'s
table, every line ✓. Inside `claude`, `/status` shows
`Auth token: CLAUDE_CODE_OAUTH_TOKEN` and `! id` shows `uid=1000(vscode)`. From
another terminal:

```bash
container list                      # the repo's -dev container, running
ps -axww -o args | grep -c "$(head -c 12 <<<"$GITHUB_TOKEN")"
```

The second command counts matches and never prints a value. Source `.env` in a
subshell first, as the spike did. **The count must be `0`.**

| Check | Result |
| --- | --- |
| `up` completes with the lock file unchanged (`git status` clean for `.devcontainer/devcontainer-lock.json`) | |
| `check-auth.sh` table, every line ✓ | |
| `claude` starts as `vscode`, token source `CLAUDE_CODE_OAUTH_TOKEN` | |
| Secrets in the host process list | |
| `uv run register-check` inside the container exits `3` | |
| What the launcher refused, if anything, quoted | |
| Anything that needed a flag or step not named here | |

Finish with `node .devcontainer/bin/container-session.mjs stop`.

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
write. Take each as its own run, and restore the file between them.

```bash
git stash list                      # nothing you want to lose
git checkout -- .devcontainer/devcontainer.json
# add ONE key, then:
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

## Run D — Criterion 4: `adopt.sh` on a host with `container` and no Docker

**Question:** how does the guided route behave on a Mac with no Docker?

Today it fails, by design of the present scripts: `00-tools.sh` demands
`docker` and a `docker info` that answers, and `30-container.sh` looks for the
container with `docker ps`. This run records the **baseline**, so the change has
a measurable before and after, and then it is repeated once the scripts are
changed.

```bash
command -v docker || echo "no docker on PATH"       # must print the second
cd "$HOME/phase15" && mkdir -p adopt-baseline && cd adopt-baseline
git init -q . && bash "$PATH_TO_EE_STANDARD_CHECKOUT/adopt.sh" status
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

**The steps become the text of `UPGRADING.md`'s optional step.** Then a second
person follows that text *literally*, on a second clone, and the run is ticked
only when they reach Run A's table with every line ✓ and no step performed from
memory. Say what the file set is that the move adds (the launcher, the CLI pin
and its lock file) and what it does **not** touch: the adopter's
`devcontainer.json`, the lock file, and the stamps on their gates. After the
move, from inside the Apple container:

```bash
uv run register-check deployments   # not a conformance run; the stamps must be unchanged
git status --short                  # only the files the step named
```

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
