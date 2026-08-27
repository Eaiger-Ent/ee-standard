# register-variance

Reports which way a change to gated configuration moved — narrowing, loosening,
or neither — and says which keys it could not classify and why.

## Why this exists at all

Because the standard has promised a *direction* since Phase 0 and never computed
one.

`00-concepts.md` § Variance says a delta usually has a knowable direction:
*"adding a lint rule strengthens, raising a coverage floor strengthens,
excluding authored content weakens."* `01-register-schema.md` goes further and
says the checker *"classifies the delta's direction and fails on any
weakening"*, then names three cases where classification declines rather than
guesses.

What existed instead was a set of asserts that **catch** particular weakenings:
an exemption hiding a tracked file, a markdown ceiling above the register's, a
coverage allow-list leaving a tracked module out. Each answers *is this
repository conformant right now*. None answers *which way did this change move*,
and the difference matters in review, where the question is about a diff rather
than about a state.

## What it is not

**It is not a gate.** The controls that must fail on a weakening already do,
through their own asserts, and they still do. This report runs on demand, and a
report that runs on demand is not a gate. Moving one of those checks here would
be trading a build failure for a command somebody has to remember.

**It writes nothing** — no config, no stamp, no register edit — except the one
fix described below, and only when asked. It deploys no control and appears in
no `deploys.json`, because a provenance stamp names a control and there is none
to name.

## Declining is the point

A classifier that answers *narrowing* when it does not know is worse than no
classifier. It launders a guess into a verdict, and the reader cannot tell the
two apart. So this reports `UNCLASSIFIED` **with the reason**, and the three
reasons are not interchangeable:

| Reason | Fixable? |
| --- | --- |
| A member was removed and another added — whether the new covers the old is a fact about the tool's rule catalogue | No. Ask the author |
| The register gives no polarity for the key | **Yes**, in one line of `variance.polarity` |
| The config is executable code rather than declarative data | No, not without changing what the repository uses |

Only the middle one has a fix, and offering it for the other two tells someone a
one-line answer exists where it does not.

## Where the direction comes from

The register, not this skill and not the checker. `variance.polarity` maps a
config setting's leaf name to the end that is stricter — `lower`, `higher`,
`true` or `false`. A setting the register does not name is one the classifier
declines to judge.

That is [ADR 0018](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0018-register-checker-boundary.md)'s
boundary test applied: a reasonable Equal Experts repository could gate a tool
this checker has never heard of, so a polarity table inside the checker would be
a coverage limit nobody could see or extend. Guessing from the name — `max_*` is
a ceiling, `min_*` is a floor — was considered and rejected: it is wrong the
first time a tool spells a ceiling `limit`, and a wrong polarity reports a
loosening as a narrowing.

## A mixed delta is a loosening

Where one key tightens and another relaxes, the file's verdict is the
relaxation. It is not a wash and it is not a majority vote: the relaxation is
real, and averaging it away is how a weakening gets merged under a green line.

## The decision behind it

[ADR 0040](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0040-a-declined-classification-is-a-verdict.md),
including why the delta is read between two git revisions rather than against
what the gate would write today — rendering a gate's template inside the checker
means re-implementing that gate's substitution, which is a second copy of the
gate living in the auditor.
