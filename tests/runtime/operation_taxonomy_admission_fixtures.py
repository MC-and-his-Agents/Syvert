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


def proposed_comment_collection_entry() -> dict[str, Any]:
    return {
        "capability_family": "comment_collection",
        "operation": "comment_collection",
        "target_type": "content",
        "execution_mode": "single",
        "collection_mode": "paginated",
        "lifecycle": "proposed",
        "runtime_delivery": False,
        "contract_refs": ("FR-0368",),
        "admission_evidence_refs": ("fr-0368:admission-evidence:comment-collection-proposed",),
        "notes": ("fake adapter expression only",),
    }


def fake_adapter_admission_manifest() -> dict[str, Any]:
    return {
        "adapter_key": "fake_taxonomy_reference",
        "declared_taxonomy_entries": [
            proposed_content_search_entry(),
            proposed_comment_collection_entry(),
        ],
        "execution_contract": {
            "runtime_delivery_allowed": False,
            "stable_lookup_allowed": False,
            "compatibility_match_allowed": False,
        },
    }


def copy_fake_adapter_admission_manifest(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    return deepcopy(manifest if manifest is not None else fake_adapter_admission_manifest())
