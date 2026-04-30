from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
import tempfile
from typing import Any, Literal

from syvert.registry import AdapterRegistry, RegistryError
from syvert.resource_lifecycle import ResourceRecord
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore
from tests.runtime.contract_harness.host import HarnessExecutionInput, execute_harness_sample
from tests.runtime.contract_harness.validation_tool import (
    ContractSampleDefinition,
    HarnessExecutionResult,
    validate_contract_sample,
)
from tests.runtime.resource_fixtures import generic_account_material, managed_account_material, proxy_material

ADAPTER_ONLY_CONTENT_DETAIL_PROFILE = "adapter_only_content_detail_v0_8"

_REQUIRED_MANIFEST_FIELDS = frozenset(
    {
        "adapter_key",
        "sdk_contract_id",
        "supported_capabilities",
        "supported_targets",
        "supported_collection_modes",
        "resource_requirement_declarations",
        "result_contract",
        "error_mapping",
        "fixture_refs",
        "contract_test_profile",
    }
)
_FORBIDDEN_MANIFEST_FIELDS = frozenset(
    {
        "compatibility_decision",
        "fallback",
        "marketplace",
        "priority",
        "provider_fallback",
        "provider_key",
        "provider_marketplace",
        "provider_offer",
        "provider_priority",
        "provider_product_allowlist",
        "provider_registry",
        "provider_score",
        "provider_selector",
        "score",
        "selector",
    }
)
_ALLOWED_ERROR_MAPPING_CATEGORIES = frozenset(
    {"invalid_input", "unsupported", "platform"}
)
_FORBIDDEN_ADAPTER_KEY_FRAGMENTS = frozenset(
    {
        "account",
        "acct",
        "dev",
        "env",
        "fallback",
        "marketplace",
        "priority",
        "prod",
        "provider",
        "route",
        "routing",
        "score",
        "selector",
        "staging",
    }
)
_MISSING = object()


class ThirdPartyContractEntryError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


@dataclass(frozen=True)
class ThirdPartyAdapterManifest:
    adapter_key: str
    sdk_contract_id: str
    supported_capabilities: tuple[str, ...]
    supported_targets: tuple[str, ...]
    supported_collection_modes: tuple[str, ...]
    resource_requirement_declarations: tuple[Any, ...]
    result_contract: Mapping[str, Any]
    error_mapping: Mapping[str, Any]
    fixture_refs: tuple[str, ...]
    contract_test_profile: str


@dataclass(frozen=True)
class AdapterContractFixture:
    fixture_id: str
    manifest_ref: str
    case_type: Literal["success", "error_mapping"]
    input: Mapping[str, Any]
    expected: Mapping[str, Any]


@dataclass
class _ManifestDeclaredAdapter:
    manifest: ThirdPartyAdapterManifest

    @property
    def supported_capabilities(self) -> frozenset[str]:
        return frozenset(self.manifest.supported_capabilities)

    @property
    def supported_targets(self) -> frozenset[str]:
        return frozenset(self.manifest.supported_targets)

    @property
    def supported_collection_modes(self) -> frozenset[str]:
        return frozenset(self.manifest.supported_collection_modes)

    @property
    def resource_requirement_declarations(self) -> tuple[Any, ...]:
        return self.manifest.resource_requirement_declarations

    def execute(self, _request: Any) -> dict[str, Any]:
        raise AssertionError("manifest declaration validation must not execute adapters")


def run_third_party_adapter_contract_test(
    *,
    manifest: Mapping[str, Any],
    fixtures: Sequence[Mapping[str, Any]],
    adapter: Any,
) -> list[dict[str, Any]]:
    normalized_manifest = validate_third_party_adapter_manifest(manifest)
    normalized_fixtures = validate_third_party_adapter_fixtures(
        normalized_manifest,
        fixtures,
    )
    _validate_adapter_public_metadata(normalized_manifest, adapter)

    results: list[dict[str, Any]] = []
    for fixture in normalized_fixtures:
        result = _execute_and_validate_fixture(normalized_manifest, fixture, adapter)
        results.append(result)
    return results


