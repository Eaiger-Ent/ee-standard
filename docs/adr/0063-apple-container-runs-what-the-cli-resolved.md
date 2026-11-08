# ADR 0063: Apple `container` Runs What the `devcontainer` CLI Resolved

**Status:** Proposed
**Date:** 2026-11-08
**Revision:** 1

## Background

**The question.** Can this repository's devcontainer run on Apple's
[`container`](https://github.com/apple/container) instead of Docker, for a
terminal and Claude CLI session, with no third-party tools? VS Code stays on
Docker. [`04-build-plan.md`](../04-build-plan.md) § Phase 14 asked it, and
[`20-apple-container-spike.md`](../20-apple-container-spike.md) records the
answer. Every claim below comes from that record, which ran on 2026-11-08 on
macOS 27.2 (arm64), `container` 1.7.1 (`a15b460`) and `@devcontainers/cli`
0.90.0.

**The constraint.** `devcontainer.json` must keep one reader. A second
interpreter of the file is theme T-2. The approach under test kept the
`devcontainer` CLI as that reader. Apple `container` only builds what the CLI
generates and runs the result.

**What the spike showed.** All five spikes passed:

- **S1.** `devcontainer build --platform linux/arm64 --docker-path <stub>`
  generates a complete context without Docker. Replaying its two `build` calls
  with `container build` produces an image that runs `gh`, `node` and `claude`
  as `vscode`, and the lock file is unchanged.
- **S3.** `vscode` can write a bind-mounted checkout, and the files land on the
  Mac owned by the developer.
- **S2.** The lifecycle, run by hand from the CLI's output, reaches a `claude`
  session where `check-auth.sh` passes.
- **S4.** The workload peaks at about 1.4 GiB of the 8 GiB given.
- **S5.** `pytest` passes (2009), `register-check` exits `3`, and all three
  pre-push hooks run.

No control changed. DEV-001 and BLD-001 read files, and CI never reads
`devcontainer.json`.

**What it needed that the brief did not name.** Each item is a fact about the
tools, not a preference:

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | The CLI must be **≥ 0.90.0**. 0.88.0 cannot parse `name:tag@digest`, the form DEV-001's pin takes, and falls back to `docker inspect`. | S1, first run |
| F2 | **`--platform linux/<arch>` is required on a Mac.** With no Docker server, the CLI looks for a base image matching the host's `process.platform`, `darwin`, and the index holds only Linux images. `read-configuration` has no `--platform`, so `--include-merged-configuration` fails on a Mac. | S1, second run. S2 |
| F3 | The values the merged view would give are available from two CLI outputs instead: plain `read-configuration` (`initializeCommand`, `runArgs`, workspace) and the `devcontainer.metadata` label the CLI writes into the image (`postCreateCommand`, `postStartCommand`, `mounts`, `containerEnv`, `remoteUser`). | S2 |
| F4 | The CLI's two runtime calls translate to `container build` by dropping exactly two Docker-only tokens, `buildx` and `--load`. The builder resolves the first build's local image, so no Dockerfile rewrite is needed. | S1 |
| F5 | **The mount point reads as `root:root`**, so git refuses a checkout mounted as the mount root (`dubious ownership`). Mounting the checkout's parent at `/workspaces` fixes it with no git configuration. | S3 |
| F6 | `container exec -u vscode` sets `HOME` but **not `USER` or `LOGNAME`**. Two tests fail under `set -u` until `-e USER=vscode -e LOGNAME=vscode` is passed. | S4, S5 |
| F7 | `--env-file` parses the `.docker` form exactly as Docker does. No secret appears in the host process list, detached or during `exec -it … claude`. | S2 |
| F8 | Host memory the guest touches is **not returned until `container stop`**, and the S1 builder holds its own allocation until `container builder stop`. | S4 |
| F9 | Installing `container` needs admin once (a signed, notarised `.pkg`). Nothing after that needs `sudo`. | Pre-flight |

## Alternatives Considered

### Option 1: Reject. Docker remains the only runtime

**Pros:** Nothing new to own. Docker Desktop, or any runtime the Dev Containers
extension reaches, keeps doing what `06-devcontainer-setup.md` § 1 already
describes, and `devcontainer up` keeps driving the whole lifecycle.

**Cons:** It discards a passing result. A terminal and Claude CLI session is
the primary way this repository is worked on, and the spike showed it running on
a first-party runtime with a smaller host footprint at idle. Docker Desktop's
VM was configured with 24 GiB; the Apple container's footprint after the full
workload was 2.1 GB.

### Option 2: A host launcher that maps the CLI's output to `container` flags

A script under `.devcontainer/bin/` does what the spike did by hand. It calls
the pinned CLI with a stub `--docker-path`, replays the logged builds through
`container build`, reads F3's two outputs, and runs the lifecycle with
`container run` and `container exec`.

**Pros:** `devcontainer.json` keeps one reader. The launcher interprets the
CLI's *resolved* output, never the file, so it inherits feature merging,
lock-file resolution and variable substitution instead of reimplementing them.
Every step it takes was demonstrated.

**Cons:** It is a runtime adapter this repository owns. It must stay correct
as the CLI and `container` change, and it handles a closed set of keys, so a
key outside that set must be refused rather than ignored (see the Decision).

### Option 3: Make the stub answer every Docker call, so `devcontainer up` drives `container`

Translate `inspect`, `run`, `exec` and the rest into `container` equivalents,
so the CLI's own `up` runs unchanged.

**Pros:** The lifecycle stays the CLI's code, not ours.

**Cons:** The CLI parses Docker's JSON output, so the stub would have to
reproduce Docker's `inspect` schema from Apple's, which is a different format.
That is a Docker emulation layer, larger than Option 2 and with a far wider
surface to drift. S1 stopped at exactly this point when the stub could not
answer `inspect`.

### Option 4: A second reader of `devcontainer.json`

Parse the file directly and build `container` flags from it.

**Pros:** It needs no stub and no CLI on the host.

**Cons:** It would be a second interpreter of the file, which is theme T-2.
It would also reimplement feature resolution, lock-file pinning and metadata
merging. Rejected by the constraint, not on the merits.

### Option 5: A third-party Docker-compatible layer over `container`

**Pros:** `devcontainer up` and possibly VS Code would work unchanged.

**Cons:** It is out of scope by the question's own terms (*no third-party
tools*). It also puts an unpinned, separately maintained runtime between a
register that pins everything and the container it describes.

