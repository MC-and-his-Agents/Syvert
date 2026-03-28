#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json

from scripts.common import (
    REPO_ROOT,
    ensure_parent,
    load_json,
    now_iso_utc,
    require_cli,
    run,
    slugify,
    syvert_state_file,
)
from scripts.policy.policy import get_policy
from scripts.workflow_contract import load_workflow_contract, render_workspace_key, resolve_workspace_root


STATE_FILE = syvert_state_file("worktrees.json")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为 Issue 创建或复用独立 worktree。")
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--class", dest="pr_class", required=True, choices=get_policy()["pr_classes"])
    parser.add_argument("--base", default="main")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def load_state(path: Path = STATE_FILE) -> dict:
    if not path.exists():
        return {"worktrees": {}}
    return load_json(path)


def save_state(state: dict, path: Path = STATE_FILE) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def issue_title_for_number(issue_number: int) -> str:
    require_cli("gh")
    completed = run(
        ["gh", "issue", "view", str(issue_number), "--json", "number,title", "--jq", ".title"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Issue #{issue_number} 不存在或无法读取。")
    title = completed.stdout.strip()
    if not title:
        raise SystemExit(f"Issue #{issue_number} 缺少标题。")
    return title


def git_head_sha(ref: str, *, cwd: Path = REPO_ROOT) -> str:
    completed = run(["git", "rev-parse", ref], cwd=cwd)
    return completed.stdout.strip()


def git_worktree_entries(repo_root: Path) -> list[dict[str, str]]:
    completed = run(["git", "worktree", "list", "--porcelain"], cwd=repo_root)
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        entries.append(current)
    return entries


def build_worktree_metadata(issue_number: int, issue_title: str, contract: dict, env: dict[str, str] | None = None) -> dict[str, str]:
    slug = slugify(issue_title)
    key = render_workspace_key(issue_number, slug, contract)
    root = resolve_workspace_root(contract, env)
    path = root / key
    return {
        "issue": str(issue_number),
        "issue_title": issue_title,
        "slug": slug,
        "key": key,
        "branch": key,
        "path": str(path),
    }


def find_existing_worktree(branch: str, path: Path, repo_root: Path) -> bool:
    entries = git_worktree_entries(repo_root)
    path_text = str(path.resolve())
    branch_ref = f"refs/heads/{branch}"
    for entry in entries:
        if entry.get("worktree") == path_text:
            return True
        if entry.get("branch") == branch_ref:
            return True
    return False


def ensure_worktree(issue_number: int, pr_class: str, base_ref: str, dry_run: bool) -> dict:
    contract, _ = load_workflow_contract()
    metadata = build_worktree_metadata(issue_number, issue_title_for_number(issue_number), contract)
    target_path = Path(metadata["path"]).expanduser()
    branch = metadata["branch"]
    base_remote = f"origin/{base_ref}"

    run(["git", "fetch", "origin", base_ref], cwd=REPO_ROOT, check=False)
    base_sha = git_head_sha(base_remote)
    reused = find_existing_worktree(branch, target_path, REPO_ROOT)

    if not dry_run and not reused:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        branch_exists = run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=REPO_ROOT, check=False).returncode == 0
        command = ["git", "worktree", "add", str(target_path)]
        if branch_exists:
            command.append(branch)
        else:
            command.extend(["-b", branch, base_remote])
        run(command, cwd=REPO_ROOT)

    head_sha = base_sha
    if not dry_run and target_path.exists():
        head_sha = git_head_sha("HEAD", cwd=target_path)

    payload = {
        "issue": issue_number,
        "class": pr_class,
        "key": metadata["key"],
        "branch": branch,
        "path": str(target_path),
        "base_ref": base_ref,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "reused": reused,
        "updated_at": now_iso_utc(),
    }

    if not dry_run:
        state = load_state()
        state.setdefault("worktrees", {})[metadata["key"]] = payload
        save_state(state)
    return payload


def print_payload(payload: dict) -> None:
    ordered_keys = ("issue", "class", "key", "branch", "path", "base_ref", "base_sha", "head_sha", "reused", "updated_at")
    for key in ordered_keys:
        print(f"{key}={payload[key]}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    payload = ensure_worktree(args.issue, args.pr_class, args.base, args.dry_run)
    print_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
