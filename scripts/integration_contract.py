from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import parse_qs, urlparse

from scripts.common import (
    REPO_ROOT,
    default_github_repo,
    integration_ref_is_checkable,
    load_json,
    normalize_integration_ref_for_comparison,
    run,
)


CONTRACT_PATH = REPO_ROOT / "scripts" / "policy" / "integration_contract.json"


@dataclass(frozen=True)
class IssueCanonicalResolution:
    issue_number: int | None
    canonical: dict[str, str]
    error: str | None


def load_integration_contract() -> dict:
    return load_json(CONTRACT_PATH)


def decode_remote_json(stdout: str, *, error_message: str) -> dict[str, object]:
    try:
        payload = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return {"error": error_message}
    if not isinstance(payload, dict):
        return {"error": error_message}
    return payload


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
CANONICAL_INTEGRATION_PROJECT_TITLE = "Syvert × WebEnvoy Integration"
CANONICAL_INTEGRATION_PROJECT_REQUIRED_FIELDS = frozenset(
    {
        "status",
        "dependency order",
        "joint acceptance",
        "owner repo",
        "contract status",
    }
)
MERGE_TIME_ALLOWED_LIVE_STATUSES = tuple(
    str(item).strip().lower() for item in RAW_CONTRACT["rules"].get("merge_time_allowed_live_statuses", [])
)
INTEGRATION_PROJECT_ITEM_QUERY = """
query($id: ID!) {
  node(id: $id) {
    __typename
    ... on ProjectV2Item {
      id
      isArchived
      fieldValues(first: 100) {
        nodes {
          __typename
          ... on ProjectV2ItemFieldSingleSelectValue {
            name
            field { ... on ProjectV2FieldCommon { name } }
          }
          ... on ProjectV2ItemFieldTextValue {
            text
            field { ... on ProjectV2FieldCommon { name } }
          }
          ... on ProjectV2ItemFieldNumberValue {
            number
            field { ... on ProjectV2FieldCommon { name } }
          }
          ... on ProjectV2ItemFieldDateValue {
            date
            field { ... on ProjectV2FieldCommon { name } }
          }
        }
      }
      project {
        url
        number
        title
        owner {
          __typename
          ... on Organization { login }
          ... on User { login }
        }
      }
      content {
        __typename
        ... on Issue {
          number
          state
          title
          url
          repository { nameWithOwner }
        }
      }
    }
  }
}
""".strip()

