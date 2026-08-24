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
    CONTROL_ARG,
    AssertFn,
    AssertResult,
    _ecosystems_present,
    _fail,
    _ok,
)
from standard_check.predicates import compile_predicate
from standard_check.repo import Repo, load_jsonc
from standard_check.rulesets import by_rule_type, required_checks, requirement_problems

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


# How a workflow reaches a secret. `secrets.NAME` covers the expression context
# and `secrets: inherit` covers handing the whole store to a called workflow —
# a reference to every secret at once, which no allow-list can enumerate and so
# fails whatever the register names. `github.token` is the same credential as
# `secrets.GITHUB_TOKEN` under another spelling, and every workflow in this
# repository uses that one; that equivalence is detection implementation and
# stays here, as `cloud_credentials:` spelling equivalence does (ADR 0018).
_SECRET_REFERENCE = re.compile(r"secrets\.([A-Za-z_][A-Za-z0-9_-]*)")
_SECRETS_INHERIT = re.compile(r"^\s*secrets:\s*inherit\s*$", re.MULTILINE)
_PLATFORM_TOKEN_CONTEXT = re.compile(r"github\.token\b")


def _workflow_triggers(doc: object) -> tuple[str, ...]:
    """The events a workflow runs on, however `on:` is spelled.

    `on:` parses as the YAML 1.1 boolean True, the same trap `_is_gating`
    documents; a workflow whose triggers could not be read reports none, which
    makes the trigger half of SEC-003 silent rather than wrong — the unnamed
    secret half still fails.
    """
    if not isinstance(doc, dict):
        return ()
    triggers: object = doc["on"] if "on" in doc else doc.get(True)
    if isinstance(triggers, str):
        return (triggers,)
    if isinstance(triggers, list):
        return tuple(str(t) for t in triggers)
    if isinstance(triggers, dict):
        return tuple(str(t) for t in triggers)
    return ()


