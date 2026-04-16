from __future__ import annotations

import ast
from pathlib import Path
import tempfile
import unittest

from syvert.platform_leakage import (
    DEFAULT_BOUNDARY_SCOPE,
    build_platform_leakage_payload,
    run_platform_leakage_check,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TARGETS = (
    "syvert/runtime.py",
    "syvert/registry.py",
    "syvert/version_gate.py",
)


class PlatformLeakageTests(unittest.TestCase):
    def test_build_payload_passes_for_current_shared_files(self) -> None:
        payload = build_platform_leakage_payload(
            version="v0.2.0",
            repo_root=REPO_ROOT,
        )

        self.assertEqual(payload["boundary_scope"], list(DEFAULT_BOUNDARY_SCOPE))
        self.assertEqual(payload["verdict"], "pass")
        self.assertEqual(payload["findings"], [])
        self.assertGreaterEqual(len(payload["evidence_refs"]), len(SCAN_TARGETS))

    def test_run_check_passes_for_current_shared_files(self) -> None:
        report = run_platform_leakage_check(
            version="v0.2.0",
            repo_root=REPO_ROOT,
        )

        self.assertEqual(report["source"], "platform_leakage")
        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["report_verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])
        self.assertEqual(report["details"]["boundary_scope"], list(DEFAULT_BOUNDARY_SCOPE))

    def test_run_check_fails_closed_when_boundary_scope_is_incomplete(self) -> None:
        report = run_platform_leakage_check(
            version="v0.2.0",
            repo_root=REPO_ROOT,
            boundary_scope=[boundary for boundary in DEFAULT_BOUNDARY_SCOPE if boundary != "version_gate_logic"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_boundary_scope", {item["code"] for item in report["details"]["failures"]})

    def test_run_check_fails_closed_when_boundary_scope_has_extra_boundary(self) -> None:
        report = run_platform_leakage_check(
            version="v0.2.0",
            repo_root=REPO_ROOT,
            boundary_scope=[*DEFAULT_BOUNDARY_SCOPE, "adapter_private_impl"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("unexpected_boundary_scope", {item["code"] for item in report["details"]["failures"]})

    def test_run_check_detects_hardcoded_platform_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if adapter_key == "xhs":\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["details"]["report_verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})
        self.assertIn("core_runtime", {item["boundary"] for item in report["details"]["findings"]})

    def test_run_check_detects_multiline_hardcoded_platform_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n'
                    "    if (\n"
                    "        adapter_key\n"
                    '        == "weibo"\n'
                    "    ):\n"
                    "        return None\n\n",
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_detects_hardcoded_platform_branch_with_adapter_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter = adapter_key\n    if adapter == "xhs":\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_detects_return_expression_platform_compare(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    return adapter_key == "xhs"\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_does_not_report_non_platform_string_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    if adapter_key == "unknown":\n        return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_does_not_report_non_platform_match_branch(self) -> None:
        if getattr(ast, "Match", None) is None:
            self.skipTest("pattern matching is unavailable in this Python runtime")
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    match adapter_key:\n        case "unknown":\n            return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_does_not_report_platform_fragment_compare_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    if adapter_key == "aweme-detail":\n        return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})
        self.assertNotIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_does_not_report_platform_fragment_match_branch(self) -> None:
        if getattr(ast, "Match", None) is None:
            self.skipTest("pattern matching is unavailable in this Python runtime")
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    match adapter_key:\n        case "a_bogus":\n            return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})
        self.assertNotIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_raise_expression_platform_compare(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    raise RuntimeError(adapter_key == "xhs")\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_detects_expression_statement_platform_compare(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    adapter_key == "xhs"\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_does_not_whitelist_normalized_platform_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if normalized.platform == "xhs":\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_error_details_platform_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if error.details.get("platform") == "douyin":\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_error_details_platform_match_branch(self) -> None:
        if getattr(ast, "Match", None) is None:
            self.skipTest("pattern matching is unavailable in this Python runtime")
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    match error.details.get("platform"):\n        case "douyin":\n            return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_allows_error_details_platform_carrier_without_branching(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    platform_name = adapter_error.details.get("platform")\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_detects_platform_specific_field_leak(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/registry.py": (
                    "MISSING = object()\n",
                    'MISSING = object()\nAWEME_FIELD = "aweme_id"\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"adapter_registry"})

    def test_run_check_detects_shared_platform_collection_constant(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    'ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}\n',
                    'ALLOWED_CONTENT_TYPES = {"video", "image_post", "mixed_media", "unknown"}\n'
                    'SUPPORTED_PLATFORMS = {"xhs", "douyin"}\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_detects_shared_platform_semantic_in_return_value(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    "    adapter_key, capability = extract_request_context(request)\n"
                    '    return {"default_platform": "xhs"}\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_detects_shared_platform_semantic_in_raise_message(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    raise RuntimeError("xhs only")\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_detects_shared_platform_semantic_in_function_default(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "def extract_request_context(request: Any) -> tuple[str, str]:\n",
                    'def extract_request_context(request: Any, default_platform: str = "xhs") -> tuple[str, str]:\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_detects_platform_specific_url_fragment(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/registry.py": (
                    "MISSING = object()\n",
                    'MISSING = object()\nSHARED_ENDPOINT = "https://www.douyin.com/aweme/v1/web/detail"\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"adapter_registry"})

    def test_run_check_ignores_docstring_platform_fragments(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "def extract_request_context(request: Any) -> tuple[str, str]:\n",
                    'def extract_request_context(request: Any) -> tuple[str, str]:\n'
                    '    """see https://www.douyin.com/aweme/v1/web/detail and selector .note-item"""\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_detects_platform_specific_selector_fragment(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/registry.py": (
                    "MISSING = object()\n",
                    'MISSING = object()\nDETAIL_SELECTOR = "[data-xhs-note-id] .note-item"\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"adapter_registry"})

    def test_run_check_detects_platform_specific_signature_fragment(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/registry.py": (
                    "MISSING = object()\n",
                    'MISSING = object()\nSHARED_SIGNATURE = "X-Bogus"\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"adapter_registry"})

    def test_run_check_detects_single_platform_shared_semantic(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/version_gate.py": (
                    "FAIL_VERDICT = \"fail\"\n",
                    'FAIL_VERDICT = "fail"\nDEFAULT_SHARED_RUNTIME = "xhs"\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"version_gate_logic"})

    def test_run_check_detects_non_reference_platform_literal_in_shared_semantic(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/version_gate.py": (
                    'FAIL_VERDICT = "fail"\n',
                    'FAIL_VERDICT = "fail"\nDEFAULT_SHARED_RUNTIME = "weibo"\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"version_gate_logic"})

    def test_run_check_does_not_whitelist_reference_pair_outside_frozen_constant(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/version_gate.py": (
                    'FAIL_VERDICT = "fail"\n',
                    'FAIL_VERDICT = "fail"\nSHARED_ROUTING = ("xhs", "douyin")\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"version_gate_logic"})

    def test_run_check_fails_closed_on_parse_failure(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    "    adapter_key, capability = extract_request_context(request)\n    if (\n",
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(report["details"]["report_verdict"], "fail")
        self.assertEqual({item["code"] for item in report["details"]["findings"]}, {"scan_parse_failure"})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"core_runtime"})

    def test_run_check_ignores_adapter_private_and_research_files(self) -> None:
        report = self.run_with_fixture(
            {},
            extra_files={
                "syvert/adapters/xhs.py": 'if platform == "xhs":\n    return {"note_id": "1"}\n',
                "docs/research/platforms/xhs-content-detail.md": "aweme_id note_id sign_base_url\n",
            },
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def run_with_fixture(
        self,
        replacements: dict[str, tuple[str, str]],
        *,
        extra_files: dict[str, str] | None = None,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            for relative_name in SCAN_TARGETS:
                source_path = REPO_ROOT / relative_name
                target_path = fixture_root / relative_name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                contents = source_path.read_text(encoding="utf-8")
                old, new = replacements.get(relative_name, ("", ""))
                if old:
                    self.assertIn(old, contents)
                    contents = contents.replace(old, new, 1)
                target_path.write_text(contents, encoding="utf-8")

            for relative_name, contents in (extra_files or {}).items():
                target_path = fixture_root / relative_name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(contents, encoding="utf-8")

            return run_platform_leakage_check(
                version="v0.2.0",
                repo_root=fixture_root,
            )


if __name__ == "__main__":
    unittest.main()
