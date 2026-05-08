from __future__ import annotations

import unittest

from syvert.resource_health import (
    RESOURCE_ADMISSION_DECISION_ADMITTED,
    RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT,
    RESOURCE_ADMISSION_DECISION_REJECTED,
    RESOURCE_INVALIDATION_REASON_CREDENTIAL_SESSION_INVALID,
    SESSION_HEALTH_HEALTHY,
    SESSION_HEALTH_INVALID,
    SESSION_HEALTH_STALE,
    SESSION_HEALTH_UNKNOWN,
    ResourceAdmissionDecision,
    ResourceHealthContractError,
    ResourceHealthEvidence,
    credential_material_from_account_resource,
    credential_material_public_projection,
    decide_resource_health_admission,
    invalidate_active_lease_from_health_evidence,
    resource_admission_decision_to_dict,
    resource_health_evidence_to_dict,
)
from syvert.resource_lifecycle import (
    AcquireRequest,
    ResourceBundle,
    ResourceLifecycleContractError,
    ResourceRecord,
    acquire,
    parse_rfc3339_utc_datetime,
)
from syvert.resource_lifecycle_store import default_resource_lifecycle_store
from tests.runtime.resource_fixtures import (
    ResourceStoreEnvMixin,
    managed_account_material,
    xhs_account_material,
)


