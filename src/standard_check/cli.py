"""The standard-check command line.

    standard-check                 # all applicable controls; exit 1 on any failure
    standard-check --tier 1        # subset
    standard-check schema          # validate controls.yaml itself
    standard-check meta GOV-001    # one meta-control
    standard-check assert <name>   # one command assert
    standard-check explain SEC-001 # what it checks, why, and the standard it cites
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from standard_check.meta import META_CHECKS
from standard_check.register import Control, Register, load_register
from standard_check.repo import Repo
from standard_check.report import render
from standard_check.runner import Verdict, run_command_assert, run_control
from standard_check.verify_meta import run_meta_control


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="standard-check",
        description="Conformance checker for the ee-standard control register.",
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
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="run all applicable controls (the default)")
    run.add_argument("--tier", type=int, choices=(1, 2, 3), default=None)
    sub.add_parser("schema", help="validate controls.yaml itself")
    meta = sub.add_parser("meta", help="run one meta-control")
    meta.add_argument("id", metavar="GOV-NNN")
    check = sub.add_parser("assert", help="run one command assert")
    check.add_argument("name")
    explain = sub.add_parser("explain", help="what a control checks, and why")
    explain.add_argument("id", metavar="ID")
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


def _cmd_run(repo_path: Path, register_path: Path | None, tier: int | None) -> int:
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    repo = Repo(repo_path)
    controls = [c for c in register.controls if tier is None or c.tier == tier]
    results = [run_control(control, register, repo) for control in controls]
    meta_results = [run_meta_control(meta, register, repo) for meta in register.meta_controls]
    print(render(register, results, meta_results))
    failed = any(r.verdict in (Verdict.FAIL, Verdict.UNCLASSIFIED) for r in results)
    meta_failed = any(not passed for _id, _title, passed, _msg in meta_results)
    return 1 if failed or meta_failed else 0


def _cmd_meta(repo_path: Path, register_path: Path | None, meta_id: str) -> int:
    register, code = _load(repo_path, register_path)
    if register is None:
        return code
    if meta_id not in META_CHECKS:
        print(
            f"unknown meta-control '{meta_id}' — known: {', '.join(sorted(META_CHECKS))}",
            file=sys.stderr,
        )
        return 2
    passed, message = META_CHECKS[meta_id](register, Repo(repo_path))
    print(f"{meta_id}: {'PASS' if passed else 'FAIL'} — {message}")
    return 0 if passed else 1


def _cmd_assert(repo_path: Path, name: str) -> int:
    passed, message = run_command_assert(name, Repo(repo_path))
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


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_path: Path = args.repo.resolve()
    register_path: Path | None = args.register
    match args.command:
        case None:
            return _cmd_run(repo_path, register_path, None)
        case "run":
            return _cmd_run(repo_path, register_path, args.tier)
        case "schema":
            return _cmd_schema(repo_path, register_path)
        case "meta":
            return _cmd_meta(repo_path, register_path, args.id)
        case "assert":
            return _cmd_assert(repo_path, args.name)
        case "explain":
            return _cmd_explain(repo_path, register_path, args.id)
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
