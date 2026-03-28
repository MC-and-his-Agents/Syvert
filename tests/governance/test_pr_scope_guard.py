from __future__ import annotations

import unittest

from scripts.pr_scope_guard import build_report


class PrScopeGuardTests(unittest.TestCase):
    def test_implementation_allows_spec_todo(self) -> None:
        report = build_report(
            "implementation",
            [
                "src/core/runtime.py",
                "docs/specs/FR-0001-example/TODO.md",
            ],
        )
        self.assertEqual(report["violations"], [])

    def test_docs_rejects_governance(self) -> None:
        report = build_report(
            "docs",
            [
                "docs/process/delivery-funnel.md",
            ],
        )
        self.assertEqual(len(report["violations"]), 1)


if __name__ == "__main__":
    unittest.main()
