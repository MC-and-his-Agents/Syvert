from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from scripts.policy.policy import spec_suite_policy


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
    "关联 decision",
}
EXEC_PLAN_METADATA_HEADERS = {"## 关联信息", "## 事项上下文"}
DECISION_METADATA_KEYS = {"Issue", "item_key", "item_type", "release", "sprint"}
BOUND_SPEC_FILE_NAMES = {"spec.md", "plan.md"}
INPUT_MODE_FORMAL_SPEC = "formal_spec"
INPUT_MODE_BOOTSTRAP = "bootstrap"
INPUT_MODE_UNBOUND = "unbound"
PLACEHOLDER_BINDING_PREFIXES = ("无", "none", "n/a", "na", "not applicable", "not-applicable")


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

    for raw_line in path.read_text(encoding="utf-8").splitlines():
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
            payload["conflict"] = "duplicate_metadata_keys"
            payload["duplicate_key"] = key
            if "Issue" in payload:
                payload["Issue"] = normalize_issue(payload["Issue"])
            return payload
        seen_keys.add(key)
        payload[key] = value

    if "Issue" in payload:
        payload["Issue"] = normalize_issue(payload["Issue"])
    return payload


def parse_markdown_metadata(text: str, *, allowed_keys: set[str] | None = None) -> dict[str, str]:
    payload: dict[str, str] = {}
    for match in METADATA_RE.finditer(text):
        key = match.group(1).strip()
        if allowed_keys is not None and key not in allowed_keys:
            continue
        if key in payload:
            continue
        payload[key] = normalize_value(match.group(2))
    if "Issue" in payload:
        payload["Issue"] = normalize_issue(payload["Issue"])
    return payload


def parse_decision_metadata(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return parse_markdown_metadata(path.read_text(encoding="utf-8"), allowed_keys=DECISION_METADATA_KEYS)


def classify_exec_plan_input_mode(payload: Mapping[str, str]) -> str:
    if has_meaningful_binding(payload.get("关联 spec", "")):
        return INPUT_MODE_FORMAL_SPEC
    if str(payload.get("item_type", "")).strip() == "GOV":
        return INPUT_MODE_BOOTSTRAP
    return INPUT_MODE_UNBOUND


def normalize_bound_spec_dir(repo_root: Path, related_spec: str) -> Path | None:
    if not related_spec or not related_spec.startswith("docs/specs/"):
        return None
    candidate = (repo_root / related_spec.rstrip("/")).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None
    if candidate.is_file() and candidate.name in BOUND_SPEC_FILE_NAMES:
        return candidate.parent
    parts = candidate.relative_to(repo_root.resolve()).parts if candidate.exists() else Path(related_spec.rstrip("/")).parts
    if len(parts) < 3 or parts[0] != "docs" or parts[1] != "specs" or not parts[2].startswith("FR-"):
        return None
    return candidate


def spec_dir_has_minimum_suite(spec_dir: Path) -> bool:
    if not spec_dir.exists() or not spec_dir.is_dir():
        return False
    required_files = set(spec_suite_policy()["required_files"])
    child_names = {child.name for child in spec_dir.iterdir()}
    return required_files.issubset(child_names)


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

    if candidate.is_file():
        if candidate.name in BOUND_SPEC_FILE_NAMES:
            candidate = candidate.parent
        else:
            return [f"`关联 spec` 必须指向 formal spec 目录或 `spec.md`/`plan.md` 文件：`{related_spec}`。"]

    relative_parts = candidate.relative_to(repo_root.resolve()).parts if candidate.exists() else Path(related_spec.rstrip("/")).parts
    if len(relative_parts) < 3 or relative_parts[0] != "docs" or relative_parts[1] != "specs" or not relative_parts[2].startswith("FR-"):
        return [f"`关联 spec` 必须绑定到具体 FR formal spec 套件：`{related_spec}`。"]
    if not candidate.exists():
        return [f"`关联 spec` 指向的路径不存在：`{related_spec}`。"]
    if not candidate.is_dir():
        return [f"`关联 spec` 必须指向 formal spec 目录或 `spec.md`/`plan.md` 文件：`{related_spec}`。"]
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

    decision_path = (repo_root / related_decision).resolve()
    try:
        decision_path.relative_to(repo_root.resolve())
    except ValueError:
        return [f"`关联 decision` 指向仓库外路径：`{related_decision}`。"]
    if not decision_path.exists():
        return [f"`关联 decision` 指向的路径不存在：`{related_decision}`。"]

    decision_fields = parse_decision_metadata(decision_path)
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
