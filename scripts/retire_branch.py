#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json

from scripts.common import REPO_ROOT, dump_json, ensure_parent, git_current_branch, load_json, now_iso_utc, require_cli, run
from scripts.state_paths import worktrees_state_path


WORKTREE_STATE_FILE = worktrees_state_path()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为已吸收或已替代的分支创建归档锚点并执行退役。")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--replaced-by", default="main")
    parser.add_argument("--strategy", choices=("merged", "superseded"), default="merged")
    parser.add_argument("--reason")
    parser.add_argument("--delete-remote", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def archive_tag_name(branch: str) -> str:
    return f"archive/branches/{branch}"


def git_local_branch_exists(branch: str, *, repo_root: Path = REPO_ROOT) -> bool:
    completed = run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=repo_root, check=False)
    return completed.returncode == 0


def git_rev_parse(ref: str, *, repo_root: Path = REPO_ROOT) -> str:
    completed = run(["git", "rev-parse", ref], cwd=repo_root)
    return completed.stdout.strip()


def git_worktree_entries(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
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


def branch_attached_to_worktree(branch: str, entries: list[dict[str, str]]) -> bool:
    branch_ref = f"refs/heads/{branch}"
    return any(entry.get("branch") == branch_ref for entry in entries)


def branch_is_ancestor(branch: str, ref: str, *, repo_root: Path = REPO_ROOT) -> bool:
    completed = run(["git", "merge-base", "--is-ancestor", branch, ref], cwd=repo_root, check=False)
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    stderr = completed.stderr.strip()
    raise SystemExit(stderr or f"无法判断 {branch} 是否已被 {ref} 吸收。")


def archive_tag_exists(tag_name: str, *, repo_root: Path = REPO_ROOT) -> bool:
    completed = run(["git", "show-ref", "--verify", f"refs/tags/{tag_name}"], cwd=repo_root, check=False)
    return completed.returncode == 0


def load_worktree_state(path: Path = WORKTREE_STATE_FILE) -> dict:
    if not path.exists():
        return {"worktrees": {}}
    return load_json(path)


def worktree_state_keys_for_branch(branch: str, state: dict) -> list[str]:
    items = state.get("worktrees", {})
    return [
        key
        for key, payload in items.items()
        if isinstance(payload, dict) and payload.get("branch") == branch
    ]


def prune_worktree_state(branch: str, *, path: Path = WORKTREE_STATE_FILE) -> list[str]:
    state = load_worktree_state(path)
    keys = worktree_state_keys_for_branch(branch, state)
    if not keys:
        return []
    for key in keys:
        state["worktrees"].pop(key, None)
    ensure_parent(path)
    dump_json(path, state)
    return keys


def build_archive_message(payload: dict[str, str | bool]) -> str:
    lines = [
        "Syvert branch retirement archive",
        "",
        f"branch: {payload['branch']}",
        f"sha: {payload['branch_sha']}",
        f"strategy: {payload['strategy']}",
        f"replaced_by: {payload['replaced_by']}",
        f"reason: {payload['reason']}",
        f"retired_at: {payload['retired_at']}",
        f"delete_remote: {payload['delete_remote']}",
    ]
    return "\n".join(lines) + "\n"


def delete_remote_branch(branch: str, *, repo_root: Path = REPO_ROOT) -> None:
    completed = run(["git", "push", "origin", "--delete", branch], cwd=repo_root, check=False)
    if completed.returncode == 0:
        return
    stderr = completed.stderr.strip()
    if "remote ref does not exist" in stderr:
        return
    raise SystemExit(stderr or f"删除远端分支失败: {branch}")


def retire_branch(
    branch: str,
    *,
    replaced_by: str,
    strategy: str,
    reason: str | None,
    delete_remote: bool,
    dry_run: bool,
    repo_root: Path = REPO_ROOT,
) -> dict[str, object]:
    require_cli("git")
    if not git_local_branch_exists(branch, repo_root=repo_root):
        raise SystemExit(f"本地分支不存在: {branch}")
    if git_current_branch(repo=repo_root) == branch:
        raise SystemExit(f"当前正位于分支 `{branch}`，不能直接退役。")
    if branch_attached_to_worktree(branch, git_worktree_entries(repo_root)):
        raise SystemExit(f"分支 `{branch}` 仍绑定活跃 worktree，需先清理 worktree。")
    if strategy == "superseded" and not reason:
        raise SystemExit("`superseded` 退役策略必须提供 `--reason`。")
    if strategy == "merged" and not branch_is_ancestor(branch, replaced_by, repo_root=repo_root):
        raise SystemExit(f"分支 `{branch}` 不是 `{replaced_by}` 的祖先提交，不能按 merged 策略退役。")

    branch_sha = git_rev_parse(branch, repo_root=repo_root)
    tag_name = archive_tag_name(branch)
    if archive_tag_exists(tag_name, repo_root=repo_root):
        raise SystemExit(f"归档标签已存在: {tag_name}")

    payload: dict[str, object] = {
        "branch": branch,
        "branch_sha": branch_sha,
        "strategy": strategy,
        "replaced_by": replaced_by,
        "reason": reason or f"merged into {replaced_by}",
        "retired_at": now_iso_utc(),
        "delete_remote": delete_remote,
        "archive_tag": tag_name,
        "state_keys_removed": worktree_state_keys_for_branch(branch, load_worktree_state()),
        "actions": [
            f"git tag -a {tag_name} {branch_sha}",
            *( [f"git push origin refs/tags/{tag_name}"] if delete_remote else [] ),
            *( [f"git push origin --delete {branch}"] if delete_remote else [] ),
            f"prune worktree state for {branch}",
            f"git branch -D {branch}",
        ],
    }

    if dry_run:
        return payload

    run(
        ["git", "tag", "-a", tag_name, branch_sha, "-m", build_archive_message(payload)],
        cwd=repo_root,
    )
    if delete_remote:
        run(["git", "push", "origin", f"refs/tags/{tag_name}"], cwd=repo_root)
        delete_remote_branch(branch, repo_root=repo_root)
    prune_worktree_state(branch)
    run(["git", "branch", "-D", branch], cwd=repo_root)
    return payload


def print_payload(payload: dict[str, object]) -> None:
    print(f"branch={payload['branch']}")
    print(f"branch_sha={payload['branch_sha']}")
    print(f"strategy={payload['strategy']}")
    print(f"replaced_by={payload['replaced_by']}")
    print(f"archive_tag={payload['archive_tag']}")
    print(f"reason={payload['reason']}")
    print(f"retired_at={payload['retired_at']}")
    print(f"delete_remote={payload['delete_remote']}")
    print(f"state_keys_removed={json.dumps(payload['state_keys_removed'], ensure_ascii=False)}")
    print("[actions]")
    for action in payload["actions"]:
        print(f"- {action}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    payload = retire_branch(
        args.branch,
        replaced_by=args.replaced_by,
        strategy=args.strategy,
        reason=args.reason,
        delete_remote=args.delete_remote,
        dry_run=args.dry_run,
    )
    print_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
