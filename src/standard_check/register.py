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
from typing import Any

import yaml

from standard_check.asserts import ASSERTS, REMOTE_ASSERTS
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
    "predicates",
    "controls",
    "meta_controls",
)
_TOOL_ALLOWED = ("version", "sha256")
_ECOSYSTEM_ALLOWED = ("manifest", "lockfiles", "dependabot")
_METADATA_ALLOWED = ("owner", "register_contract")
_STANDARD_ALLOWED = ("name", "url")
_BLOCK_ALLOWED = ("kind", "run", "assert", "args", "partial")
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
    """A pinned tool version — the single definition every locus reads."""

    name: str
    version: str
    sha256: str | None = None


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

    def _verify_blocks(self, raw: Any, where: str) -> tuple[VerifyBlock, ...]:
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
                blocks.append(VerifyBlock(kind="command", run=run.strip(), partial=partial))
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
            blocks.append(
                VerifyBlock(kind=kind, assert_name=name, args=dict(args), partial=partial)
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
            deployed_by=str(raw["deployed_by"]) if raw.get("deployed_by") is not None else None,
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
        verify = self._verify_blocks(raw["verify"], f"{where}.verify")
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
                version = entry.get("version")
                if not isinstance(version, str) or not version.strip():
                    self.error(f"{at}.version", f"must be a non-empty string, got {version!r}")
                    continue
                sha = entry.get("sha256")
                if sha is not None and (
                    not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha)
                ):
                    self.error(f"{at}.sha256", "must be 64 lowercase hex characters")
                    continue
                tools[str(name)] = Tool(name=str(name), version=version.strip(), sha256=sha)
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
        )


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