## Decision

**We will accept Apple `container` as a second runtime for terminal and Claude
CLI sessions in this repository, through a host launcher (Option 2).** VS Code
stays on Docker. The register does not change.

Option 2 is chosen over Option 1 because the result passed and the cost is
bounded by F1–F9. It is chosen over Option 3 because emulating Docker's JSON is
the larger and less stable adapter. Options 4 and 5 fail the constraint.

**The launcher reads only the CLI's output.** Its inputs are plain
`read-configuration` and the image's `devcontainer.metadata` label (F3). It
never opens `devcontainer.json`.

**The launcher handles a closed set of keys and refuses every other one.** A key
it does not map is an error naming the key, not a skipped setting. Silently
dropping one would run a container that differs from the one Docker runs, which
is the declared-but-unreachable shape this register exists to catch. A test
holds the refusal. The initial set is what the spike exercised:

- from `read-configuration`: `image`, `features`, `initializeCommand`,
  `runArgs`, `mounts`, `remoteUser`, `containerEnv`, `postCreateCommand`,
  `postStartCommand`, `customizations`, `name`, and the CLI-computed workspace;
- from the label: `id`, `remoteUser`, `mounts`, `containerEnv`,
  `postCreateCommand`, `postStartCommand`, `customizations`.

`customizations` is accepted and ignored, because it configures an editor the
launcher does not run.

**The launcher must:**

1. Invoke the `devcontainer` CLI through the path a lock file pins (below), at
   ≥ 0.90.0 (F1).
2. Pass `--platform linux/$(uname -m | sed s/x86_64/amd64/)` to every CLI call
   that resolves an image (F2).
3. Replay only the logged `build` and `buildx build` calls, removing exactly
   `buildx` and `--load`. Any other logged runtime call is an error (F4). The
   only calls it tolerates as probes are `buildx version`, `-v`, `version`,
   `inspect --type image` and `pull`.
4. Stop the builder after building (F8).
5. Run `initializeCommand` on the host, then start the container detached with
   the `runArgs`, each `type=volume` mount as `--mount`, the workspace's
   **parent** bound at `/workspaces`, and the keep-alive entrypoint `devcontainer
   up` uses (F5).
6. Pass `-e USER=<remoteUser> -e LOGNAME=<remoteUser>` on every `exec` (F6).
7. Never pass a secret as an argument. Secrets reach the container only through
   `--env-file` on `run` (F7).
8. Run `postCreateCommand` once and `postStartCommand` on every start, as
   `remoteUser`.

