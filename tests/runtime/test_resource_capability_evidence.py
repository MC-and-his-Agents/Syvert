from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from syvert.adapters.douyin import build_session_config_from_context as build_douyin_session_config_from_context
from syvert.adapters.xhs import build_session_config_from_context as build_xhs_session_config_from_context
from syvert.real_adapter_regression import seed_reference_regression_resources
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
)
from tests.runtime.resource_fixtures import (
    build_managed_resource_bundle,
    douyin_account_material,
    xhs_account_material,
)


class ResourceCapabilityEvidenceTests(unittest.TestCase):
    def test_validate_frozen_resource_capability_evidence_contract_accepts_current_baseline(self) -> None:
        validate_frozen_resource_capability_evidence_contract()

        self.assertEqual(approved_resource_capability_ids(), frozenset({"account", "proxy"}))
        self.assertEqual(
            {entry.capability_id for entry in approved_resource_capability_vocabulary_entries()},
            {"account", "proxy"},
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

    def test_runtime_requested_slots_match_account_and_proxy_evidence(self) -> None:
        self.assertEqual(
            RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE[(CONTENT_DETAIL_BY_URL, LEGACY_COLLECTION_MODE)],
            ("account", "proxy"),
        )

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
