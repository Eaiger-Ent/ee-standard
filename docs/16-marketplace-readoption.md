# Re-adopting from the marketplace

The runbook for the two Phase 6 exit criteria that need a macOS host with
Docker: *the consumer repo re-adopts from the marketplace copy and still passes*
— **closed 2026-08-30**, and § Building the shipped template, which is what
[`08-adopting.md`](08-adopting.md) § Status still owes a reader before it can
claim the template has been built.

It is written for an operator on a host this container is not, so it states what
that host must have and what each step is expected to produce, and it **does not
restate the adoption steps themselves**: those live in
[`08-adopting.md`](08-adopting.md) and a second copy of them here would be free
to drift from the guide an adopter actually follows.

## Why this run exists at all

Phase 4 adopted `Eaiger-Ent/ee-standard-consumer` and closed 6/6 — but it
installed `control-register` from **this repository's own directory** used as a
marketplace, not from a published one. That was a bounded deviation, recorded at
the time, and this is the criterion that was left open to settle it.

The difference is not academic. The published copy went through the incubator's
`promote.py` and four remediation commits, and for a day it was a **different
plugin at the same version number** — nine rewritten `SKILL.md` files, ten new
files, and a devcontainer template whose quoted placeholders failed a control on
a correctly pinned container
([`15-phase-6-review.md`](15-phase-6-review.md) § The ninth and tenth slices).
Both are fixed. Neither would have been found by installing from a local
directory, which is the whole argument for this run.

## What the host must have

| Requirement | Why, and how to check |
| --- | --- |
| **macOS with Docker running** | `devcontainer build`/`up` has no Docker inside the container. `docker info` must succeed |
| **The `devcontainer` CLI** | `devcontainer --version`. The template is built by it, not by `docker build` |
| **`claude` logged in** | `claude setup-token` on the host, per [`08-adopting.md`](08-adopting.md) § 2.0a. The token is the Keychain's and cannot be produced inside |
| **`gh` authenticated to `Eaiger-Ent`** | For the consumer repository. `gh auth status` |
| **A credential for `EqualExperts/ee-skills`** | Only if you take the private route below. `ee-skills` is private; the public route needs nothing |
| **The consumer repo cloned** | `Eaiger-Ent/ee-standard-consumer`, untouched since 2026-08-26 |

Four steps are the host's and everything else is the container's —
[`08-adopting.md`](08-adopting.md) § 2.0a is that split, with the three costs
Phase 4 paid for getting it wrong. Read it before starting; it is the section
that saves the most time.

## Which marketplace

**Both, and they are different artefacts.** This is the part most likely to be
got wrong by doing the obvious thing.

| Route | Serves | Who uses it |
| --- | --- | --- |
| `Eaiger-Ent/ee-standard` | This repository's tree, directly | **What an adopter follows** — [`08-adopting.md`](08-adopting.md) § 0.0, and what [ADR 0044](adr/0044-the-adopter-installs-from-the-public-marketplace.md) makes the published route. Public: needs no credential |
| `EqualExperts/ee-skills` | The promoted copy, after `promote.py` | What the criterion means by *the marketplace copy*. Private |

They are byte-identical as of 2026-08-30 and were not the day before. **Check
that they still are before trusting either**, because if they have diverged
again that is the finding, not the conformance run:

```bash
claude plugin marketplace list          # read the Source line of each; see below
claude plugin marketplace add Eaiger-Ent/ee-standard
claude plugin marketplace update ee-standard
claude plugin marketplace update ee-skills
claude plugin install control-register@ee-standard --scope user
# and, with an ee-skills credential:
claude plugin install control-register@ee-skills --scope user
diff -rq ~/.claude/plugins/cache/ee-standard/control-register/*/ \
         ~/.claude/plugins/cache/ee-skills/control-register/*/ --exclude='.in_use'
```

