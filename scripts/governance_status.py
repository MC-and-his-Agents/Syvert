#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json

from scripts.common import REPO_ROOT, default_github_repo, integration_ref_is_checkable, legacy_state_file, load_json, run, syvert_state_file
from scripts.integration_contract import (
    build_review_packet,
    fetch_integration_ref_live_state,
    merge_gate_requires_integration_recheck,
    parse_pr_integration_check,
    validate_issue_fetch,
    validate_integration_ref_live_state,
)
from scripts.item_context import (
    active_exec_plans_for_issue,
    load_item_context_from_exec_plan,
    matching_exec_plan_for_issue,
    parse_item_context_from_body,
)
from scripts.pr_guardian import find_latest_guardian_result, load_guardian_state


GUARDIAN_STATE_FILE = syvert_state_file("guardian.json")
REVIEW_POLLER_STATE_FILE = syvert_state_file("review-poller.json")
WORKTREE_STATE_FILE = syvert_state_file("worktrees.json")
LEGACY_REVIEW_POLLER_STATE = legacy_state_file("syvert-pr-review.json")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="聚合治理状态面。")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--issue", type=int)
    scope.add_argument("--pr", type=int)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def load_state_with_legacy(primary: Path, legacy: Path | None = None) -> dict:
    if primary.exists():
        return load_json(primary)
    if legacy and legacy.exists():
        return load_json(legacy)
    return {}


def load_review_poller_state() -> dict:
    return load_state_with_legacy(REVIEW_POLLER_STATE_FILE, LEGACY_REVIEW_POLLER_STATE)


def load_worktree_state() -> dict:
    return load_state_with_legacy(WORKTREE_STATE_FILE)


def fetch_pr_meta(pr_number: int) -> dict:
    completed = run(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "number,headRefOid,headRefName,body",
        ],
        cwd=REPO_ROOT,
    )
    return json.loads(completed.stdout or "{}")


