#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import hashlib
import json
import py_compile
import tempfile

from scripts.common import REPO_ROOT, git_changed_files, git_current_branch
from scripts.context_guard import infer_current_issue, validate_context_rules, validate_repository as validate_context_repository
from scripts.item_context import matching_exec_plan_for_issue
from scripts.open_pr import validate_pr_preflight
from scripts.policy.policy import classify_paths
from scripts.pr_scope_guard import build_report
from scripts.workflow_guard import validate_repository as validate_workflow_repository


def infer_pr_class(changed_paths: list[str]) -> str:
    categories = {item.category for item in classify_paths(changed_paths)}
    if "governance" in categories:
        return "governance"
    if "spec" in categories:
        return "spec"
    if categories and categories <= {"docs"}:
        return "docs"
    return "implementation"


REQUIRED_GOVERNANCE_FILES = (
    Path("WORKFLOW.md"),
    Path("docs/process/agent-loop.md"),
    Path("docs/process/branch-retirement.md"),
    Path("docs/process/worktree-lifecycle.md"),
    Path("scripts/create_worktree.py"),
    Path("scripts/governance_status.py"),
    Path("scripts/retire_branch.py"),
    Path("scripts/context_guard.py"),
    Path("scripts/workflow_guard.py"),
    Path("scripts/sync_repo_settings.py"),
)

REQUIRED_LOOM_CARRIER_FILES = (
    Path(".loom/README.md"),
    Path(".loom/bootstrap/manifest.json"),
    Path(".loom/bootstrap/init-result.json"),
    Path(".loom/bin/loom_init.py"),
    Path(".loom/bin/fact_chain_support.py"),
    Path(".loom/bin/governance_surface.py"),
    Path(".loom/bin/loom_flow.py"),
    Path(".loom/bin/loom_status.py"),
    Path(".loom/bin/loom_check.py"),
    Path(".loom/bin/runtime_paths.py"),
    Path(".loom/bin/runtime_state.py"),
    Path(".loom/companion/manifest.json"),
    Path(".loom/companion/repo-interface.json"),
    Path(".loom/companion/interop.json"),
    Path(".loom/status/current.md"),
    Path(".loom/shadow/shadow-parity.json"),
)