**A marketplace has a source, and the first line is there because it may not be
the one you assume.** `claude plugin marketplace list` prints it, and on the
macOS host `ee-skills` was `Source: Directory (/Users/nathan/git/ee-skills)` — a
clone twenty commits behind `origin/master`. A `diff` against that compares this
tree with a host's stale opinion of the promoted copy, and it is silent for the
same reason a correct one is, so it reads as a pass. Where the source is a
directory, update the clone or run the check somewhere the marketplace resolves
to `GitHub (EqualExperts/ee-skills)` — the consumer's own devcontainer does, and
is where this check belongs anyway.

Silence is the pass. Do the conformance run against the **`ee-skills`** copy,
since that is the one the criterion names, and record that the public one is
identical rather than running everything twice.

## The steps

1. **Remove the Phase 4 install.** The consumer has `control-register` from a
   local directory used as a marketplace; leaving it installed means the run
   proves nothing. `claude plugin uninstall`, and remove that marketplace too.
2. **Install from the marketplace**, as above.
3. **Follow [`08-adopting.md`](08-adopting.md) from § 0.1.** The register is
   already committed in the consumer, so § 0.1 is a check rather than a fetch.
4. **Run `/register-adopt`.** It should find most controls already satisfied —
   this is a re-adoption, and a gate that rewrites an artefact identically is
   the expected outcome, not a no-op to be alarmed by.
5. **Run the checker and both workflows.**

## What passing looks like

Judge against what Phase 4 measured, not against a green light:

```text
uv run register-check
  12 passed, 0 failed, 1 skipped (predicate: terraform), 3/3 meta-controls
  exit 3
```

**Exit `3` is the pass.** SEC-003's remote blocks answer only inside a GitHub
Actions job, so a developer's own token settles nothing about the credential CI
carries. A `0` here would mean something had been skipped that should not have
been. A `1` is a real violation and fails the criterion.

Then: both workflows green on push and pull_request, and no provenance stamp
*ahead* of the gate that wrote it.

