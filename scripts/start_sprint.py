#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from scripts.common import require_cli, run


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="创建或校验 GitHub milestone。")
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--repo", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def milestone_exists(repo: str, name: str) -> bool:
    completed = run(["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100"])
    milestones = json.loads(completed.stdout or "[]")
    return any(item.get("title") == name for item in milestones)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.dry_run:
        print(f"Dry run: 将创建里程碑 `{args.name}`。")
        return 0
    require_cli("gh")
    run(["gh", "auth", "status"])
    repo = args.repo or run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]).stdout.strip()

    if milestone_exists(repo, args.name):
        print(f"里程碑 `{args.name}` 已存在。")
        return 0

    run(
        [
            "gh",
            "api",
            f"repos/{repo}/milestones",
            "--method",
            "POST",
            "-f",
            f"title={args.name}",
            "-f",
            f"description={args.description}",
        ]
    )
    print(f"已创建里程碑 `{args.name}`。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
