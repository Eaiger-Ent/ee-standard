"""Command assertions — the `standard-check assert <name>` closed set.

These are the checks the register invokes as `kind: command` verify blocks.
They read workflow and configuration files; none of them executes anything.
"""

from __future__ import annotations

import configparser
import fnmatch
import re
import tomllib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

import yaml

from standard_check.asserts_file import (
    AssertFn,
    AssertResult,
    _ecosystems_present,
    _fail,
    _ok,
)
from standard_check.predicates import compile_predicate
from standard_check.repo import Repo, load_jsonc

if TYPE_CHECKING:  # `register` imports the assert registries — importing it
    from standard_check.register import (  # at runtime would be circular
        ConfigLocation,
        Gate,
        Register,
        Stack,
    )


@dataclass(frozen=True)
class WorkflowStep:
    path: str
    job: str
    run: str
    uses: str
    suppressed: bool  # continue-on-error on the step or its job
    gating: bool = True  # the workflow runs on push or pull_request


def _truthy(value: object) -> bool:
    """YAML `true`, and the string `"true"`.

    `continue-on-error: "true"` is quoted in real workflows and GitHub honours
    it, so an identity test against `True` read a suppressed step as blocking —
    the exact direction of error LNT-001 and TST-001 exist to catch (§ D).
    """
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _is_gating(doc: dict[Any, Any]) -> bool:
    """Whether this workflow runs on the events that gate a merge.

    `on:` was never read, so a `workflow_dispatch`-only workflow — one that runs
    only when a human clicks it — counted as a CI gate. That is theme T-3 in its
    purest form: declared, and unreachable from the event that matters (§ D).
    """
    # `on:` parses as the YAML 1.1 boolean True, hence checking both keys.
    triggers: object = doc["on"] if "on" in doc else doc.get(True)
    if isinstance(triggers, str):
        return triggers in ("push", "pull_request", "pull_request_target")
    if isinstance(triggers, list):
        return any(str(t) in ("push", "pull_request", "pull_request_target") for t in triggers)
    if isinstance(triggers, dict):
        return any(str(t) in ("push", "pull_request", "pull_request_target") for t in triggers)
    return False


def _workflow_steps(repo: Repo) -> Iterator[WorkflowStep]:
    for path in repo.workflow_files():
        doc = yaml.safe_load(repo.read(path))
        if not isinstance(doc, dict):
            continue
        jobs = doc.get("jobs")
        if not isinstance(jobs, dict):
            continue
        gating = _is_gating(doc)
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            job_suppressed = _truthy(job.get("continue-on-error"))
            # A job-level `uses:` is a reusable workflow call — a real
            # third-party reference that SUP-003 must pin. Walking only
            # `jobs.*.steps` made it invisible (§ D).
            if job.get("uses"):
                yield WorkflowStep(
                    path=path,
                    job=str(job_id),
                    run="",
                    uses=str(job["uses"]),
                    suppressed=job_suppressed,
                    gating=gating,
                )
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                yield WorkflowStep(
                    path=path,
                    job=str(job_id),
                    run=str(step.get("run") or ""),
                    uses=str(step.get("uses") or ""),
                    suppressed=job_suppressed or _truthy(step.get("continue-on-error")),
                    gating=gating,
                )


# The fallback set, used only when the register names none. It exists for the
# same reason `suppression`'s does: an older register should detect something
# rather than nothing, and a SEC-002 that looks for no credential at all is the
# green-over-nothing this repository exists to prevent.
_DEFAULT_CLOUD_CREDENTIALS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GCP_SA_KEY",
    "SERVICE_ACCOUNT_KEY",
    "AZURE_CLIENT_SECRET",
    "AZURE_CREDENTIALS",
)