**Ask that in the form the consumer's checker can answer.** `register-check
deployments` is the spelling used in this repository and it need not exist
there: the consumer is pinned to the checker tag its register names, and the
subcommand arrived with [ADR 0038](adr/0038-the-stamp-records-the-deployment-contract.md).
**Do not decide that from the register contract** — ADR 0038 landed *at*
contract 30, which is also the contract `v0.5.0` ships, so a consumer and this
repository can agree on the contract number and disagree about whether the
subcommand exists. Run `register-check --help` and look. Where it is absent,
read the state from each control's `deployed_by` and the provenance stamps in
the files those gates wrote. It is a weaker question — a stamp says what was deployed, `deployments`
reconciles that against what is *installed*
([ADR 0043](adr/0043-a-declination-is-reconciled-against-the-installed-skill.md))
— so record which of the two you asked. A consumer behind this repository is
not a defect; it is what pinning to a tagged ref
([ADR 0032](adr/0032-the-checker-is-installed-from-a-tagged-ref.md)) means.

## What would fail the criterion

Worth knowing in advance, so a bad result is recognised rather than explained
away:

- Any control failing that passed in Phase 4 — the published artefact is not
  equivalent to the local one.
- `DEV-001` failing on the devcontainer template — the placeholder-quoting
  defect returning.
- A gate that cannot find `${CLAUDE_PLUGIN_ROOT}/reference/…` — the promotion
  routed the shared files into `skills/<bundle>/` after all.
- `/register-adopt` unable to dispatch a gate — the `disable-model-invocation`
  regression [ADR 0035](adr/0035-a-dispatched-skill-is-reachable.md) fixed.

**Record the result either way.** A failure here is worth more than a pass: it
is the last chance to find something before an adopter does, which is the reason
this criterion was not closed by the plugin installing cleanly on a developer's
machine.

## Where the record goes

Two places, and they are not copies of each other. The first run of this runbook
recorded only the first, which left the evidence for a criterion of *this*
repository legible only in another one.

| Where | What it holds | Whose voice |
| --- | --- | --- |
| The consumer's `README.md` § Adoption record | What happened to **that** repository: what was installed, what the gates did, what the checker reported | The operator's, on the machine that ran it |
| [`15-phase-6-review.md`](15-phase-6-review.md), as a slice | What the run **proves** about the standard, and anything it found that no criterion asked about | This repository's |

The second **cites** the first and does not copy it — pinned to the consumer's
merge commit rather than to a pull request number, because a commit is
git-tracked and immutable where a pull request page is neither. Two records of
one run, each free to drift from the other, is the duplication this repository
exists to prevent; and an issue is not a third option, being untracked by git
and outside the docs tree `tests/test_file_map.py` holds true.

## Building the shipped template

The second run this document covers, and the one still outstanding. It closes no
part of the re-adoption criterion above — that one is done — and everything
below is about a different sentence: `08-adopting.md` § Status claiming *"Exists
and has been built"* of the devcontainer template.

### Why it is owed

That row cites Phase 4's build on **2026-08-25**, and the template has changed
seven times since, four of them in `setup.sh`, which runs at container create
under `set -euo pipefail`:

| Change | Landed | Why a build is the only thing that tests it |
| --- | --- | --- |
| `chown` loop over a node glob, so `claude update` works | ADR 0035 close-out | A glob that matches nothing, or a path the feature moved |
| `git config --global --add safe.directory "$PWD"` | Phase 4 close-out | Only observable from inside a bind-mounted workspace |
| Placeholders quoted (`uv_version="{{UV_VERSION}}"`) | `53966cc`, from upstream | Taken from the promoted copy and never built here |
| `pre-commit install --hook-type pre-push`, guarded on reachability | [ADR 0039](adr/0039-a-push-is-a-locus.md) | The guard exists because the unguarded form aborted container create |

Phase 4 is the precedent for why a file test cannot stand in: *it did not build
first time*, and the three defects that exposed were all things no assert
reads. The ninth slice is the narrower precedent — it caught the quoting defect
by diffing and running an assert, which is exactly why the fix has never been
through a `devcontainer up`.

### Where to build it

**Not in the consumer.** Its `.devcontainer/` is the copy Phase 4 took, it is
that repository's adopted artefact, and replacing it would destroy the thing the
re-adoption run just verified. Use a scratch repository.

**An empty directory is not enough, and this document said it was.** Two
corrections, both taken on 2026-08-30 and both changing what the build measures:

**Take the register from `main`, not from the newest tag.** § 0.1's fetch is
right for an adopter and wrong for this build. `v0.5.0` pins **uv 0.12.5** where
`main` pins **0.12.6**, and `main`'s `setup.sh` is sixty-five lines different
from the one that tag ships. Each pair is internally consistent — a tag ships a
register and a template as one artefact — so following § 0.1 verbatim would
cross them and build the new template against the old register. Copy
`controls.yaml` out of the `ee-standard` clone the template comes from.

**Seed the repository, or two of the four changes go untested.** The claim that
the substitution *"reads the register and nothing else"* is true of the
substitution and false of the build. `setup.sh` guards the
[ADR 0039](adr/0039-a-push-is-a-locus.md) hook block on
`[ -f .pre-commit-config.yaml ]` and the frozen install on `uv.lock`, so in a
bare directory the whole block is skipped, neither hook is written, and step 3's
`ls .git/hooks/pre-push` has nothing to find. The *unreachable* arm was already
rehearsed here with stubs; the *reachable* arm — the one that writes both hook
types — has never run anywhere. So the scratch repository commits a minimal
`pyproject.toml`, a `uv.lock` carrying `pre-commit`, and a trivial
`.pre-commit-config.yaml` before the first `up`. If the host has no uv to write
the lock file, commit the other two and **record which arm ran**: an untested
arm reported as tested is the failure this phase keeps finding.

### The steps

1. **Copy and substitute**, per [`08-adopting.md`](08-adopting.md) § 2.0 —
   the four placeholders, the aarch64 checksum fetched from the release, and the
   two-source agreement check on the x86_64 one. Follow that section rather than
   anything written here; it is the guide an adopter reads and this is a
   rehearsal of it. **Its extraction commands are now executed by
   `tests/test_devcontainer_placeholders.py`** rather than only read, so a
   § 2.0 that has stopped finding a value fails the build here instead of at
   `sha256sum -c` on the host.
2. **`devcontainer up`**, and read what `setup.sh` prints rather than only its
   exit code. Three of the four changes above fail *quietly* if they fail: a
   glob matching nothing is a no-op, and the pre-commit branch is written to
   report rather than abort.
3. **Then, inside the container**: `uv --version` against the register's pin,
   `uv run python -V` against `.python-version`, `git log -1` (the
   `safe.directory` write), `ls .git/hooks/pre-commit .git/hooks/pre-push`
   (**both**, which is the ADR 0039 change), and `claude update` reaching the
   permissions fix rather than *"Insufficient permissions to install update"*.

### What has already been rehearsed, and what is left

Everything in step 1 was run in this repository's own container on 2026-08-30,
so the host is owed the build and not the preparation:

| Rehearsed | Result |
| --- | --- |
| The four placeholders, by count and location | Exactly four, in `devcontainer.json` (2) and `setup.sh` (3 lines) — § 2.0's description is accurate |
| § 2.0's `uv_block` extraction commands, verbatim | `0.12.6` and the x86_64 sha, both non-empty |
| The aarch64 checksum fetch | `d58030ac…128d`, the release endpoint answers |
| The x86_64 two-source agreement check | **Agrees** — register and vendor are the same digest |
| Substitution, then `grep -rn '{{'` | **None remaining** |
| `devcontainer.json` parses; features vs. `devcontainer-lock.json` | Valid; image digest-pinned; **3 features, 3 locked** |
| `bash -n` over all three scripts | Syntax clean |
| The ADR 0039 pre-commit branch, under `set -euo pipefail` with stubs | Both arms correct: reachable → `install --hook-type pre-commit --hook-type pre-push`; **unreachable → the note, and the script survives** |

**What none of that touches is the point of the build**: whether the nvm glob
matches a real path, whether `safe.directory` fixes a real bind mount, whether
uv actually downloads and verifies against the quoted digests, and whether
`claude update` clears the permissions error. Those are the four changes, and a
static check can only show they are well-formed.

**One build exercises one architecture**, and the record must say which.
`setup.sh` branches on `uname -m` and reaches a different placeholder and a
different digest per arm, so an Apple Silicon host verifies the aarch64 digest
and leaves the x86_64 one untested. Either arm closes the criterion; naming the
one that ran is what stops the record claiming both.

**One static finding, and it is latent rather than live.** The `chown` loop's
comment says an unmatched glob is *"a no-op rather than an error"*. It is a
no-op for control flow — measured, the script continues under `set -e` — but the
loop's exit status is `1`, because `[ -d "$d" ]` is the last thing to run in the
body. Nothing depends on that today, since statements follow it. It would become
live the moment that loop is the last statement in the file, where the same code
exits `1` and fails container create. Worth knowing before anyone reorders
`setup.sh`; not worth changing ahead of the build that is about to exercise it.

### What passing looks like

A container that creates, and all five checks in step 3 answering. There is no
`register-check` verdict to quote here: the scratch repository has no gates
deployed, so a conformance run over it would measure the scratch repository
rather than the template.

**A failure here is the most valuable result this phase can still produce**, for
the reason § What would fail the criterion gives above — it is the last place a
defect is cheaper than an adopter finding it, and unlike everything else in this
document it is testing a change that has never been executed anywhere.

The record goes where § Where the record goes says. There is no consumer
repository in this one, so the operator's half and this repository's half are
both [`15-phase-6-review.md`](15-phase-6-review.md).