def no_unregistered_workflow_secrets(
    repo: Repo,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    """SEC-003 — every secret a workflow reaches is one the register names.

    This is an allow-list, and the direction is the opposite of
    `no_static_cloud_keys`: there, a credential the register has not heard of
    passes, because the list enumerates what is forbidden. Here a credential
    the register has not heard of fails, because the list enumerates what is
    permitted — so a register with no `platform_credentials:` block permits no
    secret at all rather than checking none (ADR 0022 requirement 1).
    """
    permitted = {credential.name: credential for credential in register.platform_credentials}
    findings: list[str] = []
    for path in repo.workflow_files():
        text = repo.read(path)
        if _SECRETS_INHERIT.search(text):
            findings.append(
                f"{path}: passes `secrets: inherit`, which hands a called workflow every "
                "secret this repository holds — a reference no allow-list can enumerate"
            )
        names = set(_SECRET_REFERENCE.findall(text))
        if _PLATFORM_TOKEN_CONTEXT.search(text):
            names.add("GITHUB_TOKEN")
        triggers = _workflow_triggers(yaml.safe_load(text))
        for name in sorted(names):
            credential = permitted.get(name)
            if credential is None:
                findings.append(
                    f"{path}: references {name}, which `platform_credentials:` does not name "
                    "— a credential nobody decided"
                )
                continue
            if credential.triggers is None:
                continue
            forbidden = [event for event in triggers if event not in credential.triggers]
            if forbidden:
                findings.append(
                    f"{path}: references {name} in a workflow that runs on "
                    f"{', '.join(forbidden)}, which `platform_credentials:` does not permit "
                    f"for it (permitted: {', '.join(credential.triggers)})"
                )
    if findings:
        return _fail("; ".join(findings))
    return _ok(
        f"every secret referenced by a workflow is one of the {len(permitted)} the register "
        "names, under an event it permits"
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


#: Words that precede a command without being one. Stripped before asking
#: whether a tool is what a command *runs*, so `sudo gitleaks detect` and
#: `CI=1 ruff check` are the invocations they plainly are.
_COMMAND_PREFIXES = ("sudo", "env", "time", "exec", "nohup")
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _commands(run: str) -> Iterator[str]:
    """Each command in a `run:` block, with its prefix words stripped.

    A tool is run by a step when it is the **command**, not when its name
    appears in one. Before contract 16 this was a substring search over the
    whole `run:` text, and `gate-secrets`' own CI template defeated it: the
    install step mentions `gitleaks` six times — in a URL, in a tarball name, as
    an argument to `tar`, `install` and `rm` — so a workflow that installed the
    scanner and never ran it satisfied SEC-001's ci locus. Deleting the secret
    scan step left the control green.
    """
    for line in _logical_lines(run):
        for command in re.split(r"&&|\|\||;|\|", line):
            words = command.strip().split()
            while words and (words[0] in _COMMAND_PREFIXES or _ASSIGNMENT.match(words[0])):
                words.pop(0)
            if words:
                yield " ".join(words)


def _ci_run_mentions(repo: Repo, pattern: str, *, hook: str | None = None) -> bool:
    """Whether a gating step *runs* `pattern` — anchored at command position.

    `pattern` is matched with `re.match` against each command in each step, so a
    tool named inside a command's arguments is not that command. Callers pass an
    escaped invocation or one wrapped in `\b`; both anchor cleanly.
    """
    for step in _workflow_steps(repo):
        # A suppressed step is not the ci locus. `continue-on-error: true` means
        # the job succeeds whatever the gate reports, so the tool runs and the
        # merge is not gated on it — which is the *declared and unreachable*
        # shape (theme T-3) one level in from the one `_is_gating` catches.
        # SEC-001 and SUP-003 have no `no-failure-suppression` block of their
        # own, so without this a suppressed secret-scan step counted as wiring.
        if not step.gating or step.suppressed:
            continue
        if any(re.match(pattern, command) for command in _commands(step.run)):
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


# Where a repository states editor behaviour, and where it must not. Both paths
# are VS Code's own layout rather than anything a register could vary, so they
# stay in the checker (ADR 0018) — what is bound, and by which extension, comes
# from `stacks:`.
_WORKSPACE_SETTINGS = ".vscode/settings.json"
_DEVCONTAINER = ".devcontainer/devcontainer.json"


def _settings(repo: Repo, path: str, *, at: tuple[str, ...] = ()) -> dict[str, Any]:
    """A settings mapping from a JSONC file, or an empty one.

    `at` walks into a nested object — `devcontainer.json` holds its settings
    under `customizations.vscode.settings`, where `.vscode/settings.json` is the
    mapping itself.
    """
    if not repo.exists(path):
        return {}
    node: object = load_jsonc(repo.root / path)
    for key in at:
        node = node.get(key) if isinstance(node, dict) else None
    return node if isinstance(node, dict) else {}


def _binding_problems(repo: Repo, stack: str, gate: Gate) -> list[str]:
    """Whether the gate's extension *holds* its file type, not merely exists.

    ADR 0029 point 4. Presence never excluded: `charliermarsh.ruff` was
    installed for the whole time `ghcr.io/devcontainers/features/python:1` had
    Python files bound to `ms-python.autopep8`, and the assert called that a
    pass. The binding is read at workspace scope because that is the only scope
    that wins by documented rule — the containers.dev merge table says of
    `customizations` only that "merging is left to the tools".

    An **unstated** binding fails, and this is the case that matters: the
    autopep8 binding was written by a feature, so no tracked file said anything
    at all. An assert that only objected to a wrong value in a file nobody had
    written would have passed the state it exists to catch.
    """
    binding = gate.editor_binding
    if binding is None or not gate.editor_extension:
        return []
    selector = f"[{binding.language}]"
    problems = []
    scoped = _settings(repo, _WORKSPACE_SETTINGS).get(selector)
    held = scoped.get(binding.setting) if isinstance(scoped, dict) else None
    if held is None:
        problems.append(
            f"{stack}: editor locus — {_WORKSPACE_SETTINGS} does not set "
            f'"{selector}".{binding.setting}, so whichever extension a feature or '
            f"the base image binds holds {binding.language} files"
        )
    elif str(held) != gate.editor_extension:
        problems.append(
            f"{stack}: editor locus — {binding.language} files are bound to {held}, "
            f"not to {gate.editor_extension}, which {gate.tool} is pinned as"
        )
    # A second statement of the binding, in the file ADR 0029 point 1 takes it
    # out of. Wrong even when it agrees: it lands in the same machine-scoped
    # file a feature's does and competes on undefined terms, so agreeing today
    # is luck rather than a rule.
    container = _settings(repo, _DEVCONTAINER, at=("customizations", "vscode", "settings"))
    if isinstance(container.get(selector), dict) and binding.setting in container[selector]:
        problems.append(
            f"{stack}: editor locus — {_DEVCONTAINER} also sets "
            f'"{selector}".{binding.setting}; the binding belongs at workspace scope alone'
        )
    return problems


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
    problems += _binding_problems(repo, stack, gate)
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

    Which linter, where its configuration lives, its pre-commit hook id, its
    editor extension id and the file type that extension must hold all come
    from the register's `stacks:` (ADR 0018). They were a checker-side
    dictionary knowing ruff and eslint, so "the standard mandates ruff" was a
    decision no reviewer could find.

    From contract 21 the editor locus is verified by exclusion rather than by
    presence — see `_binding_problems` for why presence was not enough.
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


def _fingerprint_paths(line: str, tracked: set[str]) -> list[str]:
    """Tracked paths named by one gitleaks ignore entry.

    A fingerprint is `commit:path:rule-id:line`, or `path:rule-id:line` for a
    no-git scan, and a bare path is also accepted by the tool. Rather than
    committing to one spelling, every colon-separated field is tested against
    what git tracks — a field that is a tracked path is a tracked path whichever
    position it occupies, and one that is not cannot be mistaken for one.
    """
    return [field for field in line.split(":") if field in tracked]


def secrets_gate_wired_at_all_loci(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """SEC-001's `enforces`, verified at each locus it names.

    SEC-001 declares `locus: [pre-commit, ci, remote]` and, until this assert,
    verified one of them: `precommit_hook_present` read the hook, the remote
    block deferred to Phase 3, and **nothing at all read the CI locus**. A
    repository could delete its secret-scanning job and keep a green SEC-001 —
    a control declared at three loci and checked at one, which is § A's defect
    and the same shape § H found in GOV-001.

    Deleting the pre-commit hook was caught; deleting the CI job was not. Both
    are now failures, and the remote locus stays honestly deferred rather than
    being quietly folded in here.

    Everything a repository could reasonably need to differ comes from the
    register (ADR 0018): the tool's name, how a locus reaches it, and where its
    exemption list lives. What stays here is the shape — that a control naming a
    locus must be reachable at it.
    """
    tool = str(args.get("tool", ""))
    if not tool:
        return _fail("assert requires a 'tool' argument naming the scanner")
    ignore_file = str(args.get("ignore_file", ""))

    # How the pinned artefact is reached, not merely which tool is named
    # (ADR 0020). A tool the register pins by invocation is looked for by that
    # invocation; one it pins by version is installed onto PATH and invoked by
    # name, and `tool_versions_match_register` is what holds those pins in step.
    pinned = register.tools.get(tool)
    invocation = pinned.invocation if pinned and pinned.invocation else tool

    problems: list[str] = []
    if not _hook_mentions(repo, invocation):
        problems.append(f"pre-commit locus — no hook runs '{invocation}'")
    if not _ci_run_mentions(repo, re.escape(invocation), hook=tool):
        problems.append(f"ci locus — no gating step runs '{invocation}'")

    # ADR 0019, applied to the one exemption list this gate has. SEC-001 is
    # `variance: forbidden` with `baseline: null`: an entry that suppresses a
    # finding in a file git tracks hides authored content from a control that
    # admits no tolerated violations. An entry naming nothing tracked suppresses
    # a finding about content this repository does not author, which scopes the
    # tool rather than weakening the control.
    if ignore_file and ignore_file in repo.tracked:
        for number, raw in enumerate(repo.read(ignore_file).splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            hidden = _fingerprint_paths(line, repo.tracked)
            if hidden:
                problems.append(
                    f"{ignore_file}:{number} suppresses findings in "
                    f"{', '.join(sorted(hidden))}, which git tracks (ADR 0019)"
                )

    if problems:
        return _fail("; ".join(problems))
    scoped = f", and {ignore_file} hides nothing git tracks" if ignore_file in repo.tracked else ""
    return _ok(f"pre-commit and ci loci both reach {tool} through '{invocation}'{scoped}")


#: This checker's own console script. Recognising it by name is a property of
#: the checker rather than of any repository (ADR 0018): a gate whose tool *is*
#: the auditor has to be judged by which subcommand it runs, and no other tool
#: does.
_SELF = "standard-check"

#: The subcommands that audit no control. Running the checker is not the same as
#: auditing with it: `standard-check schema` validates the register and reads not
#: one control, and this repository's own pre-commit config runs exactly that —
#: which credited SUP-003 with a pre-commit gate that could never have failed it.
_NON_AUDITING_SUBCOMMANDS = ("schema", "meta", "assert", "explain")


def gate_wired_at_declared_loci(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """Every locus this control declares runs something that enforces it.

    A control's `locus:` list is a claim, and until contract 14 several controls
    made it with nothing checking it. SUP-003, BLD-001, DEV-001 and IAC-001 each
    declared `[pre-commit, ci]` and verified only their *property* — every
    `uses:` is a SHA, the final USER is not root, the lock file covers every
    feature — read out of the files on disk. That is a different claim from
    *something enforces this before a commit lands and before a merge does*, and
    a repository with no pre-commit hook of any kind reported PASS on all four.

    The loci come from the control being evaluated rather than from `args:`,
    which is what stops this assert becoming a fourth near-copy: contract 14
    shipped `supply_chain_gate_wired_at_all_loci` knowing two loci by name, and
    BLD-001, DEV-001 and IAC-001 would each have grown another. Three copies of
    one check was already one too many.

    `remote` is skipped deliberately and named as skipped. Verifying platform
    state is Phase 3's, and a locus quietly dropped here is the silence this
    assert exists to remove.
    """
    tool = str(args.get("tool", ""))
    if not tool:
        return _fail("assert requires a 'tool' argument naming the gate's tool")
    pinned = register.tools.get(tool)
    if pinned is None:
        return _fail(f"the register mandates '{tool}' at these loci and pins no such tool")
    invocation = pinned.invocation or tool
    control_id = str(args.get(CONTROL_ARG, ""))
    # `register.controls` rather than `register.control()`, which also resolves
    # meta-controls: a meta-control checks the register rather than the
    # repository and declares no loci, so there would be nothing here for it to
    # be wired at.
    control = next((c for c in register.controls if c.id == control_id), None)
    if control is None:  # pragma: no cover — the runner supplies a real control
        return _fail(f"no control with a declared locus named '{control_id}'")

    problems: list[str] = []
    checked: list[str] = []
    deferred: list[str] = []
    for locus in control.locus:
        if locus == "remote":
            deferred.append(locus)
            continue
        if locus == "pre-commit":
            found = any(
                _reaches(str(hook.get("entry", "")), tool, invocation, control_id)
                for hook in _precommit_hooks(repo)
            )
        elif locus == "ci":
            # `suppressed` for the same reason `gating` is here: a step carrying
            # `continue-on-error: true` runs the gate and does not gate on it.
            found = any(
                step.gating
                and not step.suppressed
                and _reaches(step.run, tool, invocation, control_id)
                for step in _workflow_steps(repo)
            )
        elif locus == "editor":
            found = any(
                invocation in extension for extension in _devcontainer_extensions(repo)
            )
        else:  # pragma: no cover — LOCI is closed and every member is handled
            return _fail(f"locus '{locus}' is declared and this assert cannot read it")
        if found:
            checked.append(locus)
        else:
            problems.append(f"{locus} locus — nothing runs '{invocation}' for {control_id}")
    if problems:
        return _fail("; ".join(problems))
    reached = " and ".join(checked) if checked else "no local"
    note = f" ({', '.join(deferred)} deferred to Phase 3)" if deferred else ""
    return _ok(f"{reached} loci reach {control_id} through '{invocation}'{note}")


def _reaches(text: str, tool: str, invocation: str, control: str) -> bool:
    """Whether `text` runs `invocation` in a way that enforces `control`.

    For an ordinary tool this is the invocation appearing as an invocation. For
    the checker it is narrower, because running the checker is not the same as
    auditing with it: a full run — the invocation followed by nothing or by
    flags — reaches every applicable control, a selective run reaches only the
    controls it names, and `schema`, `meta`, `assert` and `explain` reach none
    at all however pinned their invocation.
    """
    for command in _commands(text):
        match = re.match(rf"{re.escape(invocation)}(?![-\w])", command)
        if match is None:
            continue
        if tool != _SELF:
            return True
        rest = command[match.end() :].split()
        if rest and rest[0] in _NON_AUDITING_SUBCOMMANDS:
            continue
        selected = re.findall(r"--control[=\s]+(\S+)", command)
        if not selected or control in selected:
            return True
    return False


def ruleset_recorded_matches_register(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """The branch ruleset a repository records says what the register requires.

    **This verifies intent, not platform state.** A recorded ruleset GitHub has
    never been told about protects nothing, and nothing here may stand in for
    the `kind: remote` block beside it — that block reports SKIPPED (no
    credentials) until Phase 3, deliberately, and its verdict is the one that
    says the branch is protected.

    What this closes is smaller and real. CI-001's only locus is `remote`, which
    made `gate-repo` the one gate with no file to write, no stamp to leave and
    nothing observable until a later phase. A gate that cannot be watched
    working is the shape this repository's review record keeps re-opening
    criteria over. Recording the ruleset as a reviewable artefact — derived from
    the register's `args:` at deploy time — gives the deployment something a
    reader and a checker can both see.

    The requirements are the register's, and they are the *same* `args:` the
    remote assert reads. Two blocks would be two definitions of "protected",
    free to drift from each other.

    **Register contract 19 made this read what a rule *does*, not that a rule of
    that name is present.** Until then the recorded ruleset spelled every rule
    as a bare `{"type": ...}`, and this assert checked only that each type
    appeared. Two things were wrong with that, in opposite directions:

    The record was not a payload. GitHub's REST schema requires `parameters` on
    `pull_request` and `required_status_checks`, so `gate-repo`'s apply step
    returned 422 for every adopter — a gate that could not deploy the control it
    exists to deploy. The rules that take no parameters, `non_fast_forward` and
    `deletion`, are checked in the other direction for the same reason: a
    payload the API rejects is not a record of anything.

    The record was also weaker than the control it recorded. A
    `required_status_checks` rule naming **no context** requires no check, and
    CI-001's `enforces` reads *at least one passing status check*. So a ruleset
    that gated nothing satisfied `require_status_checks: true` — the same shape
    as the four loci nothing read at contract 14, where a verdict turned on a
    thing being present rather than on what the thing did.

    `required_checks` is the register's, because which checks a repository
    requires is a fact about that repository (ADR 0018). It is then held to the
    workflows: a named context must be produced by a job in a **gating**
    workflow and that job must not be suppressed. Without the cross-check the
    register would carry a second copy of job ids, free to drift from the
    workflows — theme T-2, in the file that exists to prevent it. With it, a
    renamed job fails here rather than silently un-protecting the branch, and a
    `continue-on-error` job cannot be a required check that always passes.
    """
    path = str(args.get("path", ""))
    if not path:
        return _fail("assert requires a 'path' argument naming the recorded ruleset")
    if path not in repo.tracked:
        return _fail(
            f"{path} is not tracked — a ruleset git does not carry is not one anybody "
            "can review, and this control's remote block cannot be reached without "
            "credentials either"
        )
    # JSONC, like `.devcontainer/devcontainer.json`, and for the same reason: the
    # stamp is a `//` comment and a file that cannot carry one cannot carry its
    # own provenance. GitHub's API takes strict JSON, so the gate strips the
    # comment lines on the way out — which is a filter on a payload, not a
    # second copy of the ruleset.
    try:
        document = load_jsonc(repo.root / path)
    except (OSError, ValueError) as exc:
        return _fail(f"{path} is not readable JSON: {exc}")
    if not isinstance(document, dict):
        return _fail(f"{path} must be a JSON object describing one ruleset")

    problems = _ruleset_problems(document, args, repo)
    if problems:
        return _fail("; ".join(problems))
    checks = ", ".join(required_checks(args)) or "none named"
    return _ok(
        f"{path} records a ruleset matching the register, requiring {checks} — intent "
        "only; whether the platform enforces it is the remote block's, and is not "
        "claimed here"
    )


#: Rule types GitHub's REST schema requires a `parameters` object on, and those
#: it accepts none for. Not a repository's choice — it is the API's own shape,
#: and getting it wrong means the apply call is rejected rather than the control
#: being weakened, which is why it is checked at all (ADR 0018).
_RULES_NEEDING_PARAMETERS = frozenset({"pull_request", "required_status_checks"})
_RULES_TAKING_NO_PARAMETERS = frozenset({"non_fast_forward", "deletion"})


def _check_contexts(repo: Repo) -> dict[str, bool]:
    """Status check contexts this repository produces, and whether each is suppressed.

    GitHub names a check run after the job's `name:` where it has one and after
    the job id otherwise, so that is what a `required_status_checks` context has
    to match. Only gating workflows count: a job in a `workflow_dispatch`-only
    workflow reports no check on a pull request, so requiring it would block
    every merge rather than gate one.
    """
    contexts: dict[str, bool] = {}
    for workflow in repo.workflow_files():
        doc = yaml.safe_load(repo.read(workflow))
        if not isinstance(doc, dict) or not _is_gating(doc):
            continue
        jobs = doc.get("jobs")
        if not isinstance(jobs, dict):
            continue
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            contexts[str(job.get("name") or job_id)] = _truthy(job.get("continue-on-error"))
    return contexts


def _ruleset_problems(
    document: Mapping[str, object],
    args: Mapping[str, object],
    repo: Repo,
) -> list[str]:
    """Where the recorded ruleset falls short of what the register requires."""
    problems: list[str] = []
    if document.get("enforcement") != "active":
        problems.append(
            f"enforcement is {document.get('enforcement')!r}, not 'active' — an evaluated "
            "or disabled ruleset reports what would have happened and blocks nothing"
        )
    by_type = by_rule_type(document.get("rules"))
    # The requirement reading is `rulesets.py`'s, and the remote block reads the
    # platform's rules through the same function. What stays here is what only a
    # recorded artefact can be wrong about: a payload the API would reject, a
    # condition naming a branch by name, and a required check no workflow
    # produces.
    problems.extend(
        f"the recorded ruleset {problem}" if problem.startswith("does not require") else problem
        for problem in requirement_problems(by_type, args)
    )
    problems.extend(_payload_problems(by_type))
    if args.get("require_status_checks") is True and required_checks(args):
        problems.extend(_unproduced_checks(required_checks(args), repo))
    target = document.get("conditions")
    if isinstance(target, dict):
        refs = target.get("ref_name")
        include = refs.get("include") if isinstance(refs, dict) else None
        if isinstance(include, list) and "~DEFAULT_BRANCH" not in include:
            problems.append(
                f"conditions target {include} rather than ~DEFAULT_BRANCH — a ruleset "
                "naming a branch by name stops protecting it the day the default moves"
            )
    return problems


def _payload_problems(by_type: Mapping[str, Mapping[str, object]]) -> list[str]:
    """Whether GitHub's API would accept this document as written.

    A record the API rejects is not a record of what protects the branch — it is
    a description of a call that cannot be made. `gate-repo` POSTs this file
    with its comment lines stripped and nothing else changed, so anything wrong
    here is wrong on the wire.
    """
    problems: list[str] = []
    for rule_type in sorted(_RULES_NEEDING_PARAMETERS & set(by_type)):
        if not isinstance(by_type[rule_type].get("parameters"), dict):
            problems.append(
                f"the '{rule_type}' rule has no 'parameters' object, which GitHub's API "
                "requires — the apply call is rejected with 422 and the control is not "
                "deployed, however complete this file looks"
            )
    for rule_type in sorted(_RULES_TAKING_NO_PARAMETERS & set(by_type)):
        if "parameters" in by_type[rule_type]:
            problems.append(
                f"the '{rule_type}' rule carries 'parameters', which GitHub's API does not "
                "accept for it"
            )
    return problems


def _unproduced_checks(required: list[str], repo: Repo) -> list[str]:
    """A required check no gating job produces, or one a suppressed job produces.

    The cross-check is what keeps `required_checks` from becoming a second copy
    of the workflows' job ids. A context nothing produces blocks every merge
    rather than gating one, and a context produced by a `continue-on-error` job
    is a required check that always passes — which is the T-3 shape GOV-001
    exists to catch, arriving through the ruleset instead of the workflow.
    """
    contexts = _check_contexts(repo)
    if not contexts:
        return [
            "no gating workflow produces any status check, so no ruleset can require one — "
            "a workflow that runs on neither push nor pull_request reports nothing on a "
            "pull request"
        ]
    problems: list[str] = []
    for check in required:
        if check not in contexts:
            problems.append(
                f"required check '{check}' is produced by no job in a gating workflow "
                f"(these are: {', '.join(sorted(contexts))}) — GitHub waits forever for a "
                "check nothing reports, so this blocks every merge rather than gating one"
            )
        elif contexts[check]:
            problems.append(
                f"required check '{check}' comes from a job with continue-on-error, so it "
                "reports success whatever happens — a required check that cannot fail"
            )
    return problems


COMMAND_ASSERTS: dict[str, AssertFn] = {
    "no-static-cloud-keys": no_static_cloud_keys,
    "ci-installs-frozen": ci_installs_frozen,
    "actions-pinned-to-sha": actions_pinned_to_sha,
    "linter-wired-at-all-loci": linter_wired_at_all_loci,
    "no-failure-suppression": no_failure_suppression,
    "typecheck-strict-and-blocking": typecheck_strict_and_blocking,
    "tests-run-and-block": tests_run_and_block,
    "markdown_gate_wired_at_all_loci": markdown_gate_wired_at_all_loci,
    "secrets_gate_wired_at_all_loci": secrets_gate_wired_at_all_loci,
    "gate_wired_at_declared_loci": gate_wired_at_declared_loci,
    "ruleset_recorded_matches_register": ruleset_recorded_matches_register,
    "no_unregistered_workflow_secrets": no_unregistered_workflow_secrets,
}
