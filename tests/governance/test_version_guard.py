from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.version_guard import validate_repository


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_valid_version_fixture(repo: Path) -> None:
    write(
        repo / "docs/process/version-management.md",
        """# Syvert Version Management

vMAJOR.MINOR.PATCH
v1.10.0
v1.9.0
GitHub Release
annotated tag
published truth carrier
runtime schema version
v2.0.0
docs/roadmap-v1-to-v2.md
docs/process/python-packaging.md
Python package
""",
    )
    write(
        repo / "docs/process/python-packaging.md",
        """# Syvert Python Packaging

package publish 不是 release 完成的默认条件
Python package version 必须从 Git tag 派生
禁止在 `syvert/__init__.py` 手写
pyproject.toml
python -m build
GitHub Release
PyPI / GitHub Packages 发布必须作为独立 FR 批准
""",
    )
    write(
        repo / "docs/roadmap-v0-to-v1.md",
        """# Roadmap

docs/process/version-management.md
docs/roadmap-v1-to-v2.md
v1.0.0
""",
    )
    write(
        repo / "docs/roadmap-v1-to-v2.md",
        """# Roadmap

docs/process/version-management.md
Stabilization Gate
v1.10
runtime capability contract
""",
    )
    write(
        repo / "docs/releases/README.md",
        """# Releases

version-management.md
""",
    )
    write(
        repo / "docs/releases/_template.md",
        """# Release vX.Y.Z

## 版本管理

- 版本类型：major / minor / patch
- 是否改变公共 contract：是 / 否
- 是否需要 tag / GitHub Release：是 / 否
- published truth carrier
- docs/process/version-management.md
""",
    )
    write(repo / "docs/releases/v1.0.0.md", "# Release v1.0.0\n\n## 目标\n")
    write(
        repo / ".github/workflows/version-guard.yml",
        """name: Version Guard

on:
  pull_request:
    paths:
      - "docs/releases/**"
      - "docs/process/python-packaging.md"

jobs:
  version-guard:
    steps:
      - run: python3 scripts/version_guard.py --mode ci
""",
    )
    write(repo / "vision.md", "# Vision\n")


class VersionGuardTests(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_version_fixture(repo)

            errors = validate_repository(repo)

        self.assertEqual(errors, [])

    def test_missing_python_packaging_doc_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_version_fixture(repo)
            (repo / "docs/process/python-packaging.md").unlink()

            errors = validate_repository(repo)

        self.assertTrue(any("python-packaging.md" in error for error in errors))

    def test_workflow_must_watch_python_packaging_doc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_version_fixture(repo)
            workflow = (repo / ".github/workflows/version-guard.yml").read_text(encoding="utf-8")
            workflow = workflow.replace('      - "docs/process/python-packaging.md"\n', "")
            (repo / ".github/workflows/version-guard.yml").write_text(workflow, encoding="utf-8")

            errors = validate_repository(repo)

        self.assertTrue(any("docs/process/python-packaging.md" in error for error in errors))

    def test_version_management_must_reference_packaging_doc(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_valid_version_fixture(repo)
            content = (repo / "docs/process/version-management.md").read_text(encoding="utf-8")
            content = content.replace("docs/process/python-packaging.md\n", "")
            (repo / "docs/process/version-management.md").write_text(content, encoding="utf-8")

            errors = validate_repository(repo)

        self.assertTrue(any("docs/process/python-packaging.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
