# ADR 0056: Craft Names a Surface Only Where the Control Register Names None

**Status:** Accepted
**Date:** 2026-10-18
**Revision:** 1

## Background

**The problem.** The S6 trial decided that `python/strict` should install three
pytest guards and a branch-coverage floor. Craft cannot write them anywhere.
Every file a profile writes must be one `controls.yaml`'s `stacks:` block names,
and `stacks:` names no pytest configuration and no coverage configuration. So
the revision is decided and has nowhere to go.

**The rule that stops it is a good rule.** `docs/craft/design.profiles.md`
§ The config surface says *every file named below is quoted from `stacks:`, and
none is chosen here*, and `craft/python.yaml` carries no `file:` key because
ADR 0055 makes the control register the source of where configuration lives.
The point was to stop Craft keeping a second list of the locations LNT-001 and
TYP-001 read. That point holds. What the rule did not anticipate is a tool no
control gates, where there is no first list for Craft's to be a second copy of.

**Three facts shape any answer, and each was measured on pytest 9.1.1.**

| Fact | Consequence |
| --- | --- |
| A `pytest.ini` beside `pyproject.toml` replaces the pyproject configuration entirely: *configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)* | The same nearest-file hazard ruff has, and Craft's ruff installer already refuses a sibling `ruff.toml` for it |
| `[tool.pytest]` and `[tool.pytest.ini_options]` in one file is an error: *Cannot use both … simultaneously* | An installer must write into whichever spelling the repository already uses, and never add the other |
| `pytest-socket` is switched on only through `addopts`, and `pytest-cov` measures nothing without `--cov` there. `pytest-timeout` has its own key, `timeout`; `pytest-randomly` needs no configuration | Two of the four guards need a key the repository may already own, and a TOML key cannot be split between two writers |

**The fourth fact is about the number.** A coverage floor is a threshold, and
the right one belongs to the repository: 94% was right for the trial repository
and is no default. Every threshold Craft writes today — `max-complexity`,
`max-statements` — is the profile's. This is the first that is not.

## Alternatives Considered

### Option 1: Give pytest a gate in `controls.yaml`'s `stacks:` — Rejected

Add a `test` role beside `lint` and `typecheck`, naming pytest's configuration
locations, so Craft quotes them as it quotes ruff's.

**Pros:** The design rule survives untouched. The locations live where every
other tool's do.

**Cons:** No control would read the entry. TST-001 gates the test *command*,
from `ecosystems:`, and asserts nothing about pytest's configuration. The
checker's gate roles are a closed set (`_GATE_ROLES`), so this is a checker
change, a register contract and a checker release that every adopter takes, all
for a field only Craft reads. `craft/meta.yaml` already declines exactly this
for its two predicates: *adding one to the control register purely for Craft's
benefit is the direction ADR 0053 sent Craft data away from.*

### Option 2: Craft names a surface only where the control register names none — Chosen

`craft/meta.yaml` gains `surfaces:`, one entry per tool, giving that tool's
configuration locations in the order the tool itself searches them. An entry is
legal only for a tool `stacks:` does not name. A tool named in both is a schema
error, which is the rule `craft/meta.yaml` already applies to predicates.

**Pros:** No second copy can exist. The register names a location, or Craft
does, never both, and a test makes that illegal rather than discouraged. The day
a control comes to gate pytest's configuration, Craft's entry fails the build
and moves, rather than drifting.

**Cons:** Craft's register gains a kind of fact it was designed not to hold, and
the design document's rule needs a stated exception.

### Option 3: Craft installs the plugins and hands the wiring to the adopter — Rejected

Add the four dependencies, write nothing into pytest's configuration, and put
the flags in the residue as a step to take.

**Pros:** No new kind of register fact. No contested key.

**Cons:** An installed plugin nobody switches on is inert. That is the gap
`CLAUDE.md` names for hooks: *a wired locus is not an installed hook.* The trial
showed which of these two the owner would have been left with. The profile
would report a guard it had not installed.

## Decision

**We choose Option 2: Craft names a tool's configuration surface only where
`stacks:` names none, and a tool named in both is a schema error.**

Three rules come with it, and each answers one of the measured facts.

**1. `addopts` is written only where the repository has none.** It is one key
holding one value, so Craft cannot own a span of it. Where `addopts` already
exists outside Craft's markers, the installer stops and names the flags to add,
as it already stops on a hand-written `[tool.ruff.lint] select`. A repository at
its start, which ADR 0052 says the profile is for, has none.

