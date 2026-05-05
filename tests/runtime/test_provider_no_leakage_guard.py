from __future__ import annotations

import unittest

from syvert.adapter_provider_compatibility_decision import (
    decide_adapter_provider_compatibility,
    project_compatibility_decision_for_core,
)
from syvert.provider_no_leakage_guard import (
    PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED,
    PROVIDER_NO_LEAKAGE_STATUS_FAILED,
    PROVIDER_NO_LEAKAGE_STATUS_PASSED,
    assert_core_provider_no_leakage,
    guard_core_provider_no_leakage,
)
from syvert.registry import AdapterRegistry
from syvert.resource_lifecycle import (
    ResourceBundle,
    ResourceLease,
    ResourceLifecycleSnapshot,
    ResourceRecord,
    resource_bundle_to_dict,
    snapshot_to_dict,
)
from syvert.resource_lifecycle_store import default_resource_lifecycle_store
from syvert.runtime import TaskInput, TaskRequest, execute_task_with_record, failure_envelope, runtime_contract_error
from syvert.task_record import (
    TaskRequestSnapshot,
    create_task_record,
    finish_task_record,
    start_task_record,
    task_record_to_dict,
)
from tests.runtime.adapter_provider_compatibility_decision_fixtures import valid_compatibility_decision_input
from tests.runtime.test_registry import DeclarativeAdapter
from tests.runtime.test_runtime import TEST_ADAPTER_KEY, SuccessfulAdapter, TaskRecordStoreEnvMixin


