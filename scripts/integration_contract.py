from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from scripts.common import REPO_ROOT, integration_ref_is_checkable, load_json, normalize_integration_ref_for_comparison, run


CONTRACT_PATH = REPO_ROOT / "scripts" / "policy" / "integration_contract.json"


@dataclass(frozen=True)
class IssueCanonicalResolution:
    issue_number: int | None
    canonical: dict[str, str]
    error: str | None


def load_integration_contract() -> dict:
    return load_json(CONTRACT_PATH)


RAW_CONTRACT = load_integration_contract()
FIELD_ORDER = tuple(str(name) for name in RAW_CONTRACT["field_order"])
ISSUE_SCOPE_FIELDS = tuple(str(name) for name in RAW_CONTRACT["issue_scope_fields"])
PR_SCOPE_FIELDS = tuple(str(name) for name in RAW_CONTRACT["pr_scope_fields"])
FIELD_DEFINITIONS = {str(item["name"]): item for item in RAW_CONTRACT["fields"]}
FIELD_CHOICES = {
    name: tuple(str(choice) for choice in definition.get("choices", []))
    for name, definition in FIELD_DEFINITIONS.items()
    if definition.get("type") == "enum"
}
REF_EXAMPLES = tuple(str(example) for example in FIELD_DEFINITIONS["integration_ref"].get("examples", []))
CONTRACT_SOURCE_MACHINE_READABLE = str(RAW_CONTRACT["canonical_source"]["machine_readable"])
CONTRACT_SOURCE_MODULE = str(RAW_CONTRACT["canonical_source"]["python_module"])


def field_names(scope: str) -> tuple[str, ...]:
    if scope == "issue":
        return ISSUE_SCOPE_FIELDS
    if scope == "pr":
        return PR_SCOPE_FIELDS
    raise ValueError(f"未知 contract scope: {scope}")


def field_choices(name: str) -> tuple[str, ...]:
    return FIELD_CHOICES.get(name, ())


def markdown_section_label(name: str) -> str:
    choices = field_choices(name)
    if not choices:
        return f"- {name}:"
    rendered = " / ".join(f"`{choice}`" for choice in choices)
    return f"- {name}（{rendered}）:"


def render_contract_reference_lines() -> list[str]:
    return [
        f"Canonical integration contract source: `{CONTRACT_SOURCE_MACHINE_READABLE}` / `{CONTRACT_SOURCE_MODULE}`",
    ]


def render_issue_form_guidance_lines() -> list[str]:
    return [
        "按 canonical contract 填写以下字段。",
        "`merge_gate` 的触发条件、`integration_ref` 的合法格式与 legacy 兼容规则，以 canonical contract 为准。",
        "纯本仓库事项必须显式收口为 local-only 组合；跨仓事项必须按 contract 进入 integration gate。",
    ]


def render_pr_template_guidance_lines() -> list[str]:
    return [
        "按 canonical contract 填写并校验 `integration_check`。",
        "`merge_gate` 的触发条件、`integration_ref` 的可核查格式与归一规则，以 canonical contract 为准。",
        "`integration_check_required` 的最终复核发生在 merge gate，不要把 merge-time recheck 写成 reviewer 已完成动作。",
    ]


