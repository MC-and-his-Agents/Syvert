#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import hashlib
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
    default_github_repo,
    dump_json,
    ensure_parent,
    format_changed_files,
    load_json,
    require_cli,
    run,
)
from scripts.integration_contract import (
    ISSUE_SCOPE_FIELDS,
    PR_SCOPE_FIELDS,
    build_review_packet,
    extract_issue_canonical_integration_fields,
    fetch_integration_ref_live_state,
    field_choices,
    merge_gate_requires_integration_recheck as merge_gate_requires_integration_recheck_payload,
    parse_integration_check_payload,
    parse_pr_integration_check,
    render_review_packet_lines,
    validate_integration_ref_live_state,
    validate_issue_fetch,
    validate_pr_integration_contract,
)
from scripts.item_context import active_exec_plans_for_issue, load_item_context_from_exec_plan, parse_item_context_from_body
from scripts.open_pr import extract_issue_summary_sections
from scripts.policy.policy import classify_paths
from scripts.state_paths import guardian_legacy_state_path, guardian_state_path


SCHEMA_PATH = REPO_ROOT / "scripts" / "policy" / "pr_review_result_schema.json"
CODE_REVIEW_PATH = "code_review.md"
DEFAULT_STATE_FILE = guardian_state_path()
VALID_VERDICTS = {"APPROVE", "REQUEST_CHANGES"}
INTEGRATION_STATUS_VALUES = set(field_choices("integration_status_checked_before_pr"))
REVIEW_REQUIRED_BODY_FIELDS = ("issue", "item_key", "item_type", "release", "sprint")
REVIEW_EXECUTION_RULES = (
    "工件完整性只用于确认输入是否足够，不要把 checks、Draft 状态或 merge 动作当成 reviewer 结论来源。",
    "若缺少必要工件或验证证据，应明确指出阻断项；merge gate、head 绑定与 squash merge 安全性由 guardian gate 入口单独消费。",
)
METADATA_ONLY_CLOSEOUT_DOC_PREFIXES = (
    "docs/exec-plans/",
    "docs/releases/",
    "docs/sprints/",
)
METADATA_ONLY_CLOSEOUT_MARKERS = (
    "metadata-only closeout follow-up",
    "metadata-only review sync",
)
REVIEW_SECTION_ALIASES = {
    "摘要": "summary",
    "Issue 摘要": "issue_summary",
    "关联事项": "item_context",
    "Review Artifacts": "review_artifacts",
    "风险": "risk",
    "风险级别": "risk",
    "验证": "validation",
    "回滚": "rollback",
}
REVIEW_ARTIFACT_REQUIRED_FIELDS = (
    "Active exec-plan",
    "Governing spec / bootstrap contract",
    "Review artifact",
    "Validation evidence",
)
REVIEW_ARTIFACT_EMPTY_VALUES = {
    "",
    "tbd",
    "todo",
    "n/a",
    "na",
    "none",
    "无",
    "待补充",
    "未填写",
    "未定位",
    "未定位到 active exec-plan",
    "未定位到 governing artifact",
}
RAW_BODY_NOISE_HEADINGS = {"变更文件", "检查清单"}
REVIEW_GUIDE_HEADINGS = (
    "## 工件完整性检查",
    "## Review Rubric",
    "## 事项分级视角",
    "## 职责边界说明",
)
ISSUE_CONTEXT_HEADINGS = ("Goal", "Scope", "Required Outcomes", "Acceptance", "Acceptance Criteria", "Out of Scope", "Dependency")
REVIEW_ARTIFACT_REQUIRED_TEMPLATE_SECTIONS = ("summary", "item_context", "risk", "validation", "rollback")
REVIEW_ARTIFACT_REQUIRED_AFTER = datetime(2026, 4, 27, tzinfo=timezone.utc)
REVIEW_ARTIFACT_NEW_TEMPLATE_MARKERS = ("## Loom Runtime Locator",)
REVIEW_ARTIFACT_PLACEHOLDER_MARKERS = (
    "由受控流程继续补充",
    "见 ## 验证",
    "见 `## 验证`",
)
VALIDATION_COMMAND_PREFIXES = (
    "python",
    "python3",
    "python3.11",
    "npm",
    "make",
    "pytest",
    "env ",
    "gh ",
)


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
            "number,title,body,url,isDraft,baseRefName,headRefName,headRefOid,author,createdAt",
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


