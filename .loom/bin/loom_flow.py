#!/usr/bin/env python3
"""Daily execution CLI for Loom checkpoints, workspace lifecycle, and purity checks."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fact_chain_support import (
    STATUS_FIELDS,
    STATUS_SOURCE_FIELDS,
    inspect_fact_chain,
    load_json_file,
    markdown_sections,
    parse_key_value_section,
    parse_recovery_entry,
    parse_work_item,
)
from governance_surface import build_governance_surface
from runtime_paths import shared_asset, shared_script
from runtime_state import detect_runtime_state

PR_TEMPLATE_SECTIONS = (
    "## Summary",
    "## Validation",
    "## Risks And Follow-ups",
    "## Related Work",
)

OWNED_TEMP_ROOTS = (
    ".loom/.tmp",
    ".loom/tmp",
    ".loom/runtime/cache",
    ".loom/runtime/tmp",
    ".loom/flow/tmp",
)
OWNED_RUNTIME_EVIDENCE_ROOTS = (
    ".loom/runtime/review",
)

TERMINAL_CHECKPOINTS = {
    "retired",
    "done",
    "closed",
    "merged",
    "archived",
}

RUNTIME_EVIDENCE_FIELDS = (
    "run_entry",
    "logs_entry",
    "diagnostics_entry",
    "verification_entry",
    "lane_entry",
)

RECOVERY_FIELD_LABELS = {
    "current_checkpoint": "Current Checkpoint",
    "current_stop": "Current Stop",
    "next_step": "Next Step",
    "blockers": "Blockers",
    "latest_validation_summary": "Latest Validation Summary",
    "recovery_boundary": "Recovery Boundary",
    "current_lane": "Current Lane",
}

WORK_ITEM_FIELD_LABELS = {
    "item_id": "Item ID",
    "goal": "Goal",
    "scope": "Scope",
    "execution_path": "Execution Path",
    "workspace_entry": "Workspace Entry",
    "recovery_entry": "Recovery Entry",
    "validation_entry": "Validation Entry",
    "closing_condition": "Closing Condition",
}

REVIEW_DECISIONS = {"allow", "block", "fallback"}
REVIEW_KINDS = {"general_review", "code_review", "spec_review"}
REVIEW_FINDING_SEVERITIES = {"warn", "block"}
REVIEW_FINDING_DISPOSITION_STATUSES = {"accepted", "rejected", "deferred"}
DEFAULT_REVIEW_ENGINE = "codex"
DEFAULT_REVIEW_ADAPTER = "loom/default-codex"
DEFAULT_REVIEW_ENGINE_TIMEOUT_SECONDS = 120
ENGINE_FAILURE_REASONS = {
    "engine_unavailable",
    "schema_drift",
    "runtime_conflict",
    "repo_diff_detected",
}
SHADOW_PARITY_SURFACES = ("admission", "review", "merge_ready", "closeout")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Loom daily execution checks against a target repository.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    checkpoint = subparsers.add_parser("checkpoint", help="Evaluate a Loom checkpoint against the fact chain")
    checkpoint.add_argument("stage", choices=("admission", "build", "merge"))
    checkpoint.add_argument("--target", required=True, help="Target repository root")
    checkpoint.add_argument("--item", help="Expected current item id")
    checkpoint.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    workspace = subparsers.add_parser("workspace", help="Manage Loom workspace lifecycle semantics")
    workspace.add_argument("operation", choices=("create", "locate", "cleanup", "retire"))
    workspace.add_argument("--target", required=True, help="Target repository root")
    workspace.add_argument("--item", help="Expected current item id")
    workspace.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    purity = subparsers.add_parser("purity-check", help="Evaluate Loom workspace purity from the fact chain")
    purity.add_argument("--target", required=True, help="Target repository root")
    purity.add_argument("--item", help="Expected current item id")
    purity.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    fact_chain = subparsers.add_parser("fact-chain", help="Read and validate the Loom fact chain")
    fact_chain.add_argument("--target", required=True, help="Target repository root")
    fact_chain.add_argument("--item", help="Expected current item id")
    fact_chain.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    runtime = subparsers.add_parser("runtime-evidence", help="Read runtime evidence from the Loom fact chain")
    runtime.add_argument("--target", required=True, help="Target repository root")
    runtime.add_argument("--item", help="Expected current item id")
    runtime.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    runtime_state = subparsers.add_parser("runtime-state", help="Read the Loom runtime scene/carrier state")
    runtime_state.add_argument("--target", required=True, help="Target repository root")
    runtime_state.add_argument("--item", help="Expected current item id")
    runtime_state.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    state = subparsers.add_parser(
        "state-check",
        help="Check active-state consistency, checkpoint completeness, and scope overflow signals",
    )
    state.add_argument("--target", required=True, help="Target repository root")
    state.add_argument("--item", help="Expected current item id")
    state.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    review = subparsers.add_parser("review", help="Read, run, or record a Loom formal review artifact")
    review.add_argument("operation", choices=("read", "run", "record"))
    review.add_argument("--target", required=True, help="Target repository root")
    review.add_argument("--item", help="Expected current item id")
    review.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )
    review.add_argument("--review-file", help="Optional review artifact path relative to the target root")
    review.add_argument("--decision", choices=tuple(sorted(REVIEW_DECISIONS)))
    review.add_argument("--kind", choices=tuple(sorted(REVIEW_KINDS)))
    review.add_argument("--summary", help="Stable review conclusion summary")
    review.add_argument("--reviewer", help="Reviewer identity")
    review.add_argument("--fallback-to", choices=("admission", "build", "merge"))
    review.add_argument("--findings-file", help="Optional findings JSON path relative to the target root")
    review.add_argument("--engine-adapter", help="Optional review engine adapter identifier consumed by this record")
    review.add_argument("--engine-evidence", help="Optional review engine evidence path relative to the target root")
    review.add_argument("--normalized-findings", help="Optional normalized findings path relative to the target root")
    review.add_argument("--blocking-issue", action="append", default=[], help="Blocking review finding")
    review.add_argument("--follow-up", action="append", default=[], help="Follow-up item recorded by the review")

    recovery = subparsers.add_parser("recovery", help="Write the authored Loom recovery entry")
    recovery.add_argument("operation", choices=("writeback",))
    recovery.add_argument("--target", required=True, help="Target repository root")
    recovery.add_argument("--item", help="Expected current item id")
    recovery.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )
    recovery.add_argument("--current-checkpoint", help="Updated checkpoint value")
    recovery.add_argument("--current-stop", help="Updated current stop")
    recovery.add_argument("--next-step", help="Updated next step")
    recovery.add_argument("--blockers", help="Updated blockers summary")
    recovery.add_argument("--latest-validation-summary", help="Updated validation summary")
    recovery.add_argument("--recovery-boundary", help="Updated recovery boundary")
    recovery.add_argument("--current-lane", help="Updated current lane")

    work_item = subparsers.add_parser("work-item", help="Create or update a Loom work item")
    work_item.add_argument("operation", choices=("create", "update"))
    work_item.add_argument("--target", required=True, help="Target repository root")
    work_item.add_argument("--item", required=True, help="Work item id")
    work_item.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )
    work_item.add_argument("--goal", help="Static goal")
    work_item.add_argument("--scope", help="Static scope")
    work_item.add_argument("--execution-path", help="Execution path")
    work_item.add_argument("--workspace-entry", help="Workspace entry")
    work_item.add_argument("--recovery-entry", help="Recovery entry path relative to the target root")
    work_item.add_argument("--validation-entry", help="Validation entry command")
    work_item.add_argument("--closing-condition", help="Closing condition")
    work_item.add_argument("--artifact", action="append", default=[], help="Associated artifact for create")
    work_item.add_argument("--add-artifact", action="append", default=[], help="Associated artifact to append")
    work_item.add_argument("--remove-artifact", action="append", default=[], help="Associated artifact to remove")
    work_item.add_argument("--activate", action="store_true", help="Activate this item in the current fact chain")
    work_item.add_argument("--init-recovery", action="store_true", help="Initialize the recovery entry when creating")

    host = subparsers.add_parser("host-lifecycle", help="Classify host objects against Loom lifecycle boundaries")
    host.add_argument("--target", required=True, help="Target repository root")
    host.add_argument("--item", help="Expected current item id")
    host.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    closeout = subparsers.add_parser("closeout", help="Check or sync Loom closeout state with GitHub control plane")
    closeout.add_argument("operation", choices=("check", "sync"))
    closeout.add_argument("--target", required=True, help="Target repository root")
    closeout.add_argument("--issue", type=int, help="GitHub issue number to validate or sync")
    closeout.add_argument("--pr", type=int, help="GitHub pull request number to validate or sync")
    closeout.add_argument("--project", type=int, help="GitHub project number to validate or sync")
    closeout.add_argument("--phase", type=int, help="GitHub Phase issue number")
    closeout.add_argument("--fr", type=int, help="GitHub FR issue number")
    closeout.add_argument("--branch", help="GitHub branch name bound to the work item")
    closeout.add_argument("--owner", help="GitHub owner; auto-detected from origin when omitted")
    closeout.add_argument("--repo", dest="repo_name", help="GitHub repository name; auto-detected from origin when omitted")
    closeout.add_argument("--comment", help="Optional closeout comment for issue sync")
    closeout.add_argument("--skip-gate", action="store_true", help="Skip local loom_check execution during closeout")

    reconciliation = subparsers.add_parser("reconciliation", help="Audit Loom GitHub drift before closeout reconciliation")
    reconciliation.add_argument("operation", choices=("audit", "sync"))
    reconciliation.add_argument("--target", required=True, help="Target repository root")
    reconciliation.add_argument("--issue", type=int, help="GitHub issue number to audit")
    reconciliation.add_argument("--pr", type=int, help="GitHub pull request number to audit")
    reconciliation.add_argument("--project", type=int, help="GitHub project number to audit")
    reconciliation.add_argument("--phase", type=int, help="GitHub Phase issue number")
    reconciliation.add_argument("--fr", type=int, help="GitHub FR issue number")
    reconciliation.add_argument("--branch", help="GitHub branch name bound to the work item")
    reconciliation.add_argument("--owner", help="GitHub owner; auto-detected from origin when omitted")
    reconciliation.add_argument("--repo", dest="repo_name", help="GitHub repository name; auto-detected from origin when omitted")
    reconciliation.add_argument("--comment", help="Optional closeout comment for issue sync")
    reconciliation.add_argument("--comment-file", help="Read closeout comment body from a file")
    reconciliation.add_argument("--dry-run", action="store_true", help="Preview reconciliation sync actions without writing GitHub state")

    shadow = subparsers.add_parser("shadow-parity", help="Compare Loom and repo-native parity surfaces without changing merge gates")
    shadow.add_argument("--target", required=True, help="Target repository root")
    shadow.add_argument(
        "--surface",
        choices=(*SHADOW_PARITY_SURFACES, "all"),
        default="all",
        help="Shadow surface to compare; defaults to all supported surfaces",
    )
    shadow.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )
    shadow.add_argument(
        "--mode",
        choices=("validation-only", "blocking"),
        default="validation-only",
        help="Shadow parity enforcement mode; defaults to validation-only.",
    )
    shadow.add_argument(
        "--blocking",
        action="store_true",
        help="Shortcut for --mode blocking. This is explicit opt-in and never the default.",
    )

    runtime_parity = subparsers.add_parser(
        "runtime-parity",
        help="Validate Loom core strong-governance runtime parity without host-specific orchestration",
    )
    runtime_parity.add_argument("operation", choices=("validate",))
    runtime_parity.add_argument("--target", required=True, help="Target repository root")
    runtime_parity.add_argument("--item", help="Expected current item id")
    runtime_parity.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    governance_profile = subparsers.add_parser(
        "governance-profile",
        help="Read Loom governance maturity and upgrade requirements",
    )
    governance_profile.add_argument("operation", choices=("status", "upgrade-plan", "upgrade", "binding"))
    governance_profile.add_argument("--target", required=True, help="Target repository root")
    governance_profile.add_argument("--to", choices=("standard", "strong"), help="Target maturity for governance-profile upgrade")
    governance_profile.add_argument("--dry-run", action="store_true", default=True, help="Preview upgrade actions without writing files; this is the default")
    governance_profile.add_argument("--apply", dest="dry_run", action="store_false", help="Apply Loom-owned scaffold writes")
    governance_profile.add_argument("--force", action="store_true", help="Allow replacement of existing Loom-owned scaffold files during upgrade apply")
    governance_profile.add_argument("--owner", help="GitHub owner; auto-detected from origin when omitted")
    governance_profile.add_argument("--repo", dest="repo_name", help="GitHub repository name; auto-detected from origin when omitted")
    governance_profile.add_argument("--phase", type=int, help="GitHub Phase issue number")
    governance_profile.add_argument("--fr", type=int, help="GitHub FR issue number")
    governance_profile.add_argument("--issue", type=int, help="GitHub Work Item issue number")
    governance_profile.add_argument("--pr", type=int, help="GitHub implementation PR number")
    governance_profile.add_argument("--branch", help="GitHub branch name bound to the work item")
    governance_profile.add_argument("--sync", action="store_true", help="Preview host binding repairs; writes are intentionally disabled in this phase")

    flow = subparsers.add_parser("flow", help="Run a bundled high-frequency Loom flow")
    flow.add_argument("operation", choices=("pre-review", "review", "spec-review", "resume", "handoff", "merge-ready"))
    flow.add_argument("--target", required=True, help="Target repository root")
    flow.add_argument("--item", help="Expected current item id")
    flow.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )

    return parser.parse_args(argv)


def emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    result = payload.get("result")
    return 0 if result == "pass" else 1


def runtime_state_payload(target_root: Path) -> dict[str, Any]:
    return detect_runtime_state(__file__, "loom-flow", target_root=target_root)


def runtime_state_block_payload(
    *,
    command: str,
    runtime_state: dict[str, Any],
    summary: str,
    operation: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "command": command,
        "result": "block",
        "summary": summary,
        "missing_inputs": list(runtime_state.get("missing_inputs", [])),
        "fallback_to": runtime_state.get("fallback_to"),
        "runtime_state": runtime_state,
    }
    if operation is not None:
        payload["operation"] = operation
    return payload


def repo_specific_default_fallback(surface: str) -> str:
    return {
        "spec_review": "build",
        "review": "build",
        "merge_ready": "merge",
        "closeout": "merge",
    }[surface]


def repo_specific_requirements_payload(
    repo_interface: object,
    *,
    target_root: Path,
    surface: str,
) -> dict[str, Any]:
    empty_payload = {
        "surface": surface,
        "result": "pass",
        "declared_requirements": [],
        "blocking_requirements": [],
        "advisory_requirements": [],
        "summary": "no repo companion requirements are declared for this surface.",
        "missing_inputs": [],
        "fallback_to": None,
    }
    if not isinstance(repo_interface, dict):
        return {
            **empty_payload,
            "result": "block",
            "summary": "repo companion interface could not be read from governance_surface.",
            "missing_inputs": ["governance_surface.repo_interface"],
            "fallback_to": repo_specific_default_fallback(surface),
        }

    availability = repo_interface.get("availability")
    if availability == "absent":
        return {
            **empty_payload,
            "summary": "no repo companion interface is declared for this repository.",
        }
    if availability == "companion_docs_only":
        return {
            **empty_payload,
            "summary": "legacy companion docs are present, but no machine-readable repo companion requirements are declared.",
        }
    if availability == "incomplete":
        missing_inputs = repo_interface.get("missing_inputs")
        return {
            **empty_payload,
            "result": "block",
            "summary": "repo companion interface is incomplete, so Loom cannot safely consume repo-specific requirements.",
            "missing_inputs": list(missing_inputs) if isinstance(missing_inputs, list) else ["repo companion interface"],
            "fallback_to": repo_specific_default_fallback(surface),
        }
    if availability != "present":
        return {
            **empty_payload,
            "result": "block",
            "summary": "repo companion interface returned an unknown availability state.",
            "missing_inputs": [f"unknown repo companion availability: {availability}"],
            "fallback_to": repo_specific_default_fallback(surface),
        }

    repo_specific_locator = repo_interface.get("repo_specific_requirements")
    declared_locator = (
        repo_specific_locator.get("locator")
        if isinstance(repo_specific_locator, dict)
        else ".loom/companion/repo-interface.json"
    )
    repo_specific_path = target_root / str(declared_locator)
    blocking: list[dict[str, Any]] = []
    advisory: list[dict[str, Any]] = []
    declared: list[dict[str, Any]] = []
    try:
        payload = load_json_file(repo_specific_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {
            **empty_payload,
            "result": "block",
            "summary": "repo companion requirements are declared, but the machine-readable interface could not be loaded.",
            "missing_inputs": [f"missing repo companion interface: {repo_specific_path}"],
            "fallback_to": repo_specific_default_fallback(surface),
        }

    requirements = payload.get("repo_specific_requirements") if isinstance(payload, dict) else None
    entries = requirements.get(surface) if isinstance(requirements, dict) else None
    if not isinstance(entries, list):
        return {
            **empty_payload,
            "result": "block",
            "summary": "repo companion interface is missing the requested surface requirements.",
            "missing_inputs": [f"repo companion surface missing: {surface}"],
            "fallback_to": repo_specific_default_fallback(surface),
        }

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        declared.append(entry)
        if entry.get("enforcement") == "blocking":
            blocking.append(entry)
        elif entry.get("enforcement") == "advisory":
            advisory.append(entry)

    if blocking:
        summary = (
            "companion-declared blocking requirements remain outside Loom core and must be handled before this surface can pass."
        )
        result = "block"
        fallback_to = repo_specific_default_fallback(surface)
        missing_inputs = [f"repo companion requirement: {entry.get('id', 'unknown')}" for entry in blocking]
    elif advisory:
        summary = "only companion-declared advisory requirements are present for this surface."
        result = "pass"
        fallback_to = None
        missing_inputs = []
    else:
        summary = "no repo companion requirements are declared for this surface."
        result = "pass"
        fallback_to = None
        missing_inputs = []
    return {
        "surface": surface,
        "result": result,
        "declared_requirements": declared,
        "blocking_requirements": blocking,
        "advisory_requirements": advisory,
        "summary": summary,
        "missing_inputs": missing_inputs,
        "fallback_to": fallback_to,
    }


def load_repo_interop_contract(repo_interop: object, *, target_root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(repo_interop, dict):
        return None, ["governance_surface.repo_interop"]
    availability = repo_interop.get("availability")
    if availability == "absent":
        return None, ["repo interop contract is absent"]
    if availability == "incomplete":
        missing_inputs = repo_interop.get("missing_inputs")
        return None, list(missing_inputs) if isinstance(missing_inputs, list) else ["repo interop contract is incomplete"]
    if availability != "present":
        return None, [f"unknown repo interop availability: {availability}"]

    contract_locator = repo_interop.get("contract")
    declared_locator = (
        contract_locator.get("locator")
        if isinstance(contract_locator, dict)
        else ".loom/companion/interop.json"
    )
    interop_path = target_root / str(declared_locator)
    try:
        payload = load_json_file(interop_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None, [f"missing repo interop contract: {interop_path}"]
    if not isinstance(payload, dict):
        return None, [f"repo interop contract is unreadable: {interop_path}"]
    return payload, []


def normalized_shadow_value(path: Path) -> tuple[str | None, str | None]:
    try:
        if path.is_dir():
            return None, f"shadow parity locator points to a directory: {path}"
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"cannot read shadow parity locator `{path}`: {exc.strerror or exc}"
    if not raw_text.strip():
        return None, f"shadow parity locator is empty: {path}"

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        for key in ("parity_value", "result", "decision", "status", "verdict", "value"):
            value = payload.get(key)
            if isinstance(value, (str, int, float, bool)) and str(value).strip():
                return str(value).strip().lower(), None
        return json.dumps(payload, ensure_ascii=False, sort_keys=True), None
    if isinstance(payload, list):
        return json.dumps(payload, ensure_ascii=False, sort_keys=True), None
    if isinstance(payload, (str, int, float, bool)) and str(payload).strip():
        return str(payload).strip().lower(), None

    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped.lower(), None
    return None, f"shadow parity locator does not expose a comparable value: {path}"


def shadow_parity_report(
    repo_interop: object,
    *,
    target_root: Path,
    surface: str,
) -> dict[str, Any]:
    empty_report = {
        "surface": surface,
        "result": "unreadable",
        "classification": "gate_failure",
        "blocking": False,
        "summary": "shadow parity could not be evaluated for this surface.",
        "missing_inputs": [],
        "recommended_action": "restore the declared Loom and repo-native shadow parity locators before treating this surface as authoritative.",
        "host_adapters": [],
        "repo_native_carriers": [],
        "loom_surface": {
            "status": "missing",
            "locator": "unknown",
            "normalized_value": None,
        },
        "repo_surface": {
            "status": "missing",
            "locator": "unknown",
            "normalized_value": None,
        },
    }
    interop_payload, interop_errors = load_repo_interop_contract(repo_interop, target_root=target_root)
    if interop_errors:
        return {
            **empty_report,
            "summary": "shadow parity is unavailable because the repo interop contract is missing or incomplete.",
            "missing_inputs": interop_errors,
        }
    if not isinstance(interop_payload, dict):
        return empty_report

    host_adapters = interop_payload.get("host_adapters")
    repo_native_carriers = interop_payload.get("repo_native_carriers")
    shadow_surfaces = interop_payload.get("shadow_surfaces")
    if not isinstance(host_adapters, list) or not isinstance(repo_native_carriers, list) or not isinstance(shadow_surfaces, dict):
        return {
            **empty_report,
            "summary": "shadow parity is unavailable because the repo interop contract cannot be consumed safely.",
            "missing_inputs": ["repo interop contract"],
        }

    relevant_host_adapters = [
        entry for entry in host_adapters if isinstance(entry, dict) and surface in entry.get("surfaces", [])
    ]
    relevant_repo_native_carriers = [
        entry for entry in repo_native_carriers if isinstance(entry, dict) and surface in entry.get("surfaces", [])
    ]
    declared_surface = shadow_surfaces.get(surface)
    if not isinstance(declared_surface, dict):
        return {
            **empty_report,
            "summary": "shadow parity is unavailable because this surface is not declared in the repo interop contract.",
            "missing_inputs": [f"shadow surface missing: {surface}"],
            "host_adapters": relevant_host_adapters,
            "repo_native_carriers": relevant_repo_native_carriers,
        }

    loom_locator = declared_surface.get("loom_locator")
    repo_locator = declared_surface.get("repo_locator")
    loom_path = target_root / str(loom_locator)
    repo_path = target_root / str(repo_locator)

    loom_value, loom_error = normalized_shadow_value(loom_path)
    repo_value, repo_error = normalized_shadow_value(repo_path)

    missing_inputs: list[str] = []
    if loom_error:
        missing_inputs.append(loom_error)
    if repo_error:
        missing_inputs.append(repo_error)

    loom_surface = {
        "status": "readable" if loom_error is None else "missing",
        "locator": str(loom_locator),
        "normalized_value": loom_value,
    }
    repo_surface = {
        "status": "readable" if repo_error is None else "missing",
        "locator": str(repo_locator),
        "normalized_value": repo_value,
    }

    if loom_error or repo_error or loom_value is None or repo_value is None:
        return {
            **empty_report,
            "summary": "shadow parity is unreadable because one or both declared surfaces cannot be normalized.",
            "missing_inputs": missing_inputs,
            "host_adapters": relevant_host_adapters,
            "repo_native_carriers": relevant_repo_native_carriers,
            "loom_surface": loom_surface,
            "repo_surface": repo_surface,
        }
    if loom_value == repo_value:
        return {
            "surface": surface,
            "result": "match",
            "classification": None,
            "blocking": False,
            "summary": "Loom and repo-native surfaces report the same normalized result.",
            "missing_inputs": [],
            "recommended_action": "no shadow parity action required.",
            "host_adapters": relevant_host_adapters,
            "repo_native_carriers": relevant_repo_native_carriers,
            "loom_surface": loom_surface,
            "repo_surface": repo_surface,
        }
    return {
        "surface": surface,
        "result": "mismatch",
        "classification": "drift",
        "blocking": False,
        "summary": "Loom and repo-native surfaces disagree on the normalized result.",
        "missing_inputs": [],
        "recommended_action": "resolve the parity mismatch or explicitly choose the authoritative surface outside repo interop before enabling blocking consumption.",
        "host_adapters": relevant_host_adapters,
        "repo_native_carriers": relevant_repo_native_carriers,
        "loom_surface": loom_surface,
        "repo_surface": repo_surface,
    }


def normalize_checkpoint(raw: str) -> str:
    lowered = raw.strip().lower()
    if "commit checkpoint" in lowered or "admission checkpoint" in lowered:
        return "admission"
    if "build checkpoint" in lowered:
        return "build"
    if "merge checkpoint" in lowered:
        return "merge"
    if "retired" in lowered:
        return "retired"
    return lowered.replace(" checkpoint", "").strip()


def checkpoint_rank(name: str) -> int:
    ranks = {
        "admission": 1,
        "build": 2,
        "merge": 3,
        "retired": 99,
    }
    return ranks.get(name, -1)


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    if not (root / ".git").exists():
        return None
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None


def run_process(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def git_branch(root: Path) -> str | None:
    result = run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if result is None or result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def git_head_sha(root: Path) -> str | None:
    result = run_git(root, ["rev-parse", "HEAD"])
    if result is None or result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


def git_changed_paths(root: Path, base: str, head: str) -> tuple[list[str], list[str]]:
    result = run_git(root, ["diff", "--name-only", "--no-renames", f"{base}..{head}"])
    if result is None:
        return [], ["git is unavailable while comparing reviewed HEAD to current HEAD"]
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git diff failed"
        return [], [detail]
    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return paths, []


def git_tracked_diff_fingerprint(root: Path) -> tuple[str | None, list[str]]:
    result = run_git(root, ["diff", "--binary", "--no-ext-diff", "HEAD", "--"])
    if result is None:
        return None, ["git is unavailable while fingerprinting tracked changes"]
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git diff failed"
        return None, [detail]
    return result.stdout, []


def git_remote_origin(root: Path) -> str | None:
    result = run_git(root, ["remote", "get-url", "origin"])
    if result is None or result.returncode != 0:
        return None
    remote = result.stdout.strip()
    return remote or None


def detect_github_repo(root: Path) -> tuple[str | None, str | None]:
    remote = git_remote_origin(root)
    if not remote:
        return None, None
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", remote)
    if not match:
        return None, None
    return match.group("owner"), match.group("repo")


def read_text_file(path_str: str) -> tuple[str | None, list[str]]:
    path = Path(path_str).expanduser()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"failed to read {path}: {exc.strerror or exc}"]
    return text, []


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cleanup_scratch_tree(target_root: Path, scratch_dir: Path) -> None:
    shutil.rmtree(scratch_dir, ignore_errors=True)
    for candidate in (scratch_dir.parent, scratch_dir.parent.parent):
        try:
            candidate.relative_to(target_root)
        except ValueError:
            continue
        try:
            candidate.rmdir()
        except OSError:
            pass


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


def github_issue_state(value: Any) -> str:
    return str(value or "unknown").upper()


def github_pr_state(payload: dict[str, Any]) -> str:
    if payload.get("merged_at"):
        return "MERGED"
    return str(payload.get("state") or "unknown").upper()


def normalize_rest_issue(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": payload.get("node_id"),
        "databaseId": payload.get("id"),
        "number": payload.get("number"),
        "state": github_issue_state(payload.get("state")),
        "title": payload.get("title"),
        "body": payload.get("body"),
        "url": payload.get("html_url"),
    }


def normalize_rest_pr(payload: dict[str, Any]) -> dict[str, Any]:
    head = payload.get("head") if isinstance(payload.get("head"), dict) else {}
    base = payload.get("base") if isinstance(payload.get("base"), dict) else {}
    merge_commit_sha = payload.get("merge_commit_sha")
    return {
        "number": payload.get("number"),
        "state": github_pr_state(payload),
        "title": payload.get("title"),
        "body": payload.get("body"),
        "url": payload.get("html_url"),
        "isDraft": bool(payload.get("draft")),
        "mergedAt": payload.get("merged_at"),
        "mergeCommit": {"oid": merge_commit_sha} if isinstance(merge_commit_sha, str) and merge_commit_sha else None,
        "mergeStateStatus": str(payload.get("mergeable_state")).upper() if payload.get("mergeable_state") else None,
        "headRefName": head.get("ref"),
        "baseRefName": base.get("ref"),
    }


def github_issue_payload(root: Path, owner: str, repo_name: str, issue_number: int) -> tuple[dict[str, Any] | None, list[str]]:
    payload, errors = gh_rest_json(root, f"repos/{owner}/{repo_name}/issues/{issue_number}")
    if errors or payload is None:
        return None, errors
    return normalize_rest_issue(payload), []


def github_pr_payload(root: Path, owner: str, repo_name: str, pr_number: int) -> tuple[dict[str, Any] | None, list[str]]:
    payload, errors = gh_rest_json(root, f"repos/{owner}/{repo_name}/pulls/{pr_number}")
    if errors or payload is None:
        return None, errors
    return normalize_rest_pr(payload), []


def github_branch_payload(root: Path, owner: str, repo_name: str, branch_name: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload, errors = gh_rest_json(root, f"repos/{owner}/{repo_name}/branches/{quote(branch_name, safe='')}")
    if errors or payload is None:
        return None, errors
    commit = payload.get("commit") if isinstance(payload.get("commit"), dict) else {}
    return {
        "name": payload.get("name") or branch_name,
        "protected": bool(payload.get("protected")),
        "commit": {"sha": commit.get("sha")} if isinstance(commit.get("sha"), str) else None,
    }, []


def gh_json_list(root: Path, args: list[str], key: str) -> tuple[list[dict[str, Any]], list[str]]:
    payload, errors = gh_json(root, args)
    if errors or payload is None:
        return [], errors
    value = payload.get(key)
    if not isinstance(value, list):
        return [], [f"gh {' '.join(args)} is missing `{key}`"]
    return [entry for entry in value if isinstance(entry, dict)], []


def gh_graphql(root: Path, query: str, variables: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-F", f"{key}={value}"])
    payload, errors = gh_json(root, args)
    if errors or payload is None:
        return None, errors
    data = payload.get("data")
    if not isinstance(data, dict):
        return None, ["gh api graphql is missing `data`"]
    return data, []


def graphql_budget_guard(scope: str, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "graphql_only": True,
        "budget_scope": scope,
        "status": "unavailable" if errors else "guarded",
        "errors": list(errors or []),
        "fallback_to": "manual-reconciliation" if errors else None,
        "recommended_action": (
            "Retry this GraphQL-only host read with explicit operator intent, or continue with REST-backed issue/PR evidence when ProjectV2/native sub-issue data is not required."
            if errors
            else "Use this GraphQL-only host read sparingly; high-frequency repo, issue, and PR reads must stay on REST."
        ),
    }


def git_dirty_entries(root: Path) -> list[dict[str, str]]:
    result = run_git(root, ["status", "--porcelain=v1"])
    if result is None or result.returncode != 0:
        return []

    entries: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        remainder = line[3:]
        path_text = remainder.split(" -> ", 1)[-1].strip()
        if not path_text:
            continue
        entries.append({"status": status, "path": path_text})
    return entries


def git_tracked_files(root: Path, relative: str) -> list[str]:
    result = run_git(root, ["ls-files", "--", relative])
    if result is None or result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def relative_to_root(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def resolve_workspace_path(target_root: Path, workspace_entry: str) -> tuple[Path | None, list[str]]:
    errors: list[str] = []
    raw = Path(workspace_entry)
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        resolved = (target_root / raw).resolve()
    try:
        resolved.relative_to(target_root.resolve())
    except ValueError:
        return None, [f"workspace entry escapes target root: {workspace_entry}"]
    return resolved, errors


def current_cwd_relative(target_root: Path) -> str | None:
    cwd = Path.cwd().resolve()
    try:
        return str(cwd.relative_to(target_root.resolve()))
    except ValueError:
        return None


def update_markdown_bullet(path: Path, label: str, value: str) -> None:
    pattern = re.compile(rf"(?m)^- {re.escape(label)}:\s*.*$")
    replacement = f"- {label}: {value}"
    text = path.read_text(encoding="utf-8")
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"unable to update `{label}` in {path}")
    path.write_text(updated, encoding="utf-8")


def replace_markdown_section(path: Path, section_name: str, new_lines: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(?ms)(^## {re.escape(section_name)}\n\n)(.*?)(?=^## |\Z)"
    )
    replacement = "\\1" + "\n".join(new_lines).rstrip() + "\n\n"
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"unable to update `{section_name}` in {path}")
    path.write_text(updated, encoding="utf-8")


def render_status_surface(report: dict[str, Any], runtime_evidence: dict[str, dict[str, Any]]) -> str:
    facts = report["facts"]
    status_path = report["fact_chain"]["entry_points"]["status_surface"]
    return (
        "# Current Status\n\n"
        "## Derived Fact Chain View\n\n"
        f"- Item ID: {facts['item_id']['value']}\n"
        f"- Goal: {facts['goal']['value']}\n"
        f"- Scope: {facts['scope']['value']}\n"
        f"- Execution Path: {facts['execution_path']['value']}\n"
        f"- Workspace Entry: {facts['workspace_entry']['value']}\n"
        f"- Recovery Entry: {facts['recovery_entry']['value']}\n"
        f"- Review Entry: {facts['review_entry']['value']}\n"
        f"- Validation Entry: {facts['validation_entry']['value']}\n"
        f"- Closing Condition: {facts['closing_condition']['value']}\n"
        f"- Current Checkpoint: {facts['current_checkpoint']['value']}\n"
        f"- Current Stop: {facts['current_stop']['value']}\n"
        f"- Next Step: {facts['next_step']['value']}\n"
        f"- Blockers: {facts['blockers']['value']}\n"
        f"- Latest Validation Summary: {facts['latest_validation_summary']['value']}\n"
        f"- Recovery Boundary: {facts['recovery_boundary']['value']}\n"
        f"- Current Lane: {facts['current_lane']['value']}\n\n"
        "## Runtime Evidence\n\n"
        f"- Run Entry: {runtime_evidence['run_entry']['value']}\n"
        f"- Logs Entry: {runtime_evidence['logs_entry']['value']}\n"
        f"- Diagnostics Entry: {runtime_evidence['diagnostics_entry']['value']}\n"
        f"- Verification Entry: {runtime_evidence['verification_entry']['value']}\n"
        f"- Lane Entry: {runtime_evidence['lane_entry']['value']}\n\n"
        "## Sources\n\n"
        f"- Static Truth: {report['fact_chain']['entry_points']['work_item']}\n"
        f"- Dynamic Truth: {report['fact_chain']['entry_points']['recovery_entry']}\n"
        "- Locator Truth: .loom/bootstrap/init-result.json\n"
        f"- Fact Chain CLI: {report['fact_chain']['read_entry']}\n"
    )


def sync_status_surface(target_root: Path, output_relative: str, runtime_evidence: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    output_path = target_root / output_relative
    try:
        init_result = load_json_file(output_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {}, [f"invalid init-result JSON: {exc}"]

    fact_chain = init_result.get("fact_chain")
    if not isinstance(fact_chain, dict):
        return {}, ["init-result is missing required section: fact_chain"]
    entry_points = fact_chain.get("entry_points")
    if not isinstance(entry_points, dict):
        return {}, ["init-result.fact_chain.entry_points must be an object"]

    work_item_ref = str(entry_points.get("work_item", ""))
    recovery_ref = str(entry_points.get("recovery_entry", ""))
    status_ref = str(entry_points.get("status_surface", ""))
    work_item_path = target_root / work_item_ref
    recovery_path = target_root / recovery_ref
    status_path = target_root / status_ref
    if not work_item_path.exists() or not recovery_path.exists():
        return {}, ["fact-chain carrier is missing during status sync"]
    work_item, work_item_errors = parse_work_item(work_item_path, target_root)
    recovery_entry, recovery_errors = parse_recovery_entry(recovery_path, target_root)
    errors = [*work_item_errors, *recovery_errors]
    if errors:
        return {}, errors
    pseudo_report = {
        "fact_chain": {
            "read_entry": str(fact_chain.get("read_entry", "python3 .loom/bin/loom_init.py fact-chain --target .")),
            "entry_points": {
                "work_item": work_item_ref,
                "recovery_entry": recovery_ref,
                "status_surface": status_ref,
            },
        },
        "facts": {
            "item_id": {"value": str(work_item["item_id"])},
            "goal": {"value": str(work_item["goal"])},
            "scope": {"value": str(work_item["scope"])},
            "execution_path": {"value": str(work_item["execution_path"])},
            "workspace_entry": {"value": str(work_item["workspace_entry"])},
            "recovery_entry": {"value": str(work_item["recovery_entry"])},
            "review_entry": {"value": str(work_item["review_entry"])},
            "validation_entry": {"value": str(work_item["validation_entry"])},
            "closing_condition": {"value": str(work_item["closing_condition"])},
            "current_checkpoint": {"value": recovery_entry["current_checkpoint"]},
            "current_stop": {"value": recovery_entry["current_stop"]},
            "next_step": {"value": recovery_entry["next_step"]},
            "blockers": {"value": recovery_entry["blockers"]},
            "latest_validation_summary": {"value": recovery_entry["latest_validation_summary"]},
            "recovery_boundary": {"value": recovery_entry["recovery_boundary"]},
            "current_lane": {"value": recovery_entry["current_lane"]},
        },
    }
    status_path.write_text(render_status_surface(pseudo_report, runtime_evidence), encoding="utf-8")
    refreshed, refresh_errors = load_fact_chain_report(target_root, output_relative)
    if refresh_errors:
        return {}, refresh_errors
    return refreshed, []


def read_runtime_evidence(target_root: Path, status_relative: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    status_path = target_root / status_relative
    if not status_path.exists():
        return {}, [f"missing status surface: {status_relative}"]
    sections = markdown_sections(status_path)
    values, errors = parse_key_value_section(
        sections,
        "Runtime Evidence",
        {
            "Run Entry": "run_entry",
            "Logs Entry": "logs_entry",
            "Diagnostics Entry": "diagnostics_entry",
            "Verification Entry": "verification_entry",
            "Lane Entry": "lane_entry",
        },
        status_relative,
    )
    if errors:
        return {}, errors
    return {
        key: {
            "value": values[key],
            "status": "not_applicable" if values[key] == "not_applicable" else "present",
        }
        for key in RUNTIME_EVIDENCE_FIELDS
    }, []


def default_review_path(item_id: str) -> str:
    return f".loom/reviews/{item_id}.json"


def default_spec_review_path(item_id: str) -> str:
    return f".loom/reviews/{item_id}.spec.json"


def allowed_post_review_carrier_paths(context: dict[str, Any], *review_paths: str) -> set[str]:
    return {
        *review_paths,
        str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"]),
        str(context["report"]["fact_chain"]["entry_points"]["status_surface"]),
    }


def formal_spec_path(context: dict[str, Any]) -> str | None:
    preferred = f".loom/specs/{context['item_id']}/spec.md"
    if (context["target_root"] / preferred).exists():
        return preferred

    for artifact in context.get("associated_artifacts", []):
        if isinstance(artifact, str) and artifact.endswith("/spec.md") and (context["target_root"] / artifact).exists():
            return artifact

    fallback = context["target_root"] / ".loom/specs/INIT-0001/spec.md"
    if fallback.exists():
        return ".loom/specs/INIT-0001/spec.md"
    return None


def spec_suite_paths(context: dict[str, Any]) -> dict[str, str]:
    item_id = context["item_id"]
    candidates = [
        {
            "spec": f".loom/specs/{item_id}/spec.md",
            "plan": f".loom/specs/{item_id}/plan.md",
            "implementation_contract": f".loom/specs/{item_id}/implementation-contract.md",
        },
        {
            "spec": ".loom/specs/INIT-0001/spec.md",
            "plan": ".loom/specs/INIT-0001/plan.md",
            "implementation_contract": ".loom/specs/INIT-0001/implementation-contract.md",
        },
    ]
    for suite in candidates:
        if (context["target_root"] / suite["spec"]).exists():
            return suite
    return candidates[0]


def review_head_binding(
    target_root: Path,
    *,
    reviewed_head: str | None,
    allowed_paths: set[str],
) -> tuple[dict[str, Any], list[str]]:
    current_head = git_head_sha(target_root)
    payload: dict[str, Any] = {
        "reviewed_head": reviewed_head,
        "current_head": current_head,
        "status": "unknown",
        "stale": None,
        "changed_paths": [],
        "disallowed_paths": [],
    }
    if not isinstance(reviewed_head, str) or not reviewed_head.strip():
        return payload, ["review artifact is missing reviewed_head"]
    if not isinstance(current_head, str) or not current_head.strip():
        return payload, ["current HEAD is unavailable"]
    if reviewed_head == current_head:
        payload["status"] = "current"
        payload["stale"] = False
        return payload, []

    changed_paths, head_errors = git_changed_paths(target_root, reviewed_head, current_head)
    if head_errors:
        return payload, [f"review HEAD comparison failed: {detail}" for detail in head_errors]

    payload["changed_paths"] = changed_paths
    disallowed_paths = [path for path in changed_paths if path not in allowed_paths]
    payload["disallowed_paths"] = disallowed_paths
    if changed_paths and not disallowed_paths:
        payload["status"] = "carrier-only"
        payload["stale"] = False
        return payload, []

    payload["status"] = "stale"
    payload["stale"] = True
    if not changed_paths:
        return payload, ["review artifact was recorded against a different HEAD"]
    return payload, ["review artifact is stale for the current HEAD"]


def spec_review_head_binding(
    context: dict[str, Any],
    *,
    reviewed_head: str | None,
    review_path: str,
) -> tuple[dict[str, Any], list[str]]:
    current_head = git_head_sha(context["target_root"])
    payload: dict[str, Any] = {
        "reviewed_head": reviewed_head,
        "current_head": current_head,
        "status": "unknown",
        "stale": None,
        "changed_paths": [],
        "spec_changed_paths": [],
    }
    if not isinstance(reviewed_head, str) or not reviewed_head.strip():
        return payload, ["review artifact is missing reviewed_head"]
    if not isinstance(current_head, str) or not current_head.strip():
        return payload, ["current HEAD is unavailable"]
    if reviewed_head == current_head:
        payload["status"] = "current"
        payload["stale"] = False
        return payload, []

    changed_paths, head_errors = git_changed_paths(context["target_root"], reviewed_head, current_head)
    if head_errors:
        return payload, [f"review HEAD comparison failed: {detail}" for detail in head_errors]

    suite = spec_suite_paths(context)
    watched_paths = {
        suite["spec"],
        suite["plan"],
        suite["implementation_contract"],
    }
    spec_changed_paths = [path for path in changed_paths if path in watched_paths]
    payload["changed_paths"] = changed_paths
    payload["spec_changed_paths"] = spec_changed_paths
    if spec_changed_paths:
        payload["status"] = "stale"
        payload["stale"] = True
        return payload, ["spec review is stale because the formal spec path changed after approval"]

    payload["status"] = "implementation-drift-only"
    payload["stale"] = False
    return payload, []


def review_gate_payload(
    context: dict[str, Any],
    *,
    review_path: str,
    expected_kind: str,
    gate_name: str,
    required: bool,
    path_label: str | None = None,
) -> dict[str, Any]:
    review_record, _, review_errors = load_review_record(
        context["target_root"],
        context["item_id"],
        review_path,
    )
    head_binding = {
        "reviewed_head": None,
        "current_head": git_head_sha(context["target_root"]),
        "status": "unknown",
        "stale": None,
        "changed_paths": [],
        "disallowed_paths": [],
    }
    missing_inputs: list[str] = []
    result = "pass" if required else "not_applicable"
    fallback_to: str | None = None

    if path_label is not None and not path_label.strip():
        missing_inputs.append(f"missing formal {gate_name.replace('_', ' ')} path")
        result = "block"
        fallback_to = "build"

    if review_errors:
        missing_inputs.extend(review_errors)
        result = "block"
        fallback_to = "build"
    elif review_record is None:
        if required:
            missing_inputs.append(f"missing {gate_name.replace('_', ' ')} artifact: {review_path}")
            result = "block"
            fallback_to = "build"
    else:
        if review_record.get("kind") != expected_kind:
            missing_inputs.append(
                f"{gate_name.replace('_', ' ')} artifact must declare kind `{expected_kind}`"
            )
            result = "block"
            fallback_to = "build"
        decision = review_record.get("decision")
        if decision == "allow":
            if expected_kind == "spec_review":
                binding_payload, binding_errors = spec_review_head_binding(
                    context,
                    reviewed_head=review_record.get("reviewed_head"),
                    review_path=review_path,
                )
            else:
                binding_payload, binding_errors = review_head_binding(
                    context["target_root"],
                    reviewed_head=review_record.get("reviewed_head"),
                    allowed_paths=allowed_post_review_carrier_paths(context, review_path),
                )
            head_binding = binding_payload
            if binding_errors:
                missing_inputs.extend(binding_errors)
                result = "block"
                fallback_to = "build"
        elif decision == "fallback":
            missing_inputs.append(f"{gate_name.replace('_', ' ')} decision is fallback: {review_record['summary']}")
            result = "fallback"
            fallback_to = review_record.get("fallback_to") or "build"
        else:
            missing_inputs.append(f"{gate_name.replace('_', ' ')} decision is blocking: {review_record['summary']}")
            result = "block"
            fallback_to = "build"

    summary = (
        f"{gate_name.replace('_', ' ')} is not required for the current item."
        if result == "not_applicable"
        else (
            f"{gate_name.replace('_', ' ')} is approved for the current HEAD."
            if result == "pass"
            else f"{gate_name.replace('_', ' ')} is missing, stale, or not approved."
        )
    )
    return {
        "path": review_path,
        "required": required,
        **({"formal_spec_path": path_label} if path_label is not None else {}),
        "result": result,
        "summary": summary,
        "missing_inputs": missing_inputs,
        "fallback_to": fallback_to,
        "record": review_record,
        "head_binding": head_binding,
    }


def spec_review_gate_payload(context: dict[str, Any]) -> dict[str, Any]:
    spec_path = formal_spec_path(context)
    return review_gate_payload(
        context,
        review_path=default_spec_review_path(context["item_id"]),
        expected_kind="spec_review",
        gate_name="spec_review",
        required=spec_path is not None,
        path_label=spec_path,
    )


def implementation_review_status_payload(context: dict[str, Any]) -> dict[str, Any]:
    review_record, review_path, review_errors = load_review_record(
        context["target_root"],
        context["item_id"],
        context["review_entry"],
    )
    missing_inputs = list(review_errors)
    head_binding = {
        "reviewed_head": None,
        "current_head": git_head_sha(context["target_root"]),
        "status": "unknown",
        "stale": None,
        "changed_paths": [],
        "disallowed_paths": [],
    }
    result = "pass"
    fallback_to: str | None = None
    if review_record is None and not review_errors:
        missing_inputs.append(f"missing implementation review artifact: {review_path}")
        result = "block"
        fallback_to = "build"
    elif review_record is not None:
        if review_record.get("kind") not in {"general_review", "code_review"}:
            missing_inputs.append("implementation review artifact must declare kind `general_review` or `code_review`")
            result = "block"
            fallback_to = "build"
        binding_payload, binding_errors = review_head_binding(
            context["target_root"],
            reviewed_head=review_record.get("reviewed_head"),
            allowed_paths=allowed_post_review_carrier_paths(context, review_path),
        )
        head_binding = binding_payload
        if binding_errors:
            missing_inputs.extend(binding_errors)
            result = "block"
            fallback_to = "build"
    if review_record is not None and review_record.get("decision") == "block":
        missing_inputs.append(f"implementation review decision is blocking: {review_record['summary']}")
        result = "block"
        fallback_to = "build"
    elif review_record is not None and review_record.get("decision") == "fallback":
        missing_inputs.append(f"implementation review decision is fallback: {review_record['summary']}")
        result = "fallback"
        fallback_to = review_record.get("fallback_to") or "build"
    return {
        "path": review_path,
        "result": result,
        "summary": (
            "implementation review is approved for the current HEAD."
            if result == "pass"
            else "implementation review is missing, stale, or not approved."
        ),
        "missing_inputs": missing_inputs,
        "fallback_to": fallback_to,
        "record": review_record,
        "head_binding": head_binding,
    }


def compat_findings_from_lists(
    *,
    decision: str | None,
    blocking_issues: list[str],
    follow_ups: list[str],
) -> list[dict[str, Any]]:
    del decision
    findings: list[dict[str, Any]] = []
    for index, summary in enumerate(blocking_issues, start=1):
        findings.append(
            {
                "id": f"compat-block-{index}",
                "summary": summary,
                "severity": "block",
                "rebuttal": None,
                "disposition": {
                    "status": "rejected",
                    "summary": "Projected from compatibility `blocking_issues`.",
                },
            }
        )
    for index, summary in enumerate(follow_ups, start=1):
        findings.append(
            {
                "id": f"compat-follow-up-{index}",
                "summary": summary,
                "severity": "warn",
                "rebuttal": None,
                "disposition": {
                    "status": "deferred",
                    "summary": "Projected from compatibility `follow_ups`.",
                },
            }
        )
    return findings


def compat_lists_from_findings(findings: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    blocking_issues: list[str] = []
    follow_ups: list[str] = []
    for finding in findings:
        summary = finding.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            continue
        if finding.get("severity") == "block":
            blocking_issues.append(summary.strip())
        elif finding.get("severity") == "warn":
            follow_ups.append(summary.strip())
    return blocking_issues, follow_ups


def normalize_review_findings(raw_findings: Any, *, relative: str) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(raw_findings, list):
        return [], [f"review artifact `{relative}` `findings` must be a list"]

    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, finding in enumerate(raw_findings, start=1):
        if not isinstance(finding, dict):
            errors.append(f"review artifact `{relative}` findings[{index}] must be a JSON object")
            continue
        normalized = dict(finding)
        finding_id = normalized.get("id")
        summary = normalized.get("summary")
        severity = normalized.get("severity")
        rebuttal = normalized.get("rebuttal")
        disposition = normalized.get("disposition")
        if not isinstance(finding_id, str) or not finding_id.strip():
            errors.append(f"review artifact `{relative}` findings[{index}] must include non-empty `id`")
        else:
            normalized["id"] = finding_id.strip()
        if not isinstance(summary, str) or not summary.strip():
            errors.append(f"review artifact `{relative}` findings[{index}] must include non-empty `summary`")
        else:
            normalized["summary"] = summary.strip()
        if severity not in REVIEW_FINDING_SEVERITIES:
            errors.append(
                f"review artifact `{relative}` findings[{index}] severity must be one of "
                f"{', '.join(sorted(REVIEW_FINDING_SEVERITIES))}"
            )
        if rebuttal is not None:
            if not isinstance(rebuttal, str) or not rebuttal.strip():
                errors.append(f"review artifact `{relative}` findings[{index}] `rebuttal` must be null or a non-empty string")
            else:
                normalized["rebuttal"] = rebuttal.strip()
        if disposition is not None:
            if not isinstance(disposition, dict):
                errors.append(f"review artifact `{relative}` findings[{index}] `disposition` must be null or an object")
            else:
                status = disposition.get("status")
                disposition_summary = disposition.get("summary")
                if status not in REVIEW_FINDING_DISPOSITION_STATUSES:
                    errors.append(
                        f"review artifact `{relative}` findings[{index}] disposition status must be one of "
                        f"{', '.join(sorted(REVIEW_FINDING_DISPOSITION_STATUSES))}"
                    )
                if not isinstance(disposition_summary, str) or not disposition_summary.strip():
                    errors.append(
                        f"review artifact `{relative}` findings[{index}] disposition must include non-empty `summary`"
                    )
                else:
                    normalized["disposition"] = {
                        **disposition,
                        "status": status,
                        "summary": disposition_summary.strip(),
                    }
        findings.append(normalized)
    return findings, errors


def target_relative_label(target_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(target_root.resolve()))
    except ValueError:
        return str(path.resolve())


def load_findings_file(target_root: Path, findings_file: str) -> tuple[list[dict[str, Any]] | None, list[str]]:
    findings_path = Path(findings_file).expanduser()
    if not findings_path.is_absolute():
        findings_path = (target_root / findings_path).resolve()

    label = target_relative_label(target_root, findings_path)
    try:
        payload = json.loads(findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"invalid findings file `{label}`: {exc}"]

    if isinstance(payload, dict):
        payload = payload.get("findings")

    findings, errors = normalize_review_findings(payload, relative=label)
    if errors:
        return None, errors
    return findings, []


def load_review_record(
    target_root: Path,
    item_id: str,
    review_file: str | None = None,
) -> tuple[dict[str, Any] | None, str, list[str]]:
    relative = review_file or default_review_path(item_id)
    review_path = target_root / relative
    if not review_path.exists():
        return None, relative, []
    try:
        payload = load_json_file(review_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, relative, [f"invalid review artifact `{relative}`: {exc}"]
    if not isinstance(payload, dict):
        return None, relative, [f"review artifact `{relative}` must be a JSON object"]
    errors: list[str] = []
    for field in ("item_id", "decision", "kind", "summary", "reviewer", "reviewed_head", "reviewed_validation_summary"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"review artifact `{relative}` is missing `{field}`")
    if payload.get("item_id") != item_id:
        errors.append(f"review artifact `{relative}` item_id does not match `{item_id}`")
    if payload.get("decision") not in REVIEW_DECISIONS:
        errors.append(f"review artifact `{relative}` decision must be one of {', '.join(sorted(REVIEW_DECISIONS))}")
    if payload.get("kind") not in REVIEW_KINDS:
        errors.append(f"review artifact `{relative}` kind must be one of {', '.join(sorted(REVIEW_KINDS))}")
    fallback_to = payload.get("fallback_to")
    if fallback_to not in {None, "admission", "build", "merge"}:
        errors.append(f"review artifact `{relative}` fallback_to must be null, admission, build, or merge")
    compatibility_lists: dict[str, list[str]] = {}
    for list_field in ("blocking_issues", "follow_ups"):
        value = payload.get(list_field)
        if value is not None and not isinstance(value, list):
            errors.append(f"review artifact `{relative}` `{list_field}` must be a list when present")
            continue
        entries: list[str] = []
        for index, entry in enumerate(value or [], start=1):
            if not isinstance(entry, str) or not entry.strip():
                errors.append(f"review artifact `{relative}` `{list_field}`[{index}] must be a non-empty string")
                continue
            entries.append(entry.strip())
        compatibility_lists[list_field] = entries

    findings_value = payload.get("findings")
    if findings_value is None:
        findings = compat_findings_from_lists(
            decision=payload.get("decision") if isinstance(payload.get("decision"), str) else None,
            blocking_issues=compatibility_lists.get("blocking_issues", []),
            follow_ups=compatibility_lists.get("follow_ups", []),
        )
    else:
        findings, finding_errors = normalize_review_findings(findings_value, relative=relative)
        errors.extend(finding_errors)

    blocking_issues, follow_ups = compat_lists_from_findings(findings)
    normalized_payload = dict(payload)
    normalized_payload["findings"] = findings
    normalized_payload["blocking_issues"] = blocking_issues
    normalized_payload["follow_ups"] = follow_ups
    return normalized_payload, relative, errors


def build_review_flow_payload(
    target_root: Path,
    output_relative: str,
    expected_item: str | None,
    *,
    operation: str = "review",
) -> dict[str, Any]:
    runtime_state = runtime_state_payload(target_root)
    steps: list[dict[str, Any]] = [
        {
            "name": "runtime-state",
            "result": runtime_state["result"],
            "summary": runtime_state["summary"],
            "missing_inputs": runtime_state["missing_inputs"],
            "fallback_to": runtime_state["fallback_to"],
        }
    ]
    if runtime_state["result"] != "pass":
        return {
            "command": "flow",
            "operation": operation,
            "result": "block",
            "summary": "flow command is blocked because the Loom runtime state is inconsistent.",
            "missing_inputs": runtime_state["missing_inputs"],
            "fallback_to": runtime_state["fallback_to"],
            "steps": steps,
            "runtime_state": runtime_state,
        }

    context, errors = load_context(target_root, output_relative, expected_item)
    if errors:
        return {
            "command": "flow",
            "operation": operation,
            "result": "block",
            "summary": "flow command could not read a valid Loom fact chain.",
            "missing_inputs": [f"fact-chain: {message}" for message in errors],
            "fallback_to": "admission",
            "steps": steps,
            "runtime_state": runtime_state,
        }

    steps.append(
        {
            "name": "fact-chain",
            "result": "pass",
            "summary": "fact chain is readable from a single entry.",
            "missing_inputs": [],
            "fallback_to": None,
        }
    )

    state_payload = state_check_payload(context)
    steps.append(
        {
            "name": "state-check",
            "result": state_payload["result"],
            "summary": state_payload["summary"],
            "missing_inputs": state_payload["missing_inputs"],
            "fallback_to": state_payload["fallback_to"],
        }
    )

    runtime_fields, runtime_missing = runtime_evidence_from_report(context["report"])
    runtime_result = "pass" if not runtime_missing else "block"
    steps.append(
        {
            "name": "runtime-evidence",
            "result": runtime_result,
            "summary": (
                "runtime evidence entries are readable."
                if runtime_result == "pass"
                else "runtime evidence entries are incomplete or inconsistent."
            ),
            "missing_inputs": runtime_missing,
            "fallback_to": "admission" if runtime_missing else None,
            "runtime_evidence": runtime_fields,
        }
    )

    build_payload = checkpoint_payload("build", context)
    governance_surface = build_governance_surface(target_root)
    surface_name = "review" if operation == "review" else "spec_review"
    repo_specific_requirements = repo_specific_requirements_payload(
        governance_surface.get("repo_interface"),
        target_root=target_root,
        surface=surface_name,
    )
    if operation == "spec-review":
        review_path = default_spec_review_path(context["item_id"])
        review_record, _, review_errors = load_review_record(target_root, context["item_id"], review_path)
        review_step_name = "spec-review-entry"
        review_step_result = "pass" if review_record and not review_errors else "block"
        review_step_summary = (
            "spec review artifact is readable and ready for authoring."
            if review_record and not review_errors
            else "spec review artifact is missing or invalid."
        )
        review_step_missing = review_errors or ([] if review_record else [f"missing review artifact: {review_path}"])
        review_step_fallback = "build" if (review_errors or review_record is None) else None
        review_payload = {
            "path": review_path,
            "record": review_record,
        }
        extra_steps: list[dict[str, Any]] = []
    else:
        review_path = context["review_entry"]
        review_record, _, review_errors = load_review_record(target_root, context["item_id"], review_path)
        review_payload = review_gate_payload(
            context,
            review_path=review_path,
            expected_kind=implementation_review_kind(context),
            gate_name="implementation_review",
            required=True,
        )
        spec_gate = spec_review_gate_payload(context)
        extra_steps = [
            {
                "name": "spec-review-gate",
                "result": (
                    "pass"
                    if spec_gate["result"] in {"pass", "not_applicable"}
                    else ("fallback" if spec_gate["result"] == "fallback" else "block")
                ),
                "summary": spec_gate["summary"],
                "missing_inputs": spec_gate["missing_inputs"],
                "fallback_to": spec_gate["fallback_to"],
            }
        ]
        review_step_name = "review-entry"
        review_step_result = "pass" if review_record and not review_errors else "block"
        review_step_summary = (
            "formal review artifact is readable."
            if review_record and not review_errors
            else "formal review artifact is missing or invalid."
        )
        review_step_missing = review_errors or ([] if review_record else [f"missing review artifact: {review_path}"])
        review_step_fallback = "build" if (review_errors or review_record is None) else None
    steps.extend(
        [
            {
                "name": "checkpoint-build",
                "result": build_payload["result"],
                "summary": build_payload["summary"],
                "missing_inputs": build_payload["missing_inputs"],
                "fallback_to": build_payload["fallback_to"],
            },
            *extra_steps,
            {
                "name": review_step_name,
                "result": review_step_result,
                "summary": review_step_summary,
                "missing_inputs": review_step_missing,
                "fallback_to": review_step_fallback,
            },
        ]
    )

    result = "pass"
    fallback_to: str | None = None
    for step in steps:
        step_result = step["result"]
        if step_result == "fallback":
            result = "fallback"
            fallback_to = step.get("fallback_to") or "admission"
            break
        if step_result == "block" and result == "pass":
            result = "block"
            fallback_to = step.get("fallback_to")
    if result != "block" and repo_specific_requirements["result"] == "block":
        result = "block"
        fallback_to = fallback_to or repo_specific_requirements["fallback_to"]

    if result == "block" and repo_specific_requirements["result"] == "block":
        summary = (
            "spec-review flow exposed companion-declared blocking requirements instead of pretending Loom core already covers them."
            if operation == "spec-review"
            else "review flow exposed companion-declared blocking requirements instead of pretending Loom core already covers them."
        )
    else:
        summary = (
            "spec-review flow prepared the formal spec review context and exposed the spec gate artifact."
            if operation == "spec-review" and result == "pass"
            else (
                "spec-review flow found missing spec review material or earlier blocking signals."
                if operation == "spec-review"
                else (
                    "review flow prepared the semantic review context and exposed the formal review artifact."
                    if result == "pass"
                    else "review flow found missing review material or earlier blocking signals."
                )
            )
        )

    missing_inputs: list[str] = []
    for step in steps:
        if step["result"] in {"block", "fallback"}:
            for message in step.get("missing_inputs", []):
                if message not in missing_inputs:
                    missing_inputs.append(message)
    if repo_specific_requirements["result"] == "block":
        for message in repo_specific_requirements.get("missing_inputs", []):
            if message not in missing_inputs:
                missing_inputs.append(message)

    return {
        "command": "flow",
        "operation": operation,
        "item": {
            "id": context["item_id"],
            "goal": context["goal"],
            "scope": context["scope"],
            "execution_path": context["execution_path"],
        },
        "result": result,
        "summary": summary,
        "missing_inputs": missing_inputs,
        "fallback_to": fallback_to,
        "steps": steps,
        "runtime_state": runtime_state,
        "state_check": {
            "result": state_payload["result"],
            "summary": state_payload["summary"],
            "missing_inputs": state_payload["missing_inputs"],
            "fallback_to": state_payload["fallback_to"],
            "checks": state_payload["checks"],
        },
        "runtime_evidence": runtime_fields,
        "build_checkpoint": {
            "result": build_payload["result"],
            "summary": build_payload["summary"],
            "missing_inputs": build_payload["missing_inputs"],
            "fallback_to": build_payload["fallback_to"],
        },
        **(
            {
                "spec_review": review_payload,
            }
            if operation == "spec-review"
            else {
                "review": {
                    "path": review_path,
                    "record": review_record,
                },
                "spec_review": spec_gate,
            }
        ),
        "repo_specific_requirements": repo_specific_requirements,
        "current_checkpoint": {
            "raw": context["current_checkpoint_raw"],
            "normalized": context["current_checkpoint"],
        },
    }


def run_default_review_engine(
    context: dict[str, Any],
    build_payload: dict[str, Any],
    review_path: str,
    *,
    review_kind: str | None = None,
) -> dict[str, Any]:
    reviewed_head = git_head_sha(context["target_root"]) or "unknown-head"
    runtime_root = review_runtime_root(context, reviewed_head)
    prompt_path = runtime_root / "prompt.txt"
    result_path = runtime_root / "engine-result.json"
    findings_path = runtime_root / "normalized-findings.json"
    metadata_path = runtime_root / "engine-metadata.json"
    scratch_dir = context["target_root"] / ".loom/runtime/tmp" / "review-engine" / context["item_id"]
    prompt_text = build_default_review_prompt(
        context=context,
        build_payload=build_payload,
        runtime_fields=runtime_evidence_from_report(context["report"])[0],
        review_path=review_path,
    )
    runtime_root.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt_text, encoding="utf-8")

    effective_kind = review_kind or default_review_kind(context)

    before_fingerprint, fingerprint_errors = git_tracked_diff_fingerprint(context["target_root"])
    if fingerprint_errors:
        cleanup_scratch_tree(context["target_root"], scratch_dir)
        return {
            "result": "block",
            "summary": "default review engine could not verify tracked-change purity before execution.",
            "missing_inputs": [f"engine preflight: {message}" for message in fingerprint_errors],
            "fallback_to": None,
            "engine": {
                "engine": DEFAULT_REVIEW_ENGINE,
                "adapter": DEFAULT_REVIEW_ADAPTER,
                "result": "block",
                "failure_reason": "runtime_conflict",
                "reviewed_head": reviewed_head,
                "evidence": {
                    "runtime_root": relative_to_root(runtime_root, context["target_root"]),
                    "prompt": relative_to_root(prompt_path, context["target_root"]),
                    "raw_result": relative_to_root(result_path, context["target_root"]),
                    "normalized_findings": relative_to_root(findings_path, context["target_root"]),
                    "metadata": relative_to_root(metadata_path, context["target_root"]),
                },
            },
        }

    scratch_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    scratch_dir_text = str(scratch_dir.resolve())
    env["TMPDIR"] = scratch_dir_text
    env["TMP"] = scratch_dir_text
    env["TEMP"] = scratch_dir_text

    failure_reason: str | None = None
    failure_detail: str | None = None
    raw_payload: dict[str, Any] | None = None
    try:
        completed = subprocess.run(
            [
                DEFAULT_REVIEW_ENGINE,
                "exec",
                "-C",
                str(context["target_root"]),
                "-s",
                "workspace-write",
                "--output-schema",
                str(review_engine_schema_path()),
                "-o",
                str(result_path),
                "-",
            ],
            cwd=context["target_root"],
            env=env,
            input=prompt_text,
            text=True,
            capture_output=True,
            check=False,
            timeout=DEFAULT_REVIEW_ENGINE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        failure_reason = "engine_unavailable"
        failure_detail = f"default review engine `{DEFAULT_REVIEW_ENGINE}` is unavailable in PATH"
    except subprocess.TimeoutExpired:
        failure_reason = "runtime_conflict"
        failure_detail = (
            f"default review engine timed out after {DEFAULT_REVIEW_ENGINE_TIMEOUT_SECONDS}s"
        )
    else:
        if completed.returncode != 0:
            failure_reason = "runtime_conflict"
            failure_detail = completed.stderr.strip() or completed.stdout.strip() or "default review engine returned a non-zero exit status"
        else:
            try:
                if result_path.exists():
                    raw_payload = load_json_file(result_path)
                elif completed.stdout.strip():
                    raw_payload = json.loads(completed.stdout)
                else:
                    failure_reason = "schema_drift"
                    failure_detail = "default review engine did not emit a structured result"
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                failure_reason = "schema_drift"
                failure_detail = f"default review engine returned invalid JSON: {exc}"

    after_fingerprint, after_errors = git_tracked_diff_fingerprint(context["target_root"])
    if after_errors and failure_reason is None:
        failure_reason = "runtime_conflict"
        failure_detail = after_errors[0]
    elif failure_reason is None and before_fingerprint != after_fingerprint:
        failure_reason = "repo_diff_detected"
        failure_detail = "default review engine modified tracked repository content"

    if failure_reason is None and raw_payload is None:
        failure_reason = "schema_drift"
        failure_detail = "default review engine did not produce a readable review result"

    engine_evidence = {
        "runtime_root": relative_to_root(runtime_root, context["target_root"]),
        "prompt": relative_to_root(prompt_path, context["target_root"]),
        "raw_result": relative_to_root(result_path, context["target_root"]),
        "normalized_findings": relative_to_root(findings_path, context["target_root"]),
        "metadata": relative_to_root(metadata_path, context["target_root"]),
    }

    if failure_reason is not None:
        write_json_file(
            metadata_path,
            {
                "engine": DEFAULT_REVIEW_ENGINE,
                "adapter": DEFAULT_REVIEW_ADAPTER,
                "failure_reason": failure_reason,
                "summary": failure_detail,
                "reviewed_head": reviewed_head,
            },
        )
        cleanup_scratch_tree(context["target_root"], scratch_dir)
        return {
            "result": "block",
            "summary": "default review engine failed closed before a formal review record could be authored.",
            "missing_inputs": [failure_detail or f"default review engine failed: {failure_reason}"],
            "fallback_to": None,
            "engine": {
                "engine": DEFAULT_REVIEW_ENGINE,
                "adapter": DEFAULT_REVIEW_ADAPTER,
                "result": "block",
                "failure_reason": failure_reason,
                "reviewed_head": reviewed_head,
                "evidence": engine_evidence,
            },
        }

    if raw_payload is not None and not result_path.exists():
        write_json_file(result_path, raw_payload)

    normalized_payload, normalization_errors = normalize_engine_review_result(
        raw_payload,
        relative=relative_to_root(result_path, context["target_root"]),
    )
    if normalization_errors or normalized_payload is None:
        write_json_file(
            metadata_path,
            {
                "engine": DEFAULT_REVIEW_ENGINE,
                "adapter": DEFAULT_REVIEW_ADAPTER,
                "failure_reason": "schema_drift",
                "summary": "normalized engine output did not satisfy Loom review schema",
                "errors": normalization_errors,
                "reviewed_head": reviewed_head,
            },
        )
        cleanup_scratch_tree(context["target_root"], scratch_dir)
        return {
            "result": "block",
            "summary": "default review engine returned a structured payload that Loom could not safely normalize.",
            "missing_inputs": normalization_errors,
            "fallback_to": None,
            "engine": {
                "engine": DEFAULT_REVIEW_ENGINE,
                "adapter": DEFAULT_REVIEW_ADAPTER,
                "result": "block",
                "failure_reason": "schema_drift",
                "reviewed_head": reviewed_head,
                "evidence": engine_evidence,
            },
        }

    write_json_file(findings_path, {"findings": normalized_payload["findings"]})
    write_json_file(
        metadata_path,
            {
                "engine": DEFAULT_REVIEW_ENGINE,
                "adapter": DEFAULT_REVIEW_ADAPTER,
                "result": "pass",
                "reviewed_head": reviewed_head,
                "decision": normalized_payload["decision"],
                "summary": normalized_payload["summary"],
                "kind": effective_kind,
            },
        )
    cleanup_scratch_tree(context["target_root"], scratch_dir)
    return {
        "result": "pass",
        "summary": "default review engine produced a Loom-normalized formal review draft.",
        "missing_inputs": [],
        "fallback_to": None,
        "engine": {
            "engine": DEFAULT_REVIEW_ENGINE,
            "adapter": DEFAULT_REVIEW_ADAPTER,
            "result": "pass",
            "failure_reason": None,
            "reviewed_head": reviewed_head,
            "evidence": engine_evidence,
        },
        "review_record_input": {
            "decision": normalized_payload["decision"],
            "summary": normalized_payload["summary"],
            "reviewer": DEFAULT_REVIEW_ADAPTER,
            "kind": effective_kind,
            "findings_file": relative_to_root(findings_path, context["target_root"]),
            "engine_adapter": DEFAULT_REVIEW_ADAPTER,
            "engine_evidence": relative_to_root(result_path, context["target_root"]),
            "normalized_findings": relative_to_root(findings_path, context["target_root"]),
        },
    }


def render_work_item(data: dict[str, Any]) -> str:
    return (
        f"# {data['item_id']}\n\n"
        "## Static Facts\n\n"
        f"- Item ID: {data['item_id']}\n"
        f"- Goal: {data['goal']}\n"
        f"- Scope: {data['scope']}\n"
        f"- Execution Path: {data['execution_path']}\n"
        f"- Workspace Entry: {data['workspace_entry']}\n"
        f"- Recovery Entry: {data['recovery_entry']}\n"
        f"- Review Entry: {data['review_entry']}\n"
        f"- Validation Entry: {data['validation_entry']}\n"
        f"- Closing Condition: {data['closing_condition']}\n\n"
        "## Associated Artifacts\n\n"
        + "".join(f"- `{artifact}`\n" for artifact in data["associated_artifacts"])
    )


def render_recovery_entry(item_id: str, values: dict[str, str]) -> str:
    return (
        f"# {item_id} Progress\n\n"
        "## Dynamic Facts\n\n"
        f"- Item ID: {item_id}\n"
        f"- Current Checkpoint: {values['current_checkpoint']}\n"
        f"- Current Stop: {values['current_stop']}\n"
        f"- Next Step: {values['next_step']}\n"
        f"- Blockers: {values['blockers']}\n"
        f"- Latest Validation Summary: {values['latest_validation_summary']}\n"
        f"- Recovery Boundary: {values['recovery_boundary']}\n"
        f"- Current Lane: {values['current_lane']}\n"
    )


def check_pr_template(target_root: Path) -> tuple[dict[str, Any], list[str]]:
    path = target_root / ".github/PULL_REQUEST_TEMPLATE.md"
    if not path.exists():
        return {"exists": False, "path": ".github/PULL_REQUEST_TEMPLATE.md", "sections": {}}, ["missing PR template"]

    text = path.read_text(encoding="utf-8")
    sections = {section: (section in text) for section in PR_TEMPLATE_SECTIONS}
    missing = [f"PR template missing section: {section}" for section, present in sections.items() if not present]
    return {
        "exists": True,
        "path": ".github/PULL_REQUEST_TEMPLATE.md",
        "sections": sections,
    }, missing


def active_workspace_conflicts(target_root: Path, item_id: str, workspace_entry: str) -> list[str]:
    work_items_dir = target_root / ".loom/work-items"
    if not work_items_dir.exists():
        return []

    conflicts: list[str] = []
    for candidate in sorted(work_items_dir.glob("*.md")):
        try:
            parsed_item, errors = parse_work_item(candidate, target_root)
        except OSError:
            continue
        if errors:
            continue
        other_item_id = str(parsed_item["item_id"])
        if other_item_id == item_id:
            continue
        if str(parsed_item["workspace_entry"]) != workspace_entry:
            continue
        recovery_rel = str(parsed_item["recovery_entry"])
        recovery_path = target_root / recovery_rel
        if not recovery_path.exists():
            conflicts.append(other_item_id)
            continue
        try:
            recovery_data, recovery_errors = parse_recovery_entry(recovery_path, target_root)
        except OSError:
            conflicts.append(other_item_id)
            continue
        if recovery_errors:
            conflicts.append(other_item_id)
            continue
        if normalize_checkpoint(recovery_data["current_checkpoint"]) not in TERMINAL_CHECKPOINTS:
            conflicts.append(other_item_id)
    return conflicts


def collect_temp_paths(target_root: Path) -> list[Path]:
    paths: list[Path] = []
    for relative in OWNED_TEMP_ROOTS:
        candidate = target_root / relative
        if candidate.exists():
            paths.append(candidate)
    return paths


def path_matches_owned_roots(path: str, roots: tuple[str, ...]) -> bool:
    normalized = path.rstrip("/")
    for root in roots:
        owned_root = root.rstrip("/")
        if normalized == owned_root:
            return True
        if normalized.startswith(f"{owned_root}/"):
            return True
    return False


def owned_dirty_path_kind(target_root: Path, path: str) -> str | None:
    if path_matches_owned_roots(path, OWNED_TEMP_ROOTS):
        return "temp"
    if path_matches_owned_roots(path, OWNED_RUNTIME_EVIDENCE_ROOTS):
        return "evidence"

    normalized = path.rstrip("/")
    for root in OWNED_TEMP_ROOTS:
        candidate = target_root / root
        if candidate.exists() and root.rstrip("/").startswith(f"{normalized}/"):
            return "temp"
    for root in OWNED_RUNTIME_EVIDENCE_ROOTS:
        candidate = target_root / root
        if candidate.exists() and root.rstrip("/").startswith(f"{normalized}/"):
            return "evidence"
    return None


def dirty_paths_by_owner(target_root: Path) -> tuple[list[str], list[str]]:
    owned: list[str] = []
    foreign: list[str] = []
    for entry in git_dirty_entries(target_root):
        path = entry["path"]
        if owned_dirty_path_kind(target_root, path) == "temp":
            owned.append(path)
        else:
            foreign.append(path)
    return owned, foreign


def dirty_runtime_evidence_paths(target_root: Path) -> list[str]:
    evidence: list[str] = []
    for entry in git_dirty_entries(target_root):
        path = entry["path"]
        if owned_dirty_path_kind(target_root, path) == "evidence":
            evidence.append(path)
    return evidence


def declared_scope_paths(scope_text: str) -> list[str]:
    candidates: list[str] = []
    for raw in re.findall(r"`([^`]+)`", scope_text):
        token = raw.strip()
        if not token:
            continue
        if token.startswith("/"):
            token = token.lstrip("/")
        if token.startswith("./"):
            token = token[2:]
        if token in {".", ""}:
            continue
        if "/" not in token and not token.endswith(".md"):
            continue
        candidates.append(token.rstrip("/"))

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(candidate)
    return deduped


def path_in_scope(path: str, scope_paths: list[str]) -> bool:
    return any(path == scope_path or path.startswith(f"{scope_path}/") for scope_path in scope_paths)


def load_context(target_root: Path, output_relative: str, expected_item: str | None) -> tuple[dict[str, Any], list[str]]:
    report, errors = load_fact_chain_report(target_root, output_relative)
    if errors:
        return {}, errors

    item_id = report["fact_chain"]["entry_points"]["current_item_id"]
    if expected_item and expected_item != item_id:
        return {}, [f"current item mismatch: expected `{expected_item}`, got `{item_id}`"]

    facts = report["facts"]
    workspace_entry = str(facts["workspace_entry"]["value"])
    workspace_path, workspace_errors = resolve_workspace_path(target_root, workspace_entry)
    if workspace_errors:
        return {}, workspace_errors
    if workspace_path is None:
        return {}, [f"unable to resolve workspace entry: {workspace_entry}"]

    context = {
        "target_root": target_root,
        "output_relative": output_relative,
        "report": report,
        "item_id": item_id,
        "work_item_path": target_root / report["fact_chain"]["entry_points"]["work_item"],
        "recovery_path": target_root / report["fact_chain"]["entry_points"]["recovery_entry"],
        "status_path": target_root / report["fact_chain"]["entry_points"]["status_surface"],
        "workspace_entry": workspace_entry,
        "workspace_path": workspace_path,
        "validation_entry": str(facts["validation_entry"]["value"]),
        "review_entry": str(facts["review_entry"]["value"]),
        "current_checkpoint_raw": str(facts["current_checkpoint"]["value"]),
        "current_checkpoint": normalize_checkpoint(str(facts["current_checkpoint"]["value"])),
        "goal": str(facts["goal"]["value"]),
        "scope": str(facts["scope"]["value"]),
        "execution_path": str(facts["execution_path"]["value"]),
        "associated_artifacts": list(facts["associated_artifacts"]["value"]),
        "current_stop": str(facts["current_stop"]["value"]),
        "next_step": str(facts["next_step"]["value"]),
        "blockers": str(facts["blockers"]["value"]),
        "latest_validation_summary": str(facts["latest_validation_summary"]["value"]),
        "recovery_boundary": str(facts["recovery_boundary"]["value"]),
        "current_lane": str(facts["current_lane"]["value"]),
        "closing_condition": str(facts["closing_condition"]["value"]),
        "read_entry": str(report["fact_chain"]["read_entry"]),
    }
    return context, []


def review_runtime_root(context: dict[str, Any], reviewed_head: str | None = None) -> Path:
    head = (reviewed_head or git_head_sha(context["target_root"]) or "unknown-head").strip() or "unknown-head"
    safe_head = re.sub(r"[^A-Za-z0-9_.-]", "-", head)
    return context["target_root"] / ".loom/runtime/review" / context["item_id"] / safe_head


def default_review_kind(context: dict[str, Any]) -> str:
    scope_paths = declared_scope_paths(context["scope"])
    if scope_paths and all(path.endswith(".md") or path.startswith(".loom/") for path in scope_paths):
        return "general_review"
    return "code_review"


def implementation_review_kind(context: dict[str, Any]) -> str:
    scope_paths = declared_scope_paths(context["scope"])
    if scope_paths and all(path.endswith(".md") or path.startswith(".loom/") for path in scope_paths):
        return "general_review"
    return "code_review"


def review_focus_paths(context: dict[str, Any]) -> list[str]:
    result = run_git(context["target_root"], ["diff", "--name-only", "--no-renames", "HEAD", "--"])
    if result is not None and result.returncode == 0:
        tracked_paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if tracked_paths:
            return tracked_paths
    scope_paths = declared_scope_paths(context["scope"])
    if scope_paths:
        return scope_paths
    return [relative_to_root(context["workspace_path"], context["target_root"])]


def review_engine_schema_path() -> Path:
    return shared_asset(__file__, "review/loom-review-result-schema.json")


def normalize_engine_review_result(payload: Any, *, relative: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(payload, dict):
        return None, [f"engine result `{relative}` must be a JSON object"]

    decision = payload.get("decision")
    summary = payload.get("summary")
    findings_payload = payload.get("findings")
    errors: list[str] = []
    if decision not in REVIEW_DECISIONS:
        errors.append(f"engine result `{relative}` decision must be one of {', '.join(sorted(REVIEW_DECISIONS))}")
    if not isinstance(summary, str) or not summary.strip():
        errors.append(f"engine result `{relative}` must include non-empty `summary`")
    findings, finding_errors = normalize_review_findings(findings_payload, relative=relative)
    errors.extend(finding_errors)
    if errors:
        return None, errors

    return {
        **payload,
        "decision": decision,
        "summary": summary.strip(),
        "findings": findings,
    }, []


def manual_review_payload(
    *,
    context: dict[str, Any],
    findings_file: str | None,
    kind: str,
    review_record_path: str,
) -> dict[str, Any]:
    command = [
        "python3",
        "tools/loom_flow.py",
        "review",
        "record",
        "--target",
        str(context["target_root"]),
        "--item",
        context["item_id"],
        "--decision",
        "<allow|block|fallback>",
        "--kind",
        kind,
        "--summary",
        "<stable review summary>",
        "--reviewer",
        "<reviewer-id>",
    ]
    if findings_file:
        command.extend(["--findings-file", findings_file])
    return {
        "summary": "If the default engine is blocked, complete formal review by writing the same review record manually.",
        "review_record_path": review_record_path,
        "findings_file": findings_file,
        "recommended_kind": kind,
        "command": command,
    }


def build_default_review_prompt(
    *,
    context: dict[str, Any],
    build_payload: dict[str, Any],
    runtime_fields: dict[str, dict[str, Any]],
    review_path: str,
) -> str:
    focus_paths = review_focus_paths(context)
    is_spec_review = review_path == default_spec_review_path(context["item_id"])
    spec_path = formal_spec_path(context) if is_spec_review else None
    if spec_path and spec_path not in focus_paths:
        focus_paths = [spec_path, *focus_paths]
    workspace_path = relative_to_root(context["workspace_path"], context["target_root"])
    runtime_lines = [
        f"- {field}: {runtime_fields[field]['value']}"
        for field in RUNTIME_EVIDENCE_FIELDS
    ]
    path_lines = [f"- `{path}`" for path in focus_paths[:20]]
    if len(focus_paths) > 20:
        path_lines.append(f"- ... ({len(focus_paths) - 20} more paths omitted)")
    return "\n".join(
        [
            "你是 Loom 默认 formal reviewer。",
            "请基于当前仓库工作树做正式语义审查，并只输出符合 schema 的 JSON 结果。",
            "优先阅读当前事项直接相关的文件与差异，不要做整仓广播式探索。",
            "",
            "Loom 审查边界：",
            "- 你负责 reviewer rubric：判断方向、边界、语义正确性、风险与验证充分性。",
            "- 你不是 merge gate；不要输出 safe_to_merge、guardian verdict 或宿主按钮决策。",
            "- 你的输出只是 review evidence；最终正式真相会被回写到单一 review record。",
            "- 若阻断项成立，decision 设为 `block`；若当前输入不足以形成正式结论，decision 设为 `fallback`。",
            *(
                [
                    "- 当前任务是 spec review；必须优先判断 formal spec 是否完整、边界是否清晰、接受条件是否足以支撑后续实现 review。",
                    f"- Formal Spec Path: {spec_path}",
                ]
                if spec_path
                else []
            ),
            "",
            "当前事项：",
            f"- Item ID: {context['item_id']}",
            f"- Goal: {context['goal']}",
            f"- Scope: {context['scope']}",
            f"- Execution Path: {context['execution_path']}",
            f"- Workspace Entry: {context['workspace_entry']}",
            f"- Workspace Path: {workspace_path}",
            f"- Review Record Path: {review_path}",
            f"- Latest Validation Summary: {context['latest_validation_summary']}",
            "",
            "Build Checkpoint：",
            f"- Result: {build_payload['result']}",
            f"- Summary: {build_payload['summary']}",
            "",
            "Runtime Evidence Entrypoints：",
            *runtime_lines,
            "",
            "优先审查这些路径：",
            *path_lines,
            "",
            "Findings 写作要求：",
            "- 每条 finding 必须包含 `id`、`summary`、`severity`、`rebuttal`、`disposition`。",
            "- `severity` 只允许 `warn` 或 `block`。",
            "- `disposition.status` 只允许 `accepted`、`rejected`、`deferred`。",
            "- 若没有阻断项但仍有后续动作，可输出 `warn` findings。",
            "",
            "Decision 规则：",
            "- `allow`: 当前事项已通过 formal review。",
            "- `block`: 存在明确阻断项。",
            "- `fallback`: 当前输入不足或需要先回到前序 checkpoint 再继续。",
        ]
    ).rstrip() + "\n"


def load_fact_chain_report(target_root: Path, output_relative: str) -> tuple[dict[str, Any], list[str]]:
    report, errors = inspect_fact_chain(target_root, output_relative)
    if errors and all("Runtime Evidence" in message for message in errors):
        report, errors = inspect_fact_chain_legacy(target_root, output_relative)
    if errors:
        return {}, errors
    if not report:
        return {}, ["no fact-chain report was produced"]
    return report, []


def inspect_fact_chain_legacy(target_root: Path, output_relative: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    output_path = target_root / output_relative
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
    if errors:
        return {}, errors

    work_item_path = target_root / str(work_item_ref)
    recovery_path = target_root / str(recovery_ref)
    status_path = target_root / str(status_ref)
    for label, path in (
        ("work_item", work_item_path),
        ("recovery_entry", recovery_path),
        ("status_surface", status_path),
    ):
        if not path.exists():
            errors.append(f"declared fact-chain carrier is missing on disk: {label} -> {path.relative_to(target_root)}")
    if errors:
        return {}, errors

    work_item, work_item_errors = parse_work_item(work_item_path, target_root)
    recovery_entry, recovery_errors = parse_recovery_entry(recovery_path, target_root)
    status_sections = markdown_sections(status_path)
    status_values, status_errors = parse_key_value_section(
        status_sections,
        "Derived Fact Chain View",
        STATUS_FIELDS,
        str(status_path.relative_to(target_root)),
    )
    status_sources, source_errors = parse_key_value_section(
        status_sections,
        "Sources",
        STATUS_SOURCE_FIELDS,
        str(status_path.relative_to(target_root)),
    )
    errors.extend(work_item_errors)
    errors.extend(recovery_errors)
    errors.extend(status_errors)
    errors.extend(source_errors)
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

    expected_status = {
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
    for field_name, expected_value in expected_status.items():
        actual_value = status_values.get(field_name)
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
    if errors:
        return {}, errors

    report = {
        "target": str(target_root),
        "fact_chain": {
            "mode": str(mode),
            "read_entry": str(read_entry),
            "entry_points": {
                "current_item_id": str(current_item_id),
                "work_item": str(work_item_ref),
                "recovery_entry": str(recovery_ref),
                "status_surface": str(status_ref),
            },
        },
        "facts": {
            "item_id": {"value": str(work_item["item_id"])},
            "goal": {"value": str(work_item["goal"])},
            "scope": {"value": str(work_item["scope"])},
            "execution_path": {"value": str(work_item["execution_path"])},
            "associated_artifacts": {"value": list(work_item["associated_artifacts"])},
            "workspace_entry": {"value": str(work_item["workspace_entry"])},
            "recovery_entry": {"value": str(work_item["recovery_entry"])},
            "review_entry": {"value": str(work_item["review_entry"])},
            "validation_entry": {"value": str(work_item["validation_entry"])},
            "closing_condition": {"value": str(work_item["closing_condition"])},
            "current_checkpoint": {"value": recovery_entry["current_checkpoint"]},
            "current_stop": {"value": recovery_entry["current_stop"]},
            "next_step": {"value": recovery_entry["next_step"]},
            "blockers": {"value": recovery_entry["blockers"]},
            "latest_validation_summary": {"value": recovery_entry["latest_validation_summary"]},
            "recovery_boundary": {"value": recovery_entry["recovery_boundary"]},
            "current_lane": {"value": recovery_entry["current_lane"]},
        },
        "runtime_evidence": {},
        "derived_status_surface": {
            "path": str(status_ref),
            "values": expected_status,
            "runtime_evidence": {},
            "sources": expected_sources,
        },
    }
    return report, []


def purity_report_from_context(context: dict[str, Any], fact_chain_errors: list[str] | None = None) -> dict[str, Any]:
    target_root = context["target_root"]
    workspace_path = context["workspace_path"]
    workspace_entry = context["workspace_entry"]
    item_id = context["item_id"]

    hard_failures: list[str] = []
    report_only: list[str] = []

    if fact_chain_errors:
        hard_failures.extend(f"fact-chain: {message}" for message in fact_chain_errors)

    if not workspace_path.exists():
        hard_failures.append(f"declared workspace entry does not exist on disk: {workspace_entry}")
    elif not workspace_path.is_dir():
        hard_failures.append(f"declared workspace entry is not a directory: {workspace_entry}")

    cwd_relative = current_cwd_relative(target_root)
    workspace_relative = relative_to_root(workspace_path, target_root)
    if cwd_relative is not None:
        if workspace_relative != "." and cwd_relative != workspace_relative and not cwd_relative.startswith(f"{workspace_relative}/"):
            hard_failures.append(
                f"current working directory is outside the declared workspace: cwd={cwd_relative}, workspace={workspace_relative}"
            )

    owned_dirty, foreign_dirty = dirty_paths_by_owner(target_root)
    evidence_dirty = dirty_runtime_evidence_paths(target_root)
    foreign_dirty = [path for path in foreign_dirty if path not in evidence_dirty]
    if foreign_dirty:
        preview = ", ".join(sorted(foreign_dirty)[:5])
        hard_failures.append(f"workspace contains untriaged residual changes: {preview}")
    if owned_dirty:
        preview = ", ".join(sorted(owned_dirty)[:5])
        hard_failures.append(f"loom-owned temporary residue is still present: {preview}")
    if evidence_dirty:
        preview = ", ".join(sorted(evidence_dirty)[:5])
        report_only.append(f"runtime review evidence is present and does not block purity on its own: {preview}")

    scope_paths = declared_scope_paths(context["scope"])
    out_of_scope_changes: list[str] = []
    if scope_paths:
        for path in foreign_dirty:
            if not path_in_scope(path, scope_paths):
                out_of_scope_changes.append(path)
        if out_of_scope_changes:
            preview = ", ".join(sorted(out_of_scope_changes)[:5])
            hard_failures.append(f"scope overflow detected: {preview}")

    conflicts = active_workspace_conflicts(target_root, item_id, workspace_entry)
    if conflicts:
        hard_failures.append(
            "workspace is bound to multiple active work items: " + ", ".join(sorted(conflicts))
        )

    branch = git_branch(target_root)
    if branch:
        report_only.append(f"branch purity is host-managed and reported via host-lifecycle: current branch `{branch}`")
    else:
        report_only.append("branch purity is host-managed and reported via host-lifecycle: no branch information available")

    report_only.append("PR purity is host-managed and reported via host-lifecycle")

    state = "failed" if hard_failures else "clean"
    return {
        "state": state,
        "workspace_entry": workspace_entry,
        "workspace_path": workspace_relative,
        "scope_assessment": {
            "mode": "constrained" if scope_paths else "unconstrained",
            "declared_paths": scope_paths,
            "out_of_scope_changes": sorted(out_of_scope_changes),
        },
        "hard_failures": hard_failures,
        "report_only": report_only,
    }


def base_workspace_payload(context: dict[str, Any], operation: str) -> dict[str, Any]:
    purity = purity_report_from_context(context)
    return {
        "command": "workspace",
        "operation": operation,
        "item": {
            "id": context["item_id"],
            "goal": context["goal"],
            "scope": context["scope"],
            "execution_path": context["execution_path"],
        },
        "workspace": {
            "entry": context["workspace_entry"],
            "path": relative_to_root(context["workspace_path"], context["target_root"]),
            "exists": context["workspace_path"].exists(),
        },
        "recovery": {
            "path": str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"]),
            "current_stop": context["current_stop"],
            "next_step": context["next_step"],
            "latest_validation_summary": context["latest_validation_summary"],
        },
        "checkpoint": {
            "raw": context["current_checkpoint_raw"],
            "normalized": context["current_checkpoint"],
        },
        "purity": purity,
        "missing_inputs": [],
        "fallback_to": None,
    }


def checkpoint_payload(stage: str, context: dict[str, Any]) -> dict[str, Any]:
    purity = purity_report_from_context(context)
    missing_inputs: list[str] = []
    result = "pass"
    fallback_to: str | None = None

    if purity["hard_failures"]:
        missing_inputs.append("purity")
        result = "fallback"
        fallback_to = "admission"

    required = {
        "admission": (
            ("goal", context["goal"]),
            ("scope", context["scope"]),
            ("execution_path", context["execution_path"]),
            ("workspace_entry", context["workspace_entry"]),
            ("recovery_entry", str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"])),
            ("validation_entry", context["validation_entry"]),
            ("closing_condition", context["closing_condition"]),
            ("current_checkpoint", context["current_checkpoint_raw"]),
            ("current_stop", context["current_stop"]),
            ("next_step", context["next_step"]),
        ),
        "build": (
            ("goal", context["goal"]),
            ("scope", context["scope"]),
            ("execution_path", context["execution_path"]),
            ("workspace_entry", context["workspace_entry"]),
            ("recovery_entry", str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"])),
            ("status_surface", str(context["report"]["fact_chain"]["entry_points"]["status_surface"])),
            ("validation_entry", context["validation_entry"]),
            ("latest_validation_summary", context["latest_validation_summary"]),
            ("current_lane", context["current_lane"]),
            ("closing_condition", context["closing_condition"]),
        ),
        "merge": (
            ("goal", context["goal"]),
            ("scope", context["scope"]),
            ("execution_path", context["execution_path"]),
            ("workspace_entry", context["workspace_entry"]),
            ("recovery_entry", str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"])),
            ("review_entry", context["review_entry"]),
            ("status_surface", str(context["report"]["fact_chain"]["entry_points"]["status_surface"])),
            ("validation_entry", context["validation_entry"]),
            ("latest_validation_summary", context["latest_validation_summary"]),
            ("current_lane", context["current_lane"]),
            ("recovery_boundary", context["recovery_boundary"]),
            ("blockers", context["blockers"]),
            ("closing_condition", context["closing_condition"]),
        ),
    }[stage]

    for label, value in required:
        if not str(value).strip():
            missing_inputs.append(label)

    current_rank = checkpoint_rank(context["current_checkpoint"])
    requested_rank = checkpoint_rank(stage)
    if context["current_checkpoint"] in TERMINAL_CHECKPOINTS:
        result = "fallback"
        fallback_to = context["current_checkpoint"]
    elif current_rank != -1 and current_rank < requested_rank:
        result = "fallback"
        fallback_to = context["current_checkpoint"]

    blocker_text = context["blockers"].strip().lower()
    if blocker_text not in {"none", "none recorded", "none recorded."}:
        result = "block" if result == "pass" else result

    pr_template: dict[str, Any] | None = None
    review_record: dict[str, Any] | None = None
    review_path: str | None = None
    spec_review: dict[str, Any] | None = None
    if stage == "merge":
        pr_template, pr_template_errors = check_pr_template(context["target_root"])
        if pr_template_errors:
            missing_inputs.extend(pr_template_errors)
            if result == "pass":
                result = "block"
        spec_review = spec_review_gate_payload(context)
        if spec_review["result"] in {"block", "fallback"}:
            missing_inputs.extend(spec_review["missing_inputs"])
            if spec_review["result"] == "fallback" and result == "pass":
                result = "fallback"
                fallback_to = spec_review["fallback_to"] or "build"
            elif result == "pass":
                result = "block"
        review_record, review_path, review_errors = load_review_record(
            context["target_root"],
            context["item_id"],
            context["review_entry"],
        )
        if review_errors:
            missing_inputs.extend(review_errors)
            if result == "pass":
                result = "block"
        elif review_record is None:
            missing_inputs.append(f"missing review artifact: {review_path}")
            if result == "pass":
                result = "block"
        else:
            decision = review_record["decision"]
            if review_record.get("reviewed_validation_summary") != context["latest_validation_summary"]:
                missing_inputs.append("review artifact does not match the latest validation summary")
                if result == "pass":
                    result = "block"
            binding_payload, binding_errors = review_head_binding(
                context["target_root"],
                reviewed_head=review_record.get("reviewed_head"),
                allowed_paths=allowed_post_review_carrier_paths(context, review_path),
            )
            review_record["head_binding"] = binding_payload
            if binding_errors:
                missing_inputs.extend(binding_errors)
                if result == "pass":
                    result = "block"
            if decision == "block":
                if result == "pass":
                    result = "block"
                missing_inputs.append(f"review decision is blocking: {review_record['summary']}")
            elif decision == "fallback":
                result = "fallback"
                fallback_to = review_record.get("fallback_to") or "build"

    if missing_inputs and result == "pass":
        result = "block"

    if result == "pass":
        summary = f"{stage} checkpoint can be consumed from the current Loom fact chain."
    elif result == "block":
        summary = f"{stage} checkpoint is missing execution material but does not require a checkpoint rollback."
    else:
        fallback_label = fallback_to or "admission"
        summary = f"{stage} checkpoint cannot proceed from the current state; fall back to `{fallback_label}`."

    payload = {
        "command": "checkpoint",
        "checkpoint": stage,
        "item": {
            "id": context["item_id"],
            "goal": context["goal"],
            "scope": context["scope"],
            "execution_path": context["execution_path"],
        },
        "workspace": {
            "entry": context["workspace_entry"],
            "path": relative_to_root(context["workspace_path"], context["target_root"]),
        },
        "recovery": {
            "path": str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"]),
            "current_checkpoint": context["current_checkpoint_raw"],
            "current_stop": context["current_stop"],
            "next_step": context["next_step"],
            "latest_validation_summary": context["latest_validation_summary"],
            "current_lane": context["current_lane"],
        },
        "review": {
            "path": context["review_entry"],
        },
        "purity": purity,
        "result": result,
        "summary": summary,
        "missing_inputs": missing_inputs,
        "fallback_to": fallback_to,
    }
    if pr_template is not None:
        payload["pr_template"] = pr_template
    if review_path is not None:
        payload["review"] = {
            "path": review_path,
            "record": review_record,
        }
    if spec_review is not None:
        payload["spec_review"] = spec_review
    return payload


def handle_checkpoint(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "checkpoint",
                "checkpoint": args.stage,
                "result": "fallback",
                "summary": "checkpoint evaluation could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
            }
        )
    return emit(checkpoint_payload(args.stage, context))


def handle_workspace(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            runtime_state_block_payload(
                command="workspace",
                operation=args.operation,
                runtime_state=runtime_state,
                summary="workspace lifecycle command is blocked because the Loom runtime state is inconsistent.",
            )
        )
    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "workspace",
                "operation": args.operation,
                "result": "fallback",
                "summary": "workspace lifecycle command could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
                "runtime_state": runtime_state,
            }
        )

    def emit_workspace(payload: dict[str, Any]) -> int:
        payload["runtime_state"] = runtime_state
        return emit(payload)

    payload = base_workspace_payload(context, args.operation)
    workspace_path = context["workspace_path"]
    purity = payload["purity"]

    if args.operation == "locate":
        payload["result"] = "pass" if not purity["hard_failures"] else "block"
        payload["summary"] = "workspace location was resolved from the fact chain."
        if purity["hard_failures"]:
            payload["summary"] = "workspace location resolved, but the workspace is not execution-ready."
            payload["missing_inputs"] = list(purity["hard_failures"])
        return emit_workspace(payload)

    if args.operation == "create":
        if purity["hard_failures"] and any("does not exist on disk" not in failure for failure in purity["hard_failures"]):
            payload["result"] = "block"
            payload["summary"] = "workspace creation is blocked until the current workspace state is clean."
            payload["missing_inputs"] = list(purity["hard_failures"])
            return emit_workspace(payload)

        created = False
        if not workspace_path.exists():
            workspace_path.mkdir(parents=True, exist_ok=True)
            created = True

        refreshed, refresh_errors = load_context(target_root, args.output, args.item)
        if refresh_errors:
            payload["result"] = "block"
            payload["summary"] = "workspace path was created, but the fact chain could not be reloaded."
            payload["missing_inputs"] = [f"fact-chain: {message}" for message in refresh_errors]
            return emit_workspace(payload)

        payload = base_workspace_payload(refreshed, args.operation)
        payload["created"] = created
        payload["result"] = "pass"
        payload["summary"] = "workspace semantics are established from `workspace_entry`."
        return emit_workspace(payload)

    if args.operation == "cleanup":
        owned_dirty, foreign_dirty = dirty_paths_by_owner(target_root)
        temp_paths = collect_temp_paths(target_root)
        if foreign_dirty:
            payload["result"] = "block"
            payload["summary"] = "cleanup stopped because the workspace contains non-Loom changes."
            payload["missing_inputs"] = [f"non-loom residue: {path}" for path in foreign_dirty]
            return emit_workspace(payload)

        removed: list[str] = []
        for temp_path in temp_paths:
            relative = relative_to_root(temp_path, target_root)
            tracked = git_tracked_files(target_root, relative)
            if tracked:
                payload["result"] = "block"
                payload["summary"] = "cleanup refused to delete tracked files from a Loom temporary path."
                payload["missing_inputs"] = [f"tracked temp path: {relative}"]
                return emit_workspace(payload)
            if temp_path.is_dir():
                shutil.rmtree(temp_path)
                removed.append(relative)
            else:
                temp_path.unlink()
                removed.append(relative)

        if owned_dirty and not removed:
            payload["result"] = "block"
            payload["summary"] = "cleanup found Loom temporary residue in git status, but no owned temp paths could be removed."
            payload["missing_inputs"] = [f"owned temp residue: {path}" for path in owned_dirty]
            return emit_workspace(payload)

        payload["removed_paths"] = removed
        payload["result"] = "pass"
        payload["summary"] = "cleanup removed Loom-owned temporary residue." if removed else "cleanup found no Loom-owned temporary residue."
        payload["purity"] = purity_report_from_context(context)
        return emit_workspace(payload)

    cleanup_payload = base_workspace_payload(context, "cleanup")
    owned_dirty, foreign_dirty = dirty_paths_by_owner(target_root)
    if foreign_dirty:
        cleanup_payload["result"] = "block"
        cleanup_payload["summary"] = "retire cannot proceed because cleanup is blocked by non-Loom changes."
        cleanup_payload["missing_inputs"] = [f"non-loom residue: {path}" for path in foreign_dirty]
        return emit_workspace(cleanup_payload)

    for temp_path in collect_temp_paths(target_root):
        relative = relative_to_root(temp_path, target_root)
        tracked = git_tracked_files(target_root, relative)
        if tracked:
            cleanup_payload["result"] = "block"
            cleanup_payload["summary"] = "retire cannot proceed because cleanup would need to delete tracked files."
            cleanup_payload["missing_inputs"] = [f"tracked temp path: {relative}"]
            return emit_workspace(cleanup_payload)
        if temp_path.is_dir():
            shutil.rmtree(temp_path)
        else:
            temp_path.unlink()

    update_markdown_bullet(context["recovery_path"], "Current Checkpoint", "retired")
    if context["status_path"].exists():
        update_markdown_bullet(context["status_path"], "Current Checkpoint", "retired")

    refreshed, refresh_errors = load_context(target_root, args.output, args.item)
    if refresh_errors:
        return emit(
            {
                "command": "workspace",
                "operation": "retire",
                "result": "block",
                "summary": "retire wrote `retired`, but the fact chain no longer reads cleanly.",
                "missing_inputs": [f"fact-chain: {message}" for message in refresh_errors],
                "fallback_to": "admission",
                "runtime_state": runtime_state,
            }
        )

    payload = base_workspace_payload(refreshed, "retire")
    payload["result"] = "pass"
    payload["summary"] = "workspace was retired by updating the recovery entry checkpoint to `retired`."
    payload["retired"] = True
    payload["removed_paths"] = [path for path in owned_dirty if any(path == root or path.startswith(f"{root}/") for root in OWNED_TEMP_ROOTS)]
    return emit_workspace(payload)


def handle_purity(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            runtime_state_block_payload(
                command="purity-check",
                runtime_state=runtime_state,
                summary="purity-check is blocked because the Loom runtime state is inconsistent.",
            )
        )
    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        payload = {
            "command": "purity-check",
            "result": "block",
            "summary": "purity-check could not read a valid Loom fact chain.",
            "missing_inputs": [f"fact-chain: {message}" for message in errors],
            "fallback_to": "admission",
            "runtime_state": runtime_state,
            "purity": {
                "state": "failed",
                "hard_failures": [f"fact-chain: {message}" for message in errors],
                "report_only": [
                    "branch purity is report-only in v1",
                    "PR purity is report-only in v1",
                ],
            },
        }
        return emit(payload)

    purity = purity_report_from_context(context)
    result = "pass" if not purity["hard_failures"] else "block"
    summary = "workspace purity is compatible with continued execution." if result == "pass" else "workspace purity requires cleanup or re-scoping before review."
    payload = {
        "command": "purity-check",
        "item": {
            "id": context["item_id"],
            "goal": context["goal"],
            "scope": context["scope"],
            "execution_path": context["execution_path"],
        },
        "workspace": {
            "entry": context["workspace_entry"],
            "path": relative_to_root(context["workspace_path"], context["target_root"]),
        },
        "checkpoint": {
            "raw": context["current_checkpoint_raw"],
            "normalized": context["current_checkpoint"],
        },
        "purity": purity,
        "result": result,
        "summary": summary,
        "missing_inputs": list(purity["hard_failures"]),
        "fallback_to": "admission" if purity["hard_failures"] else None,
        "runtime_state": runtime_state,
    }
    return emit(payload)


def handle_fact_chain(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    report, errors = load_fact_chain_report(target_root, args.output)
    if errors:
        return emit(
            {
                "command": "fact-chain",
                "result": "block",
                "summary": "fact-chain command could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
            }
        )

    item_id = report["fact_chain"]["entry_points"]["current_item_id"]
    if args.item and args.item != item_id:
        return emit(
            {
                "command": "fact-chain",
                "result": "block",
                "summary": "fact-chain command found an item mismatch.",
                "missing_inputs": [f"current item mismatch: expected `{args.item}`, got `{item_id}`"],
                "fallback_to": "admission",
            }
        )

    return emit(
        {
            "command": "fact-chain",
            "result": "pass",
            "summary": "fact chain can be read and validated from a single entry.",
            "missing_inputs": [],
            "fallback_to": None,
            "report": report,
        }
    )


def runtime_evidence_from_report(report: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    runtime_evidence = report.get("runtime_evidence")
    missing_inputs: list[str] = []
    fields: dict[str, Any] = {}
    if not isinstance(runtime_evidence, dict):
        missing_inputs.append("runtime_evidence is missing from fact-chain report")
        return fields, missing_inputs

    for key in RUNTIME_EVIDENCE_FIELDS:
        entry = runtime_evidence.get(key)
        if not isinstance(entry, dict):
            missing_inputs.append(f"runtime_evidence.{key} is missing")
            continue
        value = entry.get("value")
        status = entry.get("status")
        if not isinstance(value, str) or not value.strip():
            missing_inputs.append(f"runtime_evidence.{key}.value must be a non-empty string")
        if status not in {"present", "not_applicable"}:
            missing_inputs.append(f"runtime_evidence.{key}.status must be `present` or `not_applicable`")
        elif status == "present" and value == "not_applicable":
            missing_inputs.append(f"runtime_evidence.{key} is `present` but uses `not_applicable`")
        elif status == "not_applicable" and value != "not_applicable":
            missing_inputs.append(f"runtime_evidence.{key} is `not_applicable` but value is `{value}`")
        fields[key] = {
            "value": value,
            "status": status,
            "source": entry.get("source"),
        }
    return fields, missing_inputs


def handle_runtime_evidence(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            {
                "command": "runtime-evidence",
                "result": "block",
                "summary": "runtime-evidence is blocked because the Loom runtime state is inconsistent.",
                "missing_inputs": runtime_state["missing_inputs"],
                "fallback_to": runtime_state["fallback_to"],
                "runtime_state": runtime_state,
            }
        )
    report, errors = load_fact_chain_report(target_root, args.output)
    if errors:
        return emit(
            {
                "command": "runtime-evidence",
                "result": "block",
                "summary": "runtime-evidence command could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
                "runtime_state": runtime_state,
            }
        )

    item_id = report["fact_chain"]["entry_points"]["current_item_id"]
    if args.item and args.item != item_id:
        return emit(
            {
                "command": "runtime-evidence",
                "result": "block",
                "summary": "runtime-evidence command found an item mismatch.",
                "missing_inputs": [f"current item mismatch: expected `{args.item}`, got `{item_id}`"],
                "fallback_to": "admission",
                "runtime_state": runtime_state,
            }
        )

    fields, missing_inputs = runtime_evidence_from_report(report)

    result = "pass" if not missing_inputs else "block"
    summary = (
        "runtime evidence entries are readable and distinguish `present` from `not_applicable`."
        if result == "pass"
        else "runtime evidence entries are incomplete or inconsistent."
    )
    return emit(
        {
            "command": "runtime-evidence",
            "item_id": item_id,
            "result": result,
            "summary": summary,
            "missing_inputs": missing_inputs,
            "fallback_to": "admission" if missing_inputs else None,
            "runtime_evidence": fields,
            "runtime_state": runtime_state,
        }
    )


def state_check_payload(context: dict[str, Any]) -> dict[str, Any]:
    purity = purity_report_from_context(context)
    active_state_failures: list[str] = []
    checkpoint_failures: list[str] = []
    scope_failures: list[str] = []

    current_checkpoint = context["current_checkpoint"]
    if current_checkpoint in TERMINAL_CHECKPOINTS:
        active_state_failures.append(f"current checkpoint is terminal: `{current_checkpoint}`")

    active_conflicts = active_workspace_conflicts(context["target_root"], context["item_id"], context["workspace_entry"])
    if active_conflicts:
        active_state_failures.append(
            "workspace is shared by multiple active items: " + ", ".join(sorted(active_conflicts))
        )

    known_checkpoints = {"admission", "build", "merge", "retired"} | TERMINAL_CHECKPOINTS
    if current_checkpoint not in known_checkpoints:
        checkpoint_failures.append(f"unknown checkpoint value: `{context['current_checkpoint_raw']}`")
    if current_checkpoint in {"admission", "build", "merge"}:
        for field_name in ("current_stop", "next_step", "latest_validation_summary", "recovery_boundary", "current_lane"):
            value = str(context[field_name]).strip()
            if not value:
                checkpoint_failures.append(f"checkpoint integrity missing `{field_name}`")

    scope_assessment = purity.get("scope_assessment")
    if isinstance(scope_assessment, dict):
        out_of_scope_changes = scope_assessment.get("out_of_scope_changes")
        if isinstance(out_of_scope_changes, list) and out_of_scope_changes:
            preview = ", ".join(out_of_scope_changes[:5])
            scope_failures.append(f"out-of-scope changes detected: {preview}")

    missing_inputs: list[str] = []
    for collection in (purity["hard_failures"], active_state_failures, checkpoint_failures, scope_failures):
        for message in collection:
            if message not in missing_inputs:
                missing_inputs.append(message)

    result = "pass" if not missing_inputs else "block"
    summary = (
        "active state, checkpoint integrity, and scope signals are consistent."
        if result == "pass"
        else "state-check found active-state conflicts, checkpoint gaps, or scope overflow signals."
    )
    return {
        "command": "state-check",
        "item": {
            "id": context["item_id"],
            "goal": context["goal"],
            "scope": context["scope"],
            "execution_path": context["execution_path"],
        },
        "checkpoint": {
            "raw": context["current_checkpoint_raw"],
            "normalized": current_checkpoint,
        },
        "workspace": {
            "entry": context["workspace_entry"],
            "path": relative_to_root(context["workspace_path"], context["target_root"]),
        },
        "checks": {
            "active_state_failures": active_state_failures,
            "checkpoint_failures": checkpoint_failures,
            "scope_failures": scope_failures,
        },
        "purity": purity,
        "result": result,
        "summary": summary,
        "missing_inputs": missing_inputs,
        "fallback_to": "admission" if missing_inputs else None,
    }


def handle_state_check(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            {
                "command": "state-check",
                "result": "block",
                "summary": "state-check is blocked because the Loom runtime state is inconsistent.",
                "missing_inputs": runtime_state["missing_inputs"],
                "fallback_to": runtime_state["fallback_to"],
                "runtime_state": runtime_state,
            }
        )
    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "state-check",
                "result": "block",
                "summary": "state-check could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
                "runtime_state": runtime_state,
            }
        )
    payload = state_check_payload(context)
    payload["runtime_state"] = runtime_state
    return emit(payload)


def handle_runtime_state(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    return emit(
        {
            "command": "runtime-state",
            "result": runtime_state["result"],
            "summary": runtime_state["summary"],
            "missing_inputs": runtime_state["missing_inputs"],
            "fallback_to": runtime_state["fallback_to"],
            "runtime_state": runtime_state,
        }
    )


def host_lifecycle_payload(context: dict[str, Any]) -> dict[str, Any]:
    branch = git_branch(context["target_root"])
    purity = purity_report_from_context(context)
    worktree_root = current_cwd_relative(context["target_root"])
    branch_status = "report_only" if branch else "host_managed_without_local_branch"
    pr_status = "report_only"
    worktree_status = "host_managed"
    missing_inputs: list[str] = []
    if worktree_root is None:
        worktree_observation = "current process is outside the target repository"
    else:
        worktree_observation = worktree_root
    if any(message.startswith("branch purity") for message in purity["report_only"]):
        branch_next = "keep branch lifecycle on the host platform; Loom only reports purity and closeout dependencies."
    else:
        branch_next = "branch lifecycle remains host-managed."
    return {
        "command": "host-lifecycle",
        "item": {
            "id": context["item_id"],
            "goal": context["goal"],
            "scope": context["scope"],
            "execution_path": context["execution_path"],
        },
        "result": "pass",
        "summary": "workspace is Loom-managed; branch, PR, and git worktree lifecycles remain host-managed with explicit boundary checks.",
        "missing_inputs": missing_inputs,
        "fallback_to": None,
        "objects": {
            "workspace": {
                "ownership": "loom",
                "entry": context["workspace_entry"],
                "path": relative_to_root(context["workspace_path"], context["target_root"]),
                "lifecycle_entry": "python3 .loom/bin/loom_flow.py workspace create|locate|cleanup|retire",
            },
            "branch": {
                "ownership": "host",
                "current_branch": branch,
                "purity_status": branch_status,
                "next_action": branch_next,
            },
            "pr": {
                "ownership": "host",
                "purity_status": pr_status,
                "next_action": "use host PR lifecycle; Loom only consumes PR template, required checks, and closeout sync state.",
            },
            "worktree": {
                "ownership": "host",
                "cwd_within_repo": worktree_observation,
                "next_action": "Loom models execution workspace semantics and does not create or retire git worktrees itself.",
                "status": worktree_status,
            },
        },
        "purity": purity,
    }


def governance_profile_payload(target_root: Path, operation: str) -> dict[str, Any]:
    governance_surface = build_governance_surface(target_root)
    control_plane = governance_surface.get("governance_control_plane")
    maturity = control_plane.get("maturity") if isinstance(control_plane, dict) else None
    if not isinstance(maturity, dict):
        return {
            "command": "governance-profile",
            "operation": operation,
            "result": "block",
            "summary": "governance profile maturity could not be read from the unified control plane.",
            "missing_inputs": ["governance_control_plane.maturity"],
            "fallback_to": "admission",
            "governance_surface": governance_surface,
        }

    current = maturity.get("current")
    next_level = maturity.get("next")
    missing_by_level = maturity.get("missing_by_level")
    missing_details_by_level = maturity.get("missing_details_by_level")
    missing_inputs: list[Any] = []
    missing_details: list[Any] = []
    if operation == "upgrade-plan" and isinstance(next_level, str) and isinstance(missing_by_level, dict):
        raw_missing = missing_by_level.get(next_level, [])
        if isinstance(raw_missing, list):
            missing_inputs = raw_missing
        if isinstance(missing_details_by_level, dict):
            raw_details = missing_details_by_level.get(next_level, [])
            if isinstance(raw_details, list):
                missing_details = raw_details
    result = "pass" if not missing_inputs else "block"
    summary = (
        f"governance profile is already at `{current}` maturity."
        if operation == "status" or result == "pass"
        else f"governance profile can upgrade toward `{next_level}` after the missing contracts are installed."
    )
    return {
        "command": "governance-profile",
        "operation": operation,
        "result": result,
        "summary": summary,
        "missing_inputs": missing_inputs,
        "missing_details": missing_details,
        "recommended_action": "run governance-profile upgrade --dry-run" if result == "block" else None,
        "fallback_to": None if result == "pass" else "adoption",
        "maturity": maturity,
        "governance_control_plane": control_plane,
    }


UPGRADE_SCAFFOLD: dict[str, dict[str, str]] = {
    ".loom/companion/manifest.json": json.dumps(
        {
            "schema_version": "loom-repo-companion-manifest/v1",
            "companion_entry": ".loom/companion/AGENTS.md",
            "repo_interface": ".loom/companion/repo-interface.json",
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    ".loom/companion/repo-interface.json": json.dumps(
        {
            "schema_version": "loom-repo-interface/v2",
            "companion_entry": ".loom/companion/AGENTS.md",
            "repo_specific_requirements": {"review": [], "merge_ready": [], "closeout": []},
            "specialized_gates": [],
            "metadata_contract": {"fields": []},
            "context_schema": {"fields": []},
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    ".loom/companion/interop.json": json.dumps(
        {
            "schema_version": "loom-repo-interop/v1",
            "host_adapters": [],
            "repo_native_carriers": [],
            "shadow_surfaces": {},
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    ".loom/companion/AGENTS.md": "# Loom Repo Companion\n\n本文件承接 repo-local governance residue；Loom core 与 GitHub profile 规则仍以上游合同为准。\n",
}


def governance_upgrade_actions(target_root: Path, target_level: str, maturity: dict[str, Any]) -> list[dict[str, Any]]:
    missing_by_level = maturity.get("missing_by_level")
    missing_details_by_level = maturity.get("missing_details_by_level")
    missing = missing_by_level.get(target_level, []) if isinstance(missing_by_level, dict) else []
    missing_details = missing_details_by_level.get(target_level, []) if isinstance(missing_details_by_level, dict) else []
    actions: list[dict[str, Any]] = []
    for relative, content in UPGRADE_SCAFFOLD.items():
        path = target_root / relative
        owner = "loom-owned" if relative.startswith(".loom/") else "repo-owned"
        actions.append(
            {
                "action": "write_scaffold" if not path.exists() else "keep_existing",
                "path": relative,
                "owner": owner,
                "status": "present" if path.exists() else "planned",
                "reason": "required by governance profile upgrade path",
                "bytes": len(content.encode("utf-8")),
            }
        )
    for item in missing if isinstance(missing, list) else []:
        detail = next((row for row in missing_details if isinstance(row, dict) and row.get("id") == item), {})
        actions.append(
            {
                "action": "satisfy_missing_input",
                "id": item,
                "owner": (
                    "loom-owned"
                    if str(item) in {"repo_interface", "repo_interop"}
                    else "profile"
                ),
                "status": "planned",
                "layer": detail.get("layer"),
                "recommended_action": detail.get("recommended_action"),
                "reason": f"`{target_level}` maturity currently reports this missing input.",
            }
        )
    return actions


def governance_profile_upgrade_payload(
    *,
    target_root: Path,
    target_level: str | None,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    if target_level is None:
        return {
            "command": "governance-profile",
            "operation": "upgrade",
            "result": "block",
            "summary": "governance profile upgrade requires `--to standard` or `--to strong`.",
            "missing_inputs": ["to"],
            "fallback_to": "adoption",
        }
    base = governance_profile_payload(target_root, "upgrade-plan")
    maturity = base.get("maturity") if isinstance(base.get("maturity"), dict) else {}
    actions = governance_upgrade_actions(target_root, target_level, maturity if isinstance(maturity, dict) else {})
    blockers: list[str] = []
    written_files: list[str] = []
    if not dry_run:
        for action in actions:
            if action.get("action") != "write_scaffold":
                continue
            relative = action.get("path")
            if not isinstance(relative, str):
                continue
            if action.get("owner") != "loom-owned":
                blockers.append(f"{relative} is repo-owned")
                continue
            path = target_root / relative
            if path.exists() and not force:
                blockers.append(f"{relative} already exists; use --force to replace Loom-owned scaffold")
                continue
            content = UPGRADE_SCAFFOLD.get(relative)
            if content is None:
                blockers.append(f"{relative} has no scaffold content")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            written_files.append(relative)
    result = "block" if blockers else "pass"
    return {
        "command": "governance-profile",
        "operation": "upgrade",
        "schema_version": "loom-governance-upgrade/v1",
        "result": result,
        "summary": (
            f"governance profile upgrade toward `{target_level}` produced a dry-run action plan."
            if dry_run and result == "pass"
            else f"governance profile upgrade toward `{target_level}` applied Loom-owned scaffold writes."
            if result == "pass"
            else f"governance profile upgrade toward `{target_level}` is blocked by unsafe writes."
        ),
        "missing_inputs": blockers,
        "fallback_to": None if result == "pass" else "adoption",
        "target_maturity": target_level,
        "dry_run": dry_run,
        "force": force,
        "actions": actions,
        "written_files": written_files,
        "maturity": maturity,
    }


def maturity_upgrade_path(governance_surface: dict[str, Any], target_root: Path) -> dict[str, Any]:
    control_plane = governance_surface.get("governance_control_plane")
    maturity = control_plane.get("maturity") if isinstance(control_plane, dict) else None
    if not isinstance(maturity, dict):
        return {
            "result": "block",
            "current": "unknown",
            "next": None,
            "missing_inputs": ["governance_control_plane.maturity"],
            "missing_details": [],
            "fallback_to": "admission",
            "upgrade_entry": None,
            "validation_entries": [],
        }
    current = maturity.get("current")
    next_level = maturity.get("next")
    missing_by_level = maturity.get("missing_by_level")
    missing_details_by_level = maturity.get("missing_details_by_level")
    missing_inputs = []
    missing_details = []
    if isinstance(next_level, str):
        if isinstance(missing_by_level, dict) and isinstance(missing_by_level.get(next_level), list):
            missing_inputs = list(missing_by_level[next_level])
        if isinstance(missing_details_by_level, dict) and isinstance(missing_details_by_level.get(next_level), list):
            missing_details = list(missing_details_by_level[next_level])
    return {
        "result": "pass" if next_level is None else "block",
        "current": current,
        "next": next_level,
        "missing_inputs": missing_inputs,
        "missing_details": missing_details,
        "fallback_to": None if next_level is None else "adoption",
        "upgrade_entry": (
            f"python3 tools/loom_flow.py governance-profile upgrade --target {target_root} --to {next_level} --dry-run"
            if isinstance(next_level, str)
            else None
        ),
        "validation_entries": [
            f"python3 tools/loom_flow.py governance-profile status --target {target_root}",
            f"python3 tools/loom_flow.py governance-profile upgrade-plan --target {target_root}",
        ],
    }


def issue_binding_entry(role: str, number: int | None, payload: dict[str, Any] | None, errors: list[str]) -> dict[str, Any]:
    status = "present" if payload is not None else "missing"
    if errors:
        status = "unreadable"
    return {
        "role": role,
        "number": number,
        "status": status,
        "state": payload.get("state") if payload else None,
        "title": payload.get("title") if payload else None,
        "url": payload.get("url") if payload else None,
        "errors": errors,
    }


def text_mentions_issue(text: object, issue_number: int) -> bool:
    if not isinstance(text, str):
        return False
    pattern = re.compile(rf"(?i)(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|refs?|related)\s+#?{issue_number}\b|#{issue_number}\b")
    return bool(pattern.search(text))


def github_binding_payload(
    *,
    target_root: Path,
    owner: str | None,
    repo_name: str | None,
    phase_number: int | None,
    fr_number: int | None,
    issue_number: int | None,
    pr_number: int | None,
    branch_name: str | None,
    sync: bool,
    dry_run: bool,
    require_complete_chain: bool = True,
) -> dict[str, Any]:
    detected_owner, detected_repo = detect_github_repo(target_root)
    owner = owner or detected_owner
    repo_name = repo_name or detected_repo
    missing_inputs: list[str] = []
    findings: list[dict[str, Any]] = []
    repair_plan: list[dict[str, Any]] = []

    if not owner or not repo_name:
        missing_inputs.append("owner/repo")
    if issue_number is None:
        missing_inputs.append("work_item issue")
    if sync and not dry_run:
        missing_inputs.append("dry-run")
        findings.append(
            {
                "category": "gate_failure",
                "kind": "binding_failure",
                "severity": "block",
                "subject": "governance-profile binding sync",
                "why_blocking": "binding sync is read-only in this phase unless --dry-run is set.",
                "fallback_to": "github-profile-binding",
                "evidence": {"sync": sync, "dry_run": dry_run},
            }
        )

    phase_payload: dict[str, Any] | None = None
    fr_payload: dict[str, Any] | None = None
    issue_payload: dict[str, Any] | None = None
    pr_payload: dict[str, Any] | None = None
    branch_payload: dict[str, Any] | None = None
    phase_errors: list[str] = []
    fr_errors: list[str] = []
    issue_errors: list[str] = []
    pr_errors: list[str] = []
    branch_errors: list[str] = []

    if owner and repo_name:
        if phase_number is not None:
            phase_payload, phase_errors = github_issue_payload(target_root, owner, repo_name, phase_number)
            missing_inputs.extend(f"phase: {message}" for message in phase_errors)
        if fr_number is not None:
            fr_payload, fr_errors = github_issue_payload(target_root, owner, repo_name, fr_number)
            missing_inputs.extend(f"fr: {message}" for message in fr_errors)
        if issue_number is not None:
            issue_payload, issue_errors = github_issue_payload(target_root, owner, repo_name, issue_number)
            missing_inputs.extend(f"work_item: {message}" for message in issue_errors)
        if pr_number is not None:
            pr_payload, pr_errors = github_pr_payload(target_root, owner, repo_name, pr_number)
            missing_inputs.extend(f"pr: {message}" for message in pr_errors)

    inferred_branch = branch_name
    if inferred_branch is None and pr_payload is not None and isinstance(pr_payload.get("headRefName"), str):
        inferred_branch = pr_payload.get("headRefName")
    if owner and repo_name and inferred_branch:
        branch_payload, branch_errors = github_branch_payload(target_root, owner, repo_name, inferred_branch)
        missing_inputs.extend(f"branch: {message}" for message in branch_errors)

    if issue_payload is not None and pr_payload is not None:
        pr_body = pr_payload.get("body")
        if not text_mentions_issue(pr_body, int(issue_payload.get("number") or issue_number or 0)):
            findings.append(
                {
                    "category": "gate_failure",
                    "kind": "binding_failure",
                    "severity": "block",
                    "subject": f"PR #{pr_number} -> Work Item #{issue_number}",
                    "why_blocking": "implementation PR body does not mention the Work Item issue.",
                    "fallback_to": "github-profile-binding",
                    "evidence": {
                        "pr_number": pr_number,
                        "issue_number": issue_number,
                        "expected_reference": f"#{issue_number}",
                    },
                }
            )
            repair_plan.append(
                {
                    "action": "update_pr_body",
                    "subject": f"PR #{pr_number}",
                    "body_append": f"\n\nRelated Work\n\n- Closes #{issue_number}\n",
                    "mode": "dry-run" if dry_run else "not-applied",
                }
            )
    if issue_payload is not None and fr_payload is not None and not text_mentions_issue(issue_payload.get("body"), int(fr_number or 0)):
        findings.append(
            {
                "category": "gate_failure",
                "kind": "binding_failure",
                "severity": "block",
                "subject": f"Work Item #{issue_number} -> FR #{fr_number}",
                "why_blocking": "Work Item issue body does not mention the FR issue.",
                "fallback_to": "github-profile-binding",
                "evidence": {"work_item": issue_number, "fr": fr_number, "expected_reference": f"#{fr_number}"},
            }
        )
    if fr_payload is not None and phase_payload is not None and not text_mentions_issue(fr_payload.get("body"), int(phase_number or 0)):
        findings.append(
            {
                "category": "gate_failure",
                "kind": "binding_failure",
                "severity": "block",
                "subject": f"FR #{fr_number} -> Phase #{phase_number}",
                "why_blocking": "FR issue body does not mention the Phase issue.",
                "fallback_to": "github-profile-binding",
                "evidence": {"fr": fr_number, "phase": phase_number, "expected_reference": f"#{phase_number}"},
            }
        )

    merge_commit = pr_payload.get("mergeCommit") if isinstance(pr_payload, dict) else None
    merge_commit_sha = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
    target_branch = pr_payload.get("baseRefName") if isinstance(pr_payload, dict) else None
    binding = {
        "schema_version": "loom-github-binding/v1",
        "repository": {"owner": owner, "name": repo_name},
        "objects": {
            "phase": issue_binding_entry("phase", phase_number, phase_payload, phase_errors),
            "fr": issue_binding_entry("fr", fr_number, fr_payload, fr_errors),
            "work_item": issue_binding_entry("work_item", issue_number, issue_payload, issue_errors),
            "branch": {
                "role": "branch",
                "name": inferred_branch,
                "status": "present" if branch_payload is not None else ("unreadable" if branch_errors else "missing"),
                "head_sha": branch_payload.get("commit", {}).get("sha") if isinstance(branch_payload, dict) and isinstance(branch_payload.get("commit"), dict) else None,
                "errors": branch_errors,
            },
            "implementation_pr": {
                "role": "implementation_pr",
                "number": pr_number,
                "status": "present" if pr_payload is not None else ("unreadable" if pr_errors else "missing"),
                "state": pr_payload.get("state") if pr_payload else None,
                "isDraft": pr_payload.get("isDraft") if pr_payload else None,
                "headRefName": pr_payload.get("headRefName") if pr_payload else None,
                "baseRefName": pr_payload.get("baseRefName") if pr_payload else None,
                "url": pr_payload.get("url") if pr_payload else None,
                "errors": pr_errors,
            },
            "merge_commit": {
                "role": "merge_commit",
                "sha": merge_commit_sha,
                "status": "present" if merge_commit_sha else "missing",
            },
            "target_branch": {
                "role": "target_branch",
                "name": target_branch,
                "status": "present" if target_branch else "missing",
            },
        },
        "chain": [
            {"from": "phase", "to": "fr", "status": "present" if phase_payload and fr_payload else "missing"},
            {"from": "fr", "to": "work_item", "status": "present" if fr_payload and issue_payload else "missing"},
            {"from": "work_item", "to": "implementation_pr", "status": "present" if issue_payload and pr_payload else "missing"},
            {"from": "implementation_pr", "to": "merge_commit", "status": "present" if merge_commit_sha else "missing"},
            {"from": "merge_commit", "to": "target_branch", "status": "present" if merge_commit_sha and target_branch else "missing"},
        ],
        "findings": findings,
        "repair_plan": repair_plan if sync or dry_run else [],
    }
    if require_complete_chain:
        chain_complete = all(entry.get("status") == "present" for entry in binding["chain"])
    else:
        required_edges = []
        if issue_number is not None and pr_number is not None:
            required_edges.append(("work_item", "implementation_pr"))
        if pr_number is not None and pr_payload is not None and pr_payload.get("state") == "MERGED":
            required_edges.extend([("implementation_pr", "merge_commit"), ("merge_commit", "target_branch")])
        chain_complete = all(
            entry.get("status") == "present"
            for entry in binding["chain"]
            if (entry.get("from"), entry.get("to")) in required_edges
        )
    if not chain_complete and "binding_chain" not in missing_inputs:
        missing_inputs.append("binding_chain")
    result = "pass" if not missing_inputs and not findings and chain_complete else "block"
    return {
        "command": "governance-profile",
        "operation": "binding",
        "schema_version": "loom-github-binding/v1",
        "result": result,
        "summary": (
            "GitHub profile binding chain is readable."
            if result == "pass"
            else "GitHub profile binding chain is incomplete or inconsistent."
        ),
        "missing_inputs": missing_inputs,
        "fallback_to": None if result == "pass" else "github-profile-binding",
        "binding": binding,
    }


def handle_governance_profile(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    if args.operation == "upgrade":
        return emit(
            governance_profile_upgrade_payload(
                target_root=target_root,
                target_level=args.to,
                dry_run=args.dry_run,
                force=args.force,
            )
        )
    if args.operation == "binding":
        return emit(
            github_binding_payload(
                target_root=target_root,
                owner=args.owner,
                repo_name=args.repo_name,
                phase_number=args.phase,
                fr_number=args.fr,
                issue_number=args.issue,
                pr_number=args.pr,
                branch_name=args.branch,
                sync=args.sync,
                dry_run=args.dry_run,
            )
        )
    return emit(governance_profile_payload(target_root, args.operation))


def handle_host_lifecycle(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "host-lifecycle",
                "result": "block",
                "summary": "host-lifecycle could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
            }
        )
    return emit(host_lifecycle_payload(context))


def project_status_context(root: Path, owner: str, project_number: int) -> tuple[dict[str, Any], list[str]]:
    project_view, view_errors = gh_json(root, ["project", "view", str(project_number), "--owner", owner, "--format", "json"])
    if view_errors or project_view is None:
        return {}, view_errors
    field_list_payload, field_errors = gh_json(root, ["project", "field-list", str(project_number), "--owner", owner, "--format", "json"])
    if field_errors or field_list_payload is None:
        return {}, field_errors
    fields = field_list_payload.get("fields")
    if not isinstance(fields, list):
        return {}, ["project field list is missing `fields`"]
    status_field_id: str | None = None
    done_option_id: str | None = None
    for field in fields:
        if not isinstance(field, dict):
            continue
        if field.get("name") != "Status":
            continue
        status_field_id = str(field.get("id"))
        options = field.get("options")
        if isinstance(options, list):
            for option in options:
                if isinstance(option, dict) and option.get("name") == "Done":
                    done_option_id = str(option.get("id"))
    project_id = project_view.get("id")
    if not isinstance(project_id, str) or not project_id:
        return {}, ["project view is missing `id`"]
    if not status_field_id or not done_option_id:
        return {}, ["project is missing a `Status` field with a `Done` option"]
    item_list = run_process(["gh", "project", "item-list", str(project_number), "--owner", owner, "--format", "json"], root)
    if item_list.returncode != 0:
        detail = item_list.stderr.strip() or item_list.stdout.strip() or "gh project item-list failed"
        return {}, [detail]
    try:
        payload = json.loads(item_list.stdout)
    except json.JSONDecodeError as exc:
        return {}, [f"invalid JSON from gh project item-list: {exc.msg}"]
    items = payload.get("items")
    if not isinstance(items, list):
        return {}, ["project item list is missing `items`"]
    return {
        "project_id": project_id,
        "status_field_id": status_field_id,
        "done_option_id": done_option_id,
        "items": items,
    }, []


def find_project_item(items: list[dict[str, Any]], number: int, kind: str) -> dict[str, Any] | None:
    for item in items:
        content = item.get("content")
        if not isinstance(content, dict):
            continue
        if content.get("number") != number:
            continue
        item_type = content.get("type")
        if kind == "issue" and item_type == "Issue":
            return item
        if kind == "pr" and item_type == "PullRequest":
            return item
    return None


def project_item_for_issue(root: Path, issue_id: str, project_number: int) -> tuple[dict[str, Any] | None, list[str]]:
    # GraphQL-only for now: GitHub ProjectV2 item field values are not covered by the REST budget-hardening pass.
    query = """
