#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import re

from scripts.common import REPO_ROOT, git_changed_files, has_chinese, run


CC_REGEX = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._/-]+\))?: .+$"
)


def validate_message(message: str) -> list[str]:
    errors: list[str] = []
    if not CC_REGEX.match(message):
        errors.append("提交信息必须符合 Conventional Commits 规范，例如 `feat: 增加某项能力`。")
    if not has_chinese(message):
        errors.append("提交信息必须包含中文。")
    return errors


def read_messages_from_range(base_ref: str, head_ref: str) -> list[str]:
    completed = run(["git", "log", "--format=%s", f"{base_ref}..{head_ref}"], cwd=REPO_ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or f"无法读取提交范围 {base_ref}..{head_ref}")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验中文 Conventional Commits。")
    parser.add_argument("--mode", choices=("commit-msg", "pr"))
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--message-file", help="commit-msg hook 传入的提交信息文件")
    source.add_argument("--commit-msg-file", help="与 --message-file 等价的兼容参数")
    source.add_argument("--message", action="append", help="直接提供待校验的提交信息，可重复传入")
    source.add_argument("--stdin", action="store_true", help="从标准输入逐行读取提交信息")
    source.add_argument("--base-ref", help="与 --head-ref 组合，校验一个 commit range")
    source.add_argument("--base-sha", help="与 --head-sha 组合，校验一个 commit range")
    parser.add_argument("--head-ref", default="HEAD", help="commit range 的头部引用，默认 HEAD")
    parser.add_argument("--head-sha", help="与 --base-sha 组合，校验一个 commit range")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    messages: list[str]

    message_file = args.message_file or args.commit_msg_file
    base_ref = args.base_ref or args.base_sha
    head_ref = args.head_ref if args.base_ref else (args.head_sha or args.head_ref)

    if message_file:
        messages = [Path(message_file).read_text(encoding="utf-8").strip()]
    elif args.message:
        messages = [message.strip() for message in args.message if message.strip()]
    elif args.stdin:
        messages = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]
    else:
        messages = read_messages_from_range(base_ref, head_ref)

    if not messages:
        print("未检测到需要校验的提交信息。")
        return 0

    failures = False
    for message in messages:
        errors = validate_message(message)
        if errors:
            failures = True
            print(f"提交信息不合规: {message}", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)

    if failures:
        return 1

    print(f"已校验 {len(messages)} 条提交信息，全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
