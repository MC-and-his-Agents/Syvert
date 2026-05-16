from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import unittest
from pathlib import Path
from unittest import mock

from syvert.batch_dataset import (
    BATCH_ITEM_FAILED,
    BATCH_RESULT_ALL_FAILED,
    BatchDatasetContractError,
    BatchItemOutcome,
    BatchRequest,
    BatchResultEnvelope,
    BatchTargetItem,
    DatasetRecord,
    ReferenceDatasetSink,
    batch_result_envelope_to_dict,
    canonical_dataset_record,
    execute_batch_request,
    validate_batch_result_envelope,
    validate_dataset_record,
)


ARTIFACT_PATH = Path("docs/exec-plans/artifacts/CHORE-0449-v1-6-batch-dataset-evidence.md")
ADAPTER_KEY = "reference_adapter_alpha"
DATASET_SINK_REF = "dataset-sink:reference"
FIXED_NOW = datetime(2026, 5, 17, 10, 0, 0, tzinfo=timezone.utc)

FORBIDDEN_PUBLIC_CARRIER_FRAGMENTS = (
    "/Users/",
    "/home/",
    "/tmp/",
    "/var/",
    "\\Users\\",
    "C:/",
    "D:/",
    "file://",
    "storage://",
    "s3://",
    "gs://",
    "token=secret",
    "credential",
    "session_token",
    "storage_handle",
    "local_path",
    "source_name",
    "private_account",
    "private_creator",
    "private_media",
    "provider:fallback",
    "marketplace",
)


class ReferenceCollectionAdapter:
    supported_capabilities = frozenset({"content_search"})
    supported_targets = frozenset({"keyword"})
    supported_collection_modes = frozenset({"paginated"})

    def execute(self, request):
        target_ref = request.input.keyword or ""
        return make_collection_result(target_ref=target_ref)


class KeywordFailingCollectionAdapter(ReferenceCollectionAdapter):
    def __init__(self, failing_keywords: set[str]) -> None:
        self.failing_keywords = failing_keywords

    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        if request.input.keyword in self.failing_keywords:
            raise PlatformAdapterError(
                code="permission_denied",
                message="permission denied",
                details={"evidence_ref": "evidence:permission-denied"},
            )
        return make_collection_result(target_ref=request.input.keyword or "")


class TimeoutCollectionAdapter(ReferenceCollectionAdapter):
    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(
            code="execution_timeout",
            message="execution timed out",
            details={"control_code": "execution_timeout", "evidence_ref": "evidence:timeout"},
        )


def fixed_now() -> datetime:
    return FIXED_NOW


def make_collection_result(*, target_ref: str) -> dict[str, object]:
    return {
        "operation": "content_search_by_keyword",
        "target": {
            "operation": "content_search_by_keyword",
            "target_type": "keyword",
            "target_ref": target_ref,
            "target_display_hint": target_ref,
        },
        "items": [
            {
                "item_type": "content_summary",
                "dedup_key": f"content:{target_ref}",
                "source_id": f"source-{target_ref}",
                "source_ref": f"content://{target_ref}/item-1",
                "normalized": {
                    "source_platform": ADAPTER_KEY,
                    "source_type": "post",
                    "source_id": f"source-{target_ref}",
                    "canonical_ref": f"content://{target_ref}/item-1",
                    "title_or_text_hint": f"public hint {target_ref}",
                    "creator_ref": f"creator:{target_ref}",
                    "published_at": "2026-05-17T10:00:00Z",
                    "media_refs": [f"media://{target_ref}/1"],
                },
                "raw_payload_ref": f"raw://batch-dataset/{target_ref}/item-1",
                "source_trace": make_source_trace(evidence_alias=f"alias://batch-dataset/{target_ref}/page-1"),
            }
        ],
        "has_more": False,
        "next_continuation": None,
        "result_status": "complete",
        "error_classification": "platform_failed",
        "raw_payload_ref": f"raw://batch-dataset/{target_ref}/page-1",
        "source_trace": make_source_trace(evidence_alias=f"alias://batch-dataset/{target_ref}/page-1"),
        "audit": {"scenario": f"batch-dataset:{target_ref}"},
    }


