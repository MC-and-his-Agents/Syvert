#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import sys
from pathlib import Path

from scripts.common import REPO_ROOT, git_ls_files


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PATH_RE = re.compile(
    r"(?<![A-Za-z0-9._/-])("
    r"AGENTS\.md|vision\.md|adapter-sdk\.md|framework-positioning\.md|code_review\.md|spec_review\.md|"
    r"docs/[A-Za-z0-9._/-]+|scripts/[A-Za-z0-9._/-]+\.py|\.github/[A-Za-z0-9._/-]+|\.githooks/[A-Za-z0-9._/-]+"
    r")(?![A-Za-z0-9._/-])"
)


def tracked_markdown_files(repo_root: Path) -> list[Path]:
    files = git_ls_files(["*.md", "docs/**/*.md"], repo=repo_root)
    ignored_prefixes = (
        "tests/governance/fixtures/",
    )
    filtered = [item for item in files if not item.startswith(ignored_prefixes)]
    return sorted({repo_root / item for item in filtered})


def normalize_ref(source_file: Path, raw_ref: str, repo_root: Path) -> Path | None:
    value = raw_ref.split("#", 1)[0].rstrip("/")
    if not value:
        return None
    if value.startswith(("http://", "https://", "mailto:")):
        return None
    if value.startswith("/"):
        return Path(value)
    if value.startswith("./") or value.startswith("../"):
        return (source_file.parent / value).resolve()
    return (repo_root / value).resolve()


def validate_markdown_links(repo_root: Path) -> list[str]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    for markdown_file in tracked_markdown_files(repo_root):
        content = markdown_file.read_text(encoding="utf-8")
        refs: list[str] = []
        refs.extend(match.group(1) for match in LINK_RE.finditer(content))
        refs.extend(match.group(1) for match in PATH_RE.finditer(content))
        for ref in refs:
            if "*" in ref or "XXXX" in ref:
                continue
            resolved = normalize_ref(markdown_file, ref, repo_root)
            if resolved is None:
                continue
            try:
                resolved.relative_to(repo_root)
            except ValueError:
                errors.append(f"{markdown_file}: 引用了仓库外路径 `{ref}`")
                continue
            if not resolved.exists():
                errors.append(f"{markdown_file}: 引用了不存在的路径 `{ref}`")
    return errors


def validate_python_sources(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((repo_root / "scripts").rglob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{path}: Python 语法错误: {exc.msg}")
    return errors


def validate_json_files(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((repo_root / "scripts").rglob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: JSON 语法错误: {exc}")
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验文档链接、路径引用和治理脚本基础语法。")
    parser.add_argument("--mode", choices=("ci", "pre-commit"), default="ci")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.repo_root).resolve()

    errors = []
    errors.extend(validate_python_sources(root))
    errors.extend(validate_json_files(root))
    errors.extend(validate_markdown_links(root))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("docs-guard 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
