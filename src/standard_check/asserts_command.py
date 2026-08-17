"""Command assertions — the `standard-check assert <name>` closed set.

These are the checks the register invokes as `kind: command` verify blocks.
They read workflow and configuration files; none of them executes anything.
"""

from __future__ import annotations

import configparser
import re
import tomllib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import yaml

from standard_check.asserts_file import AssertFn, AssertResult, _fail, _ok
from standard_check.repo import Repo, load_jsonc

if TYPE_CHECKING:  # `register` imports the assert registries — importing it
    from standard_check.register import Register  # at runtime would be circular


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


_STATIC_KEY_NAMES = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GCP_SA_KEY",
    "SERVICE_ACCOUNT_KEY",
    "AZURE_CLIENT_SECRET",
    "AZURE_CREDENTIALS",
)

# Matched case-insensitively, and with `-`/`_` treated alike: the same key is
# spelled `aws-access-key-id:` as an action input and `AWS_ACCESS_KEY_ID` as an
# env var. A case-sensitive substring test over the uppercase spellings missed
# `aws-access-key-id: ${{ secrets.PROD_KEY }}` entirely (§ D) — the commonest
# way the credential actually appears.
_STATIC_KEY_PATTERNS = tuple(
    (name, re.compile(name.replace("_", "[-_]"), re.IGNORECASE)) for name in _STATIC_KEY_NAMES
)


