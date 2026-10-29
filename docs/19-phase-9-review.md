# Phase 9 — YAML is linted before anything reads it

The evidence for each tick in [`04-build-plan.md`](04-build-plan.md) § Phase 9.
The decision is [ADR 0059](adr/0059-yaml-is-linted-before-anything-reads-it.md).

## Every gate template is valid YAML

**Closed 2026-10-28**, by ADR 0059 revision 2.

**The defect.** Ten of the gate skills' YAML templates did not parse. Each
failing line was a value beginning with a placeholder, such as
`run: {{TOOL_INVOCATION}} run --control BLD-001`. YAML reads a leading `{` as
the start of a flow mapping. The YAML around the placeholders was sound.

**The fix.** The 33 placeholder names used by the gate skills are spelled
`<<NAME>>`, in every template, every `SKILL.md` substitution table,
`gate-quality/editor-binding-rules.md` and the tests that render them. `<` is
legal at the start of a YAML value. The devcontainer and adoption templates
under `plugins/control-register/templates/` keep `{{NAME}}`. They are a
separate mechanism an adopter's `sed` fills, and they are not YAML.

**Why not `__NAME__`.** It was tried first. The proof below rejected it:
`gate-secrets` has `{{TOOL}}_${TOOL_VERSION}`, which became
`__TOOL___${TOOL_VERSION}`. Nothing can tell whether that is `TOOL` followed by
`_` or a placeholder named `TOOL_`, and that includes the model running the
gate. `<<` and `>>` cannot occur inside a name, so `<<NAME>>` has no such case.

**How it was shown to hold.**

| Claim | Evidence |
| --- | --- |
| Nothing changed but the marker | Undoing the respelling on each of the 54 files under `skills/` reproduces the file at `main` byte for byte |
| A gate writes exactly what it wrote before | All 16 templates, rendered with one distinct value per placeholder, give identical bytes from either spelling. No `contractVersion` moves |
| The templates parse | `yamllint` 1.37.1 with ADR 0059's floor over `skills/*/templates/*.yaml`: 10 errors at `main`, 0 after |
| They keep parsing | `test_a_yaml_template_is_yaml_before_it_is_rendered`, one case per YAML template. Fails when one line's indentation is broken |
| The old spelling cannot return | `test_the_gate_skills_spell_a_placeholder_one_way`. Fails when `{{TOOL_INVOCATION}}` is put back in one template |
| An unfilled placeholder is still caught | The seven render tests share `UNFILLED` in `tests/conftest.py`. With `<<TOOL>>` left unfilled in `gate-iac`'s render, it fails |

**The guard that would have gone vacuous.** The seven render tests checked
`"{{" not in text`. After the respelling that check can never fail. Measured:
with `<<TOOL>>` left unfilled and the old check in place, all 12 `gate-iac`
tests pass. A deployment with a placeholder left in would have passed every test
written to catch one. That is why the pattern is defined once, in `conftest.py`,
next to a comment saying so.

**Owed upstream.** `docs/promotion/published.json` declares the edited files
`owed-upstream`. One incubator amendment has to carry the templates and the
`SKILL.md` prose together, because a gate whose `SKILL.md` and templates
disagree about the marker deploys with placeholders left in.

## YML-001 is in the register, and passes here

**Closed 2026-10-29**, items 1 and 4, at register contract 37.

**What landed.** YML-001 in `controls.yaml`, with ADR 0059's fields. Its floor
and globs are in the file block's `args`. `tools.yamllint` uses the lockfile
form, because this repository has `uv.lock`. `yamllint` 1.38.0 is a dev
dependency, and `yaml_gate_wired_at_all_loci` is in the closed set. This
repository is wired at all three loci by hand: `.yamllint.yml`,
`.claude/hooks/yaml-lint.py` and its `PostToolUse` entry, a `repo: local`
pre-commit hook, and a step in the Conformance job. None of it is stamped,
because `lint-yaml` has not run here (item 3, below).

**How it was shown to hold.**

| Claim | Evidence |
| --- | --- |
| The floor costs nothing here | `uv run yamllint .` over all 38 tracked YAML files: 0 findings |
| Coverage is what git tracks | `yamllint --list-files .` matches `git ls-files '*.yml' '*.yaml'` exactly, plus `.yamllint.yml` itself. `ignore-from-file: .gitignore` hides nothing tracked |
| It fails on ADR 0059's case | A second `verify:` added to DOC-001 in `controls.yaml`: `run --control YML-001` exits `1`, `duplication of key "verify" in mapping` |
| Each part of the assert is load-bearing | Nine more mutations in this repository, each a `FAIL` naming its cause: `truthy` at warning, `key-duplicates` removed, `allowed-values` widened, `extends: default` with no floor, an `ignore:` over `.github/`, `yaml-files` narrowed, and each of the three loci unwired |
| The tests are load-bearing | Eleven tests in `test_asserts_command.py`, reading the floor from the register. Four mutations of the assert, each caught: the level check removed, the editor locus check removed, list widening allowed, a preset's level assumed `error` |

**Why the floor must be stated.** A rule a configuration inherits through
`extends` keeps the preset's level, and yamllint's `default` preset sets
`truthy` to warning. Warnings exit `0`. So the assert rejects a floor rule
reached only through a preset, which is the shape `lint-yaml` writes.

## What `lint-yaml` 0.1.15 would deploy

Measured 2026-10-29, while item 3 was being prepared. `lint-yaml` 0.1.15 is
published in `ee-skills`. ADR 0059 says it is "in neither `ee-skills` nor this
repository's marketplace", and that is no longer true. Its hook carries
incubator#1143's annotation and passes `uv run mypy` here unedited, so item 3's
TYP-001 half holds.

The rest does not meet YML-001. A run here would write:

| Locus | What it writes | Why YML-001 fails it |
| --- | --- | --- |
| Config | `.yamllint.yml` with `extends: default`, overwriting this one | `key-duplicates` is not stated, and `truthy` has no `level`, so the preset's warning applies |
| Editor | `.claude/hooks/yaml-lint.py` | Fails `uv run ruff check` seven times (E401, I001, PTH110, PTH119), and its `python3` shebang fails `test_toolchain_pin.py`. With a configured invocation it labels its output `uv`, not `yamllint` |
| Pre-commit | `adrienverge/yamllint` pinned by `rev:` | The form ADR 0059 rejects: the version is in `.pre-commit-config.yaml`, not the register |
| CI | `pip install yamllint` in `lint.yml` | Pins nothing (ADR 0020). This one is already the ADR's first upstream ask |

So item 3 is blocked on `lint-yaml` itself. Its config, its pre-commit hook
and its hook script's lint conformance would be three asks beyond the ADR's
two. The hand-wired hook here is that script with exactly those three edits,
and its header names each one.