def _credential_patterns(register: Register) -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Each credential name, matched however a workflow spells it.

    Which names to look for is the register's (ADR 0018, fourth pass — § H4);
    that `AWS_ACCESS_KEY_ID` and `aws-access-key-id:` are the same credential is
    detection implementation and stays here. A case-sensitive substring test
    over the uppercase spellings missed `aws-access-key-id: ${{ secrets.PROD_KEY }}`
    entirely (§ D) — the commonest way the credential actually appears.
    """
    names = register.cloud_credentials or _DEFAULT_CLOUD_CREDENTIALS
    return tuple(
        (name, re.compile(re.escape(name).replace("_", "[-_]"), re.IGNORECASE))
        for name in names
    )


def no_static_cloud_keys(
    repo: Repo,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    patterns = _credential_patterns(register)
    findings: list[str] = []
    for path in repo.workflow_files():
        text = repo.read(path)
        findings.extend(
            f"{path}: references {name}" for name, pattern in patterns if pattern.search(text)
        )
    if findings:
        return _fail("; ".join(findings))
    return _ok(
        f"no workflow references any of the {len(patterns)} static cloud credentials the "
        "register names"
    )


_EXACT_PIN_NPM = re.compile(r"@\d[\w.\-]*$")
_EXACT_PIN_PIP = re.compile(r"==\d[\w.\-]*$")


def _installed_packages(words: list[str]) -> list[str] | None:
    """Package arguments after a literal `install` word, or None if there is none.

    `npm install-ci-test` is a real command whose word boundary satisfies the
    regex while `install` is not itself a word, so this must not assume it is
    present.
    """
    if "install" not in words:
        return None
    return [w for w in words[words.index("install") + 1 :] if not w.startswith("-")]


def _logical_lines(run: str) -> Iterator[str]:
    """Shell lines with backslash continuations joined.

    Iterating physical lines split `pip install \\` from the pinned package on
    the next line, so a conformant install was reported as unpinned (§ D).
    """
    buffer = ""
    for raw_line in run.splitlines():
        line = raw_line.split("#")[0]
        if line.rstrip().endswith("\\"):
            buffer += line.rstrip()[:-1] + " "
            continue
        yield buffer + line
        buffer = ""
    if buffer:
        yield buffer


def _install_offences(run: str) -> Iterator[str]:
    for line in _logical_lines(run):
        for command in re.split(r"&&|\|\||;", line):
            words = command.strip().split()
            if not words:
                continue
            text = " ".join(words)
            if re.search(r"\buv sync\b", text) and not re.search(r"--(frozen|locked)\b", text):
                yield f"'{text}' re-resolves — use uv sync --frozen"
            elif re.search(r"\b(?:poetry|pdm) install\b", text) and not re.search(
                r"--(?:sync|frozen|no-update|check)\b", text
            ):
                yield f"'{text}' re-resolves — poetry/pdm install must read the lockfile"
            elif re.search(r"\b(uv )?pip3? install\b", text):
                args = _installed_packages(words)
                requirements = re.search(r"-r\s+\S+", text)
                if args and not requirements and any(not _EXACT_PIN_PIP.search(a) for a in args):
                    yield f"'{text}' installs unpinned packages"
            elif re.search(r"\bnpm install\b", text):
                args = _installed_packages(words)
                if args is not None and (
                    not args or any(not _EXACT_PIN_NPM.search(a) for a in args)
                ):
                    yield f"'{text}' re-resolves — use npm ci or an exact-pinned install"
            elif re.search(r"\byarn install\b", text) and "--immutable" not in text:
                yield f"'{text}' re-resolves — use yarn install --immutable"
            elif re.search(r"\bpnpm install\b", text) and "--frozen-lockfile" not in text:
                yield f"'{text}' re-resolves — use pnpm install --frozen-lockfile"


def ci_installs_frozen(
    repo: Repo,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    """Every ecosystem present installs from its lockfile in a step that gates.

    Both halves were checker-side constants and both are register facts now.
    What a frozen install *looks like* is `ecosystems.<name>.frozen_install`
    (contract 8): this held a two-entry map — python and node — so a repository
    with a `go.mod`, a `Cargo.toml` or a `Gemfile` was told "every CI install is
    frozen or exact-pinned" with nothing checked, which is the map ADR 0018
    called the measured harm surviving in the assert beside the one it was moved
    out of (§ H3).

    The evidence must also come from a step that can fail a merge (§ H1): a
    `uv sync --frozen` in a `workflow_dispatch`-only workflow shows what a human
    can choose to run, not what a merge has to pass.
    """
    offences: list[str] = []
    frozen: set[str] = set()
    present = _ecosystems_present(repo, register)
    compiled = {
        name: [re.compile(pattern) for pattern in ecosystem.frozen_install]
        for name, ecosystem in present.items()
    }
    for step in _workflow_steps(repo):
        # An offence is an offence wherever it runs: a step that re-resolves is
        # not made safe by running on a trigger that gates nothing.
        offences.extend(f"{step.path} ({step.job}): {o}" for o in _install_offences(step.run))
        if not step.gating:
            continue
        for line in _logical_lines(step.run):
            frozen.update(
                name for name, patterns in compiled.items()
                if any(pattern.search(line) for pattern in patterns)
            )
    if offences:
        return _fail("; ".join(offences))
    # An ecosystem whose graph is never installed frozen has not satisfied this
    # control — a TypeScript repo with no workflows at all used to pass it
    # vacuously, because only python was ever required (§ D).
    missing = sorted(name for name in present if name not in frozen)
    if missing:
        return _fail(
            "no gating CI step installs the dependency graph in frozen mode for: "
            + ", ".join(missing)
        )
    if not present:
        return _ok("no package manager detected — nothing to install")
    return _ok(
        "every CI install is frozen or exact-pinned, for: " + ", ".join(sorted(present))
    )


_SHA40 = re.compile(r"^[0-9a-f]{40}$")
# A container action is pinned by image digest, which is 64 hex characters after
# `sha256:`. Requiring 40 rejected `uses: docker://alpine@sha256:<64 hex>` — a
# reference that is pinned as hard as a commit SHA (§ D).
_DOCKER_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def actions_pinned_to_sha(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    owner = repo.owner()
    problems = []
    for step in _workflow_steps(repo):
        uses = step.uses
        if not uses or uses.startswith("./"):
            continue
        action_owner = uses.split("/")[0]
        if owner is not None and action_owner == owner:
            continue
        _, at, ref = uses.rpartition("@")
        pinned = bool(at) and (
            _SHA40.match(ref) is not None
            or (uses.startswith("docker://") and _DOCKER_DIGEST.match(ref) is not None)
        )
        if not pinned:
            problems.append(f"{step.path} ({step.job}): uses {uses}")
    if problems:
        return _fail("not pinned to a commit SHA or image digest: " + "; ".join(problems))
    return _ok("every third-party action reference is pinned by SHA or digest")


def _precommit_hooks(repo: Repo) -> list[dict[str, Any]]:
    if not repo.exists(".pre-commit-config.yaml"):
        return []
    config = yaml.safe_load(repo.read(".pre-commit-config.yaml"))
    if not isinstance(config, dict):
        return []
    return [
        hook
        for repo_block in config.get("repos") or []
        if isinstance(repo_block, dict)
        for hook in repo_block.get("hooks") or []
        if isinstance(hook, dict)
    ]


def _hook_mentions(repo: Repo, token: str) -> bool:
    return any(
        token in str(hook.get("id", "")) or token in str(hook.get("entry", ""))
        for hook in _precommit_hooks(repo)
    )


# A CI step that runs the whole pre-commit suite runs every hook in it, so it
# reaches any gate the pre-commit config wires. Requiring the literal tool string
# failed a repo that lints via `pre-commit run --all-files` (§ D).
_PRE_COMMIT_RUN = re.compile(r"\bpre-commit run\b[^\n]*--all-files\b")


def _ci_run_mentions(repo: Repo, pattern: str, *, hook: str | None = None) -> bool:
    for step in _workflow_steps(repo):
        if not step.gating:
            continue
        if re.search(pattern, step.run):
            return True
        if hook and _PRE_COMMIT_RUN.search(step.run) and _hook_mentions(repo, hook):
            return True
    return False


def _devcontainer_extensions(repo: Repo) -> list[str]:
    """Editor extensions the repo installs, from either place they can live.

    Demanding a devcontainer entry invented a hidden LNT-001 dependency on
    DEV-001's artefact: a repo whose editor locus is `.vscode/extensions.json`,
    with no devcontainer at all, failed a control it satisfied (§ D).
    """
    found: list[str] = []
    if repo.exists(".devcontainer/devcontainer.json"):
        config = load_jsonc(repo.root / ".devcontainer/devcontainer.json")
        if isinstance(config, dict):
            customizations = config.get("customizations")
            vscode = customizations.get("vscode") if isinstance(customizations, dict) else None
            extensions = vscode.get("extensions") if isinstance(vscode, dict) else None
            if isinstance(extensions, list):
                found += [str(e) for e in extensions]
    if repo.exists(".vscode/extensions.json"):
        config = load_jsonc(repo.root / ".vscode/extensions.json")
        if isinstance(config, dict):
            recommendations = config.get("recommendations")
            if isinstance(recommendations, list):
                found += [str(e) for e in recommendations]
    return found


def _config_files(repo: Repo, location: ConfigLocation) -> list[str]:
    """Paths this config location resolves to, in the repository."""
    if repo.exists(location.file):
        return [location.file]
    return repo.glob_basename(location.file)


def _load_config(repo: Repo, path: str) -> Any:
    """A config file parsed by its extension, or None if it cannot be read.

    Knowing that a `.toml` is read with tomllib, an `.ini` with configparser and
    a `.json` with the JSONC reader is detection implementation and stays in the
    checker (ADR 0018).
    """
    try:
        if path.endswith(".toml"):
            return tomllib.loads(repo.read(path))
        if path.endswith((".ini", ".cfg")):
            parser = configparser.ConfigParser()
            parser.read_string(repo.read(path))
            return {name: dict(parser[name]) for name in parser.sections()}
        if path.endswith((".json", ".jsonc")):
            return load_jsonc(repo.root / path)
        return yaml.safe_load(repo.read(path))
    except (OSError, ValueError, configparser.Error, yaml.YAMLError, tomllib.TOMLDecodeError):
        return None


def _walk(doc: Any, dotted: str) -> Any:
    """The value at a dotted path from a document's root, or None."""
    for key in dotted.split("."):
        if not isinstance(doc, dict) or key not in doc:
            return None
        doc = doc[key]
    return doc


