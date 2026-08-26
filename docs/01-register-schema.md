# Register schema

Field-by-field specification for `controls.yaml`. Concepts behind these fields
are in [`00-concepts.md`](00-concepts.md).

The register is validated by `register-check schema` on every commit. A malformed
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
| `platform_credentials` | no | list | Secrets SEC-003 permits a workflow to reference — see [`platform_credentials`](#platform_credentials). |
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
| `rationale_adr` | yes | path or URL | The ADR recording why this control exists. A path resolves against the **register's own directory**; an `http(s)` URL is a citation, whose existence the schema does not decide. See below. |

### `rationale_adr`

**A path or an `http(s)` URL, and which one you use depends on where your ADRs
live relative to your register.**

A path resolves against the directory holding `controls.yaml`, not against the
repository being checked. That is right for the repository that authors a
register and wrong for every repository that adopts one: a register fetched into
a consumer repo names `docs/adr/…` files that were never going to be there, and
until register contract 30 that failed **every control in the register** on a
directory the adopter had no reason to have. Phase 4 met it at Step 1 of the
first real adoption.

So a citation may be a URL instead. The schema checks its shape and stops there —
whether a URL resolves is not decidable from a file, and a check that guessed
would be reporting on something it never looked at.

**What replaces the existence check is not nothing.** For the register this
repository ships, `tests/test_rationale_citations.py` holds every citation to
the address `tools.register-check.install.repository` names *and* to a file in
this working tree, so a renamed or archived ADR still fails a build — just not
an adopter's. That is a test rather than a control because it governs how this
repository keeps its own records, not what a conformant repository contains
([ADR 0022](adr/0022-a-platform-token-ci-carries.md) requirement 6).

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

#### `provenance_stamp_present` and `deployed_by`

A control whose artefacts a gate skill writes names that gate in `deployed_by`,
and reads its stamp back with a `provenance_stamp_present` block:

```yaml
deployed_by: gate-secrets
verify:
  - kind: file
    assert: provenance_stamp_present
    args: { skill: gate-secrets }
```

The two must name the same skill, and the schema rejects a register where they
do not — two fields in one entry saying who deploys a control, free to drift
apart, would be theme T-2 inside the file that exists to prevent it. A
`provenance_stamp_present` block on a control with no `deployed_by` is rejected
for the same reason: the stamp records the gate that writes the artefact, so
there has to be one.

What the block checks is **soundness, not currency**. A stamp behind the
register is staleness, which is reported and never enforced
([`00-concepts.md`](00-concepts.md) § Notify, never redeploy); a stamp naming a
control the register does not define, or claiming a contract the register has
not reached, is a defect in the deployment and fails.

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
`kind: command` — the `register-check assert <name>` form used before contract
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
    run: register-check meta GOV-001
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

#### The one exception

A meta-control verifies itself by self-invocation, and that block is
`kind: command`:

```yaml
meta_controls:
  - id: GOV-002
    verify:
      - kind: command
        run: register-check meta GOV-002
```

It runs **in process** — `verify_meta.py` matches that exact shape and calls the
check directly, never shelling out — so by the definition above it is a
`file`-shaped assertion declared as a command, which the schema rejects
everywhere else.

**The shape is forced, not chosen.** A meta-control carries a three-valued
`Verdict` ([ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md)) so that
GOV-002 can report "no comparison point" rather than fabricating a violation. A
`kind: file` assert returns a boolean, which cannot express that third answer, so
unifying the two would mean widening every assert's return type to carry a
verdict — a cost paid by eight asserts to tidy three blocks.

**And it decides nothing.** The reason contract 3 rejected the
`register-check assert …` spelling was that GOV-001 derives reachability from
`kind: command` blocks, so the miscategorisation chose a control's verdict.
GOV-001 iterates `register.controls` and never `meta_controls`, so the same
mistake here reaches no verdict at all.

The exception is bounded by the validator rather than by convention: only a
meta-control may use the spelling, and only for **its own id**. A control using
it is rejected — that would be § E again, in the branch GOV-001 actually reads —
and so is a meta-control whose block runs a different meta-control's check,
which would render one control's verdict under another's name.

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
    release_repo: gitleaks/gitleaks
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

`source: toolchain` is the third case, and it behaves like `lockfile` for a
different reason: the version lives in a file every locus reads, so again no
locus repeats it — but no package manager produced or maintains the file. A
human writes it. `.python-version` is the case that created the field
([ADR 0027](adr/0027-the-interpreter-is-a-pinned-tool.md)):

```yaml
  python:
    source: toolchain
    toolchain: .python-version
    invocation: uv run
```

Neither existing value would have been true. `literal` means the number lives in
the register and each locus repeats it; `lockfile` means a package manager owns
it. The interpreter is neither, and recording it as either would have been a
claim the register could not keep.

Prefer `lockfile`, then `toolchain`. Both eliminate duplication rather than
reconciling it — a `literal` tool is the case where nothing else is available.
`lockfile` comes first because a package manager maintains the file; a toolchain
file is maintained by whoever remembers, which is why the bot annotation matters
more there rather than less.

**`pinned_at` is required under `source: literal`** and rejected under the other
two, the same asymmetry as `version:` and for the same reason: neither a
lockfile-sourced nor a toolchain-sourced tool has a version at any locus to keep
in step, so there are no repetitions to list.

**`toolchain` names the file that owns the version** and is required under
`source: toolchain`, rejected under the other two. `lockfile:` beside it is a
schema error rather than a synonym — the distinction between a file a package
manager writes and a file a person writes is the whole content of the third
source value.

**`release_repo` names where a literal tool's release is fetched from**, as
`owner/name`. It is optional, and rejected under `source: lockfile` — a
lockfile-sourced tool is installed by its package manager and has no release to
download. It exists because a gate skill that installs the tool has to know, and
the value previously lived only inside the `# renovate: … depName=` annotation,
which is written for a bot rather than as a field anything can read. A fork or
an internal mirror is a reasonable thing for a repository to differ on without
the checker changing, so it answers *yes* to
[ADR 0018](adr/0018-register-checker-boundary.md)'s test.

**`install` names where an adopting repository obtains the tool**, and is the
one field here that is about a repository other than this one:

```yaml
  register-check:
    source: lockfile
    lockfile: uv.lock
    invocation: uv run register-check
    install:
      repository: https://github.com/<owner>/<repo>   # https, so no credential
      ref: v0.1.0                                     # a version tag, never a branch
```

It is optional, and it exists for the case `lockfile` cannot answer on its own:
`source: lockfile` says a package manager owns the version, and says nothing
about how the package got into the manifest. For every other tool that is not a
question — `markdownlint-cli2` is on npm — and for the checker it was the whole
of the gap ([ADR 0032](adr/0032-the-checker-is-installed-from-a-tagged-ref.md)):
three Tier-1 controls run a command that, outside this repository, did not exist.

`repository` must be an `https` URL, because an adopter clones it without being
granted anything, and a scheme that needs a credential is an install nobody
outside can run. `ref` must be a version tag such as `v1.2.3`. A branch resolves
to whatever it says today — the defect DEV-001 refuses in an image tag and
SUP-003 in an action ref — and a bare SHA is a pin that says nothing about which
release it is. The address lives here rather than in the skill that reads it for
the same reason `release_repo` does: a fork or an internal mirror is a
reasonable thing for a repository to differ on without the checker changing.

What is deliberately **not** here is the spelling that turns an address into a
requirement. That is `ecosystems.<name>.git_dependency`, because PEP 440's
direct reference is a fact about Python and not about this project — and a
repository moving to an internal mirror would otherwise have to restate the
grammar to change the host.

**`invocation` is its mirror** — required under `source: lockfile` and
`source: toolchain`, rejected under `source: literal`. A literal tool is
installed onto `PATH` at each locus, so its pin is the version; the other two
are resolved by something that reads an authority file, so the register records
how a locus reaches it. `.python-version` selects nothing on its own: `uv run`
reads it and `python3` does not, so a locus spelling the second gets the system
interpreter no matter what the file says.

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
      - .github/workflows/register-check.yml
```

`tool_versions_match_register` reads exactly these paths. A declared site that
does not exist fails, and so does one that exists but holds no pin — both are
the same silence, and silence reading as agreement is what this field was moved
out of the checker to stop. A toolchain file is held to the same two rules for
the same reason: untracked fails, and tracked-but-naming-no-version fails, since
either leaves every locus resolving as though the file were not there. Until contract 8 the loci were four of this
repository's own filenames inside `register-check`, so renaming a workflow took
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
    lock_entry:                        # regexes; what a package looks like in a lockfile
      - '(?m)^\s+{package} \('
    frozen_install_command:            # what a gate writes, keyed by lockfile
      Gemfile.lock: "bundle install --deployment"
    add_dev_dependency:                # optional; see below
      Gemfile.lock: "bundle add --group development {package}"
```

Every field except `add_dev_dependency` is required and every list non-empty.
`frozen_install` and `lock_entry` are compiled at schema time like
`suppression`, because a pattern that matches nothing is a control passing
vacuously rather than a crash — an ecosystem the checker knew nothing about is
exactly how a repository with a `go.mod` came to be told that every CI install
was frozen.

**`lock_entry` is the existence half of
[ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md).** That ADR made
every locus invoke the artefact its lockfile owns, and measured the one
condition no spelling of `invocation` covers: `uv run <tool>` falls through to
`PATH` when the tool is absent from the project altogether (§ Applied to the
quality gates, case C). An invocation cannot assert the existence of the thing
it invokes, so `stack_tool_pinned_in_lockfile` looks the package up, and these
patterns are how it is recognised. `{package}` is substituted with the name
sought, regex-escaped — a plain substitution rather than `str.format`, because a
regular expression is full of braces.

**`frozen_install_command` is what a gate writes where `frozen_install` is what
the checker credits**, and the schema holds the pair together: every command
must match one of its own ecosystem's patterns. Without that rule a register
could have a gate deploy an install step the control it deploys then refuses —
a deployment that fails its own verification, discovered by whoever ran it. It
is required of **every** ecosystem, covering every lockfile that ecosystem
declares, because SUP-001 applies `always`: an ecosystem with a lockfile it
cannot install from is a control nothing can deploy.

**`add_dev_dependency` is how a gate creates a pin that is missing**, keyed by
the lockfile that is present rather than by the ecosystem: `uv add --dev` and
`poetry add --group dev` are both python, and which one is right is a fact about
the repository. It is optional in general and **required of any ecosystem a
stack names**, covering every lockfile that ecosystem declares — a gate that can
fail a control for an unpinned tool and cannot pin it would deploy a control it
is unable to satisfy. Inventing an idiom for ecosystems no gate deploys into
would be worse than leaving it absent, which is why it is not required
everywhere. Each command must contain the `{package}` placeholder; one with
nowhere to put the name adds a different dependency every time, or none.

**`git_dependency` is how this ecosystem spells a dependency on a git ref**, as
the `{package}` that `add_dev_dependency` above then takes. It must name all
three of `{package}`, `{repository}` and `{ref}`; a template that dropped one
would compose an address that resolves to *something*, which is worse than one
that does not compose.

```yaml
  python:
    git_dependency: "{package} @ git+{repository}@{ref}"
```

It is optional, and its absence is a verdict rather than a default:
`register-install` stops and says this ecosystem has no spelling for a git
dependency instead of inventing one, because the wrong grammar fails at install
time in the adopter's repository rather than here. Only `python` declares one
today, and [ADR 0032](adr/0032-the-checker-is-installed-from-a-tagged-ref.md)
§ The non-Python adopter is not solved records that as known.

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

### `platform_credentials`

The secrets SEC-003 permits a workflow to reference, and the events each may
appear under ([ADR 0022](adr/0022-a-platform-token-ci-carries.md),
requirement 2).

```yaml
platform_credentials:
  - name: GITHUB_TOKEN
    triggers: any               # `any`, or a list of workflow events
    max_lifetime_hours: 24
```

**This is an allow-list, and `cloud_credentials:` above is a deny-list.** The
direction is the whole difference: a deny-list that has not heard of a
credential passes it, so omitting it makes the checker fall back to a built-in
set; an allow-list that has not heard of one fails it, so omitting this section
permits no secret at all. An empty list is rejected rather than read that way,
because omitting the key says it already.

`triggers` is what makes the deployment-environment posture checkable rather
than a convention. A standing credential names the events it may appear under,
so a branch that adds `pull_request:` to a workflow in order to reach the
secret fails here — the guard cannot live in the workflow file the pull request
is editing. `any` is legitimate only for a credential the platform mints per
job and revokes with it: the event cannot change what such a token reaches,
because it does not outlive the job that ran under it.

`max_lifetime_hours` is a positive whole number of hours, and from contract 23
SEC-003's `kind: remote` block reads it: `platform_token_expires_within`
compares the `github-authentication-token-expiration` header GitHub returns for
the credential the run carries against the **largest** lifetime any entry
permits, and fails a token that outlives it. The block answers only inside a
GitHub Actions job — SEC-003's locus is `ci`, and a developer's own token is a
different credential — and is UNCLASSIFIED everywhere else.

That a workflow spells the platform token `${{ github.token }}` as often as
`${{ secrets.GITHUB_TOKEN }}` is detection and stays in the checker, as
`cloud_credentials:` spelling equivalence does.

### `stacks`

Per-stack gate tools: which linter and type checker a stack mandates, and how
each locus runs them. A register fact per
[ADR 0018](adr/0018-register-checker-boundary.md) — a repository may mandate a
different linter without the checker changing.

```yaml
stacks:
  python:                       # the key IS a predicate name
    source_globs: ["*.py"]      # the tracked files its gates must cover
    ecosystem: python           # whose lockfile pins the gate tools below
    gates:
      lint:                     # role: lint | typecheck
        tool: ruff
        invocation: ruff check  # matched as an invocation in a gating CI step
        pre_commit: ruff        # hook id or entry substring
        editor_extension: charliermarsh.ruff
        editor_binding:         # the file type that extension must hold
          language: python
          setting: editor.defaultFormatter
        config:
          - {file: pyproject.toml, section: tool.ruff}
          - {file: ruff.toml}
      typecheck:
        tool: mypy
        package: mypy           # optional; the name in the lockfile, if different
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
| `package` | no | The name the tool is pinned under, where it differs. Defaults to `tool`. |
| `invocation` | yes | How CI runs it. Matched as an invocation, not a substring. |
| `config` | yes | Where its configuration may live, most specific first. |
| `pre_commit` | no | Hook id or entry substring at the pre-commit locus. |
| `editor_extension` | no | Extension id, found in `devcontainer.json` **or** `.vscode/extensions.json`. |
| `editor_binding` | no | `{language, setting}` — the file type `editor_extension` must hold. Requires `editor_extension`. |
| `strict_key` | no | A boolean inside the matched section that must be true. |
| `coverage_key` | no | Dotted path, **from the config file's root**, to the tool's allow-list. |

**`ecosystem` and `package` are the two names a pin needs.** A stack and an
ecosystem are different things — `python` the stack mandates ruff and mypy,
`python` the ecosystem knows what a lockfile is — and `ecosystem` says which one
pins the other's tools. It is required, and required to name a defined
ecosystem: a stack whose ecosystem is absent or misspelt is a stack whose gate
tools no lockfile is checked for. `package` covers the case where the tool's
name is not the package's: `tsc` is a binary the `typescript` package ships, so
searching a correctly-pinned lockfile for `tsc` finds nothing and would fail a
repository that satisfies the control.

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

**`editor_binding` is presence turned into exclusivity** (register contract 21,
[ADR 0029](adr/0029-the-editor-locus-is-configured-by-the-repository.md) points
3 and 4). An extension being installed is not that extension being the tool that
runs, and the difference is where a control was passing over a live violation:
`ghcr.io/devcontainers/features/python:1` published

```json
"[python]": { "editor.defaultFormatter": "ms-python.autopep8" }
```

in a repository whose register pinned ruff, with `charliermarsh.ruff` installed
alongside it the whole time. DEV-001's digest pin governs what a feature
*installs* and says nothing about what it *configures*, so nothing saw it.

The binding is read from **`.vscode/settings.json`**, at workspace scope, which
is the only scope that wins by documented rule: the containers.dev merge table
says of `customizations` only that "merging is left to the tools". Three states
fail — another extension holding the language, *nobody* holding it, and the same
binding restated in `devcontainer.json`. The second is the one that matters,
because in the case above no tracked file said anything at all and an assert
objecting only to a wrong value would have passed it. The third fails even when
the two agree: agreement under an undefined merge rule is luck.

`language` and `setting` are both register facts rather than checker ones. A
stack may mandate a formatter for one file type and not another, and not every
linter is its language's formatter — the `typescript` lint gate declares no
binding, because eslint is not TypeScript's formatter and demanding it hold
`editor.defaultFormatter` would mandate something no reasonable repository
writes. Omitting the field asserts the gate's tool holds no file type, the same
shape `coverage_key`'s absence has. Declaring it without `editor_extension` is a
schema error: a file type must be held by something.

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
      - kind: file
        assert: stack_tool_pinned_in_lockfile
        args: { role: lint }
```

The two blocks are the two halves of ADR 0020 and are separable on purpose. The
first says every locus reaches the artefact the lockfile pins; the second says
the pin exists. A repository can satisfy either without the other, and only the
pair means *the version that runs is the version that was reviewed*.

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
