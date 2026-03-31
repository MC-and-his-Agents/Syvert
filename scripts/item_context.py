from __future__ import annotations

import re
from pathlib import Path


ITEM_TYPES = {"FR", "HOTFIX", "GOV", "CHORE"}
ITEM_KEY_RE = re.compile(r"^(FR|HOTFIX|GOV|CHORE)-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
METADATA_RE = re.compile(r"^- ([^:：]+)[:：]\s*(.+?)\s*$")
BODY_ITEM_CONTEXT_RE = {
    "item_key": re.compile(r"item_key:\s*`?([A-Z]+-\d{4}-[a-z0-9-]+)`?", re.IGNORECASE),
    "item_type": re.compile(r"item_type:\s*`?([A-Z]+)`?", re.IGNORECASE),
    "release": re.compile(r"release:\s*`?([A-Za-z0-9._-]+)`?", re.IGNORECASE),
    "sprint": re.compile(r"sprint:\s*`?([A-Za-z0-9._-]+)`?", re.IGNORECASE),
    "issue": re.compile(r"Issue:\s*#?(\d+)", re.IGNORECASE),
}


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

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = METADATA_RE.match(raw_line.strip())
        if not match:
            continue
        key = match.group(1).strip()
        value = normalize_value(match.group(2))
        if key in {"item_key", "Issue", "item_type", "release", "sprint", "active 收口事项", "状态"}:
            payload[key] = value

    if "Issue" in payload:
        payload["Issue"] = normalize_issue(payload["Issue"])
    return payload


def exec_plan_path_for_item_key(repo_root: Path, item_key: str) -> Path:
    return repo_root / "docs" / "exec-plans" / f"{item_key}.md"


def load_item_context_from_exec_plan(repo_root: Path, item_key: str) -> dict[str, str]:
    matches: list[dict[str, str]] = []
    path = exec_plan_path_for_item_key(repo_root, item_key)
    payload = parse_exec_plan_metadata(path)
    if payload and not is_inactive_exec_plan(payload):
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
        if metadata.get("item_key") == item_key and not is_inactive_exec_plan(metadata):
            matches.append(metadata)

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return {"conflict": "multiple_active_exec_plans", "item_key": item_key}
    return {}


def is_inactive_exec_plan(payload: dict[str, str]) -> bool:
    return payload.get("状态", "").lower().startswith("inactive")


def matching_exec_plan_for_issue(repo_root: Path, issue_number: int) -> dict[str, str]:
    exec_plans_dir = repo_root / "docs" / "exec-plans"
    if not exec_plans_dir.exists():
        return {}

    matches: list[dict[str, str]] = []
    for path in sorted(exec_plans_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        payload = parse_exec_plan_metadata(path)
        if payload.get("Issue") == str(issue_number):
            matches.append(payload)

    eligible = [item for item in matches if not is_inactive_exec_plan(item)]
    if len(eligible) != 1:
        return {}

    candidate = eligible[0]
    active_item = candidate.get("active 收口事项", "")
    if active_item and active_item != candidate.get("item_key", ""):
        return {}
    return candidate