REQUIRED_LOOM_SHADOW_SURFACES = {"admission", "review", "merge_ready", "closeout"}
REQUIRED_COMPANION_REQUIREMENTS = {
    "review": {
        "syvert-review-rubric": {
            "locator": "code_review.md",
            "enforcement": "blocking",
        },
    },
    "merge_ready": {
        "syvert-guardian-merge-gate": {
            "locator": "code_review.md",
            "enforcement": "blocking",
        },
    },
    "closeout": {
        "syvert-delivery-closeout": {
            "locator": "docs/process/delivery-funnel.md",
            "enforcement": "advisory",
        },
    },
}
REQUIRED_SPECIALIZED_GATES = {
    "workflow-guard": {
        "locator": "scripts/workflow_guard.py",
        "gate_type": "admission",
    },
    "governance-gate": {
        "locator": "scripts/governance_gate.py",
        "gate_type": "build",
    },
    "pr-guardian": {
        "locator": "scripts/pr_guardian.py",
        "gate_type": "merge_ready",
    },
}
REQUIRED_METADATA_CONTRACT_LOCATORS = {
    "integration_check": {
        "applicability_locator": "WORKFLOW.md",
        "authority_locator": "scripts/policy/integration_contract.json",
    },
}
REQUIRED_CONTEXT_SCHEMA_LOCATORS = {
    "issue": ("WORKFLOW.md", "docs/process/delivery-funnel.md"),
    "item_key": ("WORKFLOW.md", "WORKFLOW.md"),
    "item_type": ("WORKFLOW.md", "WORKFLOW.md"),
    "release": ("WORKFLOW.md", "WORKFLOW.md"),
    "sprint": ("WORKFLOW.md", "WORKFLOW.md"),
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验治理基线变更是否保持纯度。")
    parser.add_argument("--mode", choices=("ci", "local"), default="local")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--base-ref")
    parser.add_argument("--base-sha")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--head-sha")
    return parser.parse_args(argv)


def markdown_fields(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative_path(repo_root: Path, raw_locator: object, *, label: str) -> tuple[str | None, str | None]:
    if not isinstance(raw_locator, str) or not raw_locator.strip():
        return None, f"{label} 必须是非空相对路径"
    path = Path(raw_locator)
    if path.is_absolute():
        return None, f"{label} 必须是仓库内相对路径"
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None, f"{label} 不得指向仓库外: {raw_locator}"
    if not resolved.exists():
        return raw_locator, f"{label} 指向缺失文件: {raw_locator}"
    return raw_locator, None


def artifact_paths(payload: object, field: str) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    raw_artifacts = payload.get(field)
    if not isinstance(raw_artifacts, list):
        return set()
    return {
        artifact["path"]
        for artifact in raw_artifacts
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str) and artifact.get("path")
    }


def markdown_artifact_refs(path: Path) -> set[str]:
    refs: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- `") and stripped.endswith("`"):
            refs.add(stripped[3:-1])
    return refs


def validate_companion_locator_truth(repo_root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = repo_root / ".loom/companion/manifest.json"
    repo_interface_path = repo_root / ".loom/companion/repo-interface.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Loom companion manifest 无法读取: {manifest_path}: {exc}"]
    try:
        repo_interface = json.loads(repo_interface_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Loom repo interface 无法读取: {repo_interface_path}: {exc}"]

    if manifest.get("schema_version") != "loom-repo-companion-manifest/v1":
        errors.append("Loom companion manifest schema_version 必须是 loom-repo-companion-manifest/v1")
    for field, expected in (
        ("companion_entry", ".loom/companion/README.md"),
        ("repo_interface", ".loom/companion/repo-interface.json"),
    ):
        actual, error = repo_relative_path(repo_root, manifest.get(field), label=f"companion manifest `{field}`")
        if actual != expected:
            errors.append(f"Loom companion manifest `{field}` 必须是 {expected}")
        if error:
            errors.append(error)

    if repo_interface.get("schema_version") not in {"loom-repo-interface/v1", "loom-repo-interface/v2"}:
        errors.append("Loom repo interface schema_version 必须是 loom-repo-interface/v1 或 loom-repo-interface/v2")
    actual_companion_entry, error = repo_relative_path(
        repo_root,
        repo_interface.get("companion_entry"),
        label="repo interface `companion_entry`",
    )
    if actual_companion_entry != ".loom/companion/README.md":
        errors.append("Loom repo interface `companion_entry` 必须是 .loom/companion/README.md")
    if error:
        errors.append(error)

    repo_specific_requirements = repo_interface.get("repo_specific_requirements")
    if not isinstance(repo_specific_requirements, dict):
        errors.append("Loom repo interface 必须声明 repo_specific_requirements")
    else:
        for required_surface, required_entries in REQUIRED_COMPANION_REQUIREMENTS.items():
            requirements = repo_specific_requirements.get(required_surface)
            if not isinstance(requirements, list):
                errors.append(f"Loom repo interface 必须声明 `{required_surface}` repo-specific requirements")
                continue
            by_id = {
                requirement.get("id"): requirement
                for requirement in requirements
                if isinstance(requirement, dict) and isinstance(requirement.get("id"), str)
            }
            for required_id, expected_contract in required_entries.items():
                requirement = by_id.get(required_id)
                if not isinstance(requirement, dict):
                    errors.append(f"Loom repo interface `{required_surface}` 缺少 required requirement `{required_id}`")
                    continue
                expected_locator = expected_contract["locator"]
                if requirement.get("locator") != expected_locator:
                    errors.append(
                        f"Loom repo interface `{required_surface}` requirement `{required_id}` locator 必须是 {expected_locator}"
                    )
                expected_enforcement = expected_contract["enforcement"]
                if requirement.get("enforcement") != expected_enforcement:
                    errors.append(
                        f"Loom repo interface `{required_surface}` requirement `{required_id}` enforcement 必须是 {expected_enforcement}"
                    )
        for surface, requirements in repo_specific_requirements.items():
            if not isinstance(requirements, list):
                errors.append(f"Loom repo interface surface `{surface}` 必须是列表")
                continue
            for index, requirement in enumerate(requirements):
                if not isinstance(requirement, dict):
                    errors.append(f"Loom repo interface surface `{surface}` requirement[{index}] 必须是对象")
                    continue
                _, locator_error = repo_relative_path(
                    repo_root,
                    requirement.get("locator"),
                    label=f"repo interface `{surface}` requirement[{index}].locator",
                )
                if locator_error:
                    errors.append(locator_error)

    specialized_gates = repo_interface.get("specialized_gates")
    if not isinstance(specialized_gates, list):
        errors.append("Loom repo interface 必须声明 specialized_gates 列表")
    else:
        gates_by_id = {
            gate.get("id"): gate
            for gate in specialized_gates
            if isinstance(gate, dict) and isinstance(gate.get("id"), str)
        }
        for required_id, expected_contract in REQUIRED_SPECIALIZED_GATES.items():
            gate = gates_by_id.get(required_id)
            if not isinstance(gate, dict):
                errors.append(f"Loom repo interface specialized_gates 缺少 required gate `{required_id}`")
                continue
            expected_locator = expected_contract["locator"]
            if gate.get("locator") != expected_locator:
                errors.append(f"Loom repo interface specialized gate `{required_id}` locator 必须是 {expected_locator}")
            expected_gate_type = expected_contract["gate_type"]
            if gate.get("gate_type") != expected_gate_type:
                errors.append(f"Loom repo interface specialized gate `{required_id}` gate_type 必须是 {expected_gate_type}")
        for index, gate in enumerate(specialized_gates):
            if not isinstance(gate, dict):
                errors.append(f"Loom repo interface specialized_gates[{index}] 必须是对象")
                continue
            _, locator_error = repo_relative_path(
                repo_root,
                gate.get("locator"),
                label=f"repo interface specialized_gates[{index}].locator",
            )
            if locator_error:
                errors.append(locator_error)

    metadata_contract = repo_interface.get("metadata_contract")
    if isinstance(metadata_contract, dict):
        metadata_fields = {
            field.get("id"): field
            for field in metadata_contract.get("fields", [])
            if isinstance(field, dict) and isinstance(field.get("id"), str)
        }
        for required_id, expected_locators in REQUIRED_METADATA_CONTRACT_LOCATORS.items():
            field = metadata_fields.get(required_id)
            if not isinstance(field, dict):
                errors.append(f"Loom repo interface metadata_contract 缺少 required field `{required_id}`")
                continue
            for locator_key, expected_locator in expected_locators.items():
                if field.get(locator_key) != expected_locator:
                    errors.append(
                        f"Loom repo interface metadata_contract field `{required_id}` {locator_key} 必须是 {expected_locator}"
                    )
        for index, field in enumerate(metadata_contract.get("fields", [])):
            if not isinstance(field, dict):
                continue
            for locator_key in ("applicability_locator", "authority_locator"):
                _, locator_error = repo_relative_path(
                    repo_root,
                    field.get(locator_key),
                    label=f"repo interface metadata_contract.fields[{index}].{locator_key}",
                )
                if locator_error:
                    errors.append(locator_error)

    context_schema = repo_interface.get("context_schema")
    if isinstance(context_schema, dict):
        context_fields = {
            field.get("id"): field
            for field in context_schema.get("fields", [])
            if isinstance(field, dict) and isinstance(field.get("id"), str)
        }
        for required_id, (expected_authority, expected_mapping) in REQUIRED_CONTEXT_SCHEMA_LOCATORS.items():
            field = context_fields.get(required_id)
            if not isinstance(field, dict):
                errors.append(f"Loom repo interface context_schema 缺少 required field `{required_id}`")
                continue
            if field.get("authority_locator") != expected_authority:
                errors.append(
                    f"Loom repo interface context_schema field `{required_id}` authority_locator 必须是 {expected_authority}"
                )
            if field.get("mapping_rule_locator") != expected_mapping:
                errors.append(
                    f"Loom repo interface context_schema field `{required_id}` mapping_rule_locator 必须是 {expected_mapping}"
                )
        for index, field in enumerate(context_schema.get("fields", [])):
            if not isinstance(field, dict):
                continue
            for locator_key in ("authority_locator", "mapping_rule_locator"):
                _, locator_error = repo_relative_path(
                    repo_root,
                    field.get(locator_key),
                    label=f"repo interface context_schema.fields[{index}].{locator_key}",
                )
                if locator_error:
                    errors.append(locator_error)
    return errors


def validate_shadow_surface_evidence(repo_root: Path, evidence_path: Path, *, expected_surface: str, expected_side: str) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Loom shadow parity evidence 无法读取: {evidence_path}: {exc}"]

    if payload.get("schema_version") != "loom-shadow-surface-evidence/v1":
        errors.append(f"Loom shadow parity evidence `{evidence_path}` schema_version 非法")
    if payload.get("surface") != expected_surface:
        errors.append(f"Loom shadow parity evidence `{evidence_path}` surface 必须是 {expected_surface}")
    if payload.get("side") != expected_side:
        errors.append(f"Loom shadow parity evidence `{evidence_path}` side 必须是 {expected_side}")
    if not str(payload.get("parity_value", "")).strip():
        errors.append(f"Loom shadow parity evidence `{evidence_path}` 缺少 parity_value")

    source_files = payload.get("source_files")
    source_hashes = payload.get("source_sha256")
    if not isinstance(source_files, list) or not source_files:
        errors.append(f"Loom shadow parity evidence `{evidence_path}` 必须列出 source_files")
    if not isinstance(source_hashes, dict) or not source_hashes:
        errors.append(f"Loom shadow parity evidence `{evidence_path}` 必须列出 source_sha256")
        return errors

    root = repo_root.resolve()
    listed_sources = {entry for entry in source_files if isinstance(entry, str)} if isinstance(source_files, list) else set()
    if listed_sources != set(source_hashes):
        errors.append(f"Loom shadow parity evidence `{evidence_path}` 的 source_files 与 source_sha256 必须一致")
    for relative_path, expected_hash in source_hashes.items():
        if not isinstance(relative_path, str) or not isinstance(expected_hash, str) or not expected_hash.strip():
            errors.append(f"Loom shadow parity evidence `{evidence_path}` 包含非法 source hash entry")
            continue
        source_path = (root / relative_path).resolve()
        try:
            source_path.relative_to(root)
        except ValueError:
            errors.append(f"Loom shadow parity evidence `{evidence_path}` 引用了仓库外 source: {relative_path}")
            continue
        if not source_path.is_file():
            errors.append(f"Loom shadow parity evidence `{evidence_path}` 引用了缺失 source: {relative_path}")
            continue
        actual_hash = sha256_file(source_path)
        if actual_hash != expected_hash:
            errors.append(f"Loom shadow parity evidence `{evidence_path}` source hash 已漂移: {relative_path}")
    return errors


def validate_review_payload(path: Path, *, expected_kind: str, item_id: str) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Loom review artifact 无法读取: {path}: {exc}"]
    for field in ("schema_version", "item_id", "decision", "kind", "summary", "reviewer", "reviewed_head", "reviewed_validation_summary"):
        if not str(payload.get(field, "")).strip():
            errors.append(f"Loom review artifact `{path}` 缺少 `{field}`")
    if payload.get("schema_version") != "loom-review/v1":
        errors.append(f"Loom review artifact `{path}` schema_version 必须是 loom-review/v1")
    if payload.get("item_id") != item_id:
        errors.append(f"Loom review artifact `{path}` item_id 必须是 {item_id}")
    if payload.get("kind") != expected_kind:
        errors.append(f"Loom review artifact `{path}` kind 必须是 {expected_kind}")
    if payload.get("decision") not in {"allow", "block", "fallback"}:
        errors.append(f"Loom review artifact `{path}` decision 非法")
    return errors


def validate_loom_carrier_semantics(repo_root: Path) -> list[str]:
    errors: list[str] = []
    status_path = repo_root / ".loom/status/current.md"
    bootstrap_manifest_path = repo_root / ".loom/bootstrap/manifest.json"
    init_result_path = repo_root / ".loom/bootstrap/init-result.json"
    shadow_path = repo_root / ".loom/shadow/shadow-parity.json"
    interop_path = repo_root / ".loom/companion/interop.json"

    if not status_path.exists():
        return errors
    status = markdown_fields(status_path)
    item_id = status.get("Item ID") or "INIT-0001"
    work_item_path = repo_root / f".loom/work-items/{item_id}.md"
    progress_path = repo_root / f".loom/progress/{item_id}.md"
    review_path = repo_root / f".loom/reviews/{item_id}.json"
    spec_review_path = repo_root / f".loom/reviews/{item_id}.spec.json"
    spec_dir = repo_root / f".loom/specs/{item_id}"
    canonical_fields = {
        "Workspace Entry": ".",
        "Recovery Entry": f".loom/progress/{item_id}.md",
        "Review Entry": f".loom/reviews/{item_id}.json",
        "Validation Entry": "python3 .loom/bin/loom_init.py verify --target .",
    }
    for path in (
        work_item_path,
        progress_path,
        review_path,
        spec_review_path,
        spec_dir / "spec.md",
        spec_dir / "plan.md",
        spec_dir / "implementation-contract.md",
        shadow_path,
    ):
        if not path.exists():
            errors.append(f"缺少当前 Loom item carrier: {path}")
    if errors:
        return errors

    work_item = markdown_fields(work_item_path)
    progress = markdown_fields(progress_path)
    try:
        bootstrap_manifest = json.loads(bootstrap_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        bootstrap_manifest = {}
    try:
        init_result = json.loads(init_result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        init_result = {}
    if bootstrap_manifest.get("schema_version") != "loom-bootstrap-manifest/v1":
        errors.append("Loom bootstrap manifest schema_version 必须是 loom-bootstrap-manifest/v1")
    if init_result.get("schema_version") != "loom-init-output/v1":
        errors.append("Loom init-result schema_version 必须是 loom-init-output/v1")

    for field in ("Item ID", "Goal", "Scope", "Execution Path", "Workspace Entry", "Recovery Entry", "Review Entry", "Validation Entry", "Closing Condition"):
        if not work_item.get(field):
            errors.append(f"Loom work item 缺少 `{field}`")
    for field, expected in canonical_fields.items():
        if work_item.get(field) and work_item[field] != expected:
            errors.append(f"Loom work item 的 `{field}` 必须是 `{expected}`")
    for field in (
        "Item ID",
        "Goal",
        "Scope",
        "Execution Path",
        "Workspace Entry",
        "Recovery Entry",
        "Review Entry",
        "Validation Entry",
        "Closing Condition",
        "Current Checkpoint",
        "Latest Validation Summary",
    ):
        if not status.get(field):
            errors.append(f"Loom status 缺少 `{field}`")
        elif work_item.get(field) and work_item[field] != status[field]:
            errors.append(f"Loom status 与 work item 的 `{field}` 不一致")
    for field, expected in canonical_fields.items():
        if status.get(field) and status[field] != expected:
            errors.append(f"Loom status 的 `{field}` 必须是 `{expected}`")
    for field in ("Item ID", "Current Checkpoint", "Latest Validation Summary"):
        if not progress.get(field):
            errors.append(f"Loom progress 缺少 `{field}`")
        elif status.get(field) and progress[field] != status[field]:
            errors.append(f"Loom progress 与 status 的 `{field}` 不一致")

    errors.extend(validate_review_payload(review_path, expected_kind="general_review", item_id=item_id))
    errors.extend(validate_review_payload(spec_review_path, expected_kind="spec_review", item_id=item_id))
    try:
        review_payload = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        review_payload = {}
    if review_payload.get("reviewed_validation_summary") != progress.get("Latest Validation Summary"):
        errors.append("Loom review 的 reviewed_validation_summary 必须匹配 progress/status 最新验证摘要")
    try:
        spec_review_payload = json.loads(spec_review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        spec_review_payload = {}
    if spec_review_payload.get("reviewed_validation_summary") != progress.get("Latest Validation Summary"):
        errors.append("Loom spec review 的 reviewed_validation_summary 必须匹配 progress/status 最新验证摘要")

    required_bootstrap_paths = {str(path) for path in REQUIRED_LOOM_CARRIER_FILES}
    required_bootstrap_paths.update(
        {
            f".loom/work-items/{item_id}.md",
            f".loom/progress/{item_id}.md",
            f".loom/reviews/{item_id}.json",
            f".loom/reviews/{item_id}.spec.json",
            f".loom/specs/{item_id}/spec.md",
            f".loom/specs/{item_id}/plan.md",
            f".loom/specs/{item_id}/implementation-contract.md",
        }
    )
    required_bootstrap_paths.update(
        path.as_posix()
        for path in sorted((repo_root / ".loom/shadow").glob("*.json"))
        if path.name != "shadow-parity.json"
        for path in [path.relative_to(repo_root)]
    )
    manifest_artifacts = artifact_paths(bootstrap_manifest, "artifacts")
    init_artifacts = artifact_paths(init_result, "initial_artifacts")
    for required_path in sorted(required_bootstrap_paths):
        if required_path not in manifest_artifacts:
            errors.append(f"Loom bootstrap manifest artifacts 缺少 `{required_path}`")
        if required_path not in init_artifacts:
            errors.append(f"Loom init-result initial_artifacts 缺少 `{required_path}`")
    for artifact_path in sorted(manifest_artifacts | init_artifacts):
        _, artifact_error = repo_relative_path(repo_root, artifact_path, label=f"Loom bootstrap artifact `{artifact_path}`")
        if artifact_error:
            errors.append(artifact_error)

    fact_chain = init_result.get("fact_chain")
    if not isinstance(fact_chain, dict):
        errors.append("Loom init-result 必须声明 fact_chain")
    else:
        entry_points = fact_chain.get("entry_points")
        if not isinstance(entry_points, dict):
            errors.append("Loom init-result fact_chain.entry_points 必须是对象")
        else:
            expected_entry_points = {
                "current_item_id": item_id,
                "work_item": f".loom/work-items/{item_id}.md",
                "recovery_entry": f".loom/progress/{item_id}.md",
                "status_surface": ".loom/status/current.md",
            }
            for field, expected in expected_entry_points.items():
                if entry_points.get(field) != expected:
                    errors.append(f"Loom init-result fact_chain.entry_points.{field} 必须是 {expected}")

    initial_work_items = init_result.get("initial_work_items")
    matching_initial_work_item = None
    if isinstance(initial_work_items, list):
        for candidate in initial_work_items:
            if isinstance(candidate, dict) and candidate.get("id") == item_id:
                matching_initial_work_item = candidate
                break
    if matching_initial_work_item is None:
        errors.append(f"Loom init-result initial_work_items 缺少 `{item_id}`")
        initial_work_item_artifacts: set[str] = set()
    else:
        for field, expected in (
            ("recovery_entry", f".loom/progress/{item_id}.md"),
            ("review_entry", f".loom/reviews/{item_id}.json"),
            ("validation_entry", "python3 .loom/bin/loom_init.py verify --target ."),
            ("workspace_entry", "."),
        ):
            if matching_initial_work_item.get(field) != expected:
                errors.append(f"Loom init-result work item `{item_id}` 的 {field} 必须是 {expected}")
        initial_work_item_artifacts = {
            artifact
            for artifact in matching_initial_work_item.get("artifacts", [])
            if isinstance(artifact, str) and artifact
        }
    work_item_artifacts = markdown_artifact_refs(work_item_path)
    for required_path in sorted(required_bootstrap_paths):
        if required_path not in initial_work_item_artifacts:
            errors.append(f"Loom init-result work item artifacts 缺少 `{required_path}`")
        if required_path not in work_item_artifacts:
            errors.append(f"Loom work item Associated Artifacts 缺少 `{required_path}`")

    errors.extend(validate_companion_locator_truth(repo_root))

    try:
        shadow_payload = json.loads(shadow_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        shadow_payload = {}
    if shadow_payload.get("result") != "pass":
        errors.append("Loom shadow parity artifact result 必须为 pass")
    if shadow_payload.get("schema_version") != "loom-shadow-parity-evidence/v1":
        errors.append("Loom shadow parity artifact schema_version 必须是 loom-shadow-parity-evidence/v1")
    if not isinstance(shadow_payload.get("surfaces"), list) or not shadow_payload.get("surfaces"):
        errors.append("Loom shadow parity artifact 必须列出 surfaces")

    try:
        interop_payload = json.loads(interop_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        interop_payload = {}
    shadow_surfaces = interop_payload.get("shadow_surfaces")
    if not isinstance(shadow_surfaces, dict) or not shadow_surfaces:
        errors.append("Loom repo interop contract 必须声明 shadow_surfaces")
    else:
        declared_surface_set = set(shadow_surfaces)
        if declared_surface_set != REQUIRED_LOOM_SHADOW_SURFACES:
            errors.append("Loom repo interop shadow_surfaces 必须固定为 admission/review/merge_ready/closeout")
        artifact_surface_set = set(shadow_payload.get("surfaces", [])) if isinstance(shadow_payload.get("surfaces"), list) else set()
        if artifact_surface_set != declared_surface_set:
            errors.append("Loom shadow parity artifact surfaces 必须与 repo interop shadow_surfaces 完全一致")

        artifact_sources = set()
        for source_field in ("loom_sources", "repo_sources"):
            sources = shadow_payload.get(source_field)
            if not isinstance(sources, list) or not sources:
                errors.append(f"Loom shadow parity artifact 必须列出 {source_field}")
                continue
            artifact_sources.update(entry for entry in sources if isinstance(entry, str))

        for surface, declared_surface in sorted(shadow_surfaces.items()):
            if not isinstance(declared_surface, dict):
                errors.append(f"Loom shadow surface `{surface}` 必须是对象")
                continue
            surface_values: dict[str, str] = {}
            for side, locator_key in (("loom", "loom_locator"), ("repo", "repo_locator")):
                locator = declared_surface.get(locator_key)
                if not isinstance(locator, str) or not locator.strip():
                    errors.append(f"Loom shadow surface `{surface}` 缺少 {locator_key}")
                    continue
                if not locator.startswith(".loom/shadow/") or not locator.endswith(".json") or locator.endswith("shadow-parity.json"):
                    errors.append(f"Loom shadow surface `{surface}` 的 {locator_key} 必须指向结构化 shadow evidence JSON")
                    continue
                if locator not in artifact_sources:
                    errors.append(f"Loom shadow surface `{surface}` 的 {locator_key} 必须被 shadow-parity artifact 引用")
                evidence_path = repo_root / locator
                if not evidence_path.exists():
                    errors.append(f"Loom shadow surface `{surface}` 缺少 evidence: {locator}")
                    continue
                errors.extend(
                    validate_shadow_surface_evidence(
                        repo_root,
                        evidence_path,
                        expected_surface=surface,
                        expected_side=side,
                    )
                )
                try:
                    evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                parity_value = evidence_payload.get("parity_value")
                if isinstance(parity_value, str):
                    surface_values[side] = parity_value
            if surface_values.get("loom") != surface_values.get("repo"):
                errors.append(f"Loom shadow surface `{surface}` 的 loom/repo parity_value 必须一致")

        declared_locators = {
            declared_surface[locator_key]
            for declared_surface in shadow_surfaces.values()
            if isinstance(declared_surface, dict)
            for locator_key in ("loom_locator", "repo_locator")
            if isinstance(declared_surface.get(locator_key), str)
        }
        if artifact_sources != declared_locators:
            errors.append("Loom shadow parity artifact sources 必须与 repo interop locators 完全一致")

    return errors


def validate_loom_carrier_repository(repo_root: Path, changed_paths: list[str]) -> list[str]:
    if not any(path == ".loom" or path.startswith(".loom/") for path in changed_paths):
        return []

    errors: list[str] = []
    for relative_path in REQUIRED_LOOM_CARRIER_FILES:
        if not (repo_root / relative_path).exists():
            errors.append(f"缺少 Loom carrier 必需工件: {repo_root / relative_path}")

    loom_root = repo_root / ".loom"
    if loom_root.exists():
        for json_path in sorted(loom_root.rglob("*.json")):
            try:
                with json_path.open("r", encoding="utf-8") as handle:
                    json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Loom carrier JSON 无效: {json_path}: {exc}")

        bin_root = loom_root / "bin"
        if bin_root.exists():
            with tempfile.TemporaryDirectory(prefix="syvert-loom-pycompile-") as temp_dir:
                temp_root = Path(temp_dir)
                for index, py_path in enumerate(sorted(bin_root.glob("*.py"))):
                    try:
                        py_compile.compile(
                            str(py_path),
                            cfile=str(temp_root / f"{index}-{py_path.name}c"),
                            doraise=True,
                        )
                    except py_compile.PyCompileError as exc:
                        errors.append(f"Loom carrier Python 语法无效: {py_path}: {exc.msg}")

    errors.extend(validate_loom_carrier_semantics(repo_root))
    return errors


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    base_ref = args.base_ref or args.base_sha
    head_ref = args.head_sha or args.head_ref
    if not base_ref:
        print("governance-gate 需要 `--base-ref` 或 `--base-sha`。", file=sys.stderr)
        return 1

    changed = git_changed_files(base_ref, head_ref, repo=repo_root)
    inferred_pr_class = infer_pr_class(changed)
    report = build_report(inferred_pr_class, changed)
    if report["violations"]:
        print("治理基线改动不得超出 governance PR 允许范围。", file=sys.stderr)
        for item in report["violations"]:
            print(f"- {item['path']} ({item['category']})", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(validate_workflow_repository(repo_root))
    errors.extend(validate_context_repository(repo_root))
    errors.extend(validate_loom_carrier_repository(repo_root, changed))
    current_issue = infer_current_issue(args.head_ref)
    if current_issue is None and args.head_sha is None:
        current_issue = infer_current_issue(git_current_branch(repo=repo_root))
    if current_issue is None:
        errors.append("governance-gate 无法从 `--head-ref` 或当前分支推断当前事项，已拒绝继续执行。")
    else:
        errors.extend(validate_context_rules(repo_root, changed, current_issue=current_issue))
        active_exec_plan = matching_exec_plan_for_issue(repo_root, current_issue)
        if active_exec_plan:
            if inferred_pr_class in {"governance", "spec", "implementation", "docs"}:
                errors.extend(
                    validate_pr_preflight(
                        inferred_pr_class,
                        current_issue,
                        active_exec_plan.get("item_key"),
                        active_exec_plan.get("item_type"),
                        active_exec_plan.get("release"),
                        active_exec_plan.get("sprint"),
                        changed,
                        repo_root=repo_root,
                        validate_worktree_binding_check=False,
                    )
                )
    for relative_path in REQUIRED_GOVERNANCE_FILES:
        if not (repo_root / relative_path).exists():
            errors.append(f"缺少治理栈 v2 必需工件: {repo_root / relative_path}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("governance-gate 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
