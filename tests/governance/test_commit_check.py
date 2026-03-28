from __future__ import annotations

import unittest

from scripts.commit_check import validate_message


class CommitCheckTests(unittest.TestCase):
    def test_accepts_chinese_conventional_commit(self) -> None:
        self.assertEqual(validate_message("feat: 增加治理入口"), [])

    def test_rejects_missing_chinese(self) -> None:
        errors = validate_message("feat: add governance entry")
        self.assertTrue(any("中文" in error for error in errors))

    def test_rejects_invalid_format(self) -> None:
        errors = validate_message("增加治理入口")
        self.assertTrue(any("Conventional Commits" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
