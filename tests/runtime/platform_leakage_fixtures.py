from __future__ import annotations


def canonical_platform_leakage_evidence_refs() -> list[str]:
    return [
        "platform_leakage:scan:syvert/registry.py",
        "platform_leakage:scan:syvert/runtime.py",
        "platform_leakage:scan:syvert/version_gate.py",
    ]


def canonical_platform_leakage_payload(*, version: str = "v0.2.0") -> dict[str, object]:
    return {
        "version": version,
        "boundary_scope": [
            "core_runtime",
            "shared_input_model",
            "shared_error_model",
            "adapter_registry",
            "shared_result_contract",
            "version_gate_logic",
        ],
        "verdict": "pass",
        "summary": "platform leakage checks are clean",
        "findings": [],
        "evidence_refs": canonical_platform_leakage_evidence_refs(),
    }
