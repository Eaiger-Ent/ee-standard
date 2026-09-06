# ADR 0054: Craft Cites Its Sources and Copies None of Them

**Status:** Accepted
**Date:** 2026-09-06
**Revision:** 1

## Background

**The problem.** `docs/craft/plan.md` lists as decision 4: attribution and
licence, per source. `docs/craft/survey.sources.md` registers twenty-four
sources under six different licence answers, and this repository is public. What
Craft may take from each, and what it owes in return, has to be settled before
S5 ships prose to other teams.

**The licences are not uniform, and two of them constrain a public repository.**

| Source | Licence | What it constrains |
| --- | --- | --- |
| PEP 8, PEP 20, PEP 257 | Public domain | Nothing |
| ruff, pytest, the ESLint plugins, `commitlint` | MIT / ISC | Copying text requires the notice |
| `spectral`, OpenAPI Specification | Apache-2.0 | Copying text requires the notice |
| Google Python Style Guide | CC BY 3.0 | Attribution required on any copy |
| Rules of React, *You Might Not Need an Effect* | CC BY 4.0 | Attribution required on any copy |
| **OWASP ASVS** | **CC BY-SA 4.0** | **Share-alike** — a derivative inherits the licence |
| **WCAG 2.2** | **W3C Document License** | Restricts derivative works |
| **`llm-toolkit`** | **None** | Nothing to point at |

**A rule is not its wording.** "Do not use a mutable data structure as an
argument default" is an idea; copyright does not reach it. Every one of the
twenty-four sources can be read, every rule in it understood, and our own
binding written, without any licence question arising. What licences govern is
*expression* — the paragraphs, the examples, the phrasing.

**That distinction is where the risk is, because it is easy to lose.** S1 already
recorded it as finding 1 about `llm-toolkit`: Equal Experts owns the repository
and this work is Equal Experts', so the ideas are ours to use, and the absent
licence file still means there is nothing to point at when copying prose. The
same sentence is true of ASVS with the opposite cause — a licence exists, it is
share-alike, and copying its text would put a share-alike obligation on a public
repository's derived work. Two very different sources, one rule that handles both.

**`docs/craft/plan.md` already forbids half of this.** § What this workstream
will not do names "vendor another team's prose without a licence". What it does
not say is what to do about a source whose licence is present and inconvenient,
which is ASVS, and which is the row that made this decision necessary rather than
obvious.

## Alternatives Considered

### Option 1: Copy permissively-licensed prose, write our own for the rest

Take text from the MIT, Apache and public-domain rows with their notices; write
around ASVS, WCAG and `llm-toolkit`.

**Rejected, because it puts two classes of text in one artefact and no reader
can tell them apart.** A rule's prose that came from ruff's documentation and a
rule's prose someone wrote look identical on the page. The obligations differ,
the attribution differs, and the moment someone copies from the wrong row the
repository inherits a duty nobody is tracking. It also makes the Licence column
load-bearing in a way nothing checks — which is the shape of every failure
recorded in `docs/09-phase-1.5-review.md`.

### Option 2: Vendor everything, with attribution

Copy the rules as written, attribute each, and accept the obligations.

**Rejected on two counts.** `plan.md` rules out vendoring prose without a
licence, which disposes of `llm-toolkit` — the largest single body of text on
offer. And ASVS's share-alike would attach to whatever Craft ships that is
derived from it, on a public repository, for the benefit of nothing: we do not
need OWASP's words, only its requirements.

### Option 3: Cite every source, copy none of them

Sources are read for their rules, cited against an identity, and every word Craft
ships is its own.

**Chosen.** It is one rule rather than twenty-four, it is the same rule for the
source with the best licence and the source with none, and it removes both
constraining licences from the picture entirely rather than managing them.

## Decision

**Craft cites every source and copies none of them.** Every rule in every
registered source may be read, understood and bound to a tool. Every word Craft
publishes — profile documentation, the judgment-only residue S5 hands back, the
property descriptions in the Craft register — is written for Craft.

**Citation is against an identity, never as one**, which
`docs/craft/plan.md`'s naming standard already requires for a different reason:
upstream IDs are file-local and collide. The two reasons agree.

**The Licence column in `survey.sources.md` is read before wording is taken, not
after.** It exists to be consulted. Under this decision it should never change an
answer — the answer is always "write your own" — and its value is that it makes
the one case where somebody proposes an exception visible.

**Attribution is given regardless of whether it is owed.** Every property in the
Craft register cites the sources that assert it, including the public-domain ones
that require nothing. Provenance is worth more than the licence obligation it
happens to satisfy: a rule whose source is recorded can be re-checked when the
source moves, which is what `survey.sources.md` § How to re-run this sweep is for.

**No source is excluded on licence grounds.** ASVS's share-alike and WCAG's
document licence constrain copying, and Craft does not copy, so both are used in
full as sources of requirements. `llm-toolkit`'s absent licence is likewise not a
bar to reading it.

## Consequences

**Craft's prose is slower to write, and it is the only thing being paid.** Every
rule description has to be composed rather than quoted. That cost is paid once
per property and it buys a repository with no inherited obligations, no
share-alike surface, and one rule instead of a per-source matrix.

**A future contributor will propose copying something, reasonably.** A well-worded
paragraph from `react.dev` under CC BY 4.0 is genuinely usable with attribution,
and refusing it will look pedantic in that one case. The answer is that the rule's
value is in being uniform: the moment it admits a good case it stops being
checkable by reading, and the ASVS row is what the exception eventually reaches.

**Nothing here is enforced by a test or a control.** This is an authoring
convention about a workstream's own documents, in the same class as ADR 0025's
revision records — and `tests/test_adr_revisions.py` § docstring gives the reason
that class stays out of `controls.yaml`: putting it there would make every
adopter inherit an authoring convention, which [ADR
0022](0022-a-platform-token-ci-carries.md) requirement 6 rules out. A reviewer
noticing quoted prose is the whole mechanism.

**If Craft's output is ever published outside this repository**, this decision is
what makes that a non-event. There is nothing to clear, because there is nothing
of anyone else's in it.

## Related ADRs

- [ADR 0025](0025-an-amendment-is-a-recorded-revision.md) — the other authoring
  convention this repository holds about its own documents, and the precedent for
  such a convention living in an ADR and a test rather than in `controls.yaml`.
- [ADR 0022](0022-a-platform-token-ci-carries.md) § 6 — an authoring convention
  this repository holds for itself does not become something adopters inherit.
- [ADR 0053](0053-the-craft-mapping-is-register-data.md) — the Craft register
  that carries the citations this decision requires.

## References

- `docs/craft/survey.sources.md` — the twenty-four sources and their licence
  answers, including finding 1 on `llm-toolkit`'s absent licence and finding 3 on
  detection not being a licence answer.
- `docs/craft/plan.md` § What this workstream will not do — "vendor another
  team's prose without a licence", which this record generalises.
- [Creative Commons — CC BY-SA 4.0 legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode),
  § 3(b) ShareAlike: an adaptation of share-alike material must itself be
  licensed under the same terms.
- [W3C Document License](https://www.w3.org/copyright/document-license/), which
  permits copying in full but restricts derivative works.