def _uncovered_sources(repo: Repo, stack: Stack, gate: Gate) -> list[str]:
    """Tracked source files the gate's own allow-list leaves unchecked.

    ADR 0019 applied to a coverage list rather than an exemption list. An
    exemption list makes an exclusion into a line you can read: `.claude/**` is a
    string, so it can be compared against what git tracks. An allow-list makes an
    exclusion into an *absence* — `files = ["src", "tests"]` excludes `tools/` by
    not mentioning it, so there is nothing to read and no diff when coverage
    shrinks relative to the codebase.

    Measured here rather than reasoned about: a tracked module with a genuine
    type error, which nothing under the four allow-listed paths imported, left
    `uv run mypy` reporting "Success: no issues found" and TYP-001 reporting
    PASS. mypy found the error the moment it was pointed at the file. The config
    chose not to look, and the control claimed "all first-party source".

    Import-reachable files are deliberately *not* credited. mypy does follow
    imports out of the allow-list, so such a file is checked today — by accident
    of somebody importing it, and unchecked again the day that import goes.
    Coverage that can be withdrawn without editing the coverage list is not
    declared coverage.
    """
    if not gate.coverage_key:
        return []  # the tool has no allow-list; its own default is the coverage
    location = next((loc for loc in gate.config if _config_files(repo, loc)), None)
    if location is None:
        return []  # unconfigured: `_wired_problems` already reports that
    path = _config_files(repo, location)[0]
    doc = _load_config(repo, path)
    roots = _walk(doc, gate.coverage_key)
    if not isinstance(roots, list) or not roots:
        return []  # no allow-list set, so nothing is excluded by one
    prefixes = tuple(str(root).rstrip("/") for root in roots)
    uncovered = sorted(
        tracked
        for tracked in repo.tracked
        if any(fnmatch.fnmatch(PurePosixPath(tracked).name, glob) for glob in stack.source_globs)
        and not any(
            tracked == prefix
            or tracked.startswith(f"{prefix}/")
            or fnmatch.fnmatch(tracked, prefix)
            for prefix in prefixes
        )
    )
    if not uncovered:
        return []
    shown = ", ".join(uncovered[:3])
    more = f" and {len(uncovered) - 3} more" if len(uncovered) > 3 else ""
    return [
        f"{path}: {gate.coverage_key} does not cover {len(uncovered)} tracked "
        f"{stack.name} file(s) ({shown}{more}) — {gate.tool} runs over what this "
        "list names, and the control claims all first-party source"
    ]


