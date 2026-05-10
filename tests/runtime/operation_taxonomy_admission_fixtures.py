from __future__ import annotations

from copy import deepcopy
from typing import Any


def proposed_content_search_entry() -> dict[str, Any]:
    return {
        "capability_family": "content_search",
        "operation": "content_search",
        "target_type": "query",
        "execution_mode": "single",
        "collection_mode": "paginated",
        "lifecycle": "proposed",
        "runtime_delivery": False,
        "contract_refs": ("FR-0368",),
        "admission_evidence_refs": ("fr-0368:admission-evidence:content-search-proposed",),
        "notes": ("fake adapter expression only",),
    }


def stable_comment_collection_entry() -> dict[str, Any]:
    return {
        "capability_family": "comment_collection",
        "operation": "comment_collection",
        "target_type": "content",
        "execution_mode": "single",
        "collection_mode": "paginated",
        "lifecycle": "stable",
        "runtime_delivery": True,
        "contract_refs": ("FR-0404",),
        "admission_evidence_refs": ("tests.runtime.test_comment_collection",),
        "notes": ("v1.4.0 fake adapter runtime expression",),
    }


def fake_adapter_admission_manifest() -> dict[str, Any]:
    return {
        "adapter_key": "fake_taxonomy_reference",
        "declared_taxonomy_entries": [
            proposed_content_search_entry(),
            stable_comment_collection_entry(),
        ],
        "execution_contract": {
            "runtime_delivery_allowed": False,
            "comment_collection_runtime_delivery_allowed": True,
            "stable_lookup_allowed": False,
            "compatibility_match_allowed": True,
        },
    }


def copy_fake_adapter_admission_manifest(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return deepcopy(manifest if manifest is not None else fake_adapter_admission_manifest())
