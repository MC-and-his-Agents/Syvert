from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from scripts.policy.policy import formal_spec_dirs, spec_suite_policy


ITEM_TYPES = {"FR", "HOTFIX", "GOV", "CHORE"}
ITEM_KEY_RE = re.compile(r"^(FR|HOTFIX|GOV|CHORE)-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
METADATA_RE = re.compile(r"^- ([^:：]+)[:：]\s*(.*?)\s*$", re.MULTILINE)
BODY_ITEM_CONTEXT_RE = {
    "item_key": re.compile(r"item_key:\s*`?([A-Z]+-\d{4}-[a-z0-9-]+)`?", re.IGNORECASE),
    "item_type": re.compile(r"item_type:\s*`?([A-Z]+)`?", re.IGNORECASE),
    "release": re.compile(r"release:\s*`?([A-Za-z0-9._-]+)`?", re.IGNORECASE),
    "sprint": re.compile(r"sprint:\s*`?([A-Za-z0-9._-]+)`?", re.IGNORECASE),
    "issue": re.compile(r"Issue:\s*#?(\d+)", re.IGNORECASE),
}
REQUIRED_EXEC_PLAN_FIELDS = ("Issue", "item_key", "item_type", "release", "sprint")
EXEC_PLAN_METADATA_KEYS = {
    "item_key",
    "Issue",
    "item_type",
    "release",
    "sprint",
    "active 收口事项",
    "状态",
    "关联 spec",
    "额外关联 specs",
    "关联 decision",
}
EXEC_PLAN_METADATA_HEADERS = {"## 关联信息", "## 事项上下文"}
DECISION_METADATA_KEYS = {"Issue", "item_key", "item_type", "release", "sprint"}
BOUND_SPEC_FILE_NAMES = {"spec.md", "plan.md"}
INPUT_MODE_FORMAL_SPEC = "formal_spec"
INPUT_MODE_BOOTSTRAP = "bootstrap"
INPUT_MODE_UNBOUND = "unbound"
PLACEHOLDER_BINDING_PREFIXES = ("无", "none", "n/a", "na", "not applicable", "not-applicable")
LEGACY_FORMAL_SPEC_DECISION_ITEM_TYPES = {"FR", "HOTFIX", "CHORE"}
LEGACY_FORMAL_SPEC_DECISION_PATHS = {"docs/decisions/ADR-0001-governance-bootstrap-contract.md"}
MISSING_BOUND_DECISION_METADATA_ERRORS = {
    "`关联 decision` 缺少 `Issue` 字段，bootstrap contract 无法与当前事项建立对应关系。",
    "`关联 decision` 缺少 `item_key` 字段，bootstrap contract 无法与当前事项建立对应关系。",
}
LEGACY_TODO_CLEANUP_ADDITIONAL_SPEC_RULES = {
    "GOV-0029-remove-legacy-todo-md": {
        Path("docs/specs/FR-0001-governance-stack-v1"): {"spec.md", "plan.md", "risks.md", "TODO.md"},
        Path("docs/specs/FR-0002-content-detail-runtime-v0-1"): {"TODO.md"},
    }
}


def allows_legacy_metadata_free_formal_spec_decision(
    payload: Mapping[str, str],
    errors: list[str],
) -> bool:
    item_type = str(payload.get("item_type", "")).strip()
    related_spec = str(payload.get("关联 spec", "")).strip()
    related_decision = str(payload.get("关联 decision", "")).strip()
    if item_type not in LEGACY_FORMAL_SPEC_DECISION_ITEM_TYPES:
        return False
    if not has_meaningful_binding(related_spec):
        return False
    normalized_decision = Path(related_decision).as_posix()
    if normalized_decision not in LEGACY_FORMAL_SPEC_DECISION_PATHS:
        return False
    return bool(errors) and set(errors).issubset(MISSING_BOUND_DECISION_METADATA_ERRORS)


def normalize_value(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("`") and cleaned.endswith("`"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def normalize_issue(value: object) -> str:
    text = str(value).strip()
    if text.startswith("#"):
        text = text[1:]
    return text


def has_meaningful_binding(value: object) -> bool:
    cleaned = normalize_value(str(value))
    if not cleaned:
        return False
    lowered = cleaned.lower()
    return not lowered.startswith(PLACEHOLDER_BINDING_PREFIXES)


def valid_item_key(item_key: str, item_type: str | None = None) -> bool:
    match = ITEM_KEY_RE.fullmatch(item_key)
    if not match:
        return False
    if item_type is None:
        return True
    return match.group(1) == item_type


def parse_item_context_from_body(body: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    for key, pattern in BODY_ITEM_CONTEXT_RE.items():
        match = pattern.search(body or "")
        if match:
            payload[key] = match.group(1)
    return payload


def parse_exec_plan_metadata(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    payload: dict[str, str] = {"exec_plan": path.as_posix()}
    seen_keys: set[str] = set()
    in_metadata_section = False

    for raw_line in strip_fenced_code_blocks(path.read_text(encoding="utf-8")).splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            in_metadata_section = stripped in EXEC_PLAN_METADATA_HEADERS
            continue
        if not in_metadata_section:
            continue
        match = METADATA_RE.match(raw_line.strip())
        if not match:
            continue
        key = match.group(1).strip()
        value = normalize_value(match.group(2))
        if key not in EXEC_PLAN_METADATA_KEYS:
            continue
        if key in seen_keys:
            payload.setdefault("conflict", "duplicate_metadata_keys")
            payload.setdefault("duplicate_key", key)
            continue
        seen_keys.add(key)
        payload[key] = value

    if "Issue" in payload:
        payload["Issue"] = normalize_issue(payload["Issue"])
    return payload


def strip_fenced_code_blocks(text: str) -> str:
    cleaned: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if not in_fence:
            if stripped and stripped[0] in {"`", "~"}:
                marker_len = 0
                for char in stripped:
                    if char == stripped[0]:
                        marker_len += 1
                        continue
                    break
                if marker_len >= 3:
                    in_fence = True
                    fence_char = stripped[0]
                    fence_len = marker_len
                    continue
            cleaned.append(line)
            continue

        closing = stripped.strip()
        if closing and len(closing) >= fence_len and all(char == fence_char for char in closing):
            in_fence = False

    return "".join(cleaned)


def parse_markdown_metadata(
    text: str,
    *,
    allowed_keys: set[str] | None = None,
    fail_on_duplicates: bool = False,
) -> dict[str, str]:
    payload: dict[str, str] = {}
    seen_keys: set[str] = set()
    metadata_text = strip_fenced_code_blocks(text)
    for match in METADATA_RE.finditer(metadata_text):
        key = match.group(1).strip()
        if allowed_keys is not None and key not in allowed_keys:
            continue
        if key in seen_keys:
            if fail_on_duplicates:
                payload.setdefault("conflict", "duplicate_metadata_keys")
                payload.setdefault("duplicate_key", key)
            continue
        seen_keys.add(key)
        payload[key] = normalize_value(match.group(2))
    if "Issue" in payload:
        payload["Issue"] = normalize_issue(payload["Issue"])
    return payload


def parse_decision_metadata(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return parse_markdown_metadata(
        path.read_text(encoding="utf-8"),
        allowed_keys=DECISION_METADATA_KEYS,
        fail_on_duplicates=True,
    )


def classify_exec_plan_input_mode(payload: Mapping[str, str]) -> str:
    if has_meaningful_binding(payload.get("关联 spec", "")):
        return INPUT_MODE_FORMAL_SPEC
    if str(payload.get("item_type", "")).strip() == "GOV":
        return INPUT_MODE_BOOTSTRAP
    return INPUT_MODE_UNBOUND


def normalize_bound_spec_parts(related_spec: str) -> tuple[str, ...] | None:
    normalized = related_spec.rstrip("/")
    if not normalized or not normalized.startswith("docs/specs/"):
        return None
    parts = Path(normalized).parts
    if len(parts) == 3 and parts[0] == "docs" and parts[1] == "specs" and parts[2].startswith("FR-"):
        return parts
    if len(parts) == 4 and parts[0] == "docs" and parts[1] == "specs" and parts[2].startswith("FR-") and parts[3] in BOUND_SPEC_FILE_NAMES:
        return parts
    return None


def normalize_bound_spec_dir(repo_root: Path, related_spec: str) -> Path | None:
    parts = normalize_bound_spec_parts(related_spec)
    if parts is None:
        return None
    candidate = (repo_root / related_spec.rstrip("/")).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None
    if len(parts) == 4:
        if candidate.exists() and not candidate.is_file():
            return None
        return candidate.parent
    if candidate.exists() and not candidate.is_dir():
        return None
    return candidate


def normalize_bound_decision_path(repo_root: Path, related_decision: str) -> Path | None:
    if not related_decision or not related_decision.startswith("docs/decisions/"):
        return None
    candidate = (repo_root / related_decision.rstrip("/")).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None
    parts = candidate.relative_to(repo_root.resolve()).parts if candidate.exists() else Path(related_decision.rstrip("/")).parts
    if len(parts) != 3 or parts[0] != "docs" or parts[1] != "decisions" or not parts[2].endswith(".md"):
        return None
    if candidate.exists() and not candidate.is_file():
        return None
    return candidate


def spec_dir_has_minimum_suite(spec_dir: Path) -> bool:
    if not spec_dir.exists() or not spec_dir.is_dir():
        return False
    required_files = set(spec_suite_policy()["required_files"])
    child_names = {child.name for child in spec_dir.iterdir()}
    return required_files.issubset(child_names)


def parse_additional_spec_bindings(raw_value: str) -> list[str]:
    cleaned = normalize_value(raw_value)
    if not cleaned:
        return []
    return [item.strip() for item in re.split(r"[，,]", cleaned) if item.strip()]


def additional_spec_policy_item_key(payload: Mapping[str, str]) -> str | None:
    item_key = str(payload.get("item_key", "")).strip()
    if str(payload.get("item_type", "")).strip() != "GOV":
        return None
    if classify_exec_plan_input_mode(payload) != INPUT_MODE_FORMAL_SPEC:
        return None
    if item_key not in LEGACY_TODO_CLEANUP_ADDITIONAL_SPEC_RULES:
        return None
    return item_key


def diff_paths_for_spec_dir(changed_files: list[str], spec_dir: Path) -> list[Path]:
    prefix = f"{spec_dir.as_posix()}/"
    return [Path(path) for path in changed_files if path.startswith(prefix)]


def validate_additional_spec_contracts(
    repo_root: Path,
    payload: Mapping[str, str],
) -> tuple[list[str], list[Path]]:
    raw_value = str(payload.get("额外关联 specs", "")).strip()
    if not has_meaningful_binding(raw_value):
        return [], []

    policy_item_key = additional_spec_policy_item_key(payload)
    if policy_item_key is None:
        return ["`额外关联 specs` 仅允许用于 `GOV-0029-remove-legacy-todo-md` 的 legacy `TODO.md` 清理事项。"], []

    allowed_spec_rules = LEGACY_TODO_CLEANUP_ADDITIONAL_SPEC_RULES[policy_item_key]
    allowed_spec_dirs = set(allowed_spec_rules)
    errors: list[str] = []
    normalized_dirs: list[Path] = []
    seen: set[Path] = set()
    for raw_path in parse_additional_spec_bindings(raw_value):
        binding_errors = validate_bound_spec_contract(repo_root, {"关联 spec": raw_path})
        if binding_errors:
            errors.extend(f"`额外关联 specs` 条目 `{raw_path}` 非法：{error}" for error in binding_errors)
            continue
        spec_dir = normalize_bound_spec_dir(repo_root, raw_path)
        if spec_dir is None:
            errors.append(f"`额外关联 specs` 条目 `{raw_path}` 无法解析为 formal spec 套件根目录。")
            continue
        relative = spec_dir.relative_to(repo_root.resolve())
        if relative not in allowed_spec_dirs:
            errors.append(
                f"`额外关联 specs` 条目 `{raw_path}` 不在 `{policy_item_key}` 允许清理的 legacy `TODO.md` 套件范围内。"
            )
            continue
        if relative in seen:
            continue
        seen.add(relative)
        normalized_dirs.append(relative)
    return errors, normalized_dirs


def validate_additional_spec_diff_scope(
    repo_root: Path,
    payload: Mapping[str, str],
    changed_files: list[str],
    additional_spec_dirs: list[Path],
) -> list[str]:
    if not changed_files or not additional_spec_dirs:
        return []
    if additional_spec_policy_item_key(payload) is None:
        return []

    policy_item_key = additional_spec_policy_item_key(payload)
    if policy_item_key is None:
        return []

    allowed_spec_rules = LEGACY_TODO_CLEANUP_ADDITIONAL_SPEC_RULES[policy_item_key]
    errors: list[str] = []
    for spec_dir in additional_spec_dirs:
        suite_paths = diff_paths_for_spec_dir(changed_files, spec_dir)
        expected_todo = spec_dir / "TODO.md"
        allowed_paths = {spec_dir / name for name in allowed_spec_rules[spec_dir]}
        if expected_todo not in suite_paths:
            errors.append(
                f"`额外关联 specs` 条目 `{spec_dir.as_posix()}/` 必须在当前 diff 中删除该套件的 legacy `TODO.md`。"
            )
            continue
        unexpected = sorted(path.as_posix() for path in suite_paths if path not in allowed_paths)
        if unexpected:
            errors.append(
                f"`额外关联 specs` 条目 `{spec_dir.as_posix()}/` 超出当前事项允许的最小文件集合：{', '.join(unexpected)}。"
            )
            continue
        if (repo_root / expected_todo).exists():
            errors.append(
                f"`额外关联 specs` 条目 `{spec_dir.as_posix()}/` 仅允许在当前 diff 中删除 legacy `TODO.md`，发现该文件仍存在。"
            )
    return errors


def authorized_additional_spec_dirs_for_diff(
    repo_root: Path,
    payload: Mapping[str, str],
    changed_files: list[str] | None,
) -> tuple[list[str], list[Path]]:
    additional_errors, additional_spec_dirs = validate_additional_spec_contracts(repo_root, payload)
    if additional_errors:
        return additional_errors, []
    if not changed_files:
        return [], []
    diff_scope_errors = validate_additional_spec_diff_scope(repo_root, payload, changed_files, additional_spec_dirs)
    if diff_scope_errors:
        return diff_scope_errors, []
    touched_spec_dirs = formal_spec_dirs(changed_files)
    return [], [spec_dir for spec_dir in additional_spec_dirs if spec_dir in touched_spec_dirs]


def validate_bound_formal_spec_scope(
    repo_root: Path,
    payload: Mapping[str, str],
    changed_files: list[str],
) -> list[str]:
    touched_spec_dirs = formal_spec_dirs(changed_files)
    spec_dir = normalize_bound_spec_dir(repo_root, str(payload.get("关联 spec", "")).strip())
    if spec_dir is None:
        return []
    bound_spec_dir = spec_dir.relative_to(repo_root.resolve())
    additional_errors, additional_spec_dirs = validate_additional_spec_contracts(repo_root, payload)
    if additional_errors:
        return additional_errors
    diff_scope_errors = validate_additional_spec_diff_scope(repo_root, payload, changed_files, additional_spec_dirs)
    if diff_scope_errors:
        return diff_scope_errors
    if not touched_spec_dirs:
        return []
    authorized_spec_dirs = {bound_spec_dir, *additional_spec_dirs}
    if not any(path in authorized_spec_dirs for path in touched_spec_dirs):
        return ["当前 diff 触碰的 formal spec 套件与 `关联 spec` / `额外关联 specs` 绑定不一致。"]
    foreign = sorted(path.as_posix() for path in touched_spec_dirs if path not in authorized_spec_dirs)
    if foreign:
        return [f"当前 diff 只能触碰当前绑定的 formal spec 套件，发现额外套件：{', '.join(foreign)}。"]
    return []


def validate_bound_spec_contract(repo_root: Path, payload: Mapping[str, str]) -> list[str]:
    related_spec = str(payload.get("关联 spec", "")).strip()
    if not related_spec:
        return ["缺少 `关联 spec`，无法绑定当前事项的 formal spec 输入。"]
    candidate = (repo_root / related_spec.rstrip("/")).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return [f"`关联 spec` 指向仓库外路径：`{related_spec}`。"]
    if not related_spec.startswith("docs/specs/"):
        return [f"`关联 spec` 必须绑定到具体 FR formal spec 套件：`{related_spec}`。"]

    parts = normalize_bound_spec_parts(related_spec)
    if parts is None:
        return [f"`关联 spec` 必须绑定到 FR formal spec 套件根目录，或其下的 `spec.md`/`plan.md` 文件：`{related_spec}`。"]

    if len(parts) == 4:
        if not candidate.exists():
            return [f"`关联 spec` 指向的路径不存在：`{related_spec}`。"]
        if not candidate.is_file():
            return [f"`关联 spec` 必须指向 FR formal spec 套件根目录，或其下的 `spec.md`/`plan.md` 文件：`{related_spec}`。"]
        candidate = candidate.parent
    else:
        if not candidate.exists():
            return [f"`关联 spec` 指向的路径不存在：`{related_spec}`。"]
        if not candidate.is_dir():
            return [f"`关联 spec` 必须指向 FR formal spec 套件根目录，或其下的 `spec.md`/`plan.md` 文件：`{related_spec}`。"]

    if not spec_dir_has_minimum_suite(candidate):
        required_files = set(spec_suite_policy()["required_files"])
        child_names = {child.name for child in candidate.iterdir()}
        missing = sorted(required_files - child_names)
        return [f"`关联 spec` 指向的 formal spec 套件缺少最小必需文件：{', '.join(missing)}。"]
    return []


def validate_bound_decision_contract(
    repo_root: Path,
    payload: Mapping[str, str],
    *,
    require_present: bool,
) -> list[str]:
    related_decision = str(payload.get("关联 decision", "")).strip()
    if not related_decision:
        if require_present:
            return ["当前 exec-plan 缺少 `关联 decision`，bootstrap contract 无法与当前事项建立对应关系。"]
        return []

    decision_path = (repo_root / related_decision.rstrip("/")).resolve()
    try:
        decision_path.relative_to(repo_root.resolve())
    except ValueError:
        return [f"`关联 decision` 指向仓库外路径：`{related_decision}`。"]
    if not related_decision.startswith("docs/decisions/"):
        return [f"`关联 decision` 必须绑定到 `docs/decisions/*.md` 决策文档：`{related_decision}`。"]
    if normalize_bound_decision_path(repo_root, related_decision) is None:
        return [f"`关联 decision` 必须绑定到 `docs/decisions/*.md` 决策文档：`{related_decision}`。"]
    if not decision_path.exists():
        return [f"`关联 decision` 指向的路径不存在：`{related_decision}`。"]

    decision_fields = parse_decision_metadata(decision_path)
    if decision_fields.get("conflict") == "duplicate_metadata_keys":
        duplicate_key = decision_fields.get("duplicate_key", "unknown")
        return [f"`关联 decision` 元数据区存在重复键 `{duplicate_key}`，bootstrap contract 无法确认唯一绑定。"]

    errors: list[str] = []
    decision_issue = decision_fields.get("Issue", "")
    exec_issue = normalize_issue(payload.get("Issue", ""))
    decision_item_key = decision_fields.get("item_key", "")
    exec_item_key = str(payload.get("item_key", "")).strip()
    if require_present and not decision_issue:
        errors.append("`关联 decision` 缺少 `Issue` 字段，bootstrap contract 无法与当前事项建立对应关系。")
    if require_present and not decision_item_key:
        errors.append("`关联 decision` 缺少 `item_key` 字段，bootstrap contract 无法与当前事项建立对应关系。")
    if decision_issue and exec_issue and decision_issue != exec_issue:
        errors.append(
            f"`关联 decision` 的 `Issue` `{decision_issue}` 与当前 exec-plan 的 `Issue` `{exec_issue}` 不一致。"
        )
    if decision_item_key and exec_item_key and decision_item_key != exec_item_key:
        errors.append(
            f"`关联 decision` 的 `item_key` `{decision_item_key}` 与当前 exec-plan 的 `item_key` `{exec_item_key}` 不一致。"
        )
    return errors


def exec_plan_path_for_item_key(repo_root: Path, item_key: str) -> Path:
    return repo_root / "docs" / "exec-plans" / f"{item_key}.md"


def has_complete_item_context(payload: dict[str, str]) -> bool:
    return all(payload.get(field, "").strip() for field in REQUIRED_EXEC_PLAN_FIELDS)


def is_eligible_active_exec_plan(payload: dict[str, str]) -> bool:
    if not payload:
        return False
    if payload.get("conflict"):
        return False
    if is_inactive_exec_plan(payload):
        return False
    if not has_complete_item_context(payload):
        return False
    active_item = payload.get("active 收口事项", "")
    if active_item and active_item != payload.get("item_key", ""):
        return False
    return True


def load_item_context_from_exec_plan(repo_root: Path, item_key: str) -> dict[str, str]:
    matches: list[dict[str, str]] = []
    path = exec_plan_path_for_item_key(repo_root, item_key)
    payload = parse_exec_plan_metadata(path)
    if payload.get("conflict") == "duplicate_metadata_keys":
        return payload
    if is_eligible_active_exec_plan(payload):
        matches.append(payload)

    exec_plans_dir = repo_root / "docs" / "exec-plans"
    if not exec_plans_dir.exists():
        return matches[0] if len(matches) == 1 else {}
    for candidate in sorted(exec_plans_dir.glob("*.md")):
        if candidate.name == "README.md":
            continue
        if path.exists() and candidate.resolve() == path.resolve():
            continue
        metadata = parse_exec_plan_metadata(candidate)
        if metadata.get("conflict") == "duplicate_metadata_keys" and metadata.get("item_key") == item_key:
            return metadata
        if metadata.get("item_key") == item_key and is_eligible_active_exec_plan(metadata):
            matches.append(metadata)

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return {"conflict": "multiple_active_exec_plans", "item_key": item_key}
    return {}


def is_inactive_exec_plan(payload: dict[str, str]) -> bool:
    return payload.get("状态", "").lower().startswith("inactive")


def active_exec_plans_for_issue(repo_root: Path, issue_number: int) -> list[dict[str, str]]:
    exec_plans_dir = repo_root / "docs" / "exec-plans"
    if not exec_plans_dir.exists():
        return []

    matches: list[dict[str, str]] = []
    for path in sorted(exec_plans_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        payload = parse_exec_plan_metadata(path)
        if payload.get("Issue") != str(issue_number):
            continue
        if is_eligible_active_exec_plan(payload):
            matches.append(payload)
    return matches


def matching_exec_plan_for_issue(repo_root: Path, issue_number: int) -> dict[str, str]:
    eligible = active_exec_plans_for_issue(repo_root, issue_number)
    if len(eligible) != 1:
        return {}
    return eligible[0]
