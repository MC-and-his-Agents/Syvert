from __future__ import annotations

from dataclasses import replace
from pathlib import Path
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
            {entry.evidence_ref for entry in frozen_evidence_reference_entries()},
            {
                "fr-0015:runtime:content-detail-by-url-hybrid:requested-slots",
                "fr-0015:xhs:content-detail:url:hybrid:account-material",
                "fr-0015:douyin:content-detail:url:hybrid:account-material",
                "fr-0015:regression:xhs:managed-proxy-seed",
                "fr-0015:regression:douyin:managed-proxy-seed",
            },
        )

    def test_canonical_records_freeze_shared_adapter_only_and_rejected_outcomes(self) -> None:
        records = {
            (record.adapter_key, record.candidate_abstract_capability): record
            for record in frozen_dual_reference_resource_capability_evidence_records()
        }

        self.assertEqual(records[("xhs", "account")].shared_status, "shared")
        self.assertEqual(records[("xhs", "account")].decision, "approve_for_v0_5_0")
        self.assertEqual(records[("douyin", "account")].shared_status, "shared")
        self.assertEqual(records[("douyin", "account")].decision, "approve_for_v0_5_0")
        self.assertEqual(records[("xhs", "proxy")].shared_status, "shared")
        self.assertEqual(records[("douyin", "proxy")].shared_status, "shared")

        self.assertEqual(records[("douyin", "verify_fp")].shared_status, "adapter_only")
        self.assertEqual(records[("douyin", "verify_fp")].decision, "keep_adapter_local")
        self.assertEqual(records[("douyin", "ms_token")].shared_status, "adapter_only")
        self.assertEqual(records[("douyin", "webid")].shared_status, "adapter_only")

        self.assertEqual(records[("xhs", "sign_base_url")].shared_status, "rejected")
        self.assertEqual(records[("douyin", "sign_base_url")].shared_status, "rejected")
        self.assertEqual(records[("xhs", "browser_state")].shared_status, "rejected")
        self.assertEqual(records[("douyin", "browser_state")].shared_status, "rejected")

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
            with self.assertRaisesRegex(ValueError, "approved capability ids"):
                validate_frozen_resource_capability_evidence_contract()

    def test_validate_fails_closed_when_shared_record_duplicates_adapter_pair(self) -> None:
        records = frozen_dual_reference_resource_capability_evidence_records()
        duplicated_records = (*records, records[0])

        with mock.patch.object(
            resource_capability_evidence,
            "_FROZEN_DUAL_REFERENCE_RESOURCE_CAPABILITY_EVIDENCE_RECORDS",
            duplicated_records,
        ):
            with self.assertRaisesRegex(ValueError, "duplicate capability/adapter pairs"):
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

    def test_validate_fails_closed_when_evidence_source_symbol_drifts(self) -> None:
        entries = frozen_evidence_reference_entries()
        tampered_entries = (
            replace(entries[0], source_symbol="MISSING_RUNTIME_RESOURCE_SLOTS_SYMBOL"),
            *entries[1:],
        )

        with mock.patch.object(
            resource_capability_evidence,
            "_FROZEN_EVIDENCE_REFERENCE_ENTRIES",
            tampered_entries,
        ):
            with self.assertRaisesRegex(ValueError, "source_symbol must resolve"):
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