def guardian_body_fingerprint(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def build_guardian_payload(meta: dict, result: dict) -> dict:
    return {
        "schema_version": 2,
        "pr_number": meta["number"],
        "head_sha": meta["headRefOid"],
        "body_fingerprint": guardian_body_fingerprint(str(meta.get("body") or "")),
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


def valid_guardian_payload(
    payload: object,
    *,
    pr_number: int,
    head_sha: str,
    body: str | None = None,
    require_body_bound: bool = False,
) -> dict | None:
    if not isinstance(payload, dict):
        return None
    schema_version = payload.get("schema_version")
    if schema_version not in {1, 2}:
        return None
    if payload.get("pr_number") != pr_number:
        return None
    if payload.get("head_sha") != head_sha:
        return None
    body_fingerprint = payload.get("body_fingerprint")
    if body is not None:
        if schema_version == 2:
            if body_fingerprint != guardian_body_fingerprint(body):
                return None
        elif require_body_bound:
            return None
    elif schema_version == 2 and not isinstance(body_fingerprint, str):
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


def local_guardian_result(
    pr_number: int,
    head_sha: str,
    *,
    body: str | None = None,
    require_body_bound: bool = False,
    path: Path = DEFAULT_STATE_FILE,
) -> dict | None:
    payload = load_guardian_state(path).get("prs", {}).get(str(pr_number))
    return valid_guardian_payload(
        payload,
        pr_number=pr_number,
        head_sha=head_sha,
        body=body,
        require_body_bound=require_body_bound,
    )


def find_latest_guardian_result(
    pr_number: int,
    head_sha: str,
    *,
    body: str | None = None,
    require_body_bound: bool = False,
    path: Path = DEFAULT_STATE_FILE,
) -> dict | None:
    return local_guardian_result(
        pr_number,
        head_sha,
        body=body,
        require_body_bound=require_body_bound,
        path=path,
    )


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


def review_artifact_locator_candidates(value: str) -> list[str]:
    return [part.strip().strip("`").strip() for part in value.split(",") if part.strip()]


def review_artifact_locator_errors(value: str, *, field: str, require_repo_path: bool, repo_root: Path) -> list[str]:
    candidates = review_artifact_locator_candidates(value)
    if not candidates:
        return [f"`## Review Artifacts` 中 `{field}` 必须指向具体 artifact locator。"]
    errors: list[str] = []
    for candidate in candidates:
        parts = Path(candidate).parts
        if Path(candidate).is_absolute() or ".." in parts:
            errors.append(f"`## Review Artifacts` 中 `{field}` 包含非法 artifact locator：`{candidate}`。")
            continue
        if require_repo_path and "/" not in candidate:
            errors.append(f"`## Review Artifacts` 中 `{field}` 必须指向仓库内具体路径：`{candidate}`。")
            continue
        if not any(token in candidate for token in ("/", ".md", ".json", ".yml", ".yaml")):
            errors.append(f"`## Review Artifacts` 中 `{field}` 必须指向具体 artifact locator：`{candidate}`。")
            continue
        if not (repo_root / candidate).exists():
            errors.append(f"`## Review Artifacts` 中 `{field}` 指向不存在的 artifact：`{candidate}`。")
    return errors


def review_artifact_locators(meta: dict, *, repo_root: Path = REPO_ROOT) -> list[str]:
    sections = parse_markdown_sections(str(meta.get("body") or ""))
    payload = parse_bullet_kv_section(sections.get("review_artifacts", ""))
    locators: list[str] = []
    for field in ("Active exec-plan", "Governing spec / bootstrap contract", "Review artifact", "Validation evidence"):
        for candidate in review_artifact_locator_candidates(str(payload.get(field) or "")):
            path = Path(candidate)
            if path.is_absolute() or ".." in path.parts:
                continue
            if (repo_root / candidate).exists():
                locators.append(candidate)
    return list(dict.fromkeys(locators))


def validation_section_has_executed_evidence(section: str) -> bool:
    for raw_line in section.splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:].strip().strip("`")
        lowered = value.lower()
        if any(lowered.startswith(prefix) for prefix in VALIDATION_COMMAND_PREFIXES):
            return True
    return False


def validation_evidence_errors(value: str, *, sections: dict[str, str], repo_root: Path) -> list[str]:
    normalized = value.strip().strip("`").strip()
    if any(marker in normalized for marker in REVIEW_ARTIFACT_PLACEHOLDER_MARKERS):
        if not validation_section_has_executed_evidence(sections.get("validation", "")):
            return ["`## Review Artifacts` 中 `Validation evidence` 必须指向已执行验证命令或存在的验证 artifact，不能只使用模板占位说明。"]
    candidates = review_artifact_locator_candidates(value)
    concrete = False
    errors: list[str] = []
    for candidate in candidates:
        if candidate in {"## 验证", "验证"}:
            if validation_section_has_executed_evidence(sections.get("validation", "")):
                concrete = True
            continue
        lowered = candidate.lower()
        if any(lowered.startswith(prefix) for prefix in VALIDATION_COMMAND_PREFIXES):
            concrete = True
            continue
        path = Path(candidate)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"`## Review Artifacts` 中 `Validation evidence` 包含非法 artifact locator：`{candidate}`。")
            continue
        if any(token in candidate for token in ("/", ".md", ".json", ".yml", ".yaml")):
            if (repo_root / candidate).exists():
                concrete = True
            else:
                errors.append(f"`## Review Artifacts` 中 `Validation evidence` 指向不存在的 artifact：`{candidate}`。")
    if not concrete and not errors:
        errors.append("`## Review Artifacts` 中 `Validation evidence` 必须指向已执行验证命令或存在的验证 artifact。")
    return errors


