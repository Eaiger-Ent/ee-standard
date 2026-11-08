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

On an Apple silicon Mac running macOS 26, with Docker Desktop quit. This is a
deliberate exception to *work in the container, not on the host*. The spike is
about the host runtime, so it can only run on the host. Use the host session
for `container` and `devcontainer` commands and for recording results here.
Run every quality gate inside the Apple container, which is what S5 tests.

Record first:

```bash
sw_vers -productVersion; uname -m
container system start && container --version
devcontainer --version
command -v jq plutil
```

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
container run --rm -u vscode ee-standard-dev:local \
  bash -lc 'gh --version; node --version; claude --version; echo "$PATH"'
```

**If the second build cannot find `dev_container_feature_content_temp`**, the
builder cannot see local images. Fallback G1-b: replace that `FROM` line with a
`FROM scratch` stage that `COPY`s the feature directory, and build once with
the feature directory as the context. Record which variant passed.

Result: *not yet run.*

## S3 — The workspace is writable by `vscode`

**Gap.** Apple's own `volumes.md` example shows a bind-mounted host file as
`root root`. If `vscode` cannot write the checkout, nothing works. Running as
root instead would make BLD-001's `remoteUser` declared but unreachable. Pass
when the write succeeds and the file appears on the Mac owned by you.

```bash
container run --rm -u vscode -v "$PWD":/w -w /w ee-standard-dev:local \
  bash -c 'id; stat -c "%U:%G %a" . .git; touch .s3 && rm .s3 && echo WRITE-OK
           git -c safe.directory=/w status --short | head -3'
```

If it fails, try G3-b next: the workspace in a named volume
(`container volume create`, then clone inside). Try G3-c last: run as the host
uid.

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

Then, in order: run `initializeCommand` on the host. Start the container
detached with the `runArgs`, the volume mount
(`--mount type=volume,source=…,target=…`), the workspace from S3 and a
keep-alive entrypoint. Run `postCreateCommands`, then `postStartCommands`, with
`container exec -u vscode`. Finally `container exec -it -u vscode … claude`.

Pass when `setup.sh` completes, `check-auth.sh` reports Claude and `gh` as
authenticated, `claude` starts as `vscode`, and `GIT_AUTHOR_NAME` (a value with
a space) arrives intact through `--env-file`. Record any step that needed a
flag not named here.

Result: *not yet run.*

## S4 — Memory

**Gap.** An Apple container is a VM of 1 GiB and 4 CPUs by default
(`resource-usage.md`). `06-devcontainer-setup.md` asks for 8 GB. Memory the
guest frees is not returned to macOS until the container restarts.

Run `npm ci --no-audit --no-fund` and `uv run pytest` at the default, then
with `--memory 8g`. Record peak usage from `container stats --no-stream` and
Activity Monitor, and whether host memory drops after the run. Pass is a
measurement, not a threshold. It decides whether `--memory 8g` belongs in
`runArgs`.

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

Not specific to this path. The lock file pins each feature's *installer*, not
what it installs. The resolved options show `github-cli` at `version: latest`,
and `node` at `nvmVersion: latest` and `pnpmVersion: latest`. So a Docker
rebuild can already pull newer binaries under an unchanged lock file.
