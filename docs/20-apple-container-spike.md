# Phase 14 — Apple `container` as a second runtime: the spike

The brief and the record for [`04-build-plan.md`](04-build-plan.md) § Phase 14.
The commands below are the brief. Each result goes under its spike, with the
versions it ran on. Nothing here is decided until an ADR decides it.

## The question

Can this repository's devcontainer run on Apple's
[`container`](https://github.com/apple/container) (1.0.0 released 2026-06-09,
1.7.1 on 2026-11-06) instead of Docker, for a **terminal and Claude CLI**
session, using no third-party tools? VS Code stays on Docker. The register is
not in question: DEV-001 and BLD-001 read files, and CI never reads
`devcontainer.json`.

## The approach under test

**The `devcontainer` CLI stays the only reader of `devcontainer.json`.** It is
already a host prerequisite (`06-devcontainer-setup.md` § 1). Apple
`container` only builds what the CLI generates and runs the result. Anything
else would be a second interpreter of the file, which is theme T-2.

**What was shown in the Docker-less devcontainer on 2026-11-08**, using
`@devcontainers/cli` 0.90.0 with `--docker-path` pointing at a stub that logs
its arguments and exits `0`:

- `devcontainer read-configuration --include-features-configuration
  --include-merged-configuration` exits `0`. It returns the merged
  `initializeCommand`, `runArgs`, `mounts`, `remoteUser`, `postCreateCommands`,
  `postStartCommands`, `init` and `privileged`, and each feature's metadata. Its
  only runtime calls are `docker ps` and `docker inspect --type image`.
- `devcontainer build --frozen-lockfile` exits `0` and leaves the lock file
  unchanged. It downloads the three features by their locked digests and writes
  a complete build context: a plain multi-stage `Dockerfile.extended` and a
  `Dockerfile.buildContent`. Its only runtime calls are two `docker build`s.
- The generated image carries `containerEnv` and the node feature's `NVM_DIR`
  and `PATH` as `ENV` lines, and the lifecycle commands, mounts and
  `remoteUser` in a `devcontainer.metadata` label.

The one Docker-specific step: the second build's `FROM` names
`dev_container_feature_content_temp`, a local image the first build created.

## Where to run it

On an Apple silicon Mac running macOS 26 or later, with Docker Desktop quit.
This is a deliberate exception to *work in the container, not on the host*. The
spike is about the host runtime, so it can only run on the host. Use the host
session for `container` and `devcontainer` commands and for recording results
here. Run every quality gate inside the Apple container, which is what S5 tests.

**Ground rules, settled 2026-11-08:**

- `container` is Apple's signed `.pkg` from its GitHub releases. The operator
  runs the installer, because it needs `sudo`.
- The `devcontainer` CLI is whatever the host has (0.88.0 on the first run),
  not upgraded to the 0.90.0 shown in the Docker-less container. The version
  goes in the record.
- The spike runs in a **separate clone**, so the working checkout's
  `.git/hooks` and `.devcontainer/.env` are never touched. Results are written
  here, in the working checkout. The clone's directory must be named
  `ee-standard`, because `fetch-secrets.sh` derives its Keychain prefix
  (`EE_STANDARD_`) from the directory name.
- Every `container run` takes `$RES` (8 GiB, 8 CPUs), the floor
  `06-devcontainer-setup.md` asks for. It is never run at the 1 GiB default.
- Each result records the versions it ran on and the image digests it used.
- A failed spike stops the spike. No fallback is tried until a fix has been
  agreed.
- `fetch-secrets.sh` is unchanged. It runs on the Mac and needs no Docker. An
  Apple container is a Linux VM with no route to the Keychain, so the split
  between host secrets and the container stays as it is.
- Steps that need a person: running the installer, Keychain prompts, the
  interactive `claude`, and Activity Monitor readings.

Set up and record first, from the working checkout:

```bash
SRC=$PWD
git clone "$SRC" "$HOME/spike/ee-standard"      # the basename must stay ee-standard
cd "$HOME/spike/ee-standard"
git remote set-url origin "$(git -C "$SRC" remote get-url origin)"
RES="--cpus 8 --memory 8g"

sw_vers -productVersion; uname -m; sysctl -n hw.ncpu hw.memsize
container system start && container --version
devcontainer --version
command -v jq plutil
```

### Pre-flight record, 2026-11-08

**Host.** macOS 27.2, arm64, 12 CPUs, 32 GiB. `devcontainer` 0.88.0
(Homebrew). `jq` from Homebrew and `plutil` from `/usr/bin` are both present.

