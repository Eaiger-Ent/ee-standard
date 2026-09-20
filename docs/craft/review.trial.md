# Craft — the trial

Stage **S6** of [`plan.md`](plan.md). Install on a new repository at its start,
run for a stated period, and revise against what the team reports rather than
against what the plan predicted.

**Status: agreed on 2026-09-20, not yet installed.** This document begins with
the agreement because `plan.md` § S6 asks for the period to be agreed *before*
installing, and an agreement recorded afterwards is a description of what
happened rather than a commitment anyone was held to.

## What was agreed

| | |
| --- | --- |
| The repository | `anonymise-transcripts` — private, owned by this workstream's author, outside the `Eaiger-Ent` organisation |
| Its state at agreement | **One commit, zero files.** `Initial commit`, empty |
| The stack | Not yet declared. The first real commit decides it |
| The sequence | The owner's skeleton first, then the control register, then Craft |
| The period | **Two weeks from the Craft install**, not from this agreement |
| What is reviewed | S3's criteria as they hold in use, and what the person working in it reports |

**The repository is named and its owner is not.** This repository is public and
that one is private; the name is what makes the record checkable by anyone who
has access, and the handle would add nothing but reach.

## The sequence, and why this order

**The skeleton is the owner's.** A project's shape is not Craft's to invent, and
a profile that met a repository this workstream had built for it would be
measuring its own assumptions — which is the objection S3's rewrite already made
once.

**The control register comes before Craft.** A Craft profile writes rule
selection into the configuration LNT-001's gate wires at editor, pre-commit and
CI. Installed with no gate, the selection is a file that is read when somebody
runs the linter by hand, which is not the thing the two weeks are supposed to
measure. So the register is deployed first and the profile is felt the way the
design assumes it is felt: at a commit that does not complete.

**Two weeks starts at the Craft install.** Long enough for the profile to be met
in ordinary work several times over; short enough that what somebody felt is
still remembered rather than reconstructed when they are asked.

## What has already been observed, before installing anything

Two things, and both are evidence rather than preamble.

**`craft-install` would refuse this repository, correctly.** Neither predicate
holds on an empty repository — no `pyproject.toml`, no `package.json` declaring
react — so no profile applies, and the skill's rule is to name the condition that
was false rather than to report that nothing happened. The first thing the
installer meets in the wild is the case where it does nothing, which is a case
`docs/craft/build.installer.md` § How the stack is inferred wrote a table row for
and had never run.

**The trial crosses an access boundary this workstream has not crossed before.**
Every install so far has been into a scaffold in this container. This one is a
repository the standard's own tooling cannot reach: the ambient token is scoped
to `Eaiger-Ent`, so it can neither read nor push there. Three consequences,
recorded now because each will shape what the trial can say:

- **Every push is the owner's.** Work is prepared in a local clone and pushed by
  somebody with access, so nothing here is a claim about what CI did unless the
  owner reports it.
- **CI-001 is platform state.** `gate-repo` applies a default-branch ruleset
  through the GitHub API, and that call has to be made by an account with admin
  on the repository. It is the one part of the adoption this container cannot
  perform at all.
- **What the trial reports is second-hand.** That is the ordinary condition of a
  trial with a team in it, and it is worth naming before the report arrives
  rather than when it disagrees with a measurement taken here.

## What the owner needs to do first

The repository needs a stack before Craft has anything to install. Minimally, a
first real commit carrying:

- **`pyproject.toml`** with `[project]`, a `name`, a `version` and a
  `requires-python`. That file existing *is* the `python` predicate — the control
  register's, reused rather than re-spelled.
- **A source directory and a test directory**, however small. TYP-001's coverage
  key and the profile's source scope both read the layout, and a repository with
  nothing in `src/` is one where the scope cannot be seen to work.
- **A lockfile**, once there are dependencies. LNT-001 and TYP-001 require their
  tools to be reached through it, so `uv lock` is what makes the gates
  installable rather than aspirational.

**And one thing to leave out.** Do not add a `ruff.toml` or a `.ruff.toml`
beside the `pyproject.toml`, and do not write a `[tool.ruff.lint] select` by
hand. Both make the installer stop: ruff reads the *nearest* configuration file
where the register lists the checker's search order, so a sibling `ruff.toml`
silently replaces the section a profile writes. That refusal exists because the
first trial run, on a scaffold, installed a profile that applied to `src/` and
not to `tests/` and reported success —
[`build.installer.md`](build.installer.md) § The first run of the installer.

**This is also the trial's first prediction.** If the skeleton arrives with one
of those files in it, the installer should refuse and say why. Whether it does is
a result, and it is written down here before the skeleton exists so that it
cannot be rewritten afterwards.

## What this document owes

| Owed | When |
| --- | --- |
| The install record: what was inferred, what was presented, what was chosen, what was written | At the install |
| The repository's size and shape at install, so the finding counts mean something | At the install |
| What the two weeks produced — findings met, rules fought, anything switched off | At the review |
| S3's criteria as they hold in use, or the gap recorded | At the review |
| A profile revision, or the reason there is none | At the review |