def normalize_heading(text: str) -> str:
    normalized = text.strip()
    normalized = re.sub(r"\s*[:：]\s*$", "", normalized)
    normalized = re.sub(r"\s+/+\s*", " / ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.casefold()


FIELD_LOOKUP = {normalize_heading(name): name for name in FIELD_ORDER}


def extract_markdown_heading_sections(body: str) -> dict[str, str]:
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


def extract_issue_canonical_integration_fields(body: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    for heading, content in extract_markdown_heading_sections(body).items():
        canonical = FIELD_LOOKUP.get(normalize_heading(heading))
        if canonical in ISSUE_SCOPE_FIELDS and content:
            payload[canonical] = content.strip()
    return payload


def extract_integration_check_section(body: str) -> str:
    return extract_markdown_heading_sections(body).get("integration_check", "")


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
            if normalized_key not in PR_SCOPE_FIELDS:
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


def parse_pr_integration_check(body: str) -> dict[str, str]:
    return parse_integration_check_payload(extract_integration_check_section(body))


def normalize_integration_value(field: str, value: str) -> str:
    raw = str(value or "").strip()
    if field == "integration_ref":
        return normalize_integration_ref_for_comparison(raw)
    return raw.lower()


def missing_required_fields(payload: Mapping[str, str], scope: str) -> list[str]:
    return [field for field in field_names(scope) if not str(payload.get(field) or "").strip()]


def validate_enum_values(payload: Mapping[str, str], scope: str, *, prefix: str) -> list[str]:
    errors: list[str] = []
    for field in field_names(scope):
        choices = field_choices(field)
        if not choices:
            continue
        value = str(payload.get(field) or "").strip().lower()
        if value not in choices:
            errors.append(
                f"`{prefix}.{field}` 非法：`{value}`（仅允许 `{', '.join(choices)}`）。"
            )
    return errors


def evaluate_rule(rule: Mapping[str, str], payload: Mapping[str, str]) -> bool:
    field = str(rule["field"])
    operator = str(rule["operator"])
    expected = str(rule["value"]).lower()
    actual = str(payload.get(field) or "").strip().lower()
    if operator == "==":
        return actual == expected
    if operator == "!=":
        return actual != expected
    raise ValueError(f"未知 rule operator: {operator}")


def requires_integration_gate(payload: Mapping[str, str]) -> bool:
    for rule in RAW_CONTRACT["rules"]["merge_gate_required_when"]:
        if evaluate_rule(rule, payload):
            return True
    return False


def requires_checkable_integration_ref(payload: Mapping[str, str]) -> bool:
    return evaluate_rule(RAW_CONTRACT["rules"]["integration_touchpoint_requires_checkable_ref"], payload)


def compare_issue_and_pr_canonical(
    issue_canonical: Mapping[str, str],
    pr_payload: Mapping[str, str],
    *,
    issue_label: str,
    field_prefix: str = "integration_check",
) -> list[str]:
    errors: list[str] = []
    for field in ISSUE_SCOPE_FIELDS:
        expected = normalize_integration_value(field, issue_canonical.get(field, ""))
        actual = normalize_integration_value(field, pr_payload.get(field, ""))
        if expected != actual:
            errors.append(f"`{field_prefix}.{field}` 与 {issue_label} 中的 canonical integration 元数据不一致。")
    return errors


def missing_pr_integration_check_error(issue_number: int | None) -> str:
    issue_label = f"Issue #{issue_number}" if issue_number else "对应 Issue"
    return f"PR 对应的 {issue_label} 已声明 canonical integration 元数据，PR 描述缺少 canonical `integration_check` 段落。"


def validate_issue_canonical_resolution(resolution: IssueCanonicalResolution, *, allow_missing_payload: bool) -> list[str]:
    if resolution.error:
        return [resolution.error]
    if not resolution.canonical:
        return [] if allow_missing_payload else [f"Issue #{resolution.issue_number} 缺少 canonical integration 元数据，受控入口拒绝继续。"]

    missing = missing_required_fields(resolution.canonical, "issue")
    if not missing:
        return validate_enum_values(resolution.canonical, "issue", prefix="issue_canonical")
    missing_text = "、".join(f"`{field}`" for field in missing)
    return [f"Issue #{resolution.issue_number} 的 canonical integration 元数据缺少字段：{missing_text}。"]


def validate_open_pr_payload(payload: Mapping[str, str], *, issue_canonical: Mapping[str, str], issue_number: int | None) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_enum_values(payload, "pr", prefix="integration"))
    integration_ref = str(payload.get("integration_ref") or "").strip()
    merge_gate = str(payload.get("merge_gate") or "").strip().lower()
    integration_touchpoint = str(payload.get("integration_touchpoint") or "").strip().lower()
    if requires_checkable_integration_ref(payload):
        if not integration_ref:
            errors.append("`integration_touchpoint != none` 时，`integration_ref` 不能为空。")
        elif integration_ref.lower() == "none":
            errors.append("`integration_touchpoint != none` 时，`integration_ref` 不能为 `none`。")
        elif not integration_ref_is_checkable(integration_ref):
            errors.append("`integration_touchpoint != none` 时，`integration_ref` 必须指向可核查的具体 integration issue / item。")
    if merge_gate == "integration_check_required":
        if not integration_ref:
            errors.append("`merge_gate=integration_check_required` 时，`integration_ref` 不能为空。")
        if not integration_ref_is_checkable(integration_ref):
            errors.append("`merge_gate=integration_check_required` 时，`integration_ref` 必须指向具体 integration issue / item。")
        if integration_touchpoint == "none":
            errors.append("`merge_gate=integration_check_required` 时，`integration_touchpoint` 不能为 `none`。")
        if str(payload.get("integration_status_checked_before_pr") or "").strip().lower() != "yes":
            errors.append("`merge_gate=integration_check_required` 时，进入 `open_pr` 前必须记录 `integration_status_checked_before_pr=yes`。")
    if str(payload.get("integration_status_checked_before_merge") or "").strip().lower() == "yes":
        errors.append("`open_pr` 阶段不得把 `integration_status_checked_before_merge` 设为 `yes`；该字段只能在进入 `merge_pr` 前显式确认。")
    if requires_integration_gate(payload) and merge_gate != "integration_check_required":
        errors.append("触及 integration 联动、共享契约、共享 contract surface、跨仓依赖或联合验收时，`merge_gate` 必须为 `integration_check_required`。")
    if str(payload.get("external_dependency") or "").strip().lower() != "none" and integration_touchpoint == "none":
        errors.append("存在跨仓依赖、联合验收或共享 contract surface 时，`integration_touchpoint` 不能为 `none`。")
    if str(payload.get("joint_acceptance_needed") or "").strip().lower() == "yes" and integration_touchpoint == "none":
        errors.append("存在跨仓依赖、联合验收或共享 contract surface 时，`integration_touchpoint` 不能为 `none`。")
    if str(payload.get("contract_surface") or "").strip().lower() != "none" and integration_touchpoint == "none":
        errors.append("`contract_surface != none` 时，`integration_touchpoint` 不能为 `none`。")
    if merge_gate != "integration_check_required":
        if integration_ref == "":
            errors.append("纯本仓库事项也必须显式填写 `integration_ref`；若无 integration 联动，请写 `none`。")
        elif normalize_integration_value("integration_ref", integration_ref) != "none" and not integration_ref_is_checkable(integration_ref):
            errors.append("`integration_ref` 必须使用可核查的具体 integration issue / item 引用（例如 `#123`、`owner/repo#123`、issue URL 或带 `itemId=` 的 project item URL）。")
        elif normalize_integration_value("integration_ref", integration_ref) != "none":
            errors.append("纯本仓库事项必须显式使用 `integration_ref=none`，不得保留外部 integration 绑定。")

    if issue_canonical:
        issue_label = f"Issue #{issue_number}" if issue_number else "对应 Issue"
        errors.extend(compare_issue_and_pr_canonical(issue_canonical, payload, issue_label=issue_label, field_prefix="cli"))
    return errors


def validate_pr_merge_gate_payload(
    payload: Mapping[str, str],
    *,
    issue_number: int | None,
    issue_canonical: Mapping[str, str],
    require_merge_time_recheck: bool,
) -> list[str]:
    errors: list[str] = []
    merge_gate = str(payload.get("merge_gate") or "").strip().lower()
    if not merge_gate:
        return ["PR 描述中的 `integration_check.merge_gate` 不能为空。"]
    if merge_gate not in field_choices("merge_gate"):
        return [f"PR 描述中的 `integration_check.merge_gate` 非法：`{merge_gate}`（仅允许 `local_only` / `integration_check_required`）。"]
    missing = sorted(missing_required_fields(payload, "pr"))
    if missing:
        missing_text = "、".join(f"`integration_check.{field}`" for field in missing)
        return [f"PR 描述中的 `integration_check` 缺少必填字段：{missing_text}。"]

    errors.extend(validate_enum_values(payload, "pr", prefix="integration_check"))
    if issue_canonical:
        issue_label = f"Issue #{issue_number}" if issue_number else "对应 Issue"
        errors.extend(compare_issue_and_pr_canonical(issue_canonical, payload, issue_label=issue_label))

    integration_touchpoint = str(payload.get("integration_touchpoint") or "").strip().lower()
    integration_ref = str(payload.get("integration_ref") or "").strip()
    if requires_checkable_integration_ref(payload):
        if not integration_ref:
            errors.append("`integration_touchpoint != none` 时，`integration_ref` 不能为空。")
        elif integration_ref.lower() == "none":
            errors.append("`integration_touchpoint != none` 时，`integration_ref` 不能为 `none`。")
        elif not integration_ref_is_checkable(integration_ref):
            errors.append("`integration_touchpoint != none` 时，`integration_ref` 必须指向可核查的具体 integration issue / item。")

    if requires_integration_gate(payload) and merge_gate != "integration_check_required":
        errors.append(
            "`merge_gate=local_only` 与当前 integration 元数据冲突："
            "当 `integration_touchpoint != none`、`shared_contract_changed=yes`、`external_dependency != none`、"
            "`contract_surface != none` 或 `joint_acceptance_needed=yes` 时，"
            "`merge_gate` 必须为 `integration_check_required`。"
        )
    if str(payload.get("external_dependency") or "").strip().lower() != "none" and integration_touchpoint == "none":
        errors.append("存在跨仓依赖、联合验收或共享 contract surface 时，`integration_touchpoint` 不能为 `none`。")
    if str(payload.get("joint_acceptance_needed") or "").strip().lower() == "yes" and integration_touchpoint == "none":
        errors.append("存在跨仓依赖、联合验收或共享 contract surface 时，`integration_touchpoint` 不能为 `none`。")
    if str(payload.get("contract_surface") or "").strip().lower() != "none" and integration_touchpoint == "none":
        errors.append("`contract_surface != none` 时，`integration_touchpoint` 不能为 `none`。")

    if merge_gate != "integration_check_required":
        if requires_integration_gate(payload):
            return errors
        if not integration_ref:
            errors.append("纯本仓库事项也必须显式填写 `integration_ref`；若无 integration 联动，请写 `none`。")
        elif normalize_integration_value("integration_ref", integration_ref) != "none" and not integration_ref_is_checkable(integration_ref):
            errors.append("`integration_ref` 必须使用可核查的具体 integration issue / item 引用（例如 `#123`、`owner/repo#123`、issue URL 或带 `itemId=` 的 project item URL）。")
        elif normalize_integration_value("integration_ref", integration_ref) != "none":
            errors.append("纯本仓库事项必须显式使用 `integration_ref=none`，不得保留外部 integration 绑定。")
        return errors

    if integration_touchpoint == "none":
        errors.append("`merge_gate=integration_check_required` 时，`integration_touchpoint` 不能为 `none`。")
    if not integration_ref or not integration_ref_is_checkable(integration_ref):
        errors.append("`merge_gate=integration_check_required` 时，`integration_ref` 必须指向具体 integration issue / item。")
    if str(payload.get("integration_status_checked_before_pr") or "").strip().lower() != "yes":
        errors.append("`merge_gate=integration_check_required` 时，PR 描述必须记录 `integration_status_checked_before_pr=yes`。")
    if require_merge_time_recheck and str(payload.get("integration_status_checked_before_merge") or "").strip().lower() != "yes":
        errors.append("`merge_gate=integration_check_required` 时，进入 `merge_pr` 前必须把 `integration_status_checked_before_merge` 更新为 `yes`。")
    return errors


def validate_pr_integration_contract(
    payload: Mapping[str, str],
    *,
    issue_number: int | None,
    issue_canonical: Mapping[str, str],
    issue_error: str | None = None,
    require_merge_time_recheck: bool,
) -> list[str]:
    if issue_error:
        return [issue_error]
    if not payload:
        return [missing_pr_integration_check_error(issue_number)] if issue_canonical else []
    return validate_pr_merge_gate_payload(
        payload,
        issue_number=issue_number,
        issue_canonical=issue_canonical,
        require_merge_time_recheck=require_merge_time_recheck,
    )


def merge_gate_requires_integration_recheck(payload: Mapping[str, str]) -> bool:
    return str(payload.get("merge_gate") or "").strip().lower() == "integration_check_required"


def validate_issue_fetch(issue_number: int, *, allow_missing_payload: bool) -> IssueCanonicalResolution:
    completed = run(
        ["gh", "issue", "view", str(issue_number), "--json", "body"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return IssueCanonicalResolution(
            issue_number=issue_number,
            canonical={},
            error=f"无法读取 Issue #{issue_number} 的 canonical integration 元数据，拒绝继续。",
        )
    payload = json.loads(completed.stdout or "{}")
    canonical = extract_issue_canonical_integration_fields(str(payload.get("body") or ""))
    if not canonical and allow_missing_payload:
        return IssueCanonicalResolution(issue_number=issue_number, canonical={}, error=None)
    if not canonical:
        return IssueCanonicalResolution(
            issue_number=issue_number,
            canonical={},
            error=f"Issue #{issue_number} 缺少 canonical integration 元数据，受控入口拒绝继续。",
        )
    missing = missing_required_fields(canonical, "issue")
    if missing:
        missing_text = "、".join(f"`{field}`" for field in missing)
        return IssueCanonicalResolution(
            issue_number=issue_number,
            canonical=canonical,
            error=f"Issue #{issue_number} 的 canonical integration 元数据缺少字段：{missing_text}。",
        )
    enum_errors = validate_enum_values(canonical, "issue", prefix="issue_canonical")
    if enum_errors:
        return IssueCanonicalResolution(
            issue_number=issue_number,
            canonical=canonical,
            error=enum_errors[0],
        )
    return IssueCanonicalResolution(issue_number=issue_number, canonical=canonical, error=None)


def build_review_packet(
    body: str,
    *,
    issue_number: int | None,
    issue_canonical: Mapping[str, str],
    issue_error: str | None,
) -> dict[str, object]:
    pr_payload = parse_pr_integration_check(body)
    issue_label = f"Issue #{issue_number}" if issue_number else "对应 Issue"
    packet_issue_error = str(issue_error or "").strip()
    missing_pr_error = missing_pr_integration_check_error(issue_number) if issue_canonical and not pr_payload else ""
    comparison_errors = (
        [packet_issue_error]
        if packet_issue_error
        else
        [missing_pr_error]
        if missing_pr_error
        else compare_issue_and_pr_canonical(issue_canonical, pr_payload, issue_label=issue_label) if issue_canonical and pr_payload else []
    )
    normalized_issue = {
        field: normalize_integration_value(field, issue_canonical.get(field, ""))
        for field in ISSUE_SCOPE_FIELDS
        if str(issue_canonical.get(field) or "").strip()
    }
    normalized_pr = {
        field: normalize_integration_value(field, pr_payload.get(field, ""))
        for field in PR_SCOPE_FIELDS
        if str(pr_payload.get(field) or "").strip()
    }
    merge_validation_errors = validate_pr_integration_contract(
        pr_payload,
        issue_number=issue_number,
        issue_canonical=issue_canonical,
        issue_error=packet_issue_error,
        require_merge_time_recheck=False,
    )
    return {
        "contract_sources": [
            CONTRACT_SOURCE_MACHINE_READABLE,
            CONTRACT_SOURCE_MODULE,
        ],
        "issue_number": issue_number,
        "issue_error": issue_error or "",
        "issue_canonical": dict(issue_canonical),
        "normalized_issue_canonical": normalized_issue,
        "pr_canonical": pr_payload,
        "normalized_pr_canonical": normalized_pr,
        "comparison_errors": comparison_errors,
        "merge_gate": str(pr_payload.get("merge_gate") or "").strip().lower() if pr_payload else "",
        "merge_gate_requires_recheck": merge_gate_requires_integration_recheck(pr_payload) if pr_payload else False,
        "merge_validation_errors": merge_validation_errors,
    }


def render_review_packet_lines(packet: Mapping[str, object]) -> list[str]:
    lines = [
        f"- contract source: `{CONTRACT_SOURCE_MACHINE_READABLE}`",
        f"- contract module: `{CONTRACT_SOURCE_MODULE}`",
        f"- issue_number: {packet.get('issue_number') or '无'}",
        f"- issue_lookup_error: {packet.get('issue_error') or 'none'}",
    ]
    issue_canonical = packet.get("issue_canonical") or {}
    if issue_canonical:
        lines.append("- issue_canonical:")
        lines.extend([f"  - {field}: {issue_canonical[field]}" for field in ISSUE_SCOPE_FIELDS if field in issue_canonical])
    else:
        lines.append("- issue_canonical: none")
    pr_canonical = packet.get("pr_canonical") or {}
    if pr_canonical:
        lines.append("- pr_canonical:")
        lines.extend([f"  - {field}: {pr_canonical[field]}" for field in PR_SCOPE_FIELDS if field in pr_canonical])
    else:
        lines.append("- pr_canonical: none")
    normalized_issue = packet.get("normalized_issue_canonical") or {}
    if normalized_issue:
        lines.append("- normalized_issue_canonical:")
        lines.extend([f"  - {field}: {normalized_issue[field]}" for field in ISSUE_SCOPE_FIELDS if field in normalized_issue])
    normalized_pr = packet.get("normalized_pr_canonical") or {}
    if normalized_pr:
        lines.append("- normalized_pr_canonical:")
        lines.extend([f"  - {field}: {normalized_pr[field]}" for field in PR_SCOPE_FIELDS if field in normalized_pr])
    comparison_errors = packet.get("comparison_errors") or []
    if comparison_errors:
        lines.append("- canonical_mismatches:")
        lines.extend([f"  - {item}" for item in comparison_errors])
    else:
        lines.append("- canonical_mismatches: none")
    merge_validation_errors = packet.get("merge_validation_errors") or []
    if merge_validation_errors:
        lines.append("- merge_gate_validation:")
        lines.extend([f"  - {item}" for item in merge_validation_errors])
    else:
        lines.append("- merge_gate_validation: ok")
    lines.append(f"- merge_gate: {packet.get('merge_gate') or 'none'}")
    lines.append(f"- merge_gate_requires_recheck: {'yes' if packet.get('merge_gate_requires_recheck') else 'no'}")
    return lines
