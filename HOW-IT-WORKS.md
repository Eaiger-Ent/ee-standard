# How it works

The mechanism, for someone deciding whether to adopt this or trying to
understand a verdict it produced. Not a reference — every term it uses is
defined in [`docs/00-concepts.md`](docs/00-concepts.md), and it links there
rather than restating, so the two cannot drift.

Adopting it instead? [`START-HERE.md`](START-HERE.md).

## The one idea

**A register entry is the control, not documentation of one.**

`controls.yaml` holds fifteen entries. Each names a property — *a commit
containing a secret cannot reach the remote* — and everything that enforces that
property is generated from the entry rather than written beside it. The CI
workflow, the pre-commit hook, the editor setting, the devcontainer, the
branch-protection ruleset: all derived, none independent.

That inverts the usual arrangement, where a policy document says one thing and
CI does another and nothing compares them. Here there is one definition and a
checker that reads the whole chain.

## What an entry contains

Five fields carry the weight. [`docs/01-register-schema.md`](docs/01-register-schema.md)
is the field-by-field specification.

- **`enforces`** — the property, in a sentence.
- **`rung`** — how hard it bites: `advisory`, `warn`, `blocking`, or
  `blocking (baselined)`. Moving up a rung is an explicit recorded decision.
- **`locus`** — *where* it runs: `editor`, `pre-commit`, `pre-push`, `ci`,
  `remote`. A control declaring three loci must be wired at all three, with the
  same pinned tool version at each.
- **`applies_to`** — a predicate, evaluated against the repository's files. A
  repository with no Terraform skips the Terraform control; it cannot *declare*
  its way out of one.
- **`verify`** — the blocks that decide the verdict. `command` runs an external
  tool and reads its exit code, `file` asserts over repository files, `remote`
  reads platform API state.

## What actually blocks a merge

Three things have to line up, and the interesting failure is when two of them do.

1. A control is `blocking` and declares the `ci` locus.
2. A CI job runs its verification and can fail.
3. The platform enforces that job as a **required status check** on the default
   branch.

Miss the third and you have a lint workflow that exists, is believed in, runs on
every pull request, goes red — and blocks nothing. Nothing about the repository
on disk reveals it. That is the failure this standard was built around, and it
is why `GOV-001` reads what GitHub *actually enforces* through the API and fails
a check the register requires and the platform does not.

## Who does what

**A skill deploys. It never enforces.**

The gates — `gate-secrets`, `gate-quality`, `gate-supply-chain`, `gate-build`,
`gate-iac`, `gate-repo` — are Claude skills that read the register and write the
artefacts: hooks, workflow steps, configs, a ruleset. `register-adopt` dispatches
them in dependency order.

What runs at commit time is a pinned binary reading a pinned config. There is no
model in CI, and a repository whose conformance depended on one would have no
gate at all. A skill can install a gate, explain it, and propose a fix; it cannot
be one.

## How drift becomes visible

Every artefact a gate writes carries an `ee-control:` provenance stamp naming the
control, the gate, the gate's deployment contract, and the register version. So
*never deployed*, *deployed and current*, and *deployed and stale* are three
computable states rather than three things somebody has to remember.
`register-check deployments` reads them.

Staleness is **reported, never enforced** — a stale gate exits `0`. What fails is
a stamp claiming a contract ahead of the installed gate, or a record that has
stopped describing reality.

## Reading a verdict

Exit codes are the whole vocabulary
([ADR 0016](docs/adr/0016-exit-codes-for-unverifiable-controls.md)):

| Code | Meaning |
| --- | --- |
| `0` | Every applicable control was verified and holds |
| `1` | A verified violation |
| `3` | No violation found, but something could not be verified |

`3` is the one that matters. A control whose tool is absent, or whose remote
block has no credential, is `UNCLASSIFIED` — never a pass. `--require-complete`
promotes `3` to `1`, which is how CI refuses to accept "I could not check".

A locally-run `uv run register-check` exits `3` here and in any adopting
repository, because some remote blocks answer only inside a GitHub Actions job.
That is the honest report rather than a regression.

## What it costs

A Mac with Docker, admin on the repository, and a plan where rulesets are
available — public, or paid. All development happens inside the devcontainer,
and everything runs through `uv`: the pinned interpreter, the pinned tools, the
same versions at every locus.

## Where to go next

| You want | Read |
| --- | --- |
| To adopt this | [`START-HERE.md`](START-HERE.md) |
| The vocabulary, precisely | [`docs/00-concepts.md`](docs/00-concepts.md) |
| The register's field specification | [`docs/01-register-schema.md`](docs/01-register-schema.md) |
| The full adoption reference | [`docs/08-adopting.md`](docs/08-adopting.md) |
| Which file holds what | [`docs/14-file-map.md`](docs/14-file-map.md) |
| Why a decision was taken | [`docs/adr/`](docs/adr/) — one per control, plus the cross-cutting ones |
