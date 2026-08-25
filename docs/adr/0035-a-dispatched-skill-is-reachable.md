# ADR 0035: A Dispatched Skill Is Reachable; Only the Front Door Is Not

**Status:** Accepted
**Date:** 2026-08-25
**Revision:** 1

## Background

Phase 4 ran `/register-adopt` in a repository that did not author the standard,
which is the first time anything had. It stopped at Step 0:

```text
Skill control-register:register-install cannot be used with Skill tool due to
disable-model-invocation. Ask the user to run /control-register:register-install
yourself — it cannot be invoked via the Skill tool.
```

All eight skills in the plugin carried `disable-model-invocation: true`.
`register-adopt` exists to dispatch seven of them, and carries `Skill` in its
`allowed-tools` to do it. So the documented front door — *"the only entry point
you need"* — has never been able to take its first step, and neither could it
have taken any later one: the six gates are dispatched the same way.

**Why nothing caught it.** Two things had to line up.

`tests/test_register_adopt.py` drives every gate in the skill's own dispatch
order, and it passes. It drives them in Python, through their shipped templates,
which is the pipeline rather than the dispatch — a limit
[`10-phase-2-review.md`](../10-phase-2-review.md) § What is proved, and what is
not states plainly: *what is proved is that the pipeline works, not that a model
follows the prose*. Phase 4 has now found what that limit was hiding.

And the preflight that should have said so reported a pass. P9 is exactly this
check — *"a called skill has `disable-model-invocation: true` and cannot be
invoked via the Skill tool"* — with exactly this fix:

> remove `disable-model-invocation: true` from the called skill's `SKILL.md` and
> add a note to its `README.md` explaining which skill(s) invoke it.

`register-adopt`'s recorded run reads `{"skill": "register-adopt", "overall":
"PASS", "fails": 0}`. The dispatch targets are named in prose — `/gate-secrets`,
`/gate-quality` — and not in any field a checker resolves, so P9 saw a skill with
`Skill` in `allowed-tools` and no callee it could name. **The criterion was
ticked on a check that could not see the defect**, which is the shape this
repository has now re-opened eight boxes over.

## Decision

**`register-adopt` keeps `disable-model-invocation: true`. The six gates and
`register-install` drop it, and each says in its `README.md` that it is
dispatched and why the flag must not come back.**

The flag's purpose is to stop a model deciding, on its own initiative, to deploy
a gate or change platform state. That purpose is served entirely by the entry
point: a chain that begins at `/register-adopt` is one an operator started, and
`register-adopt` is the skill a model still cannot invoke for itself. Keeping the
flag on the callees does not add a second guard — it removes the first, because
a front door that cannot open is one every operator routes around by running
seven skills by hand, unplanned and in whatever order they guess.

**What guards the platform mutations is not this flag, and never was.**
`gate-repo` asks its own question before each `gh api` call that changes state,
independently of the plan-level confirmation, and
`tests/test_gate_repo_confirmation.py` enumerates them: every non-`GET` call in
the skill must appear in the skill's own table with a question standing between
it and the call before it, so a fourth mutation fails the build until it has
both. That was Phase 3's tenth slice, and it is the control that matters here —
a confirmation the operator sees, rather than a frontmatter key that makes the
skill unreachable.

## Consequences

The front door works, which is the point.

**Seven skills become model-invocable, and that is a real widening.** A model may
now reach `/gate-secrets` or `/gate-repo` without an operator naming it. The
mitigation is the one above for the only gate that touches anything outside the
repository; the other five write files into a working tree, where a diff is the
review. This is a smaller widening than it looks and a larger one than none, and
it is stated rather than filed under an implementation detail.

**[ADR 0033](0033-the-submission-tool-reaches-the-skills-by-symlink.md) has a
sentence that is now false.** It records the symlinks as safe *because* all
eight carry the flag, so they are "available to a person and never to a model
choosing for itself". The symlink decision is untouched and correct; the safety
sentence describes a state that no longer holds for seven of the eight. It is
amended in place, as a numbered revision, per
[ADR 0025](0025-an-amendment-is-a-recorded-revision.md) — the decision is
unchanged and only the record has become factually false, which is the one case
[ADR 0026](0026-an-adr-stands-on-its-own.md) permits.

**Preflight P4 will now warn on seven skills** — side-effect verbs in the
description without the flag. That warning is correct as a default and wrong
here, and the answer is the one P9 already prescribes rather than a suppression:
the `README.md` note naming the dispatcher. Phase 2's criterion *"every SKILL.md
passes preflight P1–P11"* is re-opened rather than quietly re-read, because it
was ticked over a P9 that could not resolve a prose dispatch.

**What is still not proved is that a model follows the prose.** This ADR removes
the thing that made the dispatch impossible; it does not demonstrate that the
seven steps are followed correctly once possible. Phase 4's own run is that
evidence, and it is recorded in
[`12-phase-4-review.md`](../12-phase-4-review.md) rather than asserted here.
