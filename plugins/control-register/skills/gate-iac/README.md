# gate-iac

Deploys IAC-001 — *infrastructure code is statically analysed before apply* —
in whichever repository you point it at.

## What it writes

| Locus | Artefact | Contents |
| --- | --- | --- |
| pre-commit | `.pre-commit-config.yaml` | One hook running the checker for IAC-001, stamped at the hook |
| ci | the gating workflow, or nothing | Omitted where a full audit already reaches the control |

Two templates live in `templates/` and carry the placeholders the skill fills:
`precommit-hook.yaml` and `ci-steps.yaml`.

## Why one hook runs two analysers

IAC-001's verify blocks are `checkov --directory . --compact --quiet` and
`tflint --recursive`. The hook runs the **control**, and the control runs both:
`register-check run --control IAC-001` executes them through the same path the
audit uses.

That is not a shortcut. Two hooks each invoking one analyser would be two
statements of what "analysed" means, free to drift from each other and from the
register — a `--recursive` dropped at one locus and kept at another, discovered
by a finding that CI caught and pre-commit did not. One hook, one control, one
definition.

It also means the arguments stay the register's. `--compact --quiet` and
`--recursive` are in `controls.yaml` and this skill never rewrites them: a
control whose arguments a skill chooses is a control nobody can review.

## The verdict this gate is most likely to produce

**`UNCLASSIFIED`, not `PASS`.** IAC-001 names two analysers and this standard's
register pins neither, because this repository has no `*.tf` to analyse. An
absent analyser is *cannot verify*
(ADR 0016),
which is the honest verdict — and the skill will not make it green by installing
an unpinned tool. That would leave the version unrecorded, which is exactly the
condition `tool_versions_match_register` exists to fail.

What closes it is a `tools.checkov` and `tools.tflint` entry in **your**
register, naming the loci you install them at — your register records your own
files (`08-adopting.md` § 3.5).

## Exit `1` has two causes and they are not the same

- A failing wiring or stamp block is a **failed deployment**.
- A failing `checkov` or `tflint` block is a **successful deployment** finding
  real problems in your Terraform — the gate working on its first run.

The skill reports which, quotes the block, and does not describe the second as a
deployment failure. Conflating them is how a working gate gets rolled back.

## What it leaves alone

**`terraform validate`.** It checks syntax and provider schema, which neither
analyser does. Not a predecessor — a different check.

**A second analyser**, such as `tfsec` or `terrascan`. Having one is not a
violation, but two analysers means two suppression files, and only one of them
is a place this standard checks
(ADR 0019).
The skill shows what each is configured to do and asks.

**A repository with no `*.tf`.** The predicate is evaluated against files and
never self-declared. IAC-001 skips, and a hook for infrastructure that does not
exist can only ever be noise.

## Invocation

Invoked by `register-adopt`, which dispatches it through the Skill tool — do
not add `disable-model-invocation: true` here. A dispatched skill carrying that
flag cannot be reached at all, which is preflight P9 and is what stopped the
front door at Step 0 in Phase 4. The reasoning, and what guards the platform
mutations instead, is
ADR 0035.