def parse_github_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def review_artifacts_required(meta: dict, sections: dict[str, str]) -> bool:
    body = str(meta.get("body") or "")
    if any(marker in body for marker in REVIEW_ARTIFACT_NEW_TEMPLATE_MARKERS):
        return True
    created_at = parse_github_timestamp(meta.get("createdAt"))
    if created_at is None:
        return True
    return created_at >= REVIEW_ARTIFACT_REQUIRED_AFTER


def review_artifact_gate_applies(meta: dict) -> bool:
    body = str(meta.get("body") or "")
    sections = parse_markdown_sections(str(meta.get("body") or ""))
    if (
        "createdAt" not in meta
        and not sections.get("review_artifacts", "").strip()
        and not any(marker in body for marker in REVIEW_ARTIFACT_NEW_TEMPLATE_MARKERS)
        and not any(sections.get(name, "").strip() for name in REVIEW_ARTIFACT_REQUIRED_TEMPLATE_SECTIONS)
    ):
        return False
    return bool(sections.get("review_artifacts", "").strip()) or review_artifacts_required(meta, sections)


def review_artifact_errors(meta: dict, *, repo_root: Path = REPO_ROOT) -> list[str]:
    sections = parse_markdown_sections(str(meta.get("body") or ""))
    section = sections.get("review_artifacts", "")
    if not section:
        if review_artifacts_required(meta, sections):
            return ["PR 描述缺少 `## Review Artifacts` 段落。"]
        return []
    payload = parse_bullet_kv_section(section)
    missing = [field for field in REVIEW_ARTIFACT_REQUIRED_FIELDS if field not in payload]
    if missing:
        joined = "、".join(f"`{field}`" for field in missing)
        return [f"`## Review Artifacts` 缺少必填字段：{joined}。"]

    errors: list[str] = []
    for field in REVIEW_ARTIFACT_REQUIRED_FIELDS:
        value = str(payload.get(field) or "").strip().strip("`").strip()
        if value.casefold() in REVIEW_ARTIFACT_EMPTY_VALUES:
            errors.append(f"`## Review Artifacts` 中 `{field}` 不能为空。")
            continue
        if field == "Active exec-plan":
            errors.extend(review_artifact_locator_errors(value, field=field, require_repo_path=True, repo_root=repo_root))
        if field == "Governing spec / bootstrap contract":
            errors.extend(review_artifact_locator_errors(value, field=field, require_repo_path=True, repo_root=repo_root))
        if field == "Review artifact":
            errors.extend(review_artifact_locator_errors(value, field=field, require_repo_path=False, repo_root=repo_root))
        if field == "Validation evidence":
            errors.extend(validation_evidence_errors(value, sections=sections, repo_root=repo_root))
    return errors


