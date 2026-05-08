# CHORE-0392 v1.2.0 resource governance evidence

## Purpose

This artifact records replayable evidence for `FR-0387` after the #390 runtime carrier and #391 consumer boundary work were merged. It proves the resource governance health contract can be replayed without adding runtime behavior, consumer migration, automatic login, automatic refresh, repair loops, or release closeout.

## Evidence Summary

- release：`v1.2.0`
- fr_ref：`FR-0387`
- work_item_ref：`#392 / CHORE-0392-v1-2-resource-governance-evidence`
- governing_spec_ref：`docs/specs/FR-0387-resource-governance-admission-and-health-contract/`
- runtime_pr_ref：`#393`
- consumer_boundary_pr_ref：`#394`
- status：`pass`
- covered scenarios：
  - healthy evidence admits before expiry
  - expired healthy evidence projects to stale and rejects
  - missing evidence projects to unknown and fail-closed rejects
  - malformed / unredacted / context-invalid evidence returns invalid_contract
  - pre-admission invalid evidence rejects without mutating available account resource
  - active invalid evidence bound to an active account/proxy lease performs Core-owned account invalidation while leaving proxy reusable
  - CredentialMaterial public projection stays redacted and omits private field names / values

## Structured Evidence Snapshot

`tests.runtime.test_resource_governance_evidence` rebuilds this report from runtime and consumer contracts, then compares it to the JSON snapshot below.

<!-- syvert:resource-governance-evidence-json:start -->
```json
{
  "consumer_boundary_pr_ref": "#394",
  "fr_ref": "FR-0387",
  "governing_spec_ref": "docs/specs/FR-0387-resource-governance-admission-and-health-contract/",
  "non_goals": {
    "automatic_login": false,
    "automatic_refresh": false,
    "release_closeout": false,
    "repair_loop": false
  },
  "public_boundary": {
    "consumer_boundary_ref": "PR #394",
    "credential_material_projection_redacted": true,
    "private_fields_absent_from_projection": true
  },
  "release": "v1.2.0",
  "report_id": "CHORE-0392-v1-2-resource-governance-evidence",
  "runtime_pr_ref": "#393",
  "scenarios": {
    "active_lease_invalid_core_invalidation": {
      "account_status_after": "INVALID",
      "proxy_status_after": "AVAILABLE",
      "result_type": "ResourceLease",
      "trace_closeout_types": [
        "invalidated",
        "released"
      ]
    },
    "expired_healthy_rejection": {
      "decision_status": "rejected",
      "fail_closed": true,
      "failure_reason": "credential_session_stale",
      "projected_session_health": "stale"
    },
    "healthy_admission": {
      "decision_status": "admitted",
      "fail_closed": false,
      "failure_reason": null,
      "projected_session_health": "healthy"
    },
    "invalid_contract_context_mismatch": {
      "decision_status": "invalid_contract",
      "fail_closed": true,
      "failure_reason": "health_evidence_contract_invalid",
      "projected_session_health": "unknown"
    },
    "invalid_contract_malformed": {
      "decision_status": "invalid_contract",
      "fail_closed": true,
      "failure_reason": "health_evidence_contract_invalid",
      "projected_session_health": "unknown"
    },
    "invalid_contract_unredacted": {
      "decision_status": "invalid_contract",
      "fail_closed": true,
      "failure_reason": "health_evidence_contract_invalid",
      "projected_session_health": "unknown"
    },
    "missing_evidence_unknown": {
      "decision_status": "rejected",
      "fail_closed": true,
      "failure_reason": "credential_session_unknown",
      "projected_session_health": "unknown"
    },
    "pre_admission_invalid_no_active_lease": {
      "account_status_after": "AVAILABLE",
      "decision_status": "rejected",
      "fail_closed": true,
      "failure_reason": "pre_admission_session_invalid",
      "projected_session_health": "invalid"
    }
  },
  "status": "pass",
  "validation_commands": [
    "python3 -m unittest tests.runtime.test_resource_governance_evidence tests.runtime.test_resource_health",
    "python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard",
    "python3 -m unittest tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_resource_trace_store tests.runtime.test_resource_bootstrap tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_platform_leakage",
    "python3 scripts/spec_guard.py --mode ci --all",
    "python3 scripts/docs_guard.py --mode ci",
    "python3 scripts/workflow_guard.py --mode ci",
    "BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha \"$BASE\" --head-sha \"$HEAD_SHA\" --head-ref issue-392-v1-2-resource-governance-evidence"
  ],
  "work_item_ref": "#392"
}
```
<!-- syvert:resource-governance-evidence-json:end -->

## Scenario Notes

- Healthy admission uses `ResourceHealthEvidence(status=healthy)` with `evaluated_at < expires_at`, returning `admitted / healthy`.
- Expired healthy evidence uses the same evidence at the expiry boundary, returning `rejected / stale`.
- Missing evidence keeps health-gated account admission fail-closed as `rejected / unknown`.
- Invalid contract evidence covers malformed timestamp, unredacted evidence, and adapter context mismatch; all bind to `health_evidence_contract_invalid`.
- Pre-admission invalid evidence does not change an available account resource.
- Active invalid evidence is lease-bound and task/adapter/capability/operation-bound; Core invalidates only the account credential session and releases the co-leased proxy back to `AVAILABLE`.
- Public projection evidence uses account material containing private fields including `cookies`, `ms_token`, `verify_fp`, `xsec_token`, `headers`, and `authorization`, then proves those field names and values do not appear in the projection.

## Non Goals

- No automatic login.
- No automatic session refresh.
- No repair loop.
- No release closeout.