ISSUE_PROJECT_ITEMS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      number
      title
      url
      state
      projectItems(first: 100, after: $after) {
        nodes {
          __typename
          ... on ProjectV2Item {
            id
            isArchived
            fieldValues(first: 100) {
              nodes {
                __typename
                ... on ProjectV2ItemFieldSingleSelectValue {
                  name
                  field { ... on ProjectV2FieldCommon { name } }
                }
                ... on ProjectV2ItemFieldTextValue {
                  text
                  field { ... on ProjectV2FieldCommon { name } }
                }
                ... on ProjectV2ItemFieldNumberValue {
                  number
                  field { ... on ProjectV2FieldCommon { name } }
                }
                ... on ProjectV2ItemFieldDateValue {
                  date
                  field { ... on ProjectV2FieldCommon { name } }
                }
              }
            }
            project {
              url
              number
              title
              owner {
                __typename
                ... on Organization { login }
                ... on User { login }
              }
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
""".strip()


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


def semantic_integration_ref_key(value: str) -> str:
    identity, _, _ = semantic_integration_ref_identity(value)
    return identity


def semantic_integration_ref_identity(value: str) -> tuple[str, bool, str]:
    normalized = normalize_integration_ref_for_comparison(value)
    if normalized in {"", "none"}:
        return normalized, True, normalized
    if normalized.startswith("issue:"):
        return normalized, True, normalized
    if not normalized.startswith("project-item:"):
        return normalized, True, normalized
    live_state = fetch_integration_ref_live_state(value)
    if str(live_state.get("error") or "").strip():
        return normalized, False, normalized
    content_repo = str(live_state.get("content_repo") or "").strip().lower()
    content_issue_number = str(live_state.get("content_issue_number") or "").strip()
    if content_repo and content_issue_number:
        return f"issue:{content_repo}#{content_issue_number}", True, normalized
    return normalized, False, normalized


def normalize_integration_value_for_packet(field: str, value: str) -> str:
    raw = str(value or "").strip()
    if field == "integration_ref":
        return semantic_integration_ref_key(raw)
    return normalize_integration_value(field, raw)


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
        if field == "integration_ref":
            expected, expected_resolved, expected_static = semantic_integration_ref_identity(str(issue_canonical.get(field, "") or ""))
            actual, actual_resolved, actual_static = semantic_integration_ref_identity(str(pr_payload.get(field, "") or ""))
            if expected == actual:
                continue
            cross_form_pair = {
                expected_static.split(":", 1)[0],
                actual_static.split(":", 1)[0],
            } == {"issue", "project-item"}
            if cross_form_pair and (not expected_resolved or not actual_resolved):
                continue
            errors.append(f"`{field_prefix}.{field}` 与 {issue_label} 中的 canonical integration 元数据不一致。")
            continue
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


def parse_issue_ref(integration_ref: str) -> tuple[str, int] | None:
    ref = integration_ref.strip()
    local_match = re.match(r"^#(\d+)$", ref)
    if local_match:
        return default_github_repo(), int(local_match.group(1))

    repo_match = re.match(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)$", ref)
    if repo_match:
        return repo_match.group(1), int(repo_match.group(2))

    url_match = re.match(r"^https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d+)$", ref)
    if url_match:
        return url_match.group(1), int(url_match.group(2))
    return None


def parse_project_item_ref(integration_ref: str) -> tuple[str, str, str] | None:
    parsed = urlparse(integration_ref.strip())
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        return None
    if len(path_parts) < 4 or path_parts[0] != "orgs" or path_parts[2] != "projects":
        return None
    item_ids = parse_qs(parsed.query).get("itemId", [])
    if not item_ids:
        return None
    return path_parts[1], path_parts[3], item_ids[0]


def value_from_project_item_node(node: Mapping[str, object]) -> str:
    typename = str(node.get("__typename") or "")
    if typename == "ProjectV2ItemFieldSingleSelectValue":
        return str(node.get("name") or "").strip()
    if typename == "ProjectV2ItemFieldTextValue":
        return str(node.get("text") or "").strip()
    if typename == "ProjectV2ItemFieldNumberValue":
        number = node.get("number")
        return "" if number is None else str(number).strip()
    if typename == "ProjectV2ItemFieldDateValue":
        return str(node.get("date") or "").strip()
    return ""


def normalize_label_value(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def extract_label_value(labels: Iterable[str], prefixes: tuple[str, ...]) -> str:
    for label in labels:
        candidate = label.strip().lower()
        for prefix in prefixes:
            if candidate.startswith(prefix):
                return normalize_label_value(candidate[len(prefix) :])
    return ""


def repo_name_from_slug(slug: str) -> str:
    if "/" not in slug:
        return slug.strip().lower()
    return slug.split("/", 1)[1].strip().lower()


def canonical_integration_project_owner() -> str:
    repo_slug = default_github_repo()
    owner, _, _ = repo_slug.partition("/")
    return owner.strip().lower()


def project_item_fields(node: Mapping[str, object]) -> dict[str, str]:
    field_nodes = ((node.get("fieldValues") or {}).get("nodes") or []) if isinstance(node, dict) else []
    fields: dict[str, str] = {}
    if isinstance(field_nodes, list):
        for raw_node in field_nodes:
            if not isinstance(raw_node, dict):
                continue
            field_name = str(((raw_node.get("field") or {}).get("name") or "")).strip()
            if not field_name:
                continue
            fields[field_name.lower()] = value_from_project_item_node(raw_node)
    return fields


def is_canonical_integration_project_item(node: Mapping[str, object], fields: Mapping[str, str]) -> bool:
    project = node.get("project") or {}
    project_title = str((project or {}).get("title") or "").strip()
    project_owner = str(((project or {}).get("owner") or {}).get("login") or "").strip().lower()
    return (
        project_title == CANONICAL_INTEGRATION_PROJECT_TITLE
        and project_owner == canonical_integration_project_owner()
        and CANONICAL_INTEGRATION_PROJECT_REQUIRED_FIELDS.issubset(fields.keys())
    )


def build_project_item_live_state(
    integration_ref: str,
    node: Mapping[str, object],
    *,
    source: str,
    expected_owner: str | None = None,
    expected_project_number: str | None = None,
    require_canonical_contract: bool = False,
) -> dict[str, object]:
    if str(node.get("__typename") or "") != "ProjectV2Item":
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": source,
            "error": "`integration_ref` 指向对象不是可读的 ProjectV2Item，拒绝继续。",
        }
    if bool(node.get("isArchived")):
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": source,
            "error": "`integration_ref` 指向的 ProjectV2Item 已归档，不能作为 merge gate 真相源。",
        }

    fields = project_item_fields(node)
    if require_canonical_contract and not is_canonical_integration_project_item(node, fields):
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": source,
            "error": (
                "`integration_ref` 必须指向 owner 级 canonical integration project item "
                f"`{CANONICAL_INTEGRATION_PROJECT_TITLE}`，拒绝继续。"
            ),
        }
    project = node.get("project") or {}
    project_url = str((project or {}).get("url") or "").strip()
    project_owner = str(((project or {}).get("owner") or {}).get("login") or "").strip().lower()
    project_number_actual = str((project or {}).get("number") or "").strip()
    if expected_owner and project_owner and project_owner != expected_owner.strip().lower():
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": source,
            "error": (
                "`integration_ref` 与 project item 实际归属不一致："
                f"URL owner=`{expected_owner}`，返回 owner=`{project_owner}`。"
            ),
        }
    if expected_project_number and project_number_actual and project_number_actual != expected_project_number.strip():
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": source,
            "error": (
                "`integration_ref` 与 project item 实际 project 编号不一致："
                f"URL projects/{expected_project_number}，返回 projects/{project_number_actual}。"
            ),
        }

    status = normalize_label_value(fields.get("status", ""))
    dependency_order = normalize_label_value(fields.get("dependency order", ""))
    joint_acceptance = normalize_label_value(fields.get("joint acceptance", ""))
    contract_status = normalize_label_value(fields.get("contract status", ""))
    owner_repo = normalize_label_value(fields.get("owner repo", ""))
    blocked = status == "blocked"

    return {
        "integration_ref": integration_ref,
        "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
        "source": source,
        "url": integration_ref,
        "project_url": project_url,
        "project_title": str((project or {}).get("title") or "").strip(),
        "project_number": project_number_actual or (expected_project_number or "").strip(),
        "organization": project_owner or (expected_owner or "").strip().lower(),
        "item_id": str(node.get("id") or "").strip(),
        "status": status,
        "dependency_order": dependency_order,
        "joint_acceptance": joint_acceptance,
        "contract_status": contract_status,
        "owner_repo": owner_repo,
        "blocked": blocked,
        "error": "",
    }


def fetch_issue_integration_ref_live_state(integration_ref: str, repo_slug: str, issue_number: int) -> dict[str, object]:
    owner, _, name = repo_slug.partition("/")
    issue: dict[str, object] | None = None
    project_nodes: list[dict[str, object]] = []
    after: str | None = None

    while True:
        command = [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={ISSUE_PROJECT_ITEMS_QUERY}",
            "-F",
            f"owner={owner}",
            "-F",
            f"name={name}",
            "-F",
            f"number={issue_number}",
        ]
        if after:
            command.extend(["-f", f"after={after}"])
        completed = run(command, cwd=REPO_ROOT, check=False)
        if completed.returncode != 0:
            return {
                "integration_ref": integration_ref,
                "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
                "source": "issue",
                "error": f"无法读取 `integration_ref` 指向的 issue `{repo_slug}#{issue_number}`，拒绝继续。",
            }

        payload = decode_remote_json(
            completed.stdout,
            error_message=(
                f"无法解析 `integration_ref` 指向的 issue `{repo_slug}#{issue_number}` 的远端响应，拒绝继续。"
            ),
        )
        if payload.get("error"):
            return {
                "integration_ref": integration_ref,
                "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
                "source": "issue",
                "error": str(payload["error"]),
            }
        current_issue = (((payload.get("data") or {}).get("repository") or {}).get("issue") or {}) if isinstance(payload, dict) else {}
        if not isinstance(current_issue, dict) or not current_issue:
            return {
                "integration_ref": integration_ref,
                "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
                "source": "issue",
                "error": f"无法读取 `integration_ref` 指向的 issue `{repo_slug}#{issue_number}`，拒绝继续。",
            }

        issue = current_issue
        project_items = (current_issue.get("projectItems") or {}) if isinstance(current_issue, dict) else {}
        nodes = project_items.get("nodes") or []
        if isinstance(nodes, list):
            project_nodes.extend(item for item in nodes if isinstance(item, dict))
        page_info = project_items.get("pageInfo") or {}
        has_next_page = bool(page_info.get("hasNextPage"))
        if not has_next_page:
            break
        after = str(page_info.get("endCursor") or "").strip()
        if not after:
            return {
                "integration_ref": integration_ref,
                "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
                "source": "issue",
                "error": (
                    f"`integration_ref` 指向的 issue `{repo_slug}#{issue_number}` 的 projectItems 分页信息不完整，"
                    "无法完整读取 owner 级 integration project item，拒绝继续。"
                ),
            }

    if issue is None:
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": "issue",
            "error": f"无法读取 `integration_ref` 指向的 issue `{repo_slug}#{issue_number}`，拒绝继续。",
        }

    candidates: list[dict[str, object]] = []
    for raw_node in project_nodes:
        if not isinstance(raw_node, dict) or bool(raw_node.get("isArchived")):
            continue
        fields = project_item_fields(raw_node)
        if not is_canonical_integration_project_item(raw_node, fields):
            continue
        candidate = build_project_item_live_state(integration_ref, raw_node, source="issue_project_item")
        if str(candidate.get("error") or "").strip():
            continue
        candidates.append(candidate)

    if not candidates:
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": "issue",
            "url": str(issue.get("url") or "").strip(),
            "title": str(issue.get("title") or "").strip(),
            "error": (
                f"`integration_ref` 指向的 issue `{repo_slug}#{issue_number}` 未挂接可核查的 integration project item，"
                "无法读取 `status` / `dependency_order` / `joint_acceptance`，拒绝继续。"
            ),
        }
    if len(candidates) > 1:
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": "issue",
            "url": str(issue.get("url") or "").strip(),
            "title": str(issue.get("title") or "").strip(),
            "error": (
                f"`integration_ref` 指向的 issue `{repo_slug}#{issue_number}` 命中多个可核查的 integration project item，"
                "当前无法唯一确定 merge gate 真相源，拒绝继续。"
            ),
        }

    candidate = dict(candidates[0])
    candidate["source"] = "issue"
    candidate["url"] = str(issue.get("url") or "").strip()
    candidate["title"] = str(issue.get("title") or "").strip()
    candidate["issue_state"] = normalize_label_value(str(issue.get("state") or ""))
    return candidate


def fetch_project_item_integration_ref_live_state(
    integration_ref: str,
    organization: str,
    project_number: str,
    item_id: str,
) -> dict[str, object]:
    completed = run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={INTEGRATION_PROJECT_ITEM_QUERY}",
            "-F",
            f"id={item_id}",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": "project_item",
            "error": f"无法读取 `integration_ref` 指向的 project item `{item_id}`，拒绝继续。",
        }

    payload = decode_remote_json(
        completed.stdout,
        error_message=f"无法解析 `integration_ref` 指向的 project item `{item_id}` 的远端响应，拒绝继续。",
    )
    if payload.get("error"):
        return {
            "integration_ref": integration_ref,
            "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
            "source": "project_item",
            "error": str(payload["error"]),
        }
    node = ((payload.get("data") or {}).get("node") or {}) if isinstance(payload, dict) else {}
    live_state = build_project_item_live_state(
        integration_ref,
        node,
        source="project_item",
        expected_owner=organization,
        expected_project_number=project_number,
        require_canonical_contract=True,
    )
    if not str(live_state.get("error") or "").strip():
        content = node.get("content") or {}
        if str(content.get("__typename") or "") != "Issue":
            return {
                "integration_ref": integration_ref,
                "normalized_ref": normalize_integration_ref_for_comparison(integration_ref),
                "source": "project_item",
                "error": "`integration_ref` 直连的 project item 必须绑定到可核查的 Issue 内容，拒绝继续。",
            }
        repository = content.get("repository") or {}
        live_state["content_type"] = "issue"
        live_state["content_url"] = str(content.get("url") or "").strip()
        live_state["content_issue_number"] = str(content.get("number") or "").strip()
        live_state["content_repo"] = str(repository.get("nameWithOwner") or "").strip()
        live_state["item_id"] = item_id
    return live_state


def fetch_integration_ref_live_state(integration_ref: str) -> dict[str, object]:
    ref = integration_ref.strip()
    if not ref:
        return {}
    if not integration_ref_is_checkable(ref):
        return {
            "integration_ref": ref,
            "normalized_ref": normalize_integration_ref_for_comparison(ref),
            "source": "unknown",
            "error": "`integration_ref` 不是可核查的 issue / project item 引用，拒绝继续。",
        }

    issue_ref = parse_issue_ref(ref)
    if issue_ref:
        repo_slug, issue_number = issue_ref
        return fetch_issue_integration_ref_live_state(ref, repo_slug, issue_number)

    project_item_ref = parse_project_item_ref(ref)
    if project_item_ref:
        organization, project_number, item_id = project_item_ref
        return fetch_project_item_integration_ref_live_state(ref, organization, project_number, item_id)

    return {
        "integration_ref": ref,
        "normalized_ref": normalize_integration_ref_for_comparison(ref),
        "source": "unknown",
        "error": "`integration_ref` 格式无法解析为 issue / project item，拒绝继续。",
    }


def validate_integration_ref_live_state(
    payload: Mapping[str, str],
    live_state: Mapping[str, object],
    *,
    current_repo_slug: str | None = None,
) -> list[str]:
    if not merge_gate_requires_integration_recheck(payload):
        return []
    integration_ref = str(payload.get("integration_ref") or "").strip()
    if not integration_ref or not integration_ref_is_checkable(integration_ref):
        return []
    if not live_state:
        return ["无法读取 `integration_ref` 当前状态，拒绝继续。"]

    errors: list[str] = []
    error_text = str(live_state.get("error") or "").strip()
    if error_text:
        return [error_text]

    if bool(live_state.get("blocked")):
        errors.append("`integration_ref` 当前状态为 `blocked`，拒绝继续。")

    dependency_order = normalize_label_value(str(live_state.get("dependency_order") or ""))
    status = normalize_label_value(str(live_state.get("status") or ""))
    owner_repo = normalize_label_value(str(live_state.get("owner_repo") or ""))
    contract_status = normalize_label_value(str(live_state.get("contract_status") or ""))
    if not status:
        errors.append("无法从 `integration_ref` 读取当前 `status`，拒绝继续。")
    elif status not in MERGE_TIME_ALLOWED_LIVE_STATUSES:
        allowed = " / ".join(MERGE_TIME_ALLOWED_LIVE_STATUSES)
        errors.append(
            f"`integration_ref` 当前 `status` 为 `{status}`，未进入允许合并的状态集合（仅允许 `{allowed}`）。"
        )
    if not dependency_order:
        errors.append("无法从 `integration_ref` 读取当前 `dependency_order`，拒绝继续。")
    if not owner_repo:
        errors.append("无法从 `integration_ref` 读取当前 `owner_repo`，拒绝继续。")
    if not contract_status:
        errors.append("无法从 `integration_ref` 读取当前 `contract_status`，拒绝继续。")
    repo_name = repo_name_from_slug(current_repo_slug or default_github_repo())
    if dependency_order == "webenvoy_first" and repo_name == "syvert":
        errors.append("`integration_ref` 的依赖顺序要求 `webenvoy_first`，当前仓库不得先合并。")
    if dependency_order == "syvert_first" and repo_name == "webenvoy":
        errors.append("`integration_ref` 的依赖顺序要求 `syvert_first`，当前仓库不得先合并。")

    if str(payload.get("joint_acceptance_needed") or "").strip().lower() == "yes":
        joint_acceptance = normalize_label_value(str(live_state.get("joint_acceptance") or ""))
        if not joint_acceptance:
            errors.append("`joint_acceptance_needed=yes`，但无法从 `integration_ref` 读取联合验收状态，拒绝继续。")
        elif joint_acceptance == "failed":
            errors.append("`integration_ref` 联合验收状态为 `failed`，拒绝继续。")
        elif joint_acceptance not in {"ready", "passed"}:
            errors.append(f"`integration_ref` 联合验收状态未就绪（当前 `{joint_acceptance}`），拒绝继续。")
    return errors


def validate_issue_canonical_payload(payload: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    merge_gate = str(payload.get("merge_gate") or "").strip().lower()
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
            "Issue canonical integration 元数据与 contract 组合约束冲突："
            "当 `integration_touchpoint != none`、`shared_contract_changed=yes`、`external_dependency != none`、"
            "`contract_surface != none` 或 `joint_acceptance_needed=yes` 时，`merge_gate` 必须为 `integration_check_required`。"
        )
    if str(payload.get("external_dependency") or "").strip().lower() != "none" and integration_touchpoint == "none":
        errors.append("存在跨仓依赖、联合验收或共享 contract surface 时，`integration_touchpoint` 不能为 `none`。")
    if str(payload.get("joint_acceptance_needed") or "").strip().lower() == "yes" and integration_touchpoint == "none":
        errors.append("存在跨仓依赖、联合验收或共享 contract surface 时，`integration_touchpoint` 不能为 `none`。")
    if str(payload.get("contract_surface") or "").strip().lower() != "none" and integration_touchpoint == "none":
        errors.append("`contract_surface != none` 时，`integration_touchpoint` 不能为 `none`。")

    if merge_gate != "integration_check_required":
        if not integration_ref:
            errors.append("Issue canonical integration 元数据中的 `integration_ref` 不能为空；纯本仓库事项请显式填写 `none`。")
        elif normalize_integration_value("integration_ref", integration_ref) != "none" and not integration_ref_is_checkable(integration_ref):
            errors.append("Issue canonical integration 元数据中的 `integration_ref` 必须使用可核查的具体 integration issue / item 引用。")
        elif normalize_integration_value("integration_ref", integration_ref) != "none":
            errors.append("Issue canonical integration 元数据中 `merge_gate=local_only` 时必须显式使用 `integration_ref=none`。")
        return errors

    if integration_touchpoint == "none":
        errors.append("`merge_gate=integration_check_required` 时，`integration_touchpoint` 不能为 `none`。")
    if not integration_ref or not integration_ref_is_checkable(integration_ref):
        errors.append("`merge_gate=integration_check_required` 时，`integration_ref` 必须指向具体 integration issue / item。")
    return errors


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
    payload = decode_remote_json(
        completed.stdout,
        error_message=f"无法解析 Issue #{issue_number} 的 canonical integration 元数据响应，拒绝继续。",
    )
    if payload.get("error"):
        return IssueCanonicalResolution(
            issue_number=issue_number,
            canonical={},
            error=str(payload["error"]),
        )
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
    contract_errors = validate_issue_canonical_payload(canonical)
    if contract_errors:
        return IssueCanonicalResolution(
            issue_number=issue_number,
            canonical=canonical,
            error=contract_errors[0],
        )
    return IssueCanonicalResolution(issue_number=issue_number, canonical=canonical, error=None)


def build_review_packet(
    body: str,
    *,
    issue_number: int | None,
    issue_canonical: Mapping[str, str],
    issue_error: str | None,
    integration_ref_live: Mapping[str, object] | None = None,
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
        field: normalize_integration_value_for_packet(field, issue_canonical.get(field, ""))
        for field in ISSUE_SCOPE_FIELDS
        if str(issue_canonical.get(field) or "").strip()
    }
    normalized_pr = {
        field: normalize_integration_value_for_packet(field, pr_payload.get(field, ""))
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
    packet_integration_ref_live = dict(integration_ref_live or {})
    integration_ref_live_errors = (
        validate_integration_ref_live_state(
            pr_payload,
            packet_integration_ref_live,
            current_repo_slug=default_github_repo(),
        )
        if integration_ref_live is not None
        else []
    )
    if integration_ref_live_errors:
        merge_validation_errors = [*merge_validation_errors, *[item for item in integration_ref_live_errors if item not in merge_validation_errors]]
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
        "integration_ref_live": packet_integration_ref_live,
        "integration_ref_live_errors": integration_ref_live_errors,
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
    integration_ref_live = packet.get("integration_ref_live") or {}
    if integration_ref_live:
        lines.append("- integration_ref_live:")
        for key in (
            "source",
            "status",
            "dependency_order",
            "joint_acceptance",
            "contract_status",
            "owner_repo",
            "url",
            "project_url",
            "error",
        ):
            value = str(integration_ref_live.get(key) or "").strip()
            if value:
                lines.append(f"  - {key}: {value}")
    else:
        lines.append("- integration_ref_live: none")
    integration_ref_live_errors = packet.get("integration_ref_live_errors") or []
    if integration_ref_live_errors:
        lines.append("- integration_ref_live_validation:")
        lines.extend([f"  - {item}" for item in integration_ref_live_errors])
    merge_validation_errors = packet.get("merge_validation_errors") or []
    if merge_validation_errors:
        lines.append("- merge_gate_validation:")
        lines.extend([f"  - {item}" for item in merge_validation_errors])
    else:
        lines.append("- merge_gate_validation: ok")
    lines.append(f"- merge_gate: {packet.get('merge_gate') or 'none'}")
    lines.append(f"- merge_gate_requires_recheck: {'yes' if packet.get('merge_gate_requires_recheck') else 'no'}")
    return lines
