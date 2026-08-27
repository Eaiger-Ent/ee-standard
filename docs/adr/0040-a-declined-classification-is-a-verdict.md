# ADR 0040: A Declined Variance Classification Is a Verdict

**Status:** Accepted
**Date:** 2026-08-27
**Revision:** 1

## Background

`00-concepts.md` § Variance has promised since Phase 0 that a `narrowing-only`
control's local delta has a **direction**: *"adding a lint rule strengthens,
raising a coverage floor strengthens, excluding authored content weakens."*
`01-register-schema.md` § `variance` goes further and says the checker
*"classifies the delta's direction and fails on any weakening"*, and names three
cases where classification fails and the answer is `UNCLASSIFIED` rather than a
guess.

None of that existed. What the checker does today is **catch** particular
weakenings with particular asserts: an exemption that hides a tracked file, a
markdown ceiling above the register's, a coverage allow-list that leaves a
tracked module out. Each is a hard-won rule about one config key, and each
answers *is this repository conformant right now* — not *which way did this
change move*. Nothing in `src/` reads a delta and reports a direction, and
`register-variance`, the skill named to report one, has never been built.

The gap matters most where the plan says it does. Phase 5's build plan carries
two criteria for it, moved out of Phase 4 on 2026-08-24 because that phase would
otherwise have tested machinery a later phase builds: *a weakening is classified
by direction, not merely caught*, and *the three known `UNCLASSIFIED` cases
report as `UNCLASSIFIED`, not as a guess in either direction*.

The second is the harder one, and it is the reason this needs a decision rather
than an afternoon. A classifier that returns *narrowing* when it does not know
is worse than no classifier: it launders a guess into a verdict, and the person
reading the report has no way to tell the two apart.

## Decision

**Declining to classify is a verdict the mechanism produces, not a case it falls
through.** Four parts.

**1. The delta compared is one gated config file between two git revisions.**
`register-check variance [--against REF]` reads each config the register names,
at `REF` and in the working tree, and reports the direction between them.

It is deliberately **not** a comparison against what the gate would write today.
Rendering a gate's template inside the checker means re-implementing that gate's
substitution — which values fill which placeholders, and where the block is
placed — and that is a second copy of the gate living in the auditor. The
register holds the values; what it does not hold, and what belongs to each
SKILL.md, is the placement. A checker that grew its own copy would disagree with
the gate eventually, and the disagreement would surface as a report nobody can
act on.

**2. Three shapes are classifiable, and the rest is not.**

| Shape | Direction |
| --- | --- |
| Membership of a mapping or list — rules, entries, allow-list members | added only → **narrowing**; removed only → **loosening**; both → **unclassified** |
| A scalar whose key the register gives a polarity | moved toward the stricter end → narrowing; away → loosening |
| Anything else, and any config that is not declarative data | **unclassified** |

The three cases the schema names fall out of this rather than being special-cased,
which is the property worth having: *a rule replaced by a differently named rule*
is a membership delta with both additions and removals; *a threshold whose
direction depends on the metric's polarity* is a scalar whose key the register
has not given one; *a config expressed as executable code* is not declarative
data and cannot be parsed into either shape.

**3. Polarity is a register fact.** A new top-level `variance.polarity` block
maps a config key to the end that is stricter — `lower`, `higher`, `true` or
`false`. A key the register does not name is one the classifier declines to
judge, and that is the mechanism for case 2 rather than an omission in it.

It is the register's rather than the checker's by ADR 0018's test: a reasonable
Equal Experts repository could gate a tool this one has never heard of, whose
keys this checker could not enumerate. Guessing polarity from the key's name —
`max_*` is a ceiling, `min_*` is a floor — was considered and rejected: it looks
principled and is wrong the first time a tool spells a ceiling `limit`, and a
wrong polarity reports a loosening as a narrowing, which is the one failure this
ADR exists to prevent.

**4. A mixed delta is a loosening.** Where one file's keys disagree, the report
takes the strictest reading in this order: **loosening** beats **unclassified**
beats **narrowing** beats **unchanged**. A change that tightens one rule and
relaxes another is not a wash — the relaxation is real, and averaging it away is
how a weakening gets merged with a green report above it.

Exit codes are ADR 0016's vocabulary, unchanged: `1` for a loosening of a
`narrowing-only` control, `3` where something could not be classified, `0`
otherwise. `variance` is its own command and **not** part of a conformance run,
for the reason `deployments` is not: it answers a different question, about a
change rather than about a state.

## Alternatives considered

**Compare the deployed artefact against the gate's rendered template.** This is
what `02-skill-family.md` § The three moments describes for the sweep, and it is
right about the moment and wrong about the instrument — see point 1. The sweep
can still ask *is this gate owed a re-run*, which is what
`register-check deployments` already answers from the stamp.

**A key-to-polarity table inside the checker.** Rejected by ADR 0018's boundary
test. It would also have made the checker's coverage invisible: a repository
whose tool is missing from the table would get *unclassified* with no way to see
that the fix was one line of register.

**Report a mixed delta as neutral, or as its majority direction.** Rejected. A
loosening does not stop being one because something else tightened beside it,
and a majority vote over config keys is a number with no meaning.

**Fail the conformance run on an unclassified delta.** Rejected as a category
error: a conformance run reports whether the repository is conformant *now*, and
an unclassifiable change may be perfectly conformant. The controls that must
fail on a weakening already do, through their own asserts.

## Consequences

A weakening of a `narrowing-only` control can now be named as one, with the file
and the key, rather than only failing whichever assert happens to cover it. The
three declining cases report as declining, and each one says which of the three
it is, so a reader can tell *the classifier cannot know this* from *nobody has
told the register the polarity yet* — the second being a one-line fix and the
first not being a fix at all.

**The classifier's coverage is exactly the register's `variance.polarity`
block plus membership.** That is a small surface today, and honestly small
rather than quietly small: a repository that wants more direction gets it by
naming more keys, and the report says which keys it declined on.

**It reads git, so it needs a ref that exists.** On a shallow clone, or where
`--against` names something absent, there is no delta to classify and the
command says so rather than reporting *unchanged* — an absent baseline and an
identical baseline are not the same answer.

**Nothing here weakens the asserts that already catch weakenings.** ADR 0019's
rule still fails a build; the markdown ceiling still fails a build. This adds a
direction to a change, and it must never become the place those checks move to:
a report that runs on demand is not a gate.
