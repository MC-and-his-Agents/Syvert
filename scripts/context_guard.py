#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import re

from scripts.common import REPO_ROOT, git_changed_files, git_current_branch
from scripts.item_context import (
    INPUT_MODE_BOOTSTRAP,
    INPUT_MODE_FORMAL_SPEC,
    INPUT_MODE_UNBOUND,
    active_exec_plans_for_issue,
    classify_exec_plan_input_mode,
    is_eligible_active_exec_plan,
    is_inactive_exec_plan,
    normalize_bound_spec_dir,
    parse_exec_plan_metadata,
    validate_bound_decision_contract,
    validate_bound_formal_spec_scope,
    validate_bound_spec_contract,
)
from scripts.policy.policy import formal_spec_dirs, spec_suite_policy
from scripts.spec_guard import validate_suite


ALLOWED_ITEM_TYPES = {"FR", "HOTFIX", "GOV", "CHORE"}
ITEM_KEY_RE = re.compile(r"^(FR|HOTFIX|GOV|CHORE)-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_RE = re.compile(r"^- ([^：:\n]+)[：:][ \t]*(.*)$", re.MULTILINE)
HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
CODE_RE = re.compile(r"`([^`]+)`")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SHA40_RE = re.compile(r"\b[0-9a-f]{40}\b")
ISSUE_REF_RE = re.compile(r"^issue-(\d+)(?:-|$)")

SPEC_CONTEXT_FIELDS = ("Issue", "item_key", "item_type", "release", "sprint")
EXEC_CONTEXT_FIELDS = ("Issue", "item_key", "item_type", "release", "sprint")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验治理事项上下文字段与索引语义。")
    parser.add_argument("--mode", choices=("ci", "local"), default="local")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--base-ref")
    parser.add_argument("--base-sha")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--head-sha")
    parser.add_argument("--current-issue", type=int)
    return parser.parse_args(argv)


def normalize_value(raw_value: str) -> str:
    raw_value = raw_value.strip()
    if not raw_value:
        return ""
    code_match = CODE_RE.search(raw_value)
    if code_match:
        return code_match.group(1).strip()
    value = raw_value.strip("`").strip()
    return value


def extract_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in FIELD_RE.finditer(text):
        key = match.group(1).strip()
        value = normalize_value(match.group(2))
        if key not in fields:
            fields[key] = value
    return fields


def heading_exists(text: str, heading: str) -> bool:
    headings = {item.group(1).strip() for item in HEADING_RE.finditer(text)}
    return heading in headings


def is_template(path: Path) -> bool:
    return path.name == "_template.md" or "_template" in path.parts


def _matches(path: Path, pattern: str) -> bool:
    return re.search(pattern, path.as_posix()) is not None


def is_exec_plan_file(path: Path) -> bool:
    return _matches(path, r"(^|/)docs/exec-plans/[^/]+\.md$") and path.name != "README.md"


def is_release_file(path: Path) -> bool:
    return _matches(path, r"(^|/)docs/releases/[^/]+\.md$") and path.name != "README.md"


def is_sprint_file(path: Path) -> bool:
    return _matches(path, r"(^|/)docs/sprints/[^/]+\.md$") and path.name != "README.md"


def is_decision_file(path: Path) -> bool:
    return _matches(path, r"(^|/)docs/decisions/[^/]+\.md$") and path.name != "README.md"


def decision_item_type_from_name(path: Path) -> str | None:
    stem = path.stem
    typed = re.match(r"^ADR-(FR|HOTFIX|GOV|CHORE)-\d{4}(?:-|$)", stem)
    if typed:
        return typed.group(1)
    legacy = re.match(r"^ADR-\d{4}(?:-|$)", stem)
    if legacy:
        return None
    return None


def is_spec_suite_file(path: Path) -> bool:
    value = path.as_posix()
    if re.search(r"(^|/)docs/specs/_template/(spec|plan|TODO)\.md$", value):
        return True
    return re.search(r"(^|/)docs/specs/FR-[^/]+/(spec|plan|TODO)\.md$", value) is not None


def is_todo_spec_file(path: Path) -> bool:
    value = path.as_posix()
    if re.search(r"(^|/)docs/specs/_template/TODO\.md$", value):
        return True
    return re.search(r"(^|/)docs/specs/FR-[^/]+/TODO\.md$", value) is not None


def should_skip_reference(value: str) -> bool:
    if not value:
        return True
    if value.startswith(("http://", "https://", "mailto:")):
        return True
    placeholders = ("<", ">", "XXXX", "YYYY", "vX.Y.Z", "ITEM-KEY", "*")
    return any(token in value for token in placeholders)


def validate_item_key(path: Path, item_key: str, item_type: str, *, allow_empty: bool) -> list[str]:
    errors: list[str] = []
    if allow_empty and not item_key:
        return errors
    if not item_key:
        return [f"{path}: `item_key` 不能为空。"]
    if not ITEM_KEY_RE.match(item_key):
        errors.append(f"{path}: `item_key` 格式非法，需为 `<item_type>-<4-digit>-<slug>`。")
        return errors
    prefix = item_key.split("-", 1)[0]
    if item_type and prefix != item_type:
        errors.append(f"{path}: `item_key` 前缀 `{prefix}` 与 `item_type` `{item_type}` 不一致。")
    return errors


def validate_context_fields(path: Path, fields: dict[str, str], required: tuple[str, ...], *, allow_empty: bool) -> list[str]:
    errors: list[str] = []
    for key in required:
        if key not in fields:
            errors.append(f"{path}: 缺少 `{key}` 字段。")
            continue
        if not allow_empty and not fields[key]:
            errors.append(f"{path}: `{key}` 不能为空。")
    if "item_type" in fields and fields.get("item_type") and fields["item_type"] not in ALLOWED_ITEM_TYPES:
        errors.append(f"{path}: `item_type` 非法，必须是 {sorted(ALLOWED_ITEM_TYPES)} 之一。")
    if "item_key" in fields:
        errors.extend(
            validate_item_key(path, fields.get("item_key", ""), fields.get("item_type", ""), allow_empty=allow_empty)
        )
    return errors


def validate_exec_plan(path: Path, *, repo_root: Path) -> list[str]:
    if not path.exists():
        return [f"{path}: exec-plan 文件不存在（可能已删除）。"]
    text = path.read_text(encoding="utf-8")
    fields = parse_exec_plan_metadata(path)
    template_mode = is_template(path)
    if fields.get("conflict") == "duplicate_metadata_keys":
        duplicate_key = fields.get("duplicate_key", "unknown")
        return [f"{path}: exec-plan 元数据区存在重复键 `{duplicate_key}`。"]
    errors = validate_context_fields(path, fields, EXEC_CONTEXT_FIELDS, allow_empty=template_mode)

    checkpoint_heading = "最近一次 checkpoint 对应的 head SHA"
    if not heading_exists(text, checkpoint_heading):
        errors.append(f"{path}: 缺少 `{checkpoint_heading}` 段落。")
    else:
        if not template_mode and not SHA40_RE.search(text):
            errors.append(f"{path}: 缺少可解析的 40 位 checkpoint head SHA。")
    if not template_mode:
        input_mode = classify_exec_plan_input_mode(fields)
        if input_mode == INPUT_MODE_FORMAL_SPEC:
            bound_spec_errors = validate_bound_spec_contract(repo_root, fields)
            errors.extend(f"{path}: {error}" for error in bound_spec_errors)
            if not bound_spec_errors:
                spec_dir = normalize_bound_spec_dir(repo_root, str(fields.get("关联 spec", "")).strip())
                if spec_dir is not None:
                    errors.extend(
                        f"{path}: 绑定 `关联 spec` 的 formal spec 套件不可审查：{error}"
                        for error in validate_suite(spec_dir)
                    )
            if fields.get("关联 decision", ""):
                errors.extend(
                    f"{path}: {error}"
                    for error in validate_bound_decision_contract(repo_root, fields, require_present=False)
                )
        elif input_mode == INPUT_MODE_BOOTSTRAP:
            errors.extend(
                f"{path}: {error}"
                for error in validate_bound_decision_contract(repo_root, fields, require_present=True)
            )
        elif fields.get("关联 decision", ""):
            errors.extend(
                f"{path}: {error}"
                for error in validate_bound_decision_contract(repo_root, fields, require_present=False)
            )
    return errors


def validate_spec_context_file(path: Path) -> list[str]:
    if not path.exists():
        return [f"{path}: formal spec 文件不存在（可能已删除）。"]
    text = path.read_text(encoding="utf-8")
    fields = extract_fields(text)
    template_mode = is_template(path)
    return validate_context_fields(path, fields, SPEC_CONTEXT_FIELDS, allow_empty=template_mode)


def extract_doc_paths(text: str) -> list[str]:
    refs: list[str] = []
    refs.extend(match.group(1).strip() for match in MARKDOWN_LINK_RE.finditer(text))
    refs.extend(match.group(1).strip() for match in CODE_RE.finditer(text) if "docs/" in match.group(1))
    return refs


def validate_release_or_sprint(path: Path, repo_root: Path) -> list[str]:
    if not path.exists():
        return [f"{path}: release/sprint 索引文件不存在（可能已删除）。"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if is_release_file(path):
        required_headings = ("目标", "明确不在范围", "目标判据", "纳入事项", "关联工件")
    else:
        required_headings = ("本轮目标", "入口事项", "目标判据", "协作入口", "关联工件")
        if not (heading_exists(text, "release") or heading_exists(text, "所属 release")):
            errors.append(f"{path}: 缺少 `release` 段落。")

    for heading in required_headings:
        if not heading_exists(text, heading):
            errors.append(f"{path}: 缺少 `{heading}` 段落。")

    for ref in extract_doc_paths(text):
        if should_skip_reference(ref):
            continue
        normalized = ref.split("#", 1)[0].rstrip("/")
        if not normalized.startswith("docs/"):
            continue
        target = (repo_root / normalized).resolve()
        try:
            target.relative_to(repo_root.resolve())
        except ValueError:
            errors.append(f"{path}: 引用了仓库外路径 `{ref}`。")
            continue
        if not target.exists():
            errors.append(f"{path}: 引用了不存在的路径 `{ref}`。")
    return errors


def validate_decision(path: Path) -> list[str]:
    if not path.exists():
        return [f"{path}: decision 文档不存在（可能已删除）。"]
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return [f"{path}: decision 文档不能为空。"]
    return []


def is_valid_governance_exec_plan_binding(exec_plan_path: Path, fields: dict[str, str]) -> bool:
    if not is_eligible_active_exec_plan(fields):
        return False
    if fields.get("item_type") != "GOV":
        return False
    issue = fields.get("Issue", "").strip()
    item_key = fields.get("item_key", "").strip()
    if not issue or not item_key:
        return False
    if exec_plan_path.name != f"{item_key}.md":
        return False
    return not validate_item_key(exec_plan_path, item_key, "GOV", allow_empty=False)


def infer_current_issue(*refs: str | None) -> int | None:
    for ref in refs:
        normalized = str(ref or "").strip()
        if not normalized:
            continue
        match = ISSUE_REF_RE.match(normalized)
        if match:
            return int(match.group(1))
    return None


def eligible_governance_exec_plans(
    repo_root: Path,
    *,
    current_issue: int | None,
) -> list[tuple[Path, dict[str, str]]]:
    if current_issue is not None:
        payloads = active_exec_plans_for_issue(repo_root, current_issue)
    else:
        payloads = []
        for exec_plan in (repo_root / "docs" / "exec-plans").glob("*.md"):
            if exec_plan.name in {"README.md", "_template.md"}:
                continue
            payloads.append(parse_exec_plan_metadata(exec_plan))

    matches: list[tuple[Path, dict[str, str]]] = []
    for fields in payloads:
        exec_plan_path = Path(str(fields.get("exec_plan", "")).strip())
        if not exec_plan_path.exists():
            continue
        if is_valid_governance_exec_plan_binding(exec_plan_path, fields):
            matches.append((exec_plan_path, fields))
    return matches


def authorized_formal_spec_dirs(repo_root: Path, *, current_issue: int | None) -> set[Path]:
    authorized: set[Path] = set()
    payloads: list[dict[str, str]] = []
    if current_issue is not None:
        payloads.extend(active_exec_plans_for_issue(repo_root, current_issue))
    else:
        for exec_plan in (repo_root / "docs" / "exec-plans").glob("*.md"):
            if exec_plan.name in {"README.md", "_template.md"}:
                continue
            fields = parse_exec_plan_metadata(exec_plan)
            if is_eligible_active_exec_plan(fields):
                payloads.append(fields)
    for fields in payloads:
        item_key = fields.get("item_key", "").strip()
        item_type = fields.get("item_type", "").strip()
        input_mode = classify_exec_plan_input_mode(fields)
        if input_mode == INPUT_MODE_FORMAL_SPEC:
            if validate_bound_spec_contract(repo_root, fields):
                continue
            spec_dir = normalize_bound_spec_dir(repo_root, str(fields.get("关联 spec", "")).strip())
            if spec_dir is None:
                continue
            authorized.add(spec_dir.relative_to(repo_root.resolve()))
            continue
        if input_mode == INPUT_MODE_UNBOUND and item_type == "FR" and item_key:
            expected_dir = repo_root / "docs" / "specs" / item_key
            if expected_dir.exists():
                authorized.add(expected_dir.relative_to(repo_root))
    return authorized


def collect_targets(
    repo_root: Path,
    changed_paths: list[str] | None,
) -> tuple[list[Path], list[Path], list[Path], list[Path], list[Path]]:
    exec_plans: set[Path] = set()
    spec_files: set[Path] = set()
    release_files: set[Path] = set()
    sprint_files: set[Path] = set()
    decision_files: set[Path] = set()

    if changed_paths is not None:
        for raw_path in changed_paths:
            path = Path(raw_path)
            target = repo_root / path
            if is_exec_plan_file(path) and target.exists():
                exec_plans.add(repo_root / path)
            if is_release_file(path) and target.exists():
                release_files.add(repo_root / path)
            if is_sprint_file(path) and target.exists():
                sprint_files.add(repo_root / path)
            if is_decision_file(path) and target.exists():
                decision_files.add(repo_root / path)
            if is_spec_suite_file(path):
                path_parts = path.parts
                if len(path_parts) >= 3 and path_parts[2] == "_template" and target.exists():
                    spec_files.add(repo_root / path)
                else:
                    suite_dir = repo_root / "docs" / "specs" / path_parts[2]
                    for name in ("spec.md", "plan.md"):
                        candidate = suite_dir / name
                        if candidate.exists():
                            spec_files.add(candidate)
                    todo_candidate = suite_dir / "TODO.md"
                    if todo_candidate.exists():
                        spec_files.add(todo_candidate)
    else:
        exec_plans.update(path for path in (repo_root / "docs" / "exec-plans").glob("*.md") if path.name != "README.md")
        release_files.update(path for path in (repo_root / "docs" / "releases").glob("*.md") if path.name != "README.md")
        sprint_files.update(path for path in (repo_root / "docs" / "sprints").glob("*.md") if path.name != "README.md")
        decision_files.update(path for path in (repo_root / "docs" / "decisions").glob("*.md") if path.name != "README.md")
        specs_root = repo_root / "docs" / "specs"
        for suite_dir in specs_root.glob("FR-*"):
            if not suite_dir.is_dir():
                continue
            for name in ("spec.md", "plan.md"):
                candidate = suite_dir / name
                if candidate.exists():
                    spec_files.add(candidate)
        for suite_dir in specs_root.glob("FR-*"):
            if not suite_dir.is_dir():
                continue
            candidate = suite_dir / "TODO.md"
            if candidate.exists():
                spec_files.add(candidate)
        template_dir = specs_root / "_template"
        for name in ("spec.md", "plan.md"):
            candidate = template_dir / name
            if candidate.exists():
                spec_files.add(candidate)
        template_todo = template_dir / "TODO.md"
        if template_todo.exists():
            spec_files.add(template_todo)

    return (
        sorted(exec_plans),
        sorted(spec_files),
        sorted(release_files),
        sorted(sprint_files),
        sorted(decision_files),
    )


def validate_context_rules(
    repo_root: Path,
    changed_paths: list[str] | None = None,
    *,
    current_issue: int | None = None,
) -> list[str]:
    errors: list[str] = []
    exec_plans, spec_files, release_files, sprint_files, decision_files = collect_targets(repo_root, changed_paths)

    if changed_paths is not None:
        for raw_path in changed_paths:
            path = Path(raw_path)
            if not (
                is_exec_plan_file(path)
                or is_release_file(path)
                or is_sprint_file(path)
                or is_decision_file(path)
                or is_spec_suite_file(path)
            ):
                continue
            target = repo_root / path
            if not target.exists():
                errors.append(f"{target}: 变更目标不存在（可能已删除），请补充替代工件或同步调整引用。")

    if changed_paths is not None:
        touched_spec_dirs = formal_spec_dirs(changed_paths)
        if touched_spec_dirs:
            authorized_spec_dirs = authorized_formal_spec_dirs(repo_root, current_issue=current_issue)
            for spec_dir in sorted(touched_spec_dirs):
                if spec_dir not in authorized_spec_dirs:
                    errors.append(
                        f"{repo_root / spec_dir}: 当前 touched formal spec 套件未被任何 active exec-plan 绑定。"
                    )

    if changed_paths is not None:
        for raw_path in changed_paths:
            path = Path(raw_path)
            target = repo_root / path
            if not (is_exec_plan_file(path) and not is_template(path) and target.exists()):
                continue
            fields = parse_exec_plan_metadata(target)
            exec_issue = fields.get("Issue", "").strip()
            if current_issue is not None and exec_issue and exec_issue != str(current_issue) and not is_inactive_exec_plan(fields):
                errors.append(
                    f"{target}: 当前 touched exec-plan 的 `Issue` `{exec_issue}` 与当前执行回合 `#{current_issue}` 不一致。"
                )
            input_mode = classify_exec_plan_input_mode(fields)
            if input_mode == INPUT_MODE_FORMAL_SPEC:
                errors.extend(
                    f"{target}: {error}"
                    for error in validate_bound_formal_spec_scope(repo_root, fields, changed_paths)
                )
            if fields.get("item_type") != "GOV":
                continue
            if input_mode != INPUT_MODE_BOOTSTRAP:
                continue
            errors.extend(
                f"{target}: {error}"
                for error in validate_bound_decision_contract(repo_root, fields, require_present=True)
            )

        exec_plan_to_decision: dict[str, list[tuple[Path, dict[str, str]]]] = {}
        for exec_plan, fields in eligible_governance_exec_plans(repo_root, current_issue=current_issue):
            related_decision = fields.get("关联 decision", "")
            if not related_decision:
                continue
            decision_path = (repo_root / related_decision).resolve()
            try:
                normalized = decision_path.relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                continue
            exec_plan_to_decision.setdefault(normalized, []).append((exec_plan, fields))

        for raw_path in changed_paths:
            path = Path(raw_path)
            target = repo_root / path
            if not (is_decision_file(path) and target.exists()):
                continue
            decision_item_type = decision_item_type_from_name(path)
            if decision_item_type in {"FR", "HOTFIX", "CHORE"}:
                continue
            normalized_target = target.resolve().relative_to(repo_root.resolve()).as_posix()
            if normalized_target not in exec_plan_to_decision:
                errors.append(f"{target}: 当前 touched decision 未被任何 exec-plan 通过 `关联 decision` 关联。")
                continue
            for exec_plan_path, exec_plan_fields in exec_plan_to_decision[normalized_target]:
                payload = dict(exec_plan_fields)
                payload["关联 decision"] = normalized_target
                require_present = classify_exec_plan_input_mode(exec_plan_fields) == INPUT_MODE_BOOTSTRAP
                errors.extend(
                    f"{target}: {error}"
                    for error in validate_bound_decision_contract(repo_root, payload, require_present=require_present)
                )

    for path in exec_plans:
        errors.extend(validate_exec_plan(path, repo_root=repo_root))
    for path in spec_files:
        errors.extend(validate_spec_context_file(path))
    for path in release_files:
        errors.extend(validate_release_or_sprint(path, repo_root))
    for path in sprint_files:
        errors.extend(validate_release_or_sprint(path, repo_root))
    for path in decision_files:
        errors.extend(validate_decision(path))
    return errors


def validate_repository(repo_root: Path) -> list[str]:
    # Repository-wide validation enforces current baseline artifacts only:
    # templates plus release/sprint index documents. Historical instance files
    # are validated when they re-enter a changed execution round.
    errors: list[str] = []
    baseline_paths: list[str] = []
    template_candidates = (
        repo_root / "docs" / "exec-plans" / "_template.md",
        repo_root / "docs" / "specs" / "_template" / "spec.md",
        repo_root / "docs" / "specs" / "_template" / "plan.md",
        repo_root / "docs" / "releases" / "_template.md",
        repo_root / "docs" / "sprints" / "_template.md",
    )
    for candidate in template_candidates:
        relative = candidate.relative_to(repo_root).as_posix()
        if candidate.exists():
            baseline_paths.append(relative)
        else:
            errors.append(f"{candidate}: 缺少基线模板工件 `{relative}`。")

    template_todo = repo_root / "docs" / "specs" / "_template" / "TODO.md"
    if template_todo.exists():
        baseline_paths.append(template_todo.relative_to(repo_root).as_posix())
    else:
        errors.append(f"{template_todo}: 缺少基线模板工件 `{template_todo.relative_to(repo_root).as_posix()}`。")

    for path in sorted((repo_root / "docs" / "releases").glob("*.md")):
        if path.name in {"README.md", "_template.md"}:
            continue
        baseline_paths.append(path.relative_to(repo_root).as_posix())

    for path in sorted((repo_root / "docs" / "sprints").glob("*.md")):
        if path.name in {"README.md", "_template.md"}:
            continue
        baseline_paths.append(path.relative_to(repo_root).as_posix())

    errors.extend(validate_context_rules(repo_root, changed_paths=baseline_paths))
    return errors


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    base_ref = args.base_ref or args.base_sha
    head_ref = args.head_sha or args.head_ref

    changed_paths: list[str] | None = None
    if base_ref:
        changed_paths = git_changed_files(base_ref, head_ref, repo=repo_root)

    current_issue = args.current_issue
    if current_issue is None:
        current_issue = infer_current_issue(args.head_ref)
    if current_issue is None:
        current_issue = infer_current_issue(git_current_branch(repo=repo_root))

    if changed_paths is None:
        errors = validate_repository(repo_root)
    else:
        errors = validate_context_rules(repo_root, changed_paths, current_issue=current_issue)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("context-guard 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