class ProviderNoLeakageGuardTests(unittest.TestCase):
    def test_core_projection_excludes_adapter_bound_provider_evidence(self) -> None:
        decision = matched_decision()
        projection = project_compatibility_decision_for_core(decision)

        result = guard_core_provider_no_leakage(
            surface_name="core_projection",
            surface=projection,
            decision=decision,
        )

        self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_PASSED)
        self.assertNotIn("provider_key", projection)
        self.assertNotIn("offer_id", projection)
        self.assertNotIn("adapter_bound_provider_evidence", projection)

    def test_registry_discovery_surfaces_exclude_provider_fields(self) -> None:
        decision = matched_decision()
        registry = AdapterRegistry.from_mapping({"xhs": DeclarativeAdapter()})
        surfaces = {
            "capabilities": registry.discover_capabilities("xhs"),
            "targets": registry.discover_targets("xhs"),
            "collection_modes": registry.discover_collection_modes("xhs"),
            "resource_requirements": registry.discover_resource_requirements("xhs"),
        }

        result = guard_core_provider_no_leakage(
            surface_name="registry_discovery",
            surface=surfaces,
            decision=decision,
        )

        self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_PASSED)

    def test_task_record_payload_excludes_provider_identity(self) -> None:
        decision = matched_decision()
        request = TaskRequestSnapshot(
            adapter_key="xhs",
            capability="content_detail_by_url",
            target_type="url",
            target_value="https://example.test/post/1",
            collection_mode="hybrid",
        )
        record = create_task_record("task-no-provider", request, occurred_at="2026-05-04T10:00:00Z")
        running = start_task_record(record, occurred_at="2026-05-04T10:00:01Z")
        failed = finish_task_record(
            running,
            failure_envelope(
                "task-no-provider",
                "xhs",
                "content_detail_by_url",
                runtime_contract_error("compatibility_unmatched", "compatibility decision unmatched"),
            ),
            occurred_at="2026-05-04T10:00:02Z",
        )

        result = guard_core_provider_no_leakage(
            surface_name="task_record",
            surface=task_record_to_dict(failed),
            decision=decision,
        )

        self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_PASSED)

    def test_resource_lifecycle_surfaces_exclude_provider_identity(self) -> None:
        decision = matched_decision()
        account = ResourceRecord(
            resource_id="account-001",
            resource_type="account",
            status="IN_USE",
            material={"managed_adapter_key": "xhs", "account_ref": "account-ref-001"},
        )
        proxy = ResourceRecord(
            resource_id="proxy-001",
            resource_type="proxy",
            status="IN_USE",
            material={"proxy_endpoint": "http://proxy.internal"},
        )
        bundle = ResourceBundle(
            bundle_id="bundle-001",
            lease_id="lease-001",
            task_id="task-no-provider",
            adapter_key="xhs",
            capability="content_detail_by_url",
            requested_slots=("account", "proxy"),
            acquired_at="2026-05-04T10:00:00Z",
            account=account,
            proxy=proxy,
        )
        lease = ResourceLease(
            lease_id="lease-001",
            bundle_id="bundle-001",
            task_id="task-no-provider",
            adapter_key="xhs",
            capability="content_detail_by_url",
            resource_ids=("account-001", "proxy-001"),
            acquired_at="2026-05-04T10:00:00Z",
        )
        snapshot = ResourceLifecycleSnapshot(
            schema_version="v0.4.0",
            revision=1,
            resources=(account, proxy),
            leases=(lease,),
        )

        result = guard_core_provider_no_leakage(
            surface_name="resource_lifecycle",
            surface={
                "bundle": resource_bundle_to_dict(bundle),
                "snapshot": snapshot_to_dict(snapshot),
            },
            decision=decision,
        )

        self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_PASSED)

    def test_guard_fails_closed_for_provider_field_on_core_surface(self) -> None:
        decision = matched_decision()

        result = guard_core_provider_no_leakage(
            surface_name="core_routing",
            surface={"selected_provider": "native_xhs_detail"},
            decision=decision,
        )

        self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
        self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)
        self.assertEqual(result.evidence.forbidden_field_paths, ("core_routing.selected_provider",))

    def test_guard_fails_closed_for_forbidden_provider_decision_synonyms(self) -> None:
        decision = matched_decision()
        cases = (
            "provider",
            "providerId",
            "provider_capability",
            "provider_capabilities",
            "provider_offer",
            "provider_profile",
            "provider_registry_entry",
            "external_provider_ref",
            "native_provider",
            "browser_provider",
            "resource_provider",
            "compatibility_decision",
            "core_provider_registry",
            "core_provider_discovery",
            "selector",
            "routing",
            "marketplace_listing",
            "offerID",
            "OfferID",
        )
        for field_name in cases:
            with self.subTest(field_name=field_name):
                result = guard_core_provider_no_leakage(
                    surface_name="core_surface",
                    surface={field_name: "x"},
                    decision=decision,
                )

                self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
                self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)
                self.assertEqual(result.evidence.forbidden_field_paths, (f"core_surface.{field_name}",))

    def test_guard_fails_closed_for_camel_case_provider_fields(self) -> None:
        decision = matched_decision()
        cases = (
            "providerKey",
            "offerId",
            "selectedProvider",
            "compatibilityDecision",
            "resourceSupply",
            "providerCapabilities",
            "externalProviderRef",
            "nativeProvider",
            "browserProvider",
            "resourceProvider",
        )
        for field_name in cases:
            with self.subTest(field_name=field_name):
                result = guard_core_provider_no_leakage(
                    surface_name="core_surface",
                    surface={field_name: "x"},
                    decision=decision,
                )

                self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
                self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)
                self.assertEqual(result.evidence.forbidden_field_paths, (f"core_surface.{field_name}",))

    def test_guard_fails_closed_for_provider_identity_value_on_core_surface(self) -> None:
        decision = matched_decision()

        result = guard_core_provider_no_leakage(
            surface_name="task_record",
            surface={"routing_summary": {"chosen": "native_xhs_detail"}},
            decision=decision,
        )

        self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
        self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)
        self.assertEqual(result.evidence.forbidden_value_paths, ("task_record.routing_summary.chosen",))

    def test_guard_fails_closed_for_embedded_provider_identity_value(self) -> None:
        decision = matched_decision()
        cases = (
            ("core_routing", {"route_ref": "route:native_xhs_detail"}),
            ("task_record", {"offer_ref": "offer:native-xhs-detail-001"}),
            ("core_routing", {"chosen": "nativeXhsDetail"}),
            ("core_routing", {"chosen": "NativeXhsDetail"}),
        )
        for surface_name, surface in cases:
            with self.subTest(surface_name=surface_name):
                result = guard_core_provider_no_leakage(
                    surface_name=surface_name,
                    surface=surface,
                    decision=decision,
                )

                self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
                self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)

    def test_guard_fails_closed_for_provider_identity_in_mapping_keys(self) -> None:
        decision = matched_decision()
        cases = (
            ("core_routing", {"routes": {"native_xhs_detail": "enabled"}}),
            ("task_record", {"offers": {"native-xhs-detail-001": {"status": "seen"}}}),
        )
        for surface_name, surface in cases:
            with self.subTest(surface_name=surface_name):
                result = guard_core_provider_no_leakage(
                    surface_name=surface_name,
                    surface=surface,
                    decision=decision,
                )

                self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
                self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)

    def test_guard_fails_closed_for_provider_specific_failed_envelope_values(self) -> None:
        decision = matched_decision()
        cases = (
            {"error": {"code": "provider_unavailable"}},
            {"error": {"code": "provider_contract_violation"}},
            {"error": {"code": "invalid_provider_offer"}},
            {"error": {"failure_category": "provider"}},
            {"error": {"failure_category": "provider_failure"}},
            {"error": {"failureCategory": "provider"}},
            {"error": {"FailureCategory": "provider_failure"}},
            {"error": {"failure-category": "provider"}},
            {"error": {"message": "provider_unavailable in downstream"}},
        )
        for surface in cases:
            with self.subTest(surface=surface):
                result = guard_core_provider_no_leakage(
                    surface_name="runtime_envelope",
                    surface=surface,
                    decision=decision,
                )

                self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
                self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)

    def test_guard_fails_closed_for_forbidden_provider_semantics_in_string_values(self) -> None:
        decision = matched_decision()
        cases = (
            {"decision_detail": "provider_selector"},
            {"field_names": ["selected_provider"]},
            {"routing_summary": "routing_policy"},
            {"mode": "route:provider_selector"},
            {"mode": "mode:selected_provider"},
            {"policy": "policy/routing_policy"},
            {"classification": "provider_product_support"},
            {"classification": "provider_lifecycle"},
            {"classification": "provider_lease"},
            {"classification": "resource_pool"},
            {"classification": "account_pool"},
            {"classification": "proxy_pool"},
            {"source": "marketplace_listing"},
            {"service_level": "sla"},
            {"field_names": ["provider_capabilities"]},
            {"metadata": "external_provider_ref"},
            {"metadata": "native_provider"},
            {"metadata": "browser_provider"},
            {"metadata": "resource_provider"},
        )
        for surface in cases:
            with self.subTest(surface=surface):
                result = guard_core_provider_no_leakage(
                    surface_name="core_surface",
                    surface=surface,
                    decision=decision,
                )

                self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_FAILED)
                self.assertEqual(result.error_code, PROVIDER_NO_LEAKAGE_ERROR_PROVIDER_LEAKAGE_DETECTED)

    def test_assert_guard_raises_for_provider_lifecycle_field(self) -> None:
        decision = matched_decision()

        with self.assertRaises(AssertionError):
            assert_core_provider_no_leakage(
                surface_name="resource_lifecycle",
                surface={"provider_lifecycle": {"lease": "provider-lease-001"}},
                decision=decision,
            )


