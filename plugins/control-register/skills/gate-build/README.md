# gate-build

Deploys BLD-001 — *every container image stage ends as a non-root user* — and
DEV-001 — *devcontainer features are version-pinned* — in whichever repository
you point it at.

## What it writes

| Locus | Artefact | Contents |
| --- | --- | --- |
| — | `.devcontainer/devcontainer.json` | `remoteUser`, stamped for BLD-001; a digest-pinned `image`, stamped for DEV-001 |
| — | `.devcontainer/devcontainer-lock.json` | Every feature resolved to a digest |
| — | `.devcontainer/setup.sh` | Created when absent, and otherwise left alone |
| pre-commit | `.pre-commit-config.yaml` | One hook running the checker for both controls, stamped twice |
| ci | the gating workflow, or nothing | Omitted where a full audit already reaches both |

Three templates live in `templates/` and carry the placeholders the skill
fills: `devcontainer.json`, `precommit-hook.yaml` and `ci-steps.yaml`.

## Why two controls and one skill

Because they read the same file. BLD-001 wants a user and DEV-001 wants two
pins, and both are keys in `devcontainer.json`. Two skills editing one file in
turn would each rewrite what the last one wrote.

One hook covers both loci and carries **two** stamps. The read-back matches on
the control being evaluated, so a hook stamped for BLD-001 alone leaves DEV-001's
pre-commit locus unrecorded even though the same command enforces it.

## It pins what it finds; it does not choose

`project-init` decides *which* image and which features a repository uses.
DEV-001 insists that whichever were chosen are pinned, and BLD-001 that the
container does not end as root. Those are different questions and neither skill
should be asked the other's
([`03-devcontainer.md`](../../../../docs/03-devcontainer.md) § How this composes
with `project-init`). Inventing an image or a user here produces a container
that does not start, which is a worse failure than the one being fixed.

The same line divides this gate from the shipped **template**, which lives at
`plugins/control-register/templates/devcontainer/`. The template produces the initial
`.devcontainer/`; this gate pins it afterwards.

## The two half-states it exists to catch

**A lock file covering some features.** Phase 0.5's own exit criterion was
re-opened over exactly this: a lock file pinning three of four features reads as
solved and is not.

**A complete lock file over a floating image tag.** The more dangerous of the
two, for the same reason — it reads as solved and is not. Both halves or
neither.

**An absent container user.** A devcontainer naming neither `containerUser` nor
`remoteUser` runs as whatever its base image uses, which may be root today and
may become root on any digest bump. Non-root by luck is not the property BLD-001
states, and this was a JSON key nothing verified until register contract 7.

## `.devcontainer/setup.sh` is its file, not its content

This gate creates `setup.sh` when the devcontainer has none. It does not own
what other gates install there: `gate-secrets` writes and stamps the scanner's
install block, exactly as both gates write their own hooks into one
`.pre-commit-config.yaml`. Shared file, per-region stamps.

This gate writes **no** stamp of its own into `setup.sh`. Neither control has a
locus there, and a stamp naming a control whose locus the file is not is a claim
rather than a record.

## What it cannot verify

**A Dockerfile linter it does not pin.** BLD-001's container half runs
`hadolint`, and an absent linter is `UNCLASSIFIED — cannot verify`, not a pass
([ADR 0016](../../../../docs/adr/0016-exit-codes-for-unverifiable-controls.md)).
What closes it is a `tools.hadolint` entry in **that repository's** register,
naming the loci it installs the linter at — your register records your own files
([`08-adopting.md`](../../../../docs/08-adopting.md) § 3.4). This gate does not
install a tool the register does not pin, and this standard's own register pins
none, because this repository has no Dockerfile to lint.
