# ADR 0043: A Declination Is Reconciled Against the Installed Skill

**Status:** Accepted
**Date:** 2026-08-28
**Revision:** 1

## Background

[ADR 0042](0042-a-deploying-skill-reads-local-configuration.md) revision 2 gave
`deployment-decisions.yaml` two rules, and said plainly why each one is what
makes the file a record rather than an opt-out:

> `version` names the release being declined, and covers **that release only**.
> A later one re-opens the question, which is the whole point — a declination
> that covered every future version would be a permanent exemption wearing a
> reason.
>
> `review_by` expires it.

Only the second was implemented. `decision_problems` fails an expired entry, an
entry naming a skill nothing here stamps, and an entry for a release the
repository has already **deployed** — that last one comparing the declined
version against the stamp. Nothing compared it against the release that is
**installed**, which is the comparison the first rule is about.

The gap was measured on 2026-08-28. `lint-md` was updated 1.0.7 → 1.0.8; the
declination named 1.0.7; `register-check deployments` exited `0` with the entry
listed as live, and printed underneath it, verbatim:

```text
A declination covers the version it names and no later one: a new release
re-opens the question.
```

The report stated the rule and did not apply it. That is worse than not stating
it: the sentence reads as a check that has been made. A declination is the one
record in this repository that says *do not take this release*, and it had gone
quiet about the release it was no longer speaking for — silently, with no line
to read and no diff on the day it stopped being true, which is the same failure
[ADR 0019](0019-exemptions-cannot-hide-tracked-files.md) describes about
exemptions and `tests/test_file_map.py` describes about the map.

## Decision

**We will reconcile a declination against the skill version that is installed,
not only against the version that is stamped.**

An entry whose skill is installed at a version strictly later than the one it
names has stopped covering that skill, and is reported as a record that has
stopped describing reality — the same class as an expired entry, and the same
exit code.

Three parts.

**1. Where "installed" comes from.** The Claude Code plugin inventory,
`plugins/installed_plugins.json` under `$CLAUDE_CONFIG_DIR`, defaulting to
`~/.claude`. It is read directly rather than through the `claude` CLI: a checker
that shelled out to `claude plugin list` would need the CLI on `PATH` to answer
a question about a JSON file, and would fail in every environment that has the
file and not the binary.

A skill installed at more than one scope contributes the **highest** version it
is installed at. The question is whether any installed copy is later than the
record's, and a record that covered the older of two installations while a newer
one sat beside it would be covering the copy that is not going to run.

**2. Absence is not agreement.** Three things are reported as *not known* rather
than as *not superseded*: no inventory file, no entry for that skill, and a
version either side of the comparison that does not parse. The report says which
of those it hit, and the run's exit code is unaffected.

This is the same discipline as `kind: remote`'s `UNCLASSIFIED`
([ADR 0021](0021-how-remote-verification-authenticates.md)): reading the absence
of an answer as an answer reports a state produced by not having looked. It
matters here because the environments differ — a developer's container has the
inventory and CI has no plugins installed at all, so a rule that treated "not
found" as "still covered" would be right locally and wrong nowhere it could be
noticed.

**3. The inventory path may live in the checker.** [ADR 0018](0018-register-checker-boundary.md)'s
question is whether a reasonable Equal Experts repository could need this to
differ without changing the checker. It could not: where Claude Code keeps its
plugin inventory is a property of the harness, identical in every repository
that has one, and the one axis on which it does vary — `CLAUDE_CONFIG_DIR` — is
already the harness's own environment variable rather than a register value.
Putting the path in `controls.yaml` would make every adopter restate a constant.

## Alternatives considered

**Record the installed version in the entry.** Add an `installed_at_record_time`
field and fail when it disagrees. Rejected: it is a second copy of a number the
machine can read, it goes stale in exactly the way the record is supposed to
catch, and it asks the author of a declination to write down something that was
true for as long as it took to save the file.

**Compare against the marketplace latest.** Rejected for
[SUP-004](0041-a-pinned-digest-is-checked-against-what-was-published.md)'s
reason, in the other direction: a repository would be told its record was stale
because somebody else cut a release, before anyone here had installed it. The
question a declination answers is what *this machine* would run if the skill
were re-run, and that is the installed version.

**Fail the conformance run.** Rejected. `deployments` is not part of a
conformance run and this does not change that. A record that has stopped
describing reality is worth an exit code on the command that reads the record —
it already is one for an expired entry — and is not worth blocking a merge over,
because the fix is a decision somebody makes rather than an edit anybody can
make correctly under time pressure.

## Consequences

The verdict is now environment-dependent, which no other part of this command
is. A run in a container with the plugin installed can report a stale record
that the same commit in CI cannot. That is accepted and is why part 2 is written
the way it is: the report names the reason it could not look, so the two runs
disagree visibly rather than silently.

`register-check deployments` gains an exit-`1` case that fires on the state this
repository is in as this ADR is written — `lint-md` installed at 1.0.8 against a
declination naming 1.0.7 — and it should. The record needs deleting, which is
what taking the 1.0.8 deployment does.

The residual risk is that a repository with no Claude Code installation never
exercises the check at all, so a declination there expires (rule 2) rather than
being superseded (rule 1). Rule 2 still bounds it; rule 1 is what makes the
bound shorter when the machine can see further.
