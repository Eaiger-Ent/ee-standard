"""Command assertions — the `standard-check assert <name>` closed set.

These are the checks the register invokes as `kind: command` verify blocks.
They read workflow and configuration files; none of them executes anything.
"""

from __future__ import annotations

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


def _workflow_steps(repo: Repo) -> Iterator[WorkflowStep]:
    for path in repo.workflow_files():
        doc = yaml.safe_load(repo.read(path))
        if not isinstance(doc, dict):
            continue
        jobs = doc.get("jobs")
        if not isinstance(jobs, dict):
            continue
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            job_suppressed = job.get("continue-on-error") is True
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                yield WorkflowStep(
                    path=path,
                    job=str(job_id),
                    run=str(step.get("run") or ""),
                    uses=str(step.get("uses") or ""),
                    suppressed=job_suppressed or step.get("continue-on-error") is True,
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


def no_static_cloud_keys(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    findings: list[str] = []
    for path in repo.workflow_files():
        text = repo.read(path)
        findings.extend(f"{path}: references {name}" for name in _STATIC_KEY_NAMES if name in text)
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


def _install_offences(run: str) -> Iterator[str]:
    for raw_line in run.splitlines():
        line = raw_line.split("#")[0]
        for command in re.split(r"&&|\|\||;", line):
            words = command.strip().split()
            if not words:
                continue
            text = " ".join(words)
            if re.search(r"\buv sync\b", text) and not re.search(r"--(frozen|locked)\b", text):
                yield f"'{text}' re-resolves — use uv sync --frozen"
            elif re.search(r"\b(uv )?pip install\b", text):
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


_FROZEN_PY = re.compile(r"\buv sync\b.*--(frozen|locked)\b|\bpip install\b.*-r\s+\S+")


def ci_installs_frozen(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    offences: list[str] = []
    frozen_python_install = False
    for step in _workflow_steps(repo):
        offences.extend(f"{step.path} ({step.job}): {o}" for o in _install_offences(step.run))
        if _FROZEN_PY.search(step.run):
            frozen_python_install = True
    if offences:
        return _fail("; ".join(offences))
    if repo.exists("pyproject.toml") and not frozen_python_install:
        return _fail("no CI step installs the python dependency graph in frozen mode")
    return _ok("every CI install is frozen or exact-pinned")


_SHA40 = re.compile(r"^[0-9a-f]{40}$")


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
        if not at or not _SHA40.match(ref):
            problems.append(f"{step.path} ({step.job}): uses {uses}")
    if problems:
        return _fail("not pinned to a 40-character commit SHA: " + "; ".join(problems))
    return _ok("every third-party action reference is a full commit SHA")


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


def _ci_run_mentions(repo: Repo, pattern: str) -> bool:
    return any(re.search(pattern, step.run) for step in _workflow_steps(repo))


def _devcontainer_extensions(repo: Repo) -> list[str]:
    if not repo.exists(".devcontainer/devcontainer.json"):
        return []
    config = load_jsonc(repo.root / ".devcontainer/devcontainer.json")
    if not isinstance(config, dict):
        return []
    customizations = config.get("customizations")
    vscode = customizations.get("vscode") if isinstance(customizations, dict) else None
    extensions = vscode.get("extensions") if isinstance(vscode, dict) else None
    return [str(e) for e in extensions] if isinstance(extensions, list) else []


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
        if not _ci_run_mentions(repo, r"\bruff check\b"):
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
        if not _ci_run_mentions(repo, r"\beslint\b"):
            problems.append("typescript: ci locus — no step runs eslint")
    if problems:
        return _fail("; ".join(problems))
    return _ok("linter wired at editor, pre-commit and ci from one configuration")


_SUPPRESSION = re.compile(r"\|\|\s*true\b|\|\|\s*exit 0\b|\bset \+e\b|--exit-zero\b")


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


def typecheck_strict_and_blocking(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    problems = []
    if repo.exists("pyproject.toml"):
        mypy_config = _pyproject(repo).get("tool", {}).get("mypy", {})
        if mypy_config.get("strict") is not True:
            problems.append("python: [tool.mypy] strict = true is not set")
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
        if not _ci_run_mentions(repo, r"\btsc\b"):
            problems.append("typescript: ci locus — no step runs tsc")
    if problems:
        return _fail("; ".join(problems))
    return _ok("type checking is strict and blocks in CI")


_TEST_COMMAND = re.compile(
    r"\bpytest\b|\bnpm test\b|\bvitest\b|\bjest\b|\bgo test\b|\bcargo test\b"
)


def tests_run_and_block(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    test_steps = [s for s in _workflow_steps(repo) if _TEST_COMMAND.search(s.run)]
    if not test_steps:
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
