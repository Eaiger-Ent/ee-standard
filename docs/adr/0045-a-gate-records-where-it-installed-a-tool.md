# ADR 0045: A Gate Records Where It Installed a Tool

**Status:** Accepted
**Date:** 2026-08-30
**Revision:** 1

## Background

`tools.<tool>.pinned_at` is the list of files that repeat a tool's version, and
it is what makes the register's pins checkable. Two asserts read it:
`tool_versions_match_register` (SUP-001) compares the version at every listed
site, and `tool_digests_match_register` (SUP-004) does the same for digests and
additionally reports a digest found *inside* a listed site that the register
does not name.

Both iterate the declared list and nothing else:

```python
for tool in literal:
    for path in tool.pinned_at:
```

```python
files = sorted({path for tool in register.tools.values() for path in tool.pinned_at})
```

**So a file that installs a register-pinned tool and is not in `pinned_at` is
compared by nothing, in either direction, and reports no verdict.** The list is
an allow-list, and what an allow-list leaves out is invisible — the argument
[ADR 0019](0019-exemptions-cannot-hide-tracked-files.md) makes about exemptions,
one level up. `docs/14-file-map.md` earned a test in both directions for exactly
this property; `pinned_at` has one direction.

For this repository the gap is nearly harmless, because the register and the
files were written together by the same hand on the same day. For an adopter it
is live, and the reason is that **the standard asks them to close it manually.**
`gate-secrets` writes an install block into their gating workflow, and the
template it writes from carries this instruction as a comment:

```text
The version appears twice in the repository once this is written — here and in
the developer environment — which is why the register records those sites in
`tools.{{TOOL}}.pinned_at` and `tool_versions_match_register` fails the build
when one drifts. Add this workflow's path there if it is not already listed.
```

An adopter's gating workflow is not named `register-check.yml`, so the path
almost never *is* already listed. The instruction is a comment inside a file the
gate generates — not a step the gate performs, not a prompt the adopter answers,
and not a line the deployment narration reads out. Missing it costs them a
gitleaks pin that drifts uncompared while SUP-001 and SUP-004 both report PASS.

This was found by
[`17-adopter-onboarding-review.md`](../17-adopter-onboarding-review.md) § K,
reviewing the adopter surface for a reader who has never seen this repository.

## Decision

**A deploying gate writes `tools.<tool>.pinned_at` in the register, for a tool it
has just installed at a path not already listed.** The manual instruction is
removed from `gate-secrets`' CI-steps template, because a step that is now
performed must not also be requested.

Three constraints make it safe, and all three are load-bearing:

**1. Additive only.** A gate may add a path. It may never remove one. Adding a
path can only increase what is compared, which is the `narrowing-only` direction
every one of these controls already declares; removing one is the loosening a
gate must never be able to perform on its own.

**2. That field only.** A gate may write `pinned_at` and no other part of the
register. Not `rung`, not `verify`, not `variance`, not `applies_to`, not
`tier`, not a tool's `version` or `sha256`. Those define what conformant means;
`pinned_at` records where this repository happens to keep a file.

**3. Only for a path it wrote.** The path comes from the artefact the gate has
just written, in the same step. A gate never surveys the repository for files
that might install its tool.

## Why this does not breach the register boundary

The stated boundary is that a gate writes artefacts and the register is what it
reads, and this is the first exception to it. It holds because of what
`pinned_at` is.

**The register holds two kinds of thing, and only one of them is policy.**
`rung`, `verify`, `variance`, `applies_to` and `tier` decide what conformant
means: two repositories that differ on them are conformant to different
standards. `pinned_at` is not of that kind. It is a repository-local fact about
where files live — two conformant repositories legitimately hold different
values, and neither is more conformant than the other. A gate computing it is a
gate recording what it did, not a gate deciding what the rule is.

**The safety test is whether a wrong write can weaken a control.** It cannot.
Under constraint 1 the only reachable error is an *extra* path, which makes the
checker compare a file it need not — a false failure, loud and immediately
diagnosable, never a false pass. The failure mode this replaces is the opposite
and is the one that matters: silence that reads as agreement.

**It does not become a general licence.** The three constraints are the whole
permission. A later gate wanting to write some other field is a new decision and
a new ADR, and the narrowness is the point — this ADR exists because one field
had a manual step that reliably failed, not because gates should own the
register.

## No provenance stamp is written for this

A stamp names a control and the gate that deployed an artefact for it, and the
register is not a deployed artefact — it is the thing artefacts derive from.
Stamping `controls.yaml` would claim the register as `gate-secrets`' output,
which is the inversion this whole repository is arranged against. The write is
recorded the way any other reviewable change is: the gate names it in its
narration before making it, and it appears in the diff of the commit the
adoption produces.

This matches [ADR 0032](0032-the-checker-is-installed-from-a-tagged-ref.md)'s
reasoning for `register-install` writing no stamp — a stamp needs a control to
name, and there is none for *the register records where a tool was installed*.

## Alternatives considered

**The checker scans for strays.** Have `tool_digests_match_register`'s stray
direction extended to the whole repository: find files that install a
register-pinned tool and are absent from `pinned_at`, and fail them. Rejected
because it requires a heuristic for *installs this tool*, and a heuristic
false-positives — a changelog quoting `gitleaks 8.30.1`, a review document
naming a version, this ADR itself. A false failure on a Tier-1 `blocking`
control is expensive, and the alternative here needs no heuristic at all: the
gate knows precisely which file it just wrote. This is not closed by the present
decision, only made much less urgent; if it is taken later it will be as a
second, independent check rather than as a replacement for this one.

**Prompt the adopter instead of writing.** Have the gate ask *"add
`.github/workflows/ci.yml` to `tools.gitleaks.pinned_at`?"* and let them do it.
Rejected: it is the current design with a better user interface. The failure is
not that adopters refuse, it is that a manual step in the middle of a long
deployment is skipped, and a prompt at that moment is one more thing to accept
without reading.

**Leave the comment.** Rejected. It is the status quo, and the status quo is
what produced the finding — an instruction placed where the reader is least
likely to be looking, protecting a check that silently does nothing when it is
missed.

## Consequences

`gate-secrets` gains a register write and therefore a new deployment contract:
`gates.gate-secrets.contractVersion` moves from 6, and under
[ADR 0038](0038-the-stamp-records-the-deployment-contract.md) every existing
`gate-secrets` stamp then reads stale until the gate is re-run. That is the
staleness machinery working rather than a cost to avoid, and it is reported and
never enforced.

The adopter loses a step that could fail silently. That is the whole benefit,
and it is worth naming that it is *only* about SEC-001's tool today, because
`gate-secrets` is the gate whose template carried the instruction. Any other
gate that installs a register-pinned tool into a file of the adopter's naming
inherits the same permission and the same three constraints.

**A gate must not reformat the register.** It appends a path to one list. This
is the rule `gate-supply-chain` already follows for `.github/dependabot.yml` —
*"add only the missing entries, do not reformat the file, a wholesale rewrite
makes this gate's change unreviewable"* — and it matters more here, because the
register is the file every other verdict is computed from.

**A register that cannot be written is reported, not worked around.** If the
register is read-only, or is a shared file the repository does not own, the gate
says so and names the path it would have added. It does not fall back to the
comment, because a fallback nobody sees is what this ADR removes.

§ K of the review remains open in one respect, deliberately: a file that
installs a pinned tool and was written by a *human* rather than by a gate is
still invisible to the allow-list. This decision closes the path that the
standard itself creates, which is the one it is responsible for.
