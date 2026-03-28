#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import os
import tempfile

from scripts.common import (
    REPO_ROOT,
    format_changed_files,
    git_changed_files,
    git_current_branch,
    git_fetch_branch,
    require_cli,
    run,
)
from scripts.policy.policy import formal_spec_dirs, get_policy, risk_level, spec_suite_policy
from scripts.pr_scope_guard import build_report


TEMPLATE_PATH = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="创建受控 PR。")
    parser.add_argument("--class", dest="pr_class", required=True, choices=get_policy()["pr_classes"])
    parser.add_argument("--issue", type=int)
    parser.add_argument("--title")
    parser.add_argument("--base", default="main")
    parser.add_argument("--closing", default="fixes", choices=get_policy()["closing_modes"])
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def ensure_not_main(branch: str) -> None:
    if branch == "main":
        raise SystemExit("当前分支是 main，请切到独立分支后再创建 PR。")


def latest_commit_subject() -> str:
    return run(["git", "log", "-1", "--pretty=%s"], cwd=REPO_ROOT).stdout.strip()


def risk_reason_for_class(pr_class: str) -> str:
    reasons = {
        "governance": "涉及治理基线、门禁机制或工作流入口。",
        "spec": "涉及正式规约区，必须先收口契约边界。",
        "implementation": "涉及实现或测试改动，需要验证行为变化。",
        "docs": "仅包含文档层改动，不应混入治理或实现行为变化。",
    }
    return reasons[pr_class]


def closing_line(issue: int | None, mode: str) -> str:
    if not issue or mode == "none":
        return "无"
    prefix = "Fixes" if mode == "fixes" else "Refs"
    return f"{prefix} #{issue}"


def has_bootstrap_contract(repo_root: Path) -> bool:
    decisions_dir = repo_root / "docs" / "decisions"
    exec_plans_dir = repo_root / "docs" / "exec-plans"
    decision_files = [path for path in decisions_dir.glob("*.md") if path.name != "README.md"] if decisions_dir.exists() else []
    exec_plan_files = [path for path in exec_plans_dir.glob("*.md") if path.name != "README.md"] if exec_plans_dir.exists() else []
    return bool(decision_files and exec_plan_files)


def has_formal_spec_input(repo_root: Path, changed_files: list[str]) -> bool:
    if formal_spec_dirs(changed_files):
        return True
    specs_root = repo_root / "docs" / "specs"
    if not specs_root.exists():
        return False
    required_files = set(spec_suite_policy()["required_files"])
    for path in specs_root.iterdir():
        if not path.is_dir() or not path.name.startswith("FR-"):
            continue
        child_names = {child.name for child in path.iterdir()}
        if required_files.issubset(child_names):
            return True
    return False


def issue_requires_formal_input(issue: int) -> bool:
    require_cli("gh")
    completed = run(
        [
            "gh",
            "issue",
            "view",
            str(issue),
            "--json",
            "title,labels",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return False

    payload = json.loads(completed.stdout or "{}")
    title = str(payload.get("title") or "")
    labels = {
        str(item.get("name", "")).lower()
        for item in payload.get("labels", [])
        if isinstance(item, dict)
    }
    return "FR-" in title.upper() or any(label in {"core", "governance", "spec"} or label.startswith("fr-") for label in labels)


def validate_pr_preflight(pr_class: str, issue: int | None, changed_files: list[str], *, repo_root: Path) -> list[str]:
    errors: list[str] = []

    if pr_class == "governance" and issue is None:
        errors.append("`governance` 类 PR 必须绑定 Issue。")

    if pr_class == "spec" and not formal_spec_dirs(changed_files):
        errors.append("`spec` 类 PR 必须包含正式规约区变更。")

    if pr_class in {"governance", "spec"}:
        if not (has_formal_spec_input(repo_root, changed_files) or has_bootstrap_contract(repo_root)):
            errors.append("核心事项缺少 formal spec 或 bootstrap contract。")

    if pr_class == "governance" and not (has_formal_spec_input(repo_root, changed_files) or has_bootstrap_contract(repo_root)):
        errors.append("`governance` 类 PR 缺少 `exec-plan` 或 formal spec 套件。")

    if pr_class == "implementation" and issue is not None and issue_requires_formal_input(issue):
        if not (has_formal_spec_input(repo_root, changed_files) or has_bootstrap_contract(repo_root)):
            errors.append("绑定 Issue 的实现事项缺少 formal spec 或 bootstrap contract。")

    return errors


def build_body(args: argparse.Namespace, changed_files: list[str]) -> str:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"缺少 PR 模板: {TEMPLATE_PATH}")
    body = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "{{PR_CLASS}}": args.pr_class,
        "{{ISSUE}}": f"#{args.issue}" if args.issue else "无",
        "{{CLOSING}}": closing_line(args.issue, args.closing),
        "{{RISK_LEVEL}}": risk_level(args.pr_class),
        "{{RISK_REASON}}": risk_reason_for_class(args.pr_class),
        "{{CHANGED_FILES}}": format_changed_files(changed_files),
        "{{VALIDATION_SUGGESTION}}": "- 已执行：\n- 未执行：",
        "{{ROLLBACK}}": "如需回滚，使用独立 revert PR 撤销本次变更。",
    }
    for token, value in replacements.items():
        body = body.replace(token, value)
    return body


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    branch = git_current_branch(repo=REPO_ROOT)
    ensure_not_main(branch)
    git_fetch_branch(args.base, repo=REPO_ROOT)
    changed_files = git_changed_files(f"origin/{args.base}", repo=REPO_ROOT)
    report = build_report(args.pr_class, changed_files)
    if report["violations"]:
        print("PR class 与改动类别不一致：", file=sys.stderr)
        for item in report["violations"]:
            print(f"- {item['path']} ({item['category']})", file=sys.stderr)
        return 1
    preflight_errors = validate_pr_preflight(args.pr_class, args.issue, changed_files, repo_root=REPO_ROOT)
    if preflight_errors:
        for error in preflight_errors:
            print(error, file=sys.stderr)
        return 1

    title = args.title or latest_commit_subject()
    body = build_body(args, changed_files)

    if args.dry_run:
        print(title)
        print(body)
        return 0

    require_cli("gh")
    run(["gh", "auth", "status"], cwd=REPO_ROOT)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(body)
        body_path = Path(handle.name)

    try:
        command = ["gh", "pr", "create", "--base", args.base, "--title", title, "--body-file", str(body_path)]
        if args.draft:
            command.append("--draft")
        completed = run(command, cwd=REPO_ROOT)
        print(completed.stdout.strip())
        return 0
    finally:
        if body_path.exists():
            os.unlink(body_path)


if __name__ == "__main__":
    raise SystemExit(main())
