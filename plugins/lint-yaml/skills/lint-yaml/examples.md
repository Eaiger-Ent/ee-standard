# lint-yaml — Calibration Examples

## §Strong

All four artefacts produced; smoke-test runs cleanly:

- `.yamllint.yml` written with `extends: default`, `line-length.max: 200`, and `key-duplicates`
  and `truthy` stated at `level: error`
- `.pre-commit-config.yaml` has a `repo: local` yamllint hook whose `entry:` is `YAMLLINT_INVOCATION`
- `.github/workflows/ci.yml` (or `lint.yml`) has a `Lint YAML` step running `YAMLLINT_INVOCATION .`
- All three loci run the same pinned invocation (`uv run yamllint`, or `uvx --from yamllint==<version> yamllint`)
- `<YAMLLINT_INVOCATION> .` exits 0 with 0 violations

Expected output matches the **Success** block in `output-templates.md`.

## §Weak

A weak run is missing ≥1 artefact:

- Config written but pre-commit hook missing (Step 3 skipped or failed silently)
- Pre-commit hook added but CI step missing (Step 4 skipped)
- Linter installed but `.yamllint.yml` not written
- Smoke-test not run (Step 5 skipped)
- A locus runs a different `yamllint` from the others — a bare `pip install yamllint` in CI, or a
  `rev:`-pinned pre-commit mirror — so the version a commit is checked with is not the one CI uses

Any of these produces an incomplete setup that will not catch YAML violations in CI or on commit.
