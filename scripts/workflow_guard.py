#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse

from scripts.common import REPO_ROOT
from scripts.workflow_contract import load_workflow_contract, validate_workflow_contract


REQUIRED_FILES = (
    Path("WORKFLOW.md"),
    Path("docs/process/agent-loop.md"),
    Path("docs/process/worktree-lifecycle.md"),
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 WORKFLOW 契约与 repo harness 运行协议。")
    parser.add_argument("--mode", choices=("ci", "pre-commit"), default="ci")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    return parser.parse_args(argv)


def validate_repository(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        target = repo_root / path
        if not target.exists():
            errors.append(f"缺少必需文件 `{path.as_posix()}`")

    workflow_path = repo_root / "WORKFLOW.md"
    if not workflow_path.exists():
        return errors

    try:
        contract, body = load_workflow_contract(workflow_path)
    except Exception as exc:
        errors.append(str(exc))
        return errors

    errors.extend(validate_workflow_contract(contract, body))
    return errors


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    errors = validate_repository(repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("workflow-guard 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
