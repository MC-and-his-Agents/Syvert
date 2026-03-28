#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import subprocess
import tempfile

from scripts.common import REPO_ROOT, require_cli, run


REQUIRED_CHECKS = [
    "Validate Commit Messages",
    "Validate Docs And Guard Scripts",
    "Validate Spec Review Boundaries",
    "Validate Governance Tooling",
]
RULESET_NAME = "syvert-main-pr-gate"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="同步 GitHub 仓库治理设置。")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def desired_repo_settings() -> dict:
    return {
        "allow_squash_merge": True,
        "allow_merge_commit": False,
        "allow_rebase_merge": False,
        "delete_branch_on_merge": True,
    }


def desired_branch_protection() -> dict:
    return {
        "required_status_checks": {
            "strict": True,
            "contexts": REQUIRED_CHECKS,
        },
        "enforce_admins": True,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "required_conversation_resolution": True,
        "required_linear_history": False,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "block_creations": False,
        "lock_branch": False,
        "allow_fork_syncing": False,
    }


def desired_ruleset() -> dict:
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "conditions": {
            "ref_name": {
                "include": ["refs/heads/main"],
                "exclude": [],
            }
        },
        "rules": [
            {
                "type": "pull_request",
                "parameters": {
                    "allowed_merge_methods": ["squash"],
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": True,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [{"context": item} for item in REQUIRED_CHECKS],
                    "strict_required_status_checks_policy": True,
                },
            },
        ],
    }


def current_repo_settings(repo: str) -> dict:
    completed = run(
        [
            "gh",
            "api",
            f"repos/{repo}",
            "--jq",
            "{allow_squash_merge,allow_merge_commit,allow_rebase_merge,delete_branch_on_merge}",
        ],
        cwd=REPO_ROOT,
    )
    return json.loads(completed.stdout or "{}")


def current_branch_protection(repo: str) -> dict:
    completed = run(["gh", "api", f"repos/{repo}/branches/main/protection"], cwd=REPO_ROOT)
    payload = json.loads(completed.stdout or "{}")
    status_checks = payload.get("required_status_checks") or {}
    return {
        "required_status_checks": {
            "strict": status_checks.get("strict"),
            "contexts": status_checks.get("contexts", []),
        },
        "enforce_admins": (payload.get("enforce_admins") or {}).get("enabled"),
        "required_pull_request_reviews": payload.get("required_pull_request_reviews"),
        "restrictions": payload.get("restrictions"),
        "required_conversation_resolution": (payload.get("required_conversation_resolution") or {}).get("enabled"),
        "required_linear_history": (payload.get("required_linear_history") or {}).get("enabled"),
        "allow_force_pushes": (payload.get("allow_force_pushes") or {}).get("enabled"),
        "allow_deletions": (payload.get("allow_deletions") or {}).get("enabled"),
        "block_creations": (payload.get("block_creations") or {}).get("enabled"),
        "lock_branch": (payload.get("lock_branch") or {}).get("enabled"),
        "allow_fork_syncing": (payload.get("allow_fork_syncing") or {}).get("enabled"),
    }


def current_rulesets(repo: str) -> list[dict]:
    completed = run(["gh", "api", f"repos/{repo}/rulesets"], cwd=REPO_ROOT, check=False)
    if completed.returncode != 0:
        return []
    return json.loads(completed.stdout or "[]")


def diff_settings(current: dict, expected: dict) -> dict:
    diff: dict[str, object] = {}
    for key, value in expected.items():
        current_value = current.get(key)
        if isinstance(value, dict):
            nested = diff_settings(current_value or {}, value)
            if nested:
                diff[key] = nested
            continue
        if current_value != value:
            diff[key] = {"current": current_value, "expected": value}
    return diff


def run_gh_with_json(method: str, endpoint: str, payload: dict) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False)
        handle.flush()
        path = Path(handle.name)
    try:
        completed = subprocess.run(
            ["gh", "api", "--method", method, endpoint, "--input", str(path)],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(completed.stderr.strip() or f"无法更新 `{endpoint}`")
    finally:
        path.unlink(missing_ok=True)


def ruleset_id_for_name(repo: str, name: str) -> int | None:
    for item in current_rulesets(repo):
        if item.get("name") == name:
            return int(item["id"])
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    require_cli("gh")

    repo_settings = current_repo_settings(args.repo)
    branch_protection = current_branch_protection(args.repo)
    expected_repo = desired_repo_settings()
    expected_branch = desired_branch_protection()
    expected_ruleset = desired_ruleset()
    current_ruleset = next((item for item in current_rulesets(args.repo) if item.get("name") == RULESET_NAME), {})

    diff = {
        "repo": diff_settings(repo_settings, expected_repo),
        "branch_protection": diff_settings(branch_protection, expected_branch),
        "ruleset": diff_settings(current_ruleset, expected_ruleset),
    }

    if args.dry_run:
        print(json.dumps(diff, ensure_ascii=False, indent=2))
        return 0

    if diff["repo"]:
        run_gh_with_json("PATCH", f"repos/{args.repo}", expected_repo)
    if diff["branch_protection"]:
        run_gh_with_json("PUT", f"repos/{args.repo}/branches/main/protection", expected_branch)
    ruleset_id = ruleset_id_for_name(args.repo, RULESET_NAME)
    if ruleset_id is None:
        run_gh_with_json("POST", f"repos/{args.repo}/rulesets", expected_ruleset)
    elif diff["ruleset"]:
        run_gh_with_json("PUT", f"repos/{args.repo}/rulesets/{ruleset_id}", expected_ruleset)

    print("sync-repo-settings 完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