def integration_merge_gate_errors(meta: dict, *, require_live_state: bool = False) -> list[str]:
    body = str(meta.get("body") or "")
    issue_number, issue_canonical_integration = resolve_issue_canonical_integration(meta)
    issue_canonical_error = str(meta.get("_issue_canonical_integration_error") or "").strip()
    integration_payload = parse_pr_integration_check(body)
    if issue_canonical_error:
        return [issue_canonical_error]
    errors = validate_pr_integration_contract(
        integration_payload,
        issue_number=issue_number,
        issue_canonical=issue_canonical_integration,
        issue_error=issue_canonical_error,
        require_merge_time_recheck=True,
    )
    if errors:
        return errors
    if not require_live_state or not merge_gate_requires_integration_recheck_payload(integration_payload):
        return []
    integration_ref = str(integration_payload.get("integration_ref") or "").strip()
    live_state = fetch_integration_ref_live_state(integration_ref)
    meta["_integration_ref_live_state"] = live_state
    return validate_integration_ref_live_state(
        integration_payload,
        live_state,
        current_repo_slug=default_github_repo(),
    )


def merge_gate_requires_integration_recheck(meta: dict) -> bool:
    payload = parse_pr_integration_check(str(meta.get("body") or ""))
    return bool(payload) and merge_gate_requires_integration_recheck_payload(payload)


def integration_check_section_span(body: str) -> tuple[int, int]:
    heading_pattern = re.compile(r"(?im)^#{2,6}\s+(.+?)\s*$")
    matches = list(heading_pattern.finditer(body))
    for index, match in enumerate(matches):
        if match.group(1).strip().casefold() != "integration_check":
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        return start, end
    raise SystemExit("PR 描述缺少 `## integration_check` 段落，无法在 merge 前记录 integration 复核。")


def integration_check_section_text(body: str) -> str:
    start, end = integration_check_section_span(body)
    return body[start:end]


def set_integration_status_checked_before_merge(body: str, value: str = "yes") -> str:
    pattern = re.compile(
        r"(?im)^(\s*-\s*integration_status_checked_before_merge(?:（[^）]*）|\([^)]*\))?\s*[：:]\s*)(yes|no)\s*$"
    )
    section_start, section_end = integration_check_section_span(body)
    section_body = body[section_start:section_end]
    updated_section, count = pattern.subn(rf"\1{value}", section_body, count=1)
    if count == 0:
        raise SystemExit("PR 描述缺少 `integration_status_checked_before_merge` 字段，无法在 merge 前记录 integration 复核。")
    return body[:section_start] + updated_section + body[section_end:]


