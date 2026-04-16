from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from syvert.version_gate import validate_platform_leakage_source_report


DEFAULT_BOUNDARY_SCOPE = (
    "core_runtime",
    "shared_input_model",
    "shared_error_model",
    "adapter_registry",
    "shared_result_contract",
    "version_gate_logic",
)

_SCAN_TARGETS = (
    {
        "relative_path": Path("syvert/runtime.py"),
        "default_boundary": "core_runtime",
    },
    {
        "relative_path": Path("syvert/registry.py"),
        "default_boundary": "adapter_registry",
    },
    {
        "relative_path": Path("syvert/version_gate.py"),
        "default_boundary": "version_gate_logic",
    },
)

_RUNTIME_SYMBOL_BOUNDARIES = {
    "TaskInput": "shared_input_model",
    "InputTarget": "shared_input_model",
    "CollectionPolicy": "shared_input_model",
    "CoreTaskRequest": "shared_input_model",
    "TaskRequest": "shared_input_model",
    "AdapterTaskRequest": "shared_input_model",
    "PlatformAdapterError": "shared_error_model",
    "validate_success_payload": "shared_result_contract",
    "failure_envelope": "shared_error_model",
    "runtime_contract_error": "shared_error_model",
    "classify_adapter_error": "shared_error_model",
    "invalid_input_error": "shared_error_model",
    "unsupported_error": "shared_error_model",
}

_PLATFORM_TOKEN_RE = re.compile(r"\b(xhs|douyin)\b")
_PLATFORM_FIELD_RE = re.compile(r"\b(note_id|aweme_id|sign_base_url|sec_uid|xsec_token|web_rid)\b")
_BRANCH_KEYWORD_RE = re.compile(r"\b(if|elif|case|match)\b")
_SEMANTIC_CONTEXT_RE = re.compile(
    r"\b(default|semantic|operation|registry|runtime|contract|shared|surface|capability|target|collection_mode|mode)\b"
)


def build_platform_leakage_payload(
    *,
    version: str,
    repo_root: str | Path,
    boundary_scope: Sequence[str] | Iterable[str] | None = None,
) -> dict[str, Any]:
    findings, scan_refs = _scan_shared_boundaries(repo_root)
    evidence_refs = sorted({*scan_refs, *(finding["evidence_ref"] for finding in findings)})
    verdict = "fail" if findings else "pass"
    checked_boundary_scope = _coerce_boundary_scope_input(boundary_scope)
    return {
        "version": version,
        "boundary_scope": checked_boundary_scope,
        "verdict": verdict,
        "summary": (
            f"platform leakage checks failed for version `{version}`"
            if findings
            else f"platform leakage checks passed for version `{version}`"
        ),
        "findings": findings,
        "evidence_refs": evidence_refs,
    }


def run_platform_leakage_check(
    *,
    version: str,
    repo_root: str | Path,
    boundary_scope: Sequence[str] | Iterable[str] | None = None,
) -> dict[str, Any]:
    payload = build_platform_leakage_payload(
        version=version,
        repo_root=repo_root,
        boundary_scope=boundary_scope,
    )
    return validate_platform_leakage_source_report(payload, version=version)


