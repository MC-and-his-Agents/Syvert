#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import os
import re
import tempfile

from scripts.item_context import (
    ITEM_TYPES,
    INPUT_MODE_BOOTSTRAP,
    INPUT_MODE_FORMAL_SPEC,
    INPUT_MODE_UNBOUND,
    active_exec_plans_for_issue,
    allows_legacy_metadata_free_formal_spec_decision,
    validate_additional_spec_contracts,
    classify_exec_plan_input_mode,
    load_item_context_from_exec_plan,
    spec_dir_has_minimum_suite,
    validate_bound_decision_contract,
    validate_bound_spec_contract,
    normalize_bound_spec_dir,
    normalize_issue,
    valid_item_key,
    validate_bound_formal_spec_scope,
)
from scripts.context_guard import (
    is_exec_plan_file,
    is_legacy_todo_file,
    validate_legacy_todo_cleanup_foreign_exec_plan_touch,
)

from scripts.common import (
    CommandError,
    REPO_ROOT,
    default_github_repo,
    git_changed_files,
    git_current_branch,
    git_fetch_branch,
    load_json,
    require_cli,
    run,
    syvert_state_file,
)
from scripts.integration_contract import (
    ISSUE_SCOPE_FIELDS,
    extract_issue_canonical_integration_fields,
    field_choices,
    validate_issue_fetch,
    validate_open_pr_payload,
)
from scripts.policy.policy import classify_paths, formal_spec_dirs, get_policy, risk_level
from scripts.pr_scope_guard import build_report
from scripts.spec_guard import validate_suite


TEMPLATE_PATH = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
WORKTREE_STATE_FILE = syvert_state_file("worktrees.json")
ISSUE_SUMMARY_HEADING_ALIASES: dict[str, tuple[str, ...]] = {
    "Goal": ("Goal", "Summary", "摘要", "治理目标", "执行目标", "阶段目标"),
    "Scope": ("Scope", "范围", "影响载体"),
    "Required Outcomes": ("Required Outcomes", "Formal Spec Suite", "Formal Spec 套件"),
    "Acceptance": ("Acceptance", "验收"),
    "Acceptance Criteria": ("Acceptance Criteria", "验收标准", "进入 / 关闭条件", "进入/关闭条件"),
    "Out of Scope": ("Out of Scope", "非目标"),
    "Dependency": ("Dependency", "Dependencies", "依赖", "关联 FR"),
}
ISSUE_SUMMARY_HEADINGS = tuple(ISSUE_SUMMARY_HEADING_ALIASES.keys())
FORMAL_SPEC_CORE_FILES = {"spec.md", "plan.md"}
INTEGRATION_TOUCHPOINT_CHOICES = field_choices("integration_touchpoint")
EXTERNAL_DEPENDENCY_CHOICES = field_choices("external_dependency")
MERGE_GATE_CHOICES = field_choices("merge_gate")
CONTRACT_SURFACE_CHOICES = field_choices("contract_surface")
YES_NO_CHOICES = field_choices("shared_contract_changed")


def is_deleted_legacy_todo_change(path: str, *, repo_root: Path) -> bool:
    normalized = Path(path)
    parts = normalized.parts
    if len(parts) != 4:
        return False
    if parts[0] != "docs" or parts[1] != "specs" or not parts[2].startswith("FR-") or parts[3] != "TODO.md":
        return False
    return not (repo_root / normalized).exists()


def has_formal_spec_core_file_changes(changed_files: list[str], *, repo_root: Path | None = None) -> bool:
    for path in changed_files:
        normalized = Path(path)
        parts = normalized.parts
        if len(parts) == 4 and parts[0] == "docs" and parts[1] == "specs" and parts[2].startswith("FR-") and parts[3] in FORMAL_SPEC_CORE_FILES:
            return True
    if repo_root is None:
        return False
    return bool(changed_files) and all(is_deleted_legacy_todo_change(path, repo_root=repo_root) for path in changed_files)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="创建受控 PR。")
    parser.add_argument("--class", dest="pr_class", required=True, choices=get_policy()["pr_classes"])
    parser.add_argument("--issue", type=int)
    parser.add_argument("--item-key")
    parser.add_argument("--item-type")
    parser.add_argument("--release")
    parser.add_argument("--sprint")
    parser.add_argument("--title")
    parser.add_argument("--base", default="main")
    parser.add_argument("--closing", default="fixes", choices=get_policy()["closing_modes"])
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--integration-touchpoint", default="none", choices=INTEGRATION_TOUCHPOINT_CHOICES)
    parser.add_argument("--shared-contract-changed", default="no", choices=YES_NO_CHOICES)
    parser.add_argument("--integration-ref", default="none")
    parser.add_argument("--external-dependency", default="none", choices=EXTERNAL_DEPENDENCY_CHOICES)
    parser.add_argument("--merge-gate", default="local_only", choices=MERGE_GATE_CHOICES)
    parser.add_argument("--contract-surface", default="none", choices=CONTRACT_SURFACE_CHOICES)
    parser.add_argument("--joint-acceptance-needed", default="no", choices=YES_NO_CHOICES)
    parser.add_argument("--integration-status-checked-before-pr", default="no", choices=YES_NO_CHOICES)
    parser.add_argument("--integration-status-checked-before-merge", default="no", choices=YES_NO_CHOICES)
    return parser.parse_args(argv)