def _read_section(repo: Repo, location: ConfigLocation) -> dict[str, Any] | None:
    """The mapping a config location points at, or None if it is not there.

    Which file and which section are register facts; knowing that a `.toml` is
    read with tomllib, an `.ini` with configparser and a `.json` with the JSONC
    reader is detection implementation and stays here (ADR 0018). A file with no
    `section` counts as configured by existing — `ruff.toml` is ruff's config
    whatever is inside it.
    """
    for path in _config_files(repo, location):
        doc = _load_config(repo, path)
        if doc is None:
            continue
        if location.section is None:
            return doc if isinstance(doc, dict) else {}
        for key in location.section.split("."):
            if not isinstance(doc, dict) or key not in doc:
                doc = None
                break
            doc = doc[key]
        if isinstance(doc, dict):
            return doc
    return None


def _configured(repo: Repo, gate: Gate) -> dict[str, Any] | None:
    """The first config location that actually configures this gate's tool."""
    for location in gate.config:
        section = _read_section(repo, location)
        if section is not None:
            return section
    return None


def _truthy_setting(value: object) -> bool:
    """A boolean as TOML, JSON, YAML or INI spell it."""
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _applicable_gates(repo: Repo, register: Register, role: str) -> dict[str, Gate]:
    """Gates for `role` whose stack predicate this repository satisfies."""
    return {
        name: gate
        for name, gate in register.gates(role).items()
        if compile_predicate(register.predicates.get(name, False))(repo)
    }


