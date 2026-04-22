from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

from syvert.adapters.douyin import build_session_config_from_context as build_douyin_session_config_from_context
from syvert.adapters.xhs import build_session_config_from_context as build_xhs_session_config_from_context
from syvert.real_adapter_regression import seed_reference_regression_resources
from syvert import resource_capability_evidence
from syvert.resource_capability_evidence import (
    approved_resource_capability_ids,
    approved_resource_capability_vocabulary_entries,
    frozen_dual_reference_resource_capability_evidence_records,
    frozen_evidence_reference_entries,
    validate_frozen_resource_capability_evidence_contract,
)
from syvert.resource_lifecycle import MANAGED_ACCOUNT_ADAPTER_KEY_FIELD
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
from syvert.runtime import (
    AdapterExecutionContext,
    AdapterTaskRequest,
    CONTENT_DETAIL,
    CONTENT_DETAIL_BY_URL,
    LEGACY_COLLECTION_MODE,
    RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE,
    TaskInput,
    TaskRequest,
    execute_task,
)
from tests.runtime.resource_fixtures import (
    ResourceStoreEnvMixin,
    build_managed_resource_bundle,
    douyin_account_material,
    xhs_account_material,
)


class ProxyPathCaptureAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request: AdapterExecutionContext) -> dict[str, object]:
        self.last_request = request
        return {
            "raw": {"url": request.input.url},
            "normalized": {
                "platform": "stub",
                "content_id": "content-proxy-path",
                "content_type": "unknown",
                "canonical_url": request.input.url,
                "title": "",
                "body_text": "",
                "published_at": None,
                "author": {
                    "author_id": None,
                    "display_name": None,
                    "avatar_url": None,
                },
                "stats": {
                    "like_count": None,
                    "comment_count": None,
                    "share_count": None,
                    "collect_count": None,
                },
                "media": {
                    "cover_url": None,
                    "video_url": None,
                    "image_urls": [],
                },
            },
        }


