from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.docs_guard import validate_markdown_links, validate_python_sources


class DocsGuardTests(unittest.TestCase):
    def test_detects_missing_markdown_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            markdown = repo / "README.md"
            markdown.write_text("[bad](./missing.md)\n", encoding="utf-8")
            with mock.patch("scripts.docs_guard.git_ls_files", return_value=["README.md"]):
                errors = validate_markdown_links(repo)
        self.assertEqual(len(errors), 1)
        self.assertIn("不存在", errors[0])

    def test_skips_deleted_tracked_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with mock.patch("scripts.docs_guard.git_ls_files", return_value=["docs/specs/FR-0001-example/TODO.md"]):
                errors = validate_markdown_links(repo)
        self.assertEqual(errors, [])

    def test_detects_python_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            scripts_dir = repo / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "broken.py").write_text("def broken(:\n", encoding="utf-8")
            errors = validate_python_sources(repo)
        self.assertEqual(len(errors), 1)
        self.assertIn("语法错误", errors[0])


if __name__ == "__main__":
    unittest.main()
