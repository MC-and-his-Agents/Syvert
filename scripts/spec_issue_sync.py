#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import datetime as dt
import json

from scripts.common import REPO_ROOT, git_changed_files, require_cli, run


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将正式 spec 的最小元数据同步到 GitHub Issue。")
    parser.add_argument("--before-sha")
    parser.add_argument("--after-sha", default="HEAD")
    parser.add_argument("--file", action="append", dest="files")
    parser.add_argument("--repo", default="")
    return parser.parse_args(argv)


def changed_spec_files(args: argparse.Namespace) -> list[str]:
    if args.files:
        return args.files
    if not args.before_sha:
        return []
    changed = git_changed_files(args.before_sha, args.after_sha, repo=REPO_ROOT)
    return [path for path in changed if path.startswith("docs/specs/FR-") and path.endswith("/spec.md")]


def spec_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.parent.name


def existing_issue_number(directory_name: str, repo: str) -> str:
    completed = run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--search",
            f"\"[{directory_name}]\" in:title",
            "--json",
            "number,title",
        ]
    )
    issues = json.loads(completed.stdout or "[]")
    for issue in issues:
        if issue["title"].startswith(f"[{directory_name}] "):
            return str(issue["number"])
    return ""


def upsert_issue(file_path: str, repo: str) -> None:
    absolute = REPO_ROOT / file_path
    directory_name = absolute.parent.name
    title = spec_title(absolute)
    issue_title = f"[{directory_name}] {title}"
    updated_at = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    body = "\n".join(
        [
            "此 Issue 由 `spec_issue_sync.py` 自动维护最小元数据。",
            "",
            f"- FR: `{directory_name}`",
            f"- Spec 路径: `{file_path}`",
            f"- 最近同步时间: `{updated_at}`",
            "",
            "正式契约以仓库内 `spec.md` 为准，Issue 只保留索引信息，不镜像正文。",
        ]
    )

    existing = existing_issue_number(directory_name, repo)
    if existing:
        run(["gh", "issue", "edit", existing, "--repo", repo, "--title", issue_title, "--body", body], cwd=REPO_ROOT)
    else:
        run(["gh", "issue", "create", "--repo", repo, "--title", issue_title, "--body", body], cwd=REPO_ROOT)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    require_cli("gh")
    run(["gh", "auth", "status"], cwd=REPO_ROOT)
    repo = args.repo or run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"], cwd=REPO_ROOT).stdout.strip()
    files = changed_spec_files(args)
    for file_path in files:
        upsert_issue(file_path, repo)
    print(f"已同步 {len(files)} 个 spec 索引。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
