# lint-md — migrating off pymarkdownlnt

Run this section only when the pre-flight set `LEGACY_STATE` to `LEGACY_FOUND`.
Every step is conditional: if the file or the reference is absent, skip it and
move on. Report the outcome in the `Migration` block of `output-templates.md`.

1. **Remove `.pymarkdown.json`:**

   ```bash
   rm .pymarkdown.json
   ```

2. **Remove pymarkdown from `.pre-commit-config.yaml`** (if present):

   ```bash
   grep -q "jackdewinter/pymarkdown" .pre-commit-config.yaml 2>/dev/null && echo "PRESENT" || echo "ABSENT"
   ```

   If `PRESENT`: use **Edit** to remove the `jackdewinter/pymarkdown` repo block (the
   `- repo:` line and all indented lines beneath it up to the next `- repo:` or end of file).

3. **Remove pymarkdownlnt from GitHub Actions** (if present). Search all workflow files:

   ```bash
   grep -rl "pymarkdownlnt\|pymarkdown" .github/workflows/ 2>/dev/null || true
   ```

   For each match: use **Edit** to replace the pymarkdown install+scan step with the
   `markdownlint-cli2` step from Step 5 above.

4. **Remove from Python package manifest** (if present):

   ```bash
   grep -q "pymarkdownlnt" pyproject.toml 2>/dev/null && echo "PRESENT" || echo "ABSENT"
   grep -q "pymarkdownlnt" requirements*.txt 2>/dev/null && echo "PRESENT" || echo "ABSENT"
   ```

   If found, use **Edit** to remove the `pymarkdownlnt` line. Tell the user to run
   `uv sync` or `pip install -r requirements.txt` to update their environment.

5. **Confirm migration complete:**

   ```bash
   test ! -f .pymarkdown.json && echo "REMOVED" || echo "STILL_EXISTS"
   ```

   Tell the user: "Migration complete — pymarkdownlnt removed, markdownlint-cli2 in place."