class ResourceCapabilityEvidenceTests(ResourceStoreEnvMixin, unittest.TestCase):
    def test_frozen_evidence_refs_are_traceable_from_formal_research_registry(self) -> None:
        research_text = (
            Path(__file__).resolve().parents[2]
            / "docs/specs/FR-0015-dual-reference-resource-capability-evidence/research.md"
        ).read_text(encoding="utf-8")
        registry_match = re.search(
            r"## 证据登记项\n\n(?P<table>(?:\|.*\n)+?)\n## ",
            research_text,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(registry_match)

        registry_entries = {}
        for line in registry_match.group("table").splitlines():
            match = re.match(
                r"^\| `(?P<evidence_ref>fr-0015:[^`]+)` \| `(?P<source_file>[^`]+)` 中 `(?P<source_symbol>[^`]+)` \| ",
                line,
            )
            if match:
                registry_entries[match.group("evidence_ref")] = (
                    match.group("source_file"),
                    match.group("source_symbol").removesuffix("()"),
                )

        self.assertEqual(
            registry_entries,
            {
                entry.evidence_ref: (entry.source_file, entry.source_symbol)
                for entry in frozen_evidence_reference_entries()
            },
        )

    def test_validate_frozen_resource_capability_evidence_contract_accepts_current_baseline(self) -> None:
        validate_frozen_resource_capability_evidence_contract()

        self.assertEqual(approved_resource_capability_ids(), frozenset({"account", "proxy"}))
        self.assertEqual(
            {entry.capability_id for entry in approved_resource_capability_vocabulary_entries()},
            {"account", "proxy"},
        )
        self.assertEqual(
            {
                entry.capability_id: entry.approval_basis_evidence_refs
                for entry in approved_resource_capability_vocabulary_entries()
            },
            {
                "account": (
                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                    "fr-0015:xhs:content-detail:url:hybrid:account-material",
                    "fr-0015:douyin:content-detail:url:hybrid:account-material",
                ),
                "proxy": (
                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                    "fr-0015:regression:xhs:managed-proxy-seed",
                    "fr-0015:regression:douyin:managed-proxy-seed",
                ),
            },
        )
        self.assertEqual(
            {
                entry.evidence_ref: (entry.source_file, entry.source_symbol)
                for entry in frozen_evidence_reference_entries()
            },
            {
                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots": (
                    "syvert/runtime.py",
                    "RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE",
                ),
                "fr-0015:xhs:content-detail:url:hybrid:account-material": (
                    "syvert/adapters/xhs.py",
                    "build_session_config_from_context",
                ),
                "fr-0015:douyin:content-detail:url:hybrid:account-material": (
                    "syvert/adapters/douyin.py",
                    "build_session_config_from_context",
                ),
                "fr-0015:xhs:content-detail:url:hybrid:url-request-tokens": (
                    "syvert/adapters/xhs.py",
                    "build_detail_body",
                ),
                "fr-0015:douyin:content-detail:url:hybrid:request-signature-token": (
                    "syvert/adapters/douyin.py",
                    "DouyinAdapter._build_detail_params",
                ),
                "fr-0015:xhs:content-detail:url:hybrid:page-state-fallback": (
                    "syvert/adapters/xhs.py",
                    "XhsAdapter._recover_note_card_from_html",
                ),
                "fr-0015:douyin:content-detail:url:hybrid:page-state-fallback": (
                    "syvert/adapters/douyin.py",
                    "DouyinAdapter._recover_aweme_detail_from_page_state",
                ),
                "fr-0015:regression:xhs:managed-proxy-seed": (
                    "syvert/real_adapter_regression.py",
                    "seed_reference_regression_resources",
                ),
                "fr-0015:regression:douyin:managed-proxy-seed": (
                    "syvert/real_adapter_regression.py",
                    "seed_reference_regression_resources",
                ),
            },
        )

    def test_canonical_records_freeze_shared_adapter_only_and_rejected_outcomes(self) -> None:
        self.assertEqual(
            {
                (record.adapter_key, record.candidate_abstract_capability): (
                    record.resource_signals,
                    record.shared_status,
                    record.decision,
                    record.evidence_refs,
                )
                for record in frozen_dual_reference_resource_capability_evidence_records()
            },
            {
                ("xhs", "account"): (
                    (
                        "runtime_requested_slots=account,proxy",
                        "adapter_consumes_account_material=cookies,user_agent,sign_base_url,timeout_seconds",
                    ),
                    "shared",
                    "approve_for_v0_5_0",
                    (
                        "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                        "fr-0015:xhs:content-detail:url:hybrid:account-material",
                    ),
                ),
                ("douyin", "account"): (
                    (
                        "runtime_requested_slots=account,proxy",
                        "adapter_consumes_account_material=cookies,user_agent,verify_fp,ms_token,webid,sign_base_url,timeout_seconds",
                    ),
                    "shared",
                    "approve_for_v0_5_0",
                    (
                        "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                        "fr-0015:douyin:content-detail:url:hybrid:account-material",
                    ),
                ),
                ("xhs", "proxy"): (
                    (
                        "runtime_requested_slots=account,proxy",
                        "regression_seeded_resources=account,proxy",
                    ),
                    "shared",
                    "approve_for_v0_5_0",
                    (
                        "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                        "fr-0015:regression:xhs:managed-proxy-seed",
                    ),
                ),
                ("douyin", "proxy"): (
                    (
                        "runtime_requested_slots=account,proxy",
                        "regression_seeded_resources=account,proxy",
                    ),
                    "shared",
                    "approve_for_v0_5_0",
                    (
                        "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                        "fr-0015:regression:douyin:managed-proxy-seed",
                    ),
                ),
                ("douyin", "verify_fp"): (
                    ("adapter_private_account_field=verify_fp",),
                    "adapter_only",
                    "keep_adapter_local",
                    ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
                ),
                ("douyin", "ms_token"): (
                    ("adapter_private_account_field=ms_token",),
                    "adapter_only",
                    "keep_adapter_local",
                    ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
                ),
                ("douyin", "webid"): (
                    ("adapter_private_account_field=webid",),
                    "adapter_only",
                    "keep_adapter_local",
                    ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
                ),
                ("douyin", "a_bogus"): (
                    ("adapter_private_request_token=a_bogus",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:douyin:content-detail:url:hybrid:request-signature-token",),
                ),
                ("xhs", "xsec_token"): (
                    ("adapter_private_request_token=xsec_token",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:xhs:content-detail:url:hybrid:url-request-tokens",),
                ),
                ("xhs", "xsec_source"): (
                    ("adapter_private_request_token=xsec_source",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:xhs:content-detail:url:hybrid:url-request-tokens",),
                ),
                ("xhs", "sign_base_url"): (
                    ("technical_binding_field=sign_base_url",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:xhs:content-detail:url:hybrid:account-material",),
                ),
                ("douyin", "sign_base_url"): (
                    ("technical_binding_field=sign_base_url",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
                ),
                ("xhs", "cookies"): (
                    ("account_material_field=cookies",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:xhs:content-detail:url:hybrid:account-material",),
                ),
                ("douyin", "cookies"): (
                    ("account_material_field=cookies",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
                ),
                ("xhs", "user_agent"): (
                    ("account_material_field=user_agent",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:xhs:content-detail:url:hybrid:account-material",),
                ),
                ("douyin", "user_agent"): (
                    ("account_material_field=user_agent",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:douyin:content-detail:url:hybrid:account-material",),
                ),
                ("xhs", "browser_state"): (
                    ("technical_binding_candidate=browser_state",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:xhs:content-detail:url:hybrid:page-state-fallback",),
                ),
                ("douyin", "browser_state"): (
                    ("technical_binding_candidate=browser_state",),
                    "rejected",
                    "reject_for_v0_5_0",
                    ("fr-0015:douyin:content-detail:url:hybrid:page-state-fallback",),
                ),
            },
        )

    def test_validate_fails_closed_when_unapproved_shared_capability_is_added(self) -> None:
        records = frozen_dual_reference_resource_capability_evidence_records()
        expanded_records = (
            *records,
            replace(
                records[0],
                candidate_abstract_capability="browser_profile",
                evidence_refs=(
                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                    "fr-0015:xhs:content-detail:url:hybrid:account-material",
                ),
            ),
            replace(
                records[1],
                candidate_abstract_capability="browser_profile",
                evidence_refs=(
                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                    "fr-0015:douyin:content-detail:url:hybrid:account-material",
                ),
            ),
        )

        with mock.patch.object(
            resource_capability_evidence,
            "_FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS",
            expanded_records,
        ):
            with self.assertRaisesRegex(ValueError, "full canonical candidate matrix"):
                validate_frozen_resource_capability_evidence_contract()

    def test_validate_fails_closed_when_shared_record_duplicates_adapter_pair(self) -> None:
        records = frozen_dual_reference_resource_capability_evidence_records()
        duplicated_records = (*records, records[0])

        with mock.patch.object(
            resource_capability_evidence,
            "_FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS",
            duplicated_records,
        ):
            with self.assertRaisesRegex(ValueError, "duplicate candidate/adapter pairs"):
                validate_frozen_resource_capability_evidence_contract()

    def test_validate_fails_closed_when_negative_candidate_disappears(self) -> None:
        records = tuple(
            record
            for record in frozen_dual_reference_resource_capability_evidence_records()
            if (record.adapter_key, record.candidate_abstract_capability) != ("xhs", "xsec_token")
        )

        with mock.patch.object(
            resource_capability_evidence,
            "_FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS",
            records,
        ):
            with self.assertRaisesRegex(ValueError, "full canonical candidate matrix"):
                validate_frozen_resource_capability_evidence_contract()

    def test_validate_fails_closed_when_browser_state_evidence_refs_drift(self) -> None:
        records = tuple(
            replace(
                record,
                evidence_refs=("fr-0015:xhs:content-detail:url:hybrid:account-material",),
            )
            if (record.adapter_key, record.candidate_abstract_capability) == ("xhs", "browser_state")
            else record
            for record in frozen_dual_reference_resource_capability_evidence_records()
        )

        with mock.patch.object(
            resource_capability_evidence,
            "_FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS",
            records,
        ):
            with self.assertRaisesRegex(ValueError, "canonical signals, evidence refs, and outcomes"):
                validate_frozen_resource_capability_evidence_contract()

    def test_validate_fails_closed_when_approved_vocabulary_evidence_refs_drift(self) -> None:
        tampered_entries = tuple(
            replace(
                entry,
                approval_basis_evidence_refs=(
                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                    "fr-0015:regression:xhs:managed-proxy-seed",
                    "fr-0015:regression:douyin:managed-proxy-seed",
                ),
            )
            if entry.capability_id == "account"
            else entry
            for entry in approved_resource_capability_vocabulary_entries()
        )

        with mock.patch.object(
            resource_capability_evidence,
            "_APPROVED_RESOURCE_CAPABILITY_VOCABULARY_ENTRIES",
            tampered_entries,
        ):
            with self.assertRaisesRegex(ValueError, "canonical mapping derived from shared evidence records"):
                validate_frozen_resource_capability_evidence_contract()

    def test_public_accessors_fail_closed_when_baseline_drifts(self) -> None:
        tampered_entries = tuple(
            replace(
                entry,
                approval_basis_evidence_refs=(
                    "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                    "fr-0015:regression:xhs:managed-proxy-seed",
                    "fr-0015:regression:douyin:managed-proxy-seed",
                ),
            )
            if entry.capability_id == "account"
            else entry
            for entry in approved_resource_capability_vocabulary_entries()
        )

        with mock.patch.object(
            resource_capability_evidence,
            "_APPROVED_RESOURCE_CAPABILITY_VOCABULARY_ENTRIES",
            tampered_entries,
        ):
            with self.assertRaisesRegex(ValueError, "canonical mapping derived from shared evidence records"):
                resource_capability_evidence.approved_resource_capability_ids()

    def test_public_accessors_fail_closed_when_formal_research_registry_becomes_unreadable_after_first_success(self) -> None:
        research_path = resource_capability_evidence._FORMAL_RESEARCH_PATH.resolve()
        original_read_text = Path.read_text

        def fake_read_text(path_obj: Path, *args: object, **kwargs: object) -> str:
            if path_obj.resolve() == research_path:
                raise OSError("research registry unavailable")
            return original_read_text(path_obj, *args, **kwargs)

        resource_capability_evidence.approved_resource_capability_ids()

        with mock.patch("pathlib.Path.read_text", autospec=True, side_effect=fake_read_text):
            with self.assertRaisesRegex(ValueError, "formal research registry must be readable"):
                resource_capability_evidence.approved_resource_capability_ids()

    def test_public_accessors_fail_closed_when_source_file_disappears_after_first_success(self) -> None:
        runtime_path = (resource_capability_evidence._REPO_ROOT / "syvert/runtime.py").resolve()
        original_is_file = Path.is_file

        def fake_is_file(path_obj: Path) -> bool:
            if path_obj.resolve() == runtime_path:
                return False
            return original_is_file(path_obj)

        resource_capability_evidence.approved_resource_capability_ids()

        with mock.patch("pathlib.Path.is_file", autospec=True, side_effect=fake_is_file):
            with self.assertRaisesRegex(ValueError, "evidence source_file must resolve to a real file"):
                resource_capability_evidence.approved_resource_capability_ids()

    def test_validate_fails_closed_when_nested_evidence_source_pointer_drifts(self) -> None:
        tampered_entries = tuple(
            replace(
                entry,
                source_symbol="DouyinAdapter.missing_signature_method",
            )
            if entry.evidence_ref == "fr-0015:douyin:content-detail:url:hybrid:request-signature-token"
            else entry
            for entry in frozen_evidence_reference_entries()
        )

        with mock.patch.object(
            resource_capability_evidence,
            "_FROZEN_EVIDENCE_REFERENCE_ENTRIES",
            tampered_entries,
        ):
            with self.assertRaisesRegex(ValueError, "canonical source pointers from the formal research registry"):
                validate_frozen_resource_capability_evidence_contract()

    def test_runtime_requested_slots_match_account_and_proxy_evidence(self) -> None:
        self.assertEqual(
            RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE[(CONTENT_DETAIL_BY_URL, LEGACY_COLLECTION_MODE)],
            ("account", "proxy"),
        )

    def test_proxy_shared_evidence_is_exercised_through_runtime_bundle_binding(self) -> None:
        adapter = ProxyPathCaptureAdapter()

        envelope = execute_task(
            TaskRequest(
                adapter_key="stub",
                capability=CONTENT_DETAIL_BY_URL,
                input=TaskInput(url="https://example.com/runtime-proxy-evidence"),
            ),
            adapters={"stub": adapter},
            task_id_factory=lambda: "task-proxy-evidence",
        )

        self.assertEqual(envelope["status"], "success")
        self.assertEqual(adapter.last_request.resource_bundle.requested_slots, ("account", "proxy"))
        self.assertIsNotNone(adapter.last_request.resource_bundle.account)
        self.assertIsNotNone(adapter.last_request.resource_bundle.proxy)
        self.assertEqual(adapter.last_request.resource_bundle.capability, CONTENT_DETAIL_BY_URL)
        self.assertEqual(adapter.last_request.resource_bundle.proxy.resource_type, "proxy")

    def test_xhs_account_material_consumption_matches_evidence_baseline(self) -> None:
        material = xhs_account_material()
        context = self._build_execution_context(adapter_key="xhs", material=material)

        session = build_xhs_session_config_from_context(context)

        self.assertEqual(session.cookies, material["cookies"])
        self.assertEqual(session.user_agent, material["user_agent"])
        self.assertEqual(session.sign_base_url, material["sign_base_url"])
        self.assertEqual(session.timeout_seconds, material["timeout_seconds"])

    def test_douyin_account_material_consumption_matches_evidence_baseline(self) -> None:
        material = douyin_account_material()
        context = self._build_execution_context(adapter_key="douyin", material=material)

        session = build_douyin_session_config_from_context(context)

        self.assertEqual(session.cookies, material["cookies"])
        self.assertEqual(session.user_agent, material["user_agent"])
        self.assertEqual(session.verify_fp, material["verify_fp"])
        self.assertEqual(session.ms_token, material["ms_token"])
        self.assertEqual(session.webid, material["webid"])
        self.assertEqual(session.sign_base_url, material["sign_base_url"])
        self.assertEqual(session.timeout_seconds, material["timeout_seconds"])

    def test_reference_regression_resource_seed_preserves_account_and_proxy_truth(self) -> None:
        for adapter_key in ("xhs", "douyin"):
            with self.subTest(adapter_key=adapter_key):
                store = LocalResourceLifecycleStore(Path(tempfile.mkdtemp()) / "resource-lifecycle.json")
                seed_reference_regression_resources(store=store, adapter_key=adapter_key)
                snapshot = store.load_snapshot()
                resources_by_id = {record.resource_id: record for record in snapshot.resources}

                self.assertEqual(len(snapshot.resources), 2)
                self.assertIn(f"{adapter_key}-account-001", resources_by_id)
                self.assertIn(f"{adapter_key}-proxy-001", resources_by_id)
                self.assertEqual(resources_by_id[f"{adapter_key}-account-001"].resource_type, "account")
                self.assertEqual(resources_by_id[f"{adapter_key}-proxy-001"].resource_type, "proxy")
                self.assertEqual(
                    resources_by_id[f"{adapter_key}-account-001"].material[MANAGED_ACCOUNT_ADAPTER_KEY_FIELD],
                    adapter_key,
                )
                self.assertEqual(
                    resources_by_id[f"{adapter_key}-proxy-001"].material["proxy_endpoint"],
                    "http://proxy-001",
                )

    def _build_execution_context(self, *, adapter_key: str, material: dict[str, object]) -> AdapterExecutionContext:
        return AdapterExecutionContext(
            request=AdapterTaskRequest(
                capability=CONTENT_DETAIL,
                target_type="url",
                target_value="https://example.com/item",
                collection_mode=LEGACY_COLLECTION_MODE,
            ),
            resource_bundle=build_managed_resource_bundle(
                adapter_key=adapter_key,
                task_id=f"task-{adapter_key}-evidence",
                capability=CONTENT_DETAIL,
                requested_slots=("account",),
                account_material=material,
            ),
        )