**2. The installer writes into the spelling the repository uses.** If
`[tool.pytest]` exists it writes there; if `[tool.pytest.ini_options]` exists it
writes there; if neither does it creates `[tool.pytest]`. **Any other pytest
configuration makes it stop.** A `pytest.toml`, `.pytest.toml`, `pytest.ini` or
`.pytest.ini` outranks `pyproject.toml`, so Craft's lines would be ignored — the
reason it stops on a sibling `ruff.toml`. A `[pytest]` in `tox.ini` or a
`[tool:pytest]` in `setup.cfg` ranks below it, so a new `[tool.pytest]` table
would silently replace the repository's own configuration. Both directions are
the same failure, and the order is pytest's, which is what `surfaces:` records.

**3. A threshold that is the repository's is asked for and never defaulted.**
The installer asks for the coverage floor, writes the answer, and records it in
the stamp. With no answer it installs the other guards and says that the floor
was not installed, rather than inventing one.

| | Before | After |
| --- | --- | --- |
| Where a location comes from | `stacks:` only | `stacks:`, or `craft/meta.yaml` `surfaces:` for a tool `stacks:` does not name — never both |
| `python.test-independence`, `python.no-flaky-tests`, `python.branch-coverage-floor` | `candidate:` in the residue | Bound at `python/strict` |
| What `python/strict` adds to the lockfile | Nothing | `pytest-randomly`, `pytest-timeout`, `pytest-socket`, `pytest-cov`, through `ecosystems.python.add_dev_dependency` |
| `craft_contract` | 2 | 3 — an installer that did not understand `surfaces:` or a dependency-carrying instrument would write half a profile |

## Consequences

**Positive outcomes:**

- **The guards the trial needed become installable**, and the residue stops
  describing as unchecked three properties a tool can check.
- **The no-second-copy rule gets stronger, not weaker.** Today it holds because
  Craft has no locations at all. After this it holds because a test fails when
  a location is in both registers.
- **The refusals are ones the installer already makes.** A sibling config file,
  and a hand-written key Craft would need to own, are both stop conditions now.

**Trade-offs and risks:**

- **The Python profile adds dependencies for the first time.** Until now ruff
  shipped every rule it selected. Four more packages come under SUP-001's pins
  and SUP-002's update proposals, and each has to be registered in
  `craft/meta.yaml` `sources:` with its maintenance signals, per ADR 0054.
- **`addopts` makes the install refuse more often than the ruff half does.** A
  repository that already uses `addopts` gets a refusal and a list of flags. That
  is honest and it is friction.
- **A strict profile now changes how the suite runs**: random order, a timeout,
  no network past loopback, a coverage threshold. Each makes TST-001's
  verdict stricter, which `variance: narrowing-only` allows. None loosens it.
- **ADR 0055 rule 1 has nothing to forbid here.** It reads gated keys from
  `stacks:`, and pytest has none. If a control later gates pytest's
  configuration, rule 1 applies to it from that day, through the same schema
  error that moves the surface.

## Related ADRs

- [ADR 0055](0055-craft-writes-into-a-gated-section.md) — the rule that the
  control register says where configuration lives. This decision is its
  exception for a tool no control gates, and leaves the rule as it is.
- [ADR 0053](0053-the-craft-mapping-is-register-data.md) — Craft data stays out
  of the control register, which is why Option 1 is rejected.
- [ADR 0052](0052-a-profile-is-a-stack-and-a-strictness.md) — the profile is for
  a new repository, which is why refusing an existing `addopts` is cheap.
- [ADR 0054](0054-craft-cites-its-sources-and-copies-none.md) — every new tool is
  a registered source.
- [ADR 0051](0051-a-craft-rule-becomes-a-control-by-being-installed.md) — a
  coverage floor installed by a profile is still a craft rule, not a control.

## References

- [`docs/craft/review.trial.md`](../craft/review.trial.md) § The revision,
  2026-10-18 — the decision this record makes installable.
- [`docs/craft/design.profiles.md`](../craft/design.profiles.md) § The config
  surface — the rule this record makes an exception to.
- pytest, [Configuration](https://docs.pytest.org/en/stable/reference/customize.html)
  — the file search order and the two `pyproject.toml` spellings.
