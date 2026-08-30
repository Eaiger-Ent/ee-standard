# Re-adopting from the marketplace

The runbook for Phase 6's last exit criterion — *the consumer repo re-adopts
from the marketplace copy and still passes*. It is written for an operator on a
host this container is not, so it states what that host must have and what each
step is expected to produce, and it **does not restate the adoption steps
themselves**: those live in [`08-adopting.md`](08-adopting.md) and a second copy
of them here would be free to drift from the guide an adopter actually follows.

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
claude plugin marketplace add Eaiger-Ent/ee-standard
claude plugin install control-register@ee-standard --scope user
# and, with an ee-skills credential:
claude plugin install control-register@ee-skills --scope user
diff -rq ~/.claude/plugins/cache/ee-standard/control-register/*/ \
         ~/.claude/plugins/cache/ee-skills/control-register/*/ --exclude='.in_use'
```

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
