#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.common import REPO_ROOT, git_changed_files
from scripts.policy.policy import allowed_categories, classify_paths, get_policy


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 PR class 与实际改动类别是否一致。")
    parser.add_argument("--class", dest="pr_class", required=True, choices=get_policy()["pr_classes"])
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def build_report(pr_class: str, changed_paths: list[str]) -> dict:
    classified = classify_paths(changed_paths)
    allowed = allowed_categories(pr_class)
    disallowed = [item for item in classified if item.category not in allowed]
    categories = sorted({item.category for item in classified})
    return {
        "pr_class": pr_class,
        "changed_paths": changed_paths,
        "categories": categories,
        "allowed_categories": sorted(allowed),
        "violations": [{"path": item.path, "category": item.category} for item in disallowed],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    changed_paths = git_changed_files(args.base_ref, args.head_ref, repo=repo_root)
    if not changed_paths:
        print("当前分支相对基线没有变更，无法创建或校验 PR。", file=sys.stderr)
        return 1

    report = build_report(args.pr_class, changed_paths)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"PR class: {report['pr_class']}")
        print(f"变更类别: {', '.join(report['categories'])}")
        if report["violations"]:
            print("检测到不允许的改动：", file=sys.stderr)
            for item in report["violations"]:
                print(f"- {item['path']} ({item['category']})", file=sys.stderr)
        else:
            print("PR scope 校验通过。")
    return 1 if report["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
