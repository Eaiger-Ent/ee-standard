# gate-quality — editor file-type binding rules (LNT-001, Step 3b)

Installing the extension is not the extension being the tool that runs, and the
difference is the failure this step exists for: `charliermarsh.ruff` was
installed for the whole time a devcontainer feature had Python files bound to
`ms-python.autopep8`, and LNT-001 passed throughout (ADR 0029 point 4).

**Skip this sub-step where `EDITOR_LANGUAGE` is absent.** A gate whose register
entry declares no `editor_binding` holds no file type, and writing one would
mandate a binding the register does not — eslint is a linter, not TypeScript's
formatter.

Otherwise read `${CLAUDE_SKILL_DIR}/templates/editor-settings.json`, substitute
`{{EDITOR_LANGUAGE}}`, `{{EDITOR_BINDING_SETTING}}`, `{{EDITOR_EXTENSION}}`,
`{{STACK}}`, `{{SKILL_VERSION}}`, `{{GATE_CONTRACT}}`, `{{REGISTER_VERSION}}` and
`{{REGISTER_CONTRACT}}`, and merge it into **`.vscode/settings.json`**,
preserving every other setting. Create the file where it does not exist.

- **`BINDING_STATE` shows another extension holding the language:** replace that
  value and say in the stamp comment which extension was displaced. A repository
  that deliberately mandates a different one changes the register, not this
  file.
- **`BINDING_STATE` shows `devcontainer.json` also setting it:** remove it from
  there. The binding belongs at workspace scope alone — a copy in
  `devcontainer.json` lands in the same machine-scoped file a feature's does and
  merges on terms the specification declines to state. The checker fails the
  duplicate even when the two agree.

Never write the binding into `devcontainer.json`, whichever file the extension
list went into in Step 3.

The editor reads the same configuration pre-commit and CI read. Write nothing
that configures rules here: an editor with rules of its own is the second copy
this standard exists to prevent.
