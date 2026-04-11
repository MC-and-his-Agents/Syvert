#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import re

from scripts.common import REPO_ROOT, git_changed_files
from scripts.policy.policy import classify_paths, formal_spec_dirs, spec_suite_policy


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验正式规约套件与 spec 边界。")
    parser.add_argument("--mode", choices=("ci", "pre-commit"), default="ci")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--all", action="store_true", help="校验仓库内所有正式规约套件")
    parser.add_argument("--base-ref", help="用于比较变更的基线引用")
    parser.add_argument("--base-sha", help="与 --head-sha 组合使用")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--head-sha", help="与 --base-sha 组合使用")
    parser.add_argument("--staged-only", action="store_true")
    return parser.parse_args(argv)


def heading_exists(text: str, heading: str) -> bool:
    return heading in text


def validate_suite(fr_dir: Path) -> list[str]:
    errors: list[str] = []
    policy = spec_suite_policy()

    for filename in policy["required_files"]:
        target = fr_dir / filename
        if not target.exists():
            errors.append(f"{fr_dir}: 缺少 `{filename}`")
            continue
        if not target.read_text(encoding="utf-8").strip():
            errors.append(f"{fr_dir}: `{filename}` 不能为空")

    legacy_todo = fr_dir / "TODO.md"
    if legacy_todo.exists():
        errors.append(f"{legacy_todo}: legacy `TODO.md` 已退出正式治理流，请删除该文件。")

    spec_path = fr_dir / "spec.md"
    plan_path = fr_dir / "plan.md"
    if not spec_path.exists() or not plan_path.exists():
        return errors

    spec_text = spec_path.read_text(encoding="utf-8")
    plan_text = plan_path.read_text(encoding="utf-8")

    for heading in policy["spec_required_headings"]:
        if not heading_exists(spec_text, heading):
            errors.append(f"{spec_path}: 缺少 `{heading}`")
    for token in ("Given", "When", "Then"):
        if token not in spec_text:
            errors.append(f"{spec_path}: 未看到 `{token}` 场景")
    for heading in policy["plan_required_headings"]:
        if not heading_exists(plan_text, heading):
            errors.append(f"{plan_path}: 缺少 `{heading}`")

    suite_text = f"{spec_text}\n{plan_text}"
    if re.search(r"(contract|契约|payload|协议|接口)", suite_text, re.IGNORECASE):
        contracts_dir = fr_dir / "contracts"
        if not contracts_dir.exists():
            errors.append(f"{fr_dir}: 涉及契约/协议，但缺少 `contracts/`")
    if re.search(r"(data-model|schema|表结构|持久化|实体)", suite_text, re.IGNORECASE):
        if not (fr_dir / "data-model.md").exists():
            errors.append(f"{fr_dir}: 涉及共享数据模型，但缺少 `data-model.md`")
    if re.search(r"(risk|回滚|安全|账号|并发|不可逆|迁移)", suite_text, re.IGNORECASE):
        if not (fr_dir / "risks.md").exists():
            errors.append(f"{fr_dir}: 涉及高风险内容，但缺少 `risks.md`")

    return errors


def validate_changed_paths(repo_root: Path, changed_paths: list[str]) -> list[str]:
    errors: list[str] = []
    classified = classify_paths(changed_paths)
    categories = {item.category for item in classified}

    if "spec" in categories and "implementation" in categories:
        errors.append("正式 spec 变更不得与实现代码混在同一 PR。")
    if "governance" in categories and "implementation" in categories:
        errors.append("治理基线变更不得与实现代码混在同一 PR。")

    for fr_dir in formal_spec_dirs(changed_paths):
        if fr_dir.name == "_template":
            continue
        errors.extend(validate_suite(repo_root / fr_dir))
    return errors


def all_formal_spec_dirs(repo_root: Path) -> list[Path]:
    specs_root = repo_root / "docs" / "specs"
    if not specs_root.exists():
        return []
    return sorted(path for path in specs_root.iterdir() if path.is_dir() and path.name.startswith("FR-"))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []

    if args.all:
        for fr_dir in all_formal_spec_dirs(repo_root):
            errors.extend(validate_suite(fr_dir))
    else:
        base_ref = args.base_ref or args.base_sha
        head_ref = args.head_sha or args.head_ref
        if args.staged_only:
            changed = []
        elif base_ref:
            changed = git_changed_files(base_ref, head_ref, repo=repo_root)
        else:
            changed = []
        if changed:
            errors.extend(validate_changed_paths(repo_root, changed))
        else:
            for fr_dir in all_formal_spec_dirs(repo_root):
                errors.extend(validate_suite(fr_dir))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("spec-guard 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