class ProviderNoLeakageRealRuntimePathTests(TaskRecordStoreEnvMixin, unittest.TestCase):
    def test_real_runtime_task_record_and_resource_lifecycle_surfaces_exclude_provider_identity(self) -> None:
        decision = matched_decision()

        outcome = execute_task_with_record(
            TaskRequest(
                adapter_key=TEST_ADAPTER_KEY,
                capability="content_detail_by_url",
                input=TaskInput(url="https://example.com/posts/no-provider-leakage"),
            ),
            adapters={TEST_ADAPTER_KEY: SuccessfulAdapter()},
            task_id_factory=lambda: "task-real-no-provider-leakage",
        )

        self.assertEqual(outcome.envelope["status"], "success")
        self.assertIsNotNone(outcome.task_record)
        surfaces = {
            "runtime_envelope": outcome.envelope,
            "task_record": task_record_to_dict(outcome.task_record),
            "resource_lifecycle_snapshot": snapshot_to_dict(default_resource_lifecycle_store().load_snapshot()),
        }
        for surface_name, surface in surfaces.items():
            with self.subTest(surface_name=surface_name):
                result = guard_core_provider_no_leakage(
                    surface_name=surface_name,
                    surface=surface,
                    decision=decision,
                )

                self.assertEqual(result.status, PROVIDER_NO_LEAKAGE_STATUS_PASSED)


def matched_decision():
    return decide_adapter_provider_compatibility(valid_compatibility_decision_input())


if __name__ == "__main__":
    unittest.main()