def _wired_problems(repo: Repo, stack: str, gate: Gate) -> list[str]:
    """Where this gate is not wired, across the loci it names."""
    problems = []
    if _configured(repo, gate) is None:
        locations = ", ".join(
            loc.file + (f" [{loc.section}]" if loc.section else "") for loc in gate.config
        )
        problems.append(f"{stack}: no {gate.tool} configuration ({locations})")
    if gate.editor_extension and gate.editor_extension not in _devcontainer_extensions(repo):
        problems.append(
            f"{stack}: editor locus — no editor configuration installs {gate.editor_extension}"
        )
    if gate.pre_commit and not _hook_mentions(repo, gate.pre_commit):
        problems.append(f"{stack}: pre-commit locus — no {gate.pre_commit} hook")
    if not _ci_run_mentions(
        repo, rf"\b{re.escape(gate.invocation)}\b", hook=gate.pre_commit
    ):
        problems.append(f"{stack}: ci locus — no gating step runs {gate.invocation}")
    return problems


def linter_wired_at_all_loci(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """The mandated linter is configured once and wired at every declared locus.

    Which linter, where its configuration lives, its pre-commit hook id and its
    editor extension id all come from the register's `stacks:` (ADR 0018). They
    were a checker-side dictionary knowing ruff and eslint, so "the standard
    mandates ruff" was a decision no reviewer could find.
    """
    role = str(args.get("role", ""))
    if role not in ("lint", "typecheck"):
        return _fail("assert requires a 'role' argument naming a gate in the register")
    gates = _applicable_gates(repo, register, role)
    if not gates:
        return _ok("no stack with a linter gate is present")
    problems = [
        problem
        for stack, gate in sorted(gates.items())
        for problem in _wired_problems(repo, stack, gate)
    ]
    if problems:
        return _fail("; ".join(problems))
    tools = ", ".join(sorted(gate.tool for gate in gates.values()))
    return _ok(f"{tools} wired at every declared locus from one configuration")


# The set moved into the register at contract 6 (ADR 0018): a house idiom the
# checker has not heard of is a suppression that goes undetected, and adding one
# strengthens detection rather than weakening it. `|| :` is the terse spelling of
# `|| true` — `:` is the shell no-op builtin — and its absence from the original
# checker-side set is what let the commonest short idiom through (§ D).
#
# The fallback exists so an older register still detects something rather than
# nothing: a register with no `suppression:` would otherwise make every
# suppressed step invisible, which is the direction of error this control exists
# to catch.
_DEFAULT_SUPPRESSION = (
    r"\|\|\s*true\b",
    r"\|\|\s*:\s*(?:$|[;&|])",
    r"\|\|\s*exit 0\b",
    r"\bset \+e\b",
    r"--exit-zero\b",
)


def _suppression_match(register: Register, text: str) -> str | None:
    """The first suppression idiom found in `text`, if any."""
    for pattern in register.suppression or _DEFAULT_SUPPRESSION:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(0)
    return None


def no_failure_suppression(
    repo: Repo,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    problems = []
    for step in _workflow_steps(repo):
        if step.suppressed:
            target = step.run.strip().splitlines()[0] if step.run.strip() else step.uses
            problems.append(f"{step.path} ({step.job}): continue-on-error on '{target}'")
        if match := _suppression_match(register, step.run):
            problems.append(f"{step.path} ({step.job}): '{match}' in run")
    if problems:
        return _fail("; ".join(problems))
    return _ok("no CI step suppresses a failure")


def _blanket_overrides(repo: Repo, gate: Gate) -> list[str]:
    """Overrides that switch checking off for everything, after enabling it.

    `[[tool.mypy.overrides]]` is the shape of one tool's own configuration
    format, so it stays in the checker (ADR 0018) — but keyed on the register's
    tool name rather than assumed, because a repository that mandates a
    different type checker has no such table to read.
    """
    if gate.tool != "mypy" or not repo.exists("pyproject.toml"):
        return []
    try:
        overrides = (
            tomllib.loads(repo.read("pyproject.toml"))
            .get("tool", {})
            .get("mypy", {})
            .get("overrides", [])
        )
    except (OSError, tomllib.TOMLDecodeError):
        return []
    problems: list[str] = []
    if isinstance(overrides, list):
        for override in overrides:
            if not isinstance(override, dict):
                continue
            modules = override.get("module")
            modules = [modules] if isinstance(modules, str) else (modules or [])
            broad = any(str(m).strip() in ("*", "*.*") for m in modules)
            disabled = override.get("ignore_errors") is True or override.get("follow_imports") in (
                "skip",
                "silent",
            )
            if broad and disabled:
                problems.append(
                    "[[tool.mypy.overrides]] disables checking for every module — "
                    "strict mode is switched off in a second place"
                )
    return problems


def typecheck_strict_and_blocking(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """The mandated type checker is strict, wired, and its exit code is the verdict.

    Which checker, where its configuration lives and which key turns strictness
    on are register facts (ADR 0018). `strict_key` is read from whichever config
    location actually configures the tool, so `mypy.ini` and `[tool.mypy]` are
    the same statement rather than one of them being invisible (§ D).
    """
    role = str(args.get("role", ""))
    if role not in ("lint", "typecheck"):
        return _fail("assert requires a 'role' argument naming a gate in the register")
    gates = _applicable_gates(repo, register, role)
    if not gates:
        return _ok("no stack with a type-checking gate is present")

    problems: list[str] = []
    for stack, gate in sorted(gates.items()):
        problems.extend(_wired_problems(repo, stack, gate))
        section = _configured(repo, gate)
        if section is not None and gate.strict_key:
            if not _truthy_setting(section.get(gate.strict_key)):
                problems.append(f"{stack}: {gate.tool} {gate.strict_key} mode is not set")
            # Strict alongside a blanket override that ignores errors is not
            # strict typing — it is strict typing switched off in a second
            # place, which TYP-001's title forbids and nothing read (§ D).
            problems.extend(f"{stack}: {o}" for o in _blanket_overrides(repo, gate))
        problems.extend(
            f"{stack}: {problem}"
            for problem in _uncovered_sources(repo, register.stacks[stack], gate)
        )
        steps = [s for s in _workflow_steps(repo) if re.search(
            rf"\b{re.escape(gate.invocation)}\b", s.run)]
        if steps and any(
            s.suppressed or _suppression_match(register, s.run) for s in steps
        ):
            problems.append(f"{stack}: the {gate.tool} CI step suppresses its failure")
    if problems:
        return _fail("; ".join(problems))
    tools = ", ".join(sorted(gate.tool for gate in gates.values()))
    return _ok(f"{tools} runs in strict mode and blocks in CI")


_DEFAULT_TEST_COMMANDS = (
    "pytest",
    "npm test",
    "npm run test",
    "vitest",
    "jest",
    "go test",
    "cargo test",
    "tox",
    "nox",
    "make test",
    "gradle test",
    "mvn test",
    "rspec",
    "bundle exec rspec",
)


def _test_commands(register: Register) -> tuple[str, ...]:
    """Accepted test invocations: the register's, else the built-in defaults.

    ADR 0018 places these in the register — a repo may reasonably invoke its
    tests differently without the checker changing, and the six hard-coded
    spellings failed `npm run test`, `make test`, `tox`, `gradle` and `rspec`
    alike (§ D).
    """
    from_register = tuple(
        command
        for ecosystem in register.ecosystems.values()
        for command in ecosystem.test_commands
    )
    return from_register or _DEFAULT_TEST_COMMANDS


def _runs_tests(run: str, commands: tuple[str, ...]) -> bool:
    """Whether this step *invokes* one of the test commands.

    Matched as an invocation, not a substring: `pip install pytest==8.0.0`
    mentions pytest and runs nothing, and counted as a test step (§ D).
    """
    for line in _logical_lines(run):
        for command in re.split(r"&&|\|\||;", line):
            text = " ".join(command.split())
            for candidate in commands:
                if re.match(rf"^(?:\S+\s+run\s+)?{re.escape(candidate)}(?![-\w])", text):
                    return True
    return False


def tests_run_and_block(
    repo: Repo,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    commands = _test_commands(register)
    # A step in a workflow that never runs on push or pull_request is not a
    # gate, however good its command (§ D, theme T-3).
    test_steps = [
        s for s in _workflow_steps(repo) if s.gating and _runs_tests(s.run, commands)
    ]
    if not test_steps:
        if any(_runs_tests(s.run, commands) for s in _workflow_steps(repo)):
            return _fail(
                "the only step running the test command is in a workflow that does not "
                "run on push or pull_request, so it gates nothing"
            )
        return _fail("no CI step runs the test command")
    absorbed = [
        f"{s.path} ({s.job})"
        for s in test_steps
        if s.suppressed or _suppression_match(register, s.run)
    ]
    if absorbed:
        return _fail("the test step's exit code is absorbed: " + "; ".join(absorbed))
    return _ok("the test command runs in CI and its exit code is the verdict")


_MARKDOWNLINT_CONFIGS = (
    ".markdownlint.yaml",
    ".markdownlint.yml",
    ".markdownlint.jsonc",
    ".markdownlint.json",
    ".markdownlint-cli2.yaml",
    ".markdownlint-cli2.jsonc",
)

# markdownlint's own default when the rule is enabled but unconfigured. A repo
# that never names a ceiling still has one, and it is tighter than any register
# value we would set — which `narrowing-only` permits.
_MARKDOWNLINT_DEFAULT_LINE_LENGTH = 80


def _markdownlint_rules(repo: Repo) -> tuple[str, dict[str, Any]] | None:
    """The rule set, from whichever of the six config spellings holds it.

    A `.markdownlint-cli2.*` file wraps its rules in a `config:` key; the plain
    `.markdownlint.*` files are the rules themselves.
    """
    for path in _MARKDOWNLINT_CONFIGS:
        if path not in repo.tracked:
            continue
        text = repo.read(path)
        doc = load_jsonc(repo.root / path) if path.endswith(("json", "jsonc")) else yaml.safe_load(
            text
        )
        if not isinstance(doc, dict):
            continue
        if "markdownlint-cli2" in path:
            nested = doc.get("config")
            if not isinstance(nested, dict):
                continue  # a cli2 file holding only `ignores:` is not the rule set
            return path, nested
        return path, doc
    return None


def _line_length_ceiling(rules: Mapping[str, Any]) -> int | str:
    """The effective MD013 ceiling, or a sentence saying why there is none.

    Both spellings are accepted because markdownlint accepts both: `MD013` is
    the rule id and `line-length` its alias, and a config using the alias is no
    less configured for it.
    """
    md013: Any = None
    for key in ("MD013", "line-length"):
        if key in rules:
            md013 = rules[key]
            break
    if md013 is False:
        return "the line-length rule (MD013) is switched off"
    if md013 is None:
        if rules.get("default") is False:
            return "MD013 is not enabled and `default: false` leaves it off"
        return _MARKDOWNLINT_DEFAULT_LINE_LENGTH
    if not isinstance(md013, dict):
        return _MARKDOWNLINT_DEFAULT_LINE_LENGTH  # `MD013: true` — enabled, unconfigured
    for key in ("line_length", "line-length"):
        value = md013.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return _MARKDOWNLINT_DEFAULT_LINE_LENGTH


# The runner configs, as opposed to the rule-set configs above. Only these carry
# an exemption list; `.markdownlint.*` holds rules and nothing else.
_MARKDOWNLINT_RUNNER_CONFIGS = (
    ".markdownlint-cli2.yaml",
    ".markdownlint-cli2.jsonc",
)


def _hidden_tracked_files(repo: Repo) -> list[str]:
    """Markdown files the gate's own exemptions would exclude from linting.

    ADR 0019. The rule was "no ignore path", which this repository broke on its
    first day — markdownlint-cli2 globs the filesystem, so without exemptions it
    lints every third-party README in `node_modules`. Stated that way it was also
    too weak to catch what it was for: `.claude/**` sat in the same list hiding
    eleven authored violations, and a person found it, not a check.

    The property is what an exemption *hides*. A path git does not track is not
    this repository's content, and excluding it is scoping the tool rather than
    weakening the control; a path git tracks is authored here, and no
    `narrowing-only` control with `baseline: null` admits excluding it.
    """
    hidden: list[str] = []
    tracked = sorted(path for path in repo.tracked if path.endswith(".md"))
    for config in _MARKDOWNLINT_RUNNER_CONFIGS:
        if config not in repo.tracked:
            continue
        doc = (
            load_jsonc(repo.root / config)
            if config.endswith(("json", "jsonc"))
            else yaml.safe_load(repo.read(config))
        )
        if not isinstance(doc, dict):
            continue
        for pattern in doc.get("ignores") or []:
            # fnmatch's `*` crosses `/`, which is what a `**/…/**` glob means
            # here anyway, so the two spellings agree on directory trees.
            matched = [path for path in tracked if fnmatch.fnmatch(path, str(pattern))]
            if not matched:
                continue
            # Named, then counted. One offending pattern can match a whole tree,
            # and a verdict that lists every file buries the pattern that caused
            # it under the evidence for it.
            shown = ", ".join(matched[:3])
            more = f" and {len(matched) - 3} more" if len(matched) > 3 else ""
            hidden.append(
                f"{config}: '{pattern}' excludes {len(matched)} tracked file(s) "
                f"the repository authors ({shown}{more})"
            )
    return hidden


def markdown_gate_wired_at_all_loci(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """DOC-001's `enforces`, verified rather than assumed.

    The assert this replaces checked only that a configuration file existed. A
    config setting `line_length: 100000` passed it, and so did deleting the CI
    step, the pre-commit hook or the editor extension — an existence check
    standing in for a control about one rule set wired at three loci (§ A).

    Every value a repository could reasonably need to differ comes from the
    register's `args` (ADR 0018): the ceiling, the tool name and the editor
    extension id. What stays here is the shape — that the ceiling must not be
    loosened and that all three loci must be wired — which is a property of the
    control, not of any repository.
    """
    tool = str(args.get("tool", ""))
    extension = str(args.get("editor_extension", ""))
    ceiling = args.get("max_line_length")
    if not tool or not extension or not isinstance(ceiling, int):
        return _fail(
            "assert requires 'tool', 'editor_extension' and an integer "
            "'max_line_length' argument from the register"
        )

    found = _markdownlint_rules(repo)
    if found is None:
        return _fail("no tracked markdownlint configuration file")
    path, rules = found

    # How the pinned artefact is reached, not merely which tool is named. A
    # lockfile is an authority only if the invocation resolves to what it pins,
    # and `npx --no-install` falls through to PATH when the local install is
    # missing — measured, with a global binary answering for the lockfile's
    # (ADR 0020, § H6). A tool the register does not pin is invoked by name.
    pinned = register.tools.get(tool)
    invocation = pinned.invocation if pinned and pinned.invocation else tool

    problems: list[str] = []
    effective = _line_length_ceiling(rules)
    if isinstance(effective, str):
        problems.append(f"{path}: {effective}")
    elif effective > ceiling:
        # `narrowing-only` — a repo may tighten below the register's number and
        # may never raise above it (docs/00-concepts.md § Variance).
        problems.append(
            f"{path}: line length ceiling is {effective}, above the register's {ceiling}"
        )
    if extension not in _devcontainer_extensions(repo):
        problems.append(f"editor locus — no editor configuration installs {extension}")
    if not _hook_mentions(repo, invocation):
        problems.append(
            f"pre-commit locus — no hook runs '{invocation}'"
            + (f" ({tool} is pinned by {pinned.lockfile})" if pinned and pinned.lockfile else "")
        )
    if not _ci_run_mentions(repo, re.escape(invocation), hook=tool):
        problems.append(f"ci locus — no gating step runs '{invocation}'")
    # An exemption that hides authored content is a weakening of a control whose
    # `baseline: null` admits none (ADR 0019).
    problems.extend(_hidden_tracked_files(repo))
    if problems:
        return _fail("; ".join(problems))
    return _ok(
        f"{path} caps lines at {effective} (register allows {ceiling}), and every locus "
        f"reaches {tool} through '{invocation}'"
    )


COMMAND_ASSERTS: dict[str, AssertFn] = {
    "no-static-cloud-keys": no_static_cloud_keys,
    "ci-installs-frozen": ci_installs_frozen,
    "actions-pinned-to-sha": actions_pinned_to_sha,
    "linter-wired-at-all-loci": linter_wired_at_all_loci,
    "no-failure-suppression": no_failure_suppression,
    "typecheck-strict-and-blocking": typecheck_strict_and_blocking,
    "tests-run-and-block": tests_run_and_block,
    "markdown_gate_wired_at_all_loci": markdown_gate_wired_at_all_loci,
}
