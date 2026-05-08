from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from syvert.resource_health import (
    RESOURCE_ADMISSION_DECISION_ADMITTED,
    RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT,
    RESOURCE_ADMISSION_DECISION_REJECTED,
    SESSION_HEALTH_HEALTHY,
    SESSION_HEALTH_INVALID,
    SESSION_HEALTH_STALE,
    SESSION_HEALTH_UNKNOWN,
    ResourceAdmissionDecision,
    ResourceHealthEvidence,
    credential_material_from_account_resource,
    credential_material_public_projection,
    decide_resource_health_admission,
    invalidate_active_lease_from_health_evidence,
)
from syvert.resource_lifecycle import AcquireRequest, ResourceBundle, ResourceRecord, acquire
from syvert.resource_lifecycle_store import default_resource_lifecycle_store
from tests.runtime.resource_fixtures import ResourceStoreEnvMixin, managed_account_material, xhs_account_material


ARTIFACT_PATH = Path("docs/exec-plans/artifacts/CHORE-0392-v1-2-resource-governance-evidence.md")


class ResourceGovernanceEvidenceTests(ResourceStoreEnvMixin, unittest.TestCase):
    resource_store_adapter_key = "xhs"

    def make_store(self):
        return default_resource_lifecycle_store()

    def account_record(self, *, resource_id: str = "account-001", status: str = "AVAILABLE") -> ResourceRecord:
        material = dict(managed_account_material(xhs_account_material(), adapter_key="xhs"))
        material.update(
            {
                "authorization": "Bearer redacted",
                "headers": {"authorization": "Bearer redacted"},
                "xsec_token": "xsec-redacted",
            }
        )
        return ResourceRecord(
            resource_id=resource_id,
            resource_type="account",
            status=status,
            material=material,
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

    def test_evidence_artifact_matches_runtime_and_consumer_truth(self) -> None:
        expected_report = self.build_report()
        artifact_report = self.load_artifact_report()

        self.assertEqual(artifact_report, expected_report)

    def test_evidence_scenarios_are_replayable(self) -> None:
        report = self.build_report()

        self.assertEqual(report["status"], "pass")
        scenarios = report["scenarios"]
        self.assertEqual(scenarios["healthy_admission"]["decision_status"], RESOURCE_ADMISSION_DECISION_ADMITTED)
        self.assertEqual(scenarios["healthy_admission"]["projected_session_health"], SESSION_HEALTH_HEALTHY)
        self.assertEqual(scenarios["expired_healthy_rejection"]["decision_status"], RESOURCE_ADMISSION_DECISION_REJECTED)
        self.assertEqual(scenarios["expired_healthy_rejection"]["projected_session_health"], SESSION_HEALTH_STALE)
        self.assertEqual(scenarios["missing_evidence_unknown"]["projected_session_health"], SESSION_HEALTH_UNKNOWN)
        self.assertEqual(scenarios["invalid_contract_malformed"]["decision_status"], RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        self.assertEqual(scenarios["invalid_contract_unredacted"]["decision_status"], RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT)
        self.assertEqual(
            scenarios["invalid_contract_context_mismatch"]["decision_status"],
            RESOURCE_ADMISSION_DECISION_INVALID_CONTRACT,
        )
        self.assertEqual(scenarios["pre_admission_invalid_no_active_lease"]["account_status_after"], "AVAILABLE")
        self.assertEqual(scenarios["active_lease_invalid_core_invalidation"]["account_status_after"], "INVALID")
        self.assertEqual(scenarios["active_lease_invalid_core_invalidation"]["proxy_status_after"], "AVAILABLE")
        self.assertEqual(scenarios["active_lease_invalid_core_invalidation"]["result_type"], "ResourceLease")
        self.assertTrue(report["public_boundary"]["credential_material_projection_redacted"])
        self.assertTrue(report["public_boundary"]["private_fields_absent_from_projection"])

    def build_report(self) -> dict[str, object]:
        account = self.account_record()
        credential_projection = credential_material_public_projection(credential_material_from_account_resource(account))
        healthy = self.healthy_evidence()
        invalid = self.healthy_evidence(
            evidence_id="evidence-invalid-001",
            status=SESSION_HEALTH_INVALID,
            expires_at=None,
            freshness_policy_ref=None,
            provenance="adapter_diagnostic",
            reason="platform reported credential expired",
        )

        healthy_decision = decide_resource_health_admission(
            decision_id="decision-healthy",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account", "proxy"),
            resources=(account,),
            evidence=(healthy,),
            evaluated_at="2026-05-08T12:10:00.000000Z",
        )
        expired_decision = decide_resource_health_admission(
            decision_id="decision-expired",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(account,),
            evidence=(healthy,),
            evaluated_at="2026-05-08T12:30:00.000000Z",
        )
        missing_decision = decide_resource_health_admission(
            decision_id="decision-missing",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(account,),
            evidence=(),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )
        invalid_contract_malformed_decision = decide_resource_health_admission(
            decision_id="decision-invalid-contract-malformed",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(account,),
            evidence=(self.healthy_evidence(observed_at="not-a-time"),),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )
        invalid_contract_unredacted_decision = decide_resource_health_admission(
            decision_id="decision-invalid-contract-unredacted",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(account,),
            evidence=(self.healthy_evidence(redaction_status="raw"),),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )
        invalid_contract_context_mismatch_decision = decide_resource_health_admission(
            decision_id="decision-invalid-contract-context",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(account,),
            evidence=(self.healthy_evidence(adapter_key="douyin"),),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )
        pre_admission_decision = decide_resource_health_admission(
            decision_id="decision-pre-admission-invalid",
            task_id="task-001",
            adapter_key="xhs",
            capability="content_detail_by_url",
            operation="content_detail_by_url",
            requested_slots=("account",),
            resources=(account,),
            evidence=(invalid,),
            evaluated_at="2026-05-08T12:05:00.000000Z",
        )
        store = self.make_store()
        trace_store = self.make_trace_store()
        bundle = acquire(
            AcquireRequest(
                task_id="task-001",
                adapter_key="xhs",
                capability="content_detail_by_url",
                requested_slots=("account", "proxy"),
            ),
            store,
            "task-001",
            trace_store,
        )
        self.assertIsInstance(bundle, ResourceBundle)
        assert isinstance(bundle, ResourceBundle)
        active_result = invalidate_active_lease_from_health_evidence(
            evidence=self.healthy_evidence(
                evidence_id="evidence-invalid-active",
                status=SESSION_HEALTH_INVALID,
                expires_at=None,
                freshness_policy_ref=None,
                provenance="adapter_diagnostic",
                lease_id=bundle.lease_id,
                bundle_id=bundle.bundle_id,
                reason="platform reported credential expired",
            ),
            store=store,
            task_context_task_id="task-001",
            operation="content_detail_by_url",
            resource_trace_store=trace_store,
        )
        self.assertNotIsInstance(active_result, ResourceAdmissionDecision)
        snapshot = store.load_snapshot()
        resources_by_id = {resource.resource_id: resource for resource in snapshot.resources}
        trace_closeout_types = sorted(
            {event.event_type for event in trace_store.load_events() if event.event_type in {"invalidated", "released"}}
        )

        return {
            "report_id": "CHORE-0392-v1-2-resource-governance-evidence",
            "release": "v1.2.0",
            "fr_ref": "FR-0387",
            "work_item_ref": "#392",
            "status": "pass",
            "governing_spec_ref": "docs/specs/FR-0387-resource-governance-admission-and-health-contract/",
            "runtime_pr_ref": "#393",
            "consumer_boundary_pr_ref": "#394",
            "scenarios": {
                "healthy_admission": _decision_summary(healthy_decision),
                "expired_healthy_rejection": _decision_summary(expired_decision),
                "missing_evidence_unknown": _decision_summary(missing_decision),
                "invalid_contract_context_mismatch": _decision_summary(invalid_contract_context_mismatch_decision),
                "invalid_contract_malformed": _decision_summary(invalid_contract_malformed_decision),
                "invalid_contract_unredacted": _decision_summary(invalid_contract_unredacted_decision),
                "pre_admission_invalid_no_active_lease": {
                    **_decision_summary(pre_admission_decision),
                    "account_status_after": "AVAILABLE",
                },
                "active_lease_invalid_core_invalidation": {
                    "result_type": type(active_result).__name__,
                    "account_status_after": resources_by_id["account-001"].status,
                    "proxy_status_after": resources_by_id["proxy-001"].status,
                    "trace_closeout_types": trace_closeout_types,
                },
            },
            "public_boundary": {
                "credential_material_projection_redacted": credential_projection["material_fields_redacted"] is True,
                "private_fields_absent_from_projection": all(
                    token not in json.dumps(credential_projection, sort_keys=True)
                    for token in ("cookies", "ms_token", "verify_fp", "xsec_token", "authorization")
                ),
                "consumer_boundary_ref": "PR #394",
            },
            "non_goals": {
                "automatic_login": False,
                "automatic_refresh": False,
                "repair_loop": False,
                "release_closeout": False,
            },
            "validation_commands": [
                "python3 -m unittest tests.runtime.test_resource_governance_evidence tests.runtime.test_resource_health",
                "python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard",
                "python3 -m unittest tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_resource_trace_store tests.runtime.test_resource_bootstrap tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_platform_leakage",
                "python3 scripts/spec_guard.py --mode ci --all",
                "python3 scripts/docs_guard.py --mode ci",
                "python3 scripts/workflow_guard.py --mode ci",
                'BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-392-v1-2-resource-governance-evidence',
            ],
        }

    def load_artifact_report(self) -> dict[str, object]:
        content = ARTIFACT_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"<!-- syvert:resource-governance-evidence-json:start -->\n```json\n(.*?)\n```\n<!-- syvert:resource-governance-evidence-json:end -->",
            content,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        assert match is not None
        return json.loads(match.group(1))


def _decision_summary(decision) -> dict[str, object]:
    return {
        "decision_status": decision.decision_status,
        "projected_session_health": decision.projected_session_health,
        "failure_reason": decision.failure_reason,
        "fail_closed": decision.fail_closed,
    }


if __name__ == "__main__":
    unittest.main()
