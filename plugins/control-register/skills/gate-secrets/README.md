# gate-secrets

Deploys SEC-001 — *a commit containing a secret cannot reach the remote* — and
checks SEC-002 and SEC-003, in whichever repository you point it at.

## What it does

It installs the secret scanner at the version and checksum the register pins.
It wires the scanner as a pre-commit hook and a CI step, and verifies all three
controls through `register-check`. It is run as `/gate-secrets`, or dispatched
by `/register-adopt`. It reports the local loci it deployed and verified, and
which remote blocks could not answer and why.

## What it writes

| Locus | Artefact | Contents |
| --- | --- | --- |
| pre-commit | `.pre-commit-config.yaml` | The scanner as a `local` hook, stamped at the hook |
| ci | the gating workflow | A pinned install and a scan step, stamped |
| remote | — | Nothing. Push protection is a platform act only an admin can take |

Both templates live in `templates/` and carry the placeholders the skill fills
from the register: `precommit-hook.yaml` and `ci-steps.yaml`.

## Approach

### Why it takes no opinions

The scanner's name, version and checksum come from `controls.yaml` and nowhere
else. A skill that carried its own copy of a pinned version would be a second
source of truth for it, free to drift from the register the checker audits
against — which is the failure the standard exists to prevent, reproduced inside
the tool meant to prevent it.

The consequence is worth stating plainly: **this skill cannot deploy without a
register.** That is deliberate. There is no default to fall back on, because a
default is a decision nobody recorded.

### Why it verifies through `register-check`

The last step runs
`register-check run --control SEC-001 --control SEC-002 --control SEC-003`,
which evaluates the control's own verify blocks through the same code the
auditor uses. The gate does not read its own files back to decide whether it
worked. A gate that verified itself some other way would eventually disagree
with the auditor, and the disagreement would surface at the worst possible time.

Expect exit `3` today, not `0`. SEC-001's remote block reports
`SKIPPED (no credentials)` until `kind: remote` verification lands in Phase 3.
The local loci are verified; the remote locus is not, and the report says so
rather than rounding up.

### When the plan refuses push protection

Push protection is a platform act an admin takes, and on a private repository
below GitHub's paid tier it cannot be taken at all. That refusal arrives as the
same `403` a missing permission does. `reference/plan-limits.md` says how to
tell them apart. When it is the plan, the gate reports the local loci as
deployed and the remote locus as unavailable on the plan. It never offers making
the repository public as its own choice.

## Invocation

Invoked by `register-adopt`, which dispatches it through the Skill tool — do
not add `disable-model-invocation: true` here. A dispatched skill carrying that
flag cannot be reached at all, which is preflight P9 and is what stopped the
front door at Step 0 in Phase 4. The reasoning, and what guards the platform
mutations instead, is
ADR 0035.

## References

- [GitHub — Push protection for repositories](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection) — what SEC-001's remote locus is, and who can enable it
- `reference/plan-limits.md` — telling a plan refusal from a scope refusal
- ADRs 0035, 0036 and 0047, and `docs/08-adopting.md`, in the `ee-standard` repository
