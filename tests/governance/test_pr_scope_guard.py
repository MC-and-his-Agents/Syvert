from __future__ import annotations

import unittest

from scripts.pr_scope_guard import build_report


class PrScopeGuardTests(unittest.TestCase):
    def test_governance_allows_formal_spec_suite(self) -> None:
        report = build_report(
            "governance",
            [
                "scripts/pr_guardian.py",
                "docs/specs/FR-0001-governance-stack-v1/spec.md",
                "docs/specs/FR-0001-governance-stack-v1/plan.md",
                "docs/specs/FR-0001-governance-stack-v1/TODO.md",
            ],
        )
        self.assertEqual(report["violations"], [])

    def test_loom_formal_spec_suite_is_not_swallowed_by_governance_scope(self) -> None:
        report = build_report(
            "governance",
            [
                ".loom/specs/INIT-0001/spec.md",
            ],
        )
        self.assertEqual(report["categories"], ["spec"])
        self.assertEqual(report["violations"], [])

    def test_spec_allows_loom_formal_spec_suite(self) -> None:
        report = build_report(
            "spec",
            [
                ".loom/specs/INIT-0001/spec.md",
                ".loom/specs/INIT-0001/plan.md",
            ],
        )
        self.assertEqual(report["violations"], [])

    def test_implementation_rejects_legacy_todo(self) -> None:
        report = build_report(
            "implementation",
            [
                "src/core/runtime.py",
                "docs/specs/FR-0001-example/TODO.md",
            ],
        )
        self.assertTrue(any(item["path"].endswith("TODO.md") for item in report["violations"]))

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
