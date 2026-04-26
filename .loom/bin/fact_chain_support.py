#!/usr/bin/env python3
"""Shared fact-chain parsing and verification helpers for Loom bootstrap artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+\s*)?$")
KEY_VALUE_BULLET_RE = re.compile(r"^- ([^:]+):\s*(.+?)\s*$")
PLAIN_BULLET_RE = re.compile(r"^- (.+?)\s*$")

STATIC_FACT_FIELDS = {
    "Item ID": "item_id",
    "Goal": "goal",
    "Scope": "scope",
    "Execution Path": "execution_path",
    "Workspace Entry": "workspace_entry",
    "Recovery Entry": "recovery_entry",
    "Review Entry": "review_entry",
    "Validation Entry": "validation_entry",
    "Closing Condition": "closing_condition",
}

DYNAMIC_FACT_FIELDS = {
    "Item ID": "item_id",
    "Current Checkpoint": "current_checkpoint",
    "Current Stop": "current_stop",
    "Next Step": "next_step",
    "Blockers": "blockers",
    "Latest Validation Summary": "latest_validation_summary",
    "Recovery Boundary": "recovery_boundary",
    "Current Lane": "current_lane",
}

STATUS_FIELDS = {
    "Item ID": "item_id",
    "Goal": "goal",
    "Scope": "scope",
    "Execution Path": "execution_path",
    "Workspace Entry": "workspace_entry",
    "Recovery Entry": "recovery_entry",
    "Review Entry": "review_entry",
    "Validation Entry": "validation_entry",
    "Closing Condition": "closing_condition",
    "Current Checkpoint": "current_checkpoint",
    "Current Stop": "current_stop",
    "Next Step": "next_step",
    "Blockers": "blockers",
    "Latest Validation Summary": "latest_validation_summary",
    "Recovery Boundary": "recovery_boundary",
    "Current Lane": "current_lane",
}

STATUS_SOURCE_FIELDS = {
    "Static Truth": "work_item",
    "Dynamic Truth": "recovery_entry",
    "Locator Truth": "init_result",
    "Fact Chain CLI": "read_entry",
}

RUNTIME_EVIDENCE_FIELDS = {
    "Run Entry": "run_entry",
    "Logs Entry": "logs_entry",
    "Diagnostics Entry": "diagnostics_entry",
    "Verification Entry": "verification_entry",
    "Lane Entry": "lane_entry",
}

FORBIDDEN_DYNAMIC_KEYS = {
    "current_checkpoint",
    "current_stop",
    "next_step",
    "blockers",
    "latest_validation_summary",
    "recovery_boundary",
    "current_lane",
}

FORBIDDEN_STATIC_KEYS = {
    "goal",
    "scope",
    "execution_path",
    "workspace_entry",
    "recovery_entry",
    "review_entry",
    "validation_entry",
    "closing_condition",
}


def load_json_file(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _clean_value(raw: str) -> str:
    value = raw.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        value = value[1:-1].strip()
    return value


def markdown_sections(path: Path) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(raw_line)
        if match:
            current = match.group(2).strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(raw_line.rstrip())
    return sections


def parse_key_value_section(
    sections: dict[str, list[str]],
    section_name: str,
    field_map: dict[str, str],
    relative_path: str,
) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    lines = sections.get(section_name)
    if lines is None:
        return {}, [f"{relative_path}: missing section `{section_name}`"]

    values: dict[str, str] = {}
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = KEY_VALUE_BULLET_RE.match(stripped)
        if not match:
            errors.append(f"{relative_path}: invalid bullet in `{section_name}`: {stripped}")
            continue
        label = match.group(1).strip()
        if label not in field_map:
            errors.append(f"{relative_path}: unexpected field `{label}` in `{section_name}`")
            continue
        values[field_map[label]] = _clean_value(match.group(2))

    for label, canonical in field_map.items():
        if canonical not in values:
            errors.append(f"{relative_path}: missing `{label}` in `{section_name}`")
    return values, errors


def parse_list_section(sections: dict[str, list[str]], section_name: str, relative_path: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    lines = sections.get(section_name)
    if lines is None:
        return [], [f"{relative_path}: missing section `{section_name}`"]

    items: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = PLAIN_BULLET_RE.match(stripped)
        if not match:
            errors.append(f"{relative_path}: invalid bullet in `{section_name}`: {stripped}")
            continue
        items.append(_clean_value(match.group(1)))

    if not items:
        errors.append(f"{relative_path}: `{section_name}` must list at least one item")
    return items, errors


def _relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def resolve_target_relative_path(root: Path, raw_value: object, label: str) -> tuple[Path | None, str | None]:
    if not isinstance(raw_value, str) or not raw_value:
        return None, f"{label} must be a non-empty string"
    raw_path = Path(raw_value)
    if raw_path.is_absolute():
        return None, f"{label} must be relative to target root"
    resolved = (root / raw_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, f"{label} escapes target root: {raw_value}"
    return resolved, None


def validate_item_id(value: object, label: str) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return [f"{label} must be a non-empty string"]
    if value in {".", ".."} or ".." in value or "/" in value or "\\" in value:
        return [f"{label} must not contain path traversal or separators: {value}"]
    if value != value.strip():
        return [f"{label} must not include leading or trailing whitespace"]
    return []


def parse_work_item(path: Path, root: Path) -> tuple[dict[str, object], list[str]]:
    relative_path = _relative(path, root)
    sections = markdown_sections(path)
    static_facts, errors = parse_key_value_section(sections, "Static Facts", STATIC_FACT_FIELDS, relative_path)
    artifacts, artifact_errors = parse_list_section(sections, "Associated Artifacts", relative_path)
    errors.extend(artifact_errors)
    data: dict[str, object] = dict(static_facts)
    data["associated_artifacts"] = artifacts

    for forbidden_key in FORBIDDEN_DYNAMIC_KEYS:
        if forbidden_key in static_facts:
            errors.append(f"{relative_path}: `{forbidden_key}` must not be authored in `Static Facts`")
    errors.extend(validate_item_id(static_facts.get("item_id"), f"{relative_path}: Item ID"))

    return data, errors


def parse_recovery_entry(path: Path, root: Path) -> tuple[dict[str, str], list[str]]:
    relative_path = _relative(path, root)
    sections = markdown_sections(path)
    dynamic_facts, errors = parse_key_value_section(sections, "Dynamic Facts", DYNAMIC_FACT_FIELDS, relative_path)

    for forbidden_key in FORBIDDEN_STATIC_KEYS:
        if forbidden_key in dynamic_facts:
            errors.append(f"{relative_path}: `{forbidden_key}` must not be authored in `Dynamic Facts`")
    errors.extend(validate_item_id(dynamic_facts.get("item_id"), f"{relative_path}: Item ID"))

    return dynamic_facts, errors


def validate_runtime_evidence(runtime_evidence: dict[str, str], relative_path: str) -> list[str]:
    errors: list[str] = []
    for label, canonical in RUNTIME_EVIDENCE_FIELDS.items():
        if canonical not in runtime_evidence:
            continue
        value = runtime_evidence.get(canonical)
        if not isinstance(value, str) or not value:
            errors.append(f"{relative_path}: `{label}` in `Runtime Evidence` must be a non-empty string")
            continue
        if value == "not_applicable":
            continue
        if not value.strip():
            errors.append(f"{relative_path}: `{label}` in `Runtime Evidence` must not be blank")
    return errors


def parse_status_surface(path: Path, root: Path) -> tuple[dict[str, str], dict[str, str], dict[str, str], list[str]]:
    relative_path = _relative(path, root)
    sections = markdown_sections(path)
    status_facts, errors = parse_key_value_section(
        sections,
        "Derived Fact Chain View",
        STATUS_FIELDS,
        relative_path,
    )
    runtime_evidence, runtime_errors = parse_key_value_section(
        sections,
        "Runtime Evidence",
        RUNTIME_EVIDENCE_FIELDS,
        relative_path,
    )
    errors.extend(runtime_errors)
    errors.extend(validate_runtime_evidence(runtime_evidence, relative_path))
    sources, source_errors = parse_key_value_section(sections, "Sources", STATUS_SOURCE_FIELDS, relative_path)
    errors.extend(source_errors)
    return status_facts, runtime_evidence, sources, errors


def _normalize_json_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def find_forbidden_dynamic_keys(payload: object, prefix: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = _normalize_json_key(str(key))
            current_prefix = f"{prefix}.{key}" if prefix else str(key)
            if normalized in FORBIDDEN_DYNAMIC_KEYS:
                errors.append(current_prefix)
            errors.extend(find_forbidden_dynamic_keys(value, current_prefix))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            current_prefix = f"{prefix}[{index}]"
            errors.extend(find_forbidden_dynamic_keys(value, current_prefix))
    return errors


def expected_status_values(
    work_item: dict[str, object],
    recovery_entry: dict[str, str],
) -> dict[str, str]:
    return {
        "item_id": str(work_item["item_id"]),
        "goal": str(work_item["goal"]),
        "scope": str(work_item["scope"]),
        "execution_path": str(work_item["execution_path"]),
        "workspace_entry": str(work_item["workspace_entry"]),
        "recovery_entry": str(work_item["recovery_entry"]),
        "review_entry": str(work_item["review_entry"]),
        "validation_entry": str(work_item["validation_entry"]),
        "closing_condition": str(work_item["closing_condition"]),
        "current_checkpoint": recovery_entry["current_checkpoint"],
        "current_stop": recovery_entry["current_stop"],
        "next_step": recovery_entry["next_step"],
        "blockers": recovery_entry["blockers"],
        "latest_validation_summary": recovery_entry["latest_validation_summary"],
        "recovery_boundary": recovery_entry["recovery_boundary"],
        "current_lane": recovery_entry["current_lane"],
    }


def inspect_fact_chain(
    target_root: Path,
    output_relative: str = ".loom/bootstrap/init-result.json",
) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    output_path, output_error = resolve_target_relative_path(target_root, output_relative, "init-result")
    if output_error or output_path is None:
        return {}, [output_error or "invalid init-result path"]
    if not output_path.exists():
        return {}, [f"missing init-result: {output_relative}"]

    try:
        init_result = load_json_file(output_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {}, [f"invalid init-result JSON: {exc}"]

    fact_chain = init_result.get("fact_chain")
    if not isinstance(fact_chain, dict):
        return {}, ["init-result is missing required section: fact_chain"]

    read_entry = fact_chain.get("read_entry")
    mode = fact_chain.get("mode")
    entry_points = fact_chain.get("entry_points")
    if not isinstance(read_entry, str) or not read_entry:
        errors.append("init-result.fact_chain.read_entry must be a non-empty string")
    if not isinstance(mode, str) or not mode:
        errors.append("init-result.fact_chain.mode must be a non-empty string")
    if not isinstance(entry_points, dict):
        errors.append("init-result.fact_chain.entry_points must be an object")
        entry_points = {}

    forbidden_init_keys = find_forbidden_dynamic_keys(fact_chain, "fact_chain")
    if forbidden_init_keys:
        for key_path in forbidden_init_keys:
            errors.append(f"init-result must not author dynamic execution state at `{key_path}`")

    work_item_ref = entry_points.get("work_item")
    recovery_ref = entry_points.get("recovery_entry")
    status_ref = entry_points.get("status_surface")
    current_item_id = entry_points.get("current_item_id")
    for label, value in (
        ("work_item", work_item_ref),
        ("recovery_entry", recovery_ref),
        ("status_surface", status_ref),
        ("current_item_id", current_item_id),
    ):
        if not isinstance(value, str) or not value:
            errors.append(f"init-result.fact_chain.entry_points.{label} must be a non-empty string")
    errors.extend(validate_item_id(current_item_id, "init-result.fact_chain.entry_points.current_item_id"))

    if errors:
        return {}, errors

    work_item_path, work_item_path_error = resolve_target_relative_path(target_root, work_item_ref, "work_item")
    recovery_path, recovery_path_error = resolve_target_relative_path(target_root, recovery_ref, "recovery_entry")
    status_path, status_path_error = resolve_target_relative_path(target_root, status_ref, "status_surface")
    errors.extend(error for error in (work_item_path_error, recovery_path_error, status_path_error) if error)
    if errors or work_item_path is None or recovery_path is None or status_path is None:
        return {}, errors
    for label, path in (
        ("work_item", work_item_path),
        ("recovery_entry", recovery_path),
        ("status_surface", status_path),
    ):
        if not path.exists():
            errors.append(f"declared fact-chain carrier is missing on disk: {label} -> {_relative(path, target_root)}")
    if errors:
        return {}, errors

    work_item, work_item_errors = parse_work_item(work_item_path, target_root)
    recovery_entry, recovery_errors = parse_recovery_entry(recovery_path, target_root)
    status_surface, runtime_evidence, status_sources, status_errors = parse_status_surface(status_path, target_root)
    errors.extend(work_item_errors)
    errors.extend(recovery_errors)
    errors.extend(status_errors)
    if errors:
        return {}, errors

    if str(work_item["item_id"]) != str(recovery_entry["item_id"]):
        errors.append(
            "work item and recovery entry disagree on item id: "
            f"{work_item['item_id']} vs {recovery_entry['item_id']}"
        )
    if str(work_item["recovery_entry"]) != str(recovery_ref):
        errors.append(
            "work item recovery entry does not match init-result locator: "
            f"{work_item['recovery_entry']} vs {recovery_ref}"
        )
    if str(work_item["item_id"]) != str(current_item_id):
        errors.append(
            "init-result.fact_chain.entry_points.current_item_id does not match work item id: "
            f"{current_item_id} vs {work_item['item_id']}"
        )

    expected_status = expected_status_values(work_item, recovery_entry)
    for field_name, expected_value in expected_status.items():
        actual_value = status_surface.get(field_name)
        if actual_value != expected_value:
            errors.append(
                "status surface mismatch for "
                f"`{field_name}`: expected `{expected_value}`, got `{actual_value}`"
            )

    expected_sources = {
        "work_item": str(work_item_ref),
        "recovery_entry": str(recovery_ref),
        "init_result": output_relative,
        "read_entry": str(read_entry),
    }
    for source_key, expected_value in expected_sources.items():
        actual_value = status_sources.get(source_key)
        if actual_value != expected_value:
            errors.append(
                "status surface source mismatch for "
                f"`{source_key}`: expected `{expected_value}`, got `{actual_value}`"
            )

    runtime_evidence_report = {
        field_name: {
            "value": value,
            "status": "not_applicable" if value == "not_applicable" else "present",
            "source": {
                "carrier": "status_surface",
                "path": str(status_ref),
                "field": label,
            },
        }
        for label, field_name in RUNTIME_EVIDENCE_FIELDS.items()
        for value in (runtime_evidence[field_name],)
    }

    report = {
        "target": str(target_root),
        "fact_chain": {
            "mode": str(mode),
            "read_entry": str(read_entry),
            "init_result": output_relative,
            "entry_points": {
                "current_item_id": str(current_item_id),
                "work_item": str(work_item_ref),
                "recovery_entry": str(recovery_ref),
                "status_surface": str(status_ref),
            },
        },
        "facts": {
            "item_id": {
                "value": str(work_item["item_id"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Item ID"},
            },
            "goal": {
                "value": str(work_item["goal"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Goal"},
            },
            "scope": {
                "value": str(work_item["scope"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Scope"},
            },
            "execution_path": {
                "value": str(work_item["execution_path"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Execution Path"},
            },
            "associated_artifacts": {
                "value": list(work_item["associated_artifacts"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Associated Artifacts"},
            },
            "workspace_entry": {
                "value": str(work_item["workspace_entry"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Workspace Entry"},
            },
            "recovery_entry": {
                "value": str(work_item["recovery_entry"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Recovery Entry"},
            },
            "review_entry": {
                "value": str(work_item["review_entry"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Review Entry"},
            },
            "validation_entry": {
                "value": str(work_item["validation_entry"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Validation Entry"},
            },
            "closing_condition": {
                "value": str(work_item["closing_condition"]),
                "source": {"carrier": "work_item", "path": str(work_item_ref), "field": "Closing Condition"},
            },
            "current_checkpoint": {
                "value": recovery_entry["current_checkpoint"],
                "source": {"carrier": "recovery_entry", "path": str(recovery_ref), "field": "Current Checkpoint"},
            },
            "current_stop": {
                "value": recovery_entry["current_stop"],
                "source": {"carrier": "recovery_entry", "path": str(recovery_ref), "field": "Current Stop"},
            },
            "next_step": {
                "value": recovery_entry["next_step"],
                "source": {"carrier": "recovery_entry", "path": str(recovery_ref), "field": "Next Step"},
            },
            "blockers": {
                "value": recovery_entry["blockers"],
                "source": {"carrier": "recovery_entry", "path": str(recovery_ref), "field": "Blockers"},
            },
            "latest_validation_summary": {
                "value": recovery_entry["latest_validation_summary"],
                "source": {
                    "carrier": "recovery_entry",
                    "path": str(recovery_ref),
                    "field": "Latest Validation Summary",
                },
            },
            "recovery_boundary": {
                "value": recovery_entry["recovery_boundary"],
                "source": {"carrier": "recovery_entry", "path": str(recovery_ref), "field": "Recovery Boundary"},
            },
            "current_lane": {
                "value": recovery_entry["current_lane"],
                "source": {"carrier": "recovery_entry", "path": str(recovery_ref), "field": "Current Lane"},
            },
        },
        "runtime_evidence": runtime_evidence_report,
        "derived_status_surface": {
            "path": str(status_ref),
            "values": expected_status,
            "runtime_evidence": runtime_evidence,
            "sources": expected_sources,
        },
    }
    return report, errors