**Install.** `container-1.7.1-installer-signed.pkg` came from the `apple/container`
1.7.1 release, downloaded with `gh release download`. The release also ships
`container-installer-unsigned.pkg`. A `*.pkg` glob matched both, and
`installer` refused two arguments, so the package has to be named. Signature
check before install:

```text
Status: signed by a developer certificate issued by Apple for distribution
Notarization: trusted by the Apple notary service
Signed with a trusted timestamp on: 2026-11-07 00:10:04 +0000
1. Developer ID Installer: Apple Inc. - Containerization (UPBK2H6LZM)
   SHA256 45 19 B4 3D 00 F5 5E C6 31 38 D4 03 DE 1F 3C 54 23 90 EA E3 D8 2E
          59 C1 84 38 46 FB DF E1 4F 5B
2. Developer ID Certification Authority
3. Apple Root CA
```

The install was run as an admin account, because the developer account has no
`sudo`. That is the only step that needed admin. The receipt is
`com.apple.container-installer`, and `/usr/local/bin/container` reports
`container CLI version 1.7.1 (build: release, commit: a15b460)` to the
developer account. A second install run reported "Upgrading" over the first,
after an unrelated `su` password failure. There was no earlier version.

**Docker at pre-flight.** Docker Desktop was still running, from an
`AppTranslocation` path, so it was launched from a quarantined location. Its
processes: `com.docker.backend` (×3), `com.docker.build`,
`com.docker.virtualization` (VM at `--cpus 10 --memoryMiB 24576`, `--rosetta`,
virtiofs shares of `/Users`, `/tmp` and `/var/folders`), `Docker Desktop` and
its helpers. There were also two `docker exec -u vscode` processes from a VS
Code Dev Containers session in another repository. One of them carried the
container's whole environment as `-e` arguments, which is the finding below.

## S1 — The features become an image

**Gap.** Apple `container` has no notion of a feature. Pass when the image
built from the CLI's context runs `gh`, `node` and `claude` as `vscode`, with
nvm on `PATH`.

```bash
SPIKE=$(mktemp -d); mkdir -p "$SPIKE/stub" "$SPIKE/tmp"
printf '#!/bin/sh\necho "stub docker: $*" >&2\nexit 0\n' > "$SPIKE/stub/docker"
chmod +x "$SPIKE/stub/docker"

TMPDIR="$SPIKE/tmp" devcontainer build --workspace-folder . --frozen-lockfile \
  --image-name ee-standard-dev:local --docker-path "$SPIKE/stub/docker" \
  --log-level trace 2> "$SPIKE/build.log"
git status --short .devcontainer          # expect nothing
grep 'stub docker: build' "$SPIKE/build.log"   # the two builds to replay
```

Replay each logged `build` line with `container build` in place of
`docker build`, keeping its `-t`, `-f`, `--build-arg`, `--target` and context
exactly as logged. Copy them from the log rather than retyping them, so the
base image digest has one source. Then:

```bash
container run --rm $RES -u vscode ee-standard-dev:local \
  bash -lc 'gh --version; node --version; claude --version; echo "$PATH"'
container image inspect ee-standard-dev:local    # record the digest
```

**If the second build cannot find `dev_container_feature_content_temp`**, the
builder cannot see local images. Stop and record it. G1-b is the candidate fix,
for agreement before it is tried: replace that `FROM` line with a `FROM scratch`
stage that `COPY`s the feature directory, and build once with the feature
directory as the context.

Result: *not yet run.*

## S3 — The workspace is writable by `vscode`

**Gap.** Apple's own `volumes.md` example shows a bind-mounted host file as
`root root`. If `vscode` cannot write the checkout, nothing works. Running as
root instead would make BLD-001's `remoteUser` declared but unreachable. Pass
when the write succeeds and the file appears on the Mac owned by you.

```bash
container run --rm $RES -u vscode -v "$PWD":/w -w /w ee-standard-dev:local \
  bash -c 'id; stat -c "%U:%G %a" . .git; touch .s3 && rm .s3 && echo WRITE-OK
           git -c safe.directory=/w status --short | head -3'
```

If it fails, the spike stops here. Without a writable workspace there is
nothing for S2 to S5 to run on, and the fix needs agreeing first. Candidates to
record: G3-b, the workspace in a named volume (`container volume create`, then
clone inside), and G3-c, running as the host uid.

Result: *not yet run.*

## S2 — The lifecycle, by hand

