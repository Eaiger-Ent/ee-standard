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
