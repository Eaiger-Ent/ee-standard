# ADR 0050: A Tag Is Retained Only While It Is a Version Someone Should Be Running

**Status:** Accepted
**Date:** 2026-09-04
**Revision:** 1

## Background

**The problem.** Every tag this repository has ever cut is an install address,
and nothing said which of them were supported. A tag here is not a marker in the
history. It is a version of the register, the checker and the template together,
fetched over the network by three routes and recorded as a pin inside somebody
else's repository. Twelve of them existed on 2026-09-04, back to `v0.1.0`, and
every one was as installable as the newest.

**An old tag is not inert.** It ships a whole artefact, and that artefact goes
on being deployed. [`docs/15-phase-6-review.md`](../15-phase-6-review.md) records
the case: *"`v0.5.0` pins uv **0.12.5** and `main` pins **0.12.6**, and a tag
ships a register and a template as one artefact"* — the build there took
`main`'s register by hand rather than the tag's, because following the adoption
route verbatim would have crossed the two. A tag left standing is a standing
offer to deploy gates that were superseded.

**Nothing steers anybody towards an old one, and one thing steers them back
to it.** All three routes resolve the newest tag and none takes a version from a
human:

```text
adopt.sh:34            tag=$(git ls-remote --tags --refs "$REPOSITORY" | ... | tail -1)
START-HERE.md:582      tag=$(git ls-remote --tags --refs "$repo"       | ... | tail -1)
templates/adopt/guided.sh:217                                            (the same line)
```

So no adoption can *land* on an old tag. But the register it fetches carries
`tools.register-check.install.ref` naming **that same tag**, which the adopter
then owns; `register-install` installs the checker from it. A repository that
adopted at `v0.2.0` and re-runs the install a year later gets `v0.2.0`'s
checker, reading `v0.2.0`'s register, against a standard that has moved thirty
contracts. That is the one path back to an old tag, and it is silent.

## Alternatives Considered

### Option 1: Keep every tag, forever

The status quo, and the default reading of "never break a pin".

**Rejected.** It treats the pin as the thing to protect and the deployment as
somebody else's problem. The pin it protects is the one case above — a repository
re-installing a checker generations old — and protecting that case is what makes
it fail quietly. There is also no cost being avoided: a tag holds nothing, the
release pages carry no assets, and none of this is a registry where an old
version is load-bearing for a resolver.

### Option 2: Delete the release page and keep the tag

The tidy-looking half: the releases list gets shorter and nothing can break.

**Rejected, because it acts on the wrong artefact.** A release page is notes. No
route reads one, no install resolves one, and deleting it changes nothing about
what can be deployed while removing the only human-readable account of what
changed. It buys the appearance of a retention policy and none of the effect.

### Option 3: Retain a window, and delete the tag with its release page

Keep the three newest minor lines, and within each the two newest patches.
Everything outside the window goes — tag and release page together.

**Chosen.** It is the only option that changes what can be deployed. Deleting
the tag is what turns a silent re-install of a superseded artefact into a loud
failure at the fetch, and the window is drawn where a supported version stops:
you should be running the newest release, or the newest patch of the line you
are on.

## Decision

We choose Option 3: **a tag is retained only while it is a version someone
should be running.** The window is the three newest minor lines, and the two
newest patches within each; a version outside it has its tag and its release
page deleted together.

Three properties make it safe to apply, and each is a fact about this repository
rather than a hope:

**The current pin cannot be pruned by accident.**
`tests/test_register_install.py::test_the_tag_the_register_names_exists` resolves
`tools.register-check.install.ref` against the tags in the checkout — in CI, a
fresh clone of the remote — so deleting the tag the register names fails the
build.

**The notes are not the record.** A release page's body is the release commit's
message, reformatted; those commits stay on `main`. Deleting the page loses the
formatting and no content.

**A deleted tag can be re-cut.** Every tag pointed at a commit that is an
ancestor of `main`, so the artefact remains reachable and a tag deleted in error
is restored by name from its SHA.

**In `0.x` the minor is the breaking axis.** There is one major line, so the
usual major clause of such a policy is vacuous, and "three minor lines" means
three generations rather than three point releases. At `1.0` the window re-reads
as the two newest majors, three minor lines, two patches — the same sentence,
with a major axis that has become real.

## Consequences

**An adopter pinned to a pruned tag fails at the fetch.** `register-install`
cannot resolve the ref, and says so. This is the intended effect, not a
tolerated cost: the alternative is that it succeeds and deploys a superseded
register. The repair is to re-fetch the published register, which resolves the
newest tag by construction.

**Retention is applied by hand at release time, and is not a test.** A check
would have to enumerate tags over the network and fail a build for a state that
no commit can fix — a tag is not in the tree, so there is nothing to edit in
response. This ADR is the record instead, which is the same reason
`tests/test_adr_revisions.py` is a test and not a control: the rule governs how
this repository publishes itself.

**It is not a control, and must not become one.** Nothing here describes a
conformant repository — this is how this repository publishes itself, and an
adopter cuts their own tags on their own cadence. Recording it in
`controls.yaml`, or under `plugins/`, would ship one repository's publication
policy to everyone who installs the plugin, which is what
[ADR 0022](0022-a-platform-token-ci-carries.md) § 6 refuses of any arrangement
that is ours rather than the standard's.

## Applied — 2026-09-04

Twelve tags and six release pages became four and three.

```text
kept     v0.8.4  v0.8.3  v0.7.0  v0.6.0
deleted  v0.8.2  v0.8.1  v0.8.0  v0.5.0  v0.4.0  v0.3.0  v0.2.0  v0.1.0
```

Release pages existed for `v0.7.0` and `v0.8.0`–`v0.8.4`; the three inside the
deleted set went with their tags. `v0.6.0` and everything below it never had
one. After the prune the three routes still resolve `v0.8.4`, and
`tests/test_register_install.py`, `tests/test_adopter_guide.py` and
`tests/test_start_here.py` pass.

## Related ADRs

- [ADR 0032](0032-the-checker-is-installed-from-a-tagged-ref.md) — why the
  checker is installed from a tagged ref at all, which is what gives a tag its
  reach into another repository.
- [ADR 0048](0048-the-published-register-is-derived.md) — the register an
  adopter fetches is `controls.published.yaml`, fetched **at a tag**, and it is
  the artefact that carries `install.ref` into their repository.
- [ADR 0049](0049-the-adoption-route-is-executable.md) — `adopt.sh` resolves
  the newest tag and clones it, the third route that depends on there being a
  newest tag worth resolving.
- [ADR 0022](0022-a-platform-token-ci-carries.md) § 6 — a difference that is
  this repository's own is recorded where adopters do not inherit it, which is
  why this is an ADR and not a control.

## References

- [Semantic Versioning 2.0.0](https://semver.org/), § 4: a `0.y.z` major of zero
  is for initial development, and the guarantees a major line carries do not
  apply until `1.0.0` — which is why the window's major clause waits.
- [GitHub — Managing releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository),
  on deleting a release and its tag as separable acts.
