# ADR 0036: Prose Several Skills Must Follow Is Shipped Once and Read at Runtime

**Status:** Accepted
**Date:** 2026-08-26
**Revision:** 1

## Background

Two of Phase 4's findings were closed by writing a section into every skill it
applied to. Finding 19 — *every write arrived as a diff with no reason attached*
— added a *Say what each write is for* section to the six gates and to
`register-install`, seven copies. Finding 24 — *nothing ran the pre-commit hooks,
and every gate said the locus was wired* — added a *Before you write a pre-commit
hook, make sure something runs it* section to the five gates that write into
`.pre-commit-config.yaml`.

Both sections are normative: they tell the skill what to do, not what to know.
Both were correct. Both were pasted, byte for byte, into every skill they
governed — twelve copies of two rules, in a repository whose stated purpose is
that a rule has one home and everything else derives from it.

Nothing objected, because nothing was looking. `tests/test_plugin.py` forbids a
skill repeating a **version the register pins**; it says nothing about a skill
repeating a paragraph another skill also carries. So the copies were invisible
until they were measured by accident.

**What measured them was the line ceiling.** Re-running skill-preflight P1–P11
over all eight skills on 2026-08-26 — the re-run Phase 4 owed the Phase 2
criterion it re-opened — returned one failure:

```text
"skill": "gate-quality", "overall": "FAIL", "fails": 1,
"P1_line_count": {"status": "FAIL", "value": 510, "limit": 500}
```

`gate-quality` had gone 454 → 478 → 510 lines across the two changes, and 56 of
those 510 lines were the two pasted blocks. It is the longest skill because it
deploys three controls; it was the first over the line, and on the trajectory
those two changes set it would not have been the last.

So the failure is a line count and the defect is a duplication. Fixing the count
by editing `gate-quality`'s own prose down would have left eleven copies
standing and bought four lines of headroom.

## Alternatives Considered

**Trim each skill's prose until it fits.** Cheapest, and it treats the symptom.
The gate-specific prose in these skills is dense and load-bearing — every
paragraph names a control, a register key or a failure it exists to prevent — so
the lines that would go are the explanatory ones, and the next paragraph anyone
adds to five gates puts the count back.

**Let each skill keep its copy and add a test that they stay identical.** This
is the shape of a lock file: duplication tolerated because something checks it.
It fails on what the check cannot see — a test can compare seven blocks and
cannot notice that the eighth skill, added later, needed the rule and did not get
it. It also leaves the line ceiling exactly where it was.

**Put the prose in each skill's `README.md`.** A skill's README is documentation
for a person choosing the skill; `SKILL.md` is the instruction the model follows.
Moving a normative step into the README moves it out of the run.

## Decision

**Prose that more than one skill in this plugin must follow is shipped once,
under `plugins/control-register/reference/`, and read at runtime through
`${CLAUDE_PLUGIN_ROOT}`.**

Two files exist today: `pre-commit-runner.md` and `write-narration.md`. Each
skill that the rule governs carries a short pointer section in its `SKILL.md` —
the instruction to read the file, one sentence of what it is for, and the reason
it lives elsewhere — and nothing more.

`${CLAUDE_PLUGIN_ROOT}` rather than `${CLAUDE_SKILL_DIR}`: the variable expands
to the plugin's installed directory in the layout an adopter installs, which is
the layout that matters, and skill-preflight's P8 resolves it, so a pointer to a
file that does not exist is a preflight failure rather than a runtime one. The
skills already read files at runtime — every gate reads its own templates the
same way — so this adds no mechanism they did not have.

**The runtime read is the point, not a compromise.** A pointer that only
described the rule would be a thirteenth copy in summary form. The skill is told
to read the file and follow it, exactly as it is told to read a template and
substitute it.

**A pointer names the fallback.** In this repository the plugin is not installed
as a plugin — the skills are reachable through the `.claude/skills/<name>`
symlinks [ADR 0033](0033-the-submission-tool-reaches-the-skills-by-symlink.md)
created — so `${CLAUDE_PLUGIN_ROOT}` may be unset here. Each pointer says where
the file is in that case. That is one clause per pointer, and it is a fact about
how the skill was reached rather than a restatement of the rule.

## Consequences

`gate-quality` is 477 lines and every skill passes P1–P11 with zero failures,
which closes the Phase 2 criterion Phase 4 re-opened. Every other skill dropped
between 12 and 35 lines, so the headroom is the fix's, not a trim's.

**A rule now has one place to change.** The next amendment to either section is
one edit, and every skill that reads it gets it. The eighth skill, and the ninth,
get it by writing one pointer rather than by remembering there was something to
paste.

**The cost is a read the model has to make.** A skill that ignores its own
pointer skips a normative step, and nothing at runtime will say so — the same
exposure every `${CLAUDE_SKILL_DIR}/templates/…` read already carries, and the
reason the pointer is an imperative sentence in bold rather than a cross
reference.

**`tests/test_shared_reference.py` holds both directions.** A referenced file
that does not exist fails, and so does a skill that re-inlines a shared section
instead of pointing at it — the failure this ADR exists to prevent, which is the
one a test comparing copies could not have seen.

**No gate's `contractVersion` moves, and the register's contract does not
either.** Nothing this changes reaches a deployed artefact: no template changed,
no control's `rung`, `verify`, `variance` or `applies_to` changed, and the two
rules say what they said yesterday from a different file. A bump would recommend
redeploying six gates for a change no repository can observe, which is the noise
the per-gate shape exists to prevent.

**The reference files ship in the plugin and cite ADR 0036 in prose, not by
link.** `docs/` is not shipped, so a relative link out of the plugin would
resolve in this repository and dangle in every installation of it.

## Related ADRs

- [ADR 0033](0033-the-submission-tool-reaches-the-skills-by-symlink.md) — the
  symlinks that make `${CLAUDE_PLUGIN_ROOT}` unset in this repository
- [ADR 0026](0026-an-adr-stands-on-its-own.md) — why the rationale for these two
  rules stays in `docs/12-phase-4-review.md` § 19 and § 24, and is not retold in
  the reference files

## References

- [`docs/12-phase-4-review.md`](../12-phase-4-review.md) § 19 and § 24 — the two
  findings whose fixes were pasted
- [`docs/02-skill-family.md`](../02-skill-family.md) — the skill shape this
  extends
