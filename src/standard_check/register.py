"""Loading and schema-validating `controls.yaml`.

A malformed register is a build failure, not a warning — everything downstream
derives from it (docs/01-register-schema.md). Every schema error names the
field it arose from, and the assert namespace is closed: an unknown assert
name is a schema error, never a silently skipped check.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import yaml

from standard_check.asserts import ASSERTS, REMOTE_ASSERTS
from standard_check.asserts_file import CONTROL_ARG
from standard_check.predicates import PredicateSyntaxError, compile_predicate

RUNGS = ("advisory", "warn", "blocking", "blocking (baselined)")
LOCI = ("editor", "pre-commit", "ci", "remote")
# `justified` and `free` were removed at contract 3. `justified` was
# unimplementable as specified: 00-concepts.md says a justified weakening *is* a
# baseline entry, and the validator rejects any Tier-1 baseline, so the
# mechanism that stops it becoming a loophole was structurally unreachable for
# both controls that used it. `free` had no users and asserts nothing.
VARIANCES = ("forbidden", "narrowing-only")
KINDS = ("command", "file", "remote")

_CONTROL_ID = re.compile(r"^[A-Z]{2,4}-\d{3}$")
_META_ID = re.compile(r"^GOV-\d{3}$")
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

# `run:` is executed with shlex.split and no shell, so an operator in the string
# is not an operator — it becomes a literal argument. `true && false` ran as
# `true` with two ignored arguments and exited 0, which would have let a future
# `pytest && mypy` silently check only pytest. Rejected at schema time rather
# than executed correctly: giving the register a shell would make every `run:`
# string a shell-injection surface for no gain the register needs.
_SHELL_OPERATOR = re.compile(r"(?:&&|\|\||[;|&><]|\$\(|`)")

# The meta-control self-invocation, the single exception to the `kind:`
# taxonomy. `verify_meta.py` matches the same shape and runs the check in
# process; this pattern is what bounds where the spelling is allowed.
_SELF_META = re.compile(r"^standard-check meta (\S+)$")

# Keys the schema knows. Anything else is an error, not a silent no-op:
# 02-skill-family.md § Version policy describes a per-control `pinned` /
# `floating-minor` / `latest` field that exists in neither the schema doc nor
# the register, and because unknown keys were accepted, adding it would have
# been ignored rather than rejected.
_DOCUMENT_ALLOWED = (
    "version",
    "meta",
    "tools",
    "ecosystems",
    "stacks",
    "suppression",
    "cloud_credentials",
    "predicates",
    "controls",
    "meta_controls",
)
_TOOL_ALLOWED = (
    "source",
    "version",
    "sha256",
    "lockfile",
    "pinned_at",
    "invocation",
    "release_repo",
)
_TOOL_SOURCES = ("lockfile", "literal")
_ECOSYSTEM_ALLOWED = (
    "manifest",
    "lockfiles",
    "dependabot",
    "test_commands",
    "frozen_install",
)
_STACK_ALLOWED = ("gates", "source_globs")
_GATE_ALLOWED = (
    "tool",
    "invocation",
    "pre_commit",
    "editor_extension",
    "strict_key",
    "coverage_key",
    "config",
)
_GATE_REQUIRED = ("tool", "invocation", "config")
_CONFIG_ALLOWED = ("file", "section")
# The roles a gate can play. Closed, and a property of the register format
# rather than of any repository: a role the checker has no assert for could not
# be verified however well it were declared (ADR 0018).
_GATE_ROLES = ("lint", "typecheck")
_METADATA_ALLOWED = ("owner", "register_contract")
_STANDARD_ALLOWED = ("name", "url")
_BLOCK_ALLOWED = ("kind", "run", "assert", "args", "partial", "applies_to")
_PARTIAL_ALLOWED = ("unverified", "expires")

_CONTROL_REQUIRED = (
    "id",
    "title",
    "enforces",
    "standard",
    "tier",
    "rung",
    "locus",
    "applies_to",
    "verify",
    "owner",
    "variance",
    "baseline",
    "review_by",
    "rationale_adr",
)
_CONTROL_ALLOWED = (*_CONTROL_REQUIRED, "deployed_by", "also_see")
_META_REQUIRED = ("id", "title", "enforces", "rationale", "verify")
_META_FORBIDDEN = ("tier", "rung", "locus", "baseline", "applies_to", "variance")
_META_ALLOWED = _META_REQUIRED


@dataclass(frozen=True)
class SchemaError:
    """A validation failure, naming the field it arose from."""

    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


@dataclass(frozen=True)
class Partial:
    """A verification block's declaration that it is not fully implemented.

    ADR 0017. The declaration lives in the register, not the checker, so
    coverage is a register fact reviewable in the same place as everything else
    — otherwise the checker becomes a second source of truth about its own
    coverage. `expires` is what keeps it from being a loophole: past that date
    GOV-003 fails it, exactly as it fails a control past `review_by`.
    """

    unverified: str
    expires: datetime.date


@dataclass(frozen=True)
class VerifyBlock:
    kind: str
    run: str | None = None
    assert_name: str | None = None
    args: dict[str, object] = field(default_factory=dict)
    # Predicates under which this block runs. Empty means "whenever the control
    # does". A control can hold one property verified by different mechanisms
    # for different repository shapes — BLD-001's `hadolint` reads a Dockerfile
    # and its devcontainer assert reads `devcontainer.json`, and running either
    # against the wrong shape reports on something that is not there.
    applies_to: tuple[str, ...] = ()
    partial: Partial | None = None

    def describe(self) -> str:
        if self.kind == "command":
            return f"command: {self.run}"
        return f"{self.kind}: {self.assert_name}"


@dataclass(frozen=True)
class Standard:
    name: str
    url: str


@dataclass(frozen=True)
class Tool:
    """Where a tool's version is authoritative, and the value when it lives here.

    `source: lockfile` means a package manager already owns the version and the
    loci invoke the tool through it, so there is no version in the register and
    nothing to keep in step — the duplication is *eliminated*. `source: literal`
    means no package manager owns the tool, so the version lives here and each
    locus repeats it; those repetitions are reconciled rather than removed.
    """

    name: str
    source: str
    version: str | None = None
    sha256: str | None = None
    lockfile: str | None = None
    # Every locus that repeats a `literal` version. A register fact from
    # contract 8 (ADR 0018, fourth pass): these were four of this repository's
    # own filenames inside the checker, so renaming a workflow removed it from
    # comparison silently, and an adopting repository's own loci were never in
    # the list at all (§ H2).
    pinned_at: tuple[str, ...] = ()
    # How a locus reaches a `lockfile`-sourced tool's pinned artefact. The pair
    # is symmetric: a `literal` tool records where its version is repeated, a
    # `lockfile` tool records how the pin is reached — because "the lockfile
    # owns the version" is worth nothing if the invocation can resolve
    # elsewhere, which `npx --no-install` silently does (ADR 0020, § H6).
    invocation: str | None = None
    # Where a `literal` tool's release is downloaded from, as `owner/name`. A
    # gate skill that installs the tool needs it, and it was the one value
    # gate-secrets could not derive: the register carried it only inside a
    # `# renovate: depName=` comment, which is an annotation for a bot rather
    # than a field anything can read. A fork or an internal mirror is a
    # reasonable thing for a repository to differ on without the checker
    # changing, so it answers *yes* to ADR 0018's test.
    release_repo: str | None = None


@dataclass(frozen=True)
class Ecosystem:
    """A package ecosystem: how to detect it, and what counts as locked.

    A register fact from contract 3 (ADR 0018): a repository might reasonably
    need a different lockfile spelling without the checker changing, and the
    previous checker-side dictionary silently exempted Go, Rust and Java from
    SUP-001 entirely.
    """

    name: str
    manifest: tuple[str, ...]
    lockfiles: tuple[str, ...]
    dependabot: tuple[str, ...]
    test_commands: tuple[str, ...]
    # What installing from the lockfile looks like in CI, as regular
    # expressions. A register fact from contract 8 (§ H3): `ci-installs-frozen`
    # knew python and node, so every other ecosystem passed it vacuously — the
    # same two-key map ADR 0018 moved out of `lockfile_present_and_tracked`,
    # left standing in the assert next to it.
    frozen_install: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConfigLocation:
    """Where a gate tool's configuration may live.

    `section` names a table within the file. A file existing is not the same as
    the tool being configured in it — `pyproject.toml` is present in every
    Python repository and says nothing about ruff until `[tool.ruff]` is.
    """

    file: str
    section: str | None = None


@dataclass(frozen=True)
class Gate:
    """A tool that enforces one control for one stack, and how each locus runs it.

    A register fact from contract 6 (ADR 0018). Which linter is mandated, where
    its configuration lives, which editor extension serves it and how CI invokes
    it all answer *yes* to the boundary test: a reasonable Equal Experts
    repository could need any of them to differ without the checker changing.
    They were a dictionary inside the checker, so "the standard mandates ruff"
    was a fact no reviewer could find and no `review_by` could surface.

    `pre_commit` and `editor_extension` are optional in the schema but not in
    practice: the validator requires whichever the controls that use this role
    declare in their `locus:`, so a control claiming an editor locus cannot rest
    on a gate that names no extension.
    """

    role: str
    tool: str
    invocation: str
    config: tuple[ConfigLocation, ...]
    pre_commit: str | None = None
    editor_extension: str | None = None
    strict_key: str | None = None
    # Where the tool's allow-list lives, as a dotted path from the config file's
    # root. ADR 0019 applied to a coverage list: `files = [...]` is an exemption
    # whose entries are what it does *not* name, so nothing to read means
    # nothing to check. Omitting it asserts the tool has no allow-list.
    coverage_key: str | None = None


@dataclass(frozen=True)
class Stack:
    """A technology stack, detected by the predicate its name refers to.

    Keyed by predicate so that a control's `applies_to: [python, typescript]`
    and the stacks below are the same statement made once, evaluated against
    files and never self-declared.
    """

    name: str
    gates: dict[str, Gate]
    # The tracked files this stack's gates are claimed to cover.
    source_globs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Control:
    id: str
    title: str
    enforces: str
    standard: Standard
    tier: int
    rung: str
    locus: tuple[str, ...]
    applies_to: tuple[str, ...]
    verify: tuple[VerifyBlock, ...]
    owner: str
    variance: str
    baseline: str | None
    review_by: datetime.date
    rationale_adr: str
    deployed_by: str | None = None


@dataclass(frozen=True)
class MetaControl:
    id: str
    title: str
    enforces: str
    rationale: str
    verify: tuple[VerifyBlock, ...]


@dataclass(frozen=True)
class Register:
    path: Path
    version: str
    owner: str
    register_contract: int
    predicates: dict[str, bool | str]
    controls: tuple[Control, ...]
    meta_controls: tuple[MetaControl, ...]
    tools: dict[str, Tool] = field(default_factory=dict)
    ecosystems: dict[str, Ecosystem] = field(default_factory=dict)
    stacks: dict[str, Stack] = field(default_factory=dict)
    suppression: tuple[str, ...] = ()
    # Static cloud credentials SEC-002 forbids. A register fact from contract 8
    # (ADR 0018's fourth pass): the ratified decision classified these as a
    # register fact in the first place, and the move was never made (§ H4).
    cloud_credentials: tuple[str, ...] = ()

    def gates(self, role: str) -> dict[str, Gate]:
        """Every stack's gate for `role`, keyed by stack name."""
        return {
            name: stack.gates[role] for name, stack in self.stacks.items() if role in stack.gates
        }

    def control(self, control_id: str) -> Control | MetaControl | None:
        for control in self.controls:
            if control.id == control_id:
                return control
        for meta in self.meta_controls:
            if meta.id == control_id:
                return meta
        return None