def validate_third_party_adapter_manifest(manifest: Mapping[str, Any]) -> ThirdPartyAdapterManifest:
    if not isinstance(manifest, Mapping):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_shape",
            "third-party adapter manifest must be a mapping",
            details={"actual_type": type(manifest).__name__},
        )
    raw_keys = {key for key in manifest}
    if any(not isinstance(key, str) for key in raw_keys):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_shape",
            "third-party adapter manifest field names must be strings",
            details={"actual_keys": tuple(sorted(str(key) for key in raw_keys))},
        )

    forbidden_fields = tuple(sorted(raw_keys & _FORBIDDEN_MANIFEST_FIELDS))
    if forbidden_fields:
        raise ThirdPartyContractEntryError(
            "forbidden_adapter_manifest_fields",
            "third-party adapter manifest must not carry provider or compatibility fields",
            details={"forbidden_fields": forbidden_fields},
        )
    missing_fields = tuple(sorted(_REQUIRED_MANIFEST_FIELDS - raw_keys))
    extra_fields = tuple(sorted(raw_keys - _REQUIRED_MANIFEST_FIELDS))
    if missing_fields or extra_fields:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_shape",
            "third-party adapter manifest must keep the FR-0023 fixed field set",
            details={"missing_fields": missing_fields, "extra_fields": extra_fields},
        )

    adapter_key = _require_non_empty_string(
        manifest["adapter_key"],
        code="invalid_manifest_public_metadata",
        field="adapter_key",
    )
    _validate_adapter_key_boundary(adapter_key)
    sdk_contract_id = _require_non_empty_string(
        manifest["sdk_contract_id"],
        code="invalid_manifest_public_metadata",
        field="sdk_contract_id",
    )
    if "provider" in sdk_contract_id or "compatibility" in sdk_contract_id:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            "sdk_contract_id must describe the Adapter SDK/runtime contract only",
            details={"field": "sdk_contract_id", "value": sdk_contract_id},
        )

    normalized_manifest = ThirdPartyAdapterManifest(
        adapter_key=adapter_key,
        sdk_contract_id=sdk_contract_id,
        supported_capabilities=_require_non_empty_string_tuple(
            manifest["supported_capabilities"],
            field="supported_capabilities",
        ),
        supported_targets=_require_non_empty_string_tuple(
            manifest["supported_targets"],
            field="supported_targets",
        ),
        supported_collection_modes=_require_non_empty_string_tuple(
            manifest["supported_collection_modes"],
            field="supported_collection_modes",
        ),
        resource_requirement_declarations=_require_non_string_sequence(
            manifest["resource_requirement_declarations"],
            field="resource_requirement_declarations",
        ),
        result_contract=_require_mapping(manifest["result_contract"], field="result_contract"),
        error_mapping=_require_mapping(manifest["error_mapping"], field="error_mapping"),
        fixture_refs=_require_non_empty_string_tuple(
            manifest["fixture_refs"],
            field="fixture_refs",
        ),
        contract_test_profile=_require_non_empty_string(
            manifest["contract_test_profile"],
            code="invalid_manifest_public_metadata",
            field="contract_test_profile",
        ),
    )
    _validate_contract_test_profile(normalized_manifest.contract_test_profile)
    _validate_result_contract(normalized_manifest.result_contract)
    _validate_error_mapping(normalized_manifest.error_mapping)
    resource_declarations = _normalize_manifest_resource_declarations(normalized_manifest)
    return replace(
        normalized_manifest,
        resource_requirement_declarations=resource_declarations,
    )


