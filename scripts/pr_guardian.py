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
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

from scripts.common import (
    CommandError,
    REPO_ROOT,
    bool_text,
    dump_json,
    ensure_parent,
    format_changed_files,
    integration_ref_is_checkable,
    load_json,
    require_cli,
    run,
)
from scripts.item_context import active_exec_plans_for_issue, load_item_context_from_exec_plan, parse_item_context_from_body
from scripts.open_pr import extract_issue_canonical_integration_fields, extract_issue_summary_sections
from scripts.state_paths import guardian_legacy_state_path, guardian_state_path


SCHEMA_PATH = REPO_ROOT / "scripts" / "policy" / "pr_review_result_schema.json"
CODE_REVIEW_PATH = "code_review.md"
DEFAULT_STATE_FILE = guardian_state_path()
VALID_VERDICTS = {"APPROVE", "REQUEST_CHANGES"}
INTEGRATION_TOUCHPOINT_VALUES = {"none", "check_required", "active", "blocked", "resolved"}
EXTERNAL_DEPENDENCY_VALUES = {"none", "syvert", "webenvoy", "both"}
CONTRACT_SURFACE_VALUES = {
    "none",
    "execution_provider",
    "ids_trace",
    "errors",
    "raw_normalized",
    "diagnostics_observability",
    "runtime_modes",
}
JOINT_ACCEPTANCE_VALUES = {"yes", "no"}
SHARED_CONTRACT_CHANGED_VALUES = {"yes", "no"}
INTEGRATION_STATUS_VALUES = {"yes", "no"}
INTEGRATION_CHECK_CANONICAL_FIELDS = {
    "integration_touchpoint",
    "shared_contract_changed",
    "integration_ref",
    "external_dependency",
    "merge_gate",
    "contract_surface",
    "joint_acceptance_needed",
    "integration_status_checked_before_pr",
    "integration_status_checked_before_merge",
}
ISSUE_CANONICAL_INTEGRATION_FIELDS = (
    "integration_touchpoint",
    "shared_contract_changed",
    "integration_ref",
    "external_dependency",
    "merge_gate",
    "contract_surface",
    "joint_acceptance_needed",
)
REVIEW_REQUIRED_BODY_FIELDS = ("issue", "item_key", "item_type", "release", "sprint")
REVIEW_EXECUTION_RULES = (
    "工件完整性只用于确认输入是否足够，不要把 checks、Draft 状态或 merge 动作当成 reviewer 结论来源。",
    "若缺少必要工件或验证证据，应明确指出阻断项；merge gate、head 绑定与 squash merge 安全性由 guardian gate 入口单独消费。",
)
REVIEW_SECTION_ALIASES = {
    "摘要": "summary",
    "Issue 摘要": "issue_summary",
    "关联事项": "item_context",
    "风险": "risk",
    "风险级别": "risk",
    "验证": "validation",
    "回滚": "rollback",
}
RAW_BODY_NOISE_HEADINGS = {"变更文件", "检查清单"}
REVIEW_GUIDE_HEADINGS = (
    "## 工件完整性检查",
    "## Review Rubric",
    "## 事项分级视角",
    "## 职责边界说明",
)
ISSUE_CONTEXT_HEADINGS = ("Goal", "Scope", "Required Outcomes", "Acceptance", "Acceptance Criteria", "Out of Scope", "Dependency")


def codex_review_timeout_seconds() -> int | None:
    raw_value = os.environ.get("SYVERT_GUARDIAN_TIMEOUT_SECONDS")
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    try:
        timeout_seconds = int(value)
    except ValueError as exc:
        raise SystemExit("SYVERT_GUARDIAN_TIMEOUT_SECONDS 必须是正整数；留空或不设置表示不限制超时。") from exc
    if timeout_seconds <= 0:
        raise SystemExit("SYVERT_GUARDIAN_TIMEOUT_SECONDS 必须是正整数；留空或不设置表示不限制超时。")
    return timeout_seconds


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="执行 Syvert PR guardian 审查。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("review", help="执行只读审查")
    review.add_argument("pr_number", type=int)
    review.add_argument("--post-review", action="store_true")
    review.add_argument("--json-output")

    merge = subparsers.add_parser("merge-if-safe", help="审查通过后执行 squash merge")
    merge.add_argument("pr_number", type=int)
    merge.add_argument("--post-review", action="store_true")
    merge.add_argument("--delete-branch", action="store_true")
    merge.add_argument("--refresh-review", action="store_true")
    merge.add_argument("--confirm-integration-recheck", action="store_true")

    return parser.parse_args(argv)


def require_auth() -> None:
    require_cli("gh")
    require_cli("codex")
    run(["gh", "auth", "status"], cwd=REPO_ROOT)


def pr_meta(pr_number: int) -> dict:
    completed = run(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "number,title,body,url,isDraft,baseRefName,headRefName,headRefOid,author",
        ],
        cwd=REPO_ROOT,
    )
    return json.loads(completed.stdout)


def prepare_worktree(pr_number: int, meta: dict) -> tuple[Path, Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix="syvert-pr-guardian-"))
    worktree_dir = temp_dir / "worktree"
    base_ref = meta["baseRefName"]

    run(["git", "fetch", "origin", base_ref], cwd=REPO_ROOT, check=False)
    run(["git", "fetch", "origin", f"pull/{pr_number}/head:refs/remotes/origin/pr/{pr_number}"], cwd=REPO_ROOT)
    run(["git", "worktree", "add", "--detach", str(worktree_dir), f"origin/pr/{pr_number}"], cwd=REPO_ROOT)
    return temp_dir, worktree_dir


