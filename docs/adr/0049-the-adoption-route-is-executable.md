# ADR 0049: The Adoption Route Is Executable, And Detects Rather Than Instructs

**Status:** Accepted
**Date:** 2026-09-03
**Revision:** 1

## Background

`START-HERE.md` is a linear document with fourteen sections and six numbered
steps, and two people have now followed it end to end on their own machines.
Both arrived at a working repository. Both also lost time to the same class of
problem, and it is not a documentation problem:

* **`uv` was missing.** § C2 tells an adopter to run `uv init` on the Mac, and
  § B listed every other tool but not that one.
* **`gh auth login` had been answered `ssh`**, so § C wrote a `git@github.com:`
  origin that nothing inside the container can push to.
* **A global `url.…insteadOf` rewrite** turned step 1's HTTPS marketplace clone
  into an SSH one, which failed `Permission denied (publickey)` — an auth error
  that is not an auth problem.

Each was fixed in the guide. That fixes it for the next reader of *that
paragraph*, and every one of them was a **precondition that a machine could have
been asked about in a second**. A reader cannot check a precondition they do not
know exists, and the document cannot know which of the fourteen sections the
reader has already satisfied. It is a route, and the reader is holding it the way
you hold a map with no "you are here".

The failures also arrive **late and displaced**. A surviving `{{UV_VERSION}}`
placeholder is silent at step 4 and fails during a container build at
`sha256sum -c`. An untracked `.python-version` is silent until SUP-001 fails at
the very end. The distance between the cause and the report is where the time
goes.

## Decision

**Ship a chain of detection scripts that report machine state and name the next
script to run, and hold them to detecting only — the guide keeps every
instruction.**

`plugins/control-register/templates/adopt/` carries five stages and an entry
point:

| Stage | Settles |
| --- | --- |
| `00-preflight.sh` | Host tools, Docker, the `gh` protocol, URL rewrites, Keychain entries |
| `10-repo.sh` | A repository, a remote, the § C2 project, the register |
| `20-platform.sh` | Visibility, rulesets, push protection, what the plan allows |
| `30-container.sh` | Template copied, placeholders substituted, container built |
| `40-adopt.sh` | Inside: plugin, checker, installed hooks, bots, `register-check` |
| `status.sh` | Walks the route and names the first stage that is not satisfied |

Three properties make this something other than a second copy of the guide.

**1. A script prints a verdict and a section reference, never an instruction.**
A failing check reads `✗ uv — not on PATH → START-HERE.md § B`. The words that
tell you what to do exist once, in the document.
`tests/test_adopt_route.py` fails the build if a script names a section that is
not a heading in `START-HERE.md`, and if a script's *printed* output contains a
command the guide already carries — `brew install`, `uv init`,
`security add-generic-password` and the rest. A comment naming a skill to
explain what a stage is for is not output and is allowed.

**2. The exit code is the routing.** Four values, and they are what makes the
chain a chain rather than six scripts in a folder:

| Code | Means | The reader |
| --- | --- | --- |
| `0` | this stage holds | runs the next script it printed |
| `1` | a check failed | fixes it at the section named, re-runs this one |
| `2` | a manual act is outstanding | does it — or waits on whoever has the rights |
| `3` | cannot be verified from here | is on the wrong machine for this stage |

`3` is the one that earns its place. The host/container split is this
repository's most expensive gotcha — a host run once reported green about a `uv`
version it was not using — and a stage that cannot answer says so rather than
guessing. `status.sh` prints `n/a here` for it and does not count it against you.

**3. The manual acts stay manual, and are detected by their effect.** Creating a
PAT, `claude setup-token`, enabling push protection and installing Renovate are
not automated. Each is a `•` line naming the section, and the *next* run detects
that it was done. Nothing here writes to GitHub, and nothing here writes to the
adopter's repository.

**The route order lives in `_lib.sh` and nowhere else.** `status.sh` walks
`ROUTE_SCRIPTS`; a test asserts that list and the files on disk agree in both
directions, so a stage cannot be added without joining the route or deleted while
still named.

## Alternatives considered

**A single `doctor` script.** One invocation, every check, one report. Rejected
because the report is the problem: an adopter at § B does not want to be told
about their branch ruleset, and a fifty-line report where six lines apply is how
people stop reading reports. The stages exist so that each one asks only what is
answerable now.

**Scripts that fix what they find.** `brew install uv`, `git remote set-url`,
`gh auth login`. Rejected on the core invariant: the moment a script performs a
step, it holds a copy of that step, and the copy is what drifts. It also removes
the reader from decisions that are theirs — which token, which protocol, which
repository — and § E exists because those choices have consequences ninety days
later.

**Generating the scripts from `START-HERE.md`.** Tempting, and it would make the
duplication impossible rather than merely tested. Rejected as more machinery than
the problem needs: the reference test achieves the same guarantee, fails with a
legible message, and does not add a build step to a document people edit by hand.

**Putting them in this repository's `scripts/`.** Rejected: they are for
adopters, and adopters get artefacts through the plugin. They ship beside
`templates/devcontainer`, which is the thing step 4 already copies.

## Consequences

**The guide stays the only instruction, and gains a "you are here".**
`START-HERE.md` is unchanged in what it says; it gains a pointer to the route.
An adopter who prefers to read straight through loses nothing.

**A renamed section fails the build.** That is the intended cost. The references
are load-bearing, and a route that sends a reader to a section that no longer
exists is worse than no route.

**The scripts run on macOS, and say so when they do not.** `00-preflight.sh`
reads the Keychain through `security`. On another platform it exits `3` and
names § A, which states the contract a replacement for `fetch-secrets.sh` owes.

**They are not controls and never become them.** Nothing here is in
`controls.yaml`, nothing gates a merge, and a green route is not conformance —
`register-check` is what says whether the controls hold. The route only gets an
adopter to the point where that command can answer at all.

**A new step in the guide needs a stage, or it is unrouted.** This is the
maintenance burden this ADR accepts. It is bounded by the test: the route and
the directory must agree, so the failure is loud rather than silent.
