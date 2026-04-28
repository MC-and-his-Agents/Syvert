#!/usr/bin/env python3
"""Unified Loom status read surface for item, spec/review gates, and merge readiness."""

from __future__ import annotations

import argparse
from pathlib import Path

from governance_surface import build_governance_surface
from loom_flow import (
    checkpoint_payload,
    closeout_payload,
    detect_github_repo,
    emit,
    github_issue_payload,
    github_pr_payload,
    implementation_review_status_payload,
    load_context,
    runtime_state_payload,
    spec_review_gate_payload,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read unified Loom item/spec/review/merge status.")
    parser.add_argument("--target", required=True, help="Target repository root")
    parser.add_argument("--item", help="Expected current item id")
    parser.add_argument(
        "--output",
        default=".loom/bootstrap/init-result.json",
        help="Init-result path relative to the target root",
    )
    parser.add_argument("--issue", type=int, help="Optional GitHub issue number to include")
    parser.add_argument("--pr", type=int, help="Optional GitHub pull request number to include")
    parser.add_argument("--project", type=int, help="Optional GitHub project number to include in closeout")
    parser.add_argument("--owner", help="GitHub owner; auto-detected from origin when omitted")
    parser.add_argument("--repo", dest="repo_name", help="GitHub repository name; auto-detected from origin when omitted")
    return parser.parse_args(argv)


def github_status_payload(
    root: Path,
    *,
    issue_number: int | None,
    pr_number: int | None,
    owner: str | None,
    repo_name: str | None,
) -> tuple[dict[str, object], list[str]]:
    detected_owner, detected_repo = detect_github_repo(root)
    owner = owner or detected_owner
    repo_name = repo_name or detected_repo
    payload: dict[str, object] = {
        "repository": f"{owner}/{repo_name}" if owner and repo_name else None,
        "issue": None,
        "pr": None,
    }
    errors: list[str] = []
    if not owner or not repo_name:
        if issue_number is not None or pr_number is not None:
            errors.append("GitHub repository could not be detected from origin")
        return payload, errors

    if issue_number is not None:
        issue_payload, issue_errors = github_issue_payload(root, owner, repo_name, issue_number)
        if issue_errors:
            errors.extend([f"issue #{issue_number}: {message}" for message in issue_errors])
        else:
            payload["issue"] = issue_payload
    if pr_number is not None:
        pr_payload, pr_errors = github_pr_payload(root, owner, repo_name, pr_number)
        if pr_errors:
            errors.extend([f"pr #{pr_number}: {message}" for message in pr_errors])
        else:
            payload["pr"] = pr_payload
    return payload, errors


def gate_status(name: str, payload: dict[str, object] | None, *, required: bool = True) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {
            "name": name,
            "result": "block" if required else "not_applicable",
            "classification": "gate_failure" if required else None,
            "missing_inputs": [name] if required else [],
        }
    result = payload.get("result")
    missing_inputs = payload.get("missing_inputs")
    missing = missing_inputs if isinstance(missing_inputs, list) else []
    classification = None
    if result in {"block", "fallback"}:
        classification = "gate_failure"
        if any("head" in str(message).lower() for message in missing):
            classification = "head_drift"
        elif any("stale" in str(message).lower() for message in missing):
            classification = "review_stale" if name != "spec_gate" else "spec_stale"
    return {
        "name": name,
        "result": result if isinstance(result, str) else "block",
        "classification": classification,
        "missing_inputs": missing,
        "fallback_to": payload.get("fallback_to"),
    }


def governance_control_status(
    *,
    governance_surface: dict[str, object],
    spec_review: dict[str, object],
    review: dict[str, object],
    merge_ready: dict[str, object],
    github_status: dict[str, object],
    github_errors: list[str],
) -> dict[str, object]:
    control_plane = governance_surface.get("governance_control_plane")
    if not isinstance(control_plane, dict):
        return {
            "schema_version": "loom-governance-status/v2",
            "result": "block",
            "current_gate": "status_surface",
            "classifications": ["gate_failure"],
            "missing_inputs": ["governance_control_plane"],
        }

    gates = [
        {
            "name": "work_item_admission",
            "result": "pass",
            "classification": None,
            "missing_inputs": [],
            "fallback_to": "admission",
        },
        gate_status("spec_gate", spec_review),
        gate_status("build_gate", merge_ready),
        gate_status("review_gate", review),
        gate_status("merge_gate", merge_ready),
        gate_status("github_controlled_merge", None, required=False),
    ]
    if github_errors:
        gates[-1] = {
            "name": "github_controlled_merge",
            "result": "block",
            "classification": "host_signal_drift",
            "missing_inputs": github_errors,
            "fallback_to": "merge",
        }
    host_binding = control_plane.get("host_binding")
    if isinstance(host_binding, dict) and host_binding.get("result") == "block":
        existing_missing = gates[-1].get("missing_inputs", [])
        merged_missing = list(existing_missing) if isinstance(existing_missing, list) else []
        for message in host_binding.get("missing_inputs", []):
            if message not in merged_missing:
                merged_missing.append(message)
        gates[-1] = {
            "name": "github_controlled_merge",
            "result": "block",
            "classification": "host_signal_drift",
            "missing_inputs": merged_missing,
            "fallback_to": "merge",
        }

    blocking = [gate for gate in gates if gate.get("result") in {"block", "fallback"}]
    classifications = [
        str(gate["classification"])
        for gate in blocking
        if isinstance(gate.get("classification"), str)
    ]
    current_gate = blocking[0]["name"] if blocking else "closeout"
    missing_inputs: list[object] = []
    for gate in blocking:
        for message in gate.get("missing_inputs", []):
            if message not in missing_inputs:
                missing_inputs.append(message)
    pr_payload = github_status.get("pr") if isinstance(github_status, dict) else None
    head_binding = {
        "status": "present" if isinstance(pr_payload, dict) and pr_payload.get("headRefName") else "host-managed",
        "head_ref": pr_payload.get("headRefName") if isinstance(pr_payload, dict) else None,
        "base_ref": pr_payload.get("baseRefName") if isinstance(pr_payload, dict) else None,
    }
    return {
        "schema_version": "loom-governance-status/v2",
        "result": "pass" if not blocking else "block",
        "current_gate": current_gate,
        "classifications": list(dict.fromkeys(classifications)),
        "missing_inputs": missing_inputs,
        "head_binding": head_binding,
        "gate_chain": gates,
        "maturity": control_plane.get("maturity"),
    }


def closeout_status_payload(
    *,
    github_status: dict[str, object],
    github_errors: list[str],
) -> dict[str, object]:
    issue = github_status.get("issue")
    pr = github_status.get("pr")
    if issue is None and pr is None and not github_errors:
        return {
            "result": "not_applicable",
            "summary": "closeout is not evaluated because no host issue or PR was requested.",
            "reconciliation": {
                "result": "not_applicable",
                "findings": [],
            },
            "missing_inputs": [],
            "fallback_to": None,
        }
    missing_inputs: list[str] = []
    findings: list[dict[str, object]] = []
    if github_errors:
        missing_inputs.extend(github_errors)
        findings.append(
            {
                "category": "drift",
                "kind": "host_signal_drift",
                "severity": "block",
                "subject": "github",
                "why_blocking": "GitHub host signals could not be read for closeout.",
                "fallback_to": "manual-reconciliation",
                "evidence": github_errors,
            }
        )
    if isinstance(pr, dict) and pr.get("state") != "MERGED":
        missing_inputs.append("pr is not merged")
        findings.append(
            {
                "category": "gate_failure",
                "kind": "missing_prerequisite_gate",
                "severity": "block",
                "subject": f"pr #{pr.get('number')}",
                "why_blocking": "closeout requires a merged implementation PR.",
                "fallback_to": "merge",
                "evidence": {"pr_state": pr.get("state")},
            }
        )
    if isinstance(issue, dict) and isinstance(pr, dict) and issue.get("state") == "OPEN" and pr.get("state") == "MERGED":
        missing_inputs.append("issue is absorbed but open")
        findings.append(
            {
                "category": "drift",
                "kind": "absorbed_but_open",
                "severity": "block",
                "subject": f"issue #{issue.get('number')}",
                "why_blocking": "merged implementation appears absorbed but the issue is still open.",
                "fallback_to": "reconciliation-sync",
                "evidence": {"issue_state": issue.get("state"), "pr_state": pr.get("state")},
            }
        )
    result = "pass" if not missing_inputs else "block"
    reconciliation_result = "pass" if result == "pass" else "fix-needed"
    return {
        "result": result,
        "summary": (
            "closeout host signals are consistent for the requested issue/PR."
            if result == "pass"
            else "closeout host signals require reconciliation before closeout can pass."
        ),
        "reconciliation": {
            "result": reconciliation_result,
            "findings": findings,
        },
        "missing_inputs": missing_inputs,
        "fallback_to": None if result == "pass" else "reconciliation-sync",
    }


def repository_parts(github_status: dict[str, object], owner: str | None, repo_name: str | None) -> tuple[str | None, str | None]:
    if owner and repo_name:
        return owner, repo_name
    repository = github_status.get("repository")
    if isinstance(repository, str) and "/" in repository:
        detected_owner, detected_repo = repository.split("/", 1)
        return owner or detected_owner, repo_name or detected_repo
    return owner, repo_name


def full_closeout_status_payload(
    root: Path,
    *,
    issue_number: int | None,
    pr_number: int | None,
    project_number: int | None,
    owner: str | None,
    repo_name: str | None,
    github_status: dict[str, object],
    github_errors: list[str],
) -> dict[str, object]:
    if issue_number is None and pr_number is None and project_number is None:
        return closeout_status_payload(github_status=github_status, github_errors=github_errors)

    owner, repo_name = repository_parts(github_status, owner, repo_name)
    if not owner or not repo_name:
        return {
            "result": "block",
            "summary": "closeout is blocked because the GitHub repository could not be detected.",
            "reconciliation": {
                "result": "block",
                "findings": [
                    {
                        "category": "gate_failure",
                        "kind": "missing_repository",
                        "severity": "block",
                        "subject": "github repository",
                        "why_blocking": "closeout requires a readable GitHub repository binding.",
                        "fallback_to": "manual-reconciliation",
                        "evidence": github_errors,
                    }
                ],
            },
            "missing_inputs": ["github repository"],
            "fallback_to": "manual-reconciliation",
        }

    payload, errors = closeout_payload(
        target_root=root,
        issue_number=issue_number,
        pr_number=pr_number,
        project_number=project_number,
        owner=owner,
        repo_name=repo_name,
        skip_gate=False,
    )
    if errors:
        return {
            "result": "block",
            "summary": "closeout is blocked because the closeout/reconciliation gate could not complete.",
            "reconciliation": {
                "result": "block",
                "findings": [
                    {
                        "category": "gate_failure",
                        "kind": "closeout_gate_unreadable",
                        "severity": "block",
                        "subject": "closeout",
                        "why_blocking": "status closeout must consume the same fail-closed closeout gate used by Loom flow.",
                        "fallback_to": "manual-reconciliation",
                        "evidence": errors,
                    }
                ],
            },
            "missing_inputs": errors,
            "fallback_to": "manual-reconciliation",
        }

    reconciliation = payload.get("reconciliation")
    if not isinstance(reconciliation, dict):
        reconciliation = {"result": "not_applicable", "findings": []}
    return {
        "result": payload.get("result", "block"),
        "summary": payload.get("summary", "closeout consumed the full closeout/reconciliation gate."),
        "reconciliation": reconciliation,
        "missing_inputs": payload.get("missing_inputs", []),
        "fallback_to": payload.get("fallback_to"),
        "gate": payload.get("gate"),
        "issue": payload.get("issue"),
        "pr": payload.get("pr"),
        "project": payload.get("project"),
        "repo_specific_requirements": payload.get("repo_specific_requirements"),
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target_root = Path(args.target).expanduser().resolve()
    runtime_state = runtime_state_payload(target_root)
    if runtime_state["result"] != "pass":
        return emit(
            {
                "command": "status",
                "result": "block",
                "summary": "status is blocked because the Loom runtime state is inconsistent.",
                "missing_inputs": runtime_state["missing_inputs"],
                "fallback_to": runtime_state["fallback_to"],
                "runtime_state": runtime_state,
            }
        )

    context, errors = load_context(target_root, args.output, args.item)
    if errors:
        return emit(
            {
                "command": "status",
                "result": "block",
                "summary": "status could not read a valid Loom fact chain.",
                "missing_inputs": [f"fact-chain: {message}" for message in errors],
                "fallback_to": "admission",
                "runtime_state": runtime_state,
            }
        )

    spec_review = spec_review_gate_payload(context)
    review = implementation_review_status_payload(context)
    merge_ready = checkpoint_payload("merge", context)
    governance_surface = build_governance_surface(target_root)
    github_status, github_errors = github_status_payload(
        target_root,
        issue_number=args.issue,
        pr_number=args.pr,
        owner=args.owner,
        repo_name=args.repo_name,
    )
    control_status = governance_control_status(
        governance_surface=governance_surface,
        spec_review=spec_review,
        review=review,
        merge_ready=merge_ready,
        github_status=github_status,
        github_errors=github_errors,
    )
    closeout = full_closeout_status_payload(
        target_root,
        issue_number=args.issue,
        pr_number=args.pr,
        project_number=args.project,
        owner=args.owner,
        repo_name=args.repo_name,
        github_status=github_status,
        github_errors=github_errors,
    )

    missing_inputs: list[str] = []
    for section in (spec_review, review, merge_ready):
        for message in section.get("missing_inputs", []):
            if message not in missing_inputs:
                missing_inputs.append(message)
    for message in github_errors:
        if message not in missing_inputs:
            missing_inputs.append(message)
    for message in control_status.get("missing_inputs", []):
        if message not in missing_inputs:
            missing_inputs.append(str(message))

    result = "pass" if not missing_inputs else "block"
    summary = (
        "status surface shows the current item, spec gate, implementation review, and merge checkpoint in one read."
        if result == "pass"
        else "status surface is readable, but one or more governance gates are still blocking or stale."
    )
    return emit(
        {
            "command": "status",
            "result": result,
            "summary": summary,
            "missing_inputs": missing_inputs,
            "fallback_to": "admission" if missing_inputs else None,
            "runtime_state": runtime_state,
            "item": {
                "id": context["item_id"],
                "goal": context["goal"],
                "scope": context["scope"],
                "execution_path": context["execution_path"],
                "workspace_entry": context["workspace_entry"],
                "recovery_entry": str(context["report"]["fact_chain"]["entry_points"]["recovery_entry"]),
                "review_entry": context["review_entry"],
                "validation_entry": context["validation_entry"],
            },
            "current_checkpoint": {
                "raw": context["current_checkpoint_raw"],
                "normalized": context["current_checkpoint"],
            },
            "recovery": {
                "current_stop": context["current_stop"],
                "next_step": context["next_step"],
                "blockers": context["blockers"],
                "latest_validation_summary": context["latest_validation_summary"],
                "recovery_boundary": context["recovery_boundary"],
                "current_lane": context["current_lane"],
            },
            "spec_review": spec_review,
            "review": review,
            "merge_ready": merge_ready,
            "closeout": closeout,
            "governance_status": control_status,
            "governance_surface": governance_surface,
            "github": github_status,
        }
    )


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
