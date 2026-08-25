# gate-supply-chain

Deploys SUP-001 — *dependencies resolve from a committed lockfile* — SUP-002 —
*dependency updates are proposed automatically* — and SUP-003 — *third-party CI
actions are pinned to a commit SHA* — in whichever repository you point it at.

## What it writes

| Locus | Artefact | Contents |
| --- | --- | --- |
| ci | the gating workflow | A frozen install step, stamped for SUP-001, placed **above** every other gate's steps |
| ci | `.github/dependabot.yml` | One `updates:` entry per ecosystem present, stamped for SUP-002 |
| pre-commit | `.pre-commit-config.yaml` | A hook running the checker for SUP-003, stamped at the hook |
| ci | the gating workflow, or nothing | A SUP-003 step — omitted where a full audit already reaches it |
| — | every workflow | Each third-party `uses:` rewritten from a tag to the commit it points at |

Three templates live in `templates/` and carry the placeholders the skill fills
from the register: `ci-steps.yaml`, `dependabot.yaml` and `precommit-hook.yaml`.

## Why three controls and one skill

Because they are one property split three ways — what a build resolves, how it
stays current, and what it is allowed to fetch — and because two of them write
into the same gating workflow. SUP-001's install step has to sit *above* every
other gate's steps in that workflow, since those steps run the tools it places.
No separate skill could guarantee that ordering, and a lint step written before
the install lints against nothing.

The grouping is visible in the register rather than only here: all three
controls carry `deployed_by: gate-supply-chain`, each reads back its own
provenance stamp, and the plugin's `deploys.json` lists them under this gate
with a contract version of their own.

## Why SUP-003's gate is the checker

No third-party action linter shares this register's notion of an owner-exempt
action — `actions-pinned-to-sha` reads the repository's own owner from the
remote and exempts actions published by it. A second implementation would
eventually disagree with the first, and the disagreement would surface as a
commit blocked at one locus and waved through at another.

So the pre-commit hook runs `register-check run --control SUP-003`: the same
pinned binary, the same assert, one implementation. It is reached through the
register's `tools.register-check.invocation` rather than by name, because a bare
name resolves from `PATH` and for this tool what answered would be auditing the
repository ([ADR 0020](../../../../docs/adr/0020-a-locus-reaches-the-pinned-artefact.md)).

Running the checker is not the same as auditing with it. `register-check
schema`, `meta`, `assert` and `explain` reach no control, and the verify step
does not credit them — a distinction that exists because this repository's own
pre-commit config ran `register-check schema` and would otherwise have been
credited with a SUP-003 gate that could never have failed it.

## Why it takes no opinions

Which lockfiles count for an ecosystem, what installing from one looks like,
which `package-ecosystem:` spellings a bot accepts, and how a locus reaches the
checker all come from `controls.yaml`. Nothing in this skill is a version, a
command or a tool name.

`ecosystems.<name>.frozen_install_command` is what the gate writes;
`ecosystems.<name>.frozen_install` is what the checker credits. The schema holds
them together — every command must match one of its own ecosystem's patterns —
so this gate cannot write an install step its own verify step would refuse.

## What it cannot do

**Install the bot.** A `dependabot.yml` is inert until Dependabot is enabled on
the repository, and a `renovate.json` is inert until the Renovate app is
installed and its onboarding pull request is left open rather than closed. Both
are platform acts a human with admin takes
([`08-adopting.md`](../../../../docs/08-adopting.md) § 1.1). The skill says
which one the repository now needs.

**Write a lockfile.** A repository in an ecosystem with no tracked lockfile
fails SUP-001, and the gate stops rather than generating one: a lockfile this
skill produces pins a resolution nobody reviewed.

**Guess a SHA.** A tag that the API cannot resolve — moved, deleted, private —
stops that reference and is listed. A wrong SHA is worse than an unpinned tag,
because it pins the repository to code nobody chose.