def validate_third_party_adapter_fixtures(
    manifest: ThirdPartyAdapterManifest,
    fixtures: Sequence[Mapping[str, Any]],
) -> tuple[AdapterContractFixture, ...]:
    if isinstance(fixtures, (str, bytes)) or not isinstance(fixtures, Sequence):
        raise ThirdPartyContractEntryError(
            "invalid_fixture_collection",
            "third-party adapter contract fixtures must be a sequence",
            details={"actual_type": type(fixtures).__name__},
        )
    normalized = tuple(_normalize_fixture(manifest, fixture) for fixture in fixtures)
    fixture_index: dict[str, AdapterContractFixture] = {}
    for fixture in normalized:
        if fixture.fixture_id in fixture_index:
            raise ThirdPartyContractEntryError(
                "duplicate_fixture_id",
                "third-party adapter fixtures must not repeat fixture_id",
                details={"fixture_id": fixture.fixture_id},
            )
        fixture_index[fixture.fixture_id] = fixture

    missing_refs = tuple(ref for ref in manifest.fixture_refs if ref not in fixture_index)
    if missing_refs:
        raise ThirdPartyContractEntryError(
            "unresolvable_fixture_refs",
            "manifest fixture_refs must resolve to provided fixtures",
            details={"missing_refs": missing_refs},
        )
    unreferenced_fixtures = tuple(
        fixture.fixture_id for fixture in normalized if fixture.fixture_id not in manifest.fixture_refs
    )
    if unreferenced_fixtures:
        raise ThirdPartyContractEntryError(
            "unreferenced_fixtures",
            "provided fixtures must be explicitly listed in manifest fixture_refs",
            details={"unreferenced_fixtures": unreferenced_fixtures},
        )

    covered_case_types = frozenset(fixture.case_type for fixture in normalized)
    missing_case_types = tuple(sorted({"success", "error_mapping"} - covered_case_types))
    if missing_case_types:
        raise ThirdPartyContractEntryError(
            "missing_fixture_case_coverage",
            "third-party adapter fixtures must cover success and error_mapping cases",
            details={"missing_case_types": missing_case_types},
        )
    return normalized


def _normalize_manifest_resource_declarations(manifest: ThirdPartyAdapterManifest) -> tuple[Any, ...]:
    try:
        registry = AdapterRegistry.from_mapping({manifest.adapter_key: _ManifestDeclaredAdapter(manifest)})
    except RegistryError as error:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "manifest resource_requirement_declarations must pass the FR-0027 registry validator",
            details={"registry_code": error.code, **error.details},
        ) from error
    requirements = registry.discover_resource_requirements(manifest.adapter_key)
    if requirements is None:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_resource_requirement_declarations",
            "manifest resource_requirement_declarations could not be discovered after validation",
            details={"adapter_key": manifest.adapter_key},
        )
    return requirements


def _validate_adapter_public_metadata(manifest: ThirdPartyAdapterManifest, adapter: Any) -> None:
    _reject_forbidden_adapter_public_metadata(adapter, manifest.adapter_key)
    try:
        registry = AdapterRegistry.from_mapping({manifest.adapter_key: adapter})
    except RegistryError as error:
        raise ThirdPartyContractEntryError(
            "invalid_adapter_public_metadata",
            "adapter public metadata must pass the registry validator",
            details={"registry_code": error.code, **error.details},
        ) from error
    declaration = registry.lookup(manifest.adapter_key)
    if declaration is None:
        raise ThirdPartyContractEntryError(
            "invalid_adapter_public_metadata",
            "adapter registry lookup failed after successful materialization",
            details={"adapter_key": manifest.adapter_key},
        )
    mismatches: dict[str, Any] = {}
    if tuple(sorted(declaration.supported_capabilities)) != tuple(sorted(manifest.supported_capabilities)):
        mismatches["supported_capabilities"] = tuple(sorted(declaration.supported_capabilities))
    if tuple(sorted(declaration.supported_targets)) != tuple(sorted(manifest.supported_targets)):
        mismatches["supported_targets"] = tuple(sorted(declaration.supported_targets))
    if tuple(sorted(declaration.supported_collection_modes)) != tuple(sorted(manifest.supported_collection_modes)):
        mismatches["supported_collection_modes"] = tuple(sorted(declaration.supported_collection_modes))
    if declaration.resource_requirement_declarations != manifest.resource_requirement_declarations:
        mismatches["resource_requirement_declarations"] = declaration.resource_requirement_declarations
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="adapter_key",
        expected=manifest.adapter_key,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="sdk_contract_id",
        expected=manifest.sdk_contract_id,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="result_contract",
        expected=manifest.result_contract,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="error_mapping",
        expected=manifest.error_mapping,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="fixture_refs",
        expected=manifest.fixture_refs,
        mismatches=mismatches,
    )
    _compare_adapter_public_metadata_attr(
        adapter,
        manifest,
        attr_name="contract_test_profile",
        expected=manifest.contract_test_profile,
        mismatches=mismatches,
    )
    if mismatches:
        raise ThirdPartyContractEntryError(
            "adapter_manifest_metadata_mismatch",
            "adapter public metadata must match the manifest before execution",
            details={"adapter_key": manifest.adapter_key, "mismatches": mismatches},
        )