def fetch_checks_summary(pr_number: int) -> list[dict]:
    completed = run(
        ["gh", "pr", "checks", str(pr_number), "--json", "name,bucket,state,link"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return json.loads(completed.stdout or "[]")


def filter_worktrees_by_issue(state: dict, issue_number: int) -> list[dict]:
    items = state.get("worktrees", {}).values()
    return sorted((item for item in items if item.get("issue") == issue_number), key=lambda item: item["key"])


def build_item_context_for_pr(meta: dict, worktree_item: dict | None) -> dict:
    body_context = parse_item_context_from_body(str(meta.get("body") or ""))
    item_key = body_context.get("item_key", "")
    if not worktree_item or worktree_item.get("issue") is None:
        return {}
    recorded_path = str(worktree_item.get("path", "")).strip()
    if recorded_path and Path(recorded_path).resolve() != REPO_ROOT.resolve():
        return {}
    required_fields = ("issue", "item_key", "item_type", "release", "sprint")
    if any(not body_context.get(field, "") for field in required_fields):
        return {}

    payload = load_item_context_from_exec_plan(REPO_ROOT, item_key)
    if payload.get("conflict") == "duplicate_metadata_keys":
        return {}
    if payload.get("conflict") == "multiple_active_exec_plans":
        return {}
    if not payload:
        return {}
    try:
        issue_number = int(body_context["issue"])
    except (TypeError, ValueError):
        return {}
    issue_active_exec_plans = active_exec_plans_for_issue(REPO_ROOT, issue_number)
    if len(issue_active_exec_plans) != 1:
        return {}
    if issue_active_exec_plans[0].get("item_key", "") != item_key:
        return {}
    active_item = payload.get("active 收口事项", "")
    if active_item and active_item != item_key:
        return {}
    if worktree_item and worktree_item.get("issue") is not None and str(worktree_item["issue"]) != body_context.get("issue", ""):
        return {}

    comparisons = (
        ("issue", "Issue"),
        ("item_key", "item_key"),
        ("item_type", "item_type"),
        ("release", "release"),
        ("sprint", "sprint"),
    )
    for body_key, metadata_key in comparisons:
        if payload.get(metadata_key, "") != body_context.get(body_key, ""):
            return {}
    return payload


def build_status_payload(issue_number: int | None = None, pr_number: int | None = None) -> dict:
    guardian_state = load_guardian_state(GUARDIAN_STATE_FILE)
    review_poller_state = load_review_poller_state()
    worktree_state = load_worktree_state()

    payload: dict[str, object] = {
        "guardian": {},
        "review_poller": {},
        "worktrees": [],
        "checks": [],
        "item_context": {},
        "integration": {},
    }

    if pr_number is not None:
        meta = fetch_pr_meta(pr_number)
        head_sha = meta.get("headRefOid", "")
        payload["guardian"] = find_latest_guardian_result(
            pr_number,
            head_sha,
            body=str(meta.get("body") or ""),
            require_body_bound=True,
            path=GUARDIAN_STATE_FILE,
        ) or {}
        payload["review_poller"] = review_poller_state.get("prs", {}).get(str(pr_number), {})
        payload["checks"] = fetch_checks_summary(pr_number)
        branch_name = meta.get("headRefName", "")
        matching_worktrees = [item for item in worktree_state.get("worktrees", {}).values() if item.get("branch") == branch_name]
        matched_worktree: dict | None = matching_worktrees[0] if len(matching_worktrees) == 1 else None
        payload["worktrees"] = matching_worktrees[:1] if len(matching_worktrees) == 1 else matching_worktrees
        payload["item_context"] = build_item_context_for_pr(meta, matched_worktree)
        payload["integration"] = build_integration_status_for_pr(meta)
        return payload

    if issue_number is not None:
        payload["worktrees"] = filter_worktrees_by_issue(worktree_state, issue_number)
        payload["item_context"] = matching_exec_plan_for_issue(REPO_ROOT, issue_number)
        payload["integration"] = build_integration_status_for_issue(issue_number)
        return payload

    payload["guardian"] = guardian_state.get("prs", {})
    payload["review_poller"] = review_poller_state.get("prs", {})
    payload["worktrees"] = list(worktree_state.get("worktrees", {}).values())
    return payload


def build_integration_status_for_pr(meta: dict) -> dict[str, object]:
    body = str(meta.get("body") or "")
    body_context = parse_item_context_from_body(body)
    issue_number: int | None = None
    try:
        issue_text = str(body_context.get("issue") or "").strip()
        issue_number = int(issue_text) if issue_text else None
    except ValueError:
        issue_number = None
    issue_resolution = validate_issue_fetch(issue_number, allow_missing_payload=True) if issue_number is not None else None
    issue_canonical = dict(issue_resolution.canonical) if issue_resolution else {}
    issue_error = str(issue_resolution.error or "") if issue_resolution else ""
    pr_canonical = parse_pr_integration_check(body)
    integration_ref = str(pr_canonical.get("integration_ref") or "").strip()
    if not integration_ref:
        integration_ref = str(issue_canonical.get("integration_ref") or "").strip()
    integration_ref_live = fetch_integration_ref_live_state(integration_ref) if integration_ref_is_checkable(integration_ref) else {}
    packet = build_review_packet(
        body,
        issue_number=issue_number,
        issue_canonical=issue_canonical,
        issue_error=issue_error,
        integration_ref_live=integration_ref_live,
    )
    if not pr_canonical and issue_canonical:
        packet["merge_gate"] = str(issue_canonical.get("merge_gate") or "").strip().lower()
        packet["merge_gate_requires_recheck"] = merge_gate_requires_integration_recheck(issue_canonical)
    live_validation_payload = pr_canonical or issue_canonical
    live_errors = validate_integration_ref_live_state(
        live_validation_payload,
        integration_ref_live,
        current_repo_slug=default_github_repo(),
    )
    packet["integration_ref_live_errors"] = live_errors
    packet["issue_lookup_error"] = issue_error
    return packet


def build_integration_status_for_issue(issue_number: int) -> dict[str, object]:
    issue_resolution = validate_issue_fetch(issue_number, allow_missing_payload=True)
    issue_canonical = dict(issue_resolution.canonical)
    issue_error = str(issue_resolution.error or "")
    integration_ref = str(issue_canonical.get("integration_ref") or "").strip()
    integration_ref_live = fetch_integration_ref_live_state(integration_ref) if integration_ref_is_checkable(integration_ref) else {}
    packet = build_review_packet(
        "",
        issue_number=issue_number,
        issue_canonical=issue_canonical,
        issue_error=issue_error,
        integration_ref_live=integration_ref_live,
    )
    live_errors = validate_integration_ref_live_state(
        issue_canonical,
        integration_ref_live,
        current_repo_slug=default_github_repo(),
    )
    packet["pr_canonical"] = {}
    packet["normalized_pr_canonical"] = {}
    packet["comparison_errors"] = []
    packet["merge_validation_errors"] = []
    packet["integration_ref_live_errors"] = live_errors
    packet["merge_gate"] = str(issue_canonical.get("merge_gate") or "").strip().lower()
    packet["merge_gate_requires_recheck"] = packet["merge_gate"] == "integration_check_required"
    packet["issue_lookup_error"] = issue_error
    return packet


def render_text(payload: dict) -> str:
    lines: list[str] = []

    guardian = payload.get("guardian") or {}
    if guardian:
        lines.extend(
            [
                "[guardian]",
                f"verdict={guardian.get('verdict', '')}",
                f"safe_to_merge={guardian.get('safe_to_merge', '')}",
                f"head_sha={guardian.get('head_sha', '')}",
                f"reviewed_at={guardian.get('reviewed_at', '')}",
            ]
        )
    else:
        lines.extend(["[guardian]", "empty=true"])

    review_poller = payload.get("review_poller") or {}
    if review_poller:
        lines.extend(
            [
                "[review_poller]",
                f"head_sha={review_poller.get('head_sha', '')}",
                f"reviewed_at={review_poller.get('reviewed_at', '')}",
            ]
        )
    else:
        lines.extend(["[review_poller]", "empty=true"])

    worktrees = payload.get("worktrees") or []
    lines.append("[worktrees]")
    if not worktrees:
        lines.append("count=0")
    else:
        lines.append(f"count={len(worktrees)}")
        for item in worktrees:
            lines.append(f"- {item.get('key')} {item.get('branch')} {item.get('path')}")

    item_context = payload.get("item_context") or {}
    lines.append("[item_context]")
    if not item_context:
        lines.append("empty=true")
    else:
        lines.append(f"issue={item_context.get('Issue', '')}")
        lines.append(f"item_key={item_context.get('item_key', '')}")
        lines.append(f"item_type={item_context.get('item_type', '')}")
        lines.append(f"release={item_context.get('release', '')}")
        lines.append(f"sprint={item_context.get('sprint', '')}")
        lines.append(f"exec_plan={item_context.get('exec_plan', '')}")

    checks = payload.get("checks") or []
    lines.append("[checks]")
    if not checks:
        lines.append("count=0")
    else:
        lines.append(f"count={len(checks)}")
        for item in checks:
            lines.append(f"- {item.get('name')} {item.get('bucket')} {item.get('state')}")

    integration = payload.get("integration") or {}
    lines.append("[integration]")
    if not integration:
        lines.append("empty=true")
    else:
        lines.append(f"issue_number={integration.get('issue_number', '')}")
        lines.append(f"merge_gate={integration.get('merge_gate', '')}")
        lines.append(f"merge_gate_requires_recheck={integration.get('merge_gate_requires_recheck', '')}")
        pr_canonical = integration.get("pr_canonical") or {}
        issue_canonical = integration.get("issue_canonical") or {}
        lines.append(f"pr_integration_ref={pr_canonical.get('integration_ref', '')}")
        lines.append(f"issue_integration_ref={issue_canonical.get('integration_ref', '')}")
        live = integration.get("integration_ref_live") or {}
        lines.append(f"live_source={live.get('source', '')}")
        lines.append(f"live_status={live.get('status', '')}")
        lines.append(f"live_dependency_order={live.get('dependency_order', '')}")
        issue_lookup_error = str(integration.get("issue_lookup_error") or "")
        if issue_lookup_error:
            lines.append(f"issue_lookup_error={issue_lookup_error}")
        comparison_errors = integration.get("comparison_errors") or []
        lines.append(f"comparison_errors={len(comparison_errors)}")
        for item in comparison_errors:
            lines.append(f"- comparison_error: {item}")
        merge_validation_errors = integration.get("merge_validation_errors") or []
        lines.append(f"merge_validation_errors={len(merge_validation_errors)}")
        for item in merge_validation_errors:
            lines.append(f"- merge_validation_error: {item}")
        live_errors = integration.get("integration_ref_live_errors") or []
        lines.append(f"integration_ref_live_errors={len(live_errors)}")
        for item in live_errors:
            lines.append(f"- integration_live_error: {item}")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])
    payload = build_status_payload(issue_number=args.issue, pr_number=args.pr)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload), end="")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
