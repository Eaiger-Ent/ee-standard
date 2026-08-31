# control-register

**What you get.** Fifteen security and quality properties that actually hold in
your repository, and one command that proves which ones do — secrets that cannot
reach the remote, dependencies installed frozen and updated by proposal, lint and
types and tests blocking at every locus, and a default branch whose protection is
verified against what GitHub *actually enforces* rather than what a file claims.

**Why not a policy document.** A lint workflow can exist, be believed in, and not
be a required check — and nothing about the repository on disk reveals it. Here
one file is the control and everything else derives from it, so the chain from a
rule to a blocked merge is read end to end.

**Start here:**
<https://github.com/Eaiger-Ent/ee-standard/blob/main/START-HERE.md> — what to
install, which credentials you need, and six steps. It is an absolute link on
purpose: `docs/` does not ship inside this plugin, so a relative one would
resolve only in the repository that authors the standard.

## Where the authority lives

Not here. It is `controls.yaml` in the
[ee-standard repository](https://github.com/Eaiger-Ent/ee-standard) — a register
entry **is** the control, and every artefact these skills write derives from it
rather than restating it. Each skill reads the register at run time; none of
them carries a pinned version, a tool name or a rule of its own.

## Skills

| Skill | Controls | State |
| --- | --- | --- |
| `gate-secrets` | SEC-001, SEC-002, SEC-003 | **Built** — the reference gate |
| `gate-quality` | LNT-001, TYP-001, TST-001 | **Built** — three controls, two shared files |
| `gate-supply-chain` | SUP-001, SUP-002, SUP-003 | **Built** — found the locus nothing had ever read |
| `gate-build` | BLD-001, DEV-001 | **Built** — owns `.devcontainer/`, which other gates write into |
| `gate-iac` | IAC-001 | **Built** — the only gate whose controls may legitimately not apply |
| `gate-repo` | CI-001 | **Built** — the only gate whose effect is not a file. Records the ruleset, then applies it |
| `register-adopt` | dispatcher | **Built** — the front door. Writes no gate configuration of its own |
| `register-install` | none — it installs the checker | **Built** — dispatched by `register-adopt` before its own pre-flight ([ADR 0032](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0032-the-checker-is-installed-from-a-tagged-ref.md)) |
| `register-variance` | classifies local deltas | **Built** — reports a direction, and says why when it declines to |

All nine are built. `register-install` deploys no control and therefore writes no
provenance stamp: a stamp names a control, and none says *the checker is
installed*. It is listed because everything else here needs it — every gate
verifies itself with `register-check`, so a plan computed without it is computed
without its instrument.

Gates are grouped by the artefact they write, not one per control:
`gate-quality` writes one pre-commit config and one CI workflow covering three
controls, and three separate skills would fight over the same two files. The
grouping is a register fact, not a convention held here — all three controls
carry `deployed_by: gate-quality`, and a test fails a sidecar that disagrees.

## What a gate is, and is not

A gate is a pinned binary reading a pinned config, wired at every locus the
control declares. These skills **install and wire** that binary. They are never
themselves the enforcement — nothing here runs at commit time, and a repository
whose conformance depended on a model being present would have no gate at all.

Every artefact a gate writes carries an `ee-control:` provenance stamp naming
the control, the deploying skill and version, the gate's deployment contract,
and the register's version and contract. The two contracts are what make
"deployed but stale" computable without firing a redeployment notice on every
documentation release.

## Verification

Each gate's last step runs the conformance checker against the control it just
deployed, through the same code path that audits the repository:

```bash
uv run register-check run --control SEC-001
uv run register-check run --control LNT-001 --control TYP-001 --control TST-001
```

`uv run`, never a bare `register-check`: a bare name resolves against `PATH` and
would report success against some other copy entirely
([ADR 0020](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0020-a-locus-reaches-the-pinned-artefact.md)).

Writing a config and confirming the config works are different claims, and only
the second is worth anything.

## Deployment contract

`.claude-plugin/deploys.json` records what each gate writes and a
`contractVersion` **per gate** that changes only when that gate's output
changes. A redeployment is recommended when a gate's installed contract is ahead
of the one stamped in a repository, and stays silent through every release that
did not change what that gate writes.

`register-check deployments` is the reader. It exits `0` over any number of
stale or undeployed gates — staleness is reported, never enforced — and non-zero
only for a stamp claiming a contract the installed gate has not reached.

Per gate, rather than per plugin, because six gates ship here: one shared number
would recommend redeploying `gate-secrets` every time `gate-quality`'s output
moved, which is the noise the mechanism exists to avoid.
