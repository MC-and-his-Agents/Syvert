#!/usr/bin/env python3
"""Shared governance-surface detection for Loom bootstrap, route, and resume."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

from runtime_paths import installed_skill_script

CARRIER_KEYS = (
    "work_item",
    "recovery",
    "review",
    "status_surface",
    "spec_path",
    "plan_path",
)

PLANNED_LOCATORS = {
    "work_item": ".loom/work-items/INIT-0001.md",
    "recovery": ".loom/progress/INIT-0001.md",
    "review": ".loom/reviews/INIT-0001.json",
    "status_surface": ".loom/status/current.md",
    "spec_path": ".loom/specs/INIT-0001/spec.md",
    "plan_path": ".loom/specs/INIT-0001/plan.md",
}

REPO_INTERFACE_SURFACES = ("admission", "review", "merge_ready", "closeout")
REPO_INTERFACE_AVAILABILITY = {"absent", "companion_docs_only", "incomplete", "present"}
REPO_INTERFACE_MANIFEST_SCHEMA = "loom-repo-companion-manifest/v1"
REPO_INTERFACE_V1_SCHEMA = "loom-repo-interface/v1"
REPO_INTERFACE_V2_SCHEMA = "loom-repo-interface/v2"
REPO_INTERFACE_SCHEMAS = {REPO_INTERFACE_V1_SCHEMA, REPO_INTERFACE_V2_SCHEMA}
REPO_INTERFACE_ENFORCEMENT = {"blocking", "advisory"}
REPO_INTERFACE_GATE_TYPES = {
    "admission",
    "pre_review",
    "review",
    "build",
    "merge_ready",
    "closeout",
}
REPO_INTERFACE_CONTEXT_TYPES = {"string", "integer", "number", "boolean"}
REPO_INTERFACE_MANIFEST_KEYS = {"schema_version", "companion_entry", "repo_interface"}
REPO_INTERFACE_V1_KEYS = {"schema_version", "companion_entry", "repo_specific_requirements", "specialized_gates"}
REPO_INTERFACE_V2_KEYS = REPO_INTERFACE_V1_KEYS | {"metadata_contract", "context_schema"}
REPO_INTEROP_AVAILABILITY = {"absent", "incomplete", "present"}
REPO_INTEROP_SCHEMA = "loom-repo-interop/v1"
REPO_INTEROP_KEYS = {"schema_version", "host_adapters", "repo_native_carriers", "shadow_surfaces"}
REPO_INTEROP_COLLECTION_SURFACES = {
    "admission",
    "pre_review",
    "review",
    "build",
    "merge_ready",
    "closeout",
}
REPO_INTEROP_SHADOW_SURFACES = ("admission", "review", "merge_ready", "closeout")
GOVERNANCE_CONTROL_VERSION = "loom-governance-control/v1"
HOST_BINDING_OBJECTS = (
    "phase",
    "fr",
    "work_item",
    "branch",
    "worktree",
    "implementation_pr",
    "merge_commit",
    "closeout",
)
WORK_ITEM_ENFORCEMENT_FALLBACKS = {
    "roadmap": "phase",
    "phase": "fr",
    "fr": "work_item",
    "implementation_pr": "work_item",
    "merge_commit": "closeout",
}
GATE_FAILURE_TAXONOMY = {
    "spec_stale": "Approved spec no longer covers the implementation surface.",
    "review_stale": "Implementation review no longer covers the current head or scope.",
    "head_drift": "The head SHA changed after an approval gate was recorded.",
    "host_signal_drift": "GitHub issue, PR, project, branch, or check state no longer agrees with Loom's local carriers.",
    "gate_failure": "A required predecessor gate is missing, blocking, or unreadable.",
    "closeout_reconciliation_drift": "Merged work and issue/project closeout state are not yet aligned.",
}
GATE_CHAIN = (
    {
        "id": "work_item_admission",
        "requires": [],
        "fallback_to": "admission",
    },
    {
        "id": "spec_gate",
        "requires": ["work_item_admission", "formal_spec_or_not_applicable", "spec_review_approved"],
        "fallback_to": "admission",
    },
    {
        "id": "build_gate",
        "requires": ["work_item_admission", "spec_gate", "head_sha", "validation_summary", "approved_scope"],
        "fallback_to": "build",
    },
    {
        "id": "review_gate",
        "requires": ["build_gate", "head_sha", "validation_summary", "single_review_record"],
        "fallback_to": "review",
    },
    {
        "id": "merge_gate",
        "requires": ["review_gate", "head_binding", "validation_summary", "no_stale_or_drift"],
        "fallback_to": "merge",
    },
    {
        "id": "github_controlled_merge",
        "requires": ["merge_gate", "required_checks", "branch_protection", "merge_policy"],
        "fallback_to": "merge",
    },
    {
        "id": "closeout",
        "requires": ["github_controlled_merge", "merge_commit", "target_main", "reconciliation_audit"],
        "fallback_to": "reconciliation-sync",
    },
)
MATURITY_LEVELS = {
    "light": {
        "requires": ["work_item", "recovery", "status_surface", "review"],
        "summary": "Minimal Work Item -> review -> merge-ready governance is available.",
    },
    "standard": {
        "requires": [
            "light",
            "fr_work_item_layer",
            "spec_path",
            "plan_path",
            "spec_gate",
            "status_control_plane",
            "basic_host_binding",
            "closeout_reconciliation_read",
        ],
        "summary": "Formal spec, spec gate, status control plane, basic host binding, and closeout/reconciliation reads are available.",
    },
    "strong": {
        "requires": ["standard", "repo_interface", "repo_interop", "github_controlled_merge"],
        "summary": "Host-backed binding, reconciliation, controlled merge, and closeout gates are available.",
    },
}
MATURITY_REQUIRED_FIELDS = {
    "light": [
        {
            "id": "work_item",
            "layer": "core",
            "required": True,
            "defaulting": "generated",
            "recommended_action": "run loom-init or restore the Work Item carrier",
        },
        {
            "id": "recovery",
            "layer": "core",
            "required": True,
            "defaulting": "generated",
            "recommended_action": "restore the recovery carrier",
        },
        {
            "id": "status_surface",
            "layer": "core",
            "required": True,
            "defaulting": "generated",
            "recommended_action": "restore the status surface carrier",
        },
        {
            "id": "review",
            "layer": "core",
            "required": True,
            "defaulting": "generated",
            "recommended_action": "restore the review carrier",
        },
    ],
    "standard": [
        {
            "id": "fr_work_item_layer",
            "layer": "github-profile",
            "required": True,
            "defaulting": "profile",
            "recommended_action": "declare the FR -> Work Item split through the GitHub profile upgrade path",
        },
        {
            "id": "spec_path",
            "layer": "core",
            "required": True,
            "defaulting": "generated",
            "recommended_action": "install formal spec scaffold",
        },
        {
            "id": "plan_path",
            "layer": "core",
            "required": True,
            "defaulting": "generated",
            "recommended_action": "install execution plan scaffold",
        },
        {
            "id": "spec_gate",
            "layer": "core",
            "required": True,
            "defaulting": "generated",
            "recommended_action": "record or restore the spec review gate",
        },
        {
            "id": "status_control_plane",
            "layer": "core",
            "required": True,
            "defaulting": "builtin",
            "recommended_action": "run loom_status or loom_check to rebuild the status control plane",
        },
        {
            "id": "basic_host_binding",
            "layer": "github-profile",
            "required": True,
            "defaulting": "profile",
            "recommended_action": "run governance-profile binding and repair missing host bindings",
        },
        {
            "id": "closeout_reconciliation_read",
            "layer": "github-profile",
            "required": True,
            "defaulting": "profile",
            "recommended_action": "install repo interop so closeout can consume reconciliation",
        },
    ],
    "strong": [
        {
            "id": "repo_interface",
            "layer": "repo-owned-residue",
            "required": True,
            "defaulting": "scaffold",
            "recommended_action": "install or repair the repo companion interface",
        },
        {
            "id": "repo_interop",
            "layer": "repo-owned-residue",
            "required": True,
            "defaulting": "scaffold",
            "recommended_action": "install or repair the repo interop contract",
        },
        {
            "id": "github_controlled_merge",
            "layer": "github-profile",
            "required": True,
            "defaulting": "host",
            "recommended_action": "enable controlled merge binding and required host gates",
        },
    ],
}


def run_process(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args=args, returncode=124, stdout="", stderr="command timed out after 15s")


def file_exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def relative_locator(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def safe_read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def command_prefix(root: Path, tool_name: str) -> str:
    loom_tool = root / ".loom/bin" / tool_name
    if loom_tool.exists():
        return f"python3 .loom/bin/{tool_name}"
    if tool_name == "loom_init.py":
        return f"python3 {installed_skill_script(__file__, 'loom-init')}"
    if tool_name == "loom_flow.py":
        return f"python3 {installed_skill_script(__file__, 'loom-resume')}"
    return "unknown"


def git_remote_origin(root: Path) -> str | None:
    result = run_process(["git", "remote", "get-url", "origin"], root)
    if result.returncode != 0:
        return None
    remote = result.stdout.strip()
    return remote or None


def detect_github_repo(root: Path) -> tuple[str | None, str | None]:
    remote = git_remote_origin(root)
    if not remote:
        return None, None
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", remote)
    if not match:
        return None, None
    return match.group("owner"), match.group("repo")


def gh_json(root: Path, args: list[str]) -> tuple[dict[str, Any] | None, list[str]]:
    result = run_process(["gh", *args], root)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "gh command failed"
        return None, [detail]
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON from gh {' '.join(args)}: {exc.msg}"]
    if not isinstance(payload, dict):
        return None, [f"gh {' '.join(args)} did not return a JSON object"]
    return payload, []


def gh_rest_json(root: Path, path: str) -> tuple[dict[str, Any] | None, list[str]]:
    return gh_json(root, ["api", path])


def detect_loom_state(root: Path) -> str:
    active_requirements = (
        root / ".loom/bootstrap/init-result.json",
        root / ".loom/work-items",
        root / ".loom/progress",
        root / ".loom/status/current.md",
    )
    if all(path.exists() for path in active_requirements):
        return "active"

    partial_markers = (
        root / ".loom",
        root / "AGENTS.md",
        root / ".github/PULL_REQUEST_TEMPLATE.md",
    )
    if any(path.exists() for path in partial_markers):
        return "partial"
    return "absent"


def detect_repository_mode(root: Path, loom_state: str, scenario_override: str | None = None) -> str:
    if scenario_override in {"new", "small-existing", "complex-existing"}:
        return scenario_override

    init_result = safe_read_json(root / ".loom/bootstrap/init-result.json")
    if isinstance(init_result, dict):
        run = init_result.get("run")
        if isinstance(run, dict):
            scenario_key = run.get("scenario_key")
            if scenario_key in {"new", "small-existing", "complex-existing"}:
                return str(scenario_key)

    code_dirs = ("src", "app", "lib", "cmd", "pkg", "services", "packages")
    boundary_files = (
        "README.md",
        "AGENTS.md",
        "WORKFLOW.md",
        "docs/WORKFLOW.md",
        "package.json",
        "pyproject.toml",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        ".github/workflows",
    )
    baseline_count = sum(1 for entry in boundary_files if file_exists(root, entry))
    code_count = sum(1 for entry in code_dirs if file_exists(root, entry))

    meaningful_entries = 0
    for path in root.iterdir():
        if path.name in {".git", ".DS_Store"}:
            continue
        if path.name == ".loom" and loom_state != "absent":
            continue
        meaningful_entries += 1

    if loom_state == "absent" and meaningful_entries <= 2 and baseline_count <= 1 and code_count == 0:
        return "new"
    if baseline_count + code_count >= 4 or meaningful_entries >= 8:
        return "complex-existing"
    return "small-existing"


def carrier_entry(status: str, locator: str, source: str) -> dict[str, str]:
    return {"status": status, "locator": locator, "source": source}


def has_legacy_companion_docs(root: Path) -> bool:
    companion_dir = root / ".loom" / "companion"
    if not companion_dir.exists() or not companion_dir.is_dir():
        return False
    for path in companion_dir.iterdir():
        if path.name in {"manifest.json", "repo-interface.json"}:
            continue
        if path.suffix.lower() == ".md":
            return True
    return False


def relative_locator_from_value(root: Path, raw_locator: object) -> str | None:
    if not isinstance(raw_locator, str):
        return None
    locator = raw_locator.strip()
    if not locator:
        return None
    locator_path = Path(locator)
    if locator_path.is_absolute():
        try:
            return str(locator_path.resolve().relative_to(root.resolve()))
        except ValueError:
            return None
    resolved = (root / locator_path).resolve()
    try:
        return str(resolved.relative_to(root.resolve()))
    except ValueError:
        return None


def resolve_locator(root: Path, raw_locator: object) -> tuple[str | None, Path | None]:
    locator = relative_locator_from_value(root, raw_locator)
    if locator is None:
        return None, None
    return locator, (root / locator).resolve()


def locator_status_entry(
    *,
    root: Path,
    raw_locator: object,
    source: str,
) -> tuple[dict[str, str], str | None]:
    locator, target = resolve_locator(root, raw_locator)
    if locator is None or target is None:
        return carrier_entry("missing", "unknown", source), f"{source} is missing a valid locator"
    if not target.exists():
        return carrier_entry("missing", locator, source), f"{source} points to missing path `{locator}`"
    return carrier_entry("present", locator, source), None


def validate_repo_specific_requirement(
    *,
    root: Path,
    surface: str,
    entry: object,
    index: int,
) -> list[str]:
    prefix = f"repo_interface.{surface}[{index}]"
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]
    missing_inputs: list[str] = []
    for field in ("id", "summary", "locator", "enforcement"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            missing_inputs.append(f"{prefix} missing `{field}`")
    enforcement = entry.get("enforcement")
    if enforcement not in REPO_INTERFACE_ENFORCEMENT:
        missing_inputs.append(f"{prefix} enforcement must be `blocking` or `advisory`")
    locator, target = resolve_locator(root, entry.get("locator"))
    if locator is None or target is None:
        missing_inputs.append(f"{prefix} locator must be a non-empty string")
    elif not target.exists():
        missing_inputs.append(f"{prefix} locator points to missing path `{locator}`")
    return missing_inputs


def validate_specialized_gate(
    *,
    root: Path,
    entry: object,
    index: int,
) -> list[str]:
    prefix = f"specialized_gates[{index}]"
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]
    missing_inputs: list[str] = []
    for field in ("id", "summary", "locator"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            missing_inputs.append(f"{prefix} missing `{field}`")
    locator, target = resolve_locator(root, entry.get("locator"))
    if locator is None or target is None:
        missing_inputs.append(f"{prefix} locator must be a non-empty string")
    elif not target.exists():
        missing_inputs.append(f"{prefix} locator points to missing path `{locator}`")
    gate_type = entry.get("gate_type")
    if gate_type is not None and gate_type not in REPO_INTERFACE_GATE_TYPES:
        missing_inputs.append(
            f"{prefix} gate_type must be one of `admission`, `pre_review`, `review`, `build`, `merge_ready`, `closeout`"
        )
    return missing_inputs


def validate_metadata_contract(
    *,
    root: Path,
    entry: object,
) -> list[str]:
    prefix = "metadata_contract"
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]
    fields = entry.get("fields")
    if not isinstance(fields, list):
        return [f"{prefix} must include `fields` as a list"]
    missing_inputs: list[str] = []
    for index, field in enumerate(fields):
        field_prefix = f"{prefix}.fields[{index}]"
        if not isinstance(field, dict):
            missing_inputs.append(f"{field_prefix} must be an object")
            continue
        for required in ("id", "summary", "applicability_locator", "authority_locator", "enforcement"):
            value = field.get(required)
            if required == "enforcement":
                continue
            if not isinstance(value, str) or not value.strip():
                missing_inputs.append(f"{field_prefix} missing `{required}`")
        enforcement = field.get("enforcement")
        if enforcement not in REPO_INTERFACE_ENFORCEMENT:
            missing_inputs.append(f"{field_prefix} enforcement must be `blocking` or `advisory`")
        for locator_field in ("applicability_locator", "authority_locator"):
            locator, target = resolve_locator(root, field.get(locator_field))
            if locator is None or target is None:
                missing_inputs.append(f"{field_prefix} `{locator_field}` must be a non-empty string")
            elif not target.exists():
                missing_inputs.append(f"{field_prefix} `{locator_field}` points to missing path `{locator}`")
    return missing_inputs


def validate_context_schema(
    *,
    root: Path,
    entry: object,
) -> list[str]:
    prefix = "context_schema"
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]
    fields = entry.get("fields")
    if not isinstance(fields, list):
        return [f"{prefix} must include `fields` as a list"]
    missing_inputs: list[str] = []
    for index, field in enumerate(fields):
        field_prefix = f"{prefix}.fields[{index}]"
        if not isinstance(field, dict):
            missing_inputs.append(f"{field_prefix} must be an object")
            continue
        for required in ("id", "summary", "type", "mapping_rule_locator"):
            value = field.get(required)
            if not isinstance(value, str) or not value.strip():
                missing_inputs.append(f"{field_prefix} missing `{required}`")
        field_type = field.get("type")
        if field_type not in REPO_INTERFACE_CONTEXT_TYPES:
            missing_inputs.append(f"{field_prefix} type must be one of `string`, `integer`, `number`, `boolean`")
        if not isinstance(field.get("required"), bool):
            missing_inputs.append(f"{field_prefix} `required` must be a boolean")
        locator, target = resolve_locator(root, field.get("mapping_rule_locator"))
        if locator is None or target is None:
            missing_inputs.append(f"{field_prefix} `mapping_rule_locator` must be a non-empty string")
        elif not target.exists():
            missing_inputs.append(f"{field_prefix} `mapping_rule_locator` points to missing path `{locator}`")
    return missing_inputs


def validate_repo_interop_collection_entry(
    *,
    root: Path,
    collection: str,
    entry: object,
    index: int,
) -> list[str]:
    prefix = f"{collection}[{index}]"
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]
    missing_inputs: list[str] = []
    for field in ("id", "summary", "locator"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            missing_inputs.append(f"{prefix} missing `{field}`")
    surfaces = entry.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        missing_inputs.append(f"{prefix} must include `surfaces` as a non-empty list")
    else:
        for surface_index, surface in enumerate(surfaces):
            if surface not in REPO_INTEROP_COLLECTION_SURFACES:
                missing_inputs.append(
                    f"{prefix}.surfaces[{surface_index}] must be one of `admission`, `pre_review`, `review`, `build`, `merge_ready`, `closeout`"
                )
    locator, target = resolve_locator(root, entry.get("locator"))
    if locator is None or target is None:
        missing_inputs.append(f"{prefix} locator must be a non-empty string")
    elif not target.exists():
        missing_inputs.append(f"{prefix} locator points to missing path `{locator}`")
    return missing_inputs


def validate_shadow_surface(
    *,
    root: Path,
    surface: str,
    entry: object,
) -> list[str]:
    prefix = f"shadow_surfaces.{surface}"
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]
    missing_inputs: list[str] = []
    summary = entry.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        missing_inputs.append(f"{prefix} missing `summary`")
    for locator_field in ("loom_locator", "repo_locator"):
        locator, target = resolve_locator(root, entry.get(locator_field))
        if locator is None or target is None:
            missing_inputs.append(f"{prefix} `{locator_field}` must be a non-empty string")
        elif not target.exists():
            missing_inputs.append(f"{prefix} `{locator_field}` points to missing path `{locator}`")
    return missing_inputs


def detect_repo_interface(root: Path) -> tuple[dict[str, Any], list[str]]:
    companion_dir = root / ".loom" / "companion"
    manifest_path = companion_dir / "manifest.json"
    repo_interface_path = companion_dir / "repo-interface.json"

    repo_interface_surface: dict[str, Any] = {
        "availability": "absent",
        "manifest": carrier_entry("missing", ".loom/companion/manifest.json", "companion manifest"),
        "companion_entry": carrier_entry("missing", "unknown", "repo companion manifest"),
        "repo_specific_requirements": carrier_entry("missing", "unknown", "repo companion interface"),
        "specialized_gates": carrier_entry("missing", "unknown", "repo companion interface"),
        "summary": "no repo companion interface is declared for this repository.",
        "missing_inputs": [],
    }
    missing_inputs: list[str] = []

    if not manifest_path.exists():
        if has_legacy_companion_docs(root):
            repo_interface_surface["availability"] = "companion_docs_only"
            repo_interface_surface["summary"] = (
                "legacy companion docs are present, but no machine-readable repo companion manifest is declared."
            )
        return repo_interface_surface, missing_inputs

    repo_interface_surface["manifest"] = carrier_entry(
        "present",
        ".loom/companion/manifest.json",
        "repository scan",
    )
    manifest = safe_read_json(manifest_path)
    if manifest is None:
        missing_inputs.append("repo companion manifest is unreadable")
        repo_interface_surface["availability"] = "incomplete"
        repo_interface_surface["summary"] = "repo companion manifest exists, but the machine-readable interface is incomplete."
        repo_interface_surface["missing_inputs"] = missing_inputs
        return repo_interface_surface, missing_inputs

    if manifest.get("schema_version") != REPO_INTERFACE_MANIFEST_SCHEMA:
        missing_inputs.append(
            f"repo companion manifest schema must be `{REPO_INTERFACE_MANIFEST_SCHEMA}`"
        )
    extra_manifest_keys = sorted(set(manifest.keys()) - REPO_INTERFACE_MANIFEST_KEYS)
    if extra_manifest_keys:
        missing_inputs.append(
            "repo companion manifest must stay locator-only: "
            + ", ".join(extra_manifest_keys)
        )

    companion_entry, companion_error = locator_status_entry(
        root=root,
        raw_locator=manifest.get("companion_entry"),
        source="repo companion manifest.companion_entry",
    )
    repo_interface_surface["companion_entry"] = companion_entry
    if companion_error:
        missing_inputs.append(companion_error)

    manifest_repo_interface, manifest_repo_interface_error = locator_status_entry(
        root=root,
        raw_locator=manifest.get("repo_interface"),
        source="repo companion manifest.repo_interface",
    )
    repo_interface_surface["repo_specific_requirements"] = manifest_repo_interface
    repo_interface_surface["specialized_gates"] = manifest_repo_interface.copy()
    if manifest_repo_interface_error:
        missing_inputs.append(manifest_repo_interface_error)

    repo_interface_locator, repo_interface_target = resolve_locator(root, manifest.get("repo_interface"))
    if repo_interface_surface["repo_specific_requirements"]["status"] != "present":
        if repo_interface_path.exists() and manifest_repo_interface_error:
            missing_inputs.append("repo companion manifest must point `repo_interface` to `.loom/companion/repo-interface.json`")
    else:
        interface_payload = safe_read_json(repo_interface_target or repo_interface_path)
        if interface_payload is None:
            missing_inputs.append("repo companion interface is unreadable")
        else:
            interface_schema = interface_payload.get("schema_version")
            if interface_schema not in REPO_INTERFACE_SCHEMAS:
                missing_inputs.append(
                    "repo companion interface schema must be `loom-repo-interface/v1` or `loom-repo-interface/v2`"
                )
            allowed_interface_keys = (
                REPO_INTERFACE_V2_KEYS if interface_schema == REPO_INTERFACE_V2_SCHEMA else REPO_INTERFACE_V1_KEYS
            )
            extra_interface_keys = sorted(set(interface_payload.keys()) - allowed_interface_keys)
            if extra_interface_keys:
                missing_inputs.append(
                    "repo companion interface contains unexpected top-level fields: "
                    + ", ".join(extra_interface_keys)
                )
            interface_companion_entry, interface_companion_error = locator_status_entry(
                root=root,
                raw_locator=interface_payload.get("companion_entry"),
                source="repo companion interface.companion_entry",
            )
            if interface_companion_entry["status"] == "present":
                repo_interface_surface["companion_entry"] = interface_companion_entry
            if interface_companion_error:
                missing_inputs.append(interface_companion_error)

            requirements = interface_payload.get("repo_specific_requirements")
            if not isinstance(requirements, dict):
                missing_inputs.append("repo companion interface must include `repo_specific_requirements`")
            else:
                for surface in REPO_INTERFACE_SURFACES:
                    entries = requirements.get(surface)
                    if not isinstance(entries, list):
                        missing_inputs.append(
                            f"repo companion interface surface `{surface}` must be a list"
                        )
                        continue
                    for index, entry in enumerate(entries):
                        missing_inputs.extend(
                            validate_repo_specific_requirement(
                                root=root,
                                surface=surface,
                                entry=entry,
                                index=index,
                            )
                        )

            specialized_gates = interface_payload.get("specialized_gates")
            if not isinstance(specialized_gates, list):
                missing_inputs.append("repo companion interface must include `specialized_gates` as a list")
            else:
                for index, entry in enumerate(specialized_gates):
                    missing_inputs.extend(
                        validate_specialized_gate(
                            root=root,
                            entry=entry,
                            index=index,
                        )
                    )

            if interface_schema == REPO_INTERFACE_V2_SCHEMA:
                metadata_contract = interface_payload.get("metadata_contract")
                if metadata_contract is not None:
                    missing_inputs.extend(
                        validate_metadata_contract(
                            root=root,
                            entry=metadata_contract,
                        )
                    )
                context_schema = interface_payload.get("context_schema")
                if context_schema is not None:
                    missing_inputs.extend(
                        validate_context_schema(
                            root=root,
                            entry=context_schema,
                        )
                    )

    if missing_inputs:
        repo_interface_surface["availability"] = "incomplete"
        repo_interface_surface["summary"] = (
            "repo companion manifest exists, but the machine-readable interface is incomplete."
        )
    else:
        repo_interface_surface["availability"] = "present"
        repo_interface_surface["summary"] = (
            "repo companion manifest and machine-readable repo interface are readable."
        )
    repo_interface_surface["missing_inputs"] = list(dict.fromkeys(missing_inputs))
    return repo_interface_surface, list(dict.fromkeys(missing_inputs))


def detect_repo_interop(root: Path) -> tuple[dict[str, Any], list[str]]:
    interop_path = root / ".loom" / "companion" / "interop.json"
    repo_interop_surface: dict[str, Any] = {
        "availability": "absent",
        "contract": carrier_entry("missing", ".loom/companion/interop.json", "repository scan"),
        "host_adapters": carrier_entry("missing", "unknown", "repo interop contract"),
        "repo_native_carriers": carrier_entry("missing", "unknown", "repo interop contract"),
        "shadow_surfaces": carrier_entry("missing", "unknown", "repo interop contract"),
        "summary": "no repo interop contract is declared for this repository.",
        "missing_inputs": [],
    }
    missing_inputs: list[str] = []

    if not interop_path.exists():
        return repo_interop_surface, missing_inputs

    repo_interop_surface["contract"] = carrier_entry(
        "present",
        ".loom/companion/interop.json",
        "repository scan",
    )
    interop_payload = safe_read_json(interop_path)
    if interop_payload is None:
        missing_inputs.append("repo interop contract is unreadable")
    else:
        if interop_payload.get("schema_version") != REPO_INTEROP_SCHEMA:
            missing_inputs.append(f"repo interop contract schema must be `{REPO_INTEROP_SCHEMA}`")
        extra_keys = sorted(set(interop_payload.keys()) - REPO_INTEROP_KEYS)
        if extra_keys:
            missing_inputs.append(
                "repo interop contract contains unexpected top-level fields: "
                + ", ".join(extra_keys)
            )

        for key in ("host_adapters", "repo_native_carriers", "shadow_surfaces"):
            repo_interop_surface[key] = carrier_entry(
                "present",
                ".loom/companion/interop.json",
                "repo interop contract",
            )

        host_adapters = interop_payload.get("host_adapters")
        if not isinstance(host_adapters, list):
            missing_inputs.append("repo interop contract must include `host_adapters` as a list")
        else:
            for index, entry in enumerate(host_adapters):
                missing_inputs.extend(
                    validate_repo_interop_collection_entry(
                        root=root,
                        collection="host_adapters",
                        entry=entry,
                        index=index,
                    )
                )

        repo_native_carriers = interop_payload.get("repo_native_carriers")
        if not isinstance(repo_native_carriers, list):
            missing_inputs.append("repo interop contract must include `repo_native_carriers` as a list")
        else:
            for index, entry in enumerate(repo_native_carriers):
                missing_inputs.extend(
                    validate_repo_interop_collection_entry(
                        root=root,
                        collection="repo_native_carriers",
                        entry=entry,
                        index=index,
                    )
                )

        shadow_surfaces = interop_payload.get("shadow_surfaces")
        if not isinstance(shadow_surfaces, dict):
            missing_inputs.append("repo interop contract must include `shadow_surfaces` as an object")
        else:
            extra_shadow_surfaces = sorted(set(shadow_surfaces.keys()) - set(REPO_INTEROP_SHADOW_SURFACES))
            if extra_shadow_surfaces:
                missing_inputs.append(
                    "repo interop contract shadow_surfaces contains unexpected surfaces: "
                    + ", ".join(extra_shadow_surfaces)
                )
            for surface in REPO_INTEROP_SHADOW_SURFACES:
                if surface not in shadow_surfaces:
                    missing_inputs.append(f"repo interop contract shadow_surfaces missing `{surface}`")
                    continue
                missing_inputs.extend(
                    validate_shadow_surface(
                        root=root,
                        surface=surface,
                        entry=shadow_surfaces.get(surface),
                    )
                )

    if missing_inputs:
        repo_interop_surface["availability"] = "incomplete"
        repo_interop_surface["summary"] = "repo interop contract exists, but the machine-readable read surface is incomplete."
    else:
        repo_interop_surface["availability"] = "present"
        repo_interop_surface["summary"] = "repo interop contract is readable for host adapters, repo-native carriers, and shadow parity."
    repo_interop_surface["missing_inputs"] = list(dict.fromkeys(missing_inputs))
    return repo_interop_surface, list(dict.fromkeys(missing_inputs))


def first_match(directory: Path, suffix: str, root: Path) -> str:
    for path in sorted(directory.glob(f"*{suffix}")):
        return relative_locator(path, root)
    return ""


def detect_carrier_summary(root: Path, *, repository_mode: str, planning_mode: bool) -> dict[str, dict[str, str]]:
    item_dir = root / ".loom/work-items"
    recovery_dir = root / ".loom/progress"
    review_dir = root / ".loom/reviews"
    status_path = root / ".loom/status/current.md"
    spec_path = root / ".loom/specs/INIT-0001/spec.md"
    plan_path = root / ".loom/specs/INIT-0001/plan.md"

    present_locators = {
        "work_item": first_match(item_dir, ".md", root) if item_dir.exists() else "",
        "recovery": first_match(recovery_dir, ".md", root) if recovery_dir.exists() else "",
        "review": first_match(review_dir, ".json", root) if review_dir.exists() else "",
        "status_surface": relative_locator(status_path, root) if status_path.exists() else "",
        "spec_path": relative_locator(spec_path, root) if spec_path.exists() else "",
        "plan_path": relative_locator(plan_path, root) if plan_path.exists() else "",
    }

    summary: dict[str, dict[str, str]] = {}
    for key in CARRIER_KEYS:
        locator = present_locators[key]
        if locator:
            summary[key] = carrier_entry("present", locator, "repository scan")
        elif planning_mode and repository_mode == "new":
            summary[key] = carrier_entry("planned", PLANNED_LOCATORS[key], "bootstrap plan")
        else:
            summary[key] = carrier_entry("missing", "unknown", "repository scan")
    return summary


def detect_execution_entry(root: Path, loom_state: str, *, bootstrap_mode: bool) -> str:
    if bootstrap_mode:
        return "python3 .loom/bin/loom_flow.py flow resume --target . --item INIT-0001"
    if loom_state == "active":
        return f"{command_prefix(root, 'loom_flow.py')} flow resume --target . --item INIT-0001"
    if loom_state == "partial":
        return f"{command_prefix(root, 'loom_init.py')} route --target <repo> --task \"请接手当前事项并恢复上下文后继续推进\""
    return "unknown"


def detect_validation_entry(loom_state: str, *, bootstrap_mode: bool) -> str:
    if bootstrap_mode:
        return "python3 .loom/bin/loom_init.py verify --target ."
    if loom_state == "active":
        return "python3 .loom/bin/loom_init.py verify --target ."
    if loom_state == "partial":
        return f"python3 {installed_skill_script(__file__, 'loom-init')} verify --target <repo>"
    return "unknown"


def detect_review_merge_surface(root: Path, loom_state: str, *, bootstrap_mode: bool) -> dict[str, str]:
    pr_template = ".github/PULL_REQUEST_TEMPLATE.md" if file_exists(root, ".github/PULL_REQUEST_TEMPLATE.md") else "unknown"
    validation_surface = ".loom/status/current.md" if file_exists(root, ".loom/status/current.md") else "unknown"
    if bootstrap_mode and validation_surface == "unknown":
        validation_surface = ".loom/status/current.md"

    if bootstrap_mode:
        merge_surface = "python3 .loom/bin/loom_flow.py checkpoint merge --target . --item INIT-0001"
    elif loom_state == "active":
        merge_surface = f"{command_prefix(root, 'loom_flow.py')} checkpoint merge --target . [--item <id>]"
    else:
        merge_surface = "unknown"
    return {
        "pr_template": pr_template,
        "validation_surface": validation_surface,
        "merge_surface": merge_surface,
    }


def detect_github_control_plane(root: Path) -> tuple[dict[str, Any], list[str]]:
    owner, repo = detect_github_repo(root)
    surface: dict[str, Any] = {
        "repository": f"{owner}/{repo}" if owner and repo else "unknown",
        "default_branch": "unknown",
        "branch_protection": "unknown",
        "required_checks": "unknown",
        "pr_reviews": "unknown",
    }
    missing_inputs: list[str] = []

    if not owner or not repo:
        missing_inputs.append("cannot resolve GitHub repository from git origin")
        return surface, missing_inputs

    repo_payload, repo_errors = gh_rest_json(root, f"repos/{owner}/{repo}")
    if repo_errors or repo_payload is None:
        missing_inputs.extend(f"github control plane: {message}" for message in repo_errors)
        return surface, missing_inputs

    full_name = repo_payload.get("full_name")
    if isinstance(full_name, str) and full_name:
        surface["repository"] = full_name
    branch_name = repo_payload.get("default_branch")
    if isinstance(branch_name, str) and branch_name:
        surface["default_branch"] = branch_name
    if surface["default_branch"] == "unknown":
        missing_inputs.append("github control plane: default branch is unavailable")
        return surface, missing_inputs

    branch_payload, branch_errors = gh_json(
        root,
        ["api", f"repos/{owner}/{repo}/branches/{quote(surface['default_branch'], safe='')}"],
    )
    if branch_errors or branch_payload is None:
        missing_inputs.extend(f"github control plane: {message}" for message in branch_errors)
        return surface, missing_inputs

    protected = branch_payload.get("protected")
    if isinstance(protected, bool):
        surface["branch_protection"] = "enabled" if protected else "disabled"
    protection = branch_payload.get("protection")
    if isinstance(protection, dict):
        required_status = protection.get("required_status_checks")
        if isinstance(required_status, dict):
            contexts = required_status.get("contexts")
            if isinstance(contexts, list) and all(isinstance(item, str) for item in contexts):
                surface["required_checks"] = contexts
            else:
                surface["required_checks"] = []
        pull_request_reviews = protection.get("required_pull_request_reviews")
        if isinstance(pull_request_reviews, dict):
            surface["pr_reviews"] = "required"
        elif surface["branch_protection"] == "enabled":
            surface["pr_reviews"] = "not_required"
    return surface, missing_inputs


def detect_host_binding_surface(
    root: Path,
    *,
    carrier_summary: dict[str, dict[str, str]],
    github_control_plane: dict[str, Any],
    repo_interface: dict[str, Any],
    repo_interop: dict[str, Any],
) -> dict[str, Any]:
    branch_result = run_process(["git", "branch", "--show-current"], root)
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    worktree_result = run_process(["git", "rev-parse", "--show-toplevel"], root)
    worktree = worktree_result.stdout.strip() if worktree_result.returncode == 0 else ""
    default_branch = github_control_plane.get("default_branch")
    required_objects: dict[str, dict[str, Any]] = {
        "work_item": {
            "status": carrier_summary.get("work_item", {}).get("status", "missing"),
            "locator": carrier_summary.get("work_item", {}).get("locator", "unknown"),
            "authority": "loom fact chain",
        },
        "branch": {
            "status": "present" if branch else "missing",
            "locator": branch or "unknown",
            "authority": "git",
        },
        "worktree": {
            "status": "present" if worktree else "missing",
            "locator": worktree or "unknown",
            "authority": "git",
        },
        "implementation_pr": {
            "status": "host-managed",
            "locator": "GitHub PR linked from Work Item or branch",
            "authority": "host",
        },
        "merge_commit": {
            "status": "host-managed",
            "locator": "GitHub merged PR mergeCommit",
            "authority": "host",
        },
        "closeout": {
            "status": "present" if repo_interop.get("availability") == "present" else "host-managed",
            "locator": "reconciliation audit + closeout gate",
            "authority": "loom + host",
        },
    }
    profile_objects = {
        "phase": {
            "status": "profile-defined",
            "locator": "GitHub parent issue or equivalent planning object",
            "authority": "github-profile",
        },
        "fr": {
            "status": "profile-defined",
            "locator": "GitHub sub-issue or equivalent formal request",
            "authority": "github-profile",
        },
    }
    missing_inputs = [
        key
        for key in ("work_item", "branch", "worktree")
        if required_objects[key]["status"] in {"missing", "unknown"}
    ]
    if default_branch in {None, "unknown"}:
        missing_inputs.append("github default branch")
    if repo_interface.get("availability") == "incomplete":
        missing_inputs.append("repo interface")
    if repo_interop.get("availability") == "incomplete":
        missing_inputs.append("repo interop")
    return {
        "schema_version": "loom-host-binding/v1",
        "required_objects": {**profile_objects, **required_objects},
        "default_branch": default_branch,
        "missing_inputs": missing_inputs,
        "result": "pass" if not missing_inputs else "block",
        "summary": (
            "host binding surface can relate the active Work Item to branch, worktree, PR, merge commit, and closeout."
            if not missing_inputs
            else "host binding surface is readable, but required binding facts are missing or host-managed."
        ),
    }


def maturity_status(
    *,
    carrier_summary: dict[str, dict[str, str]],
    repo_interface: dict[str, Any],
    repo_interop: dict[str, Any],
    github_control_plane: dict[str, Any],
    host_binding: dict[str, Any],
) -> dict[str, Any]:
    carrier_present = {
        key: value.get("status") == "present"
        for key, value in carrier_summary.items()
    }
    spec_gate_present = (
        carrier_present.get("review", False)
        and carrier_present.get("spec_path", False)
        and carrier_present.get("plan_path", False)
    )
    repo_interface_present = repo_interface.get("availability") == "present"
    repo_interop_present = repo_interop.get("availability") == "present"
    basic_host_binding_present = host_binding.get("result") == "pass"
    github_control_plane_present = github_control_plane.get("default_branch") != "unknown"
    facts = {
        **carrier_present,
        "light": False,
        "standard": False,
        "fr_work_item_layer": repo_interface_present,
        "spec_gate": spec_gate_present,
        "status_control_plane": True,
        "basic_host_binding": basic_host_binding_present,
        "closeout_reconciliation_read": repo_interop_present,
        "repo_interface": repo_interface_present,
        "repo_interop": repo_interop_present,
        "github_controlled_merge": (
            github_control_plane_present
            and basic_host_binding_present
            and repo_interface_present
            and repo_interop_present
        ),
    }
    achieved: list[str] = []
    missing_by_level: dict[str, list[str]] = {}
    missing_details_by_level: dict[str, list[dict[str, Any]]] = {}
    for level in ("light", "standard", "strong"):
        missing = [field for field in MATURITY_LEVELS[level]["requires"] if not facts.get(field)]
        missing_by_level[level] = missing
        field_rows = MATURITY_REQUIRED_FIELDS.get(level, [])
        missing_details_by_level[level] = [
            row
            for row in field_rows
            if row["id"] in missing
        ]
        if not missing:
            achieved.append(level)
            facts[level] = True
    current = achieved[-1] if achieved else "unadopted"
    next_level = None
    for level in ("light", "standard", "strong"):
        if level not in achieved:
            next_level = level
            break
    return {
        "schema_version": "loom-governance-maturity/v1",
        "current": current,
        "achieved": achieved,
        "next": next_level,
        "levels": MATURITY_LEVELS,
        "required_fields": MATURITY_REQUIRED_FIELDS,
        "missing_by_level": missing_by_level,
        "missing_details_by_level": missing_details_by_level,
    }


def governance_control_plane(
    *,
    carrier_summary: dict[str, dict[str, str]],
    github_control_plane: dict[str, Any],
    repo_interface: dict[str, Any],
    repo_interop: dict[str, Any],
    host_binding: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": GOVERNANCE_CONTROL_VERSION,
        "execution_entry": {
            "only_default_entry": "work_item",
            "illegal_entry_fallbacks": WORK_ITEM_ENFORCEMENT_FALLBACKS,
            "result": "pass" if carrier_summary.get("work_item", {}).get("status") == "present" else "block",
        },
        "host_binding": host_binding,
        "taxonomy": GATE_FAILURE_TAXONOMY,
        "gate_chain": GATE_CHAIN,
        "maturity": maturity_status(
            carrier_summary=carrier_summary,
            repo_interface=repo_interface,
            repo_interop=repo_interop,
            github_control_plane=github_control_plane,
            host_binding=host_binding,
        ),
    }


def build_governance_surface(
    root: Path,
    *,
    bootstrap_mode: bool = False,
    scenario_override: str | None = None,
) -> dict[str, Any]:
    loom_state = detect_loom_state(root)
    repository_mode = detect_repository_mode(root, loom_state, scenario_override=scenario_override)
    planning_mode = bootstrap_mode and repository_mode == "new" and loom_state != "active"
    carrier_summary = detect_carrier_summary(root, repository_mode=repository_mode, planning_mode=planning_mode)
    github_control_plane, github_missing = detect_github_control_plane(root)
    execution_entry = detect_execution_entry(root, loom_state, bootstrap_mode=bootstrap_mode)
    validation_entry = detect_validation_entry(loom_state, bootstrap_mode=bootstrap_mode)
    review_merge_surface = detect_review_merge_surface(root, loom_state, bootstrap_mode=bootstrap_mode)
    repo_interface, repo_interface_missing = detect_repo_interface(root)
    repo_interop, repo_interop_missing = detect_repo_interop(root)
    host_binding = detect_host_binding_surface(
        root,
        carrier_summary=carrier_summary,
        github_control_plane=github_control_plane,
        repo_interface=repo_interface,
        repo_interop=repo_interop,
    )
    control_plane = governance_control_plane(
        carrier_summary=carrier_summary,
        github_control_plane=github_control_plane,
        repo_interface=repo_interface,
        repo_interop=repo_interop,
        host_binding=host_binding,
    )

    missing_inputs: list[str] = []
    if bootstrap_mode and repository_mode == "new":
        missing_inputs.extend(github_missing)
        summary = "repository is treated as new; Loom can plan the first governance carriers and bootstrap entrypoints without adding a second truth source."
    else:
        present_carriers = [key for key, value in carrier_summary.items() if value["status"] == "present"]
        if not present_carriers:
            missing_inputs.append("no stable Loom carriers are readable yet")
        missing_inputs.extend(github_missing)
        if repo_interface["availability"] == "incomplete":
            missing_inputs.extend(repo_interface_missing)
        if repo_interop["availability"] == "incomplete":
            missing_inputs.extend(repo_interop_missing)
        if host_binding["result"] == "block":
            missing_inputs.extend(f"host binding: {message}" for message in host_binding["missing_inputs"])
        control_plane_ready = github_control_plane["default_branch"] != "unknown"
        carrier_ready = bool(present_carriers)
        summary = (
            "resume chain is readable and the current governance carriers can support continued execution."
            if carrier_ready and control_plane_ready
            else "resume chain is only partially supported because governance carriers or GitHub control-plane signals are incomplete."
        )

    return {
        "repository_mode": repository_mode,
        "loom_state": loom_state,
        "carrier_summary": carrier_summary,
        "execution_entry": execution_entry,
        "validation_entry": validation_entry,
        "review_merge_surface": review_merge_surface,
        "github_control_plane": github_control_plane,
        "repo_interface": repo_interface,
        "repo_interop": repo_interop,
        "governance_control_plane": control_plane,
        "summary": summary,
        "missing_inputs": list(dict.fromkeys(missing_inputs)),
    }