class _Validator:
    def __init__(self, register_path: Path) -> None:
        self.register_path = register_path
        self.errors: list[SchemaError] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(SchemaError(where, message))

    def _block_predicates(self, raw: object, where: str) -> tuple[str, ...]:
        """Predicates narrowing a single verify block to one repository shape.

        Validated against the *control's* own `applies_to` afterwards, in
        `_blocks_narrow_within_their_control` — a block naming a predicate its
        control does not is a block that can never run, which is exactly the
        declared-but-unreachable shape the register exists to catch.
        """
        if raw is None:
            return ()
        if not isinstance(raw, list) or not raw:
            self.error(where, "must be a non-empty list of predicate names")
            return ()
        names: list[str] = []
        for entry in raw:
            if not isinstance(entry, str) or not entry.strip():
                self.error(where, "must contain only predicate names")
                return ()
            names.append(entry.strip())
        return tuple(names)

    def _verify_blocks(
        self, raw: Any, where: str, *, meta_id: str | None = None
    ) -> tuple[VerifyBlock, ...]:
        if not isinstance(raw, list) or not raw:
            self.error(where, "must be a non-empty list of verification blocks")
            return ()
        blocks: list[VerifyBlock] = []
        for i, block in enumerate(raw):
            here = f"{where}[{i}]"
            if not isinstance(block, dict):
                self.error(here, "must be a mapping")
                continue
            self._unknown_keys(block, _BLOCK_ALLOWED, here)
            kind = block.get("kind")
            if kind not in KINDS:
                self.error(f"{here}.kind", f"must be one of {', '.join(KINDS)}, got {kind!r}")
                continue
            partial = self._partial(block.get("partial"), f"{here}.partial")
            block_predicates = self._block_predicates(block.get("applies_to"), f"{here}.applies_to")
            if kind == "command":
                run = block.get("run")
                if not isinstance(run, str) or not run.strip():
                    self.error(f"{here}.run", "kind: command requires a non-empty run string")
                    continue
                if match := _SHELL_OPERATOR.search(run):
                    self.error(
                        f"{here}.run",
                        f"contains the shell operator {match.group(0)!r}, but run strings are "
                        "executed without a shell — it would become a literal argument, not an "
                        "operator. Split it into one block per command",
                    )
                    continue
                if run.strip().startswith("standard-check assert "):
                    self.error(
                        f"{here}.run",
                        "an in-process assertion is `kind: file` with an `assert:` name, not a "
                        "command. Declaring it a command is what let GOV-001 read it as a "
                        "reachable CI step while the file asserts beside it were invisible",
                    )
                    continue
                # `standard-check meta GOV-NNN` is the one in-process assertion
                # the `kind:` taxonomy admits as a command, and only here. A
                # meta-control carries a three-valued Verdict (ADR 0016), which
                # a `kind: file` assert's boolean cannot express, so the shape
                # is forced rather than chosen — see docs/01-register-schema.md
                # § The one exception. Bounding it is what keeps it an exception
                # rather than a hole: a *control* using this spelling would be
                # the § E miscategorisation again, in the branch GOV-001 reads.
                if match := _SELF_META.match(run.strip()):
                    if meta_id is None:
                        self.error(
                            f"{here}.run",
                            "only a meta-control may verify itself by self-invocation; a "
                            "control's in-process assertion is `kind: file` with an "
                            "`assert:` name",
                        )
                        continue
                    if match.group(1) != meta_id:
                        self.error(
                            f"{here}.run",
                            f"runs {match.group(1)}'s check under {meta_id}, so the verdict "
                            "rendered would be another control's — a meta-control verifies "
                            "itself",
                        )
                        continue
                blocks.append(
                    VerifyBlock(
                        kind="command",
                        run=run.strip(),
                        partial=partial,
                        applies_to=block_predicates,
                    )
                )
                continue
            name = block.get("assert")
            if not isinstance(name, str):
                self.error(f"{here}.assert", f"kind: {kind} requires an assert name")
                continue
            known = ASSERTS.keys() if kind == "file" else REMOTE_ASSERTS
            if name not in known:
                self.error(
                    f"{here}.assert",
                    f"unknown assert name '{name}' (kind: {kind}) — known: "
                    + ", ".join(sorted(known)),
                )
                continue
            args = block.get("args", {})
            if not isinstance(args, dict):
                self.error(f"{here}.args", "must be a mapping")
                continue
            # The runner supplies the id of the control a block belongs to, so
            # an assert that reads a stamp back knows whose stamp. A register
            # that wrote it here would be stating a control's own id inside its
            # own entry — a second copy of it in the file that exists to prevent
            # second copies, and free to name a different control than the one
            # it sits under.
            if CONTROL_ARG in args:
                self.error(
                    f"{here}.args.{CONTROL_ARG}",
                    "is supplied by the checker from the control this block sits "
                    "under — naming it here would be a second copy of the id",
                )
                continue
            blocks.append(
                VerifyBlock(
                    kind=kind,
                    assert_name=name,
                    args=dict(args),
                    partial=partial,
                    applies_to=block_predicates,
                )
            )
        return tuple(blocks)

    def _partial(self, raw: Any, where: str) -> Partial | None:
        """ADR 0017's declaration that a block is not fully implemented."""
        if raw is None:
            return None
        if not isinstance(raw, dict):
            self.error(where, "must be a mapping with 'unverified' and 'expires'")
            return None
        self._unknown_keys(raw, _PARTIAL_ALLOWED, where)
        unverified = raw.get("unverified")
        if not isinstance(unverified, str) or not unverified.strip():
            self.error(
                f"{where}.unverified",
                "must name the property this block cannot yet verify — an unnamed "
                "gap is the silence the annotation exists to end",
            )
            unverified = None
        expires = raw.get("expires")
        if isinstance(expires, str):
            try:
                expires = datetime.date.fromisoformat(expires)
            except ValueError:
                self.error(f"{where}.expires", f"must be an ISO date, got {expires!r}")
                expires = None
        elif not isinstance(expires, datetime.date):
            self.error(
                f"{where}.expires",
                "a partial declaration requires an expiry — without one it becomes "
                f"permanent, got {expires!r}",
            )
            expires = None
        if unverified is None or not isinstance(expires, datetime.date):
            return None
        return Partial(unverified=unverified.strip(), expires=expires)

    def _unknown_keys(self, raw: dict[str, Any], allowed: tuple[str, ...], where: str) -> None:
        for key in raw:
            if key not in allowed:
                self.error(
                    f"{where}.{key}",
                    f"unknown key — allowed here: {', '.join(sorted(allowed))}",
                )

    def _require(self, raw: dict[str, Any], names: tuple[str, ...], where: str) -> bool:
        missing = [n for n in names if n not in raw]
        for name in missing:
            self.error(f"{where}.{name}", "required field is missing")
        return not missing

    def _control(self, raw: Any, where: str, predicates: dict[str, bool | str]) -> Control | None:
        if not isinstance(raw, dict):
            self.error(where, "must be a mapping")
            return None
        control_id = raw.get("id")
        if isinstance(control_id, str) and _CONTROL_ID.match(control_id):
            where = f"{where} ({control_id})"
        else:
            self.error(f"{where}.id", f"must match AAA-NNN, got {control_id!r}")
        self._unknown_keys(raw, _CONTROL_ALLOWED, where)
        if not self._require(raw, _CONTROL_REQUIRED, where):
            return None
        before = len(self.errors)

        tier = raw["tier"]
        if tier not in (1, 2, 3):
            self.error(f"{where}.tier", f"must be 1, 2 or 3, got {tier!r}")
        rung = raw["rung"]
        if rung not in RUNGS:
            self.error(f"{where}.rung", f"must be one of {', '.join(RUNGS)}, got {rung!r}")
        locus = raw["locus"]
        if not isinstance(locus, list) or not locus or any(x not in LOCI for x in locus):
            self.error(f"{where}.locus", f"must be a non-empty subset of {', '.join(LOCI)}")
        applies_to = raw["applies_to"]
        if not isinstance(applies_to, list) or not applies_to:
            self.error(f"{where}.applies_to", "must be a non-empty list of predicate names")
        else:
            for name in applies_to:
                if name not in predicates:
                    self.error(f"{where}.applies_to", f"unknown predicate '{name}'")
        standard = raw["standard"]
        if (
            not isinstance(standard, dict)
            or not isinstance(standard.get("name"), str)
            or not isinstance(standard.get("url"), str)
        ):
            self.error(f"{where}.standard", "must be a mapping with 'name' and 'url'")
        else:
            self._unknown_keys(standard, _STANDARD_ALLOWED, f"{where}.standard")
            if not str(standard["url"]).startswith(("http://", "https://")):
                self.error(
                    f"{where}.standard.url", f"must be an http(s) URL, got {standard['url']!r}"
                )
        # `also_see` was accepted and validated by nothing before contract 3 —
        # unknown keys were permitted, so a field carrying external URLs was
        # exempt from the rule that every URL in the register resolves.
        also_see = raw.get("also_see", [])
        if not isinstance(also_see, list):
            self.error(f"{where}.also_see", "must be a list of {name, url} mappings")
        else:
            for j, entry in enumerate(also_see):
                at = f"{where}.also_see[{j}]"
                if (
                    not isinstance(entry, dict)
                    or not isinstance(entry.get("name"), str)
                    or not isinstance(entry.get("url"), str)
                ):
                    self.error(at, "must be a mapping with 'name' and 'url'")
                    continue
                self._unknown_keys(entry, _STANDARD_ALLOWED, at)
                if not str(entry["url"]).startswith(("http://", "https://")):
                    self.error(f"{at}.url", f"must be an http(s) URL, got {entry['url']!r}")
        variance = raw["variance"]
        if variance not in VARIANCES:
            self.error(
                f"{where}.variance", f"must be one of {', '.join(VARIANCES)}, got {variance!r}"
            )
        baseline = raw["baseline"]
        if baseline is not None and not isinstance(baseline, str):
            self.error(f"{where}.baseline", "must be a path or null")
        if tier == 1 and baseline is not None:
            self.error(
                f"{where}.baseline",
                "Tier-1 controls carry baseline: null by design — a control that "
                "cannot be met at birth does not belong in Tier 1",
            )
        review_by = raw["review_by"]
        if isinstance(review_by, str):
            try:
                review_by = datetime.date.fromisoformat(review_by)
            except ValueError:
                self.error(f"{where}.review_by", f"must be an ISO date, got {review_by!r}")
        elif not isinstance(review_by, datetime.date):
            self.error(f"{where}.review_by", f"must be an ISO date, got {review_by!r}")
        rationale_adr = raw["rationale_adr"]
        if not isinstance(rationale_adr, str):
            self.error(f"{where}.rationale_adr", "must be a path")
        elif not (self.register_path.parent / rationale_adr).is_file():
            self.error(f"{where}.rationale_adr", f"file does not exist: {rationale_adr}")
        for text_field in ("title", "enforces", "owner"):
            if not isinstance(raw[text_field], str) or not str(raw[text_field]).strip():
                self.error(f"{where}.{text_field}", "must be a non-empty string")
        verify = self._verify_blocks(raw["verify"], f"{where}.verify")
        deployed_by = str(raw["deployed_by"]) if raw.get("deployed_by") is not None else None
        self._stamp_names_the_deploying_gate(verify, deployed_by, where)

        if len(self.errors) > before or not verify:
            return None
        return Control(
            id=str(control_id),
            title=str(raw["title"]).strip(),
            enforces=str(raw["enforces"]).strip(),
            standard=Standard(name=str(standard["name"]), url=str(standard["url"])),
            tier=int(tier),
            rung=str(rung),
            locus=tuple(str(x) for x in locus),
            applies_to=tuple(str(x) for x in applies_to),
            verify=verify,
            owner=str(raw["owner"]),
            variance=str(variance),
            baseline=baseline,
            review_by=review_by,
            rationale_adr=str(rationale_adr),
            deployed_by=deployed_by,
        )

    def _stamp_names_the_deploying_gate(
        self, verify: tuple[VerifyBlock, ...], deployed_by: str | None, where: str
    ) -> None:
        """`provenance_stamp_present` reads back the gate `deployed_by` names.

        Two fields in one control entry would otherwise say who deploys it, free
        to drift apart — a second copy of a rule inside the register itself,
        which is theme T-2 in the one file that exists to prevent it. That the
        two must agree is a property of the register format rather than of any
        repository, so it is the checker's (ADR 0018): no reasonable Equal
        Experts repository needs a stamp assert to read back a different gate
        from the one recorded as writing its artefacts.
        """
        for i, block in enumerate(verify):
            if block.assert_name != "provenance_stamp_present":
                continue
            named = block.args.get("skill")
            if deployed_by is None:
                self.error(
                    f"{where}.verify[{i}].args.skill",
                    "reads back a provenance stamp, but the control names no "
                    "`deployed_by` — the gate that writes an artefact is what the "
                    "stamp records",
                )
            elif named != deployed_by:
                self.error(
                    f"{where}.verify[{i}].args.skill",
                    f"is {named!r}, but the control is deployed_by {deployed_by!r} — "
                    "a stamp is read back from the gate that writes it",
                )

    def _meta_control(self, raw: Any, where: str) -> MetaControl | None:
        if not isinstance(raw, dict):
            self.error(where, "must be a mapping")
            return None
        meta_id = raw.get("id")
        if isinstance(meta_id, str) and _META_ID.match(meta_id):
            where = f"{where} ({meta_id})"
        else:
            self.error(f"{where}.id", f"must match GOV-NNN, got {meta_id!r}")
        for name in _META_FORBIDDEN:
            if name in raw:
                self.error(
                    f"{where}.{name}",
                    "meta-controls carry no tier, rung, locus, variance or baseline — "
                    "they are unconditionally blocking wherever the checker runs",
                )
        self._unknown_keys(raw, _META_ALLOWED, where)
        if not self._require(raw, _META_REQUIRED, where):
            return None
        before = len(self.errors)
        for text_field in ("title", "enforces", "rationale"):
            if not isinstance(raw[text_field], str) or not str(raw[text_field]).strip():
                self.error(f"{where}.{text_field}", "must be a non-empty string")
        verify = self._verify_blocks(
            raw["verify"],
            f"{where}.verify",
            meta_id=meta_id if isinstance(meta_id, str) else "",
        )
        if len(self.errors) > before or not verify:
            return None
        return MetaControl(
            id=str(meta_id),
            title=str(raw["title"]).strip(),
            enforces=str(raw["enforces"]).strip(),
            rationale=str(raw["rationale"]).strip(),
            verify=verify,
        )

    def validate(self, raw: Any) -> Register | None:
        if not isinstance(raw, dict):
            self.error("(document)", "the register must be a YAML mapping")
            return None
        self._unknown_keys(raw, _DOCUMENT_ALLOWED, "(document)")
        version = raw.get("version")
        if not isinstance(version, str) or not _SEMVER.match(version):
            self.error("version", f"must be a semver string, got {version!r}")
        meta = raw.get("meta")
        owner, contract = "", 0
        if not isinstance(meta, dict):
            self.error("meta", "required mapping is missing")
        else:
            self._unknown_keys(meta, _METADATA_ALLOWED, "meta")
            if not isinstance(meta.get("owner"), str):
                self.error("meta.owner", "must be a string")
            else:
                owner = meta["owner"]
            if not isinstance(meta.get("register_contract"), int) or isinstance(
                meta.get("register_contract"), bool
            ):
                self.error("meta.register_contract", "must be an integer")
            else:
                contract = meta["register_contract"]
        tools: dict[str, Tool] = {}
        tools_raw = raw.get("tools") or {}
        if not isinstance(tools_raw, dict):
            self.error("tools", "must be a mapping of tool name to {version, sha256}")
        else:
            for name, entry in tools_raw.items():
                at = f"tools.{name}"
                if not isinstance(entry, dict):
                    self.error(at, "must be a mapping with a 'version'")
                    continue
                self._unknown_keys(entry, _TOOL_ALLOWED, at)
                source = entry.get("source")
                if source not in _TOOL_SOURCES:
                    self.error(
                        f"{at}.source",
                        f"must be one of {', '.join(_TOOL_SOURCES)}, got {source!r}",
                    )
                    continue
                # Deliberately not named `version`: that is the register's own
                # version, bound above and read below.
                tool_version = entry.get("version")
                lockfile = entry.get("lockfile")
                if source == "lockfile":
                    if tool_version is not None:
                        self.error(
                            f"{at}.version",
                            "a lockfile-sourced tool carries no version here — the lockfile "
                            "is the authority, and a copy beside it is the drift this "
                            "field exists to prevent",
                        )
                        continue
                    if not isinstance(lockfile, str) or not lockfile.strip():
                        self.error(f"{at}.lockfile", "must name the lockfile that owns the version")
                        continue
                elif not isinstance(tool_version, str) or not tool_version.strip():
                    self.error(f"{at}.version", f"must be a non-empty string, got {tool_version!r}")
                    continue
                sha = entry.get("sha256")
                if sha is not None and (
                    not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha)
                ):
                    self.error(f"{at}.sha256", "must be 64 lowercase hex characters")
                    continue
                pinned_at = self._pinned_at(entry.get("pinned_at"), str(source), at)
                if pinned_at is None:
                    continue
                invocation = entry.get("invocation")
                if source == "lockfile" and (
                    not isinstance(invocation, str) or not invocation.strip()
                ):
                    self.error(
                        f"{at}.invocation",
                        "a lockfile-sourced tool must record how a locus reaches the pinned "
                        "artefact — an authority no invocation resolves to is not an authority",
                    )
                    continue
                release_repo = entry.get("release_repo")
                if release_repo is not None and not (
                    isinstance(release_repo, str) and re.fullmatch(r"[\w.-]+/[\w.-]+", release_repo)
                ):
                    self.error(f"{at}.release_repo", "must be an owner/name repository reference")
                    continue
                if source == "lockfile" and release_repo is not None:
                    self.error(
                        f"{at}.release_repo",
                        "a lockfile-sourced tool is installed by its package manager, so it has "
                        "no release to download",
                    )
                    continue
                if source == "literal" and invocation is not None:
                    self.error(
                        f"{at}.invocation",
                        "a literal tool is installed onto PATH at each locus, so its pin is the "
                        "version recorded here and not the path it is reached by",
                    )
                    continue
                tools[str(name)] = Tool(
                    name=str(name),
                    source=str(source),
                    version=tool_version.strip() if isinstance(tool_version, str) else None,
                    sha256=sha,
                    lockfile=str(lockfile) if isinstance(lockfile, str) else None,
                    pinned_at=pinned_at,
                    invocation=invocation.strip() if isinstance(invocation, str) else None,
                    release_repo=release_repo,
                )
        ecosystems: dict[str, Ecosystem] = {}
        ecosystems_raw = raw.get("ecosystems") or {}
        if not isinstance(ecosystems_raw, dict):
            self.error("ecosystems", "must be a mapping of ecosystem name to its file sets")
        else:
            for name, entry in ecosystems_raw.items():
                at = f"ecosystems.{name}"
                if not isinstance(entry, dict):
                    self.error(at, "must be a mapping")
                    continue
                self._unknown_keys(entry, _ECOSYSTEM_ALLOWED, at)
                fields: dict[str, tuple[str, ...]] = {}
                for key in _ECOSYSTEM_ALLOWED:
                    value = entry.get(key)
                    if not isinstance(value, list) or not value:
                        self.error(f"{at}.{key}", "must be a non-empty list of strings")
                        break
                    if any(not isinstance(x, str) for x in value):
                        self.error(f"{at}.{key}", "must contain only strings")
                        break
                    # Compiled here rather than at first use: a pattern that
                    # does not parse would otherwise be a crash mid-run, and one
                    # that parses but is never reached is a control passing
                    # vacuously — the failure this field was added to stop.
                    if key == "frozen_install":
                        broken = self._uncompilable(value, f"{at}.{key}")
                        if broken:
                            break
                    fields[key] = tuple(str(x) for x in value)
                else:
                    ecosystems[str(name)] = Ecosystem(name=str(name), **fields)
        predicates_raw = raw.get("predicates")
        predicates: dict[str, bool | str] = {}
        if not isinstance(predicates_raw, dict) or not predicates_raw:
            self.error("predicates", "required non-empty mapping is missing")
        else:
            for name, expr in predicates_raw.items():
                if not isinstance(expr, bool | str):
                    self.error(f"predicates.{name}", f"must be a string or boolean, got {expr!r}")
                    continue
                try:
                    compile_predicate(expr)
                except PredicateSyntaxError as exc:
                    self.error(f"predicates.{name}", str(exc))
                    continue
                predicates[str(name)] = expr
        stacks = self._stacks(raw["stacks"], predicates) if "stacks" in raw else {}
        suppression = self._suppression(raw["suppression"]) if "suppression" in raw else ()
        cloud_credentials = (
            self._cloud_credentials(raw["cloud_credentials"])
            if "cloud_credentials" in raw
            else ()
        )
        controls_raw = raw.get("controls")
        controls: list[Control] = []
        if not isinstance(controls_raw, list) or not controls_raw:
            self.error("controls", "required non-empty list is missing")
        else:
            for i, entry in enumerate(controls_raw):
                control = self._control(entry, f"controls[{i}]", predicates)
                if control is not None:
                    controls.append(control)
        meta_raw = raw.get("meta_controls")
        meta_controls: list[MetaControl] = []
        if not isinstance(meta_raw, list):
            self.error("meta_controls", "required list is missing")
        else:
            for i, entry in enumerate(meta_raw):
                meta_control = self._meta_control(entry, f"meta_controls[{i}]")
                if meta_control is not None:
                    meta_controls.append(meta_control)
        seen: set[str] = set()
        for control_id in [c.id for c in controls] + [m.id for m in meta_controls]:
            if control_id in seen:
                self.error("controls", f"duplicate control id '{control_id}'")
            seen.add(control_id)
        self._gates_cover_declared_loci(controls, stacks)
        self._blocks_narrow_within_their_control(controls, predicates)
        if self.errors:
            return None
        return Register(
            path=self.register_path,
            version=str(version),
            owner=owner,
            register_contract=contract,
            predicates=predicates,
            controls=tuple(controls),
            meta_controls=tuple(meta_controls),
            tools=tools,
            ecosystems=ecosystems,
            stacks=stacks,
            suppression=suppression,
            cloud_credentials=cloud_credentials,
        )

    def _config_locations(self, raw: object, at: str) -> tuple[ConfigLocation, ...]:
        if not isinstance(raw, list) or not raw:
            self.error(at, "must be a non-empty list of {file, section?} mappings")
            return ()
        found: list[ConfigLocation] = []
        for i, entry in enumerate(raw):
            here = f"{at}[{i}]"
            if not isinstance(entry, dict):
                self.error(here, "must be a mapping")
                continue
            self._unknown_keys(entry, _CONFIG_ALLOWED, here)
            file = entry.get("file")
            if not isinstance(file, str) or not file.strip():
                self.error(f"{here}.file", "must name a configuration file")
                continue
            section = entry.get("section")
            if section is not None and (not isinstance(section, str) or not section.strip()):
                self.error(f"{here}.section", "must be a non-empty string when present")
                continue
            found.append(ConfigLocation(file=file, section=section))
        return tuple(found)

    def _gate(self, raw: object, role: str, at: str) -> Gate | None:
        if not isinstance(raw, dict):
            self.error(at, "must be a mapping")
            return None
        self._unknown_keys(raw, _GATE_ALLOWED, at)
        for key in _GATE_REQUIRED:
            if key not in raw:
                self.error(f"{at}.{key}", "is required")
                return None
        strings: dict[str, str] = {}
        for key in ("tool", "invocation"):
            value = raw.get(key)
            if not isinstance(value, str) or not value.strip():
                self.error(f"{at}.{key}", "must be a non-empty string")
                return None
            strings[key] = value.strip()
        optional: dict[str, str | None] = {}
        for key in ("pre_commit", "editor_extension", "strict_key", "coverage_key"):
            value = raw.get(key)
            if value is None:
                optional[key] = None
                continue
            if not isinstance(value, str) or not value.strip():
                self.error(f"{at}.{key}", "must be a non-empty string when present")
                return None
            optional[key] = value.strip()
        config = self._config_locations(raw.get("config"), f"{at}.config")
        if not config:
            return None
        return Gate(
            role=role,
            tool=strings["tool"],
            invocation=strings["invocation"],
            config=config,
            pre_commit=optional["pre_commit"],
            editor_extension=optional["editor_extension"],
            strict_key=optional["strict_key"],
            coverage_key=optional["coverage_key"],
        )

    def _stacks(self, raw: object, predicates: dict[str, bool | str]) -> dict[str, Stack]:
        """Per-stack gate tools, keyed by the predicate that detects the stack."""
        if not isinstance(raw, dict):
            self.error("stacks", "must be a mapping of stack name to its gates")
            return {}
        stacks: dict[str, Stack] = {}
        for name, entry in raw.items():
            at = f"stacks.{name}"
            # The key is the predicate. A stack nothing can detect is a stack
            # that never applies, which is theme T-3 in the register itself.
            if str(name) not in predicates:
                self.error(at, f"names no predicate — known: {', '.join(sorted(predicates))}")
                continue
            if not isinstance(entry, dict):
                self.error(at, "must be a mapping")
                continue
            self._unknown_keys(entry, _STACK_ALLOWED, at)
            gates_raw = entry.get("gates")
            if not isinstance(gates_raw, dict) or not gates_raw:
                self.error(f"{at}.gates", "must be a non-empty mapping of role to gate")
                continue
            gates: dict[str, Gate] = {}
            for role, gate_raw in gates_raw.items():
                here = f"{at}.gates.{role}"
                if str(role) not in _GATE_ROLES:
                    self.error(here, f"must be one of {', '.join(_GATE_ROLES)}")
                    continue
                gate = self._gate(gate_raw, str(role), here)
                if gate is not None:
                    gates[str(role)] = gate
            globs = entry.get("source_globs")
            if not isinstance(globs, list) or not globs or any(
                not isinstance(g, str) or not g.strip() for g in globs
            ):
                # Required, because a gate that declares a `coverage_key` has
                # nothing to compare its allow-list against without it — and an
                # uncomparable allow-list is the silence ADR 0019 removes.
                self.error(f"{at}.source_globs", "must be a non-empty list of file globs")
                continue
            if gates:
                stacks[str(name)] = Stack(
                    name=str(name),
                    gates=gates,
                    source_globs=tuple(g.strip() for g in globs),
                )
        return stacks

    # Which gate field each locus is verified through. A control declaring a
    # locus that its gate cannot express is the T-3 shape the register exists to
    # stop: declared, and unverifiable by construction.
    _LOCUS_FIELD: ClassVar[dict[str, str]] = {
        "editor": "editor_extension",
        "pre-commit": "pre_commit",
    }

    def _gates_cover_declared_loci(
        self, controls: list[Control], stacks: dict[str, Stack]
    ) -> None:
        """Every locus a role-driven control declares is expressible by its gates.

        Checked here, once, rather than at every run: a control claiming an
        `editor` locus while its gate names no extension would otherwise either
        fail every repository or — worse — be quietly skipped, and which of those
        happened would depend on how the assert was written.
        """
        for control in controls:
            roles = {
                str(block.args["role"])
                for block in control.verify
                if isinstance(block.args.get("role"), str)
            }
            for role in sorted(roles):
                for stack_name in control.applies_to:
                    stack = stacks.get(stack_name)
                    if stack is None:
                        continue  # `always`, or a predicate with no gate tooling
                    at = f"stacks.{stack_name}.gates.{role}"
                    gate = stack.gates.get(role)
                    if gate is None:
                        self.error(
                            at,
                            f"is missing, but {control.id} applies to '{stack_name}' and "
                            f"verifies through role '{role}'",
                        )
                        continue
                    for locus in control.locus:
                        field_name = self._LOCUS_FIELD.get(locus)
                        if field_name and getattr(gate, field_name) is None:
                            self.error(
                                f"{at}.{field_name}",
                                f"is required: {control.id} declares a '{locus}' locus, "
                                "which is verified through this field",
                            )

    def _blocks_narrow_within_their_control(
        self, controls: list[Control], predicates: dict[str, bool | str]
    ) -> None:
        """A block's `applies_to` narrows its control's — it cannot widen it.

        A block naming a predicate its control does not can never run: the
        control is skipped before the block is reached. That is a verification
        declared and unreachable, which is theme T-3 in the one file that exists
        to stop it, so it is a schema error rather than a silent no-op.
        """
        for control in controls:
            for i, block in enumerate(control.verify):
                at = f"{control.id}.verify[{i}].applies_to"
                for name in block.applies_to:
                    if name not in predicates:
                        self.error(
                            at,
                            f"names no predicate — known: {', '.join(sorted(predicates))}",
                        )
                    elif name not in control.applies_to:
                        self.error(
                            at,
                            f"names '{name}', which {control.id} does not apply to "
                            f"({', '.join(control.applies_to)}) — the block could never run",
                        )

    def _uncompilable(self, patterns: list[Any], at: str) -> bool:
        """Report any entry that is not a valid regular expression."""
        broken = False
        for i, pattern in enumerate(patterns):
            try:
                re.compile(str(pattern))
            except re.error as exc:
                self.error(f"{at}[{i}]", f"is not a valid regular expression: {exc}")
                broken = True
        return broken

    def _pinned_at(self, raw: object, source: str, at: str) -> tuple[str, ...] | None:
        """The loci that repeat a `literal` tool's version. None on error.

        Required under `source: literal` and rejected under `source: lockfile`,
        which is the same asymmetry as `version:` and for the same reason: a
        lockfile-sourced tool has no version at any locus to keep in step, so a
        list of loci here would describe repetitions that do not exist.

        Required rather than optional because an empty list is indistinguishable
        from a tool nobody pins, and "nothing was compared" reading as a pass is
        the § A defect this field was moved out of the checker to stop.
        """
        if source == "lockfile":
            if raw is not None:
                self.error(
                    f"{at}.pinned_at",
                    "a lockfile-sourced tool has no version at any locus to keep in step, so "
                    "there are no loci to list",
                )
                return None
            return ()
        if not isinstance(raw, list) or not raw:
            self.error(
                f"{at}.pinned_at",
                "a literal tool must list every locus that repeats its version — the loci are "
                "a property of the repository, not of the checker (ADR 0018)",
            )
            return None
        sites: list[str] = []
        for i, entry in enumerate(raw):
            if not isinstance(entry, str) or not entry.strip():
                self.error(f"{at}.pinned_at[{i}]", "must be a non-empty path")
                return None
            sites.append(entry.strip())
        return tuple(sites)

    def _cloud_credentials(self, raw: object) -> tuple[str, ...]:
        """Secret names SEC-002 forbids a workflow from referencing."""
        if not isinstance(raw, list) or not raw:
            self.error(
                "cloud_credentials",
                "must be a non-empty list of credential names — an empty list is a control "
                "that looks for nothing",
            )
            return ()
        names: list[str] = []
        for i, entry in enumerate(raw):
            if not isinstance(entry, str) or not entry.strip():
                self.error(f"cloud_credentials[{i}]", "must be a non-empty string")
                continue
            names.append(entry.strip())
        return tuple(names)

    def _suppression(self, raw: object) -> tuple[str, ...]:
        """Patterns that count as swallowing a failure.

        Validated as regular expressions here rather than at first use: a
        pattern that does not compile would otherwise surface as a crash in the
        middle of a run, and the failure mode of a suppression list that silently
        matches nothing is a green report over a suppressed gate.
        """
        if not isinstance(raw, list) or not raw:
            self.error("suppression", "must be a non-empty list of regular expressions")
            return ()
        patterns: list[str] = []
        for i, entry in enumerate(raw):
            at = f"suppression[{i}]"
            if not isinstance(entry, str) or not entry.strip():
                self.error(at, "must be a non-empty string")
                continue
            try:
                re.compile(entry)
            except re.error as exc:
                self.error(at, f"is not a valid regular expression: {exc}")
                continue
            patterns.append(entry)
        return tuple(patterns)


def load_register(path: Path) -> tuple[Register | None, list[SchemaError]]:
    """Parse and schema-validate the register at `path`."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [SchemaError("(file)", f"cannot read {path}: {exc}")]
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [SchemaError("(document)", f"not parseable as YAML: {exc}")]
    validator = _Validator(path)
    register = validator.validate(raw)
    return register, validator.errors
