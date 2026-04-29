#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json

from scripts.common import dump_json, env_with_repo_pythonpath, load_json, parse_pr_class_from_body, require_cli, run
from scripts.state_paths import review_poller_legacy_state_path, review_poller_state_path


DEFAULT_STATE_FILE = review_poller_state_path()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 head SHA 变化轮询 PR guardian。")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-post-review", action="store_true")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--milestone")
    parser.add_argument("--pr-class")
    return parser.parse_args(argv)


def ensure_state_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        legacy_path = review_poller_legacy_state_path()
        if path == DEFAULT_STATE_FILE and legacy_path.exists():
            dump_json(path, load_json(legacy_path))
            return
        dump_json(path, {"prs": {}})


def list_open_prs() -> list[dict]:
    completed = run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--json",
            "number,title,headRefOid,headRefName,isDraft,baseRefName,milestone,body",
        ]
    )
    return json.loads(completed.stdout or "[]")


def review_pr(pr_number: int, post_review: bool) -> None:
    command = [sys.executable, str(Path("scripts/pr_guardian.py")), "review", str(pr_number)]
    if post_review:
        command.append("--post-review")
    run(command, env=env_with_repo_pythonpath())


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    require_cli("gh")
    state_path = Path(args.state_file)
    ensure_state_file(state_path)
    state = load_json(state_path)

    reviewed = 0
    state_changed = False
    for pr in list_open_prs():
        if pr["baseRefName"] != args.base_branch or pr["isDraft"]:
            continue
        if args.milestone and (pr.get("milestone") or {}).get("title") != args.milestone:
            continue
        pr_class = parse_pr_class_from_body(pr.get("body") or "")
        if args.pr_class and pr_class != args.pr_class:
            continue

        previous_sha = state.get("prs", {}).get(str(pr["number"]), {}).get("head_sha", "")
        if previous_sha == pr["headRefOid"]:
            continue

        reviewed += 1
        if not args.dry_run:
            review_pr(pr["number"], post_review=not args.no_post_review)
            state.setdefault("prs", {})[str(pr["number"])] = {
                "head_sha": pr["headRefOid"],
            }
            state_changed = True

    if not args.dry_run and state_changed:
        dump_json(state_path, state)

    print(f"轮询完成，触发审查 {reviewed} 个 PR。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