def _validate_adapter_key_boundary(adapter_key: str) -> None:
    normalized = adapter_key.lower()
    forbidden_fragments = tuple(
        sorted(fragment for fragment in _FORBIDDEN_ADAPTER_KEY_FRAGMENTS if fragment in normalized)
    )
    if forbidden_fragments:
        raise ThirdPartyContractEntryError(
            "invalid_adapter_key_boundary",
            "adapter_key must not carry provider, account, environment, or routing strategy semantics",
            details={"adapter_key": adapter_key, "forbidden_fragments": forbidden_fragments},
        )


def _reject_forbidden_adapter_public_metadata(adapter: Any, adapter_key: str) -> None:
    exposed_fields: list[str] = []
    for field in sorted(_FORBIDDEN_MANIFEST_FIELDS):
        try:
            getattr(adapter, field)
        except AttributeError:
            continue
        except Exception:
            exposed_fields.append(field)
            continue
        exposed_fields.append(field)
    if exposed_fields:
        raise ThirdPartyContractEntryError(
            "forbidden_adapter_public_metadata_fields",
            "adapter public metadata must not expose provider or compatibility fields",
            details={"adapter_key": adapter_key, "forbidden_fields": tuple(exposed_fields)},
        )


def _compare_adapter_public_metadata_attr(
    adapter: Any,
    manifest: ThirdPartyAdapterManifest,
    *,
    attr_name: str,
    expected: Any,
    mismatches: dict[str, Any],
) -> None:
    try:
        actual = getattr(adapter, attr_name)
    except Exception:
        actual = _MISSING
    if attr_name == "fixture_refs" and actual is not _MISSING:
        try:
            actual = tuple(actual)
        except TypeError:
            pass
    if actual != expected:
        mismatches[attr_name] = {
            "expected": expected,
            "actual": "missing" if actual is _MISSING else actual,
            "adapter_key": manifest.adapter_key,
        }


def _execute_and_validate_fixture(
    manifest: ThirdPartyAdapterManifest,
    fixture: AdapterContractFixture,
    adapter: Any,
) -> dict[str, Any]:
    expected_outcome = "success" if fixture.case_type == "success" else "legal_failure"
    sample = ContractSampleDefinition(sample_id=fixture.fixture_id, expected_outcome=expected_outcome)
    with tempfile.TemporaryDirectory(prefix=f"syvert-third-party-contract-{fixture.fixture_id}-") as temp_dir:
        resource_store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
        resource_store.seed_resources(
            [
                ResourceRecord(
                    resource_id="third-party-account-001",
                    resource_type="account",
                    status="AVAILABLE",
                    material=managed_account_material(generic_account_material(), adapter_key=manifest.adapter_key),
                ),
                ResourceRecord(
                    resource_id="third-party-proxy-001",
                    resource_type="proxy",
                    status="AVAILABLE",
                    material=proxy_material(),
                ),
            ]
        )
        runtime_envelope = execute_harness_sample(
            HarnessExecutionInput(
                sample_id=fixture.fixture_id,
                url=_fixture_url(fixture),
                adapter_key=manifest.adapter_key,
            ),
            adapters={manifest.adapter_key: adapter},
            task_id=f"task-{fixture.fixture_id}",
            resource_lifecycle_store=resource_store,
        )
    result = validate_contract_sample(sample, HarnessExecutionResult(runtime_envelope=runtime_envelope))
    if result["verdict"] == "legal_failure":
        return _validate_error_mapping_observation(fixture, result)
    return result