def cleanup(temp_dir: Path) -> None:
    worktree_dir = temp_dir / "worktree"
    if worktree_dir.exists():
        run(["git", "worktree", "remove", "--force", str(worktree_dir)], cwd=REPO_ROOT, check=False)
    shutil.rmtree(temp_dir, ignore_errors=True)


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_guardian_payload(meta: dict, result: dict) -> dict:
    return {
        "schema_version": 1,
        "pr_number": meta["number"],
        "head_sha": meta["headRefOid"],
        "verdict": result["verdict"],
        "safe_to_merge": result["safe_to_merge"],
        "summary": result["summary"],
        "reviewed_at": now_iso_utc(),
    }


def load_guardian_state(path: Path = DEFAULT_STATE_FILE) -> dict:
    if path.exists():
        return load_json(path)
    legacy_path = guardian_legacy_state_path()
    if path == DEFAULT_STATE_FILE and legacy_path.exists():
        return load_json(legacy_path)
    return {"prs": {}}


def save_guardian_result(pr_number: int, payload: dict, *, path: Path = DEFAULT_STATE_FILE) -> None:
    ensure_parent(path)
    state = load_guardian_state(path)
    state.setdefault("prs", {})[str(pr_number)] = payload
    dump_json(path, state)


def valid_guardian_payload(payload: object, *, pr_number: int, head_sha: str) -> dict | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != 1:
        return None
    if payload.get("pr_number") != pr_number:
        return None
    if payload.get("head_sha") != head_sha:
        return None
    if payload.get("verdict") not in VALID_VERDICTS:
        return None
    if not isinstance(payload.get("safe_to_merge"), bool):
        return None
    if not isinstance(payload.get("summary"), str):
        return None
    if not isinstance(payload.get("reviewed_at"), str):
        return None
    return payload


def local_guardian_result(pr_number: int, head_sha: str, *, path: Path = DEFAULT_STATE_FILE) -> dict | None:
    payload = load_guardian_state(path).get("prs", {}).get(str(pr_number))
    return valid_guardian_payload(payload, pr_number=pr_number, head_sha=head_sha)


def find_latest_guardian_result(pr_number: int, head_sha: str, *, path: Path = DEFAULT_STATE_FILE) -> dict | None:
    return local_guardian_result(pr_number, head_sha, path=path)


def parse_all_markdown_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_heading: str | None = None
    preamble: list[str] = []

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if current_heading == "Issue 摘要" and heading in ISSUE_CONTEXT_HEADINGS:
                sections.setdefault(current_heading, []).append(line.rstrip())
                continue
            current_heading = heading
            sections.setdefault(current_heading, [])
            continue
        if current_heading is None:
            preamble.append(line.rstrip())
            continue
        if current_heading:
            sections[current_heading].append(line.rstrip())

    payload = {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}
    preamble_text = "\n".join(preamble).strip()
    if preamble_text:
        payload["__preamble__"] = preamble_text
    return payload


def parse_markdown_sections(body: str) -> dict[str, str]:
    raw_sections = parse_all_markdown_sections(body)
    sections: dict[str, str] = {}
    for heading, content in raw_sections.items():
        key = REVIEW_SECTION_ALIASES.get(heading)
        if key and content:
            sections[key] = content
    return sections


