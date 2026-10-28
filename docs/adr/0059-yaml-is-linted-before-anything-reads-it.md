# ADR 0059: YAML Is Linted Before Anything Reads It

**Status:** Accepted
**Date:** 2026-10-28
**Revision:** 2

Rationale for control **YML-001** in `controls.yaml`.

## Background

**The problem.** YAML is where a repository keeps its gates. The CI workflows,
the pre-commit config, the update bot's config and, here, the register itself
are all YAML. The parsers that read them forgive mistakes. A malformed file is
often not rejected. It is read as something else, and the gate it describes
quietly does less. Nothing in the register checks the YAML itself.

**A duplicate key is the clearest case.** The YAML 1.2.2 specification says
each key in a mapping is unique. PyYAML does not enforce that: it keeps the last
value and drops the earlier ones without a word. `register-check` loads
`controls.yaml` with `yaml.safe_load` (`register.py`, `load_register`).

Measured 2026-10-28: a second `verify:` key was added to the end of DOC-001,
holding one `command` block that runs `true`. Then:

| Check | Result |
| --- | --- |
| `register-check --register <copy> schema` | `schema: OK`, exit `0` |
| `register-check --register <copy> explain DOC-001` | one verify block, `command: true` |
| `yamllint` with only `key-duplicates` enabled | `duplication of key "verify" in mapping`, exit `1` |

So one pasted line removed both of DOC-001's real checks. Every control check
and the schema check still passed. The same thing can happen to a workflow
step's `run:`, a pre-commit hook's `entry:`, or a Dependabot `ignore:`. Each tool
reads its own file with its own parser, and the register has no say over those.

**The YAML 1.1 booleans are the second case.** `yaml.safe_load('on: push')`
returns `{True: 'push'}`, and `country: NO` reads as `False`. The checker
already works around the first one (`asserts_command.py`, line 70). That
workaround is in one place, for one key.

**A file that does not parse is the third.** GitHub does not run a workflow file
it cannot parse. If that workflow's check is required, the merge waits forever.
If it is not required, the gate is simply gone, and the build goes green.