def _normalize_fixture(
    manifest: ThirdPartyAdapterManifest,
    fixture: Mapping[str, Any],
) -> AdapterContractFixture:
    if not isinstance(fixture, Mapping):
        raise ThirdPartyContractEntryError(
            "invalid_fixture_shape",
            "third-party adapter fixture must be a mapping",
            details={"actual_type": type(fixture).__name__},
        )
    raw_keys = {key for key in fixture}
    required_fields = frozenset({"fixture_id", "manifest_ref", "case_type", "input", "expected"})
    missing_fields = tuple(sorted(required_fields - raw_keys))
    extra_fields = tuple(sorted(raw_keys - required_fields))
    if missing_fields or extra_fields:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_shape",
            "third-party adapter fixture must keep the fixed field set",
            details={"missing_fields": missing_fields, "extra_fields": extra_fields},
        )
    fixture_id = _require_non_empty_string(
        fixture["fixture_id"],
        code="invalid_fixture_shape",
        field="fixture_id",
    )
    manifest_ref = _require_non_empty_string(
        fixture["manifest_ref"],
        code="invalid_fixture_shape",
        field="manifest_ref",
    )
    if manifest_ref != manifest.adapter_key:
        raise ThirdPartyContractEntryError(
            "fixture_manifest_ref_mismatch",
            "fixture manifest_ref must match manifest adapter_key",
            details={"fixture_id": fixture_id, "manifest_ref": manifest_ref, "adapter_key": manifest.adapter_key},
        )
    case_type = _require_non_empty_string(
        fixture["case_type"],
        code="invalid_fixture_shape",
        field="case_type",
    )
    if case_type not in {"success", "error_mapping"}:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_case_type",
            "fixture case_type must be success or error_mapping",
            details={"fixture_id": fixture_id, "case_type": case_type},
        )
    normalized = AdapterContractFixture(
        fixture_id=fixture_id,
        manifest_ref=manifest_ref,
        case_type=case_type,  # type: ignore[arg-type]
        input=_require_mapping(fixture["input"], field="input"),
        expected=_require_mapping(fixture["expected"], field="expected"),
    )
    _validate_fixture_expected_contract(normalized)
    return normalized


def _validate_contract_test_profile(profile: str) -> None:
    if profile != ADAPTER_ONLY_CONTENT_DETAIL_PROFILE:
        raise ThirdPartyContractEntryError(
            "unsupported_contract_test_profile",
            "contract_test_profile must be adapter_only_content_detail_v0_8",
            details={"contract_test_profile": profile},
        )


def _validate_result_contract(result_contract: Mapping[str, Any]) -> None:
    required_payload_fields = _require_non_empty_string_tuple(
        result_contract.get("success_payload_fields"),
        field="result_contract.success_payload_fields",
    )
    if required_payload_fields != ("raw", "normalized"):
        raise ThirdPartyContractEntryError(
            "invalid_result_contract",
            "result_contract must require raw and normalized success payload fields",
            details={"success_payload_fields": required_payload_fields},
        )
    normalized_owner = _require_non_empty_string(
        result_contract.get("normalized_owner"),
        code="invalid_result_contract",
        field="result_contract.normalized_owner",
    )
    if normalized_owner != "adapter":
        raise ThirdPartyContractEntryError(
            "invalid_result_contract",
            "normalized result must be adapter-owned",
            details={"normalized_owner": normalized_owner},
        )


def _validate_error_mapping(error_mapping: Mapping[str, Any]) -> None:
    if not error_mapping:
        raise ThirdPartyContractEntryError(
            "invalid_error_mapping",
            "error_mapping must not be empty",
        )
    for source_error, mapping in error_mapping.items():
        if not isinstance(source_error, str) or not source_error:
            raise ThirdPartyContractEntryError(
                "invalid_error_mapping",
                "error_mapping source keys must be non-empty strings",
                details={"source_error": source_error},
            )
        normalized_mapping = _require_mapping(mapping, field=f"error_mapping.{source_error}")
        category = _require_non_empty_string(
            normalized_mapping.get("category"),
            code="invalid_error_mapping",
            field=f"error_mapping.{source_error}.category",
        )
        if category not in _ALLOWED_ERROR_MAPPING_CATEGORIES:
            raise ThirdPartyContractEntryError(
                "invalid_error_mapping",
                "error_mapping category must reuse Syvert failed envelope categories",
                details={"source_error": source_error, "category": category},
            )
        _require_non_empty_string(
            normalized_mapping.get("code"),
            code="invalid_error_mapping",
            field=f"error_mapping.{source_error}.code",
        )
        _require_non_empty_string(
            normalized_mapping.get("message"),
            code="invalid_error_mapping",
            field=f"error_mapping.{source_error}.message",
        )


