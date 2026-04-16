from __future__ import annotations

import unittest
from unittest import mock

from syvert.adapters.douyin import DouyinAdapter, DouyinSessionConfig, default_page_state_transport
from syvert.adapters.xhs import XhsAdapter, XhsSessionConfig
from syvert.runtime import PlatformAdapterError
from syvert.real_adapter_regression import (
    build_real_adapter_regression_payload,
    run_real_adapter_regression,
)
from syvert.version_gate import (
    build_harness_source_report,
    orchestrate_version_gate,
    validate_platform_leakage_source_report,
    validate_real_adapter_regression_source_report,
)


class ShapeContractSpoofAdapter:
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def __init__(self, adapter_key: str) -> None:
        self.adapter_key = adapter_key

    def execute(self, request: object) -> dict[str, object]:
        return {
            "raw": {"spoofed": True, "request_type": type(request).__name__},
            "normalized": {
                "platform": self.adapter_key,
                "content_id": "spoofed-content-id",
                "url": "https://example.com/spoofed",
                "content_type": "video",
                "title": "spoofed-title",
                "description": "spoofed-description",
                "published_at": "2025-01-01T00:00:00Z",
                "author": {
                    "id": "spoofed-author",
                    "display_name": "spoofed-author",
                    "profile_url": None,
                    "avatar_url": None,
                },
                "engagement": {
                    "likes": 1,
                    "comments": 1,
                    "shares": 1,
                    "saves": 1,
                },
                "media": [],
            },
        }


def build_douyin_aweme_detail(
    *,
    aweme_id: str = "7580570616932224282",
    desc: str = "抖音正文",
    preview_title: str = "抖音标题",
    create_time: int = 1764989142,
    digg_count: int = 2871,
    comment_count: int = 220,
    share_count: int = 972,
    collect_count: int = 3220,
    video_url: str = "https://cdn.example/video.mp4",
    cover_url: str = "https://cdn.example/cover.jpg",
) -> dict[str, object]:
    return {
        "aweme_id": aweme_id,
        "aweme_type": 0,
        "desc": desc,
        "preview_title": preview_title,
        "create_time": create_time,
        "statistics": {
            "digg_count": digg_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "collect_count": collect_count,
        },
        "author": {
            "uid": "author-1",
            "nickname": "抖音作者",
            "avatar_thumb": {
                "url_list": [cover_url],
            },
        },
        "video": {
            "play_addr_h264": {"url_list": [video_url]},
            "cover": {"url_list": [cover_url]},
        },
    }


