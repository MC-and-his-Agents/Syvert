#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import py_compile
import tempfile

from scripts.common import REPO_ROOT, git_changed_files, git_current_branch
from scripts.context_guard import infer_current_issue, validate_context_rules, validate_repository as validate_context_repository
from scripts.item_context import matching_exec_plan_for_issue
from scripts.open_pr import validate_pr_preflight
from scripts.policy.policy import classify_paths
from scripts.pr_scope_guard import build_report
from scripts.workflow_guard import validate_repository as validate_workflow_repository


def infer_pr_class(changed_paths: list[str]) -> str:
    categories = {item.category for item in classify_paths(changed_paths)}
    if "governance" in categories:
        return "governance"
    if "spec" in categories:
        return "spec"
    if categories and categories <= {"docs"}:
        return "docs"
    return "implementation"


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

REQUIRED_LOOM_CARRIER_FILES = (
    Path(".loom/README.md"),
    Path(".loom/bootstrap/manifest.json"),
    Path(".loom/bootstrap/init-result.json"),
    Path(".loom/bin/loom_init.py"),
    Path(".loom/bin/loom_flow.py"),
    Path(".loom/bin/loom_check.py"),
    Path(".loom/companion/manifest.json"),
    Path(".loom/companion/repo-interface.json"),
    Path(".loom/companion/interop.json"),
    Path(".loom/reviews/INIT-0001.json"),
    Path(".loom/reviews/INIT-0001.spec.json"),
    Path(".loom/specs/INIT-0001/spec.md"),
    Path(".loom/status/current.md"),
    Path(".loom/progress/INIT-0001.md"),
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


def validate_loom_carrier_repository(repo_root: Path, changed_paths: list[str]) -> list[str]:
    if not any(path == ".loom" or path.startswith(".loom/") for path in changed_paths):
        return []

    errors: list[str] = []
    for relative_path in REQUIRED_LOOM_CARRIER_FILES:
        if not (repo_root / relative_path).exists():
            errors.append(f"缺少 Loom carrier 必需工件: {repo_root / relative_path}")

    loom_root = repo_root / ".loom"
    if loom_root.exists():
        for json_path in sorted(loom_root.rglob("*.json")):
            try:
                with json_path.open("r", encoding="utf-8") as handle:
                    json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Loom carrier JSON 无效: {json_path}: {exc}")

        bin_root = loom_root / "bin"
        if bin_root.exists():
            with tempfile.TemporaryDirectory(prefix="syvert-loom-pycompile-") as temp_dir:
                temp_root = Path(temp_dir)
                for index, py_path in enumerate(sorted(bin_root.glob("*.py"))):
                    try:
                        py_compile.compile(
                            str(py_path),
                            cfile=str(temp_root / f"{index}-{py_path.name}c"),
                            doraise=True,
                        )
                    except py_compile.PyCompileError as exc:
                        errors.append(f"Loom carrier Python 语法无效: {py_path}: {exc.msg}")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    base_ref = args.base_ref or args.base_sha
    head_ref = args.head_sha or args.head_ref
    if not base_ref:
        print("governance-gate 需要 `--base-ref` 或 `--base-sha`。", file=sys.stderr)
        return 1

    changed = git_changed_files(base_ref, head_ref, repo=repo_root)
    inferred_pr_class = infer_pr_class(changed)
    report = build_report(inferred_pr_class, changed)
    if report["violations"]:
        print("治理基线改动不得超出 governance PR 允许范围。", file=sys.stderr)
        for item in report["violations"]:
            print(f"- {item['path']} ({item['category']})", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(validate_workflow_repository(repo_root))
    errors.extend(validate_context_repository(repo_root))
    errors.extend(validate_loom_carrier_repository(repo_root, changed))
    current_issue = infer_current_issue(args.head_ref)
    if current_issue is None and args.head_sha is None:
        current_issue = infer_current_issue(git_current_branch(repo=repo_root))
    if current_issue is None:
        errors.append("governance-gate 无法从 `--head-ref` 或当前分支推断当前事项，已拒绝继续执行。")
    else:
        errors.extend(validate_context_rules(repo_root, changed, current_issue=current_issue))
        active_exec_plan = matching_exec_plan_for_issue(repo_root, current_issue)
        if active_exec_plan:
            if inferred_pr_class in {"governance", "spec", "implementation", "docs"}:
                errors.extend(
                    validate_pr_preflight(
                        inferred_pr_class,
                        current_issue,
                        active_exec_plan.get("item_key"),
                        active_exec_plan.get("item_type"),
                        active_exec_plan.get("release"),
                        active_exec_plan.get("sprint"),
                        changed,
                        repo_root=repo_root,
                        validate_worktree_binding_check=False,
                    )
                )
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
