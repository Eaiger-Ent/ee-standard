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

## A template's payload starts at column 0

**Closed 2026-10-30.**

**The defect.** Under yamllint's `default` preset the gate templates had 22
findings, all `indentation` and `comments-indentation`. That preset is what
`lint-yaml` writes and what this repository is moving to. Each payload was
indented six columns, the depth of the `hooks:` or `steps:` list it joins, so a
template read on its own was indented for no reason it could show.

**The fix.** Each YAML template's payload is at column 0, below one marker line
that names the file and the list it joins:
``# --- .pre-commit-config.yaml: items of the `repo: local` entry's `hooks:` ---``
or ``# --- the gating workflow: items of the gating job's `steps:` ---``.
`dependabot.yaml` already had one. The rule for writing it is in
`plugins/control-register/reference/template-layout.md`, and each of the six
skills that writes a YAML template points there (ADR 0036): read the column of
the list's existing items from the file, indent each non-blank line by it, and
use six spaces in a file being created. The header comments were already never
written, and the marker is not written either.

**How it was shown to hold.**

| Claim | Evidence |
| --- | --- |
| A gate writes exactly what it wrote before | For all 12 YAML templates, the payload indented as the reference says equals the body at `main`, byte for byte. So no `contractVersion` moves (ADR 0038, consequence 1) |
| The templates pass `default` | `yamllint` with `extends: default`, `line-length` 200 and `document-start` disabled, over `skills/*/templates/*.yaml`: 22 findings at `main`, 0 after |
| The render tests write what the gate writes | `template_payload` in `tests/conftest.py` is the reference's rule, done once. All five render test files use it, so the hooks and steps they deploy are the gate's |
| A payload cannot go back to depth | `test_a_yaml_template_payload_starts_at_column_0`, one case per template. It fails with `gate-iac`'s hook put back at six columns |
| The rule has one home | `test_shared_reference.py` holds `template-layout.md` to its heading, and fails a skill that inlines it |

**Owed upstream.** `docs/promotion/published.json` adds this to the ADR 0059
revision 2 difference, and declares `reference/template-layout.md` as well. The
same amendment has to carry both changes, because a `SKILL.md` that does not
indent, given a template at column 0, writes a hook pre-commit rejects.

## This repository lints at `default`

**Closed 2026-10-31.**

**What changed.** `.yamllint.yml` is now `extends: default`, with the floor
stated at `level: error`, which is the shape the amended `lint-yaml` writes
(incubator#1220). Two values differ from what that skill would write, and the
file says why for each. `line-length` is 200 rather than 120, because pinned
digests, URLs and provenance stamps are single tokens that cannot be wrapped.
`document-start` is disabled, because no file here opens with `---` and a gate
template's payload must not. ADR 0059 Option 4 allows this: style on top of the
floor is a narrowing.

**What it found.** 419 findings, after the templates were moved to column 0:

| Rule | Findings | Where | Fix |
| --- | --- | --- | --- |
| `indentation` | 314 | `craft/react.yaml`, `craft/python.yaml`, `craft/any.yaml` | Each block sequence sat at its parent key's column, PyYAML's dump style. Indented by two |
| `braces` | 104 | `controls.yaml` and `controls.published.yaml`, 52 each | `args: { … }` written `args: {…}`. The published copy is regenerated by `register-check publish` |
| `empty-lines` | 1 | `.github/workflows/register-check.yml` | A trailing blank line removed |

**How it was shown to hold.**

| Claim | Evidence |
| --- | --- |
| Nothing changed but layout | `yaml.safe_load` gives equal data before and after, for each of the three Craft files and for `controls.yaml`. `scripts/craft_publish.py` writes 0 of 16 artefacts |
| It passes | `uv run yamllint .`: 0 findings, warnings included. `run --control YML-001`: PASS |
| The floor must still be stated | With `level: error` removed from `truthy`, YML-001 fails: the rule is at the preset's level |
| Nothing else moved | 1862 tests pass. No `register_contract` bump, because no `verify`, `rung`, `variance` or `applies_to` changed |

## `lint-yaml` 0.1.16 is deployed here

**Closed 2026-10-31**, item 3. incubator#1220 was merged on 2026-10-29 and
published as `lint-yaml` 0.1.16. It was installed at user scope and run here.

**What the run did, locus by locus.**

| Step | Result |
| --- | --- |
| 1. Install | `uv add --dev yamllint` changed nothing: 1.38.0 was already in `uv.lock`. The invocation is `uv run yamllint`, from `.claude/skill-config.yaml` |
| 2. Config | `.yamllint.yml` overwritten with the skill's config, then two values changed by hand (below) |
| 2.5a. Editor hook | The hand-wired copy was `STALE`. Replaced with the canonical script, and `LINT_INVOCATION` written. It now differs from upstream by that line only |
| 2.5b. Settings | Entry already present. Skipped |
| 3. Pre-commit | The `repo: local` hook already present. Skipped |
| 4. CI | Skipped, by the operator's choice. The skill picks `lint.yml` by name, finds no step there, and would add a second step and `astral-sh/setup-uv`. YML-001's ci locus is already the step in `register-check.yml`, with the uv the register pins |
| 5. Smoke test | 85 findings under the skill's config: 46 `line-length` over 120, and 39 `document-start` warnings |

**The two values changed by hand.** `line-length` is 200, because pinned
digests, URLs and stamps cannot be wrapped. With 120, YML-001 fails. And
`document-start` is disabled, because no file here opens with `---` and a gate
template must not. The file says both, at each rule.

**How it was shown to hold.**

| Claim | Evidence |
| --- | --- |
| The hook passes TYP-001 and LNT-001 unedited | `uv run mypy` and `uv run ruff check .claude/hooks` are clean, and `test_toolchain_pin.py` passes |
| The hook runs | Given `controls.yaml` under the skill's config, it reports the findings and labels them `yamllint`, not `uv`. That is the TOOL-label fix from the amendment |
| YML-001 holds | `uv run yamllint .`: 0 findings. `run --control YML-001`: PASS. 1862 tests pass and pre-commit is clean |

**Three things still to ask of `lint-yaml`.**

- **Step 4 matches the workflow by file name.** It checks only the one file it
  picks, so a repository whose step is in another workflow gets a second one.
  It should look for the configured invocation in every workflow first.
- **`validate-config.py` imports `yaml` under a bare `python3`.** That
  interpreter has no PyYAML in this container, so the script crashed. It was
  run with `uv run python` instead.
- **Nothing the skill writes is stamped.** So `register-check deployments`
  cannot list YML-001 under `lint-yaml`, as it lists DOC-001 under `lint-md`.