query($id: ID!) {
  node(id: $id) {
    ... on Issue {
      projectItems(first: 50) {
        nodes {
          id
          project {
            number
          }
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                field {
                  ... on ProjectV2SingleSelectField {
                    name
                  }
                }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""
    data, errors = gh_graphql(root, query, {"id": issue_id})
    if errors or data is None:
        return None, errors
    node = data.get("node")
    if not isinstance(node, dict):
        return None, ["issue graphql payload is missing `node`"]
    project_items = node.get("projectItems")
    if not isinstance(project_items, dict):
        return None, ["issue graphql payload is missing `projectItems`"]
    nodes = project_items.get("nodes")
    if not isinstance(nodes, list):
        return None, ["issue graphql payload is missing `projectItems.nodes`"]
    for entry in nodes:
        if not isinstance(entry, dict):
            continue
        project = entry.get("project")
        if not isinstance(project, dict) or project.get("number") != project_number:
            continue
        status_name = None
        field_values = entry.get("fieldValues")
        if isinstance(field_values, dict):
            values = field_values.get("nodes")
            if isinstance(values, list):
                for value in values:
                    if not isinstance(value, dict):
                        continue
                    field = value.get("field")
                    if isinstance(field, dict) and field.get("name") == "Status":
                        name = value.get("name")
                        if isinstance(name, str) and name:
                            status_name = name
        return {
            "id": entry.get("id"),
            "content": {"number": None, "type": "Issue"},
            "status": status_name,
            "budget_guard": graphql_budget_guard("project_v2_item_field_values"),
        }, []
    return None, []


def set_project_item_done(root: Path, project_id: str, item_id: str, status_field_id: str, done_option_id: str) -> list[str]:
    result = run_process(
        [
            "gh",
            "project",
            "item-edit",
            "--id",
            item_id,
            "--project-id",
            project_id,
            "--field-id",
            status_field_id,
            "--single-select-option-id",
            done_option_id,
        ],
        root,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "gh project item-edit failed"
        return [detail]
    return []


def issue_tree_payload(root: Path, owner: str, repo_name: str, issue_number: int) -> tuple[dict[str, Any] | None, list[str]]:
    # GraphQL-only for now: native parent/sub-issue tree shape is outside the high-frequency REST replacement scope.
    query = """
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      id
      number
      title
      state
      url
      parent {
        id
        number
        title
        state
        url
        subIssues(first:50) {
          nodes {
            id
            number
            title
            state
            url
          }
        }
      }
      subIssues(first:50) {
        nodes {
          id
          number
          title
          state
          url
        }
      }
    }
  }
}
"""
    data, errors = gh_graphql(root, query, {"owner": owner, "name": repo_name, "number": issue_number})
    if errors or data is None:
        return None, errors
    repository = data.get("repository")
    if not isinstance(repository, dict):
        return None, ["issue tree graphql payload is missing `repository`"]
    issue = repository.get("issue")
    if not isinstance(issue, dict):
        return None, [f"issue #{issue_number} is missing from GraphQL payload"]
    issue["budget_guard"] = graphql_budget_guard("native_parent_sub_issue_tree")
    return issue, []


def contains_merged_commit(root: Path, merge_commit_sha: str) -> bool:
    run_git(root, ["fetch", "origin", "main"])
    contains = run_git(root, ["merge-base", "--is-ancestor", merge_commit_sha, "origin/main"])
    return contains is not None and contains.returncode == 0


def make_reconciliation_finding(
    *,
    kind: str,
    severity: str,
    subject: str,
    evidence: dict[str, Any],
    recommended_action: str,
    category: str = "drift",
    fallback_to: str | None = None,
) -> dict[str, Any]:
    if fallback_to is None:
        fallback_to = "manual-reconciliation" if severity == "block" else "reconciliation-sync"
    return {
        "category": category,
        "kind": kind,
        "severity": severity,
        "subject": subject,
        "evidence": evidence,
        "recommended_action": recommended_action,
        "fallback_to": fallback_to,
    }


def reconciliation_result(findings: list[dict[str, Any]]) -> str:
    if not findings:
        return "pass"
    rank = {"warn": 1, "fix-needed": 2, "block": 3}
    highest = max(rank.get(str(finding.get("severity")), 0) for finding in findings)
    if highest == 3:
        return "block"
    if highest == 2:
        return "fix-needed"
    return "warn"


def reconciliation_audit_payload(
    *,
    target_root: Path,
    phase_number: int | None,
    fr_number: int | None,
    issue_number: int | None,
    pr_number: int | None,
    project_number: int | None,
    branch_name: str | None,
    owner: str,
    repo_name: str,
) -> tuple[dict[str, Any], list[str]]:
    missing_inputs: list[str] = []
    findings: list[dict[str, Any]] = []

    if issue_number is None and pr_number is None and project_number is None:
        missing_inputs.append("issue/pr/project")

    binding_payload = github_binding_payload(
        target_root=target_root,
        owner=owner,
        repo_name=repo_name,
        phase_number=phase_number,
        fr_number=fr_number,
        issue_number=issue_number,
        pr_number=pr_number,
        branch_name=branch_name,
        sync=False,
        dry_run=False,
        require_complete_chain=False,
    )
    binding = binding_payload.get("binding") if isinstance(binding_payload.get("binding"), dict) else None
    binding_findings = binding.get("findings") if isinstance(binding, dict) else None
    if isinstance(binding_findings, list):
        for finding in binding_findings:
            if isinstance(finding, dict):
                findings.append(
                    make_reconciliation_finding(
                        kind="binding_failure",
                        severity="block",
                        subject=str(finding.get("subject") or "github profile binding"),
                        evidence={"binding": finding.get("evidence", {}), "binding_result": binding_payload.get("result")},
                        recommended_action="repair the GitHub profile binding chain before reconciliation or closeout.",
                        category="gate_failure",
                        fallback_to="manual-reconciliation",
                    )
                )

    issue_payload: dict[str, Any] | None = None
    issue_id: str | None = None
    parent_payload: dict[str, Any] | None = None
    if issue_number is not None:
        issue_payload, issue_errors = github_issue_payload(target_root, owner, repo_name, issue_number)
        if issue_errors:
            missing_inputs.extend(f"issue: {message}" for message in issue_errors)
        elif issue_payload is not None:
            raw_issue_id = issue_payload.get("id")
            if isinstance(raw_issue_id, str) and raw_issue_id:
                issue_id = raw_issue_id
            issue_tree, issue_tree_errors = issue_tree_payload(target_root, owner, repo_name, issue_number)
            if issue_tree_errors:
                issue_payload["sub_issue_tree"] = {
                    "status": "unavailable",
                    "reason": "GraphQL-only parent/sub-issue tree could not be read.",
                    "errors": issue_tree_errors,
                    "budget_guard": graphql_budget_guard("native_parent_sub_issue_tree", issue_tree_errors),
                }
            elif issue_tree is not None:
                issue_payload = {**issue_payload, **issue_tree}
                parent = issue_payload.get("parent")
                if isinstance(parent, dict):
                    parent_payload = parent

    pr_payload: dict[str, Any] | None = None
    merge_commit_sha: str | None = None
    merge_commit_in_main = False
    if pr_number is not None:
        pr_payload, pr_errors = github_pr_payload(target_root, owner, repo_name, pr_number)
        if pr_errors:
            missing_inputs.extend(f"pr: {message}" for message in pr_errors)
        elif pr_payload is not None:
            merge_commit = pr_payload.get("mergeCommit")
            if isinstance(merge_commit, dict):
                oid = merge_commit.get("oid")
                if isinstance(oid, str) and oid:
                    merge_commit_sha = oid
                    merge_commit_in_main = contains_merged_commit(target_root, merge_commit_sha)
            if pr_payload.get("state") == "MERGED" and (not merge_commit_sha or not merge_commit_in_main):
                findings.append(
                    make_reconciliation_finding(
                        kind="merge_signal_drift",
                        severity="block",
                        subject=f"PR #{pr_number} merge signal",
                        evidence={
                            "pr_state": pr_payload.get("state"),
                            "merge_commit": merge_commit_sha,
                            "merge_commit_in_main": merge_commit_in_main,
                        },
                        recommended_action="repair or re-read the merge commit basis before closeout.",
                        category="drift",
                        fallback_to="manual-reconciliation",
                    )
                )

    merged_issue_open = False
    if issue_payload is not None and pr_payload is not None:
        if issue_payload.get("state") == "OPEN" and pr_payload.get("state") == "MERGED" and merge_commit_sha and merge_commit_in_main:
            merged_issue_open = True
            findings.append(
                make_reconciliation_finding(
                    kind="merged_but_open",
                    severity="fix-needed",
                    subject=f"issue #{issue_number}",
                    evidence={
                        "issue_state": issue_payload.get("state"),
                        "pr_number": pr_number,
                        "pr_state": pr_payload.get("state"),
                        "merge_commit": merge_commit_sha,
                        "merge_commit_in_main": merge_commit_in_main,
                    },
                    recommended_action="close the merged issue or run reconciliation sync after reviewing the evidence.",
                )
            )

    parent_scope: dict[str, Any] | None = None
    if parent_payload is not None:
        parent_scope = parent_payload
    elif isinstance(issue_payload, dict):
        sub_issues = issue_payload.get("subIssues")
        if isinstance(sub_issues, dict) and isinstance(sub_issues.get("nodes"), list) and sub_issues.get("nodes"):
            parent_scope = issue_payload

    if parent_scope is not None:
        raw_children = parent_scope.get("subIssues")
        child_nodes = raw_children.get("nodes") if isinstance(raw_children, dict) else None
        unresolved_children: list[dict[str, Any]] = []
        resolved_children: list[dict[str, Any]] = []
        if isinstance(child_nodes, list):
            for child in child_nodes:
                if not isinstance(child, dict):
                    continue
                child_number = child.get("number")
                child_state = child.get("state")
                if child_state == "CLOSED":
                    resolved_children.append(child)
                    continue
                if child_number == issue_number and merged_issue_open:
                    resolved_children.append(child)
                    continue
                unresolved_children.append(child)
        parent_number = parent_scope.get("number")
        parent_state = parent_scope.get("state")
        if parent_state == "CLOSED" and unresolved_children:
            findings.append(
                make_reconciliation_finding(
                    kind="parent_drift",
                    severity="block",
                    subject=f"parent issue #{parent_number}",
                    evidence={
                        "parent_state": parent_state,
                        "unresolved_children": [
                            {"number": child.get("number"), "state": child.get("state"), "title": child.get("title")}
                            for child in unresolved_children
                        ],
                    },
                    recommended_action="reopen the parent issue or finish the unresolved child issues before treating the parent as closed out.",
                )
            )
        elif parent_state == "OPEN" and child_nodes and not unresolved_children:
            findings.append(
                make_reconciliation_finding(
                    kind="parent_drift",
                    severity="fix-needed",
                    subject=f"parent issue #{parent_number}",
                    evidence={
                        "parent_state": parent_state,
                        "resolved_children": [
                            {"number": child.get("number"), "state": child.get("state"), "title": child.get("title")}
                            for child in resolved_children
                        ],
                    },
                    recommended_action="reconcile the parent issue because all child gaps are already closed or absorbed.",
                )
            )

    project_payload: dict[str, Any] | None = None
    project_drift_details: list[dict[str, Any]] = []
    if project_number is not None:
        project_context, project_errors = project_status_context(target_root, owner, project_number)
        if project_errors:
            if any("unknown owner type" in message for message in project_errors):
                project_payload = {
                    "number": project_number,
                    "status": "unavailable",
                    "reason": "GitHub ProjectV2 CLI owner resolution is unavailable in this environment.",
                    "errors": project_errors,
                    "budget_guard": graphql_budget_guard("project_v2_status_surface", project_errors),
                }
            else:
                missing_inputs.extend(f"project: {message}" for message in project_errors)
        else:
            items = project_context["items"]
            issue_item = find_project_item(items, issue_number, "issue") if issue_number is not None else None
            issue_item_budget_guard: dict[str, Any] | None = None
            if issue_item is None and issue_id is not None and issue_number is not None:
                issue_item, issue_item_errors = project_item_for_issue(target_root, issue_id, project_number)
                if issue_item_errors:
                    issue_item_budget_guard = graphql_budget_guard(
                        "project_v2_issue_item_lookup",
                        issue_item_errors,
                    )
            pr_item = find_project_item(items, pr_number, "pr") if pr_number is not None else None
            project_payload = {
                "number": project_number,
                "project_id": project_context["project_id"],
                "status_field_id": project_context["status_field_id"],
                "done_option_id": project_context["done_option_id"],
                "issue_item": issue_item,
                "pr_item": pr_item,
            }
            if issue_item_budget_guard is not None:
                project_payload["issue_item_budget_guard"] = issue_item_budget_guard

            if issue_number is not None:
                expected_done = issue_payload is not None and (issue_payload.get("state") == "CLOSED" or merged_issue_open)
                if issue_item is None:
                    project_drift_details.append(
                        {
                            "subject": f"issue #{issue_number}",
                            "reason": "issue is missing from project",
                            "expected_done": expected_done,
                        }
                    )
                else:
                    status = issue_item.get("status")
                    if expected_done and status != "Done":
                        project_drift_details.append(
                            {
                                "subject": f"issue #{issue_number}",
                                "reason": "issue project status is not Done",
                                "expected_done": True,
                                "actual_status": status,
                            }
                        )
                    if not expected_done and status == "Done":
                        project_drift_details.append(
                            {
                                "subject": f"issue #{issue_number}",
                                "reason": "issue project status is Done while the issue still has an open gap",
                                "expected_done": False,
                                "actual_status": status,
                            }
                        )

            if pr_number is not None:
                expected_done = pr_payload is not None and pr_payload.get("state") == "MERGED"
                if pr_item is not None:
                    status = pr_item.get("status")
                    if expected_done and status != "Done":
                        project_drift_details.append(
                            {
                                "subject": f"pr #{pr_number}",
                                "reason": "pr project status is not Done",
                                "expected_done": True,
                                "actual_status": status,
                            }
                        )
                    if not expected_done and status == "Done":
                        project_drift_details.append(
                            {
                                "subject": f"pr #{pr_number}",
                                "reason": "pr project status is Done while the PR is not merged",
                                "expected_done": False,
                                "actual_status": status,
                            }
                        )

    if project_drift_details:
        findings.append(
            make_reconciliation_finding(
                kind="project_drift",
                severity="fix-needed",
                subject=f"project {project_number}",
                evidence={"drifts": project_drift_details},
                recommended_action="align the project items with the audited issue/PR state before closeout.",
            )
        )

    if missing_inputs:
        findings.append(
            make_reconciliation_finding(
                kind="host_signal_drift",
                severity="block",
                subject="github control plane",
                evidence={"missing_inputs": missing_inputs},
                recommended_action="restore readable GitHub issue, PR, project, or repository signals before closeout.",
                category="drift",
                fallback_to="manual-reconciliation",
            )
        )
        result = "block"
        summary = "reconciliation audit could not complete because required GitHub inputs were missing."
    else:
        result = reconciliation_result(findings)
        summary = (
            "reconciliation audit found no merged-but-open, absorbed-but-open, parent-drift, host-signal-drift, or project-drift findings."
            if result == "pass"
            else "reconciliation audit found GitHub drift that must be reviewed before closeout."
        )
    return (
        {
            "command": "reconciliation",
            "operation": "audit",
            "result": result,
            "summary": summary,
            "missing_inputs": missing_inputs,
            "fallback_to": None if result == "pass" else "manual-reconciliation",
            "repo": {"owner": owner, "name": repo_name},
            "issue": issue_payload,
            "parent": parent_payload,
            "pr": pr_payload,
            "project": project_payload,
            "binding": binding,
            "findings": findings,
        },
        [],
    )


def reconciliation_sync_plan(audit_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    plan: list[dict[str, Any]] = []
    skipped_actions: list[dict[str, Any]] = []
    findings = audit_payload.get("findings")
    if not isinstance(findings, list):
        return plan, skipped_actions
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = finding.get("severity")
        kind = finding.get("kind")
        subject = finding.get("subject")
        evidence = finding.get("evidence")
        if severity != "fix-needed":
            continue
        if kind in {"merged_but_open", "absorbed_but_open"}:
            plan.append(
                {
                    "kind": kind,
                    "subject": subject,
                    "action": "close_issue",
                    "issue_number": audit_payload.get("issue", {}).get("number"),
                }
            )
            continue
        if kind == "project_drift":
            project = audit_payload.get("project")
            if not isinstance(project, dict):
                skipped_actions.append(
                    {
                        "kind": kind,
                        "subject": subject,
                        "action": "set_project_status",
                        "reason": "project_drift is missing project context",
                    }
                )
                continue
            drifts = evidence.get("drifts") if isinstance(evidence, dict) else None
            if not isinstance(drifts, list):
                skipped_actions.append(
                    {
                        "kind": kind,
                        "subject": subject,
                        "action": "set_project_status",
                        "reason": "project_drift is missing drift details",
                    }
                )
                continue
            for drift in drifts:
                if not isinstance(drift, dict):
                    continue
                drift_subject = drift.get("subject")
                reason = str(drift.get("reason", ""))
                expected_done = drift.get("expected_done")
                if expected_done is not True:
                    skipped_actions.append(
                        {
                            "kind": kind,
                            "subject": drift_subject,
                            "action": "set_project_status",
                            "reason": f"requires manual reconciliation: {reason}",
                        }
                    )
                    continue
                item_key = None
                if isinstance(drift_subject, str) and drift_subject.startswith("issue #"):
                    item_key = "issue_item"
                elif isinstance(drift_subject, str) and drift_subject.startswith("pr #"):
                    item_key = "pr_item"
                item = project.get(item_key) if item_key else None
                if not isinstance(item, dict):
                    skipped_actions.append(
                        {
                            "kind": kind,
                            "subject": drift_subject,
                            "action": "set_project_status",
                            "reason": "cannot be synced because the project item is missing",
                        }
                    )
                    continue
                item_id = item.get("id")
                project_id = project.get("project_id")
                status_field_id = project.get("status_field_id")
                done_option_id = project.get("done_option_id")
                if not all(isinstance(value, str) and value for value in (item_id, project_id, status_field_id, done_option_id)):
                    skipped_actions.append(
                        {
                            "kind": kind,
                            "subject": drift_subject,
                            "action": "set_project_status",
                            "reason": "is missing project status identifiers",
                        }
                    )
                    continue
                plan.append(
                    {
                        "kind": kind,
                        "subject": drift_subject,
                        "action": "set_project_done",
                        "project_number": project.get("number"),
                        "project_id": project_id,
                        "item_id": item_id,
                        "status_field_id": status_field_id,
                        "done_option_id": done_option_id,
                    }
                )
            continue
        if kind == "parent_drift":
            parent = audit_payload.get("parent")
            parent_number = parent.get("number") if isinstance(parent, dict) else None
            if parent_number is None:
                skipped_actions.append(
                    {
                        "kind": kind,
                        "subject": subject,
                        "action": "close_issue",
                        "reason": "parent_drift is missing parent issue context",
                    }
                )
                continue
            plan.append(
                {
                    "kind": kind,
                    "subject": subject,
                    "action": "close_issue",
                    "issue_number": parent_number,
                }
            )
            continue
        skipped_actions.append(
            {
                "kind": kind,
                "subject": subject,
                "action": "unsupported",
                "reason": f"unsupported reconciliation finding `{kind}`",
            }
        )
    return plan, skipped_actions


def closeout_reconciliation_result(
    audit_payload: dict[str, Any] | None,
) -> tuple[str | None, str | None]:
    if not isinstance(audit_payload, dict):
        return None, None
    result = audit_payload.get("result")
    if result == "fix-needed":
        return "reconciliation-sync", "closeout requires reconciliation sync before it can pass."
    if result == "block":
        return "manual-reconciliation", "closeout requires manual reconciliation because the audit itself is blocked."
    return None, None


def runtime_parity_check(
    name: str,
    *,
    result: str,
    summary: str,
    evidence: dict[str, Any] | None = None,
    missing_inputs: list[str] | None = None,
    fallback_to: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "result": result,
        "summary": summary,
        "evidence": evidence or {},
        "missing_inputs": missing_inputs or [],
        "fallback_to": fallback_to,
    }


def runtime_parity_payload(
    *,
    target_root: Path,
    output_relative: str,
    expected_item: str | None,
) -> dict[str, Any]:
    runtime_state = runtime_state_payload(target_root)
    checks: list[dict[str, Any]] = []
    if runtime_state["result"] != "pass":
        checks.append(
            runtime_parity_check(
                "runtime_state",
                result="block",
                summary="runtime carrier is not consistent enough to prove runtime parity.",
                missing_inputs=list(runtime_state.get("missing_inputs", [])),
                fallback_to=runtime_state.get("fallback_to"),
                evidence={"runtime_state": runtime_state},
            )
        )
        return {
            "command": "runtime-parity",
            "operation": "validate",
            "schema_version": "loom-runtime-parity/v1",
            "result": "block",
            "summary": "Loom core runtime parity validation is blocked by runtime-state drift.",
            "missing_inputs": list(runtime_state.get("missing_inputs", [])),
            "fallback_to": runtime_state.get("fallback_to"),
            "runtime_state": runtime_state,
            "checks": checks,
        }

    context, context_errors = load_context(target_root, output_relative, expected_item)
    governance_surface = build_governance_surface(target_root)
    control_plane = governance_surface.get("governance_control_plane")
    carrier_summary = governance_surface.get("carrier_summary")

    if context_errors:
        checks.append(
            runtime_parity_check(
                "work_item",
                result="block",
                summary="runtime parity could not read the Work Item fact chain.",
                missing_inputs=[f"fact-chain: {message}" for message in context_errors],
                fallback_to="admission",
            )
        )
    else:
        checks.append(
            runtime_parity_check(
                "work_item",
                result="pass",
                summary="Work Item is readable as the single execution entry.",
                evidence={
                    "item_id": context["item_id"],
                    "work_item": context["report"]["fact_chain"]["entry_points"]["work_item"],
                    "recovery_entry": context["report"]["fact_chain"]["entry_points"]["recovery_entry"],
                    "status_surface": context["report"]["fact_chain"]["entry_points"]["status_surface"],
                },
            )
        )

    if isinstance(control_plane, dict) and control_plane.get("schema_version") == "loom-governance-control/v1":
        checks.append(
            runtime_parity_check(
                "status_control_plane",
                result="pass",
                summary="governance control plane is available as a machine-readable runtime surface.",
                evidence={
                    "schema_version": control_plane.get("schema_version"),
                    "taxonomy": sorted((control_plane.get("taxonomy") or {}).keys())
                    if isinstance(control_plane.get("taxonomy"), dict)
                    else [],
                    "maturity": (control_plane.get("maturity") or {}).get("current")
                    if isinstance(control_plane.get("maturity"), dict)
                    else None,
                },
            )
        )
    else:
        checks.append(
            runtime_parity_check(
                "status_control_plane",
                result="block",
                summary="governance control plane is missing or unreadable.",
                missing_inputs=["governance_control_plane"],
                fallback_to="admission",
            )
        )

    expected_gate_order = [
        "work_item_admission",
        "spec_gate",
        "build_gate",
        "review_gate",
        "merge_gate",
        "github_controlled_merge",
        "closeout",
    ]
    gate_chain = control_plane.get("gate_chain") if isinstance(control_plane, dict) else None
    actual_gate_order = [entry.get("id") for entry in gate_chain if isinstance(entry, dict)] if isinstance(gate_chain, (list, tuple)) else []
    checks.append(
        runtime_parity_check(
            "gate_chain",
            result="pass" if actual_gate_order == expected_gate_order else "block",
            summary=(
                "strong governance gate chain is available in runtime order."
                if actual_gate_order == expected_gate_order
                else "strong governance gate chain does not match the runtime parity contract."
            ),
            evidence={"gate_order": actual_gate_order, "expected_gate_order": expected_gate_order},
            missing_inputs=[] if actual_gate_order == expected_gate_order else ["governance_control_plane.gate_chain"],
            fallback_to=None if actual_gate_order == expected_gate_order else "admission",
        )
    )

    host_binding = control_plane.get("host_binding") if isinstance(control_plane, dict) else None
    required_objects = host_binding.get("required_objects") if isinstance(host_binding, dict) else None
    controlled_merge_ready = (
        isinstance(host_binding, dict)
        and isinstance(required_objects, dict)
        and {"implementation_pr", "merge_commit", "closeout"}.issubset(required_objects.keys())
    )
    checks.append(
        runtime_parity_check(
            "controlled_merge_contract",
            result="pass" if controlled_merge_ready else "block",
            summary=(
                "controlled merge contract exposes PR, merge commit, and closeout host-owned bindings."
                if controlled_merge_ready
                else "controlled merge contract is missing required host-owned bindings."
            ),
            evidence={
                "host_binding_result": host_binding.get("result") if isinstance(host_binding, dict) else None,
                "required_objects": sorted(required_objects.keys()) if isinstance(required_objects, dict) else [],
            },
            missing_inputs=[] if controlled_merge_ready else ["governance_control_plane.host_binding"],
            fallback_to=None if controlled_merge_ready else "merge",
        )
    )

    closeout_gate = next((entry for entry in gate_chain or [] if isinstance(entry, dict) and entry.get("id") == "closeout"), {})
    closeout_requires = closeout_gate.get("requires") if isinstance(closeout_gate, dict) else None
    closeout_ready = isinstance(closeout_requires, (list, tuple)) and "reconciliation_audit" in closeout_requires
    checks.append(
        runtime_parity_check(
            "closeout_reconciliation",
            result="pass" if closeout_ready else "block",
            summary=(
                "closeout gate consumes reconciliation audit as a runtime prerequisite."
                if closeout_ready
                else "closeout gate does not expose reconciliation audit as a runtime prerequisite."
            ),
            evidence={
                "closeout_requires": closeout_requires if isinstance(closeout_requires, (list, tuple)) else [],
                "repo_interop_availability": (governance_surface.get("repo_interop") or {}).get("availability")
                if isinstance(governance_surface.get("repo_interop"), dict)
                else None,
            },
            missing_inputs=[] if closeout_ready else ["governance_control_plane.gate_chain.closeout"],
            fallback_to=None if closeout_ready else "reconciliation-sync",
        )
    )

    checks.append(
        runtime_parity_check(
            "shadow_parity_boundary",
            result="pass",
            summary="shadow parity remains validation-only in Loom core runtime parity.",
            evidence={
                "default_result_contract": ["pass", "warn"],
                "blocking_default": False,
                "surfaces": list(SHADOW_PARITY_SURFACES),
            },
        )
    )

    if not isinstance(carrier_summary, dict):
        checks.append(
            runtime_parity_check(
                "carrier_summary",
                result="block",
                summary="carrier summary is missing from governance surface.",
                missing_inputs=["governance_surface.carrier_summary"],
                fallback_to="admission",
            )
        )

    missing_inputs: list[str] = []
    fallback_to: str | None = None
    for check in checks:
        if check["result"] == "block":
            fallback_to = fallback_to or check.get("fallback_to")
            for message in check.get("missing_inputs", []):
                if message not in missing_inputs:
                    missing_inputs.append(message)

    result = "pass" if not missing_inputs else "block"
    return {
        "command": "runtime-parity",
        "operation": "validate",
        "schema_version": "loom-runtime-parity/v1",
        "result": result,
        "summary": (
            "Loom core runtime parity is machine-readable across Work Item, status, gates, controlled merge, closeout, and shadow boundary."
            if result == "pass"
            else "Loom core runtime parity validation found missing or unreadable runtime surfaces."
        ),
        "missing_inputs": missing_inputs,
        "fallback_to": fallback_to,
        "runtime_state": runtime_state,
        "checks": checks,
    }


def closeout_payload(
    *,
    target_root: Path,
    phase_number: int | None,
    fr_number: int | None,
    issue_number: int | None,
    pr_number: int | None,
    project_number: int | None,
    branch_name: str | None,
    owner: str,
    repo_name: str,
    skip_gate: bool,
) -> tuple[dict[str, Any], list[str]]:
    missing_inputs: list[str] = []
    governance_surface = build_governance_surface(target_root)
    repo_specific_requirements = repo_specific_requirements_payload(
        governance_surface.get("repo_interface"),
        target_root=target_root,
        surface="closeout",
    )
    gate: dict[str, Any] = {"skipped": skip_gate}
    if not skip_gate:
        repo_gate = target_root / ".loom/bin/loom_check.py"
        if repo_gate.exists():
            gate_command = ["python3", ".loom/bin/loom_check.py", "."]
        else:
            gate_command = ["python3", str(shared_script(__file__, "loom_check.py")), str(target_root)]
        gate_result = run_process(gate_command, target_root)
        gate["command"] = " ".join(gate_command)
        gate["exit_code"] = gate_result.returncode
        gate["stdout"] = gate_result.stdout.strip()
        if gate_result.returncode != 0:
            missing_inputs.append("loom_check")

    reconciliation_payload: dict[str, Any] | None = None
    closeout_fallback: str | None = None
    closeout_summary_override: str | None = None
    if issue_number is not None or pr_number is not None or project_number is not None:
        reconciliation_payload, reconciliation_errors = reconciliation_audit_payload(
            target_root=target_root,
            phase_number=phase_number,
            fr_number=fr_number,
            issue_number=issue_number,
            pr_number=pr_number,
            project_number=project_number,
            branch_name=branch_name,
            owner=owner,
            repo_name=repo_name,
        )
        if reconciliation_errors:
            missing_inputs.extend(f"reconciliation: {message}" for message in reconciliation_errors)
        else:
            closeout_fallback, closeout_summary_override = closeout_reconciliation_result(reconciliation_payload)
            if closeout_fallback == "reconciliation-sync":
                missing_inputs.append("reconciliation audit requires sync")
            if closeout_fallback == "manual-reconciliation":
                missing_inputs.append("reconciliation audit is blocked")

    issue_payload: dict[str, Any] | None = None
    issue_id: str | None = None
    if issue_number is not None:
        issue_payload, issue_errors = github_issue_payload(target_root, owner, repo_name, issue_number)
        if issue_errors:
            missing_inputs.extend(f"issue: {message}" for message in issue_errors)
        elif issue_payload is not None:
            raw_issue_id = issue_payload.get("id")
            if isinstance(raw_issue_id, str) and raw_issue_id:
                issue_id = raw_issue_id

    pr_payload: dict[str, Any] | None = None
    merge_commit_sha: str | None = None
    if pr_number is not None:
        pr_payload, pr_errors = github_pr_payload(target_root, owner, repo_name, pr_number)
        if pr_errors:
            missing_inputs.extend(f"pr: {message}" for message in pr_errors)
        elif pr_payload is not None:
            merge_commit = pr_payload.get("mergeCommit")
            if isinstance(merge_commit, dict):
                oid = merge_commit.get("oid")
                if isinstance(oid, str) and oid:
                    merge_commit_sha = oid
            if pr_payload.get("state") != "MERGED":
                missing_inputs.append("pr is not merged")
            if merge_commit_sha:
                run_git(target_root, ["fetch", "origin", "main"])
                contains = run_git(target_root, ["merge-base", "--is-ancestor", merge_commit_sha, "origin/main"])
                if contains is None or contains.returncode != 0:
                    missing_inputs.append("origin/main does not contain the merged PR commit")

    project_payload: dict[str, Any] | None = None
    if project_number is not None:
        project_context, project_errors = project_status_context(target_root, owner, project_number)
        if project_errors:
            if any("unknown owner type" in message for message in project_errors):
                project_payload = {
                    "number": project_number,
                    "status": "unavailable",
                    "reason": "GitHub ProjectV2 CLI owner resolution is unavailable in this environment.",
                    "errors": project_errors,
                    "budget_guard": graphql_budget_guard("project_v2_status_surface", project_errors),
                }
            else:
                missing_inputs.extend(f"project: {message}" for message in project_errors)
        else:
            items = project_context["items"]
            issue_item = find_project_item(items, issue_number, "issue") if issue_number is not None else None
            issue_item_budget_guard: dict[str, Any] | None = None
            if issue_item is None and issue_id is not None and issue_number is not None:
                issue_item, issue_item_errors = project_item_for_issue(target_root, issue_id, project_number)
                if issue_item_errors:
                    issue_item_budget_guard = graphql_budget_guard(
                        "project_v2_issue_item_lookup",
                        issue_item_errors,
                    )
            pr_item = find_project_item(items, pr_number, "pr") if pr_number is not None else None
            if issue_number is not None and issue_item is None:
                missing_inputs.append("issue is missing from project")
            project_payload = {
                "number": project_number,
                "project_id": project_context["project_id"],
                "status_field_id": project_context["status_field_id"],
                "done_option_id": project_context["done_option_id"],
                "issue_item": issue_item,
                "pr_item": pr_item,
            }
            if issue_item_budget_guard is not None:
                project_payload["issue_item_budget_guard"] = issue_item_budget_guard
            for label, item in (("issue", issue_item), ("pr", pr_item)):
                if item is None:
                    continue
                status = item.get("status")
                if isinstance(status, str) and status != "Done":
                    missing_inputs.append(f"{label} project status is not Done")

    if issue_payload is not None and issue_payload.get("state") != "CLOSED":
        missing_inputs.append("issue is not closed")

    result = "pass" if not missing_inputs else "block"
    summary = (
        "closeout state is consistent across gate, GitHub issue/PR, project, and main."
        if result == "pass"
        else "closeout state is not yet consistent across gate, GitHub issue/PR, project, and main."
    )
    fallback_to = None if result == "pass" else "merge"
    if result == "block" and closeout_summary_override is not None:
        summary = closeout_summary_override
        fallback_to = closeout_fallback
    elif result == "pass" and isinstance(reconciliation_payload, dict) and reconciliation_payload.get("result") == "warn":
        summary = "closeout state is consistent, but reconciliation audit reported non-blocking warnings that still need review."
    if result == "pass" and repo_specific_requirements["result"] == "block":
        result = "block"
        summary = repo_specific_requirements["summary"]
        fallback_to = repo_specific_requirements["fallback_to"]
        missing_inputs.extend(repo_specific_requirements["missing_inputs"])
    return (
        {
            "command": "closeout",
            "operation": "check",
            "result": result,
            "summary": summary,
            "missing_inputs": missing_inputs,
            "fallback_to": fallback_to,
            "repo": {"owner": owner, "name": repo_name},
            "gate": gate,
            "issue": issue_payload,
            "pr": pr_payload,
            "project": project_payload,
            "repo_specific_requirements": repo_specific_requirements,
            **({"reconciliation": reconciliation_payload} if reconciliation_payload is not None else {}),
        },
        [],
    )


def handle_closeout(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            runtime_state_block_payload(
                command="closeout",
                operation=args.operation,
                runtime_state=runtime_state,
                summary="closeout is blocked because the Loom runtime state is inconsistent.",
            )
        )
    owner = args.owner
    repo_name = args.repo_name
    if not owner or not repo_name:
        detected_owner, detected_repo = detect_github_repo(target_root)
        owner = owner or detected_owner
        repo_name = repo_name or detected_repo
    if not owner or not repo_name:
        return emit(
            {
                "command": "closeout",
                "operation": args.operation,
                "result": "block",
                "summary": "closeout could not determine the GitHub repository.",
                "missing_inputs": ["owner/repo"],
                "fallback_to": "merge",
                "runtime_state": runtime_state,
            }
        )

    payload, errors = closeout_payload(
        target_root=target_root,
        phase_number=args.phase,
        fr_number=args.fr,
        issue_number=args.issue,
        pr_number=args.pr,
        project_number=args.project,
        branch_name=args.branch,
        owner=owner,
        repo_name=repo_name,
        skip_gate=args.skip_gate,
    )
    if errors:
        return emit(
            {
                "command": "closeout",
                "operation": args.operation,
                "result": "block",
                "summary": "closeout command hit an unexpected internal error.",
                "missing_inputs": errors,
                "fallback_to": "merge",
                "runtime_state": runtime_state,
            }
        )

    payload["runtime_state"] = runtime_state
    if args.operation == "check":
        return emit(payload)

    reconciliation = payload.get("reconciliation")
    repo_specific_requirements = payload.get("repo_specific_requirements")
    if isinstance(repo_specific_requirements, dict) and repo_specific_requirements.get("result") == "block":
        return emit(
            {
                **payload,
                "operation": "sync",
                "result": "block",
                "summary": "closeout sync is blocked until companion-declared blocking requirements are handled.",
                "fallback_to": repo_specific_requirements.get("fallback_to") or "merge",
                "runtime_state": runtime_state,
            }
        )
    if isinstance(reconciliation, dict):
        reconciliation_result = reconciliation.get("result")
        if reconciliation_result in {"fix-needed", "block"}:
            return emit(
                {
                    **payload,
                    "operation": "sync",
                    "result": "block",
                    "summary": (
                        "closeout sync is blocked until reconciliation sync repairs the audited drift."
                        if reconciliation_result == "fix-needed"
                        else "closeout sync is blocked because reconciliation audit could not complete."
                    ),
                    "fallback_to": "reconciliation-sync" if reconciliation_result == "fix-needed" else "manual-reconciliation",
                    "runtime_state": runtime_state,
                }
            )

    sync_missing: list[str] = []
    if args.issue is not None:
        issue = payload.get("issue")
        if isinstance(issue, dict) and issue.get("state") != "CLOSED":
            if args.comment:
                comment_result = run_process(
                    [
                        "gh",
                        "issue",
                        "comment",
                        str(args.issue),
                        "--repo",
                        f"{owner}/{repo_name}",
                        "--body",
                        args.comment,
                    ],
                    target_root,
                )
                if comment_result.returncode != 0:
                    sync_missing.append(comment_result.stderr.strip() or "failed to comment on issue")
            close_result = run_process(
                ["gh", "issue", "close", str(args.issue), "--repo", f"{owner}/{repo_name}"],
                target_root,
            )
            if close_result.returncode != 0:
                sync_missing.append(close_result.stderr.strip() or "failed to close issue")

    if args.project is not None:
        project = payload.get("project")
        if isinstance(project, dict):
            for key in ("issue_item", "pr_item"):
                item = project.get(key)
                if not isinstance(item, dict):
                    continue
                status = item.get("status")
                item_id = item.get("id")
                if not isinstance(item_id, str) or not item_id:
                    continue
                if status != "Done":
                    sync_missing.extend(
                        set_project_item_done(
                            target_root,
                            project["project_id"],
                            item_id,
                            project["status_field_id"],
                            project["done_option_id"],
                        )
                    )

    refreshed_payload, errors = closeout_payload(
        target_root=target_root,
        phase_number=args.phase,
        fr_number=args.fr,
        issue_number=args.issue,
        pr_number=args.pr,
        project_number=args.project,
        branch_name=args.branch,
        owner=owner,
        repo_name=repo_name,
        skip_gate=args.skip_gate,
    )
    if errors:
        sync_missing.extend(errors)
    refreshed_payload["operation"] = "sync"

    if sync_missing:
        refreshed_payload["result"] = "block"
        refreshed_payload["summary"] = "closeout sync could not fully align GitHub control-plane state."
        refreshed_payload["missing_inputs"] = list(dict.fromkeys(sync_missing + list(refreshed_payload.get("missing_inputs", []))))
        refreshed_payload["fallback_to"] = "merge"
    refreshed_payload["runtime_state"] = runtime_state
    return emit(refreshed_payload)


def handle_reconciliation(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            runtime_state_block_payload(
                command="reconciliation",
                operation=args.operation,
                runtime_state=runtime_state,
                summary="reconciliation is blocked because the Loom runtime state is inconsistent.",
            )
        )
    owner = args.owner
    repo_name = args.repo_name
    if not owner or not repo_name:
        detected_owner, detected_repo = detect_github_repo(target_root)
        owner = owner or detected_owner
        repo_name = repo_name or detected_repo
    if not owner or not repo_name:
        return emit(
            {
                "command": "reconciliation",
                "operation": args.operation,
                "result": "block",
                "summary": "reconciliation could not determine the GitHub repository.",
                "missing_inputs": ["owner/repo"],
                "fallback_to": "manual-reconciliation",
                "runtime_state": runtime_state,
            }
        )

    if args.comment and args.comment_file:
        return emit(
            {
                "command": "reconciliation",
                "operation": args.operation,
                "result": "block",
                "summary": "reconciliation sync accepts either --comment or --comment-file, not both.",
                "missing_inputs": ["choose one comment source"],
                "fallback_to": "manual-reconciliation",
                "runtime_state": runtime_state,
            }
        )

    comment_body = args.comment
    if args.comment_file:
        comment_body, comment_errors = read_text_file(args.comment_file)
        if comment_errors:
            return emit(
                {
                    "command": "reconciliation",
                    "operation": args.operation,
                    "result": "block",
                    "summary": "reconciliation sync could not read the requested comment file.",
                    "missing_inputs": comment_errors,
                    "fallback_to": "manual-reconciliation",
                    "runtime_state": runtime_state,
                }
            )

    payload, errors = reconciliation_audit_payload(
        target_root=target_root,
        phase_number=args.phase,
        fr_number=args.fr,
        issue_number=args.issue,
        pr_number=args.pr,
        project_number=args.project,
        branch_name=args.branch,
        owner=owner,
        repo_name=repo_name,
    )
    if errors:
        return emit(
            {
                "command": "reconciliation",
                "operation": args.operation,
                "result": "block",
                "summary": "reconciliation command hit an unexpected internal error.",
                "missing_inputs": errors,
                "fallback_to": "manual-reconciliation",
                "runtime_state": runtime_state,
            }
        )
    payload["runtime_state"] = runtime_state
    if args.operation == "audit":
        return emit(payload)

    if payload.get("result") == "block":
        return emit(
            {
                **payload,
                "operation": "sync",
                "summary": "reconciliation sync stopped because audit returned block findings or missing inputs.",
                "applied_actions": [],
                "skipped_actions": [],
                "remaining_findings": list(payload.get("findings", [])),
                "runtime_state": runtime_state,
            }
        )

    applied_actions, skipped_actions = reconciliation_sync_plan(payload)
    remaining_findings = [
        finding
        for finding in payload.get("findings", [])
        if isinstance(finding, dict) and finding.get("severity") == "warn"
    ]
    sync_missing: list[str] = []

    if args.dry_run:
        dry_run_actions = [{**action, "dry_run": True} for action in applied_actions]
        has_unresolved_fix_needed = any(
            isinstance(finding, dict) and finding.get("severity") == "fix-needed"
            for finding in payload.get("findings", [])
        ) and bool(skipped_actions)
        return emit(
            {
                **payload,
                "operation": "sync",
                "result": "block" if has_unresolved_fix_needed else "pass",
                "summary": (
                    "reconciliation sync dry-run produced the planned control-plane actions."
                    if not has_unresolved_fix_needed
                    else "reconciliation sync dry-run found fix-needed drift that still requires manual reconciliation."
                ),
                "applied_actions": dry_run_actions,
                "skipped_actions": skipped_actions,
                "remaining_findings": list(payload.get("findings", [])),
                "dry_run": True,
                "fallback_to": None if not has_unresolved_fix_needed else "manual-reconciliation",
                "runtime_state": runtime_state,
            }
        )

    executed_actions: list[dict[str, Any]] = []
    for action in applied_actions:
        step_kind = action.get("action")
        subject = action.get("subject")
        if step_kind == "close_issue":
            issue_number = action.get("issue_number")
            if not isinstance(issue_number, int):
                sync_missing.append(f"{subject} is missing an issue number for reconciliation sync")
                skipped_actions.append(
                    {
                        "kind": action.get("kind"),
                        "subject": subject,
                        "action": step_kind,
                        "reason": "missing issue number for reconciliation sync",
                    }
                )
                continue
            if comment_body and issue_number == args.issue:
                comment_result = run_process(
                    [
                        "gh",
                        "issue",
                        "comment",
                        str(issue_number),
                        "--repo",
                        f"{owner}/{repo_name}",
                        "--body",
                        comment_body,
                    ],
                    target_root,
                )
                if comment_result.returncode != 0:
                    sync_missing.append(comment_result.stderr.strip() or f"failed to comment on issue #{issue_number}")
                    skipped_actions.append(
                        {
                            "kind": action.get("kind"),
                            "subject": subject,
                            "action": step_kind,
                            "reason": f"failed to comment on issue #{issue_number}",
                        }
                    )
                    continue
            close_result = run_process(
                ["gh", "issue", "close", str(issue_number), "--repo", f"{owner}/{repo_name}"],
                target_root,
            )
            if close_result.returncode != 0:
                sync_missing.append(close_result.stderr.strip() or f"failed to close issue #{issue_number}")
                skipped_actions.append(
                    {
                        "kind": action.get("kind"),
                        "subject": subject,
                        "action": step_kind,
                        "reason": close_result.stderr.strip() or f"failed to close issue #{issue_number}",
                    }
                )
                continue
            executed_actions.append(action)
            continue
        if step_kind == "set_project_done":
            step_errors = set_project_item_done(
                target_root,
                action["project_id"],
                action["item_id"],
                action["status_field_id"],
                action["done_option_id"],
            )
            if step_errors:
                sync_missing.extend(step_errors)
                skipped_actions.append(
                    {
                        "kind": action.get("kind"),
                        "subject": subject,
                        "action": step_kind,
                        "reason": "; ".join(step_errors),
                    }
                )
                continue
            executed_actions.append(action)
            continue
        sync_missing.append(f"{subject} uses unsupported sync action `{step_kind}`")
        skipped_actions.append(
            {
                "kind": action.get("kind"),
                "subject": subject,
                "action": step_kind,
                "reason": f"unsupported sync action `{step_kind}`",
            }
        )

    refreshed_payload, refreshed_errors = reconciliation_audit_payload(
        target_root=target_root,
        phase_number=args.phase,
        fr_number=args.fr,
        issue_number=args.issue,
        pr_number=args.pr,
        project_number=args.project,
        branch_name=args.branch,
        owner=owner,
        repo_name=repo_name,
    )
    if refreshed_errors:
        sync_missing.extend(refreshed_errors)
        refreshed_payload = payload
    remaining_findings = [finding for finding in refreshed_payload.get("findings", []) if isinstance(finding, dict)]
    unresolved_fix_needed = any(finding.get("severity") == "fix-needed" for finding in remaining_findings)

    result = "pass"
    summary = "reconciliation sync aligned the requested GitHub control-plane state."
    fallback_to = None
    if sync_missing or unresolved_fix_needed:
        result = "block"
        summary = "reconciliation sync could not fully align the requested GitHub control-plane state."
        fallback_to = "manual-reconciliation"

    return emit(
        {
            **refreshed_payload,
            "operation": "sync",
            "result": result,
            "summary": summary,
            "missing_inputs": list(dict.fromkeys(sync_missing + list(refreshed_payload.get("missing_inputs", [])))),
            "fallback_to": fallback_to,
            "applied_actions": executed_actions,
            "skipped_actions": skipped_actions,
            "remaining_findings": remaining_findings,
            "audit": payload,
            "runtime_state": runtime_state,
        }
    )


def handle_review(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "review",
                "operation": args.operation,
                "result": "block",
                "summary": "review command could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
            }
        )

    requested_review_file = args.review_file
    if args.operation == "record" and args.kind == "spec_review" and not requested_review_file:
        requested_review_file = default_spec_review_path(context["item_id"])

    review_record, review_path, review_errors = load_review_record(
        target_root,
        context["item_id"],
        requested_review_file or context["review_entry"],
    )
    inferred_spec_review = review_path == default_spec_review_path(context["item_id"])
    if args.operation == "read":
        missing_inputs = list(review_errors)
        if review_record is None and not review_errors:
            missing_inputs.append(f"missing review artifact: {review_path}")
        result = "pass" if not missing_inputs else "block"
        return emit(
            {
                "command": "review",
                "operation": "read",
                "item": {"id": context["item_id"]},
                "result": result,
                "summary": (
                    "review artifact is readable and can be consumed by merge checkpoint."
                    if result == "pass"
                    else "review artifact is missing or invalid."
                ),
                "missing_inputs": missing_inputs,
                "fallback_to": "build" if missing_inputs else None,
                "review": {"path": review_path, "record": review_record},
            }
        )

    if args.operation == "run":
        flow_operation = "spec-review" if inferred_spec_review else "review"
        review_kind = "spec_review" if inferred_spec_review else implementation_review_kind(context)
        flow_payload = build_review_flow_payload(target_root, args.output, args.item, operation=flow_operation)
        review_surface = flow_payload.get("review") or (flow_payload.get("spec_review") if inferred_spec_review else None)
        if flow_payload["result"] != "pass":
            manual_review = manual_review_payload(
                context=context,
                findings_file=None,
                kind=review_kind,
                review_record_path=review_path,
            )
            return emit(
                {
                    "command": "review",
                    "operation": "run",
                    "item": flow_payload.get("item"),
                    "result": flow_payload["result"],
                    "summary": "default review engine was not started because the Loom review baseline is not ready.",
                    "missing_inputs": flow_payload["missing_inputs"],
                    "fallback_to": flow_payload["fallback_to"],
                    "steps": flow_payload.get("steps", []),
                    "runtime_state": flow_payload.get("runtime_state"),
                    "state_check": flow_payload.get("state_check"),
                    "runtime_evidence": flow_payload.get("runtime_evidence"),
                    "build_checkpoint": flow_payload.get("build_checkpoint"),
                    "review": review_surface,
                    "spec_review": flow_payload.get("spec_review"),
                    "repo_specific_requirements": flow_payload.get("repo_specific_requirements"),
                    "current_checkpoint": flow_payload.get("current_checkpoint"),
                    "engine": {
                        "engine": DEFAULT_REVIEW_ENGINE,
                        "adapter": DEFAULT_REVIEW_ADAPTER,
                        "result": "not_run",
                        "failure_reason": None,
                        "reviewed_head": git_head_sha(target_root) or "unknown-head",
                        "evidence": None,
                    },
                    "manual_review": manual_review,
                }
            )

        build_payload = flow_payload["build_checkpoint"]
        engine_payload = run_default_review_engine(context, build_payload, review_path, review_kind=review_kind)
        review_record_input = engine_payload.get("review_record_input")
        findings_file = (
            review_record_input.get("findings_file")
            if isinstance(review_record_input, dict)
            else None
        )
        manual_review = manual_review_payload(
            context=context,
            findings_file=findings_file if isinstance(findings_file, str) else None,
            kind=review_kind,
            review_record_path=review_path,
        )
        result = engine_payload["result"]
        summary = (
            engine_payload["summary"]
            if result == "pass"
            else "default review engine failed closed; record any formal review conclusion through the single review record."
        )
        return emit(
            {
                "command": "review",
                "operation": "run",
                "item": flow_payload.get("item"),
                "result": result,
                "summary": summary,
                "missing_inputs": engine_payload["missing_inputs"],
                "fallback_to": None if result == "block" else engine_payload["fallback_to"],
                "steps": flow_payload.get("steps", []),
                "runtime_state": flow_payload.get("runtime_state"),
                "state_check": flow_payload.get("state_check"),
                "runtime_evidence": flow_payload.get("runtime_evidence"),
                "build_checkpoint": flow_payload.get("build_checkpoint"),
                "review": review_surface,
                "spec_review": flow_payload.get("spec_review"),
                "repo_specific_requirements": flow_payload.get("repo_specific_requirements"),
                "current_checkpoint": flow_payload.get("current_checkpoint"),
                "engine": engine_payload["engine"],
                "manual_review": manual_review,
                **({"review_record_input": review_record_input} if isinstance(review_record_input, dict) else {}),
            }
        )

    missing_inputs: list[str] = []
    for field in ("decision", "kind", "summary", "reviewer"):
        value = getattr(args, field.replace("-", "_"), None)
        if not isinstance(value, str) or not value.strip():
            missing_inputs.append(field)
    if args.decision == "fallback" and args.fallback_to is None:
        missing_inputs.append("fallback-to")
    if missing_inputs:
        return emit(
            {
        "command": "review",
            "operation": "record",
                "result": "block",
                "summary": "review record command is missing required authored fields.",
                "missing_inputs": missing_inputs,
                "fallback_to": "build",
            }
        )

    if args.findings_file and (args.blocking_issue or args.follow_up):
        return emit(
            {
                "command": "review",
                "operation": "record",
                "result": "block",
                "summary": "review record must not mix `--findings-file` with compatibility finding flags.",
                "missing_inputs": ["choose either `--findings-file` or compatibility finding flags"],
                "fallback_to": "build",
            }
        )

    build_payload = checkpoint_payload("build", context)
    if args.decision == "allow" and build_payload["result"] != "pass":
        missing = list(build_payload["missing_inputs"])
        return emit(
            {
                "command": "review",
                "operation": "record",
                "result": "block",
                "summary": "review cannot be recorded as `allow` before build checkpoint passes.",
                "missing_inputs": missing,
                "fallback_to": build_payload["fallback_to"] or "build",
                "build_checkpoint": build_payload,
            }
        )
    if args.decision == "allow" and args.kind == "spec_review":
        spec_path = formal_spec_path(context)
        if spec_path is None:
            return emit(
                {
                    "command": "review",
                    "operation": "record",
                    "result": "block",
                    "summary": "spec review cannot be recorded as `allow` without a readable formal spec path.",
                    "missing_inputs": ["formal spec path"],
                    "fallback_to": "build",
                    "build_checkpoint": build_payload,
                }
            )
    if args.decision == "allow" and args.kind != "spec_review":
        spec_gate = spec_review_gate_payload(context)
        if spec_gate["result"] != "pass":
            return emit(
                {
                    "command": "review",
                    "operation": "record",
                    "result": "block",
                    "summary": "implementation review cannot be recorded as `allow` before spec review passes.",
                    "missing_inputs": list(spec_gate["missing_inputs"]),
                    "fallback_to": spec_gate["fallback_to"] or "build",
                    "build_checkpoint": build_payload,
                    "spec_review": spec_gate,
                }
            )

    findings: list[dict[str, Any]]
    findings_errors: list[str] = []
    if args.findings_file:
        findings, findings_errors = load_findings_file(target_root, args.findings_file)
        if findings is None:
            findings = []
    else:
        findings = compat_findings_from_lists(
            decision=args.decision,
            blocking_issues=[entry.strip() for entry in args.blocking_issue if entry.strip()],
            follow_ups=[entry.strip() for entry in args.follow_up if entry.strip()],
        )
    if findings_errors:
        return emit(
            {
                "command": "review",
                "operation": "record",
                "result": "block",
                "summary": "review record could not load a valid authoritative findings file.",
                "missing_inputs": findings_errors,
                "fallback_to": "build",
            }
        )

    blocking_issues, follow_ups = compat_lists_from_findings(findings)
    review_payload = {
        "schema_version": "loom-review/v1",
        "item_id": context["item_id"],
        "decision": args.decision,
        "kind": args.kind,
        "summary": args.summary,
        "reviewer": args.reviewer,
        "reviewed_head": git_head_sha(target_root) or "unknown",
        "reviewed_validation_summary": context["latest_validation_summary"],
        "fallback_to": args.fallback_to,
        "findings": findings,
        "blocking_issues": blocking_issues,
        "follow_ups": follow_ups,
        "consumed_inputs": {
            "work_item": str(context["report"]["fact_chain"]["entry_points"]["work_item"]),
            "recovery_entry": str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"]),
            "status_surface": str(context["report"]["fact_chain"]["entry_points"]["status_surface"]),
            "build_checkpoint": build_payload["result"],
            "engine_adapter": args.engine_adapter,
            "engine_evidence": args.engine_evidence,
            "normalized_findings": args.normalized_findings,
        },
    }
    review_abs = target_root / review_path
    review_abs.parent.mkdir(parents=True, exist_ok=True)
    write_json_file(review_abs, review_payload)

    verified_record, _, verified_errors = load_review_record(target_root, context["item_id"], review_path)
    if verified_errors or verified_record is None:
        return emit(
            {
                "command": "review",
                "operation": "record",
                "result": "block",
                "summary": "review artifact was written but could not be re-read cleanly.",
                "missing_inputs": verified_errors or [f"missing review artifact: {review_path}"],
                "fallback_to": "build",
            }
        )

    return emit(
        {
            "command": "review",
            "operation": "record",
            "item": {"id": context["item_id"]},
            "result": "pass",
            "summary": (
                "formal spec review conclusion was recorded and is ready for spec gate consumption."
                if args.kind == "spec_review"
                else "formal review conclusion was recorded and is ready for merge checkpoint consumption."
            ),
            "missing_inputs": [],
            "fallback_to": None,
            "review": {"path": review_path, "record": verified_record},
            "build_checkpoint": {
                "result": build_payload["result"],
                "summary": build_payload["summary"],
            },
        }
    )


def handle_recovery(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "recovery",
                "operation": args.operation,
                "result": "block",
                "summary": "recovery command could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
            }
        )

    updates = {
        "current_checkpoint": args.current_checkpoint,
        "current_stop": args.current_stop,
        "next_step": args.next_step,
        "blockers": args.blockers,
        "latest_validation_summary": args.latest_validation_summary,
        "recovery_boundary": args.recovery_boundary,
        "current_lane": args.current_lane,
    }
    provided = {field: value for field, value in updates.items() if isinstance(value, str) and value.strip()}
    if not provided:
        return emit(
            {
                "command": "recovery",
                "operation": "writeback",
                "result": "block",
                "summary": "recovery writeback requires at least one authored field.",
                "missing_inputs": ["current-stop | next-step | blockers | latest-validation-summary | current-checkpoint | recovery-boundary | current-lane"],
                "fallback_to": "admission",
            }
        )

    status_relative = str(context["report"]["fact_chain"]["entry_points"]["status_surface"])
    runtime_evidence, runtime_errors = read_runtime_evidence(target_root, status_relative)
    if runtime_errors:
        return emit(
            {
                "command": "recovery",
                "operation": "writeback",
                "result": "block",
                "summary": "recovery writeback could not read runtime evidence for status sync.",
                "missing_inputs": runtime_errors,
                "fallback_to": "admission",
            }
        )

    for field_name, value in provided.items():
        if field_name == "current_checkpoint":
            value = normalize_checkpoint(value) if value.strip().lower() == "retired" else value
        update_markdown_bullet(context["recovery_path"], RECOVERY_FIELD_LABELS[field_name], value)

    refreshed, refresh_errors = sync_status_surface(target_root, args.output, runtime_evidence)
    if refresh_errors:
        return emit(
            {
                "command": "recovery",
                "operation": "writeback",
                "result": "block",
                "summary": "recovery writeback updated the recovery entry, but fact-chain verification failed during status sync.",
                "missing_inputs": refresh_errors,
                "fallback_to": "admission",
            }
        )

    return emit(
        {
            "command": "recovery",
            "operation": "writeback",
            "item": {"id": context["item_id"]},
            "result": "pass",
            "summary": "recovery authored fields were updated and the derived status surface was resynchronized.",
            "missing_inputs": [],
            "fallback_to": None,
            "updated_fields": sorted(provided),
            "recovery_entry": str(refreshed["fact_chain"]["entry_points"]["recovery_entry"]),
            "status_surface": str(refreshed["fact_chain"]["entry_points"]["status_surface"]),
        }
    )


def update_active_entry_points(
    target_root: Path,
    output_relative: str,
    *,
    item_id: str,
    work_item: str,
    recovery_entry: str,
    status_surface: str,
) -> None:
    output_path = target_root / output_relative
    payload = load_json_file(output_path)
    fact_chain = payload.get("fact_chain")
    if not isinstance(fact_chain, dict):
        raise RuntimeError("init-result is missing `fact_chain`")
    entry_points = fact_chain.get("entry_points")
    if not isinstance(entry_points, dict):
        raise RuntimeError("init-result.fact_chain is missing `entry_points`")
    entry_points["current_item_id"] = item_id
    entry_points["work_item"] = work_item
    entry_points["recovery_entry"] = recovery_entry
    entry_points["status_surface"] = status_surface
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def handle_work_item(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    output_path = target_root / args.output
    if not output_path.exists():
        return emit(
            {
                "command": "work-item",
                "operation": args.operation,
                "result": "block",
                "summary": "work-item command requires an existing init-result fact-chain locator.",
                "missing_inputs": [f"missing init-result: {args.output}"],
                "fallback_to": "admission",
            }
        )

    work_item_relative = f".loom/work-items/{args.item}.md"
    work_item_path = target_root / work_item_relative
    recovery_relative = args.recovery_entry or f".loom/progress/{args.item}.md"
    recovery_path = target_root / recovery_relative
    review_relative = default_review_path(args.item)
    status_relative = ".loom/status/current.md"
    runtime_evidence: dict[str, dict[str, Any]] | None = None

    if args.operation == "create":
        required_fields = {
            "goal": args.goal,
            "scope": args.scope,
            "execution_path": args.execution_path,
            "workspace_entry": args.workspace_entry,
            "validation_entry": args.validation_entry,
            "closing_condition": args.closing_condition,
        }
        missing = [field for field, value in required_fields.items() if not isinstance(value, str) or not value.strip()]
        if missing:
            return emit(
                {
                    "command": "work-item",
                    "operation": "create",
                    "result": "block",
                    "summary": "work-item create is missing required static fields.",
                    "missing_inputs": missing,
                    "fallback_to": "admission",
                }
            )
        if work_item_path.exists():
            return emit(
                {
                    "command": "work-item",
                    "operation": "create",
                    "result": "block",
                    "summary": "work-item create refused to overwrite an existing work item.",
                    "missing_inputs": [f"work item already exists: {work_item_relative}"],
                    "fallback_to": "admission",
                }
            )

        artifacts = [work_item_relative, recovery_relative, review_relative, status_relative, *args.artifact]
        deduped_artifacts: list[str] = []
        seen: set[str] = set()
        for artifact in artifacts:
            if artifact in seen:
                continue
            seen.add(artifact)
            deduped_artifacts.append(artifact)

        work_item_payload = {
            "item_id": args.item,
            "goal": args.goal,
            "scope": args.scope,
            "execution_path": args.execution_path,
            "workspace_entry": args.workspace_entry,
            "recovery_entry": recovery_relative,
            "review_entry": review_relative,
            "validation_entry": args.validation_entry,
            "closing_condition": args.closing_condition,
            "associated_artifacts": deduped_artifacts,
        }
        work_item_path.parent.mkdir(parents=True, exist_ok=True)
        work_item_path.write_text(render_work_item(work_item_payload), encoding="utf-8")
        review_path = target_root / review_relative
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            json.dumps(
                {
                    "schema_version": "loom-review/v1",
                    "item_id": args.item,
                    "decision": "fallback",
                    "kind": "general_review",
                    "summary": "Formal review has not been recorded yet.",
                    "reviewer": "not yet assigned",
                    "reviewed_head": git_head_sha(target_root) or "unknown",
                    "reviewed_validation_summary": "No validation recorded yet.",
                    "fallback_to": "admission",
                    "findings": [
                        {
                            "id": "scaffolded-block-1",
                            "summary": "Review artifact scaffolded but not yet concluded.",
                            "severity": "block",
                            "rebuttal": None,
                            "disposition": {
                                "status": "rejected",
                                "summary": "Scaffold placeholder must be replaced by a real formal review conclusion.",
                            },
                        },
                        {
                            "id": "scaffolded-warn-1",
                            "summary": "Record a real review before asking merge checkpoint to consume it.",
                            "severity": "warn",
                            "rebuttal": None,
                            "disposition": {
                                "status": "deferred",
                                "summary": "This follow-up stays open until a real review is recorded.",
                            },
                        },
                    ],
                    "blocking_issues": ["Review artifact scaffolded but not yet concluded."],
                    "follow_ups": ["Record a real review before asking merge checkpoint to consume it."],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        if args.init_recovery:
            recovery_path.parent.mkdir(parents=True, exist_ok=True)
            recovery_path.write_text(
                render_recovery_entry(
                    args.item,
                    {
                        "current_checkpoint": "admission checkpoint",
                        "current_stop": "Work item scaffolded and waiting for the first execution pass.",
                        "next_step": "Write the first recovery update for this work item.",
                        "blockers": "None recorded.",
                        "latest_validation_summary": "No validation recorded yet.",
                        "recovery_boundary": f"Work item scaffolded at `{work_item_relative}`.",
                        "current_lane": "not yet assigned",
                    },
                ),
                encoding="utf-8",
            )

    else:
        if not work_item_path.exists():
            return emit(
                {
                    "command": "work-item",
                    "operation": "update",
                    "result": "block",
                    "summary": "work-item update requires an existing work item file.",
                    "missing_inputs": [f"missing work item: {work_item_relative}"],
                    "fallback_to": "admission",
                }
            )
        parsed_work_item, parse_errors = parse_work_item(work_item_path, target_root)
        if parse_errors:
            return emit(
                {
                    "command": "work-item",
                    "operation": "update",
                    "result": "block",
                    "summary": "work-item update could not parse the current work item.",
                    "missing_inputs": parse_errors,
                    "fallback_to": "admission",
                }
            )
        work_item_payload = {
            "item_id": args.item,
            "goal": args.goal or str(parsed_work_item["goal"]),
            "scope": args.scope or str(parsed_work_item["scope"]),
            "execution_path": args.execution_path or str(parsed_work_item["execution_path"]),
            "workspace_entry": args.workspace_entry or str(parsed_work_item["workspace_entry"]),
            "recovery_entry": args.recovery_entry or str(parsed_work_item["recovery_entry"]),
            "review_entry": str(parsed_work_item["review_entry"]),
            "validation_entry": args.validation_entry or str(parsed_work_item["validation_entry"]),
            "closing_condition": args.closing_condition or str(parsed_work_item["closing_condition"]),
            "associated_artifacts": list(parsed_work_item["associated_artifacts"]),
        }
        for artifact in args.add_artifact:
            if artifact not in work_item_payload["associated_artifacts"]:
                work_item_payload["associated_artifacts"].append(artifact)
        for artifact in args.remove_artifact:
            work_item_payload["associated_artifacts"] = [
                entry for entry in work_item_payload["associated_artifacts"] if entry != artifact
            ]
        recovery_relative = work_item_payload["recovery_entry"]
        recovery_path = target_root / recovery_relative
        work_item_path.write_text(render_work_item(work_item_payload), encoding="utf-8")

    if args.activate:
        if not recovery_path.exists():
            return emit(
                {
                    "command": "work-item",
                    "operation": args.operation,
                    "result": "block",
                    "summary": "work-item activation requires an existing recovery entry.",
                    "missing_inputs": [f"missing recovery entry: {recovery_relative}"],
                    "fallback_to": "admission",
                }
            )
        runtime_evidence, runtime_errors = read_runtime_evidence(target_root, status_relative)
        if runtime_errors:
            return emit(
                {
                    "command": "work-item",
                    "operation": args.operation,
                    "result": "block",
                    "summary": "work-item activation could not read runtime evidence from the current status surface.",
                    "missing_inputs": runtime_errors,
                    "fallback_to": "admission",
                }
            )
        update_active_entry_points(
            target_root,
            args.output,
            item_id=args.item,
            work_item=work_item_relative,
            recovery_entry=recovery_relative,
            status_surface=status_relative,
        )
        _, sync_errors = sync_status_surface(target_root, args.output, runtime_evidence)
        if sync_errors:
            return emit(
                {
                    "command": "work-item",
                    "operation": args.operation,
                    "result": "block",
                    "summary": "work-item activation updated the locator truth, but fact-chain sync failed.",
                    "missing_inputs": sync_errors,
                    "fallback_to": "admission",
                }
            )
    else:
        init_result = load_json_file(output_path)
        fact_chain = init_result.get("fact_chain")
        entry_points = fact_chain.get("entry_points") if isinstance(fact_chain, dict) else None
        if isinstance(entry_points, dict) and entry_points.get("current_item_id") == args.item:
            runtime_evidence, runtime_errors = read_runtime_evidence(target_root, status_relative)
            if runtime_errors:
                return emit(
                    {
                        "command": "work-item",
                        "operation": args.operation,
                        "result": "block",
                        "summary": "work-item authoring updated the active item, but runtime evidence could not be read for status sync.",
                        "missing_inputs": runtime_errors,
                        "fallback_to": "admission",
                    }
                )
            _, sync_errors = sync_status_surface(target_root, args.output, runtime_evidence)
            if sync_errors:
                return emit(
                    {
                        "command": "work-item",
                        "operation": args.operation,
                        "result": "block",
                        "summary": "work-item authoring updated the active item, but fact-chain sync failed.",
                        "missing_inputs": sync_errors,
                        "fallback_to": "admission",
                    }
                )

    context, context_errors = load_context(target_root, args.output, args.item if args.activate else None)
    payload: dict[str, Any] = {
        "command": "work-item",
        "operation": args.operation,
        "result": "pass",
        "summary": (
            "work item was authored successfully."
            if not args.activate
            else "work item was authored and activated as the current Loom fact chain entry."
        ),
        "missing_inputs": [],
        "fallback_to": None,
        "work_item": {
            "id": args.item,
            "path": work_item_relative,
            "recovery_entry": recovery_relative,
            "review_entry": review_relative if args.operation == "create" else work_item_payload["review_entry"],
            "activated": args.activate,
        },
    }
    if context_errors:
        payload["result"] = "block"
        payload["summary"] = "work-item authoring completed, but the fact chain no longer reads cleanly."
        payload["missing_inputs"] = context_errors
        payload["fallback_to"] = "admission"
    else:
        payload["current_fact_chain"] = {
            "current_item_id": context["item_id"],
            "work_item": str(context["report"]["fact_chain"]["entry_points"]["work_item"]),
            "recovery_entry": str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"]),
            "status_surface": str(context["report"]["fact_chain"]["entry_points"]["status_surface"]),
        }
    return emit(payload)


def handle_flow(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    steps: list[dict[str, Any]] = [
        {
            "name": "runtime-state",
            "result": runtime_state["result"],
            "summary": runtime_state["summary"],
            "missing_inputs": runtime_state["missing_inputs"],
            "fallback_to": runtime_state["fallback_to"],
        }
    ]
    if runtime_state["result"] != "pass":
        return emit(
            {
                "command": "flow",
                "operation": args.operation,
                "result": "block",
                "summary": "flow command is blocked because the Loom runtime state is inconsistent.",
                "missing_inputs": runtime_state["missing_inputs"],
                "fallback_to": runtime_state["fallback_to"],
                "steps": steps,
                "runtime_state": runtime_state,
            }
        )

    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "flow",
                "operation": args.operation,
                "result": "block",
                "summary": "flow command could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
                "steps": steps,
                "runtime_state": runtime_state,
            }
        )

    if args.operation not in {"pre-review", "review", "spec-review", "resume", "handoff", "merge-ready"}:
        return emit(
            {
                "command": "flow",
                "operation": args.operation,
                "result": "block",
                "summary": f"unsupported flow operation: {args.operation}",
                "missing_inputs": [f"unsupported operation: {args.operation}"],
                "fallback_to": None,
                "steps": steps,
                "runtime_state": runtime_state,
            }
        )
    if args.operation in {"review", "spec-review"}:
        return emit(build_review_flow_payload(target_root, args.output, args.item, operation=args.operation))

    steps.append(
        {
            "name": "fact-chain",
            "result": "pass",
            "summary": "fact chain is readable from a single entry.",
            "missing_inputs": [],
            "fallback_to": None,
        }
    )

    state_payload = state_check_payload(context)
    steps.append(
        {
            "name": "state-check",
            "result": state_payload["result"],
            "summary": state_payload["summary"],
            "missing_inputs": state_payload["missing_inputs"],
            "fallback_to": state_payload["fallback_to"],
        }
    )

    review_payload: dict[str, Any] | None = None
    governance_surface = build_governance_surface(target_root)
    upgrade_path = maturity_upgrade_path(governance_surface, target_root)
    repo_interface = governance_surface.get("repo_interface")
    repo_specific_requirements: dict[str, Any] | None = None

    if args.operation in {"resume", "handoff"}:
        locate_payload = base_workspace_payload(context, "locate")
        locate_result = "pass" if not locate_payload["purity"]["hard_failures"] else "block"
        locate_step = {
            "name": "workspace-locate",
            "result": locate_result,
            "summary": (
                "workspace is location-resolved and execution-ready."
                if locate_result == "pass"
                else "workspace is location-resolved but not execution-ready."
            ),
            "missing_inputs": list(locate_payload["purity"]["hard_failures"]),
            "fallback_to": "admission" if locate_payload["purity"]["hard_failures"] else None,
        }
        steps.append(locate_step)
    else:
        runtime_fields, runtime_missing = runtime_evidence_from_report(context["report"])
        runtime_result = "pass" if not runtime_missing else "block"
        steps.append(
            {
                "name": "runtime-evidence",
                "result": runtime_result,
                "summary": (
                    "runtime evidence entries are readable."
                    if runtime_result == "pass"
                    else "runtime evidence entries are incomplete or inconsistent."
                ),
                "missing_inputs": runtime_missing,
                "fallback_to": "admission" if runtime_missing else None,
                "runtime_evidence": runtime_fields,
            }
        )
        if args.operation == "merge-ready":
            build_payload = checkpoint_payload("build", context)
            merge_payload = checkpoint_payload("merge", context)
            repo_specific_requirements = repo_specific_requirements_payload(
                repo_interface,
                target_root=target_root,
                surface="merge_ready",
            )
            steps.extend(
                [
                    {
                        "name": "checkpoint-build",
                        "result": build_payload["result"],
                        "summary": build_payload["summary"],
                        "missing_inputs": build_payload["missing_inputs"],
                        "fallback_to": build_payload["fallback_to"],
                    },
                    {
                        "name": "checkpoint-merge",
                        "result": merge_payload["result"],
                        "summary": merge_payload["summary"],
                        "missing_inputs": merge_payload["missing_inputs"],
                        "fallback_to": merge_payload["fallback_to"],
                    },
                ]
            )
        elif args.operation == "review":
            build_payload = checkpoint_payload("build", context)
            repo_specific_requirements = repo_specific_requirements_payload(
                repo_interface,
                target_root=target_root,
                surface="review",
            )
            review_record, review_path, review_errors = load_review_record(
                target_root,
                context["item_id"],
                context["review_entry"],
            )
            review_step = {
                "name": "review-entry",
                "result": "pass" if review_record and not review_errors else "block",
                "summary": (
                    "formal review artifact is readable."
                    if review_record and not review_errors
                    else "formal review artifact is missing or invalid."
                ),
                "missing_inputs": review_errors or ([] if review_record else [f"missing review artifact: {review_path}"]),
                "fallback_to": "build" if (review_errors or review_record is None) else None,
            }
            steps.extend(
                [
                    {
                        "name": "checkpoint-build",
                        "result": build_payload["result"],
                        "summary": build_payload["summary"],
                        "missing_inputs": build_payload["missing_inputs"],
                        "fallback_to": build_payload["fallback_to"],
                    },
                    review_step,
                ]
            )
            review_payload = {
                "path": review_path,
                "record": review_record,
            }
        else:
            admission_payload = checkpoint_payload("admission", context)
            locate_payload = base_workspace_payload(context, "locate")
            locate_result = "pass" if not locate_payload["purity"]["hard_failures"] else "block"
            locate_step = {
                "name": "workspace-locate",
                "result": locate_result,
                "summary": (
                    "workspace is location-resolved and execution-ready."
                    if locate_result == "pass"
                    else "workspace is location-resolved but not execution-ready."
                ),
                "missing_inputs": list(locate_payload["purity"]["hard_failures"]),
                "fallback_to": "admission" if locate_payload["purity"]["hard_failures"] else None,
            }
            steps.append(
                {
                    "name": "checkpoint-admission",
                    "result": admission_payload["result"],
                    "summary": admission_payload["summary"],
                    "missing_inputs": admission_payload["missing_inputs"],
                    "fallback_to": admission_payload["fallback_to"],
                }
            )
            steps.append(locate_step)

    result = "pass"
    fallback_to: str | None = None
    for step in steps:
        step_result = step["result"]
        if step_result == "fallback":
            result = "fallback"
            fallback_to = step.get("fallback_to") or "admission"
            break
        if step_result == "block" and result == "pass":
            result = "block"
            fallback_to = step.get("fallback_to")
    if result != "block" and isinstance(repo_specific_requirements, dict) and repo_specific_requirements["result"] == "block":
        result = "block"
        fallback_to = fallback_to or repo_specific_requirements["fallback_to"]

    if args.operation == "resume":
        summary = (
            "resume flow rebuilt the current execution context and next step."
            if result == "pass"
            else "resume flow rebuilt context but found blocking signals before execution can continue."
        )
    elif args.operation == "handoff":
        summary = (
            "handoff flow produced the minimum writeback checklist and locator set."
            if result == "pass"
            else "handoff flow produced the minimum writeback checklist, but blocking signals remain before transfer."
        )
    elif args.operation == "merge-ready":
        if isinstance(repo_specific_requirements, dict) and result == "block" and repo_specific_requirements["result"] == "block":
            summary = "merge-ready flow found companion-declared blocking requirements that Loom core does not satisfy on its own."
        else:
            summary = (
                "merge-ready flow found the required evidence and checkpoint state for host merge."
                if result == "pass"
                else "merge-ready flow found fallback or blocking signals before host merge."
            )
    elif args.operation == "review":
        if isinstance(repo_specific_requirements, dict) and result == "block" and repo_specific_requirements["result"] == "block":
            summary = "review flow exposed companion-declared blocking requirements instead of pretending Loom core already covers them."
        else:
            summary = (
                "review flow prepared the semantic review context and exposed the formal review artifact."
                if result == "pass"
                else "review flow found missing review material or earlier blocking signals."
            )
    else:
        summary = (
            "pre-review flow is ready to proceed."
            if result == "pass"
            else "pre-review flow found blocking signals before review."
        )
    missing_inputs: list[str] = []
    for step in steps:
        if step["result"] in {"block", "fallback"}:
            for message in step.get("missing_inputs", []):
                if message not in missing_inputs:
                    missing_inputs.append(message)
    if isinstance(repo_specific_requirements, dict) and repo_specific_requirements["result"] == "block":
        for message in repo_specific_requirements.get("missing_inputs", []):
            if message not in missing_inputs:
                missing_inputs.append(message)
    if args.operation == "resume":
        for message in governance_surface.get("missing_inputs", []):
            if message not in missing_inputs:
                missing_inputs.append(message)
        for message in upgrade_path.get("missing_inputs", []):
            if message not in missing_inputs:
                missing_inputs.append(message)

    return emit(
        {
            "command": "flow",
            "operation": args.operation,
            "item": {
                "id": context["item_id"],
                "goal": context["goal"],
                "scope": context["scope"],
                "execution_path": context["execution_path"],
            },
            "result": result,
            "summary": summary,
            "missing_inputs": missing_inputs,
            "fallback_to": fallback_to,
            "steps": steps,
            "runtime_state": runtime_state,
            **({"governance_surface": governance_surface} if args.operation == "resume" else {}),
            **({"maturity_upgrade_path": upgrade_path} if args.operation == "resume" else {}),
            **(
                {
                    "workspace": {
                        "entry": locate_payload["workspace"]["entry"],
                        "path": locate_payload["workspace"]["path"],
                        "exists": locate_payload["workspace"]["exists"],
                    },
                    "checkpoint": {
                        "raw": context["current_checkpoint_raw"],
                        "normalized": context["current_checkpoint"],
                    },
                    "state_check": {
                        "result": state_payload["result"],
                        "summary": state_payload["summary"],
                        "missing_inputs": state_payload["missing_inputs"],
                        "fallback_to": state_payload["fallback_to"],
                        "checks": state_payload["checks"],
                    },
                }
                if args.operation in {"resume", "handoff"}
                else {}
            ),
            **(
                {
                    "recovery": {
                        "path": locate_payload["recovery"]["path"],
                        "current_stop": locate_payload["recovery"]["current_stop"],
                        "next_step": context["next_step"],
                        "blockers": context["blockers"],
                        "latest_validation_summary": context["latest_validation_summary"],
                    },
                }
                if args.operation == "resume"
                else {}
            ),
            **(
                {
                    "recovery_entry": str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"]),
                    "status_surface": str(context["report"]["fact_chain"]["entry_points"]["status_surface"]),
                    "current_stop": context["current_stop"],
                    "next_step": context["next_step"],
                    "blockers": context["blockers"],
                    "latest_validation_summary": context["latest_validation_summary"],
                    "fallback_target": fallback_to,
                    "writeback_fields": [
                        "current_stop",
                        "next_step",
                        "blockers",
                        "latest_validation_summary",
                    ],
                }
                if args.operation == "handoff"
                else {}
            ),
            **(
                {
                    "state_check": {
                        "result": state_payload["result"],
                        "summary": state_payload["summary"],
                        "missing_inputs": state_payload["missing_inputs"],
                        "fallback_to": state_payload["fallback_to"],
                        "checks": state_payload["checks"],
                    },
                    "runtime_evidence": runtime_fields,
                    "build_checkpoint": {
                        "result": build_payload["result"],
                        "summary": build_payload["summary"],
                        "missing_inputs": build_payload["missing_inputs"],
                        "fallback_to": build_payload["fallback_to"],
                    },
                    "review": review_payload,
                    "repo_specific_requirements": repo_specific_requirements,
                    "current_checkpoint": {
                        "raw": context["current_checkpoint_raw"],
                        "normalized": context["current_checkpoint"],
                    },
                }
                if args.operation == "review"
                else {}
            ),
            **(
                {
                    "state_check": {
                        "result": state_payload["result"],
                        "summary": state_payload["summary"],
                        "missing_inputs": state_payload["missing_inputs"],
                        "fallback_to": state_payload["fallback_to"],
                        "checks": state_payload["checks"],
                    },
                    "runtime_evidence": runtime_fields,
                    "build_checkpoint": {
                        "result": build_payload["result"],
                        "summary": build_payload["summary"],
                        "missing_inputs": build_payload["missing_inputs"],
                        "fallback_to": build_payload["fallback_to"],
                    },
                    "merge_checkpoint": {
                        "result": merge_payload["result"],
                        "summary": merge_payload["summary"],
                        "missing_inputs": merge_payload["missing_inputs"],
                        "fallback_to": merge_payload["fallback_to"],
                        "pr_template": merge_payload.get("pr_template"),
                    },
                    "spec_review": merge_payload.get("spec_review"),
                    "current_checkpoint": {
                        "raw": context["current_checkpoint_raw"],
                        "normalized": context["current_checkpoint"],
                    },
                    "current_lane": context["current_lane"],
                    "latest_validation_summary": context["latest_validation_summary"],
                    "repo_specific_requirements": repo_specific_requirements,
                }
                if args.operation == "merge-ready"
                else {}
            ),
        }
    )


def handle_shadow_parity(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            runtime_state_block_payload(
                command="shadow-parity",
                runtime_state=runtime_state,
                summary="shadow parity is blocked because the Loom runtime state is inconsistent.",
            )
        )

    governance_surface = build_governance_surface(target_root)
    repo_interop = governance_surface.get("repo_interop")
    requested_surfaces = SHADOW_PARITY_SURFACES if args.surface == "all" else (args.surface,)
    mode = "blocking" if args.blocking else args.mode
    reports = [
        shadow_parity_report(
            repo_interop,
            target_root=target_root,
            surface=surface,
        )
        for surface in requested_surfaces
    ]

    all_match = bool(reports) and all(report["result"] == "match" for report in reports)
    blocking_reports = [report for report in reports if report.get("result") != "match"]
    if mode == "blocking":
        result = "pass" if all_match else "block"
        for report in blocking_reports:
            report["blocking"] = True
    else:
        result = "pass" if all_match else "warn"
    if result == "pass":
        summary = "shadow parity matches across all requested surfaces."
    elif mode == "blocking":
        summary = "shadow parity blocking mode found mismatch or unreadable surfaces."
    else:
        summaries = {report["result"] for report in reports}
        if "mismatch" in summaries:
            summary = "shadow parity found mismatches between Loom and repo-native governance surfaces."
        else:
            summary = "shadow parity could not fully read the declared governance surfaces."

    missing_inputs: list[str] = []
    for report in reports:
        for message in report.get("missing_inputs", []):
            if message not in missing_inputs:
                missing_inputs.append(message)

    return emit(
        {
            "command": "shadow-parity",
            "mode": mode,
            "blocking": mode == "blocking",
            "result": result,
            "summary": summary,
            "missing_inputs": missing_inputs,
            "fallback_to": "manual-reconciliation" if result == "block" else None,
            "runtime_state": runtime_state,
            "governance_surface": governance_surface,
            "reports": reports,
        }
    )


def handle_runtime_parity(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    return emit(
        runtime_parity_payload(
            target_root=target_root,
            output_relative=args.output,
            expected_item=args.item,
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "fact-chain":
        return handle_fact_chain(args)
    if args.command == "runtime-state":
        return handle_runtime_state(args)
    if args.command == "runtime-evidence":
        return handle_runtime_evidence(args)
    if args.command == "state-check":
        return handle_state_check(args)
    if args.command == "review":
        return handle_review(args)
    if args.command == "recovery":
        return handle_recovery(args)
    if args.command == "work-item":
        return handle_work_item(args)
    if args.command == "host-lifecycle":
        return handle_host_lifecycle(args)
    if args.command == "closeout":
        return handle_closeout(args)
    if args.command == "reconciliation":
        return handle_reconciliation(args)
    if args.command == "shadow-parity":
        return handle_shadow_parity(args)
    if args.command == "runtime-parity":
        return handle_runtime_parity(args)
    if args.command == "governance-profile":
        return handle_governance_profile(args)
    if args.command == "flow":
        return handle_flow(args)
    if args.command == "checkpoint":
        return handle_checkpoint(args)
    if args.command == "workspace":
        return handle_workspace(args)
    return handle_purity(args)


if __name__ == "__main__":
    raise SystemExit(main())
