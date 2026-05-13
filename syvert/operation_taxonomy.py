from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


CAPABILITY_LIFECYCLE_PROPOSED = "proposed"
CAPABILITY_LIFECYCLE_EXPERIMENTAL = "experimental"
CAPABILITY_LIFECYCLE_STABLE = "stable"
CAPABILITY_LIFECYCLE_DEPRECATED = "deprecated"
CAPABILITY_LIFECYCLES = frozenset(
    {
        CAPABILITY_LIFECYCLE_PROPOSED,
        CAPABILITY_LIFECYCLE_EXPERIMENTAL,
        CAPABILITY_LIFECYCLE_STABLE,
        CAPABILITY_LIFECYCLE_DEPRECATED,
    }
)

ADMISSION_STATUS_ADMITTED = "admitted"
ADMISSION_STATUS_INVALID_CONTRACT = "invalid_contract"
ADMISSION_STATUS_REJECTED = "rejected"

ADMISSION_ERROR_INVALID_ENTRY = "invalid_taxonomy_entry"
ADMISSION_ERROR_DUPLICATE_OPERATION = "duplicate_operation"
ADMISSION_ERROR_NOT_STABLE = "operation_not_stable"

FORBIDDEN_TAXONOMY_FIELDS = frozenset(
    {
        "provider_selector",
        "provider_selection",
        "provider_routing",
        "provider_fallback",
        "fallback",
        "fallback_order",
        "priority",
        "ranking",
        "marketplace",
        "marketplace_listing",
        "provider_product_support",
        "sla",
        "workflow",
        "application_workflow",
        "content_library",
        "platform_private_object",
        "platform_private_business_object",
    }
)


@dataclass(frozen=True)
class OperationTaxonomyEntry:
    capability_family: str
    operation: str
    target_type: str
    execution_mode: str
    collection_mode: str
    lifecycle: str
    runtime_delivery: bool
    contract_refs: tuple[str, ...]
    admission_evidence_refs: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmissionReport:
    status: str
    capability_family: str | None
    operation: str | None
    lifecycle: str | None
    runtime_delivery: bool | None
    error_code: str | None = None
    message: str | None = None
    details: Mapping[str, Any] | None = None


class OperationTaxonomyContractError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


STABLE_CONTENT_DETAIL_ENTRY = OperationTaxonomyEntry(
    capability_family="content_detail",
    operation="content_detail_by_url",
    target_type="url",
    execution_mode="single",
    collection_mode="hybrid",
    lifecycle=CAPABILITY_LIFECYCLE_STABLE,
    runtime_delivery=True,
    contract_refs=(
        "FR-0002",
        "FR-0004",
        "FR-0024",
        "FR-0025",
        "FR-0026",
        "FR-0368",
    ),
    admission_evidence_refs=(
        "tests.runtime.test_real_adapter_regression",
        "tests.runtime.test_third_party_adapter_contract_entry",
        "tests.runtime.test_cli_http_same_path",
    ),
    notes=("v1.0.0 stable baseline; must not be rewritten by proposed candidates.",),
)

STABLE_CONTENT_SEARCH_BY_KEYWORD_ENTRY = OperationTaxonomyEntry(
    capability_family="content_search",
    operation="content_search_by_keyword",
    target_type="keyword",
    execution_mode="single",
    collection_mode="paginated",
    lifecycle=CAPABILITY_LIFECYCLE_STABLE,
    runtime_delivery=True,
    contract_refs=("FR-0403",),
    admission_evidence_refs=(
        "tests.runtime.test_read_side_collection",
        "tests.runtime.test_operation_taxonomy_admission_evidence",
    ),
    notes=("v1.3.0 runtime contract frozen; collection continuation + envelope shared shape.",),
)

STABLE_CONTENT_LIST_BY_CREATOR_ENTRY = OperationTaxonomyEntry(
    capability_family="content_list",
    operation="content_list_by_creator",
    target_type="creator",
    execution_mode="single",
    collection_mode="paginated",
    lifecycle=CAPABILITY_LIFECYCLE_STABLE,
    runtime_delivery=True,
    contract_refs=("FR-0403",),
    admission_evidence_refs=(
        "tests.runtime.test_read_side_collection",
        "tests.runtime.test_operation_taxonomy_admission_evidence",
    ),
    notes=("v1.3.0 runtime contract frozen; collection continuation + envelope shared shape.",),
)

STABLE_COMMENT_COLLECTION_ENTRY = OperationTaxonomyEntry(
    capability_family="comment_collection",
    operation="comment_collection",
    target_type="content",
    execution_mode="single",
    collection_mode="paginated",
    lifecycle=CAPABILITY_LIFECYCLE_STABLE,
    runtime_delivery=True,
    contract_refs=("FR-0404",),
    admission_evidence_refs=(
        "tests.runtime.test_comment_collection",
        "tests.runtime.test_operation_taxonomy",
    ),
    notes=("v1.4.0 comment collection runtime contract frozen; comment-specific hierarchy and visibility surface.",),
)