def _scan_shared_boundaries(repo_root: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    repo_path = _coerce_repo_root(repo_root)
    findings: list[dict[str, str]] = []
    evidence_refs: list[str] = []

    for target in _SCAN_TARGETS:
        relative_path = target["relative_path"]
        relative_name = relative_path.as_posix()
        default_boundary = target["default_boundary"]
        evidence_refs.append(f"platform_leakage:scan:{relative_name}")

        if repo_path is None:
            findings.append(
                _finding(
                    code="scan_target_missing",
                    message="platform leakage scan root is unavailable",
                    boundary=default_boundary,
                    evidence_ref=f"platform_leakage:{default_boundary}:{relative_name}:missing-root",
                )
            )
            continue

        file_path = repo_path / relative_path
        try:
            source_text = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            findings.append(
                _finding(
                    code="scan_target_missing",
                    message=f"platform leakage scan target `{relative_name}` is missing",
                    boundary=default_boundary,
                    evidence_ref=f"platform_leakage:{default_boundary}:{relative_name}:missing",
                )
            )
            continue
        except OSError:
            findings.append(
                _finding(
                    code="scan_target_unreadable",
                    message=f"platform leakage scan target `{relative_name}` cannot be read",
                    boundary=default_boundary,
                    evidence_ref=f"platform_leakage:{default_boundary}:{relative_name}:unreadable",
                )
            )
            continue

        boundary_resolver = _build_boundary_resolver(relative_name, source_text)
        findings.extend(_scan_file(relative_name, source_text, boundary_resolver))

    return findings, evidence_refs


def _coerce_repo_root(repo_root: str | Path) -> Path | None:
    try:
        return Path(repo_root)
    except TypeError:
        return None


def _coerce_boundary_scope_input(
    boundary_scope: Sequence[str] | Iterable[str] | None,
) -> Sequence[str] | Iterable[str]:
    if boundary_scope is None:
        return list(DEFAULT_BOUNDARY_SCOPE)
    if isinstance(boundary_scope, (str, bytes, Mapping)):
        return boundary_scope
    try:
        return list(boundary_scope)
    except TypeError:
        return boundary_scope


def _build_boundary_resolver(relative_name: str, source_text: str) -> Any:
    if relative_name == "syvert/registry.py":
        return lambda _line_number: "adapter_registry"
    if relative_name == "syvert/version_gate.py":
        return lambda _line_number: "version_gate_logic"
    if relative_name != "syvert/runtime.py":
        return lambda _line_number: "core_runtime"

    try:
        module = ast.parse(source_text)
    except SyntaxError:
        return lambda _line_number: "core_runtime"

    ranges: list[tuple[int, int, str]] = []
    for node in module.body:
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        boundary = _RUNTIME_SYMBOL_BOUNDARIES.get(node.name)
        if boundary is None:
            continue
        ranges.append((node.lineno, getattr(node, "end_lineno", node.lineno), boundary))

    def resolve(line_number: int) -> str:
        for start, end, boundary in ranges:
            if start <= line_number <= end:
                return boundary
        return "core_runtime"

    return resolve


def _scan_file(relative_name: str, source_text: str, boundary_resolver: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for line_number, line in enumerate(source_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _is_allowed_exception(relative_name, stripped):
            continue

        boundary = boundary_resolver(line_number)
        evidence_ref = f"platform_leakage:{boundary}:{relative_name}:{line_number}"
        if _PLATFORM_FIELD_RE.search(stripped):
            findings.append(
                _finding(
                    code="platform_specific_field_leak",
                    message=f"platform-specific field leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )
            continue

        platform_match = _PLATFORM_TOKEN_RE.search(stripped)
        if platform_match is None:
            continue

        if _BRANCH_KEYWORD_RE.search(stripped):
            findings.append(
                _finding(
                    code="hardcoded_platform_branch",
                    message=f"hardcoded platform branch leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )
            continue

        if "=" in stripped or _SEMANTIC_CONTEXT_RE.search(stripped):
            findings.append(
                _finding(
                    code="single_platform_shared_semantic",
                    message=f"single-platform shared semantic leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )

    return findings


def _is_allowed_exception(relative_name: str, stripped_line: str) -> bool:
    if "normalized.platform" in stripped_line:
        return True
    if "error.details" in stripped_line:
        return True
    return (
        relative_name == "syvert/version_gate.py"
        and "_FROZEN_REFERENCE_PAIR_BY_VERSION" in stripped_line
        or relative_name == "syvert/version_gate.py"
        and '"xhs"' in stripped_line
        and '"douyin"' in stripped_line
    )


def _finding(*, code: str, message: str, boundary: str, evidence_ref: str) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
        "boundary": boundary,
        "evidence_ref": evidence_ref,
    }


__all__ = [
    "DEFAULT_BOUNDARY_SCOPE",
    "build_platform_leakage_payload",
    "run_platform_leakage_check",
]