class RealAdapterRegressionTests(unittest.TestCase):
    def test_build_real_adapter_regression_payload_emits_frozen_matrix(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )

        self.assertEqual(payload["version"], "v0.2.0")
        self.assertEqual(payload["reference_pair"], ["xhs", "douyin"])
        self.assertEqual(payload["operation"], "content_detail_by_url")
        self.assertEqual(payload["target_type"], "url")
        self.assertEqual(
            payload["evidence_refs"],
            [
                "regression:xhs:success",
                "regression:xhs:invalid-input",
                "regression:douyin:success",
                "regression:douyin:platform",
            ],
        )
        self.assertEqual(payload["adapter_results"][0]["adapter_key"], "xhs")
        self.assertEqual(payload["adapter_results"][1]["adapter_key"], "douyin")
        self.assertEqual(payload["adapter_results"][0]["cases"][0]["evidence_ref"], "regression:xhs:success")
        self.assertEqual(payload["adapter_results"][1]["cases"][1]["evidence_ref"], "regression:douyin:platform")
        self.assertEqual(payload["adapter_results"][0]["cases"][0]["observed_status"], "success")
        self.assertEqual(payload["adapter_results"][0]["cases"][1]["observed_error_category"], "invalid_input")
        self.assertEqual(payload["adapter_results"][1]["cases"][1]["observed_error_category"], "platform")

    def test_run_real_adapter_regression_returns_pass_source_report(self) -> None:
        report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )

        self.assertEqual(report["source"], "real_adapter_regression")
        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["details"]["semantic_operation"], "content_detail_by_url")
        self.assertEqual(report["details"]["target_type"], "url")

    def test_build_real_adapter_regression_payload_rejects_shape_contract_spoof(self) -> None:
        adapters = self.hermetic_adapters()
        adapters["xhs"] = ShapeContractSpoofAdapter("xhs")

        with self.assertRaisesRegex(ValueError, "仅接受真实参考适配器实现"):
            build_real_adapter_regression_payload(
                version="v0.2.0",
                adapters=adapters,
            )

    def test_run_real_adapter_regression_fails_closed_for_shape_contract_spoof(self) -> None:
        adapters = self.hermetic_adapters()
        adapters["xhs"] = ShapeContractSpoofAdapter("xhs")

        report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=adapters,
        )

        self.assertEqual(report["source"], "real_adapter_regression")
        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(
            report["evidence_refs"],
            ["real_adapter_regression:binding:xhs:invalid_reference_adapter_identity"],
        )
        self.assertIn(
            "invalid_reference_adapter_identity",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_run_real_adapter_regression_fails_closed_when_reference_surface_drifts(self) -> None:
        with mock.patch.object(XhsAdapter, "supported_targets", frozenset({"url", "keyword"})):
            report = run_real_adapter_regression(
                version="v0.2.0",
                adapters=self.hermetic_adapters(),
            )

        self.assertEqual(report["verdict"], "fail")
        self.assertEqual(
            report["evidence_refs"],
            ["real_adapter_regression:binding:xhs:unexpected_reference_adapter_surface"],
        )
        self.assertIn(
            "unexpected_reference_adapter_surface",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_run_real_adapter_regression_fails_closed_when_douyin_binding_uses_default_page_state_recovery(self) -> None:
        adapters = self.hermetic_adapters()
        adapters["douyin"] = DouyinAdapter(
            session_provider=lambda path: DouyinSessionConfig(
                cookies="a=1; b=2",
                user_agent="Mozilla/5.0 TestAgent",
                verify_fp="verify-1",
                ms_token="ms-token-1",
                webid="webid-1",
                sign_base_url="http://127.0.0.1:8000",
                timeout_seconds=5,
            ),
            sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
            detail_transport=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("detail-failed")),
        )

        report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=adapters,
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "non_hermetic_reference_adapter_binding",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_run_real_adapter_regression_fails_closed_when_douyin_binding_wraps_default_page_state_recovery(self) -> None:
        adapters = self.hermetic_adapters()
        adapters["douyin"] = DouyinAdapter(
            session_provider=lambda path: DouyinSessionConfig(
                cookies="a=1; b=2",
                user_agent="Mozilla/5.0 TestAgent",
                verify_fp="verify-1",
                ms_token="ms-token-1",
                webid="webid-1",
                sign_base_url="http://127.0.0.1:8000",
                timeout_seconds=5,
            ),
            sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
            detail_transport=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("detail-failed")),
            page_state_transport=lambda **kwargs: default_page_state_transport(**kwargs),
        )

        report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=adapters,
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "non_hermetic_reference_adapter_binding",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_run_real_adapter_regression_fails_closed_when_douyin_binding_alias_wraps_default_page_state_recovery(self) -> None:
        alias = default_page_state_transport
        adapters = self.hermetic_adapters()
        adapters["douyin"] = DouyinAdapter(
            session_provider=lambda path: DouyinSessionConfig(
                cookies="a=1; b=2",
                user_agent="Mozilla/5.0 TestAgent",
                verify_fp="verify-1",
                ms_token="ms-token-1",
                webid="webid-1",
                sign_base_url="http://127.0.0.1:8000",
                timeout_seconds=5,
            ),
            sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
            detail_transport=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("detail-failed")),
            page_state_transport=lambda **kwargs: alias(**kwargs),
        )

        report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=adapters,
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "non_hermetic_reference_adapter_binding",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_validate_real_adapter_regression_rejects_missing_observed_error_category(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload["adapter_results"][1]["cases"][1]["observed_error_category"] = None

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("failed_case_without_error_category", {item["code"] for item in report["details"]["failures"]})

    def test_validate_real_adapter_regression_rejects_missing_adapter_result(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload["adapter_results"] = [payload["adapter_results"][0]]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_adapter_result", {item["code"] for item in report["details"]["failures"]})

    def test_validate_real_adapter_regression_rejects_missing_success_coverage(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload["adapter_results"][0]["cases"] = [payload["adapter_results"][0]["cases"][1]]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_success_coverage", {item["code"] for item in report["details"]["failures"]})

    def test_validate_real_adapter_regression_rejects_missing_allowed_failure_coverage(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload["adapter_results"][1]["cases"] = [payload["adapter_results"][1]["cases"][0]]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn(
            "missing_allowed_failure_coverage",
            {item["code"] for item in report["details"]["failures"]},
        )

    def test_validate_real_adapter_regression_rejects_missing_evidence_refs(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload.pop("evidence_refs")

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("missing_evidence_refs", {item["code"] for item in report["details"]["failures"]})

    def test_validate_real_adapter_regression_rejects_missing_case_evidence_ref(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload["adapter_results"][1]["cases"][1]["evidence_ref"] = ""

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("invalid_case_evidence_ref", {item["code"] for item in report["details"]["failures"]})

    def test_validate_real_adapter_regression_rejects_misbound_case_evidence_refs(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload["evidence_refs"] = [
            "regression:xhs:success",
            "regression:xhs:invalid-input",
            "regression:douyin:platform",
            "regression:douyin:success",
        ]

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("case_evidence_refs_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_validate_real_adapter_regression_rejects_frozen_case_matrix_drift(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        payload["adapter_results"][1]["cases"][1]["case_id"] = "douyin-alt-platform"

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("case_matrix_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_validate_real_adapter_regression_rejects_operation_surface_mismatch(self) -> None:
        payload = build_real_adapter_regression_payload(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )

        report = validate_real_adapter_regression_source_report(
            payload,
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            operation="content_detail",
            target_type="url",
        )

        self.assertEqual(report["verdict"], "fail")
        self.assertIn("operation_surface_mismatch", {item["code"] for item in report["details"]["failures"]})

    def test_end_to_end_real_adapter_regression_report_feeds_version_gate(self) -> None:
        regression_report = run_real_adapter_regression(
            version="v0.2.0",
            adapters=self.hermetic_adapters(),
        )
        harness_report = build_harness_source_report(
            self.valid_harness_results(),
            required_sample_ids=["sample-success", "sample-legal-failure"],
            version="v0.2.0",
        )
        leakage_report = validate_platform_leakage_source_report(
            self.valid_platform_leakage_payload(),
            version="v0.2.0",
        )

        report = orchestrate_version_gate(
            version="v0.2.0",
            reference_pair=["xhs", "douyin"],
            harness_report=harness_report,
            real_adapter_regression_report=regression_report,
            platform_leakage_report=leakage_report,
            required_harness_sample_ids=["sample-success", "sample-legal-failure"],
        )

        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["source_reports"]["real_adapter_regression"]["verdict"], "pass")

    @staticmethod
    def hermetic_adapters() -> dict[str, object]:
        xhs_adapter = XhsAdapter(
            session_provider=lambda path: XhsSessionConfig(
                cookies="a=1; b=2",
                user_agent="Mozilla/5.0 TestAgent",
                sign_base_url="http://127.0.0.1:8000",
                timeout_seconds=7,
            ),
            sign_transport=lambda base_url, payload, timeout_seconds: {
                "x_s": "signed-x-s",
                "x_t": "signed-x-t",
                "x_s_common": "signed-x-s-common",
                "x_b3_traceid": "trace-1",
            },
            detail_transport=lambda **kwargs: {
                "success": True,
                "data": {
                    "items": [
                        {
                            "note_card": {
                                "note_id": "66fad51c000000001b0224b8",
                                "type": "video",
                                "title": "测试标题",
                                "desc": "测试正文",
                                "time": 1712304300,
                                "user": {
                                    "user_id": "user-1",
                                    "nickname": "作者甲",
                                    "avatar": "https://cdn.example/avatar.jpg",
                                },
                                "interact_info": {
                                    "liked_count": "11",
                                    "comment_count": "12",
                                    "share_count": "13",
                                    "collected_count": "14",
                                },
                                "image_list": [
                                    {"url_default": "https://cdn.example/image-1.jpg"},
                                    {"url_default": "https://cdn.example/image-2.jpg"},
                                ],
                                "video": {
                                    "consumer": {
                                        "origin_video_key": "video-key-1",
                                    }
                                },
                                "cover": {
                                    "url_default": "https://cdn.example/cover.jpg",
                                },
                            }
                        }
                    ]
                },
            },
        )
        douyin_adapter = DouyinAdapter(
            session_provider=lambda path: DouyinSessionConfig(
                cookies="a=1; b=2",
                user_agent="Mozilla/5.0 TestAgent",
                verify_fp="verify-1",
                ms_token="ms-token-1",
                webid="webid-1",
                sign_base_url="http://127.0.0.1:8000",
                timeout_seconds=5,
            ),
            sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
            detail_transport=lambda **kwargs: (
                {"status_code": 0, "aweme_detail": build_douyin_aweme_detail()}
                if kwargs["params"]["aweme_id"] == "7580570616932224282"
                else (_ for _ in ()).throw(RuntimeError("detail-failed"))
            ),
            page_state_transport=lambda **kwargs: (_ for _ in ()).throw(
                PlatformAdapterError(
                    code="douyin_browser_target_tab_missing",
                    message="browser recovery disabled for hermetic regression",
                    details={},
                )
            ),
        )
        return {"xhs": xhs_adapter, "douyin": douyin_adapter}

    @staticmethod
    def valid_harness_results() -> list[dict[str, object]]:
        return [
            {
                "sample_id": "sample-success",
                "verdict": "pass",
                "reason": {"code": "success_envelope_observed", "message": "success"},
                "observed_status": "success",
                "observed_error": None,
            },
            {
                "sample_id": "sample-legal-failure",
                "verdict": "legal_failure",
                "reason": {"code": "legal_failed_envelope_observed", "message": "legal failure"},
                "observed_status": "failed",
                "observed_error": {
                    "category": "platform",
                    "code": "platform_rejected",
                    "message": "platform rejected request",
                    "details": {},
                },
            },
        ]

    @staticmethod
    def valid_platform_leakage_payload() -> dict[str, object]:
        return {
            "version": "v0.2.0",
            "boundary_scope": [
                "core_runtime",
                "shared_input_model",
                "shared_error_model",
                "adapter_registry",
                "shared_result_contract",
                "version_gate_logic",
            ],
            "verdict": "pass",
            "summary": "platform leakage checks are clean",
            "findings": [],
            "evidence_refs": ["leakage:scan:1"],
        }


if __name__ == "__main__":
    unittest.main()
