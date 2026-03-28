#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.common import REPO_ROOT, git_changed_files
from scripts.policy.policy import classify_paths


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验治理基线变更是否保持纯度。")
    parser.add_argument("--mode", choices=("ci", "local"), default="local")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--base-ref")
    parser.add_argument("--base-sha")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--head-sha")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    base_ref = args.base_ref or args.base_sha
    head_ref = args.head_sha or args.head_ref
    if not base_ref:
        print("governance-gate 需要 `--base-ref` 或 `--base-sha`。", file=sys.stderr)
        return 1

    changed = git_changed_files(base_ref, head_ref, repo=repo_root)
    classified = classify_paths(changed)
    categories = {item.category for item in classified}
    if "governance" in categories and "implementation" in categories:
        print("治理基线改动不得与实现代码混在同一 PR。", file=sys.stderr)
        for item in classified:
            if item.category == "implementation":
                print(f"- {item.path}", file=sys.stderr)
        return 1

    print("governance-gate 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
