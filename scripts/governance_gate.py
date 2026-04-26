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
    Path(".loom/bin/fact_chain_support.py"),
    Path(".loom/bin/governance_surface.py"),
    Path(".loom/bin/loom_flow.py"),
    Path(".loom/bin/loom_status.py"),
    Path(".loom/bin/loom_check.py"),
    Path(".loom/bin/runtime_paths.py"),
    Path(".loom/bin/runtime_state.py"),
    Path(".loom/companion/manifest.json"),
    Path(".loom/companion/repo-interface.json"),
    Path(".loom/companion/interop.json"),
    Path(".loom/status/current.md"),
    Path(".loom/shadow/shadow-parity.json"),
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


def markdown_fields(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def validate_review_payload(path: Path, *, expected_kind: str, item_id: str) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Loom review artifact 无法读取: {path}: {exc}"]
    for field in ("schema_version", "item_id", "decision", "kind", "summary", "reviewer", "reviewed_head", "reviewed_validation_summary"):
        if not str(payload.get(field, "")).strip():
            errors.append(f"Loom review artifact `{path}` 缺少 `{field}`")
    if payload.get("item_id") != item_id:
        errors.append(f"Loom review artifact `{path}` item_id 必须是 {item_id}")
    if payload.get("kind") != expected_kind:
        errors.append(f"Loom review artifact `{path}` kind 必须是 {expected_kind}")
    if payload.get("decision") not in {"allow", "block", "fallback"}:
        errors.append(f"Loom review artifact `{path}` decision 非法")
    return errors


def validate_loom_carrier_semantics(repo_root: Path) -> list[str]:
    errors: list[str] = []
    status_path = repo_root / ".loom/status/current.md"
    shadow_path = repo_root / ".loom/shadow/shadow-parity.json"

    if not status_path.exists():
        return errors
    status = markdown_fields(status_path)
    item_id = status.get("Item ID") or "INIT-0001"
    work_item_path = repo_root / f".loom/work-items/{item_id}.md"
    progress_path = repo_root / f".loom/progress/{item_id}.md"
    review_path = repo_root / f".loom/reviews/{item_id}.json"
    spec_review_path = repo_root / f".loom/reviews/{item_id}.spec.json"
    spec_dir = repo_root / f".loom/specs/{item_id}"
    for path in (
        work_item_path,
        progress_path,
        review_path,
        spec_review_path,
        spec_dir / "spec.md",
        spec_dir / "plan.md",
        spec_dir / "implementation-contract.md",
        shadow_path,
    ):
        if not path.exists():
            errors.append(f"缺少当前 Loom item carrier: {path}")
    if errors:
        return errors

    work_item = markdown_fields(work_item_path)
    progress = markdown_fields(progress_path)
    for field in ("Item ID", "Goal", "Scope", "Execution Path", "Workspace Entry", "Recovery Entry", "Review Entry", "Validation Entry", "Closing Condition"):
        if not work_item.get(field):
            errors.append(f"Loom work item 缺少 `{field}`")
    for field in (
        "Item ID",
        "Goal",
        "Scope",
        "Execution Path",
        "Workspace Entry",
        "Recovery Entry",
        "Review Entry",
        "Validation Entry",
        "Closing Condition",
        "Current Checkpoint",
        "Latest Validation Summary",
    ):
        if not status.get(field):
            errors.append(f"Loom status 缺少 `{field}`")
        elif work_item.get(field) and work_item[field] != status[field]:
            errors.append(f"Loom status 与 work item 的 `{field}` 不一致")
    for field in ("Item ID", "Current Checkpoint", "Latest Validation Summary"):
        if not progress.get(field):
            errors.append(f"Loom progress 缺少 `{field}`")
        elif status.get(field) and progress[field] != status[field]:
            errors.append(f"Loom progress 与 status 的 `{field}` 不一致")

    errors.extend(validate_review_payload(review_path, expected_kind="general_review", item_id=item_id))
    errors.extend(validate_review_payload(spec_review_path, expected_kind="spec_review", item_id=item_id))
    try:
        review_payload = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        review_payload = {}
    if review_payload.get("reviewed_validation_summary") != progress.get("Latest Validation Summary"):
        errors.append("Loom review 的 reviewed_validation_summary 必须匹配 progress/status 最新验证摘要")
    try:
        spec_review_payload = json.loads(spec_review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        spec_review_payload = {}
    if spec_review_payload.get("reviewed_validation_summary") != progress.get("Latest Validation Summary"):
        errors.append("Loom spec review 的 reviewed_validation_summary 必须匹配 progress/status 最新验证摘要")

    try:
        shadow_payload = json.loads(shadow_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        shadow_payload = {}
    if shadow_payload.get("result") != "pass":
        errors.append("Loom shadow parity artifact result 必须为 pass")
    if not isinstance(shadow_payload.get("surfaces"), list) or not shadow_payload.get("surfaces"):
        errors.append("Loom shadow parity artifact 必须列出 surfaces")

    return errors


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

    errors.extend(validate_loom_carrier_semantics(repo_root))
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
