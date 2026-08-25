# gate-secrets

Deploys SEC-001 — *a commit containing a secret cannot reach the remote* — and
checks SEC-002 and SEC-003, in whichever repository you point it at.

## What it writes

| Locus | Artefact | Contents |
| --- | --- | --- |
| pre-commit | `.pre-commit-config.yaml` | The scanner as a `local` hook, stamped at the hook |
| ci | the gating workflow | A pinned install and a scan step, stamped |
| remote | — | Nothing. Push protection is a platform act only an admin can take |

Both templates live in `templates/` and carry the placeholders the skill fills
from the register: `precommit-hook.yaml` and `ci-steps.yaml`.

## Why it takes no opinions

The scanner's name, version and checksum come from `controls.yaml` and nowhere
else. A skill that carried its own copy of a pinned version would be a second
source of truth for it, free to drift from the register the checker audits
against — which is the failure the standard exists to prevent, reproduced inside
the tool meant to prevent it.

The consequence is worth stating plainly: **this skill cannot deploy without a
register.** That is deliberate. There is no default to fall back on, because a
default is a decision nobody recorded.

## Why it verifies through `register-check`

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

## Invocation

Invoked by `register-adopt`, which dispatches it through the Skill tool — do
not add `disable-model-invocation: true` here. A dispatched skill carrying that
flag cannot be reached at all, which is preflight P9 and is what stopped the
front door at Step 0 in Phase 4. The reasoning, and what guards the platform
mutations instead, is
[ADR 0035](../../../../docs/adr/0035-a-dispatched-skill-is-reachable.md).