**The resource floor moves into `runArgs`:** `--cpus 8 --memory 8g`. Both
runtimes accept these flags with the same meaning. On Docker they are a ceiling
inside Docker Desktop's VM; on Apple `container` they size the VM. This replaces
the "give Docker Desktop 8 GB" sentence in `06-devcontainer-setup.md` § 1 with
a declared value.

**The CLI is pinned as a devDependency.** `@devcontainers/cli` goes in
`package.json`, exact, and is locked by `package-lock.json`. The launcher
invokes `node_modules/.bin/devcontainer`, never a bare `devcontainer`. This is
[ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md)'s rule applied to a host
tool. The global install `06-devcontainer-setup.md` § 1 documents remains for
the Docker path until a later decision moves it.

**Scope: this repository only.** The adopter template is not changed. Under
[ADR 0037](0037-the-template-is-the-whole-devcontainer-step.md) the template is
the whole devcontainer step for an adopter, and shipping a second runtime there
is a separate decision. It should follow evidence from this repository's own use,
not precede it.

### Open for the reviewer

These are recorded as choices, not settled facts. A reviewer may reverse them
without the rest falling:

- **The parent mount (F5) against a `safe.directory` entry.** Mounting the
  parent exposes every sibling of the checkout inside the container. Writing
  `safe.directory` into the container's git config exposes nothing, but it is a
  second place git trust is configured. The Decision chooses the mount, because
  it is what `devcontainer up` does on Docker (`/workspaces/<name>`) and it needs
  no configuration. The cost is real for a checkout whose siblings hold
  something sensitive.
- **Whether the CLI pin belongs in `controls.yaml` `tools:`.** Under ADR 0018 a
  tool version is register data. But this tool is a host prerequisite with no
  gate behind it, and no control reads it. The Decision keeps it in the lock
  file alone.
- **`nproc` reports 9 for `--cpus 8`** (S4). It is unexplained, and harmless
  for this workload.

## Consequences

**Positive outcomes:**

- A terminal and Claude CLI session runs without Docker Desktop, on a
  first-party, notarised runtime, with nothing needing admin after one install.
- `devcontainer.json` keeps one reader, and the launcher's input is the same
  resolved configuration Docker's path uses. A divergence between runtimes shows
  up as a refused key, not as a quietly different container.
- The resource floor becomes a declared value in `runArgs` instead of a
  sentence about Docker Desktop's settings.
- The spike showed this path keeps secrets out of the host process list (F7),
  which the VS Code path does not. *Found along the way* in the spike record
  holds that separate finding.

**Trade-offs and risks:**

- The repository owns a runtime adapter. Its correctness depends on two
  upstream tools: the CLI's stub-visible call pattern and Apple's flag surface.
  The refusal rule turns most drift into a loud error rather than a wrong
  container, but not all of it. A change in what an *accepted* key means would
  pass silently.
- `--include-merged-configuration` is unusable on a Mac (F2), so the launcher
  depends on the image label's format. That is the CLI's own output, but it is
  less documented than `read-configuration`.
- Host memory is held until the container stops (F8). A long-lived session
  costs its high-water mark, not its working set.
- The CLI moves from a global host install to a lock-file pin for this path,
  which adds `npm ci` on the host to the four host steps `CLAUDE.md` lists.
- Remaining Phase 14 criteria, if this is accepted: the launcher and its
  refusal test, the CLI pin, and `06-devcontainer-setup.md` § 1 and
  `08-adopting.md` § 2.0a naming the runtime, its host limits and how you know
  it worked.

## Related ADRs

- [ADR 0018: The Register/Checker Boundary](0018-register-checker-boundary.md) —
  the test the CLI pin's location is measured against, left open above.
- [ADR 0020: A Locus Reaches the Pinned Artefact](0020-a-locus-reaches-the-pinned-artefact.md)
  — why the launcher calls `node_modules/.bin/devcontainer`.
- [ADR 0030: uv Is Bootstrapped From a Pinned Release](0030-uv-is-bootstrapped-from-a-pinned-release.md)
  — unaffected. `setup.sh` ran unchanged inside the Apple container.
- [ADR 0037: The Template Is the Whole Devcontainer Step](0037-the-template-is-the-whole-devcontainer-step.md)
  — why the adopter template is out of scope.

## References

- [`20-apple-container-spike.md`](../20-apple-container-spike.md) — the
  record, with every command, version and digest.
- [apple/container](https://github.com/apple/container) — the runtime, 1.7.1.
- [Development Container Specification](https://containers.dev/implementors/spec/)
  — the `devcontainer.metadata` label and the merge rules the launcher inherits
  rather than reimplements.