def ensure_not_main(branch: str) -> None:
    if branch == "main":
        raise SystemExit("当前分支是 main，请切到独立分支后再创建 PR。")


def latest_commit_subject() -> str:
    return run(["git", "log", "-1", "--pretty=%s"], cwd=REPO_ROOT).stdout.strip()


def has_bound_formal_spec_input(
    repo_root: Path,
    item_key: str | None,
    item_type: str | None,
    changed_files: list[str],
    *,
    allow_unbound_local_fallback: bool,
    allow_legacy_metadata_free_decision_compat: bool = False,
) -> bool:
    if not item_key:
        return False

    exec_plan = load_item_context_from_exec_plan(repo_root, item_key)
    input_mode = classify_exec_plan_input_mode(exec_plan)
    if input_mode == INPUT_MODE_FORMAL_SPEC:
        if validate_bound_spec_contract(repo_root, exec_plan):
            return False
        related_spec = str(exec_plan.get("关联 spec", "")).strip()
        spec_dir = normalize_bound_spec_dir(repo_root, related_spec)
        if spec_dir is None:
            return False
        additional_spec_errors, additional_spec_dirs = validate_additional_spec_contracts(repo_root, exec_plan)
        if additional_spec_errors:
            return False
        if validate_bound_formal_spec_scope(repo_root, exec_plan, changed_files):
            return False
        if exec_plan.get("关联 decision", ""):
            decision_errors = validate_bound_decision_contract(repo_root, exec_plan, require_present=True)
            if decision_errors and not (
                allow_legacy_metadata_free_decision_compat
                and allows_legacy_metadata_free_formal_spec_decision(exec_plan, decision_errors)
            ):
                return False
        if validate_suite(spec_dir):
            return False
        for extra_spec_dir in additional_spec_dirs:
            if extra_spec_dir == spec_dir.relative_to(repo_root.resolve()):
                continue
            if validate_suite(repo_root / extra_spec_dir):
                return False
        return True

    if allow_unbound_local_fallback and input_mode == INPUT_MODE_UNBOUND and item_type == "FR":
        expected_dir = repo_root / "docs" / "specs" / item_key
        touched_spec_dirs = formal_spec_dirs(changed_files)
        if expected_dir.exists() and spec_dir_has_minimum_suite(expected_dir) and not validate_suite(expected_dir):
            expected_rel = expected_dir.relative_to(repo_root)
            if touched_spec_dirs:
                if expected_rel not in touched_spec_dirs:
                    return False
                if any(path != expected_rel for path in touched_spec_dirs):
                    return False
            return True

    return False


def has_bound_bootstrap_contract(repo_root: Path, item_key: str | None) -> bool:
    if not item_key:
        return False
    exec_plan = load_item_context_from_exec_plan(repo_root, item_key)
    if classify_exec_plan_input_mode(exec_plan) != INPUT_MODE_BOOTSTRAP:
        return False
    return not validate_bound_decision_contract(repo_root, exec_plan, require_present=True)


def item_requires_formal_input(repo_root: Path, item_key: str | None, item_type: str | None) -> bool:
    if not item_key or not item_type:
        return False
    exec_plan = load_item_context_from_exec_plan(repo_root, item_key)
    input_mode = classify_exec_plan_input_mode(exec_plan)
    if input_mode in {INPUT_MODE_FORMAL_SPEC, INPUT_MODE_BOOTSTRAP}:
        return True
    return item_type in {"FR", "HOTFIX", "CHORE"}


def closing_line(issue: int | None, mode: str) -> str:
    if not issue or mode == "none":
        return "无"
    prefix = "Fixes" if mode == "fixes" else "Refs"
    return f"{prefix} #{issue}"


