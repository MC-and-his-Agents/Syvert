#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import re

from scripts.common import REPO_ROOT, git_changed_files, git_current_branch
from scripts.context_guard import validate_context_rules, validate_repository as validate_context_repository
from scripts.policy.policy import classify_paths
from scripts.workflow_guard import validate_repository as validate_workflow_repository


REQUIRED_GOVERNANCE_FILES = (
    Path("WORKFLOW.md"),
    Path("docs/process/agent-loop.md"),
    Path("docs/process/branch-retirement.md"),
    Path("docs/process/worktree-lifecycle.md"),
    Path("scripts/create_worktree.py"),
    Path("scripts/governance_status.py"),
    Path("scripts/retire_branch.py"),
    Path("scripts/context_guard.py"),
    Path("scripts/workflow_guard.py"),
    Path("scripts/sync_repo_settings.py"),
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验治理基线变更是否保持纯度。")
    parser.add_argument("--mode", choices=("ci", "local"), default="local")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--base-ref")
    parser.add_argument("--base-sha")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--head-sha")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    base_ref = args.base_ref or args.base_sha
    head_ref = args.head_sha or args.head_ref
    if not base_ref:
        print("governance-gate 需要 `--base-ref` 或 `--base-sha`。", file=sys.stderr)
        return 1

    changed = git_changed_files(base_ref, head_ref, repo=repo_root)
    classified = classify_paths(changed)
    categories = {item.category for item in classified}
    if "governance" in categories and "implementation" in categories:
        print("治理基线改动不得与实现代码混在同一 PR。", file=sys.stderr)
        for item in classified:
            if item.category == "implementation":
                print(f"- {item.path}", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(validate_workflow_repository(repo_root))
    errors.extend(validate_context_repository(repo_root))
    current_issue = None
    branch = git_current_branch(repo=repo_root)
    match = re.match(r"^issue-(\d+)(?:-|$)", branch)
    if match:
        current_issue = int(match.group(1))
    errors.extend(validate_context_rules(repo_root, changed, current_issue=current_issue))
    for relative_path in REQUIRED_GOVERNANCE_FILES:
        if not (repo_root / relative_path).exists():
            errors.append(f"缺少治理栈 v2 必需工件: {repo_root / relative_path}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("governance-gate 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
