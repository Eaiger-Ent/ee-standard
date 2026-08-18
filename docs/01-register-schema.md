# Register schema

Field-by-field specification for `controls.yaml`. Concepts behind these fields
are in [`00-concepts.md`](00-concepts.md).

The register is validated by `standard-check schema` on every commit. A malformed
register is a build failure, not a warning — everything downstream derives from
it, so an unparseable register means no control is enforced.

## Top level

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `version` | yes | semver string | The register's own version. Bump per [SemVer](https://semver.org/spec/v2.0.0.html). |
| `meta.owner` | yes | string | Team accountable for the register as a whole. |
| `meta.register_contract` | yes | integer | Bumped **only** when a change alters what gets deployed. Drives staleness detection. |
| `predicates` | yes | map | Stack predicates, evaluated against the repo. |
| `tools` | no | map | Pinned tool versions and their authority — see [`tools`](#tools). |
| `ecosystems` | no | map | Package ecosystems: manifests, lockfiles, Dependabot spellings, test commands, frozen-install idioms. |
| `stacks` | no | map | Per-stack gate tools — see [`stacks`](#stacks). |
| `suppression` | no | list | Regular expressions that count as swallowing a failure. |
| `cloud_credentials` | no | list | Static cloud credential names SEC-002 forbids — see [`cloud_credentials`](#cloud_credentials). |
| `controls` | yes | list | The controls. |
| `meta_controls` | yes | list | Controls that check the register itself. |

Unknown keys are rejected at every level — document, `meta`, control,
`standard`, `also_see` entry, verify block and `partial`. A field the validator
accepts and ignores is a field that silently does nothing, which is how
`also_see` came to carry external URLs that nothing checked.

### `meta.register_contract`

This integer is the noise control for the whole system. It is bumped when a
control's `rung`, `verify`, `variance` or `applies_to` changes, and when the
register gains a field that a skill reading it has to understand — never for a
typo fix, a reworded `title`, or a new `also_see` link.

The last clause is stated because it was already the practice and not the
wording: contract 3 was a schema addition and so is contract 8, and a rule that
does not describe what has been done twice is a rule nobody can apply. A field a
skill must understand changes what deployment means, which is the test the first
sentence is reaching for.

Downstream skills recommend redeployment when the installed contract is ahead of
the one stamped in the repo. Bumping it for cosmetic edits trains people to
ignore the recommendation, which costs more than the edit saved.

## Control fields

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `id` | yes | `AAA-NNN` | Stable forever. Never reused, never renumbered. |
| `title` | yes | string | What is true when the control passes. Written as an assertion, not an instruction. |
| `enforces` | yes | string | The mechanical statement of what is checked. |
| `standard` | yes | object | `name` + `url` of the external standard. |
| `also_see` | no | list | Further `name`/`url` pairs — tool docs, internal playbooks. |
| `tier` | yes | 1-3 | See § Tiering in concepts. |
| `rung` | yes | enum | `advisory` / `warn` / `blocking`. |
| `locus` | yes | list | `editor` / `pre-commit` / `ci` / `remote`. |
| `applies_to` | yes | list | Predicate names. Unsatisfied predicate → control is **skipped**, not failed. |
| `deployed_by` | no | string | The gate skill that writes this control's artefacts. |
| `verify` | yes | list | One or more verification blocks. See below. |
| `owner` | yes | string | Team accountable for *this* control. |
| `variance` | yes | enum | `forbidden` / `narrowing-only`. |
| `also_see` | no | list | Supplementary `{name, url}` references. Each URL is validated like `standard.url`. |
| `baseline` | yes | path or `null` | Path to the baseline artefact, or `null` for no exemptions ever. |
| `review_by` | yes | ISO date | GOV-003 fails the build after this date. |
| `rationale_adr` | yes | path | The ADR recording why this control exists. |

### `id`

The identifier is the join key between the register, the provenance stamps in
deployed artefacts, the CI job names, and the ADRs. Renumbering breaks every one
of those links silently, so an ID is permanent even if the control is later
removed — a retired ID is simply never reissued.

### `title` versus `enforces`

`title` states the property in terms a reviewer can agree or disagree with:
*"A commit containing a secret cannot reach the remote."*

`enforces` states the mechanism: *"gitleaks runs as a pre-commit hook and as a
CI job, and push protection is enabled."*

Keeping them separate is what lets you notice that the mechanism no longer
achieves the property — the most common way a control becomes theatre.

### `standard`

Must be an external, citable definition with a resolving URL. "Because we said
so" is not a standard; if no external standard applies, that is a signal the
control is a local convention and belongs in a linter config rather than the
register.

Every URL in the register is verified to resolve before it is committed.

### `verify`

A list of blocks, each with a `kind`:

```yaml
verify:
  - kind: command          # exit code is the verdict
    run: gitleaks detect --no-banner --redact
  - kind: file             # a file exists and matches a shape
    assert: precommit_hook_present
    args: { id: gitleaks }
  - kind: remote           # platform API state
    assert: github_push_protection_enabled
```

All applicable blocks must pass for the control to pass. The `assert` names are
implemented in the checker and are a closed set — an unknown assert name is a
schema error, not a skipped check, so a typo cannot silently disable a control.

#### Block-level `applies_to`

A block may narrow itself to a repository shape:

```yaml
applies_to: [container, devcontainer]   # the control's shapes
verify:
  - kind: command
    run: hadolint --failure-threshold error
    applies_to: [container]             # only where a Dockerfile exists
  - kind: file
    assert: devcontainer_user_is_non_root
    applies_to: [devcontainer]
```

One control can then hold one property verified by different mechanisms for
different repository shapes. BLD-001 states that a container does not end as
root; a Dockerfile proves it with `USER`, a devcontainer with `remoteUser`, and
running either check against the other shape reports on something that is not
there — `hadolint` against a repository with no Dockerfile is a category error,
not a finding.

A block's predicates must be a **subset** of its control's. A block naming a
predicate the control does not have could never run, because the control is
skipped before the block is reached; that is a schema error rather than a silent
no-op.

If every block narrows itself out, the control reports `SKIPPED (predicate)` and
never `PASS`. The control applies but nothing verified it, and a green tick over
an empty check is the failure this distinction exists to prevent.

The three kinds are distinguished by *what performs the verification*, not by
which module implements it: `command` shells out to an external tool and reads
its exit code, `file` runs an in-process assertion over repository files, and
`remote` reads platform API state. An in-process assertion declared as
`kind: command` — the `standard-check assert <name>` form used before contract
3 — is now a schema error. It is not cosmetic: GOV-001 derives reachability from
`kind: command` blocks, so the miscategorisation decided that control's verdict.

`run:` is executed without a shell. A string containing a shell operator is
rejected at schema time, because it would become a literal argument rather than
an operator — `pytest && mypy` would have run `pytest` with two ignored
arguments and reported success.

#### `partial`

Any block may declare that it is not yet fully implemented ([ADR
0017](adr/0017-partial-verification-is-reported.md)):

```yaml
  - kind: command
    run: standard-check meta GOV-001
    partial:
      unverified: >-
        whether the CI workflow is a required status check
      expires: 2026-11-30
```

The control still renders the verdict it can compute, followed by a `partial:`
line naming what it cannot see. Both fields are required: without `unverified`
the gap is unnamed, and without `expires` "partial" becomes permanent. GOV-003
fails a declaration past its expiry, exactly as it fails a control past
`review_by`. A run containing any partial block is incomplete in the sense of
[ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md), so it cannot exit
`0`.

`remote` verifications need credentials and network, so they are skipped with an
explicit `SKIPPED (no credentials)` verdict rather than passing by default. A
skipped remote check never counts as a pass.

### `tools`

Where each tool's version is authoritative. The register does **not** try to be
the only place a version appears — a tool installed by a package manager
necessarily appears in that manager's manifest too. It records which authority
owns the value:

```yaml
tools:
  markdownlint-cli2:
    source: lockfile              # a package manager owns the version
    lockfile: package-lock.json
  gitleaks:
    source: literal               # nothing owns it; the value lives here
    version: "8.30.1"
    sha256: 551f6f...
```

Under `source: lockfile` no `version` may be recorded — the loci invoke the tool
through the package manager (`npx …`, `uv run …`), so there is no version at any
locus to disagree with, and a copy here would recreate the drift the field
exists to remove. Under `source: literal` the version lives here and each locus
repeats it; those repetitions carry a `# renovate:` annotation so a bot updates
them together, and `tool_versions_match_register` fails the build if one drifts.

The annotation is written above the `version:` line here as well as at each
locus, because the register is the authority: a proposal that moved the loci and
left this table behind is one `tool_versions_match_register` rejects. The
annotations are only worth writing if something reads them — a repository
carrying them without the bot installed has a mechanism on paper and none in
fact, which is what `docs/09-phase-1.5-review.md` § G records.

Prefer `lockfile`. It is the only option that eliminates duplication rather than
reconciling it, and it is available whenever the tool is installable from an
ecosystem the repo already locks.

**`pinned_at` is required under `source: literal`** and rejected under
`source: lockfile`, the same asymmetry as `version:` and for the same reason: a
lockfile-sourced tool has no version at any locus to keep in step, so there are
no repetitions to list.

**`invocation` is its mirror** — required under `source: lockfile`, rejected
under `source: literal`. A literal tool is installed onto `PATH` at each locus,
so its pin is the version; a lockfile tool is resolved out of a package tree, so
its pin is an artefact and the register records how a locus reaches it:

```yaml
  markdownlint-cli2:
    source: lockfile
    lockfile: package-lock.json
    invocation: node_modules/.bin/markdownlint-cli2
```

Without it, "the lockfile owns the version" is a claim about where the number is
written and not about which binary runs. `npx --no-install` was the invocation at
every locus here, and `--no-install` means *do not fetch*, not *resolve locally*:
with `node_modules` absent it exits 0 against whatever global is on `PATH`
([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md), § H6). The gate's
assert checks each declared locus against this form, so a locus reverting to
`npx` fails with the locus named.

```yaml
  gitleaks:
    source: literal
    version: "8.30.1"
    pinned_at:
      - .devcontainer/setup.sh
      - .github/workflows/standard-check.yml
```

`tool_versions_match_register` reads exactly these paths. A declared site that
does not exist fails, and so does one that exists but holds no pin — both are
the same silence, and silence reading as agreement is what this field was moved
out of the checker to stop. Until contract 8 the loci were four of this
repository's own filenames inside `standard-check`, so renaming a workflow took
it out of comparison with no verdict changing, and an adopting repository was
told its tools were pinned at no known locus against paths it had never had
(`docs/09-phase-1.5-review.md` § H2).

### `ecosystems`

A package ecosystem, and what counts as locked, installed and tested in it.

```yaml
ecosystems:
  ruby:
    manifest: [Gemfile, "*.gemspec"]   # how the ecosystem is detected
    lockfiles: [Gemfile.lock]          # any one of these, tracked
    dependabot: [bundler]              # accepted `package-ecosystem:` spellings
    test_commands: [rspec, "rake test"]
    frozen_install:                    # regexes; matched against gating CI steps
      - '\bbundle install\b[^\n]*--(?:deployment|frozen)\b'
```

Every field is required and every list non-empty. `frozen_install` is compiled at
schema time like `suppression`, because a pattern that matches nothing is a
control passing vacuously rather than a crash — an ecosystem the checker knew
nothing about is exactly how a repository with a `go.mod` came to be told that
every CI install was frozen.

The evidence must come from a step in a workflow that runs on `push` or
`pull_request`. A frozen install in a manually-triggered workflow shows what
somebody may choose to run, not what a merge has to pass.

### `cloud_credentials`

The static credential names SEC-002 forbids a workflow from referencing.

```yaml
cloud_credentials:
  - AWS_ACCESS_KEY_ID
  - GOOGLE_APPLICATION_CREDENTIALS
```

Matched case-insensitively, with `-` and `_` treated alike, so the same
credential is caught as an env var (`AWS_ACCESS_KEY_ID`) and as an action input
(`aws-access-key-id:`). That equivalence is detection and stays in the checker;
which names to look for is a register fact, because a repository on a different
cloud needs different ones and no checker change
([ADR 0018](adr/0018-register-checker-boundary.md), fourth pass). Omit the
section and the checker falls back to a built-in set, as with `suppression`.

### `stacks`

Per-stack gate tools: which linter and type checker a stack mandates, and how
each locus runs them. A register fact per
[ADR 0018](adr/0018-register-checker-boundary.md) — a repository may mandate a
different linter without the checker changing.

```yaml
stacks:
  python:                       # the key IS a predicate name
    source_globs: ["*.py"]      # the tracked files its gates must cover
    gates:
      lint:                     # role: lint | typecheck
        tool: ruff
        invocation: ruff check  # matched as an invocation in a gating CI step
        pre_commit: ruff        # hook id or entry substring
        editor_extension: charliermarsh.ruff
        config:
          - {file: pyproject.toml, section: tool.ruff}
          - {file: ruff.toml}
      typecheck:
        tool: mypy
        invocation: mypy
        pre_commit: mypy
        strict_key: strict      # a boolean in the section, which must be true
        coverage_key: tool.mypy.files   # where the tool's allow-list lives
        config:
          - {file: pyproject.toml, section: tool.mypy}
          - {file: mypy.ini, section: mypy}
```

| Field | Required | Notes |
| --- | --- | --- |
| `tool` | yes | The mandated tool's name, used in messages. |
| `invocation` | yes | How CI runs it. Matched as an invocation, not a substring. |
| `config` | yes | Where its configuration may live, most specific first. |
| `pre_commit` | no | Hook id or entry substring at the pre-commit locus. |
| `editor_extension` | no | Extension id, found in `devcontainer.json` **or** `.vscode/extensions.json`. |
| `strict_key` | no | A boolean inside the matched section that must be true. |
| `coverage_key` | no | Dotted path, **from the config file's root**, to the tool's allow-list. |

**The key is a predicate.** A stack applies exactly when its predicate does, so
`applies_to: [python, typescript]` on a control and the stacks of those names are
the same statement made once. A stack naming no predicate is a schema error: a
stack nothing can detect never applies, which is theme T-3 inside the register.

**`section` is not optional decoration.** A file being present is not the tool
being configured in it — `pyproject.toml` exists in every Python repository and
says nothing about ruff until `[tool.ruff]` does. A location with no `section`
counts as configured by existing, which is right for a file that exists only to
configure one tool.

**`coverage_key` is [ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md)
applied to a coverage list.** An exemption list makes an exclusion into a line
you can read — `.claude/**` is a string, so it can be compared against what git
tracks. An allow-list makes an exclusion into an *absence*: `files = ["src",
"tests"]` excludes `tools/` by not mentioning it, so there is nothing to read and
no diff when coverage shrinks relative to the codebase. Where one exists, every
tracked file matching the stack's `source_globs` must be under one of its roots.

The path is dotted from the file's **root**, not from the `section` — `include`
sits at the top level of a `tsconfig.json` while `strict` sits under
`compilerOptions`. Omitting the field asserts the tool has no allow-list at all,
which is true of `tsc` with no `include` (it compiles everything below its
tsconfig); that has to be a deliberate statement about the tool rather than an
oversight. An allow-list the config does not set is likewise not an exemption,
and is not reported as one.

Import-reachable files are not credited as covered. mypy follows imports out of
its allow-list, so a module something imports is checked today — by accident of
that import, and unchecked again the day it goes. Coverage that can be withdrawn
without editing the coverage list is not declared coverage.

**`pre_commit` and `editor_extension` are optional to the schema and required in
fact.** The validator demands whichever locus the controls using that role
declare: if a control lists an `editor` locus and an applicable stack's gate
names no extension, the register is rejected. Without that check a control could
claim a locus its gate had no way to verify, and whether that failed every
repository or was silently skipped would depend on how the assert was written.

A control reaches its gate through the verify block's `args`:

```yaml
      - kind: file
        assert: linter-wired-at-all-loci
        args: { role: lint }
```

### `suppression`

Regular expressions that count as swallowing a failure, used by
`no-failure-suppression` and by GOV-001's reachability test.

```yaml
suppression:
  - '\|\|\s*true\b'
  - '\|\|\s*:\s*(?:$|[;&|])'
```

Each is compiled at schema time, so a pattern that does not parse is a schema
error rather than a crash mid-run. Adding a pattern **strengthens** detection, so
a house idiom belongs here rather than in the checker — `|| :`, the terse
spelling of `|| true`, was missing from the checker's original set and let the
commonest short idiom through. Omit the section and the checker falls back to a
built-in set: an old register should detect something rather than nothing.

### `variance`

| Value | Local config may | Requires |
| --- | --- | --- |
| `forbidden` | nothing | — |
| `narrowing-only` | add rules, tighten thresholds | — |

Under `narrowing-only`, the checker classifies the delta's direction and fails
on any weakening.

`justified` and `free` were removed at contract 3 — see
[`00-concepts.md`](00-concepts.md) § Variance for why `justified` could not be
implemented as specified.

Direction classification fails in three known cases, all of which the checker
reports as `UNCLASSIFIED` rather than guessing: a rule replaced by a differently
named rule covering overlapping ground; a threshold whose direction depends on
the metric's polarity; and a config expressed as executable code rather than
declarative data.

### `baseline`

`null` means no exemptions are possible — the control passes everywhere or fails.
A path means the file at that path lists tolerated existing violations, and
GOV-002 enforces that it only ever shrinks.

Setting `baseline` from `null` to a path is a weakening and requires the same
recorded decision as a rung demotion.

### `review_by`

The date after which GOV-003 fails. This is not a reminder — it is an expiry.
Reviewing a control means re-reading the linked standard, confirming the
mechanism still achieves the property, and either extending the date or changing
the control.

An expiring control forces a re-decision rather than letting silence stand in for
agreement.

## Meta-control fields

Meta-controls take `id`, `title`, `enforces`, `rationale`, and `verify`. They
carry no `tier`, `rung`, `locus`, or `baseline` — they are unconditionally
blocking wherever the checker runs, and they cannot be baselined.

## Adding a control

1. Write the ADR first (`docs/adr/`). If the rationale will not survive being
   written down, the control is not ready.
2. Add the entry with `rung: advisory` and a `review_by` no more than a year out.
3. Verify every URL resolves.
4. Implement the `verify` blocks in the checker. An entry whose asserts do not
   exist fails schema validation, so this cannot be deferred.
5. Land it. Observe. Promote to `blocking` as a separate, deliberate change with
   its own commit, so the promotion is reviewable on its own merits.

Do **not** bump `meta.register_contract` in step 2 — advisory additions deploy
nothing. Bump it in step 5.