def integration_status_checked_before_merge_value(body: str) -> str:
    section_body = integration_check_section_text(body)
    payload = parse_integration_check_payload(section_body)
    value = str(payload.get("integration_status_checked_before_merge") or "").strip().lower()
    if not value:
        raise SystemExit("PR 描述缺少 `integration_status_checked_before_merge` 字段，无法读取 merge 前 integration 复核状态。")
    if value not in INTEGRATION_STATUS_VALUES:
        allowed = " / ".join(sorted(INTEGRATION_STATUS_VALUES))
        raise SystemExit(
            "PR 描述中的 `integration_status_checked_before_merge` 非法："
            f"`{value}`（仅允许 `{allowed}`）。"
        )
    return value


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
            try:
                update_pr_body(pr_number, latest_body)
            except (CommandError, SystemExit) as restore_exc:
                raise SystemExit(
                    "merge 前写入 `integration_status_checked_before_merge=yes` 后，无法重新读取最新 PR 描述，"
                    f"且恢复旧值失败：{restore_exc}"
                ) from restore_exc
            raise SystemExit(
                "merge 前写入 `integration_status_checked_before_merge=yes` 后，无法重新读取最新 PR 描述，"
                "已回滚到旧值，请人工复核后重试。"
            )
    return latest, previous_value


def update_pr_body(pr_number: int, body: str) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(body)
        temp_path = Path(handle.name)
    try:
        run(["gh", "pr", "edit", str(pr_number), "--body-file", str(temp_path)], cwd=REPO_ROOT)
    finally:
        temp_path.unlink(missing_ok=True)


