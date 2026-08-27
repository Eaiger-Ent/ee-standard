"""The register-check command line.

    register-check                 # all applicable controls
    register-check run --tier 1    # subset
    register-check run --control SEC-001   # one control, as a gate verifies itself
    register-check schema          # validate controls.yaml itself
    register-check meta GOV-001    # one meta-control
    register-check assert <name>   # one command assert
    register-check explain SEC-001 # what it checks, why, and the standard it cites
    register-check deployments     # which gates are deployed here, and which are owed

Exit codes for a run, per ADR 0016:

    0  every applicable control was verified, and none is violated
    1  at least one verified violation
    2  usage error, or a target that is not a repository
    3  no violation found, but at least one applicable control could not be
       verified — a missing tool, or a remote block with no credentials

`--require-complete` promotes 3 to 1, for the pipeline that must be
authoritative. A predicate skip is not incompleteness: a repo with no Terraform
genuinely satisfies IAC-001's applicability, so those runs still exit 0.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from register_check.deployments import NoPlugin, find_plugin
from register_check.deployments import build as build_deployments
from register_check.deployments import render as render_deployments
from register_check.meta import META_CHECKS
from register_check.register import Control, Register, load_register
from register_check.remote import resolve as resolve_remote
from register_check.repo import NotAGitRepository, Repo, require_git_repo
from register_check.report import render
from register_check.runner import Verdict, exit_code, run_command_assert, run_control
from register_check.verify_meta import run_meta_control


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="register-check",
        description="Conformance checker for the Equal Experts control register.",
    )
    # The liveness probe `register-adopt` and `register-install` both run before
    # anything else. It did not exist until Phase 4 ran the front door in a
    # repository that did not author the standard and both skills stopped on
    # `unrecognized arguments: --version` — a checker installed correctly,
    # pinned correctly, and unusable because nothing could ask it whether it was
    # there. Read from the installed distribution rather than written here: a
    # literal would be a second copy of `pyproject.toml`'s version, free to
    # drift from the tag the register pins.
    parser.add_argument(
        "--version",
        action="version",
        version=f"register-check {version('register-check')}",
        help="print the installed checker's version and exit",
    )
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="repository to check (default: cwd)"
    )
    parser.add_argument(
        "--register",
        type=Path,
        default=None,
        help="path to controls.yaml (default: <repo>/controls.yaml)",
    )
    parser.add_argument(
        "--github-repo",
        metavar="OWNER/NAME",
        default=None,
        help=(
            "the GitHub repository remote checks ask about "
            "(default: inferred from the origin remote)"
        ),
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="exit 1 rather than 3 when a control could not be verified",
    )
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="run all applicable controls (the default)")
    run.add_argument("--tier", type=int, choices=(1, 2, 3), default=None)
    run.add_argument(
        "--control",
        action="append",
        metavar="ID",
        default=None,
        help="verify only this control (repeatable); the gate skills' verify step",
    )
    sub.add_parser("schema", help="validate controls.yaml itself")
    meta = sub.add_parser("meta", help="run one meta-control")
    meta.add_argument("id", metavar="GOV-NNN")
    check = sub.add_parser("assert", help="run one command assert")
    check.add_argument("name")
    explain = sub.add_parser("explain", help="what a control checks, and why")
    explain.add_argument("id", metavar="ID")
    deployments = sub.add_parser(
        "deployments", help="which gates are deployed here, and which are owed a re-run"
    )
    deployments.add_argument(
        "--plugin",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "the plugin root whose .claude-plugin/deploys.json declares the gates "
            "(default: $CLAUDE_PLUGIN_ROOT, then <repo>/plugins/control-register)"
        ),
    )
    return parser


def _load(repo_path: Path, register_path: Path | None) -> tuple[Register | None, int]:
    path = register_path or repo_path / "controls.yaml"
    register, errors = load_register(path)
    if register is None:
        print(f"schema: {path} is not a valid register:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return None, 1
    return register, 0


def _cmd_schema(repo_path: Path, register_path: Path | None) -> int:
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    print(
        f"schema: OK — register v{register.version} (contract "
        f"{register.register_contract}), {len(register.controls)} controls, "
        f"{len(register.meta_controls)} meta-controls"
    )
    return 0


def _cmd_run(
    repo_path: Path,
    register_path: Path | None,
    tier: int | None,
    require_complete: bool,
    ids: list[str] | None = None,
    github_repo: str | None = None,
) -> int:
    """A conformance run, optionally narrowed to a tier or to named controls.

    `--control` is the entry point a `gate-*` skill's verify step uses. It runs
    the control's own verify blocks through `run_control` — the same function
    the full audit calls — so a gate and the auditor cannot disagree about what
    the control means. A gate that verified itself some other way would be the
    second copy this repository exists to prevent.
    """
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    repo = Repo(repo_path)
    controls = [c for c in register.controls if tier is None or c.tier == tier]
    if ids is not None:
        wanted = list(dict.fromkeys(ids))
        known = {c.id for c in controls}
        # An id nobody defines is a usage error, never an empty green run: a
        # gate that misspells its own control would otherwise report success
        # having verified nothing, which is § A's defect with a typo for a cause.
        unknown = [i for i in wanted if i not in known]
        if unknown:
            print(
                f"no control {', '.join(unknown)} in the selected set — "
                f"known: {', '.join(sorted(known))}",
                file=sys.stderr,
            )
            return 2
        controls = [c for c in controls if c.id in wanted]
    # Resolved once for the whole run and handed to every control. Resolving
    # per block would let two blocks in one report describe different
    # repositories, and a report that does not say which repository it is about
    # is not evidence about any of them.
    remote = resolve_remote(repo, github_repo)
    results = [run_control(control, register, repo, remote) for control in controls]
    # Meta-controls audit the register as a whole, so they are not part of
    # verifying one control's deployment. Narrowing the run drops them.
    meta_results = (
        []
        if ids is not None
        else [run_meta_control(meta, register, repo, remote) for meta in register.meta_controls]
    )
    print(render(register, results, meta_results))
    verdicts = [r.verdict for r in results] + [m[2] for m in meta_results]
    # A predicate-skipped control ran nothing, so its partial declarations say
    # nothing about this run — counting them would make exit 3 fire for controls
    # that legitimately do not apply.
    partial = any(
        block.block.partial is not None
        for result in results
        if result.verdict is not Verdict.SKIPPED_PREDICATE
        for block in result.blocks
    ) or any(
        block.partial is not None
        for meta in (register.meta_controls if ids is None else [])
        for block in meta.verify
    )
    return exit_code(verdicts, require_complete=require_complete, partial=partial)


def _cmd_meta(
    repo_path: Path,
    register_path: Path | None,
    meta_id: str,
    require_complete: bool,
    github_repo: str | None = None,
) -> int:
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    if meta_id not in META_CHECKS:
        print(
            f"unknown meta-control '{meta_id}' — known: {', '.join(sorted(META_CHECKS))}",
            file=sys.stderr,
        )
        return 2
    repo = Repo(repo_path)
    verdict, message = META_CHECKS[meta_id](register, repo, resolve_remote(repo, github_repo))
    print(f"{meta_id}: {verdict} — {message}")
    return exit_code([verdict], require_complete=require_complete)


def _cmd_assert(repo_path: Path, register_path: Path | None, name: str) -> int:
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    passed, message = run_command_assert(name, register, Repo(repo_path))
    print(f"assert {name}: {'PASS' if passed else 'FAIL'} — {message}")
    return 0 if passed else 1


def _cmd_explain(repo_path: Path, register_path: Path | None, control_id: str) -> int:
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    control = register.control(control_id)
    if control is None:
        print(f"no control '{control_id}' in the register", file=sys.stderr)
        return 2
    print(f"{control.id} — {control.title}")
    print(f"\nEnforces: {control.enforces}")
    if isinstance(control, Control):
        print(f"Standard: {control.standard.name} <{control.standard.url}>")
        print(
            f"Tier {control.tier}, rung: {control.rung}, "
            f"locus: {', '.join(control.locus)}, variance: {control.variance}"
        )
        print(f"Applies to: {', '.join(control.applies_to)}")
        print(f"Owner: {control.owner}; review by {control.review_by.isoformat()}")
        print(f"Rationale: {control.rationale_adr}")
        if control.deployed_by:
            print(f"Deployed by: {control.deployed_by}")
    else:
        print(f"\nRationale: {control.rationale}")
    print("\nVerification:")
    for block in control.verify:
        print(f"  - {block.describe()}")
    return 0


def _cmd_deployments(repo_path: Path, register_path: Path | None, plugin: Path | None) -> int:
    """Report deployment currency, gate by gate.

    Exit `0` over any number of stale or undeployed gates: staleness is
    reported and never enforced (`docs/00-concepts.md` § Notify, never
    redeploy), and a command that failed over one would be enforcing
    redeployment through the back door. Exit `1` only for a defect — a stamp
    claiming a contract the installed gate has not reached — which is the same
    thing `provenance_stamp_present` already fails a register contract for.
    """
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    try:
        root = find_plugin(Repo(repo_path), plugin)
        report = build_deployments(Repo(repo_path), root, register)
    except NoPlugin as exc:
        print(f"deployments: {exc}", file=sys.stderr)
        return 2
    print(render_deployments(report, register))
    return 1 if report.defective else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_path: Path = args.repo.resolve()
    register_path: Path | None = args.register
    try:
        # Only the commands that evaluate the repository need it to be one;
        # `schema` and `explain` read the register and nothing else.
        if args.command in (None, "run", "assert", "meta", "deployments"):
            require_git_repo(repo_path)
        return _dispatch(args, repo_path, register_path)
    except NotAGitRepository as exc:
        print(f"register-check: {exc}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace, repo_path: Path, register_path: Path | None) -> int:
    match args.command:
        case None:
            return _cmd_run(
                repo_path, register_path, None, args.require_complete, None, args.github_repo
            )
        case "run":
            return _cmd_run(
                repo_path,
                register_path,
                args.tier,
                args.require_complete,
                args.control,
                args.github_repo,
            )
        case "schema":
            return _cmd_schema(repo_path, register_path)
        case "meta":
            return _cmd_meta(
                repo_path, register_path, args.id, args.require_complete, args.github_repo
            )
        case "assert":
            return _cmd_assert(repo_path, register_path, args.name)
        case "explain":
            return _cmd_explain(repo_path, register_path, args.id)
        case "deployments":
            return _cmd_deployments(repo_path, register_path, args.plugin)
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
