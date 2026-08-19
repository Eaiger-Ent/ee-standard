# ee-standard

The plugin that deploys the Equal Experts control standard into a repository,
and the skills that keep it deployed.

The authority is not here. It is `controls.yaml` in the
[ee-standard repository](https://github.com/Eaiger-Ent/ee-standard) — a register
entry **is** the control, and every artefact these skills write derives from it
rather than restating it. Each skill reads the register at run time; none of
them carries a pinned version, a tool name or a rule of its own.

## Skills

| Skill | Controls | State |
| --- | --- | --- |
| `gate-secrets` | SEC-001, SEC-002 | **Built** — the reference gate |
| `gate-supply-chain` | SUP-001, SUP-002, SUP-003 | Phase 2 |
| `gate-build` | BLD-001, DEV-001 | Phase 2 |
| `gate-quality` | LNT-001, TYP-001, TST-001 | Phase 2 |
| `gate-iac` | IAC-001 | Phase 2 |
| `gate-repo` | CI-001 | Phase 3 — the only gate that mutates platform state |
| `standard-adopt` | dispatcher | Phase 2 |
| `standard-check` | installs and wraps the checker | Phase 2 |
| `standard-variance` | classifies local deltas | Phase 2 |

Gates are grouped by the artefact they write, not one per control:
`gate-quality` writes one pre-commit config and one CI workflow covering three
controls, and three separate skills would fight over the same two files.

## What a gate is, and is not

A gate is a pinned binary reading a pinned config, wired at every locus the
control declares. These skills **install and wire** that binary. They are never
themselves the enforcement — nothing here runs at commit time, and a repository
whose conformance depended on a model being present would have no gate at all.

Every artefact a gate writes carries an `ee-control:` provenance stamp naming
the control, the deploying skill and version, and the register's version and
contract. The contract is what makes "deployed but stale" computable without
firing a redeployment notice on every documentation release.

## Verification

Each gate's last step runs the conformance checker against the control it just
deployed, through the same code path that audits the repository:

```bash
standard-check run --control SEC-001
```

Writing a config and confirming the config works are different claims, and only
the second is worth anything.

## Deployment contract

`.claude-plugin/deploys.json` records what this plugin writes and a
`contractVersion` that changes **only when the written output changes**. A
redeployment is recommended when the installed contract is ahead of the one
stamped in a repository, and stays silent through every release that did not
change what gets written.