STABLE_CREATOR_PROFILE_BY_ID_ENTRY = OperationTaxonomyEntry(
    capability_family="creator_profile",
    operation="creator_profile_by_id",
    target_type="creator",
    execution_mode="single",
    collection_mode="direct",
    lifecycle=CAPABILITY_LIFECYCLE_STABLE,
    runtime_delivery=True,
    contract_refs=("FR-0405",),
    admission_evidence_refs=("tests.runtime.test_operation_taxonomy",),
    notes=("v1.5.0 creator profile runtime carrier; one-shot creator read contract and platform-neutral profile result.",),
)

STABLE_MEDIA_ASSET_FETCH_BY_REF_ENTRY = OperationTaxonomyEntry(
    capability_family="media_asset_fetch",
    operation="media_asset_fetch_by_ref",
    target_type="media_ref",
    execution_mode="single",
    collection_mode="direct",
    lifecycle=CAPABILITY_LIFECYCLE_STABLE,
    runtime_delivery=True,
    contract_refs=("FR-0405",),
    admission_evidence_refs=("tests.runtime.test_operation_taxonomy",),
    notes=(
        "v1.5.0 media asset fetch runtime carrier; one-shot media ref read contract with fail-closed no-storage boundary.",
    ),
)

STABLE_BATCH_EXECUTION_ENTRY = OperationTaxonomyEntry(
    capability_family="batch_execution",
    operation="batch_execution",
    target_type="operation_batch",
    execution_mode="batch",
    collection_mode="batch",
    lifecycle=CAPABILITY_LIFECYCLE_STABLE,
    runtime_delivery=True,
    contract_refs=("FR-0445",),
    admission_evidence_refs=(
        "tests.runtime.test_batch_dataset",
        "tests.runtime.test_operation_taxonomy",
    ),
    notes=("v1.6.0 batch/dataset Core contract carrier; wraps stable read-side item operations only.",),
)