def no_static_cloud_keys(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    findings: list[str] = []
    for path in repo.workflow_files():
        text = repo.read(path)
        findings.extend(
            f"{path}: references {name}" for name, pattern in _STATIC_KEY_PATTERNS
            if pattern.search(text)
        )
    if findings:
        return _fail("; ".join(findings))
    return _ok("no workflow references a static cloud key secret")


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


_FROZEN_PY = re.compile(
    r"\buv sync\b.*--(frozen|locked)\b"
    r"|\bpip3? install\b.*-r\s+\S+"
    r"|\b(?:poetry|pdm) install\b.*--(?:sync|frozen|no-update|check)\b"
)
_FROZEN_NODE = re.compile(
    r"\bnpm ci\b|\byarn install\b.*--immutable\b|\bpnpm install\b.*--frozen-lockfile\b"
)


def ci_installs_frozen(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    offences: list[str] = []
    frozen: set[str] = set()
    for step in _workflow_steps(repo):
        offences.extend(f"{step.path} ({step.job}): {o}" for o in _install_offences(step.run))
        for line in _logical_lines(step.run):
            if _FROZEN_PY.search(line):
                frozen.add("python")
            if _FROZEN_NODE.search(line):
                frozen.add("node")
    if offences:
        return _fail("; ".join(offences))
    # A stack whose graph is never installed frozen has not satisfied this
    # control — a TypeScript repo with no workflows at all used to pass it
    # vacuously, because only python was ever required (§ D).
    missing = [
        stack
        for stack, manifest in (("python", "pyproject.toml"), ("node", "package.json"))
        if repo.exists(manifest) and stack not in frozen
    ]
    if missing:
        return _fail(
            "no CI step installs the dependency graph in frozen mode for: " + ", ".join(missing)
        )
    return _ok("every CI install is frozen or exact-pinned")


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


def _pyproject(repo: Repo) -> dict[str, Any]:
    if not repo.exists("pyproject.toml"):
        return {}
    return tomllib.loads(repo.read("pyproject.toml"))


def linter_wired_at_all_loci(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    problems = []
    if repo.exists("pyproject.toml"):
        has_config = "ruff" in _pyproject(repo).get("tool", {}) or any(
            repo.exists(p) for p in ("ruff.toml", ".ruff.toml")
        )
        if not has_config:
            problems.append("python: no ruff configuration")
        if "charliermarsh.ruff" not in _devcontainer_extensions(repo):
            problems.append(
                "python: editor locus — devcontainer does not install the ruff extension"
            )
        if not _hook_mentions(repo, "ruff"):
            problems.append("python: pre-commit locus — no ruff hook")
        if not _ci_run_mentions(repo, r"\bruff check\b", hook="ruff"):
            problems.append("python: ci locus — no step runs ruff check")
    if repo.exists("tsconfig.json"):
        has_config = any(repo.glob_basename(p) for p in ("eslint.config.*", ".eslintrc*"))
        if not has_config:
            problems.append("typescript: no eslint configuration")
        if "dbaeumer.vscode-eslint" not in _devcontainer_extensions(repo):
            problems.append(
                "typescript: editor locus — devcontainer does not install the eslint extension"
            )
        if not _hook_mentions(repo, "eslint"):
            problems.append("typescript: pre-commit locus — no eslint hook")
        if not _ci_run_mentions(repo, r"\beslint\b", hook="eslint"):
            problems.append("typescript: ci locus — no step runs eslint")
    if problems:
        return _fail("; ".join(problems))
    return _ok("linter wired at editor, pre-commit and ci from one configuration")


# `|| :` is the terse spelling of `|| true` — `:` is the shell no-op builtin, and
# it was outside the set, so the commonest short idiom for swallowing a failure
# went undetected (§ D).
_SUPPRESSION = re.compile(
    r"\|\|\s*true\b|\|\|\s*:\s*(?:$|[;&|])|\|\|\s*exit 0\b|\bset \+e\b|--exit-zero\b",
    re.MULTILINE,
)


def no_failure_suppression(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    problems = []
    for step in _workflow_steps(repo):
        if step.suppressed:
            target = step.run.strip().splitlines()[0] if step.run.strip() else step.uses
            problems.append(f"{step.path} ({step.job}): continue-on-error on '{target}'")
        if match := _SUPPRESSION.search(step.run):
            problems.append(f"{step.path} ({step.job}): '{match.group(0)}' in run")
    if problems:
        return _fail("; ".join(problems))
    return _ok("no CI step suppresses a failure")


def _ini_mypy_strict(repo: Repo) -> bool:
    """mypy configured in its own file rather than in `pyproject.toml`.

    Only `[tool.mypy]` was read, so a repo configuring mypy in `mypy.ini` or
    `setup.cfg` — both supported by mypy itself — failed a control it satisfied
    (§ D).
    """
    for path, section in ((".mypy.ini", "[mypy]"), ("mypy.ini", "[mypy]"), ("setup.cfg", "[mypy]")):
        if not repo.exists(path):
            continue
        parser = configparser.ConfigParser()
        try:
            parser.read_string(repo.read(path))
        except configparser.Error:
            continue
        if parser.has_section(section.strip("[]")) and parser.getboolean(
            section.strip("[]"), "strict", fallback=False
        ):
            return True
    return False


def _blanket_mypy_overrides(repo: Repo) -> list[str]:
    """Overrides that switch checking off for everything, wherever they live."""
    problems: list[str] = []
    overrides = _pyproject(repo).get("tool", {}).get("mypy", {}).get("overrides", [])
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
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    problems = []
    if repo.exists("pyproject.toml"):
        mypy_config = _pyproject(repo).get("tool", {}).get("mypy", {})
        strict = mypy_config.get("strict") is True or _ini_mypy_strict(repo)
        if not strict:
            problems.append("python: mypy strict mode is not set")
        # `strict = true` alongside a blanket override that ignores errors is
        # not strict typing — it is strict typing switched off in a second
        # place. TYP-001's title forbids a per-file opt-out and nothing read
        # the overrides (§ D).
        problems.extend(f"python: {o}" for o in _blanket_mypy_overrides(repo))
        if not _hook_mentions(repo, "mypy"):
            problems.append("python: pre-commit locus — no mypy hook")
        mypy_steps = [s for s in _workflow_steps(repo) if re.search(r"\bmypy\b", s.run)]
        if not mypy_steps:
            problems.append("python: ci locus — no step runs mypy")
        elif any(s.suppressed or _SUPPRESSION.search(s.run) for s in mypy_steps):
            problems.append("python: the mypy CI step suppresses its failure")
    if repo.exists("tsconfig.json"):
        config = load_jsonc(repo.root / "tsconfig.json")
        options = config.get("compilerOptions", {}) if isinstance(config, dict) else {}
        if not (isinstance(options, dict) and options.get("strict") is True):
            problems.append("typescript: compilerOptions.strict is not true")
        if not _ci_run_mentions(repo, r"\btsc\b", hook="tsc"):
            problems.append("typescript: ci locus — no step runs tsc")
    if problems:
        return _fail("; ".join(problems))
    return _ok("type checking is strict and blocks in CI")


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
        f"{s.path} ({s.job})" for s in test_steps if s.suppressed or _SUPPRESSION.search(s.run)
    ]
    if absorbed:
        return _fail("the test step's exit code is absorbed: " + "; ".join(absorbed))
    return _ok("the test command runs in CI and its exit code is the verdict")


COMMAND_ASSERTS: dict[str, AssertFn] = {
    "no-static-cloud-keys": no_static_cloud_keys,
    "ci-installs-frozen": ci_installs_frozen,
    "actions-pinned-to-sha": actions_pinned_to_sha,
    "linter-wired-at-all-loci": linter_wired_at_all_loci,
    "no-failure-suppression": no_failure_suppression,
    "typecheck-strict-and-blocking": typecheck_strict_and_blocking,
    "tests-run-and-block": tests_run_and_block,
}
