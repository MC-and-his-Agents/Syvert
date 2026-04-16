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

    def test_run_check_fails_closed_when_boundary_scope_order_differs(self) -> None:
        report = run_platform_leakage_check(
            version="v0.2.0",
            repo_root=REPO_ROOT,
            boundary_scope=list(reversed(DEFAULT_BOUNDARY_SCOPE)),
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("boundary_scope_order_mismatch", {item["code"] for item in report["details"]["failures"]})

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

    def test_run_check_detects_alias_wrapped_platform_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    current = adapter_key\n    if current == "xhs":\n        return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_loop_alias_platform_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    for current in [adapter_key]:\n        if current == "xhs":\n            return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_startswith_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    if adapter_key.startswith("xhs"):\n        return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_carrier_branch_without_inline_literal(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if normalized.get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_carrier_alias_branch_without_inline_literal(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    carrier = normalized\n    if carrier.get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_error_details_alias_branch_without_inline_literal(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    details = error.details\n    if details.get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

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

    def test_run_check_detects_plain_single_platform_constant(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/version_gate.py": (
                    '_REAL_REGRESSION_ALLOWED_ERROR_CATEGORIES = frozenset({"invalid_input", "platform"})\n',
                    '_REAL_REGRESSION_ALLOWED_ERROR_CATEGORIES = frozenset({"invalid_input", "platform"})\nPRIMARY = "xhs"\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})
        self.assertEqual({item["boundary"] for item in report["details"]["findings"]}, {"version_gate_logic"})

    def test_run_check_allows_normalized_platform_carrier_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    return {"normalized": {"platform": "xhs"}}\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_allows_normalized_platform_carrier_subscript_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    normalized["platform"] = "xhs"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_allows_error_details_platform_carrier_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    payload = {"error": {"details": {"platform": "xhs"}}}\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_allows_error_details_platform_carrier_subscript_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    details = error.details\n    details["platform"] = "xhs"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_allows_adapter_error_details_platform_subscript_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_error.details["platform"] = "xhs"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_detects_function_decorator_platform_metadata(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "def default_task_id_factory() -> str:\n",
                    '@platform_only("xhs")\ndef default_task_id_factory() -> str:\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_class_metadata_platform_semantic(self) -> None:
        report = self.run_with_fixture(
            {},
            append_files={
                "syvert/runtime.py": '\n\n@platform_only("xhs")\nclass PlatformRuntime:\n    pass\n',
            },
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_shared_result_field(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    return {"normalized": {"xhs_extra": "1"}}\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_shared_error_details_field(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    return {"error": {"details": {"xhs_extra": "1"}}}\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_shared_result_field_via_normalized_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    normalized_payload = payload["normalized"]\n    normalized_payload["xhs_extra"] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_shared_result_field_via_neutral_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    bucket = payload["normalized"]\n    bucket["xhs_extra"] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_shared_result_field_via_same_line_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    bucket = payload["normalized"]; bucket["xhs_extra"] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_does_not_whitelist_plain_details_container(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    payload["details"]["platform"] = "xhs"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("single_platform_shared_semantic", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_conditional_error_details_alias_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if allow:\n        details = error.details\n    else:\n        details = {}\n    if details.get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_ifexp_error_details_alias_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    details = error.details if allow else {}\n    if details.get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_conditional_shared_result_alias_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if allow:\n        bucket = payload["normalized"]\n    else:\n        bucket = {}\n    bucket["xhs_extra"] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_branch_with_walrus_carrier_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if (carrier := normalized).get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_indirect_platform_specific_shared_result_key(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    key = "xhs_extra"\n    normalized[key] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertTrue(
            {"platform_specific_field_leak", "single_platform_shared_semantic"}
            & {item["code"] for item in report["details"]["findings"]}
        )

    def test_run_check_detects_indirect_normalized_platform_get_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    platform_key = "platform"\n    if normalized.get(platform_key) == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_indirect_error_details_platform_subscript_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    platform_key = "platform"\n    if error.details[platform_key] == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_does_not_report_platform_alias_from_another_function_scope(self) -> None:
        report = self.run_with_fixture(
            {},
            append_files={
                "syvert/runtime.py": (
                    "\n\ndef seed_alias(adapter_key):\n"
                    "    current = adapter_key\n"
                    "    return current\n"
                    "\n\ndef unrelated(current):\n"
                    '    if current == "xhs":\n'
                    "        return None\n"
                    "    return current\n"
                )
            },
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_does_not_report_reassigned_platform_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    current = adapter_key\n    current = "unknown"\n    if current == "xhs":\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_detects_conditional_platform_alias_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if allow:\n        current = adapter_key\n    else:\n        current = "unknown"\n    if current == "xhs":\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_ifexp_platform_alias_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    current = adapter_key if allow else "unknown"\n    if current == "xhs":\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_walrus_then_later_error_details_alias_branch(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if (details := error.details):\n        pass\n    if details.get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_allows_walrus_then_later_error_details_platform_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if (details := error.details):\n        pass\n    details["platform"] = "xhs"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_detects_mixed_raw_normalized_alias_platform_write(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if allow:\n        bucket = payload["normalized"]\n    else:\n        bucket = payload["raw"]\n    bucket["platform"] = "xhs"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_computed_platform_specific_shared_result_key(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    key = f"{current_platform}_extra"\n    normalized[key] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_percent_formatted_platform_specific_shared_result_key(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    key = "%s_extra" % current_platform\n    normalized[key] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_computed_platform_specific_error_details_key(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    key = f"{current_platform}_extra"\n    details = error.details\n    details[key] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_dot_format_platform_specific_error_details_key(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    key = "{}_extra".format(current_platform)\n    details = error.details\n    details[key] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_fail_closes_on_dead_branch_alias_union(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    if False:\n        bucket = payload["normalized"]\n    else:\n        bucket = {}\n    bucket["xhs_extra"] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_raw_field_via_neutral_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    bucket = payload["raw"]\n    bucket["douyin_extra"] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_shared_result_field_via_update(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    normalized.update({"xhs_extra": "1"})\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_specific_shared_result_field_via_setdefault(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    normalized.setdefault("xhs_extra", "1")\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("platform_specific_field_leak", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_allows_neutral_single_character_shared_result_field(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    return {"normalized": {"x": 1}}\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_allows_neutral_x_prefixed_shared_result_field(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    return {"normalized": {"x_trace": 1}}\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_allows_raw_prefixed_local_name_without_real_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    raw_value = {}\n    raw_value["xhs_extra"] = "1"\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_fail_closes_on_malformed_repo_root(self) -> None:
        report = run_platform_leakage_check(
            version="v0.2.0",
            repo_root="\0bad",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("scan_target_unreadable", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_branch_variant_compare(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    if adapter_key == "xhs-main":\n        return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_platform_branch_variant_match(self) -> None:
        if getattr(ast, "Match", None) is None:
            self.skipTest("pattern matching is unavailable in this Python runtime")
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    match adapter_key:\n        case "douyin-prod":\n            return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_detects_match_guard_platform_branch(self) -> None:
        if getattr(ast, "Match", None) is None:
            self.skipTest("pattern matching is unavailable in this Python runtime")
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    adapter_key, capability = extract_request_context(request)\n    match adapter_key:\n        case current if current == "xhs":\n            return None\n\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

    def test_run_check_does_not_report_reassigned_error_details_alias(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    details = error.details\n    details = {}\n    if details.get("platform") == current_platform:\n        return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_does_not_report_normalized_alias_from_another_function_scope(self) -> None:
        report = self.run_with_fixture(
            {},
            append_files={
                "syvert/runtime.py": (
                    "\n\ndef seeded_bucket(payload):\n"
                    '    bucket = payload["normalized"]\n'
                    "    return bucket\n"
                    "\n\ndef unrelated_scope(bucket):\n"
                    '    bucket["xhs_extra"] = "1"\n'
                    "    return bucket\n"
                )
            },
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["findings"], [])

    def test_run_check_detects_normalized_mapping_match_branch(self) -> None:
        if getattr(ast, "Match", None) is None:
            self.skipTest("pattern matching is unavailable in this Python runtime")
        report = self.run_with_fixture(
            {
                "syvert/runtime.py": (
                    "    adapter_key, capability = extract_request_context(request)\n",
                    '    match normalized:\n        case {"platform": "xhs"}:\n            return None\n\n    adapter_key, capability = extract_request_context(request)\n',
                )
            }
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("hardcoded_platform_branch", {item["code"] for item in report["details"]["findings"]})

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

    def test_run_check_does_not_whitelist_semicolon_statement_on_frozen_reference_pair_line(self) -> None:
        report = self.run_with_fixture(
            {
                "syvert/version_gate.py": (
                    "}\n_FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION: dict[str, tuple[str, ...]] = {}\n",
                    '}; SHARED_ROUTING = ("xhs", "douyin")\n_FROZEN_HARNESS_REQUIRED_SAMPLE_IDS_BY_VERSION: dict[str, tuple[str, ...]] = {}\n',
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
        append_files: dict[str, str] | None = None,
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
                contents += (append_files or {}).get(relative_name, "")
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