def parse_bullet_kv_section(section: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    current_key: str | None = None
    for raw_line in section.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("- "):
            entry = stripped[2:]
            key_part, _, value_part = entry.partition(":")
            if not _:
                key_part, _, value_part = entry.partition("：")
            normalized_key = key_part.split("（", 1)[0].split("(", 1)[0].strip()
            current_key = normalized_key
            payload[current_key] = value_part.strip()
            continue
        if current_key and stripped and raw_line[:1].isspace():
            payload[current_key] = "\n".join(filter(None, [payload[current_key], stripped])).strip()
    return payload


def parse_integration_check_payload(section: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    current_key: str | None = None
    parsing_closed = False
    for raw_line in section.splitlines():
        stripped = raw_line.strip()
        if parsing_closed:
            continue
        if stripped.startswith("- "):
            entry = stripped[2:]
            key_part, _, value_part = entry.partition(":")
            if not _:
                key_part, _, value_part = entry.partition("：")
            normalized_key = key_part.split("（", 1)[0].split("(", 1)[0].strip()
            if normalized_key not in INTEGRATION_CHECK_CANONICAL_FIELDS:
                current_key = None
                continue
            current_key = normalized_key
            payload[current_key] = value_part.strip()
            continue
        if current_key and stripped and raw_line[:1].isspace():
            payload[current_key] = "\n".join(filter(None, [payload[current_key], stripped])).strip()
            continue
        if stripped:
            current_key = None
            if payload:
                parsing_closed = True
    return payload


def integration_merge_gate_errors(meta: dict) -> list[str]:
    body = str(meta.get("body") or "")
    issue_number, issue_canonical_integration = resolve_issue_canonical_integration(meta)
    raw_sections = parse_all_markdown_sections(body)
    integration_section = raw_sections.get("integration_check", "")
    if not integration_section:
        if issue_canonical_integration:
            issue_label = f"Issue #{issue_number}" if issue_number else "对应 Issue"
            return [f"PR 对应的 {issue_label} 已声明 canonical integration 元数据，PR 描述缺少 canonical `integration_check` 段落。"]
        return []

    payload = parse_integration_check_payload(integration_section)
    integration_touchpoint = payload.get("integration_touchpoint", "").strip().lower() or "none"
    shared_contract_changed = payload.get("shared_contract_changed", "").strip().lower() or "no"
    integration_ref = payload.get("integration_ref", "").strip()
    external_dependency = payload.get("external_dependency", "").strip().lower() or "none"
    joint_acceptance_needed = payload.get("joint_acceptance_needed", "").strip().lower() or "no"
    contract_surface = payload.get("contract_surface", "").strip().lower() or "none"
    integration_status_checked_before_pr = payload.get("integration_status_checked_before_pr", "").strip().lower()
    integration_status_checked_before_merge = payload.get("integration_status_checked_before_merge", "").strip().lower()
    merge_gate = payload.get("merge_gate", "").strip().lower()
    if not merge_gate:
        return ["PR 描述中的 `integration_check.merge_gate` 不能为空。"]
    if merge_gate not in {"local_only", "integration_check_required"}:
        return [f"PR 描述中的 `integration_check.merge_gate` 非法：`{merge_gate}`（仅允许 `local_only` / `integration_check_required`）。"]
    missing_fields = [
        key
        for key in sorted(INTEGRATION_CHECK_CANONICAL_FIELDS)
        if key not in payload or not str(payload.get(key) or "").strip()
    ]
    if missing_fields:
        missing = "、".join(f"`integration_check.{field}`" for field in missing_fields)
        return [f"PR 描述中的 `integration_check` 缺少必填字段：{missing}。"]

    errors: list[str] = []
    issue_missing_fields = [
        field for field in ISSUE_CANONICAL_INTEGRATION_FIELDS if issue_canonical_integration and not str(issue_canonical_integration.get(field) or "").strip()
    ]
    if issue_missing_fields:
        missing = "、".join(f"`{field}`" for field in issue_missing_fields)
        issue_label = f"Issue #{issue_number}" if issue_number else "对应 Issue"
        errors.append(f"{issue_label} 的 canonical integration 元数据缺少字段：{missing}。")
    if integration_touchpoint not in INTEGRATION_TOUCHPOINT_VALUES:
        errors.append(
            "`integration_check.integration_touchpoint` 非法："
            f"`{integration_touchpoint}`（仅允许 `{', '.join(sorted(INTEGRATION_TOUCHPOINT_VALUES))}`）。"
        )
    if external_dependency not in EXTERNAL_DEPENDENCY_VALUES:
        errors.append(
            "`integration_check.external_dependency` 非法："
            f"`{external_dependency}`（仅允许 `{', '.join(sorted(EXTERNAL_DEPENDENCY_VALUES))}`）。"
        )
    if shared_contract_changed not in SHARED_CONTRACT_CHANGED_VALUES:
        errors.append(
            "`integration_check.shared_contract_changed` 非法："
            f"`{shared_contract_changed}`（仅允许 `{', '.join(sorted(SHARED_CONTRACT_CHANGED_VALUES))}`）。"
        )
    if contract_surface not in CONTRACT_SURFACE_VALUES:
        errors.append(
            "`integration_check.contract_surface` 非法："
            f"`{contract_surface}`（仅允许 `{', '.join(sorted(CONTRACT_SURFACE_VALUES))}`）。"
        )
    if joint_acceptance_needed not in JOINT_ACCEPTANCE_VALUES:
        errors.append(
            "`integration_check.joint_acceptance_needed` 非法："
            f"`{joint_acceptance_needed}`（仅允许 `{', '.join(sorted(JOINT_ACCEPTANCE_VALUES))}`）。"
        )
    if integration_status_checked_before_pr not in INTEGRATION_STATUS_VALUES:
        errors.append(
            "`integration_check.integration_status_checked_before_pr` 非法："
            f"`{integration_status_checked_before_pr}`（仅允许 `{', '.join(sorted(INTEGRATION_STATUS_VALUES))}`）。"
        )
    if integration_status_checked_before_merge not in INTEGRATION_STATUS_VALUES:
        errors.append(
            "`integration_check.integration_status_checked_before_merge` 非法："
            f"`{integration_status_checked_before_merge}`（仅允许 `{', '.join(sorted(INTEGRATION_STATUS_VALUES))}`）。"
        )
    integration_active = integration_touchpoint != "none"
    has_shared_contract_change = shared_contract_changed == "yes"
    has_external_dependency = external_dependency != "none"
    joint_acceptance = joint_acceptance_needed == "yes"
    has_contract_surface = contract_surface != "none"

    if integration_active and not integration_ref:
        errors.append("`integration_touchpoint != none` 时，`integration_ref` 不能为空。")
    if integration_active and integration_ref.lower() == "none":
        errors.append("`integration_touchpoint != none` 时，`integration_ref` 不能为 `none`。")
    if integration_active and integration_ref and not integration_ref_is_checkable(integration_ref):
        errors.append("`integration_touchpoint != none` 时，`integration_ref` 必须指向可核查的具体 integration issue / item。")
    if (integration_active or has_shared_contract_change or has_external_dependency or joint_acceptance or has_contract_surface) and merge_gate != "integration_check_required":
        errors.append(
            "`merge_gate=local_only` 与当前 integration 元数据冲突："
            "当 `integration_touchpoint != none`、`shared_contract_changed=yes`、`external_dependency != none`、"
            "`contract_surface != none` 或 `joint_acceptance_needed=yes` 时，"
            "`merge_gate` 必须为 `integration_check_required`。"
        )
    if (has_external_dependency or joint_acceptance or has_contract_surface) and not integration_active:
        errors.append("存在跨仓依赖、联合验收或共享 contract surface 时，`integration_touchpoint` 不能为 `none`。")
    if has_contract_surface and not integration_active:
        errors.append("`contract_surface != none` 时，`integration_touchpoint` 不能为 `none`。")
    if issue_canonical_integration and not issue_missing_fields:
        pr_issue_comparison_values = {
            "integration_touchpoint": integration_touchpoint,
            "shared_contract_changed": shared_contract_changed,
            "integration_ref": integration_ref,
            "external_dependency": external_dependency,
            "merge_gate": merge_gate,
            "contract_surface": contract_surface,
            "joint_acceptance_needed": joint_acceptance_needed,
        }
        for field in ISSUE_CANONICAL_INTEGRATION_FIELDS:
            expected = normalize_issue_canonical_integration_value(field, issue_canonical_integration.get(field, ""))
            actual = normalize_issue_canonical_integration_value(field, pr_issue_comparison_values.get(field, ""))
            if expected != actual:
                issue_label = f"Issue #{issue_number}" if issue_number else "对应 Issue"
                errors.append(f"`integration_check.{field}` 与 {issue_label} 中的 canonical integration 元数据不一致。")
    if merge_gate != "integration_check_required":
        if not integration_ref:
            errors.append("纯本仓库事项也必须显式填写 `integration_ref`；若无 integration 联动，请写 `none`。")
        if not integration_active and integration_ref.lower() != "none":
            errors.append("纯本仓库事项必须显式使用 `integration_ref=none`，不得保留外部 integration 绑定。")
        if integration_ref.lower() != "none" and not integration_ref_is_checkable(integration_ref):
            errors.append("`integration_ref` 必须使用可核查的具体 integration issue / item 引用（例如 `#123`、`owner/repo#123`、issue URL 或带 `itemId=` 的 project item URL）。")
        return errors

    if not integration_active:
        errors.append("`merge_gate=integration_check_required` 时，`integration_touchpoint` 不能为 `none`。")
    if not integration_ref or not integration_ref_is_checkable(integration_ref):
        errors.append("`merge_gate=integration_check_required` 时，`integration_ref` 必须指向具体 integration issue / item。")
    if integration_status_checked_before_pr in INTEGRATION_STATUS_VALUES and integration_status_checked_before_pr != "yes":
        errors.append("`merge_gate=integration_check_required` 时，PR 描述必须记录 `integration_status_checked_before_pr=yes`。")
    if integration_status_checked_before_merge in INTEGRATION_STATUS_VALUES and integration_status_checked_before_merge != "yes":
        errors.append("`merge_gate=integration_check_required` 时，进入 `merge_pr` 前必须把 `integration_status_checked_before_merge` 更新为 `yes`。")
    return errors


def merge_gate_requires_integration_recheck(meta: dict) -> bool:
    body = str(meta.get("body") or "")
    integration_section = parse_all_markdown_sections(body).get("integration_check", "")
    if not integration_section:
        return False
    payload = parse_integration_check_payload(integration_section)
    return payload.get("merge_gate", "").strip().lower() == "integration_check_required"


def set_integration_status_checked_before_merge(body: str, value: str = "yes") -> str:
    pattern = re.compile(
        r"(?im)^(\s*-\s*integration_status_checked_before_merge(?:（[^）]*）|\([^)]*\))?\s*[：:]\s*)(yes|no)\s*$"
    )
    updated_body, count = pattern.subn(rf"\1{value}", body, count=1)
    if count == 0:
        raise SystemExit("PR 描述缺少 `integration_status_checked_before_merge` 字段，无法在 merge 前记录 integration 复核。")
    return updated_body


def integration_status_checked_before_merge_value(body: str) -> str:
    match = re.search(
        r"(?im)^\s*-\s*integration_status_checked_before_merge(?:（[^）]*）|\([^)]*\))?\s*[：:]\s*(yes|no)\s*$",
        body,
    )
    if not match:
        raise SystemExit("PR 描述缺少 `integration_status_checked_before_merge` 字段，无法读取 merge 前 integration 复核状态。")
    return match.group(1).strip().lower()


def record_merge_time_integration_recheck(pr_number: int, meta: dict) -> tuple[dict, str]:
    expected_head_sha = str(meta.get("headRefOid") or "")
    latest = pr_meta(pr_number)
    latest_body = str(latest.get("body") or "")
    original_body = str(meta.get("body") or "")
    if expected_head_sha and latest.get("headRefOid") != expected_head_sha:
        raise SystemExit("merge 前记录 integration 复核时发现 PR HEAD 已变化，拒绝继续。")
    if latest_body != original_body:
        raise SystemExit("merge 前记录 integration 复核时发现 PR 描述已变化，拒绝覆盖并发编辑。")
    previous_value = integration_status_checked_before_merge_value(latest_body)
    updated_body = set_integration_status_checked_before_merge(latest_body, "yes")
    if updated_body != latest_body:
        update_pr_body(pr_number, updated_body)
        try:
            latest = pr_meta(pr_number)
        except (CommandError, SystemExit):
            restore_merge_time_integration_recheck(pr_number, previous_value, current_body=updated_body)
            raise
    return latest, previous_value


def update_pr_body(pr_number: int, body: str) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(body)
        temp_path = Path(handle.name)
    try:
        run(["gh", "pr", "edit", str(pr_number), "--body-file", str(temp_path)], cwd=REPO_ROOT)
    finally:
        temp_path.unlink(missing_ok=True)


def restore_merge_time_integration_recheck(pr_number: int, previous_value: str, *, current_body: str | None = None) -> None:
    latest_body = current_body
    try:
        latest = pr_meta(pr_number)
    except (CommandError, SystemExit):
        if latest_body is None:
            raise
    else:
        latest_body = str(latest.get("body") or "")
    restored_body = set_integration_status_checked_before_merge(latest_body, previous_value)
    if restored_body == latest_body:
        return
    update_pr_body(pr_number, restored_body)


def restore_merge_time_integration_recheck_or_die(pr_number: int, previous_value: str, *, failure_context: str) -> None:
    try:
        restore_merge_time_integration_recheck(pr_number, previous_value)
    except (CommandError, SystemExit) as exc:
        raise SystemExit(f"{failure_context}，且无法恢复 `integration_status_checked_before_merge`：{exc}") from exc


def extract_reviewer_rubric_excerpt(text: str) -> str:
    lines = text.splitlines()
    selected: list[str] = []
    active = False
    allowed = set(REVIEW_GUIDE_HEADINGS)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            active = stripped in allowed
        if active:
            selected.append(line)

    excerpt = "\n".join(selected).strip()
    if excerpt:
        return excerpt
    return "未能从 `code_review.md` 提取 reviewer rubric 节选，请围绕当前 diff、工件完整性与职责边界执行审查。"


def load_reviewer_rubric_excerpt(worktree_dir: Path, base_ref: str) -> str:
    completed = run(
        ["git", "show", f"origin/{base_ref}:{CODE_REVIEW_PATH}"],
        cwd=worktree_dir,
        check=False,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return extract_reviewer_rubric_excerpt(completed.stdout)

    path = worktree_dir / CODE_REVIEW_PATH
    if path.exists():
        return extract_reviewer_rubric_excerpt(path.read_text(encoding="utf-8"))
    return "未找到 `code_review.md`，请按当前变更与最小必要上下文执行 reviewer rubric 审查。"


def extract_named_markdown_sections(body: str, headings: tuple[str, ...]) -> dict[str, str]:
    selected = set(headings)
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            current = heading if heading in selected else None
            if current:
                sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line.rstrip())

    return {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}


def fetch_issue_context(issue_number: int) -> dict[str, object]:
    completed = run(
        ["gh", "issue", "view", str(issue_number), "--json", "number,title,body,url"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "identity": [f"- Issue: #{issue_number}", "- issue 上下文暂不可用"],
            "summary": "issue 内容暂不可用。",
        }

    payload = json.loads(completed.stdout or "{}")
    body = str(payload.get("body") or "").strip()
    canonical_integration = extract_issue_canonical_integration_fields(body)
    identity = [
        f"- Issue: #{payload.get('number', issue_number)}",
        f"- 标题: {payload.get('title', '')}",
        f"- 链接: {payload.get('url', '')}",
    ]
    sections = extract_named_markdown_sections(body, ISSUE_CONTEXT_HEADINGS)
    if not sections:
        sections = extract_issue_summary_sections(body)
    if sections:
        summary_parts: list[str] = []
        for heading in ISSUE_CONTEXT_HEADINGS:
            content = sections.get(heading)
            if not content:
                continue
            summary_parts.extend([f"## {heading}", content, ""])
        summary = "\n".join(summary_parts).strip()
    else:
        summary = body or "无 issue 正文。"
    return {"identity": identity, "summary": summary, "canonical_integration": canonical_integration}


def issue_number_from_meta(meta: dict) -> int | None:
    body_context = parse_item_context_from_body(str(meta.get("body") or ""))
    issue_text = str(body_context.get("issue", "")).strip().lstrip("#")
    if not issue_text:
        return None
    try:
        return int(issue_text)
    except ValueError:
        return None


def normalize_issue_canonical_integration_value(field: str, value: str) -> str:
    raw = str(value or "").strip()
    if field == "integration_ref":
        return raw
    return raw.lower()


def resolve_issue_canonical_integration(meta: dict) -> tuple[int | None, dict[str, str]]:
    cached_issue_number = meta.get("_issue_canonical_issue_number")
    cached_payload = meta.get("_issue_canonical_integration")
    if isinstance(cached_payload, dict):
        return (int(cached_issue_number) if isinstance(cached_issue_number, int) else None), {
            str(key): str(value) for key, value in cached_payload.items()
        }

    issue_number = issue_number_from_meta(meta)
    if issue_number is None:
        meta["_issue_canonical_issue_number"] = None
        meta["_issue_canonical_integration"] = {}
        return None, {}

    completed = run(
        ["gh", "issue", "view", str(issue_number), "--json", "body"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        meta["_issue_canonical_issue_number"] = issue_number
        meta["_issue_canonical_integration"] = {}
        return issue_number, {}

    payload = json.loads(completed.stdout or "{}")
    canonical = extract_issue_canonical_integration_fields(str(payload.get("body") or ""))
    meta["_issue_canonical_issue_number"] = issue_number
    meta["_issue_canonical_integration"] = canonical
    return issue_number, canonical


def fetch_diff_stats(worktree_dir: Path, base_ref: str) -> tuple[list[str], str]:
    changed = run(
        ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
        cwd=worktree_dir,
        check=False,
    )
    if changed.returncode != 0:
        raise SystemExit(changed.stderr.strip() or f"无法比较 origin/{base_ref}...HEAD")
    changed_files = [line.strip() for line in changed.stdout.splitlines() if line.strip()]

    diff_stat = run(
        ["git", "diff", "--stat", "--compact-summary", f"origin/{base_ref}...HEAD"],
        cwd=worktree_dir,
        check=False,
    )
    stat_text = diff_stat.stdout.strip() if diff_stat.returncode == 0 else ""
    return changed_files, stat_text or "无 diff stat。"


def extract_related_links_from_exec_plan(exec_plan_path: Path) -> list[str]:
    links = [exec_plan_path.as_posix()]
    patterns = (
        re.compile(r"^- 关联 spec[:：]\s*`?([^`]+)`?\s*$"),
        re.compile(r"^- 关联 decision[:：]\s*`?([^`]+)`?\s*$"),
    )
    for raw_line in exec_plan_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        for pattern in patterns:
            match = pattern.match(stripped)
            if not match:
                continue
            value = match.group(1).strip()
            if not value or value.startswith("无"):
                continue
            if "/" in value or value.endswith(".md"):
                links.append(value)
    return links


def build_item_context_summary(meta: dict, repo_root: Path) -> tuple[dict[str, str], list[str], list[str]]:
    body_context = parse_item_context_from_body(str(meta.get("body") or ""))
    notes: list[str] = []
    related_paths: list[str] = []

    missing = [field for field in REVIEW_REQUIRED_BODY_FIELDS if not body_context.get(field, "").strip()]
    if missing:
        notes.append(f"PR 正文缺少完整事项上下文字段：{', '.join(missing)}。")
        return body_context, notes, related_paths

    issue_text = body_context.get("issue", "").strip()
    try:
        issue_number = int(issue_text)
    except ValueError:
        notes.append("PR 正文中的 Issue 字段不是合法数字。")
        return body_context, notes, related_paths

    item_key = body_context["item_key"]
    exec_plan = load_item_context_from_exec_plan(repo_root, item_key)
    if exec_plan.get("conflict") == "duplicate_metadata_keys":
        notes.append("active exec-plan 元数据存在重复键，无法确认唯一事项上下文。")
        return body_context, notes, related_paths
    if exec_plan.get("conflict") == "multiple_active_exec_plans":
        notes.append("当前 item_key 命中多个 active exec-plan。")
        return body_context, notes, related_paths
    if not exec_plan:
        notes.append("当前 item_key 未找到 active exec-plan。")
        return body_context, notes, related_paths

    exec_plan_path = Path(exec_plan.get("exec_plan", ""))
    if exec_plan_path:
        if not exec_plan_path.is_absolute():
            exec_plan_path = repo_root / exec_plan_path
        related_paths.extend(extract_related_links_from_exec_plan(exec_plan_path))

    issue_exec_plans = active_exec_plans_for_issue(repo_root, issue_number)
    if len(issue_exec_plans) != 1:
        notes.append(f"当前 Issue 命中的 active exec-plan 数量异常：{len(issue_exec_plans)}。")
        return body_context, notes, related_paths
    if issue_exec_plans[0].get("item_key", "") != item_key:
        notes.append("当前 Issue 的 active exec-plan 与 PR 正文中的 item_key 不一致。")
        return body_context, notes, related_paths

    comparisons = (
        ("issue", "Issue"),
        ("item_key", "item_key"),
        ("item_type", "item_type"),
        ("release", "release"),
        ("sprint", "sprint"),
    )
    mismatched: list[str] = []
    for body_key, metadata_key in comparisons:
        expected = issue_text if body_key == "issue" else body_context[body_key]
        if exec_plan.get(metadata_key, "") != expected:
            mismatched.append(metadata_key)
    if mismatched:
        notes.append(f"PR 正文与 active exec-plan 的字段不一致：{', '.join(mismatched)}。")
        return body_context, notes, related_paths

    merged = dict(body_context)
    merged["exec_plan"] = exec_plan.get("exec_plan", "")
    return merged, notes, related_paths


def build_review_context(meta: dict, worktree_dir: Path) -> dict[str, object]:
    base_ref = meta["baseRefName"]
    raw_sections = parse_all_markdown_sections(str(meta.get("body") or ""))
    sections = parse_markdown_sections(str(meta.get("body") or ""))
    changed_files, diff_stat = fetch_diff_stats(worktree_dir, base_ref)
    item_context, context_notes, related_paths = build_item_context_summary(meta, worktree_dir)
    issue_number = 0
    try:
        issue_number = int(str(item_context.get("issue", "")).strip())
    except ValueError:
        issue_number = 0
    needs_issue_context = bool(issue_number) and not sections.get("issue_summary")
    related_paths.extend(path for path in changed_files if path.startswith("docs/specs/"))
    related_paths.extend(path for path in changed_files if path.startswith("docs/decisions/"))
    related_paths = list(dict.fromkeys(path for path in related_paths if path))

    return {
        "pr_identity": [
            f"- PR: #{meta['number']}",
            f"- 标题: {meta['title']}",
            f"- 链接: {meta['url']}",
            f"- 基线分支: {base_ref}",
            f"- 头部提交: {meta['headRefOid']}",
            f"- 头部分支: {meta.get('headRefName', '')}",
        ],
        "issue_context": fetch_issue_context(issue_number) if issue_number else {"identity": [], "summary": "", "canonical_integration": {}},
        "item_context": item_context,
        "raw_sections": raw_sections,
        "pr_sections": sections,
        "changed_files": changed_files,
        "diff_stat": diff_stat,
        "related_paths": related_paths,
        "context_notes": context_notes,
    }


def render_bullet_dict(payload: dict[str, str]) -> list[str]:
    if not payload:
        return ["- 无可确认的结构化事项上下文"]
    return [f"- {key}: {value}" for key, value in payload.items()]


def render_item_context_supplement(section: str) -> str:
    if not section.strip():
        return ""

    redundant_prefixes = (
        "- Issue:",
        "- item_key:",
        "- item_type:",
        "- release:",
        "- sprint:",
    )
    retained = [
        line
        for line in section.splitlines()
        if line.strip() and not any(line.strip().startswith(prefix) for prefix in redundant_prefixes)
    ]
    if not retained:
        return ""
    return "\n".join(retained)


def append_optional_section(lines: list[str], title: str, content: str) -> None:
    content = content.strip()
    if not content:
        return
    lines.extend(["", title, content])


def render_raw_body_fallback(raw_body: str, raw_sections: dict[str, str]) -> str:
    if not raw_body:
        return ""
    if not raw_sections:
        return raw_body

    preamble = raw_sections.get("__preamble__", "").strip()
    extra_headings = [
        heading
        for heading in raw_sections
        if heading not in REVIEW_SECTION_ALIASES and heading not in RAW_BODY_NOISE_HEADINGS
    ]
    if not extra_headings and not preamble:
        return ""

    blocks: list[str] = []
    if preamble:
        blocks.extend([preamble, ""])
    for heading in extra_headings:
        if heading == "__preamble__":
            continue
        content = raw_sections.get(heading, "")
        if not content:
            continue
        blocks.extend([f"## {heading}", content, ""])
    return "\n".join(blocks).strip()


def build_prompt(meta: dict, worktree_dir: Path) -> str:
    base_ref = meta["baseRefName"]
    context = build_review_context(meta, worktree_dir)
    rubric_excerpt = load_reviewer_rubric_excerpt(worktree_dir, base_ref)
    sections = context["pr_sections"]
    raw_body = str(meta.get("body") or "").strip()
    summary_fallback = "无结构化 PR 摘要。"
    raw_body_fallback = render_raw_body_fallback(raw_body, context["raw_sections"])

    lines = [
        "你是 Syvert PR guardian reviewer。",
        f"请在当前工作树中审查 `origin/{base_ref}` 与当前 HEAD 的差异。",
        "优先基于 diff 与必要文件做静态审查，仅在存在明确阻断线索时再运行最小必要命令。",
        "不要运行完整测试套件或与当前变更无关的重型验证。",
        "",
        "执行约束：",
        *[f"- {rule}" for rule in REVIEW_EXECUTION_RULES],
        "",
        "Reviewer Rubric 节选（来自 `code_review.md`）：",
        rubric_excerpt,
        "",
        "PR 基本信息：",
        *context["pr_identity"],
    ]

    issue_summary = sections.get("issue_summary", "").strip()
    item_context_supplement = render_item_context_supplement(sections.get("item_context", ""))
    if context["issue_context"]["identity"] or context["issue_context"]["summary"] or issue_summary:
        lines.extend(
            [
                "",
                "Issue 摘要：",
                *(context["issue_context"]["identity"] or []),
                issue_summary or str(context["issue_context"]["summary"]),
            ]
        )

    lines.extend(
        [
            "",
            "结构化事项上下文：",
            *render_bullet_dict(context["item_context"]),
            "",
            "PR 摘要：",
            sections.get("summary", summary_fallback),
            "",
            "变更文件：",
            format_changed_files(context["changed_files"]),
            "",
            "Diff Stat：",
            str(context["diff_stat"]),
        ]
    )

    append_optional_section(lines, "PR 关联事项补充：", item_context_supplement)
    lines.extend(["", "风险摘要：", sections.get("risk", "未提供结构化风险摘要。")])
    lines.extend(["", "验证摘要：", sections.get("validation", "未提供结构化验证摘要。")])
    lines.extend(["", "回滚摘要：", sections.get("rollback", "未提供结构化回滚摘要。")])
    if context["related_paths"]:
        lines.extend(["", "相关工件路径：", *[f"- `{path}`" for path in context["related_paths"]]])
    else:
        lines.extend(["", "相关工件路径：", "- 未直接定位到相关 spec / exec-plan / decision 工件。"])
    if context["context_notes"]:
        lines.extend(["", "Context Notes：", *[f"- {note}" for note in context["context_notes"]]])

    if raw_body_fallback:
        lines.extend(["", "PR 正文 fallback：", raw_body_fallback])

    return "\n".join(lines).rstrip() + "\n"


def run_codex_review(worktree_dir: Path, prompt: str, result_path: Path) -> dict:
    scratch_dir = worktree_dir / ".codex-tmp"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    scratch_dir_text = str(scratch_dir)
    env["TMPDIR"] = scratch_dir_text
    env["TMP"] = scratch_dir_text
    env["TEMP"] = scratch_dir_text
    timeout_seconds = codex_review_timeout_seconds()
    try:
        completed = subprocess.run(
            [
                "codex",
                "exec",
                "-C",
                str(worktree_dir),
                "-s",
                "workspace-write",
                "--output-schema",
                str(SCHEMA_PATH),
                "-o",
                str(result_path),
                "-",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        timeout_hint = exc.timeout if exc.timeout is not None else timeout_seconds
        raise SystemExit(f"Codex 审查超时（>{timeout_hint} 秒），未产出 guardian verdict。") from exc
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or "Codex 审查失败。")
    if result_path.exists():
        return json.loads(result_path.read_text(encoding="utf-8"))
    if completed.stdout.strip():
        return json.loads(completed.stdout)
    raise SystemExit("Codex 审查未产出结构化结果。")


def severity_label(severity: str) -> str:
    mapping = {
        "critical": "P0 / critical",
        "high": "P1 / high",
        "medium": "P2 / medium",
        "low": "P3 / low",
    }
    return mapping.get(severity, severity)


def build_review_markdown(result: dict) -> str:
    lines = [
        "## PR Review 结论",
        "",
        f"**结论**: {result['verdict']}",
        "",
        f"**允许合并**: {bool_text(result['safe_to_merge'])}",
        "",
        f"**摘要**: {result['summary']}",
        "",
        "### 需要关注的问题",
        "",
    ]

    findings = result.get("findings", [])
    if not findings:
        lines.append("- 未发现新的阻断性问题。")
    else:
        for index, finding in enumerate(findings, start=1):
            location = finding["code_location"]
            line_range = location["line_range"]
            lines.extend(
                [
                    f"{index}. **[{severity_label(finding['severity'])}] {finding['title']}**",
                    f"文件: `{location['absolute_file_path']}` (L{line_range['start']}-L{line_range['end']})",
                    f"说明: {finding['details']}",
                    "",
                ]
            )

    lines.extend(["### 合并前动作", ""])
    actions = result.get("required_actions", [])
    if not actions:
        lines.append("- 无。")
    else:
        lines.extend([f"- {action}" for action in actions])
    return "\n".join(lines).rstrip() + "\n"


def post_review(pr_number: int, meta: dict, result: dict) -> None:
    reviewer = run(["gh", "api", "user", "--jq", ".login"], cwd=REPO_ROOT).stdout.strip()
    author = (meta.get("author") or {}).get("login", "")
    markdown = build_review_markdown(result)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(markdown)
        body_file = Path(handle.name)

    try:
        if reviewer == author:
            run(["gh", "pr", "review", str(pr_number), "--comment", "--body-file", str(body_file)], cwd=REPO_ROOT)
            return

        action = "--approve" if result["verdict"] == "APPROVE" else "--request-changes"
        run(["gh", "pr", "review", str(pr_number), action, "--body-file", str(body_file)], cwd=REPO_ROOT)
    finally:
        if body_file.exists():
            os.unlink(body_file)


def all_checks_pass(pr_number: int) -> bool:
    completed = run(
        ["gh", "pr", "checks", str(pr_number), "--json", "name,bucket,state,link"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or "无法读取 GitHub checks。")
    checks = json.loads(completed.stdout or "[]")
    if not checks:
        return False
    return all(item.get("bucket") == "pass" for item in checks)


def review_once(pr_number: int, *, post: bool, json_output: str | None) -> tuple[dict, dict]:
    require_auth()
    meta = pr_meta(pr_number)
    temp_dir, worktree_dir = prepare_worktree(pr_number, meta)
    try:
        result_path = temp_dir / "review.json"
        result = run_codex_review(worktree_dir, build_prompt(meta, worktree_dir), result_path)
        payload = build_guardian_payload(meta, result)
        save_guardian_result(pr_number, payload)
        markdown = build_review_markdown(result)
        if json_output:
            Path(json_output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if post:
            post_review(pr_number, meta, result)
        print(markdown)
        return meta, result
    finally:
        cleanup(temp_dir)


def merge_if_safe(
    pr_number: int,
    *,
    post: bool,
    delete_branch: bool,
    refresh_review: bool,
    confirm_integration_recheck: bool = False,
) -> int:
    require_auth()
    current = pr_meta(pr_number)
    original_body = str(current.get("body") or "")
    payload = None if refresh_review else find_latest_guardian_result(pr_number, current["headRefOid"])

    if payload:
        print(f"复用已有 guardian verdict: {payload['verdict']} @ {payload['head_sha']}")
        result = {
            "verdict": payload["verdict"],
            "safe_to_merge": payload["safe_to_merge"],
            "summary": payload.get("summary", ""),
        }
        reviewed_head_sha = payload["head_sha"]
    else:
        meta, result = review_once(pr_number, post=post, json_output=None)
        reviewed_head_sha = meta["headRefOid"]
        current = pr_meta(pr_number)

    if result["verdict"] != "APPROVE":
        raise SystemExit("guardian 未给出 APPROVE，拒绝合并。")
    if not result["safe_to_merge"]:
        raise SystemExit("guardian 认为当前 PR 不安全，拒绝合并。")

    if current["isDraft"]:
        raise SystemExit("PR 仍为 Draft，拒绝合并。")
    if current["headRefOid"] != reviewed_head_sha:
        raise SystemExit("审查后 PR HEAD 已变化，拒绝合并。")
    if not all_checks_pass(pr_number):
        raise SystemExit("GitHub checks 未全部通过，拒绝合并。")
    merge_time_integration_recheck_recorded = False
    previous_merge_recheck_value: str | None = None
    if merge_gate_requires_integration_recheck(current):
        if not confirm_integration_recheck:
            raise SystemExit(
                "`merge_gate=integration_check_required` 时，进入 `merge_pr` 必须显式传入 "
                "`--confirm-integration-recheck`，并在该步骤记录 merge 前 integration 复核。"
            )
        preview_current = dict(current)
        preview_current["body"] = set_integration_status_checked_before_merge(str(current.get("body") or ""), "yes")
        preview_errors = integration_merge_gate_errors(preview_current)
        if preview_errors:
            detail = "\n".join(f"- {item}" for item in preview_errors)
            raise SystemExit(f"integration merge gate 未满足，拒绝合并：\n{detail}")
        current, previous_merge_recheck_value = record_merge_time_integration_recheck(pr_number, current)
        merge_time_integration_recheck_recorded = True
        if current["headRefOid"] != reviewed_head_sha:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="merge 前 integration 复核后 PR HEAD 已变化",
            )
            raise SystemExit("merge 前 integration 复核后 PR HEAD 已变化，拒绝合并。")
    integration_errors = integration_merge_gate_errors(current)
    if integration_errors:
        if merge_time_integration_recheck_recorded:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="integration merge gate 校验失败后无法保持 PR 元数据一致",
            )
        detail = "\n".join(f"- {item}" for item in integration_errors)
        raise SystemExit(f"integration merge gate 未满足，拒绝合并：\n{detail}")

    command = [
        "gh",
        "pr",
        "merge",
        str(pr_number),
        "--squash",
        "--match-head-commit",
        current["headRefOid"],
    ]
    if delete_branch:
        command.append("--delete-branch")
    try:
        run(command, cwd=REPO_ROOT)
    except CommandError:
        if merge_time_integration_recheck_recorded:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="`gh pr merge` 失败",
            )
        raise
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "review":
        review_once(args.pr_number, post=args.post_review, json_output=args.json_output)
        return 0
    return merge_if_safe(
        args.pr_number,
        post=args.post_review,
        delete_branch=args.delete_branch,
        refresh_review=args.refresh_review,
        confirm_integration_recheck=args.confirm_integration_recheck,
    )


if __name__ == "__main__":
    raise SystemExit(main())
