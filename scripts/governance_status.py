#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json

from scripts.common import REPO_ROOT, legacy_state_file, load_json, run, syvert_state_file
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
    issue_active_exec_plans = active_exec_plans_for_issue(REPO_ROOT, int(body_context["issue"]))
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
    }

    if pr_number is not None:
        meta = fetch_pr_meta(pr_number)
        head_sha = meta.get("headRefOid", "")
        payload["guardian"] = find_latest_guardian_result(pr_number, head_sha, path=GUARDIAN_STATE_FILE) or {}
        payload["review_poller"] = review_poller_state.get("prs", {}).get(str(pr_number), {})
        payload["checks"] = fetch_checks_summary(pr_number)
        branch_name = meta.get("headRefName", "")
        matched_worktree: dict | None = None
        for item in worktree_state.get("worktrees", {}).values():
            if item.get("branch") == branch_name:
                matched_worktree = item
                payload["worktrees"] = [item]
                break
        payload["item_context"] = build_item_context_for_pr(meta, matched_worktree)
        return payload

    if issue_number is not None:
        payload["worktrees"] = filter_worktrees_by_issue(worktree_state, issue_number)
        payload["item_context"] = matching_exec_plan_for_issue(REPO_ROOT, issue_number)
        return payload

    payload["guardian"] = guardian_state.get("prs", {})
    payload["review_poller"] = review_poller_state.get("prs", {})
    payload["worktrees"] = list(worktree_state.get("worktrees", {}).values())
    return payload


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