**Gap.** `devcontainer up` drives `initializeCommand`, `runArgs`, `mounts`,
`remoteUser` and the lifecycle commands through the Docker CLI. Run the steps
by hand once, taking each value from `read-configuration` rather than from
`devcontainer.json`:

```bash
devcontainer read-configuration --workspace-folder . \
  --include-merged-configuration --docker-path "$SPIKE/stub/docker" \
  > "$SPIKE/merged.json"
jq '.mergedConfiguration | {initializeCommand, runArgs, mounts, remoteUser,
  postCreateCommands, postStartCommands, init, privileged}' "$SPIKE/merged.json"
```

Then, in order: run `initializeCommand` on the host, in the clone. It needs no
Docker and may show Keychain prompts. The clone has no `.env` yet, so this run
creates it. Start the container detached with `$RES`, the `runArgs`, the volume
mount
(`--mount type=volume,source=…,target=…`), the workspace from S3 and a
keep-alive entrypoint. Run `postCreateCommands`, then `postStartCommands`, with
`container exec -u vscode`. Finally `container exec -it -u vscode … claude`.

Pass when `setup.sh` completes, `check-auth.sh` reports Claude and `gh` as
authenticated, `claude` starts as `vscode`, and `GIT_AUTHOR_NAME` (a value with
a space) arrives intact through `--env-file`, and no secret's value appears in
the host's process list while the session is open. Check with
`ps -axww -o args | grep -c "$(head -c 12 <<<"$GITHUB_TOKEN")"` after sourcing
the clone's `.env` into a subshell, which counts matches and never prints a
value. `ee-standard-claude-home` is a new
Apple volume, empty of Docker's state, so expect to re-authenticate the first
interactive `claude`. That is not a failure. Record any step that needed a flag
not named here.

Result: *not yet run.*

## S4 — Memory

**Gap.** An Apple container is a VM of 1 GiB and 4 CPUs by default
(`resource-usage.md`). `06-devcontainer-setup.md` asks for 8 GB. Memory the
guest frees is not returned to macOS until the container restarts.

Run `npm ci --no-audit --no-fund` and `uv run pytest` with `$RES`. Do not run
them at the default. First confirm the guest sees 8 GiB and 8 CPUs (`free -g`,
`nproc`). Record peak usage from `container stats --no-stream` and Activity
Monitor, and whether host memory drops after the run. If the container cannot
be given 8 GiB and more CPUs than the default, or either command fails within
them, the spike stops. A pass puts the resource flags in `runArgs`.

Result: *not yet run.*

## S5 — A full session

Inside the Apple container, as `vscode`, on the workspace S3 chose:

```bash
uv sync --frozen && uv run pytest
uv run register-check; echo "exit=$?"     # expect 3, as on Docker
git push --dry-run                        # pre-push hook runs, nothing sent
```

Pass when `pytest` passes, `register-check` exits `3`, and the pre-push hook
runs.

Result: *not yet run.*

## Found along the way

### VS Code puts the container's secrets in the host process list

Not specific to this path, and more serious than anything above. At
pre-flight, `pgrep -lf docker` on the Mac printed a VS Code Dev Containers
`docker exec -i -t -u vscode … zsh` whose arguments included
`-e GITHUB_TOKEN=…`, `-e EE_SKILLS_GITHUB_TOKEN=…` and
`-e CLAUDE_CODE_OAUTH_TOKEN=…` in clear text, along with every other variable
of the container's environment. Any process on the Mac that can list processes
can read them, and so can a tool transcript that prints them. That is how they
reached this session's output. All three are treated as exposed and are to be
rotated. The values are not recorded here.

`runArgs` uses `--env-file` precisely to keep secrets off a command line
(`fetch-secrets.sh`). That protects `docker run`. The editor's `docker exec`
for each terminal re-sends the resolved environment as arguments, which
bypasses it. So SEC-001's file-level controls hold, and the host still leaks
the values at runtime.

Two consequences for this phase. First, a host launcher for Apple `container`
must never pass a secret as an argument. That means `--env-file` on `run`, and
nothing secret on `exec`. S2 should check `ps` on the host while a session is
open. Second, no tool in a spike session should print full host command lines
(`pgrep -l`, not `pgrep -lf`).

### The lock file pins installers, not binaries

Not specific to this path. The lock file pins each feature's *installer*, not
what it installs. The resolved options show `github-cli` at `version: latest`,
and `node` at `nvmVersion: latest` and `pnpmVersion: latest`. So a Docker
rebuild can already pull newer binaries under an unchanged lock file.