def normalize_issue_summary_heading(raw_heading: str) -> str:
    heading = raw_heading.strip()
    heading = re.sub(r"\s*[:：]\s*$", "", heading)
    heading = re.sub(r"\s*/\s*", " / ", heading)
    heading = re.sub(r"\s+", " ", heading)
    return heading.casefold()


ISSUE_SUMMARY_HEADING_LOOKUP = {
    normalize_issue_summary_heading(alias): canonical
    for canonical, aliases in ISSUE_SUMMARY_HEADING_ALIASES.items()
    for alias in aliases
}
def extract_issue_form_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    heading_pattern = re.compile(r"^#{2,6}\s+(.+?)\s*$")

    for line in body.splitlines():
        stripped = line.strip()
        heading_match = heading_pattern.match(stripped)
        if heading_match:
            current = heading_match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line.rstrip())

    return {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}


def extract_issue_summary_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    for heading, content in extract_issue_form_sections(body).items():
        canonical = ISSUE_SUMMARY_HEADING_LOOKUP.get(normalize_issue_summary_heading(heading))
        if canonical and content:
            if canonical in sections:
                sections[canonical] = "\n\n".join([sections[canonical], content]).strip()
            else:
                sections[canonical] = content
    return sections

def fetch_issue_body(issue: int | None) -> str:
    if issue is None:
        return ""

    require_cli("gh")
    completed = run(
        ["gh", "issue", "view", str(issue), "--repo", default_github_repo(), "--json", "body"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return ""

    payload = json.loads(completed.stdout or "{}")
    return str(payload.get("body") or "")


def resolve_issue_canonical_integration(issue: int | None) -> tuple[dict[str, str], str | None]:
    if issue is None:
        return {}, None
    resolution = validate_issue_fetch(issue, allow_missing_payload=True)
    return resolution.canonical, resolution.error


def build_issue_summary(issue: int | None) -> str:
    body = fetch_issue_body(issue)
    if not body:
        return ""

    sections = extract_issue_summary_sections(body)
    if not sections:
        return ""

    lines: list[str] = []
    for heading in ISSUE_SUMMARY_HEADINGS:
        content = sections.get(heading)
        if not content:
            continue
        lines.extend([f"## {heading}", "", content, ""])
    return "\n".join(lines).strip()


def load_worktree_binding_for_branch(branch: str, path: Path = WORKTREE_STATE_FILE) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        state = load_json(path)
    except Exception:
        return {"conflict": "invalid_worktree_state", "branch": branch}
    matches: list[dict[str, object]] = []
    for item in (state.get("worktrees") or {}).values():
        if item.get("branch") == branch:
            matches.append(item)
    if len(matches) > 1:
        return {"conflict": "multiple_branch_bindings", "branch": branch}
    if len(matches) == 1:
        return matches[0]
    return {}


def validate_current_worktree_binding(issue: int | None, *, repo_root: Path) -> list[str]:
    if issue is None:
        return []
    if repo_root.resolve() != REPO_ROOT.resolve():
        return []
    try:
        branch = git_current_branch(repo=repo_root)
    except CommandError:
        return ["无法识别当前分支，无法确认事项上下文与执行现场一致。"]
    binding = load_worktree_binding_for_branch(branch)
    if binding.get("conflict") == "invalid_worktree_state":
        return ["`worktrees.json` 已损坏或不是合法 JSON，无法确认事项上下文与执行现场一致。"]
    if binding.get("conflict") == "multiple_branch_bindings":
        return ["当前分支在 `worktrees.json` 中命中多个 worktree 绑定，无法确认唯一执行现场。"]
    if not binding:
        return ["当前分支未找到匹配的 worktree 状态绑定，无法确认事项上下文与执行现场一致。"]
    try:
        binding_issue = int(str(binding.get("issue", -1)).lstrip("#"))
    except (TypeError, ValueError):
        return ["当前 worktree 绑定中的 `issue` 值非法，无法确认事项上下文与执行现场一致。"]
    if binding_issue != issue:
        return ["受控 PR 入口填写的 `Issue` 与当前 branch/worktree 绑定的事项不一致。"]
    recorded_path = str(binding.get("path", "")).strip()
    if recorded_path and Path(recorded_path).resolve() != repo_root.resolve():
        return ["当前仓库路径与 `worktrees.json` 中登记的 worktree `path` 不一致。"]
    return []


def validate_item_context(
    issue: int | None,
    item_key: str | None,
    item_type: str | None,
    release: str | None,
    sprint: str | None,
    *,
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    missing = [
        name
        for name, value in (
            ("Issue", issue),
            ("item_key", item_key),
            ("item_type", item_type),
            ("release", release),
            ("sprint", sprint),
        )
        if value in {None, ""}
    ]
    if missing:
        errors.append(f"受控 PR 入口缺少完整事项上下文：{', '.join(missing)}。")
        return errors

    assert issue is not None
    assert item_key is not None
    assert item_type is not None
    assert release is not None
    assert sprint is not None

    if item_type not in ITEM_TYPES:
        errors.append("`item_type` 必须为 `FR` / `HOTFIX` / `GOV` / `CHORE`。")
    if not valid_item_key(item_key, item_type):
        errors.append("`item_key` 必须匹配 `<item_type>-<4-digit>-<slug>`，且前缀与 `item_type` 一致。")

    exec_plan = load_item_context_from_exec_plan(repo_root, item_key)
    if exec_plan.get("conflict") == "duplicate_metadata_keys":
        errors.append("active `exec-plan` 在元数据区存在重复键，无法确认唯一事项上下文。")
        return errors
    if exec_plan.get("conflict") == "multiple_active_exec_plans":
        errors.append("当前 `item_key` 对应多个 active `exec-plan`，不满足“有且仅有一个 active exec-plan”的要求。")
        return errors
    if not exec_plan:
        errors.append(f"当前事项缺少 active `exec-plan`：`docs/exec-plans/{item_key}.md`。")
        return errors

    issue_active_exec_plans = active_exec_plans_for_issue(repo_root, issue)
    if not issue_active_exec_plans:
        errors.append("当前 `Issue` 缺少 active `exec-plan`，无法确认当前执行回合。")
        return errors
    if len(issue_active_exec_plans) > 1:
        errors.append("当前 `Issue` 存在多个 active `exec-plan`，不满足“每个执行回合有且仅有一个 active exec-plan”的要求。")
        return errors
    if issue_active_exec_plans[0].get("item_key", "") != item_key:
        errors.append("当前 `Issue` 的唯一 active `exec-plan` 与受控入口填写的 `item_key` 不一致。")
        return errors

    expected = {
        "item_key": item_key,
        "Issue": normalize_issue(issue),
        "item_type": item_type,
        "release": release,
        "sprint": sprint,
    }
    for field, expected_value in expected.items():
        actual = exec_plan.get(field, "")
        if actual != str(expected_value):
            label = "Issue" if field == "Issue" else field
            errors.append(f"active `exec-plan` 的 `{label}` 与受控入口填写值不一致。")
    active_item = exec_plan.get("active 收口事项")
    if active_item and active_item != item_key:
        errors.append("active `exec-plan` 的 `active 收口事项` 必须与当前 `item_key` 一致。")
    return errors


def validate_pr_preflight(
    pr_class: str,
    issue: int | None,
    item_key: str | None,
    item_type: str | None,
    release: str | None,
    sprint: str | None,
    changed_files: list[str],
    *,
    repo_root: Path,
    validate_worktree_binding_check: bool = True,
) -> list[str]:
    errors: list[str] = []

    errors.extend(validate_item_context(issue, item_key, item_type, release, sprint, repo_root=repo_root))
    if validate_worktree_binding_check:
        errors.extend(validate_current_worktree_binding(issue, repo_root=repo_root))

    for raw_path in changed_files:
        path = Path(raw_path)
        target = repo_root / path
        if is_legacy_todo_file(path) and target.exists():
            errors.append(f"{target}: legacy `TODO.md` 已退出正式治理流，请删除该文件。")
        if issue is not None and is_exec_plan_file(path) and target.exists():
            errors.extend(
                f"{target}: {error}"
                for error in validate_legacy_todo_cleanup_foreign_exec_plan_touch(
                    repo_root,
                    target,
                    current_issue=issue,
                    changed_paths=changed_files,
                )
            )

    if pr_class == "spec" and not has_formal_spec_core_file_changes(changed_files, repo_root=repo_root):
        errors.append("`spec` 类 PR 必须包含 formal spec 套件核心文件变更。")

    if pr_class == "spec" and not has_bound_formal_spec_input(
        repo_root,
        item_key,
        item_type,
        changed_files,
        allow_unbound_local_fallback=False,
    ):
        errors.append("`spec` 类 PR 缺少绑定 formal spec 输入。")

    if pr_class == "governance" and not (
        has_bound_formal_spec_input(
            repo_root,
            item_key,
            item_type,
            changed_files,
            allow_unbound_local_fallback=False,
        )
        or has_bound_bootstrap_contract(repo_root, item_key)
    ):
        errors.append("核心事项缺少 formal spec 或 bootstrap contract。")
        errors.append("`governance` 类 PR 缺少 `exec-plan` 或 formal spec 套件。")

    if pr_class == "implementation" and item_requires_formal_input(repo_root, item_key, item_type):
        if not (
            has_bound_formal_spec_input(
                repo_root,
                item_key,
                item_type,
                changed_files,
                allow_unbound_local_fallback=True,
                allow_legacy_metadata_free_decision_compat=True,
            )
            or has_bound_bootstrap_contract(repo_root, item_key)
        ):
            errors.append("绑定 Issue 的实现事项缺少 formal spec 或 bootstrap contract。")

    return errors


def validate_integration_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    issue_canonical_integration, issue_canonical_error = resolve_issue_canonical_integration(args.issue)
    if issue_canonical_error:
        errors.append(issue_canonical_error)
    payload = {
        field: str(getattr(args, field, "") or "").strip()
        for field in (
            *ISSUE_SCOPE_FIELDS,
            "integration_status_checked_before_pr",
            "integration_status_checked_before_merge",
        )
    }
    payload["integration_ref"] = str(args.integration_ref or "").strip()
    open_pr_errors = validate_open_pr_payload(
        payload,
        issue_canonical=issue_canonical_integration,
        issue_number=args.issue,
    )
    for error in open_pr_errors:
        if error.startswith("`cli."):
            field = error.split(".", 1)[1].split("`", 1)[0]
            cli_flag = f"--{field.replace('_', '-')}"
            errors.append(error.replace(f"`cli.{field}`", f"`{cli_flag}`", 1))
        else:
            errors.append(error)
    return errors


def replace_markdown_field(body: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^- {re.escape(label)}(?:（[^\n]*?）)?:\s*$", re.MULTILINE)
    replacement = f"- {label}: {value}"
    return pattern.sub(replacement, body, count=1)


def has_markdown_section(body: str, heading: str) -> bool:
    pattern = re.compile(rf"(?im)^##\s+{re.escape(heading)}\s*$")
    return bool(pattern.search(body))


def render_integration_check_section(values: dict[str, str]) -> str:
    lines = ["## integration_check", ""]
    lines.extend([f"- {label}: {value}" for label, value in values.items()])
    return "\n".join(lines)


def build_body(args: argparse.Namespace, changed_files: list[str]) -> str:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"缺少 PR 模板: {TEMPLATE_PATH}")
    body = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "{{PR_CLASS}}": args.pr_class,
        "{{ISSUE_SUMMARY}}": build_issue_summary(args.issue),
        "{{ISSUE}}": f"#{args.issue}" if args.issue else "无",
        "{{ITEM_KEY}}": args.item_key or "未填写",
        "{{ITEM_TYPE}}": args.item_type or "未填写",
        "{{RELEASE}}": args.release or "未填写",
        "{{SPRINT}}": args.sprint or "未填写",
        "{{CLOSING}}": closing_line(args.issue, args.closing),
        "{{RISK_LEVEL}}": risk_level(args.pr_class),
        "{{VALIDATION_SUGGESTION}}": "- 已执行：\n- 未执行：",
        "{{ROLLBACK}}": "如需回滚，使用独立 revert PR 撤销本次变更。",
    }
    for token, value in replacements.items():
        body = body.replace(token, value)
    integration_values = {
        "integration_touchpoint": args.integration_touchpoint,
        "shared_contract_changed": args.shared_contract_changed,
        "integration_ref": args.integration_ref,
        "external_dependency": args.external_dependency,
        "merge_gate": args.merge_gate,
        "contract_surface": args.contract_surface,
        "joint_acceptance_needed": args.joint_acceptance_needed,
        "integration_status_checked_before_pr": args.integration_status_checked_before_pr,
        "integration_status_checked_before_merge": args.integration_status_checked_before_merge,
    }
    if not has_markdown_section(body, "integration_check"):
        body = body.rstrip() + "\n\n" + render_integration_check_section(integration_values) + "\n"
    for label, value in integration_values.items():
        body = replace_markdown_field(body, label, value)
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
    preflight_errors = validate_pr_preflight(
        args.pr_class,
        args.issue,
        args.item_key,
        args.item_type,
        args.release,
        args.sprint,
        changed_files,
        repo_root=REPO_ROOT,
    )
    if preflight_errors:
        for error in preflight_errors:
            print(error, file=sys.stderr)
        return 1
    integration_errors = validate_integration_args(args)
    if integration_errors:
        for error in integration_errors:
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