def _validate_fixture_expected_contract(fixture: AdapterContractFixture) -> None:
    expected_status = _require_non_empty_string(
        fixture.expected.get("status"),
        code="invalid_fixture_expected_contract",
        field="expected.status",
    )
    if fixture.case_type == "success":
        if expected_status != "success":
            raise ThirdPartyContractEntryError(
                "invalid_fixture_expected_contract",
                "success fixture expected.status must be success",
                details={"fixture_id": fixture.fixture_id, "status": expected_status},
            )
        required_payload_fields = _require_non_empty_string_tuple(
            fixture.expected.get("required_payload_fields"),
            field="expected.required_payload_fields",
        )
        if required_payload_fields != ("raw", "normalized"):
            raise ThirdPartyContractEntryError(
                "invalid_fixture_expected_contract",
                "success fixture must require raw and normalized payload fields",
                details={"fixture_id": fixture.fixture_id, "required_payload_fields": required_payload_fields},
            )
        return

    if expected_status != "failed":
        raise ThirdPartyContractEntryError(
            "invalid_fixture_expected_contract",
            "error_mapping fixture expected.status must be failed",
            details={"fixture_id": fixture.fixture_id, "status": expected_status},
        )
    expected_error = _require_mapping(fixture.expected.get("error"), field="expected.error")
    category = _require_non_empty_string(
        expected_error.get("category"),
        code="invalid_fixture_expected_contract",
        field="expected.error.category",
    )
    code = _require_non_empty_string(
        expected_error.get("code"),
        code="invalid_fixture_expected_contract",
        field="expected.error.code",
    )
    if category not in _ALLOWED_ERROR_MAPPING_CATEGORIES:
        raise ThirdPartyContractEntryError(
            "invalid_fixture_expected_contract",
            "error_mapping fixture must expect an existing Syvert failed envelope category",
            details={"fixture_id": fixture.fixture_id, "category": category, "code": code},
        )


def _validate_error_mapping_observation(
    fixture: AdapterContractFixture,
    result: dict[str, Any],
) -> dict[str, Any]:
    expected_error = _require_mapping(fixture.expected.get("error"), field="expected.error")
    observed_error = result.get("observed_error")
    if not isinstance(observed_error, Mapping):
        return {
            **result,
            "verdict": "contract_violation",
            "reason": {
                "code": "missing_observed_error_mapping",
                "message": "error_mapping fixture did not observe a failed envelope error object",
            },
        }
    expected_category = expected_error["category"]
    expected_code = expected_error["code"]
    if observed_error.get("category") != expected_category or observed_error.get("code") != expected_code:
        return {
            **result,
            "verdict": "contract_violation",
            "reason": {
                "code": "error_mapping_mismatch",
                "message": "observed failed envelope does not match fixture error_mapping expectation",
            },
        }
    return result


def _fixture_url(fixture: AdapterContractFixture) -> str:
    input_mapping = fixture.input
    url = _require_non_empty_string(
        input_mapping.get("url"),
        code="invalid_fixture_input",
        field="input.url",
    )
    return url


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must be a mapping",
            details={"field": field, "actual_type": type(value).__name__},
        )
    return value


def _require_non_empty_string(value: Any, *, code: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ThirdPartyContractEntryError(
            code,
            f"{field} must be a non-empty string",
            details={"field": field, "actual_type": type(value).__name__},
        )
    return value


def _require_non_string_sequence(value: Any, *, field: str) -> tuple[Any, ...]:
    if value is None or isinstance(value, (str, bytes)):
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must be a non-string sequence",
            details={"field": field, "actual_type": type(value).__name__},
        )
    try:
        return tuple(value)
    except TypeError as error:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must be a non-string sequence",
            details={"field": field, "actual_type": type(value).__name__},
        ) from error


def _require_non_empty_string_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    values = _require_non_string_sequence(value, field=field)
    if not values:
        raise ThirdPartyContractEntryError(
            "invalid_manifest_public_metadata",
            f"{field} must not be empty",
            details={"field": field},
        )
    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, str) or not item:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_public_metadata",
                f"{field} must contain only non-empty strings",
                details={"field": field, "actual_type": type(item).__name__},
            )
        if item in seen:
            raise ThirdPartyContractEntryError(
                "invalid_manifest_public_metadata",
                f"{field} must not contain duplicate strings",
                details={"field": field, "duplicate_value": item},
            )
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)