def restore_merge_time_integration_recheck(pr_number: int, previous_value: str) -> None:
    latest = pr_meta(pr_number)
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
        ["gh", "issue", "view", str(issue_number), "--repo", default_github_repo(), "--json", "number,title,body,url"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "identity": [f"- Issue: #{issue_number}", "- issue 上下文暂不可用"],
            "summary": "issue 内容暂不可用。",
            "canonical_integration": {},
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


def resolve_issue_canonical_integration(meta: dict) -> tuple[int | None, dict[str, str]]:
    cached_issue_number = meta.get("_issue_canonical_issue_number")
    cached_payload = meta.get("_issue_canonical_integration")
    cached_error = meta.get("_issue_canonical_integration_error")
    if isinstance(cached_payload, dict):
        if cached_error is not None:
            meta["_issue_canonical_integration_error"] = str(cached_error)
        return (int(cached_issue_number) if isinstance(cached_issue_number, int) else None), {
            str(key): str(value) for key, value in cached_payload.items()
        }

    issue_number = issue_number_from_meta(meta)
    if issue_number is None:
        meta["_issue_canonical_issue_number"] = None
        meta["_issue_canonical_integration"] = {}
        meta["_issue_canonical_integration_error"] = None
        return None, {}

    resolution = validate_issue_fetch(issue_number, allow_missing_payload=True)
    canonical = resolution.canonical
    meta["_issue_canonical_issue_number"] = issue_number
    meta["_issue_canonical_integration"] = canonical
    meta["_issue_canonical_integration_error"] = resolution.error
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
    body = str(meta.get("body") or "")
    raw_sections = parse_all_markdown_sections(str(meta.get("body") or ""))
    sections = parse_markdown_sections(str(meta.get("body") or ""))
    changed_files, diff_stat = fetch_diff_stats(worktree_dir, base_ref)
    item_context, context_notes, related_paths = build_item_context_summary(meta, worktree_dir)
    issue_number, issue_canonical = resolve_issue_canonical_integration(meta)
    issue_error = str(meta.get("_issue_canonical_integration_error") or "")
    needs_issue_context = bool(issue_number) and not sections.get("issue_summary")
    related_paths.extend(review_artifact_locators(meta, repo_root=worktree_dir))
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
        "issue_context": fetch_issue_context(issue_number) if needs_issue_context else {"identity": [], "summary": "", "canonical_integration": {}},
        "item_context": item_context,
        "raw_sections": raw_sections,
        "pr_sections": sections,
        "integration_review_packet": build_review_packet(
            body,
            issue_number=issue_number,
            issue_canonical=issue_canonical,
            issue_error=issue_error,
        ),
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


def resolve_exec_plan_path(repo_root: Path, item_context: dict[str, str]) -> Path | None:
    path_text = str(item_context.get("exec_plan", "")).strip()
    if not path_text:
        return None
    exec_plan_path = Path(path_text)
    if not exec_plan_path.is_absolute():
        exec_plan_path = repo_root / exec_plan_path
    return exec_plan_path


def exec_plan_declares_metadata_only_closeout_follow_up(repo_root: Path, item_context: dict[str, str]) -> bool:
    exec_plan_path = resolve_exec_plan_path(repo_root, item_context)
    if exec_plan_path is None or not exec_plan_path.exists():
        return False
    normalized = exec_plan_path.read_text(encoding="utf-8").lower()
    return any(marker in normalized for marker in METADATA_ONLY_CLOSEOUT_MARKERS)


def is_metadata_only_closeout_follow_up(repo_root: Path, item_context: dict[str, str], changed_files: list[str]) -> bool:
    item_key = str(item_context.get("item_key", "")).strip().lower()
    if "closeout" not in item_key or not changed_files:
        return False
    categories = {item.category for item in classify_paths(changed_files)}
    if categories != {"docs"}:
        return False
    if not all(path.startswith(METADATA_ONLY_CLOSEOUT_DOC_PREFIXES) for path in changed_files):
        return False
    return exec_plan_declares_metadata_only_closeout_follow_up(repo_root, item_context)


def head_checkpoint_contract_rules(repo_root: Path, context: dict[str, object]) -> list[str]:
    rules = [
        "当前 live review head 以 PR 基本信息中的 `头部提交` 为准，并由 guardian state / merge gate 绑定；不要要求 active exec-plan 追写该值。",
        "active exec-plan 只承载最近一次 checkpoint / resume truth；若当前 diff 仅补 review / merge gate / closeout metadata，不要把 metadata-only head 视为新的 checkpoint。",
    ]
    item_context = context.get("item_context")
    changed_files = context.get("changed_files")
    if (
        isinstance(item_context, dict)
        and isinstance(changed_files, list)
        and is_metadata_only_closeout_follow_up(repo_root, item_context, changed_files)
    ):
        rules.append(
            "当前 diff 命中 metadata-only closeout follow-up：请核对 checkpoint 语义、追溯关系与门禁证据是否自洽；不要因 exec-plan 未把静态 SHA 追到当前 HEAD 而单独给出阻断。"
        )
    return rules


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
        "Head / Checkpoint Contract：",
        *[f"- {rule}" for rule in head_checkpoint_contract_rules(worktree_dir, context)],
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
    integration_packet = context.get("integration_review_packet") or {}
    if integration_packet:
        lines.extend(["", "Integration Review Packet：", *render_review_packet_lines(integration_packet)])

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
        if review_artifact_gate_applies(meta):
            review_artifact_validation_errors = review_artifact_errors(meta, repo_root=worktree_dir)
            if review_artifact_validation_errors:
                detail = "\n".join(f"- {item}" for item in review_artifact_validation_errors)
                raise SystemExit(f"Review Artifacts 门禁未满足，拒绝进入 guardian review：\n{detail}")
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
    reviewed_body = original_body
    payload = None if refresh_review else find_latest_guardian_result(
        pr_number,
        current["headRefOid"],
        body=original_body,
        require_body_bound=True,
    )

    if payload:
        print(f"复用已有 guardian verdict: {payload['verdict']} @ {payload['head_sha']}")
        result = {
            "verdict": payload["verdict"],
            "safe_to_merge": payload["safe_to_merge"],
            "summary": payload.get("summary", ""),
        }
        reviewed_head_sha = payload["head_sha"]
        guardian_verdict_body_bound = payload.get("schema_version") == 2
    else:
        meta, result = review_once(pr_number, post=post, json_output=None)
        reviewed_head_sha = meta["headRefOid"]
        reviewed_body = str(meta.get("body") or "")
        current = pr_meta(pr_number)
        guardian_verdict_body_bound = True

    if result["verdict"] != "APPROVE":
        raise SystemExit("guardian 未给出 APPROVE，拒绝合并。")
    if not result["safe_to_merge"]:
        raise SystemExit("guardian 认为当前 PR 不安全，拒绝合并。")

    if current["isDraft"]:
        raise SystemExit("PR 仍为 Draft，拒绝合并。")
    if current["headRefOid"] != reviewed_head_sha:
        raise SystemExit("审查后 PR HEAD 已变化，拒绝合并。")
    if guardian_verdict_body_bound and str(current.get("body") or "") != reviewed_body:
        raise SystemExit("guardian 审查后 PR 描述已变化，拒绝合并。")
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
        preview_errors = integration_merge_gate_errors(preview_current, require_live_state=True)
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
    if merge_time_integration_recheck_recorded and guardian_verdict_body_bound:
        try:
            refreshed_meta, refreshed_result = review_once(pr_number, post=post, json_output=None)
        except (CommandError, SystemExit) as exc:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="merge 前重跑 guardian 失败",
            )
            raise SystemExit(f"merge 前重跑 guardian 失败，拒绝合并：{exc}") from exc
        if refreshed_result["verdict"] != "APPROVE":
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="merge 前重跑 guardian 未通过",
            )
            raise SystemExit("merge 前重跑 guardian 未给出 APPROVE，拒绝合并。")
        if not refreshed_result["safe_to_merge"]:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="merge 前重跑 guardian 判定不安全",
            )
            raise SystemExit("merge 前重跑 guardian 判定不安全，拒绝合并。")
        reviewed_head_sha = refreshed_meta["headRefOid"]
        current = pr_meta(pr_number)
        if current["headRefOid"] != reviewed_head_sha:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="merge 前重跑 guardian 后 PR HEAD 已变化",
            )
            raise SystemExit("merge 前重跑 guardian 后 PR HEAD 已变化，拒绝合并。")
        if str(current.get("body") or "") != str(refreshed_meta.get("body") or ""):
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="merge 前重跑 guardian 后 PR 描述已变化",
            )
            raise SystemExit("merge 前重跑 guardian 后 PR 描述已变化，拒绝合并。")
    review_artifact_validation_errors: list[str] = []
    if review_artifact_gate_applies(current):
        artifact_temp_dir, artifact_worktree_dir = prepare_worktree(pr_number, current)
        try:
            review_artifact_validation_errors = review_artifact_errors(current, repo_root=artifact_worktree_dir)
        finally:
            cleanup(artifact_temp_dir)
    if review_artifact_validation_errors:
        if merge_time_integration_recheck_recorded:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="Review Artifacts 门禁校验失败后无法保持 PR 元数据一致",
            )
        detail = "\n".join(f"- {item}" for item in review_artifact_validation_errors)
        raise SystemExit(f"Review Artifacts 门禁未满足，拒绝合并：\n{detail}")
    integration_errors = integration_merge_gate_errors(current, require_live_state=True)
    if integration_errors:
        if merge_time_integration_recheck_recorded:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="integration merge gate 校验失败后无法保持 PR 元数据一致",
            )
        detail = "\n".join(f"- {item}" for item in integration_errors)
        raise SystemExit(f"integration merge gate 未满足，拒绝合并：\n{detail}")
    latest_before_merge = pr_meta(pr_number)
    if latest_before_merge["headRefOid"] != current["headRefOid"]:
        if merge_time_integration_recheck_recorded:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="执行 `gh pr merge` 前 PR HEAD 已变化",
            )
        raise SystemExit("执行 `gh pr merge` 前 PR HEAD 已变化，拒绝合并。")
    if str(latest_before_merge.get("body") or "") != str(current.get("body") or ""):
        if merge_time_integration_recheck_recorded:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="执行 `gh pr merge` 前 PR 描述已变化",
            )
        raise SystemExit("执行 `gh pr merge` 前 PR 描述已变化，拒绝合并。")
    current = latest_before_merge
    if not all_checks_pass(pr_number):
        if merge_time_integration_recheck_recorded:
            restore_merge_time_integration_recheck_or_die(
                pr_number,
                previous_merge_recheck_value or "no",
                failure_context="执行 `gh pr merge` 前 GitHub checks 已变化",
            )
        raise SystemExit("执行 `gh pr merge` 前 GitHub checks 未全部通过，拒绝合并。")

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
