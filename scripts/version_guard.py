#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import REPO_ROOT


RELEASE_FILE_RE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.md$")
TRUTH_HEADING_RE = re.compile(
    r"^## (Published truth carrier|当前发布完成真相|当前发布与 closeout 状态|当前发布状态|当前收口事实|完成依据)$",
    re.MULTILINE,
)
PUBLICATION_MARKERS = (
    "GitHub Release",
    "tag target",
    "annotated tag",
    "published at",
    "发布完成",
)
FORBIDDEN_POSITIONING_PHRASES = (
    "Application Capability Expansion",
    "Syvert Application Platform GA",
    "应用平台 GA",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_file(repo_root: Path, relative_path: str, errors: list[str]) -> Path:
    path = repo_root / relative_path
    if not path.exists():
        errors.append(f"缺少版本管理必需文件：`{relative_path}`")
    return path


def contains_all(content: str, required: tuple[str, ...]) -> list[str]:
    return [item for item in required if item not in content]


def validate_release_filename_and_title(release_file: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    relative_path = release_file.relative_to(repo_root)
    match = RELEASE_FILE_RE.match(release_file.name)
    if not match:
        errors.append(f"`{relative_path}` 必须使用 `vMAJOR.MINOR.PATCH.md` 命名")
        return errors

    version = release_file.stem
    title = read_text(release_file).splitlines()[0].strip()
    expected_title = f"# Release {version}"
    if title != expected_title:
        errors.append(f"`{relative_path}` 标题必须是 `{expected_title}`")
    return errors


def validate_release_truth_carrier(release_file: Path, repo_root: Path) -> list[str]:
    content = read_text(release_file)
    relative_path = release_file.relative_to(repo_root)
    has_publication_claim = any(marker in content for marker in PUBLICATION_MARKERS)
    if has_publication_claim and not TRUTH_HEADING_RE.search(content):
        return [f"`{relative_path}` 声明发布 / tag / GitHub Release 事实时必须有 published truth carrier 类章节"]
    return []


def validate_release_docs(repo_root: Path) -> list[str]:
    errors: list[str] = []
    releases_dir = repo_root / "docs/releases"
    template = releases_dir / "_template.md"
    readme = releases_dir / "README.md"

    if not releases_dir.exists():
        return ["缺少 release 索引目录：`docs/releases`"]

    if not template.exists():
        errors.append("缺少 release 模板：`docs/releases/_template.md`")
    else:
        template_content = read_text(template)
        missing = contains_all(
            template_content,
            (
                "## 版本管理",
                "版本类型：major / minor / patch",
                "是否改变公共 contract：是 / 否",
                "是否需要 tag / GitHub Release：是 / 否",
                "published truth carrier",
                "docs/process/version-management.md",
            ),
        )
        for item in missing:
            errors.append(f"`docs/releases/_template.md` 缺少版本管理字段：`{item}`")

    if not readme.exists():
        errors.append("缺少 release 索引说明：`docs/releases/README.md`")
    elif "version-management.md" not in read_text(readme):
        errors.append("`docs/releases/README.md` 必须引用 `docs/process/version-management.md`")

    release_files = sorted(path for path in releases_dir.glob("v*.md") if path.is_file())
    if not release_files:
        errors.append("`docs/releases/` 至少应包含一个 `vMAJOR.MINOR.PATCH.md` release 索引")
    for release_file in release_files:
        errors.extend(validate_release_filename_and_title(release_file, repo_root))
        errors.extend(validate_release_truth_carrier(release_file, repo_root))

    return errors


def validate_version_management_doc(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = require_file(repo_root, "docs/process/version-management.md", errors)
    if not path.exists():
        return errors

    content = read_text(path)
    required = (
        "vMAJOR.MINOR.PATCH",
        "v1.10.0",
        "v1.9.0",
        "GitHub Release",
        "annotated tag",
        "published truth carrier",
        "runtime schema version",
        "v2.0.0",
        "docs/roadmap-v1-to-v2.md",
        "docs/process/python-packaging.md",
        "Python package",
    )
    for item in contains_all(content, required):
        errors.append(f"`docs/process/version-management.md` 缺少关键版本语义：`{item}`")
    return errors


def validate_python_packaging_doc(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = require_file(repo_root, "docs/process/python-packaging.md", errors)
    if not path.exists():
        return errors

    content = read_text(path)
    required = (
        "package publish 不是 release 完成的默认条件",
        "Python package version 必须从 Git tag 派生",
        "禁止在 `syvert/__init__.py` 手写",
        "pyproject.toml",
        "python -m build",
        "GitHub Release",
        "PyPI / GitHub Packages 发布必须作为独立 FR 批准",
    )
    for item in contains_all(content, required):
        errors.append(f"`docs/process/python-packaging.md` 缺少 Python packaging 关键语义：`{item}`")
    return errors


def validate_roadmap_refs(repo_root: Path) -> list[str]:
    errors: list[str] = []
    roadmap_v0 = require_file(repo_root, "docs/roadmap-v0-to-v1.md", errors)
    roadmap_v1 = require_file(repo_root, "docs/roadmap-v1-to-v2.md", errors)

    if roadmap_v0.exists():
        content = read_text(roadmap_v0)
        for item in ("docs/process/version-management.md", "docs/roadmap-v1-to-v2.md", "v1.0.0"):
            if item not in content:
                errors.append(f"`docs/roadmap-v0-to-v1.md` 缺少版本路线引用：`{item}`")

    if roadmap_v1.exists():
        content = read_text(roadmap_v1)
        for item in ("docs/process/version-management.md", "Stabilization Gate", "v1.10", "runtime capability contract"):
            if item not in content:
                errors.append(f"`docs/roadmap-v1-to-v2.md` 缺少 v1.x 到 v2.0.0 关键语义：`{item}`")

    return errors


def validate_workflow(repo_root: Path) -> list[str]:
    workflow = require_file(repo_root, ".github/workflows/version-guard.yml", [])
    if not workflow.exists():
        return ["缺少 CI 门禁：`.github/workflows/version-guard.yml`"]
    content = read_text(workflow)
    missing = contains_all(
        content,
        ("scripts/version_guard.py", "pull_request", "docs/releases/**", "docs/process/python-packaging.md"),
    )
    return [f"`.github/workflows/version-guard.yml` 缺少：`{item}`" for item in missing]


def validate_forbidden_positioning(repo_root: Path) -> list[str]:
    errors: list[str] = []
    checked_paths = (
        repo_root / "vision.md",
        repo_root / "docs/roadmap-v0-to-v1.md",
        repo_root / "docs/roadmap-v1-to-v2.md",
        repo_root / "docs/process/version-management.md",
    )
    for path in checked_paths:
        if not path.exists():
            continue
        content = read_text(path)
        relative_path = path.relative_to(repo_root)
        for phrase in FORBIDDEN_POSITIONING_PHRASES:
            if phrase in content:
                errors.append(f"`{relative_path}` 不应使用含混应用化定位短语：`{phrase}`")
    return errors


def validate_repository(repo_root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_version_management_doc(repo_root))
    errors.extend(validate_python_packaging_doc(repo_root))
    errors.extend(validate_roadmap_refs(repo_root))
    errors.extend(validate_release_docs(repo_root))
    errors.extend(validate_workflow(repo_root))
    errors.extend(validate_forbidden_positioning(repo_root))
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 Syvert 版本语义、release 索引与 CI 门禁约束。")
    parser.add_argument("--mode", choices=("ci", "local"), default="local")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    errors = validate_repository(repo_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("version-guard 通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