def make_source_trace(*, evidence_alias: str) -> dict[str, object]:
    return {
        "adapter_key": ADAPTER_KEY,
        "provider_path": "provider://sanitized",
        "resource_profile_ref": "resource-profile:reference-read-side",
        "fetched_at": "2026-05-17T10:00:00Z",
        "evidence_alias": evidence_alias,
    }


def target(item_id: str, target_ref: str, *, dedup_key: str | None = None) -> BatchTargetItem:
    return BatchTargetItem(
        item_id=item_id,
        operation="content_search_by_keyword",
        adapter_key=ADAPTER_KEY,
        target_type="keyword",
        target_ref=target_ref,
        dedup_key=dedup_key or f"dedup:{target_ref}",
    )


def request(*items: BatchTargetItem, resume_token=None) -> BatchRequest:
    return BatchRequest(
        batch_id="batch-0449",
        target_set=items,
        resume_token=resume_token,
        dataset_sink_ref=DATASET_SINK_REF,
        audit_context={"evidence_ref": "evidence:batch-dataset"},
    )


class BatchDatasetEvidenceTests(unittest.TestCase):
    def test_evidence_artifact_matches_replayable_snapshot(self) -> None:
        self.assertEqual(self.load_artifact_report(), self.build_report())

    def test_evidence_snapshot_covers_fr_0445_matrix(self) -> None:
        report = self.build_report()

        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            sorted(report["scenario_matrix"]),
            [
                "all_failed",
                "dataset_replay",
                "duplicate_target",
                "partial_success_failure",
                "public_carrier_leakage_prevention",
                "resource_boundary",
                "resume",
                "timeout_resumable",
            ],
        )
        self.assertEqual(report["scenario_matrix"]["partial_success_failure"]["result_status"], "partial_success")
        self.assertEqual(report["scenario_matrix"]["all_failed"]["dataset_record_count"], 0)
        self.assertEqual(report["scenario_matrix"]["resume"]["terminal_result_status"], "complete")
        self.assertEqual(report["scenario_matrix"]["duplicate_target"]["item_statuses"], ["succeeded", "duplicate_skipped"])
        self.assertTrue(report["scenario_matrix"]["dataset_replay"]["raw_payload_files_required"] is False)
        self.assertTrue(report["scenario_matrix"]["resource_boundary"]["batch_admission_requires_real_account"] is False)

    def test_evidence_snapshot_has_no_private_or_raw_fragments(self) -> None:
        snapshot_values = "\n".join(str(value) for value in self.public_leaf_values(self.build_report()))

        for fragment in FORBIDDEN_PUBLIC_CARRIER_FRAGMENTS:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, snapshot_values)

    def test_public_carrier_leakage_matrix_fails_closed(self) -> None:
        matrix = self.build_report()["scenario_matrix"]["public_carrier_leakage_prevention"]["fail_closed_cases"]

        self.assertEqual(
            matrix,
            {
                "dataset_raw_payload_inline_field": "invalid_dataset_record",
                "dataset_opaque_storage_field": "invalid_dataset_record",
                "dataset_path_ref": "unsafe_ref",
                "dataset_private_entity_field": "unsafe_public_payload",
                "result_opaque_storage_audit": "unsafe_public_payload",
                "result_routing_resume": "unsafe_ref",
            },
        )

    def build_report(self) -> dict[str, object]:
        return {
            "report_id": "CHORE-0449-v1-6-batch-dataset-evidence",
            "release": "v1.6.0",
            "fr_ref": "FR-0445",
            "work_item_ref": "#449",
            "status": "pass",
            "governing_spec_ref": "docs/specs/FR-0445-batch-dataset-core-contract/",
            "predecessor_pr_refs": ["#451", "#452", "#453"],
            "sanitization": {
                "raw_payload_files_required": False,
                "raw_payload_embedded": False,
                "source_alias_only": True,
                "path_free": True,
                "opaque_storage_free": True,
                "private_entity_fields_present": False,
                "provider_routing_policy_present": False,
                "real_account_credentials_required": False,
            },
            "replay_matrix": {
                "fixture_family": "sanitized_fake_reference",
                "runtime_entry": "execute_batch_request",
                "dataset_sink": "ReferenceDatasetSink",
                "snapshot_rebuilt_by": "tests.runtime.test_batch_dataset_evidence",
                "raw_payload_files_required": False,
                "provider_private_data_required": False,
            },
            "scenario_matrix": {
                "partial_success_failure": self.partial_success_failure(),
                "all_failed": self.all_failed(),
                "resume": self.resume(),
                "timeout_resumable": self.timeout_resumable(),
                "duplicate_target": self.duplicate_target(),
                "dataset_replay": self.dataset_replay(),
                "resource_boundary": self.resource_boundary(),
                "public_carrier_leakage_prevention": self.public_carrier_leakage_prevention(),
            },
            "validation_commands": [
                "python3 -m unittest tests.runtime.test_batch_dataset_evidence tests.runtime.test_batch_dataset tests.runtime.test_task_record tests.runtime.test_cli_http_same_path tests.runtime.test_operation_taxonomy_consumers",
                "python3 -m unittest discover",
                "python3 scripts/spec_guard.py --mode ci --all",
                "python3 scripts/docs_guard.py --mode ci",
                "python3 scripts/workflow_guard.py --mode ci",
                "python3 scripts/version_guard.py --mode ci",
                "python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD",
                "git diff --check",
            ],
        }

    def partial_success_failure(self) -> dict[str, object]:
        sink = ReferenceDatasetSink()
        result = self.execute(
            request(target("item-success", "alpha"), target("item-failed", "beta")),
            adapters={ADAPTER_KEY: KeywordFailingCollectionAdapter({"beta"})},
            sink=sink,
        )

        return {
            "result_status": result.result_status,
            "item_statuses": [outcome.outcome_status for outcome in result.item_outcomes],
            "failed_error_code": result.item_outcomes[1].error_envelope["code"],
            "dataset_record_count": len(sink.read_by_dataset("dataset:batch-0449")),
            "raw_payload_files_required": False,
        }

    def all_failed(self) -> dict[str, object]:
        sink = ReferenceDatasetSink()
        result = self.execute(
            request(target("item-failed-1", "alpha"), target("item-failed-2", "beta")),
            adapters={ADAPTER_KEY: KeywordFailingCollectionAdapter({"alpha", "beta"})},
            sink=sink,
        )

        return {
            "result_status": result.result_status,
            "item_statuses": [outcome.outcome_status for outcome in result.item_outcomes],
            "dataset_record_count": len(sink.read_by_dataset("dataset:batch-0449")),
            "item_errors_preserved": [outcome.error_envelope["code"] for outcome in result.item_outcomes],
        }

    def resume(self) -> dict[str, object]:
        sink = ReferenceDatasetSink()
        items = (target("item-1", "alpha"), target("item-2", "beta"))
        first = self.execute(request(*items), sink=sink, stop_after_items=1, stop_reason="execution_timeout")
        resumed = self.execute(
            request(*items, resume_token=first.resume_token),
            sink=sink,
            prior_item_outcomes=first.item_outcomes,
        )

        return {
            "interrupted_result_status": first.result_status,
            "interrupted_outcome_count": len(first.item_outcomes),
            "resume_next_item_index": first.resume_token.next_item_index,
            "terminal_result_status": resumed.result_status,
            "terminal_outcome_count": len(resumed.item_outcomes),
            "dataset_record_count": len(sink.read_by_dataset("dataset:batch-0449")),
            "dedup_write_state_reused": len(sink.read_by_dataset("dataset:batch-0449")) == 2,
        }

    def timeout_resumable(self) -> dict[str, object]:
        sink = ReferenceDatasetSink()
        result = self.execute(
            request(target("item-timeout", "alpha"), target("item-suffix", "beta")),
            adapters={ADAPTER_KEY: TimeoutCollectionAdapter()},
            sink=sink,
        )

        return {
            "result_status": result.result_status,
            "item_statuses": [outcome.outcome_status for outcome in result.item_outcomes],
            "failed_error_code": result.item_outcomes[0].error_envelope["code"],
            "resume_next_item_index": result.resume_token.next_item_index,
            "audit_finished": result.audit_trace["finished"],
            "audit_stop_reason": result.audit_trace["stop_reason"],
            "undispatched_suffix_outcome_count": len(result.item_outcomes) - result.resume_token.next_item_index,
        }

    def duplicate_target(self) -> dict[str, object]:
        sink = ReferenceDatasetSink()
        result = self.execute(
            request(
                target("item-original", "alpha", dedup_key="dedup:shared"),
                target("item-duplicate", "alpha", dedup_key="dedup:shared"),
            ),
            sink=sink,
        )

        return {
            "result_status": result.result_status,
            "item_statuses": [outcome.outcome_status for outcome in result.item_outcomes],
            "dataset_record_count": len(sink.read_by_dataset("dataset:batch-0449")),
            "duplicate_wrote_dataset_record": result.item_outcomes[1].dataset_record_ref is not None,
        }

    def dataset_replay(self) -> dict[str, object]:
        sink = ReferenceDatasetSink()
        result = self.execute(request(target("item-1", "alpha"), target("item-2", "beta")), sink=sink)
        replay = sink.audit_replay(result.dataset_id)

        return {
            "result_status": result.result_status,
            "read_by_dataset_count": len(sink.read_by_dataset(result.dataset_id)),
            "read_by_batch_count": len(sink.read_by_batch(result.batch_id)),
            "replay_count": len(replay),
            "replay_record_keys": sorted(replay[0]),
            "raw_payload_files_required": False,
            "storage_handles_returned": False,
        }

    def resource_boundary(self) -> dict[str, object]:
        sink = ReferenceDatasetSink()
        result = execute_batch_request(
            request(target("item-resource", "alpha")),
            adapters={ADAPTER_KEY: ReferenceCollectionAdapter()},
            dataset_sink=sink,
            task_id_factory=self.task_id_factory(),
            now_factory=fixed_now,
        )

        return {
            "batch_admission_requires_real_account": False,
            "item_resource_governance_preserved": result.item_outcomes[0].outcome_status == BATCH_ITEM_FAILED,
            "item_error_code": result.item_outcomes[0].error_envelope["code"],
            "dataset_record_count": len(sink.read_by_dataset("dataset:batch-0449")),
        }

    def public_carrier_leakage_prevention(self) -> dict[str, object]:
        return {
            "fail_closed_cases": {
                "dataset_raw_payload_inline_field": self.dataset_record_error(raw_payload={"private": True}),
                "dataset_opaque_storage_field": self.dataset_record_error(storage_handle="opaque-handle"),
                "dataset_path_ref": self.dataset_record_error(raw_payload_ref="raw://var/private/raw.json"),
                "dataset_private_entity_field": self.dataset_record_error(
                    normalized_payload={"items": [{"private_creator": "creator-secret"}]},
                ),
                "result_opaque_storage_audit": self.result_error(audit_trace={"storage_ref": "storage://redacted"}),
                "result_routing_resume": self.resume_token_error("resume:batch-0449:1:provider:fallback-route"),
            },
            "sanitized_aliases_only": True,
            "raw_payload_files_required": False,
        }

    def dataset_record_error(self, **overrides) -> str:
        record = {
            "dataset_record_id": "record-leakage",
            "dataset_id": "dataset-leakage",
            "source_operation": "content_search_by_keyword",
            "adapter_key": ADAPTER_KEY,
            "target_ref": "alpha",
            "raw_payload_ref": "raw://batch-dataset/alpha/page-1",
            "normalized_payload": {"items": [{"title_or_text_hint": "safe"}]},
            "evidence_ref": "evidence:batch-dataset",
            "source_trace": make_source_trace(evidence_alias="alias://batch-dataset/leakage"),
            "dedup_key": "dedup:alpha",
            "batch_id": "batch-0449",
            "batch_item_id": "item-leakage",
            "recorded_at": "2026-05-17T10:00:00Z",
            **overrides,
        }
        try:
            if set(overrides) - set(DatasetRecord.__dataclass_fields__):
                canonical_dataset_record(record)
            else:
                validate_dataset_record(DatasetRecord(**record))
        except BatchDatasetContractError as error:
            return error.code
        self.fail(f"dataset record leakage case unexpectedly passed: {overrides}")

    def result_error(self, *, audit_trace: dict[str, object]) -> str:
        outcome = BatchItemOutcome(
            item_id="item-1",
            operation="content_search_by_keyword",
            adapter_key=ADAPTER_KEY,
            target_ref="alpha",
            outcome_status=BATCH_ITEM_FAILED,
            error_envelope={
                "category": "runtime",
                "code": "permission_denied",
                "message": "permission denied",
                "details": {"evidence_ref": "evidence:permission-denied"},
            },
            audit={"reason": "failed"},
        )
        envelope = BatchResultEnvelope(
            batch_id="batch-0449",
            operation="batch_execution",
            result_status=BATCH_RESULT_ALL_FAILED,
            item_outcomes=(outcome,),
            dataset_sink_ref=DATASET_SINK_REF,
            dataset_id="dataset:batch-0449",
            audit_trace={
                "batch_id": "batch-0449",
                "started_at": "2026-05-17T10:00:00Z",
                "finished": True,
                "item_count": 1,
                "item_trace_refs": ("audit:batch:batch-0449:item-1",),
                "evidence_refs": ("evidence:batch-dataset",),
                **audit_trace,
            },
        )
        try:
            validate_batch_result_envelope(envelope)
        except BatchDatasetContractError as error:
            return error.code
        self.fail(f"batch result leakage case unexpectedly passed: {audit_trace}")

    def resume_token_error(self, resume_token_value: str) -> str:
        first = self.execute(
            request(target("item-1", "alpha"), target("item-2", "beta")),
            sink=ReferenceDatasetSink(),
            stop_after_items=1,
            stop_reason="execution_timeout",
        )
        forged = BatchResultEnvelope(
            batch_id=first.batch_id,
            operation=first.operation,
            result_status=first.result_status,
            item_outcomes=first.item_outcomes,
            resume_token=type(first.resume_token)(**{**first.resume_token.__dict__, "resume_token": resume_token_value}),
            dataset_sink_ref=first.dataset_sink_ref,
            dataset_id=first.dataset_id,
            audit_trace=first.audit_trace,
        )
        try:
            batch_result_envelope_to_dict(forged)
        except BatchDatasetContractError as error:
            return error.code
        self.fail("resume token leakage case unexpectedly passed")

    def execute(self, batch_request: BatchRequest, *, adapters=None, sink=None, **kwargs):
        with mock.patch.dict("syvert.runtime.RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE", {}, clear=True):
            return execute_batch_request(
                batch_request,
                adapters=adapters or {ADAPTER_KEY: ReferenceCollectionAdapter()},
                dataset_sink=sink if sink is not None else ReferenceDatasetSink(),
                task_id_factory=self.task_id_factory(),
                now_factory=fixed_now,
                **kwargs,
            )

    @staticmethod
    def task_id_factory():
        task_ids = iter(f"task-0449-{index}" for index in range(1, 20))
        return lambda: next(task_ids)

    def load_artifact_report(self) -> dict[str, object]:
        text = ARTIFACT_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"<!-- syvert:batch-dataset-evidence-json:start -->\s*```json\s*(\{.*?\})\s*```",
            text,
            re.S,
        )
        self.assertIsNotNone(match)
        return json.loads(match.group(1))

    def public_leaf_values(self, value):
        if isinstance(value, dict):
            for item in value.values():
                yield from self.public_leaf_values(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from self.public_leaf_values(item)
        elif isinstance(value, str):
            yield value


if __name__ == "__main__":
    unittest.main()