class ResourceHealthTests(ResourceStoreEnvMixin, unittest.TestCase):
    resource_store_adapter_key = "xhs"

    def make_store(self):
        return default_resource_lifecycle_store()

    def account_record(self, *, resource_id: str = "account-001", status: str = "AVAILABLE") -> ResourceRecord:
        return ResourceRecord(
            resource_id=resource_id,
            resource_type="account",
            status=status,
            material=managed_account_material(xhs_account_material(), adapter_key="xhs"),
        )

    def healthy_evidence(self, **overrides) -> ResourceHealthEvidence:
        defaults = {
            "evidence_id": "evidence-healthy-001",
            "resource_id": "account-001",
            "resource_type": "account",
            "status": SESSION_HEALTH_HEALTHY,
            "observed_at": "2026-05-08T12:00:00.000000Z",
            "expires_at": "2026-05-08T12:30:00.000000Z",
            "freshness_policy_ref": "policy:session-health:15m",
            "provenance": "core_validation",
            "task_id": "task-001",
            "adapter_key": "xhs",
            "capability": "content_detail_by_url",
            "operation": "content_detail_by_url",
            "reason": "session probe passed",
            "redaction_status": "redacted",
        }
        defaults.update(overrides)
        return ResourceHealthEvidence(**defaults)

    def test_credential_material_public_projection_redacts_private_material(self) -> None:
        credential = credential_material_from_account_resource(self.account_record())

        projection = credential_material_public_projection(credential)

        self.assertEqual(projection["material_boundary"], "account_credential_material")
        self.assertEqual(projection["redaction_status"], "redacted")
        self.assertTrue(projection["material_fields_redacted"])
        self.assertGreater(projection["material_field_count"], 0)
        self.assertNotIn("cookies", str(projection))
        self.assertNotIn("ms_token", str(projection))
        self.assertNotIn("verify_fp", str(projection))
        self.assertNotIn("a=1; b=2", str(projection))

    def test_unknown_health_fails_closed_without_evidence(self) -> None:
        decision = decide_resource_health_admission(
            decision_id="decision-001",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account", "proxy"),
            resources=(self.account_record(),),
            evidence=(),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_REJECTED)
        self.assertEqual(decision.projected_session_health, SESSION_HEALTH_UNKNOWN)
        self.assertEqual(decision.failure_reason, "credential_session_unknown")
        self.assertTrue(decision.fail_closed)

    def test_healthy_evidence_admits_before_expiry(self) -> None:
        decision = decide_resource_health_admission(
            decision_id="decision-healthy",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account", "proxy"),
            resources=(self.account_record(),),
            evidence=(self.healthy_evidence(),),
            evaluated_at="2026-05-08T12:10:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_ADMITTED)
        self.assertEqual(decision.projected_session_health, SESSION_HEALTH_HEALTHY)
        self.assertFalse(decision.fail_closed)

    def test_redacted_diagnostics_can_name_private_field_family_without_raw_payload(self) -> None:
        for reason in ("token expired", "cookie expired", "header signature invalid"):
            with self.subTest(reason=reason):
                decision = decide_resource_health_admission(
                    decision_id="decision-redacted-diagnostic",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation="content_detail_by_url",
                    requested_slots=("account",),
                    resources=(self.account_record(),),
                    evidence=(self.healthy_evidence(reason=reason),),
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_ADMITTED)

    def test_expired_healthy_evidence_projects_to_stale(self) -> None:
        decision = decide_resource_health_admission(
            decision_id="decision-stale",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account", "proxy"),
            resources=(self.account_record(),),
            evidence=(self.healthy_evidence(),),
            evaluated_at="2026-05-08T12:30:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_REJECTED)
        self.assertEqual(decision.projected_session_health, SESSION_HEALTH_STALE)
        self.assertEqual(decision.failure_reason, "credential_session_stale")

    def test_invalid_pre_admission_evidence_rejects_without_changing_available_resource(self) -> None:
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-001",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            reason="platform reported credential expired",
        )

        decision = decide_resource_health_admission(
            decision_id="decision-invalid",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(self.account_record(),),
            evidence=(evidence,),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_REJECTED)
        self.assertEqual(decision.projected_session_health, SESSION_HEALTH_INVALID)
        self.assertEqual(decision.failure_reason, "pre_admission_session_invalid")
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "AVAILABLE")

    def test_same_observed_at_conflicting_evidence_is_deterministic_and_fail_closed(self) -> None:
        healthy = self.healthy_evidence(evidence_id="evidence-same-time-healthy")
        invalid = self.healthy_evidence(
            evidence_id="evidence-same-time-invalid",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            reason="platform reported credential expired",
        )
        stale = self.healthy_evidence(
            evidence_id="evidence-same-time-stale",
            status=SESSION_HEALTH_STALE,
            expires_at=None,
            freshness_policy_ref=None,
            reason="token expired",
        )

        for evidence_set in ((healthy, invalid), (invalid, healthy), (healthy, stale), (stale, healthy)):
            with self.subTest(evidence_ids=tuple(item.evidence_id for item in evidence_set)):
                decision = decide_resource_health_admission(
                    decision_id="decision-same-observed-at-conflict",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation="content_detail_by_url",
                    requested_slots=("account",),
                    resources=(self.account_record(),),
                    evidence=evidence_set,
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_REJECTED)
                self.assertTrue(decision.fail_closed)

    def test_same_observed_at_healthy_expiry_conflict_is_deterministic_and_fail_closed(self) -> None:
        fresh = self.healthy_evidence(
            evidence_id="evidence-same-time-fresh",
            expires_at="2026-05-08T12:30:00.000000Z",
        )
        expired = self.healthy_evidence(
            evidence_id="evidence-same-time-expired",
            expires_at="2026-05-08T12:01:00.000000Z",
        )

        for evidence_set in ((fresh, expired), (expired, fresh)):
            with self.subTest(evidence_ids=tuple(item.evidence_id for item in evidence_set)):
                decision = decide_resource_health_admission(
                    decision_id="decision-same-observed-at-expiry-conflict",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation="content_detail_by_url",
                    requested_slots=("account",),
                    resources=(self.account_record(),),
                    evidence=evidence_set,
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_REJECTED)
                self.assertEqual(decision.projected_session_health, SESSION_HEALTH_STALE)

    def test_malformed_unredacted_or_context_mismatched_evidence_is_invalid_contract(self) -> None:
        cases = (
            self.healthy_evidence(expires_at=None),
            self.healthy_evidence(redaction_status="raw"),
            self.healthy_evidence(adapter_key="douyin"),
            self.healthy_evidence(reason="raw cookies leaked"),
        )

        for evidence in cases:
            with self.subTest(evidence=evidence):
                decision = decide_resource_health_admission(
                    decision_id="decision-invalid-contract",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation="content_detail_by_url",
                    requested_slots=("account",),
                    resources=(self.account_record(),),
                    evidence=(evidence,),
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
                self.assertEqual(decision.failure_reason, "health_evidence_contract_invalid")

    def test_mapping_evidence_with_extra_private_payload_is_invalid_contract(self) -> None:
        evidence_payload = resource_health_evidence_to_dict(self.healthy_evidence())
        evidence_payload["cookies"] = "a=1; b=2"

        decision = decide_resource_health_admission(
            decision_id="decision-extra-private-payload",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(self.account_record(),),
            evidence=(evidence_payload,),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        self.assertEqual(decision.failure_reason, "health_evidence_contract_invalid")

    def test_malformed_timestamps_fail_closed_as_invalid_contract(self) -> None:
        cases = (
            {"observed_at": "not-a-time"},
            {"expires_at": "not-a-time"},
        )
        for override in cases:
            with self.subTest(override=override):
                decision = decide_resource_health_admission(
                    decision_id="decision-malformed-timestamp",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation="content_detail_by_url",
                    requested_slots=("account",),
                    resources=(self.account_record(),),
                    evidence=(self.healthy_evidence(**override),),
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

        evaluated_at_decision = decide_resource_health_admission(
            decision_id="decision-malformed-evaluated-at",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(self.account_record(),),
            evidence=(self.healthy_evidence(),),
            evaluated_at="not-a-time",
        )
        self.assertEqual(evaluated_at_decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        self.assertNotEqual(evaluated_at_decision.evaluated_at, "not-a-time")
        serialized = resource_admission_decision_to_dict(evaluated_at_decision)
        self.assertEqual(serialized["decision_status"], RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_non_health_gated_admission_does_not_consume_unrelated_malformed_evidence(self) -> None:
        malformed_evidence = {"cookies": "a=1; b=2"}

        proxy_only_decision = decide_resource_health_admission(
            decision_id="decision-proxy-only",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("proxy",),
            resources=(),
            evidence=(malformed_evidence,),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )
        non_gated_account_decision = decide_resource_health_admission(
            decision_id="decision-non-gated-account",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(self.account_record(),),
            evidence=(malformed_evidence,),
            evaluated_at="2026-05-08T12:05:00.000000Z",
            require_fresh_account_session=False,
        )

        self.assertEqual(proxy_only_decision.decision_status, RESOURCE_ADMISSION_DECISION_ADMITTED)
        self.assertEqual(proxy_only_decision.health_evidence_refs, ())
        self.assertEqual(non_gated_account_decision.decision_status, RESOURCE_ADMISSION_DECISION_ADMITTED)
        self.assertEqual(non_gated_account_decision.health_evidence_refs, ())

    def test_health_gated_admission_requires_operation_context_binding(self) -> None:
        cases = (
            {"current_operation": None, "evidence_operation": "content_detail_by_url"},
            {"current_operation": "other_operation", "evidence_operation": "content_detail_by_url"},
            {"current_operation": "content_detail_by_url", "evidence_operation": None},
        )
        for case in cases:
            with self.subTest(case=case):
                decision = decide_resource_health_admission(
                    decision_id="decision-operation-mismatch",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation=case["current_operation"],
                    requested_slots=("account",),
                    resources=(self.account_record(),),
                    evidence=(self.healthy_evidence(operation=case["evidence_operation"]),),
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_health_gated_admission_requires_adapter_and_capability_binding(self) -> None:
        cases = (
            {"adapter_key": None, "capability": "content_detail_by_url"},
            {"adapter_key": "xhs", "capability": None},
        )
        for case in cases:
            with self.subTest(case=case):
                decision = decide_resource_health_admission(
                    decision_id="decision-slice-binding-missing",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation="content_detail_by_url",
                    requested_slots=("account",),
                    resources=(self.account_record(),),
                    evidence=(self.healthy_evidence(**case),),
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_health_gated_admission_requires_task_binding(self) -> None:
        decision = decide_resource_health_admission(
            decision_id="decision-missing-task-binding",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(self.account_record(),),
            evidence=(self.healthy_evidence(task_id=None),),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_health_gated_admission_rejects_foreign_resource_evidence(self) -> None:
        foreign_evidence = self.healthy_evidence(
            evidence_id="evidence-foreign-resource",
            resource_id="account-other",
        )

        decision = decide_resource_health_admission(
            decision_id="decision-foreign-resource",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(self.account_record(),),
            evidence=(foreign_evidence,),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_health_gated_admission_rejects_mixed_valid_and_foreign_resource_evidence(self) -> None:
        selected_evidence = self.healthy_evidence(evidence_id="evidence-selected-resource")
        foreign_evidence = self.healthy_evidence(
            evidence_id="evidence-foreign-resource",
            resource_id="account-other",
        )

        decision = decide_resource_health_admission(
            decision_id="decision-mixed-resource-evidence",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(self.account_record(),),
            evidence=(selected_evidence, foreign_evidence),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )

        self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_malformed_credential_material_fails_closed_before_admission(self) -> None:
        cases = (
            ResourceRecord(
                resource_id="account-001",
                resource_type="account",
                status="AVAILABLE",
                material={"provider_account_id": "pa-001"},
            ),
            ResourceRecord(
                resource_id="account-001",
                resource_type="account",
                status="AVAILABLE",
                material=managed_account_material(xhs_account_material(), adapter_key="douyin"),
            ),
        )

        for account in cases:
            with self.subTest(account=account):
                decision = decide_resource_health_admission(
                    decision_id="decision-invalid-material",
                    task_id="task-001",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    operation="content_detail_by_url",
                    requested_slots=("account",),
                    resources=(account,),
                    evidence=(self.healthy_evidence(),),
                    evaluated_at="2026-05-08T12:05:00.000000Z",
                )
                self.assertEqual(decision.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
                self.assertEqual(decision.failure_reason, "credential_material_contract_invalid")
                self.assertTrue(decision.fail_closed)

    def test_active_lease_invalid_evidence_uses_core_owned_invalidation(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-active",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id=bundle.lease_id,
            bundle_id=bundle.bundle_id,
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertNotIsInstance(result, ResourceAdmissionDecision)
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "INVALID")
        lease = next(lease for lease in snapshot.leases if lease.lease_id == bundle.lease_id)
        self.assertEqual(lease.release_reason, RESOURCE_INVALIDATION_REASON_CREDENTIAL_SESSION_INVALID)

    def test_account_session_invalidation_does_not_invalidate_coleased_proxy(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "proxy"),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-account-proxy-bundle",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id=bundle.lease_id,
            bundle_id=bundle.bundle_id,
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertNotIsInstance(result, ResourceAdmissionDecision)
        snapshot = self.make_store().load_snapshot()
        resources_by_id = {record.resource_id: record for record in snapshot.resources}
        self.assertEqual(resources_by_id["account-001"].status, "INVALID")
        self.assertEqual(resources_by_id["proxy-001"].status, "AVAILABLE")
        original_lease = next(lease for lease in snapshot.leases if lease.lease_id == bundle.lease_id)
        invalidation_lease = next(lease for lease in snapshot.leases if lease.lease_id.endswith(":credential-session-invalidation"))
        self.assertEqual(original_lease.resource_ids, ("account-001", "proxy-001"))
        self.assertEqual(original_lease.target_status_after_release, "AVAILABLE")
        self.assertEqual(invalidation_lease.resource_ids, ("account-001",))
        self.assertEqual(invalidation_lease.target_status_after_release, "INVALID")
        trace_events = self.make_trace_store().load_events()
        account_closeout_types = {
            event.event_type
            for event in trace_events
            if event.resource_id == "account-001" and event.event_type in {"invalidated", "released"}
        }
        proxy_closeout_types = {
            event.event_type
            for event in trace_events
            if event.resource_id == "proxy-001" and event.event_type in {"invalidated", "released"}
        }
        self.assertIn("invalidated", account_closeout_types)
        self.assertEqual(proxy_closeout_types, {"released"})

    def test_invalid_evidence_without_active_lease_does_not_release_available_resource(self) -> None:
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-no-lease",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id="lease-missing",
            bundle_id="bundle-missing",
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_REJECTED)
        self.assertNotEqual(result.evaluated_at, evidence.observed_at)
        self.assertGreater(
            parse_rfc3339_utc_datetime(result.evaluated_at, field="evaluated_at"),
            parse_rfc3339_utc_datetime(evidence.observed_at, field="observed_at"),
        )
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "AVAILABLE")

    def test_no_active_lease_fallback_requires_existing_account_resource(self) -> None:
        for resource_id in ("account-missing", "proxy-001"):
            with self.subTest(resource_id=resource_id):
                evidence = self.healthy_evidence(
                    evidence_id=f"evidence-invalid-no-active-{resource_id}",
                    resource_id=resource_id,
                    status=SESSION_HEALTH_INVALID,
                    expires_at=None,
                    freshness_policy_ref=None,
                    provenance="adapter_diagnostic",
                    lease_id="lease-missing",
                    bundle_id="bundle-missing",
                    reason="platform reported credential expired",
                )

                result = invalidate_active_lease_from_health_evidence(
                    evidence=evidence,
                    store=self.make_store(),
                    task_context_task_id="task-001",
                    operation="content_detail_by_url",
                    resource_trace_store=self.make_trace_store(),
                )

                self.assertIsInstance(result, ResourceAdmissionDecision)
                assert isinstance(result, ResourceAdmissionDecision)
                self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_active_resource_with_wrong_lease_id_is_invalid_contract(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-wrong-lease-active-resource",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id="lease-wrong",
            bundle_id=bundle.bundle_id,
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        self.assertNotEqual(result.evaluated_at, evidence.observed_at)
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "IN_USE")

    def test_active_lease_invalidation_requires_task_and_lease_binding(self) -> None:
        for override in (
            {"task_id": None},
            {"lease_id": None},
            {"adapter_key": None},
            {"capability": None},
            {"operation": None},
        ):
            with self.subTest(override=override):
                evidence = self.healthy_evidence(
                    evidence_id=f"evidence-invalid-missing-{next(iter(override))}",
                    status=SESSION_HEALTH_INVALID,
                    expires_at=None,
                    freshness_policy_ref=None,
                    provenance="adapter_diagnostic",
                    lease_id=override.get("lease_id", "lease-missing"),
                    bundle_id="bundle-001",
                    reason="platform reported credential expired",
                    **{key: value for key, value in override.items() if key != "lease_id"},
                )

                result = invalidate_active_lease_from_health_evidence(
                    evidence=evidence,
                    store=self.make_store(),
                    task_context_task_id="task-001",
                    resource_trace_store=self.make_trace_store(),
                )

                self.assertIsInstance(result, ResourceAdmissionDecision)
                assert isinstance(result, ResourceAdmissionDecision)
                self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_active_lease_invalidation_rejects_non_account_resource_binding(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "proxy"),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        assert bundle.proxy is not None
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-proxy-binding",
            resource_id=bundle.proxy.resource_id,
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id=bundle.lease_id,
            bundle_id=bundle.bundle_id,
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        snapshot = self.make_store().load_snapshot()
        resources_by_id = {record.resource_id: record for record in snapshot.resources}
        self.assertEqual(resources_by_id["account-001"].status, "IN_USE")
        self.assertEqual(resources_by_id["proxy-001"].status, "IN_USE")

    def test_active_lease_invalidation_normalizes_lifecycle_store_read_failure(self) -> None:
        class BrokenStore:
            def load_snapshot(self):
                raise ResourceLifecycleContractError("resource_state_conflict: broken snapshot")

            def write_snapshot(self, snapshot):
                raise AssertionError("write_snapshot must not be called")

        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-broken-store",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id="lease-001",
            bundle_id="bundle-001",
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=BrokenStore(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_active_lease_invalidation_malformed_timestamp_is_invalid_contract(self) -> None:
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-malformed-time",
            status=SESSION_HEALTH_INVALID,
            observed_at="not-a-time",
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id="lease-001",
            bundle_id="bundle-001",
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_active_lease_invalidation_normalizes_unexpected_store_read_failure(self) -> None:
        class BrokenStore:
            def load_snapshot(self):
                raise OSError("disk unavailable")

            def write_snapshot(self, snapshot):
                raise AssertionError("write_snapshot must not be called")

        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-unexpected-store-error",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id="lease-001",
            bundle_id="bundle-001",
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=BrokenStore(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertEqual(result["error"]["category"], "runtime_contract")
        self.assertEqual(result["error"]["code"], "resource_state_conflict")

    def test_active_lease_lookup_miss_with_task_context_mismatch_is_invalid_contract(self) -> None:
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-missing-lease-wrong-task",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id="lease-missing",
            bundle_id="bundle-missing",
            task_id="task-other",
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_active_lease_invalidation_rejects_bundle_mismatch(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-wrong-bundle",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id=bundle.lease_id,
            bundle_id="bundle-other",
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "IN_USE")

    def test_active_lease_invalidation_requires_bundle_binding(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-missing-bundle",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id=bundle.lease_id,
            bundle_id=None,
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "IN_USE")

    def test_active_lease_invalidation_requires_operation_context_binding(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        cases = (
            {"current_operation": None, "evidence_operation": "content_detail_by_url"},
            {"current_operation": "other_operation", "evidence_operation": "content_detail_by_url"},
            {"current_operation": "content_detail_by_url", "evidence_operation": None},
        )
        for case in cases:
            with self.subTest(case=case):
                evidence = self.healthy_evidence(
                    evidence_id="evidence-invalid-wrong-operation",
                    status=SESSION_HEALTH_INVALID,
                    expires_at=None,
                    freshness_policy_ref=None,
                    provenance="adapter_diagnostic",
                    lease_id=bundle.lease_id,
                    bundle_id=bundle.bundle_id,
                    operation=case["evidence_operation"],
                    reason="platform reported credential expired",
                )
                result = invalidate_active_lease_from_health_evidence(
                    evidence=evidence,
                    store=self.make_store(),
                    task_context_task_id="task-001",
                    operation=case["current_operation"],
                    resource_trace_store=self.make_trace_store(),
                )
                self.assertIsInstance(result, ResourceAdmissionDecision)
                assert isinstance(result, ResourceAdmissionDecision)
                self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "IN_USE")

    def test_active_lease_invalidation_requires_adapter_and_capability_binding(self) -> None:
        store = self.make_store()
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            store,
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        for case in (
            {"adapter_key": None, "capability": "content_detail_by_url"},
            {"adapter_key": "xhs", "capability": None},
        ):
            with self.subTest(case=case):
                evidence = self.healthy_evidence(
                    evidence_id="evidence-invalid-missing-slice-binding",
                    status=SESSION_HEALTH_INVALID,
                    expires_at=None,
                    freshness_policy_ref=None,
                    provenance="adapter_diagnostic",
                    lease_id=bundle.lease_id,
                    bundle_id=bundle.bundle_id,
                    reason="platform reported credential expired",
                    **case,
                )

                result = invalidate_active_lease_from_health_evidence(
                    evidence=evidence,
                    store=store,
                    task_context_task_id="task-001",
                    operation="content_detail_by_url",
                    resource_trace_store=self.make_trace_store(),
                )

                self.assertIsInstance(result, ResourceAdmissionDecision)
                assert isinstance(result, ResourceAdmissionDecision)
                self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)

    def test_active_lease_invalidation_rejects_task_context_mismatch(self) -> None:
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account",),
            ),
            self.make_store(),
            "task-001",
            self.make_trace_store(),
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        evidence = self.healthy_evidence(
            evidence_id="evidence-invalid-wrong-task-context",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            lease_id=bundle.lease_id,
            bundle_id=bundle.bundle_id,
            reason="platform reported credential expired",
        )

        result = invalidate_active_lease_from_health_evidence(
            evidence=evidence,
            store=self.make_store(),
            task_context_task_id="task-other",
            operation="content_detail_by_url",
            resource_trace_store=self.make_trace_store(),
        )

        self.assertIsInstance(result, ResourceAdmissionDecision)
        assert isinstance(result, ResourceAdmissionDecision)
        self.assertEqual(result.decision_status, RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        snapshot = self.make_store().load_snapshot()
        account = next(record for record in snapshot.resources if record.resource_id == "account-001")
        self.assertEqual(account.status, "IN_USE")

    def test_non_invalid_evidence_cannot_trigger_invalidation(self) -> None:
        with self.assertRaises(ResourceHealthContractError):
            invalidate_active_lease_from_health_evidence(
                evidence=self.healthy_evidence(),
                store=self.make_store(),
                task_context_task_id="task-001",
                resource_trace_store=self.make_trace_store(),
            )


if __name__ == "__main__":
    unittest.main()
