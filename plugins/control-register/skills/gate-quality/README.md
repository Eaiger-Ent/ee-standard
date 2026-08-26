# gate-quality

Deploys LNT-001 — *lint and format violations block the merge* — TYP-001 —
*static type checking runs in strict mode and blocks* — and TST-001 — *a failing
test fails the build* — in whichever repository you point it at.

## What it writes

| Locus | Artefact | Contents |
| --- | --- | --- |
| editor | `.devcontainer/devcontainer.json`, or `.vscode/extensions.json` | The linter's editor extension, stamped for LNT-001 |
| pre-commit | `.pre-commit-config.yaml` | A linter hook and a type-checker hook per stack, stamped at each hook |
| ci | the gating workflow | Lint, type check and test steps, one stamp each |

Three templates live in `templates/` and carry the placeholders the skill fills
from the register: `editor-extensions.json`, `precommit-hooks.yaml` and
`ci-steps.yaml`.

## Why three controls and one skill

Because they share two files. LNT-001, TYP-001 and TST-001 all reach the same
`.pre-commit-config.yaml` and the same gating workflow, and three skills writing
those in turn would each rewrite what the last one wrote. Gates are grouped by
the artefact they write, not one per control — the general rule, of which this
is the first instance.

The grouping is visible in the register rather than only here: all three
controls carry `deployed_by: gate-quality`, each reads back its own provenance
stamp, and the plugin's `deploys.json` lists them under this gate with a
contract version of their own.

*Each* is the operative word. The stamp read-back matches on the control, not
on this skill's name, so recording the CI steps and forgetting the editor locus
fails LNT-001 rather than passing on TST-001's stamp.

## Why it takes no opinions

Which linter, which type checker, where each keeps its configuration, which key
turns strictness on, which editor extension serves it, how every locus invokes
it and which test-command spellings are acceptable all come from `controls.yaml`
and nowhere else. A skill that carried its own copy of any of them would be a
second source of truth, free to drift from the register the checker audits
against — which is the failure the standard exists to prevent, reproduced inside
the tool meant to prevent it.

The consequence is worth stating plainly: **this skill cannot deploy without a
register.** That is deliberate. There is no default to fall back on, because a
default is a decision nobody recorded.

## The two values it does not simply copy

**The hooks' file filter** is derived from the register's `source_globs` rather
than picked from pre-commit's `types:` vocabulary. `source_globs` is the set of
tracked files a stack's gates are claimed to cover; a hand-picked tag would be a
second statement of that set, free to name fewer files than the control claims.

**The test command** is the one thing the register does not settle. It records
the spellings it accepts for each ecosystem, and the repository picks one — so
the skill asks, offering exactly that set, rather than choosing. If a gating
step already runs one of them, that is the answer and nothing is asked.

## Why it verifies through `register-check`

The last step runs
`register-check run --control LNT-001 --control TYP-001 --control TST-001`,
which evaluates each control's own verify blocks through the same code the
auditor uses. The gate does not read its own files back to decide whether it
worked. A gate that verified itself some other way would eventually disagree
with the auditor, and the disagreement would surface at the worst possible time.

Expect exit `0` here, unlike `gate-secrets`. All three controls verify from
files and none declares a `remote` locus, so there is nothing Phase 3 is holding
back. A `3` means something declared itself partial, and is named rather than
rounded up.

## Invocation

Invoked by `register-adopt`, which dispatches it through the Skill tool — do
not add `disable-model-invocation: true` here. A dispatched skill carrying that
flag cannot be reached at all, which is preflight P9 and is what stopped the
front door at Step 0 in Phase 4. The reasoning, and what guards the platform
mutations instead, is
[ADR 0035](../../../../docs/adr/0035-a-dispatched-skill-is-reachable.md).