PROPOSED_OPERATION_TAXONOMY_ENTRIES = (
    OperationTaxonomyEntry(
        capability_family="content_search",
        operation="content_search",
        target_type="query",
        execution_mode="single",
        collection_mode="paginated",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
    OperationTaxonomyEntry(
        capability_family="content_list",
        operation="content_list",
        target_type="collection",
        execution_mode="single",
        collection_mode="paginated",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
    OperationTaxonomyEntry(
        capability_family="creator_profile",
        operation="creator_profile",
        target_type="creator",
        execution_mode="single",
        collection_mode="single",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
    OperationTaxonomyEntry(
        capability_family="media_asset_fetch",
        operation="media_asset_fetch",
        target_type="media_asset",
        execution_mode="single",
        collection_mode="batch",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
    OperationTaxonomyEntry(
        capability_family="media_upload",
        operation="media_upload",
        target_type="media_asset",
        execution_mode="single",
        collection_mode="single",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
    OperationTaxonomyEntry(
        capability_family="content_publish",
        operation="content_publish",
        target_type="draft",
        execution_mode="single",
        collection_mode="single",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
    OperationTaxonomyEntry(
        capability_family="scheduled_execution",
        operation="scheduled_execution",
        target_type="schedule",
        execution_mode="scheduled",
        collection_mode="single",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
    OperationTaxonomyEntry(
        capability_family="dataset_sink",
        operation="dataset_sink",
        target_type="dataset",
        execution_mode="single",
        collection_mode="stream",
        lifecycle=CAPABILITY_LIFECYCLE_PROPOSED,
        runtime_delivery=False,
        contract_refs=("FR-0368",),
        admission_evidence_refs=(),
        notes=("reserved candidate only; no v1.1 runtime capability",),
    ),
)

DEFAULT_OPERATION_TAXONOMY = (
    STABLE_CONTENT_DETAIL_ENTRY,
    STABLE_CONTENT_SEARCH_BY_KEYWORD_ENTRY,
    STABLE_CONTENT_LIST_BY_CREATOR_ENTRY,
    STABLE_COMMENT_COLLECTION_ENTRY,
    STABLE_CREATOR_PROFILE_BY_ID_ENTRY,
    STABLE_MEDIA_ASSET_FETCH_BY_REF_ENTRY,
    STABLE_BATCH_EXECUTION_ENTRY,
    *PROPOSED_OPERATION_TAXONOMY_ENTRIES,
)


def operation_taxonomy_entries() -> tuple[OperationTaxonomyEntry, ...]:
    return DEFAULT_OPERATION_TAXONOMY


def proposed_operation_taxonomy_entries() -> tuple[OperationTaxonomyEntry, ...]:
    return PROPOSED_OPERATION_TAXONOMY_ENTRIES


def validate_operation_taxonomy_entry(
    entry: OperationTaxonomyEntry | Mapping[str, Any],
) -> AdmissionReport:
    normalized = _normalize_entry(entry)
    if not isinstance(normalized, OperationTaxonomyEntry):
        return _invalid_entry_report(None, None, None, None, normalized)
    surface_error = _validate_entry_surface(entry)
    if surface_error is not None:
        return _invalid_entry_report(
            normalized.capability_family,
            normalized.operation,
            normalized.lifecycle,
            normalized.runtime_delivery,
            surface_error,
        )
    value_error = _validate_entry_values(normalized)
    if value_error is not None:
        return _invalid_entry_report(
            normalized.capability_family,
            normalized.operation,
            normalized.lifecycle,
            normalized.runtime_delivery,
            value_error,
        )
    return AdmissionReport(
        status=ADMISSION_STATUS_ADMITTED,
        capability_family=normalized.capability_family,
        operation=normalized.operation,
        lifecycle=normalized.lifecycle,
        runtime_delivery=normalized.runtime_delivery,
    )


def validate_operation_taxonomy_registry(
    entries: Iterable[OperationTaxonomyEntry | Mapping[str, Any]] = DEFAULT_OPERATION_TAXONOMY,
) -> tuple[AdmissionReport, ...]:
    reports = [validate_operation_taxonomy_entry(entry) for entry in entries]
    normalized_entries = tuple(
        entry for entry in (_normalize_entry(entry) for entry in entries) if isinstance(entry, OperationTaxonomyEntry)
    )
    for duplicate in _duplicate_operation_reports(normalized_entries):
        reports.append(duplicate)
    return tuple(reports)


def stable_operation_entry(
    *,
    operation: str,
    target_type: str,
    collection_mode: str,
    entries: Iterable[OperationTaxonomyEntry | Mapping[str, Any]] = DEFAULT_OPERATION_TAXONOMY,
) -> OperationTaxonomyEntry:
    reports = validate_operation_taxonomy_registry(entries)
    invalid_reports = tuple(report for report in reports if report.status != ADMISSION_STATUS_ADMITTED)
    if invalid_reports:
        raise OperationTaxonomyContractError(
            ADMISSION_ERROR_INVALID_ENTRY,
            "operation taxonomy registry contains invalid entries",
            details={"reports": tuple(report.__dict__ for report in invalid_reports)},
        )

    matched = tuple(
        entry
        for entry in (_normalize_entry(entry) for entry in entries)
        if isinstance(entry, OperationTaxonomyEntry)
        and entry.operation == operation
        and entry.target_type == target_type
        and entry.collection_mode == collection_mode
    )
    stable_matches = tuple(
        entry
        for entry in matched
        if entry.lifecycle == CAPABILITY_LIFECYCLE_STABLE and entry.runtime_delivery is True
    )
    if len(stable_matches) == 1:
        return stable_matches[0]
    if len(stable_matches) > 1:
        raise OperationTaxonomyContractError(
            ADMISSION_ERROR_DUPLICATE_OPERATION,
            "stable operation lookup found more than one stable entry",
            details={"operation": operation, "target_type": target_type, "collection_mode": collection_mode},
        )
    raise OperationTaxonomyContractError(
        ADMISSION_ERROR_NOT_STABLE,
        "operation is not admitted as a stable runtime capability",
        details={"operation": operation, "target_type": target_type, "collection_mode": collection_mode},
    )


def is_stable_operation(
    *,
    operation: str,
    target_type: str,
    collection_mode: str,
    entries: Iterable[OperationTaxonomyEntry | Mapping[str, Any]] = DEFAULT_OPERATION_TAXONOMY,
) -> bool:
    try:
        stable_operation_entry(
            operation=operation,
            target_type=target_type,
            collection_mode=collection_mode,
            entries=entries,
        )
    except OperationTaxonomyContractError:
        return False
    return True


def _normalize_entry(entry: OperationTaxonomyEntry | Mapping[str, Any]) -> OperationTaxonomyEntry | Mapping[str, Any]:
    if isinstance(entry, OperationTaxonomyEntry):
        return entry
    if not isinstance(entry, Mapping):
        return {"_type": type(entry).__name__}
    required = (
        "capability_family",
        "operation",
        "target_type",
        "execution_mode",
        "collection_mode",
        "lifecycle",
        "runtime_delivery",
        "contract_refs",
        "admission_evidence_refs",
    )
    if any(field not in entry for field in required):
        return entry
    return OperationTaxonomyEntry(
        capability_family=entry["capability_family"],
        operation=entry["operation"],
        target_type=entry["target_type"],
        execution_mode=entry["execution_mode"],
        collection_mode=entry["collection_mode"],
        lifecycle=entry["lifecycle"],
        runtime_delivery=entry["runtime_delivery"],
        contract_refs=tuple(entry["contract_refs"]),
        admission_evidence_refs=tuple(entry["admission_evidence_refs"]),
        notes=tuple(entry.get("notes", ())),
    )


def _validate_entry_surface(entry: OperationTaxonomyEntry | Mapping[str, Any]) -> Mapping[str, Any] | None:
    if not isinstance(entry, Mapping):
        return None
    forbidden = tuple(sorted(set(entry) & FORBIDDEN_TAXONOMY_FIELDS))
    if forbidden:
        return {"violated_rule": "taxonomy entry must not contain provider or application workflow fields", "fields": forbidden}
    return None


def _validate_entry_values(entry: OperationTaxonomyEntry) -> Mapping[str, Any] | None:
    required_strings = {
        "capability_family": entry.capability_family,
        "operation": entry.operation,
        "target_type": entry.target_type,
        "execution_mode": entry.execution_mode,
        "collection_mode": entry.collection_mode,
        "lifecycle": entry.lifecycle,
    }
    missing_or_invalid = tuple(name for name, value in required_strings.items() if not isinstance(value, str) or not value)
    if missing_or_invalid:
        return {"violated_rule": "required taxonomy strings must be non-empty", "fields": missing_or_invalid}
    if entry.lifecycle not in CAPABILITY_LIFECYCLES:
        return {
            "violated_rule": "capability lifecycle must be proposed, experimental, stable, or deprecated",
            "lifecycle": entry.lifecycle,
        }
    if not isinstance(entry.runtime_delivery, bool):
        return {"violated_rule": "runtime_delivery must be boolean", "runtime_delivery": entry.runtime_delivery}
    if not isinstance(entry.contract_refs, tuple) or any(not isinstance(ref, str) or not ref for ref in entry.contract_refs):
        return {"violated_rule": "contract_refs must be non-empty string tuple"}
    if not isinstance(entry.admission_evidence_refs, tuple) or any(
        not isinstance(ref, str) or not ref for ref in entry.admission_evidence_refs
    ):
        return {"violated_rule": "admission_evidence_refs must be string tuple"}
    if not entry.operation.startswith(entry.capability_family):
        return {
            "violated_rule": "public operation must project from capability family",
            "capability_family": entry.capability_family,
            "operation": entry.operation,
        }
    if entry.lifecycle == CAPABILITY_LIFECYCLE_STABLE:
        if entry.runtime_delivery is not True:
            return {"violated_rule": "stable taxonomy entries must be runtime-deliverable"}
        if not entry.contract_refs or not entry.admission_evidence_refs:
            return {"violated_rule": "stable taxonomy entries require contract refs and admission evidence refs"}
    if entry.lifecycle in {CAPABILITY_LIFECYCLE_PROPOSED, CAPABILITY_LIFECYCLE_EXPERIMENTAL} and entry.runtime_delivery:
        return {"violated_rule": "non-stable taxonomy entries must not be runtime-deliverable"}
    if entry.lifecycle == CAPABILITY_LIFECYCLE_DEPRECATED and entry.runtime_delivery:
        return {"violated_rule": "deprecated taxonomy entries must not be runtime-deliverable"}
    return None


def _duplicate_operation_reports(entries: tuple[OperationTaxonomyEntry, ...]) -> tuple[AdmissionReport, ...]:
    seen: dict[tuple[str, str, str], OperationTaxonomyEntry] = {}
    reports: list[AdmissionReport] = []
    for entry in entries:
        key = (entry.operation, entry.target_type, entry.collection_mode)
        if key in seen:
            reports.append(
                AdmissionReport(
                    status=ADMISSION_STATUS_INVALID_CONTRACT,
                    capability_family=entry.capability_family,
                    operation=entry.operation,
                    lifecycle=entry.lifecycle,
                    runtime_delivery=entry.runtime_delivery,
                    error_code=ADMISSION_ERROR_DUPLICATE_OPERATION,
                    message="operation taxonomy registry must not contain duplicate operation slices",
                    details={
                        "operation": entry.operation,
                        "target_type": entry.target_type,
                        "collection_mode": entry.collection_mode,
                    },
                )
            )
        else:
            seen[key] = entry
    return tuple(reports)


def _invalid_entry_report(
    capability_family: str | None,
    operation: str | None,
    lifecycle: str | None,
    runtime_delivery: bool | None,
    details: Mapping[str, Any],
) -> AdmissionReport:
    return AdmissionReport(
        status=ADMISSION_STATUS_INVALID_CONTRACT,
        capability_family=capability_family,
        operation=operation,
        lifecycle=lifecycle,
        runtime_delivery=runtime_delivery,
        error_code=ADMISSION_ERROR_INVALID_ENTRY,
        message="operation taxonomy entry violates the admission contract",
        details=dict(details),
    )