**A deployment mechanism already exists.** The `lint-yaml` skill in
`EqualExperts/ee-skills-incubator` installs `yamllint` and wires it at the
editor, pre-commit and CI loci. That is the same shape `lint-md` has for DOC-001
([ADR 0013](0013-one-markdown-rule-set.md)). Repositories are already deploying
it. That is how the TYP-001 failure over its vendored hook was found
(`08-adopting.md` § 3.2, point 2, fixed upstream in incubator#1143). Today the
register does not ask for it, so nothing verifies a deployment of it, and a
repository without it is still conformant.

**What it would cost here.** This repository tracks 38 YAML files, measured with
`yamllint` 1.37.1:

| Rule set | Findings |
| --- | --- |
| `lint-yaml`'s shipped config (`extends: default`, 120 columns) | 528: 325 indentation, 104 braces, 39 line length, 38 document start, 10 syntax, 12 other |
| Correctness only: syntax, `key-duplicates`, `truthy` | 10, all syntax, all gate templates |

The ten are `plugins/control-register/skills/*/templates/*.yaml`. Each fails
on a line whose value starts with a `{{TOOL_INVOCATION}}`-style placeholder: a
YAML value that begins with `{` opens a flow mapping. The YAML around the
placeholders is sound. Everything else in this repository already passes the
correctness rules.

## Alternatives Considered

### Option 1: No control; each tool's parser is the check — Rejected

This is the status quo. It is rejected because of the measurement above. The
parser *is* the failure. It accepts the duplicate key and the stray boolean. It
does not reject them.

### Option 2: Make `register-check`'s loader strict — Rejected as the answer

A loader that refuses duplicate keys would protect `controls.yaml`, and it may
be worth doing on its own merits. It is not the answer to this problem. It
covers one file of the 38. The workflows, the pre-commit config and the bot
config are read by GitHub, `pre-commit` and Dependabot, not by the checker. A
rule about every repository's YAML belongs in the register, not only in the
checker's loader ([ADR 0018](0018-register-checker-boundary.md)).

### Option 3: A parse-only hook (`check-yaml` from `pre-commit-hooks`) — Rejected

This is cheap and it catches syntax errors. It is rejected because it has one
locus. It has no shared configuration a repository can tighten, and no editor
locus. Our other lint controls, LNT-001 and DOC-001, are each one pinned
definition read at every locus ([ADR 0009](0009-single-lint-definition.md)).
A YAML control that worked differently would be the exception, and it would
need its own reason.

### Option 4: `yamllint` with `lint-yaml`'s full rule set as the floor — Rejected

This is what `lint-yaml` deploys today. It is rejected *as the floor*. Most of
its 528 findings here are indentation and brace style. Style is a fine choice
for a repository to make. It is not a birth condition every Equal Experts
repository must meet. Under `narrowing-only` variance, `lint-yaml`'s config is
still allowed: it is a narrowing of the floor below.

### Option 5: `yamllint` with a correctness floor, deployed by `lint-yaml` — Chosen

The register requires a small set of correctness rules. A repository may add
any rule on top. `lint-yaml` deploys it, and the register verifies the result,
as with DOC-001.

## Decision

**We choose Option 5: a new Tier 1 control, YML-001, requires `yamllint` over
every tracked YAML file at the editor, pre-commit and CI loci, with a
correctness floor of rules at `level: error`. It is deployed by `lint-yaml` and
verified by `register-check`.**

| Field | Value | Why |
| --- | --- | --- |
| `id` | `YML-001` | Its own prefix. YAML is configuration, not documentation, so not `DOC-` |
| `tier` | `1` | A birth condition. A new repository meets it for free, and this one has zero findings outside the templates |
| `rung` | `blocking` | A silently dropped key is a gate that does less. That is a defect, not advice |
| `locus` | `[editor, pre-commit, ci]` | The loci DOC-001 declares, and the loci `lint-yaml` already wires |
| `applies_to` | `[always]` | Every repository with CI has YAML |
| `deployed_by` | `lint-yaml` | The mechanism that already exists ([ADR 0013](0013-one-markdown-rule-set.md)'s reasoning) |
| `variance` | `narrowing-only` | Add rules or tighten them. Never disable the floor or lower it to a warning |
| `baseline` | `null` | Tier 1 |

**The floor.** It is held in the verify block's `args`, as a register fact
([ADR 0018](0018-register-checker-boundary.md)):

- **Syntax.** `yamllint` reports it whatever the config says.
- **`key-duplicates`.** This is the case measured above.
- **`truthy`**, with `allowed-values: ['true', 'false']` and
  `check-keys: false`. The second setting keeps a workflow's `on:` key legal.

All three must be at `level: error`. `yamllint` exits `0` over warnings unless
`--strict` is passed. A floor rule left at warning would be a check that cannot
fail.

**Coverage.** The control covers every tracked `*.yml` and `*.yaml` file. An
`ignore:` that hides a tracked file is not allowed
([ADR 0019](0019-exemptions-cannot-hide-tracked-files.md)). The globs live in
`args`, so a repository whose YAML has another extension changes the register,
not the checker.

**Pinning.** `yamllint`'s version is a `tools:` entry in the repository's own
register, and every locus reaches that pin
([ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md)). There are two forms:

| Repository | `tools.yamllint` | Invocation at every locus |
| --- | --- | --- |
| Has a Python lockfile | `source: lockfile`, as `register-check` is pinned | `uv run yamllint` |
| Has no Python lockfile | `source: literal`, a `version`, and `pinned_at` naming the loci that repeat it | `uvx --from yamllint==<version> yamllint` |

The second form is the one `uv` already uses here: a PyPI tool with no lockfile
to own it, its version written once in the register and repeated at each locus,
and `tool_versions_match_register` failing the build if one drifts. Measured
2026-10-28 from an empty directory, with no `yamllint` on `PATH`,
`uvx --from yamllint==1.37.1 yamllint --version` printed `yamllint 1.37.1`. An
absent `yamllint` is UNCLASSIFIED ([ADR 0016](0016-exit-codes-for-unverifiable-controls.md)),
never a pass. This is how IAC-001 already treats an analyser the repository has
not pinned.

`yamllint`'s pre-commit hook repository, pinned by `rev:`, was the other
candidate. It is rejected because it reaches the editor locus only by running
`pre-commit` from the hook, and it puts the version in `.pre-commit-config.yaml`
rather than in the register.

**What the checker gains.** One `kind: command` block that runs the pinned
`yamllint` over the covered files. One `kind: file` assert, a sibling of
`markdown_gate_wired_at_all_loci`, that reads the config and the three loci and
checks the floor is present and at error. The new assert name joins the closed
set, and `meta.register_contract` is bumped.

## Consequences

**Amended 2026-10-28 (revision 2): the gate templates are made valid YAML,
not renamed.** Revision 1 said the ten failing templates would take a non-YAML
suffix such as `.yaml.tmpl`. That treated the failure as a property of
templates. It is a property of one spelling. Every failing line is a value that
starts with a `{{...}}` placeholder, and a placeholder spelled with characters
legal at the start of a YAML value, such as `__TOOL_INVOCATION__`, parses.
Measured 2026-10-28: all twelve templates, respelled that way, give zero
findings under the floor.

So the placeholder spelling changes, everywhere it is used in
`plugins/control-register/`, and the files keep their names. This is better on
three counts:

- **YML-001 covers the templates.** A template that is broken YAML fails here,
  before it ships, rather than in an adopter's CI. Renaming would have taken
  that check away.
- **What a gate writes does not change.** A gate replaces a marker with the
  same value it replaced before. The rendered output is byte-identical.
- **No escaping is introduced.** Quoting each templated value was the other way
  to make the templates parse. It is rejected: substituted values are raw text
  and some carry quotes of their own, such as DOC-001's `"**/*.md"`, so every
  substitution would need escaping, and the rendered output would change.

The spelling changes in one pass across every template and substitution table,
including templates that are not YAML, so that one marker means a placeholder
everywhere. Excluding the templates from YML-001 remains the exemption ADR 0019
forbids.

**This repository deploys `lint-yaml`, and receives its hook.** The hook lands
as `.claude/hooks/yaml-lint.py`, inside `[tool.mypy] files`. It must be a
release that includes incubator#1143, or TYP-001 fails here as it did in the
adopter's repository. The hook is a deployed artefact like `md-lint.py`, not a
vendored skill. ADR 0044's rule that nothing is copied still holds.

**Adopters on the public route deploy it by hand.** `lint-yaml` is in the
incubator only. It is in neither `ee-skills` nor this repository's marketplace.
[ADR 0044](0044-the-adopter-installs-from-the-public-marketplace.md) part 2
already covers this: the by-hand route is supported, and the register verifies
it. `08-adopting.md` gains that route for YML-001, as § 3 has for DOC-001.

**Two things are asked of `lint-yaml` upstream.** Neither blocks this decision.

- Outside a uv project it runs `pip install yamllint`, which pins nothing. That
  fails ADR 0020 at every locus.
- Its shipped config should state the floor's three rules at `level: error`.
  Then a deployment is shown to meet YML-001, rather than meeting it only
  because `extends: default` happens to.

**The literal form pins `yamllint` and not its dependencies.** `uvx` resolves
PyYAML and pathspec fresh on each cold cache, where a lockfile would fix them.
That is the accepted cost of not making every repository carry a Python
lockfile for one linter. A repository that wants the stronger pin uses the
lockfile form.

**Existing adopters may fail a new Tier 1 control.** This is the cost of a new
birth condition. The floor is chosen to keep that cost close to zero: a
repository that fails it has a duplicate key, a stray boolean or a file that
does not parse, and each of those is a real defect.

## Related ADRs

- [ADR 0013](0013-one-markdown-rule-set.md): the same shape for Markdown, which
  this follows
- [ADR 0009](0009-single-lint-definition.md): one pinned definition at every
  locus
- [ADR 0018](0018-register-checker-boundary.md): why the floor and the globs
  are register data
- [ADR 0019](0019-exemptions-cannot-hide-tracked-files.md): why the templates
  are made valid YAML rather than ignored
- [ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md): how each locus
  reaches the pin
- [ADR 0016](0016-exit-codes-for-unverifiable-controls.md): why an absent
  `yamllint` is UNCLASSIFIED rather than a pass
- [ADR 0044](0044-the-adopter-installs-from-the-public-marketplace.md): the
  by-hand route for a deploying skill an adopter cannot install

## References

- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/): "each of the keys
  is unique"
- [yamllint rules](https://yamllint.readthedocs.io/en/stable/rules.html):
  `key-duplicates`, `truthy`, and the `level` setting
- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- `EqualExperts/ee-skills-incubator` `skills/lint-yaml/SKILL.md`, and
  incubator#1142 / #1143: the hook's `in_repo` annotation
- [`08-adopting.md`](../08-adopting.md) § 3.2, point 2: the vendored-hook case
  that raised this

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-10-28 | Original decision: YML-001, `yamllint` with a correctness floor at three loci, deployed by `lint-yaml`. | Nathan Carney |
| 2 | 2026-10-28 | § Consequences: the gate templates become valid YAML by respelling their placeholders, rather than being renamed to a non-YAML suffix. | Nathan Carney |
