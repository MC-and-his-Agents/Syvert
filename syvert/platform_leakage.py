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

_PLATFORM_FIELD_RE = re.compile(r"\b(note_id|aweme_id|sign_base_url|sec_uid|xsec_token|web_rid)\b")
_PLATFORM_STRING_FRAGMENT_RE = re.compile(
    r"(?:"
    r"xiaohongshu\.com|xhslink\.com|douyin\.com|iesdouyin\.com|v\.douyin\.com|"
    r"x-bogus|a_bogus|_signature|x-signature|mstoken|"
    r"data-xhs-|note-item|aweme-detail|aweme-|douyin-"
    r")"
)
_SEMANTIC_CONTEXT_RE = re.compile(
    r"\b(default|semantic|operation|registry|runtime|contract|shared|surface|capability|target|collection_mode|mode)\b"
)
_COMMON_PLATFORM_LITERALS = frozenset(
    {
        "bilibili",
        "douyin",
        "facebook",
        "instagram",
        "kuaishou",
        "reddit",
        "threads",
        "tiktok",
        "twitter",
        "weibo",
        "x",
        "xhs",
        "xiaohongshu",
        "youtube",
        "zhihu",
    }
)
_COMMON_PLATFORM_NAME_RE = re.compile(
    r"\b(?:bilibili|douyin|facebook|instagram|kuaishou|reddit|threads|tiktok|twitter|weibo|xhs|xiaohongshu|youtube|zhihu)\b"
)
_PLATFORM_BRANCH_VARIANT_RE = re.compile(
    r"^(?:bilibili|douyin|facebook|instagram|kuaishou|reddit|threads|tiktok|twitter|weibo|xhs|xiaohongshu|youtube|zhihu)"
    r"(?:[-_](?:main|prod|production|stage|staging|dev|test))?$"
)
_PLATFORM_IDENTIFIER_RE = re.compile(r"(?:^|_)(adapter|adapter_key|platform|platforms|platform_key|reference_pair)(?:_|$)")
_ERROR_CONTAINER_RE = re.compile(r"(?:^|_)(?:error|adapter_error|runtime_error|contract_error)(?:_|$)")
_SHARED_RESULT_CONTAINER_RE = re.compile(r"(?:^|_)(normalized|raw)(?:_|$)")
_AST_MATCH = getattr(ast, "Match", None)
_AST_MATCH_VALUE = getattr(ast, "MatchValue", None)
_AST_MATCH_SINGLETON = getattr(ast, "MatchSingleton", None)
_AST_MATCH_SEQUENCE = getattr(ast, "MatchSequence", None)
_AST_MATCH_OR = getattr(ast, "MatchOr", None)
_AST_MATCH_AS = getattr(ast, "MatchAs", None)
_AST_MATCH_MAPPING = getattr(ast, "MatchMapping", None)
_AST_MATCH_STAR = getattr(ast, "MatchStar", None)
_EMPTY_KEY_SIGNAL: tuple[frozenset[str], bool] = (frozenset(), False)


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
        except (OSError, ValueError):
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
        allowed_exception_lines = _build_allowed_exception_lines(relative_name, source_text)
        findings.extend(
            _scan_file(
                relative_name,
                source_text,
                boundary_resolver,
                default_boundary=default_boundary,
                allowed_exception_lines=allowed_exception_lines,
            )
        )

    return findings, evidence_refs


def _coerce_repo_root(repo_root: str | Path) -> Path | None:
    try:
        return Path(repo_root)
    except (TypeError, ValueError, OSError):
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


def _build_allowed_exception_lines(relative_name: str, source_text: str) -> frozenset[int]:
    if relative_name != "syvert/version_gate.py":
        return frozenset()

    try:
        module = ast.parse(source_text)
    except SyntaxError:
        return frozenset()

    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "_FROZEN_REFERENCE_PAIR_BY_VERSION":
                return frozenset(range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1))

    return frozenset()


def _scan_file(
    relative_name: str,
    source_text: str,
    boundary_resolver: Any,
    *,
    default_boundary: str,
    allowed_exception_lines: frozenset[int],
) -> list[dict[str, str]]:
    try:
        module = ast.parse(source_text)
    except SyntaxError as exc:
        line_number = exc.lineno or 1
        boundary = boundary_resolver(line_number) if callable(boundary_resolver) else default_boundary
        return [
            _finding(
                code="scan_parse_failure",
                message=(
                    f"platform leakage scan target `{relative_name}` cannot be parsed "
                    f"at line {line_number} and must fail closed"
                ),
                boundary=boundary or default_boundary,
                evidence_ref=f"platform_leakage:{boundary or default_boundary}:{relative_name}:{line_number}:parse-failure",
            )
        ]

    findings: list[dict[str, str]] = []
    parent_index = _build_parent_index(module)
    platform_alias_histories = _build_platform_alias_histories(module, parent_index)
    key_signal_histories = _build_key_signal_histories(module, parent_index, platform_alias_histories)
    shared_result_container_histories = _build_shared_result_container_histories(module, parent_index)
    error_details_histories = _build_error_details_histories(module, parent_index)
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line_number = getattr(node, "lineno", None)
            if line_number is None:
                continue
            current_scope = _enclosing_scope(node, parent_index)
            platform_aliases = _materialize_platform_aliases(
                platform_alias_histories,
                scope=current_scope,
                position=(line_number, getattr(node, "col_offset", 0)),
            )
            key_signals = _materialize_key_signals(
                key_signal_histories,
                scope=current_scope,
                position=(line_number, getattr(node, "col_offset", 0)),
            )
            shared_result_container_aliases = _materialize_shared_result_container_aliases(
                shared_result_container_histories,
                scope=current_scope,
                position=(line_number, getattr(node, "col_offset", 0)),
            )
            error_details_aliases = _materialize_error_details_aliases(
                error_details_histories,
                scope=current_scope,
                position=(line_number, getattr(node, "col_offset", 0)),
            )
            statement_lines = _statement_line_numbers(node)
            if statement_lines and all(line in allowed_exception_lines for line in statement_lines):
                continue
            boundary = boundary_resolver(line_number)
            evidence_ref = f"platform_leakage:{boundary}:{relative_name}:{line_number}"
            function_source = _statement_source_segment(source_text, node)
            if _function_has_single_platform_semantic(
                node,
                function_source,
                platform_aliases=platform_aliases,
            ):
                findings.append(
                    _finding(
                        code="single_platform_shared_semantic",
                        message=f"single-platform shared semantic leaked into shared layer at `{relative_name}:{line_number}`",
                        boundary=boundary,
                        evidence_ref=evidence_ref,
                    )
                )
            elif _definition_has_platform_metadata(
                node,
                platform_aliases=platform_aliases,
                shared_result_container_aliases=shared_result_container_aliases,
                error_details_aliases=error_details_aliases,
            ):
                findings.append(
                    _finding(
                        code="single_platform_shared_semantic",
                        message=f"single-platform shared semantic leaked into shared layer at `{relative_name}:{line_number}`",
                        boundary=boundary,
                        evidence_ref=evidence_ref,
                    )
                )
            continue

        if not isinstance(node, ast.stmt) or isinstance(node, ast.Module):
            continue
        line_number = getattr(node, "lineno", None)
        if line_number is None:
            continue
        current_scope = _enclosing_scope(node, parent_index)
        platform_aliases = _materialize_platform_aliases(
            platform_alias_histories,
            scope=current_scope,
            position=(line_number, getattr(node, "col_offset", 0)),
        )
        key_signals = _materialize_key_signals(
            key_signal_histories,
            scope=current_scope,
            position=(line_number, getattr(node, "col_offset", 0)),
        )
        shared_result_container_aliases = _materialize_shared_result_container_aliases(
            shared_result_container_histories,
            scope=current_scope,
            position=(line_number, getattr(node, "col_offset", 0)),
        )
        error_details_aliases = _materialize_error_details_aliases(
            error_details_histories,
            scope=current_scope,
            position=(line_number, getattr(node, "col_offset", 0)),
        )

        statement_lines = _statement_line_numbers(node)
        if statement_lines and all(line in allowed_exception_lines for line in statement_lines):
            continue

        boundary = boundary_resolver(line_number)
        evidence_ref = f"platform_leakage:{boundary}:{relative_name}:{line_number}"
        statement_source = _statement_source_segment(source_text, node)
        if _is_docstring_statement(node):
            continue
        if isinstance(node, ast.ClassDef) and _definition_has_platform_metadata(
            node,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
        ):
            findings.append(
                _finding(
                    code="single_platform_shared_semantic",
                    message=f"single-platform shared semantic leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )
            continue
        if _statement_has_platform_specific_field(
            statement_source,
            node,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        ):
            findings.append(
                _finding(
                    code="platform_specific_field_leak",
                    message=f"platform-specific field leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )
            continue

        if _statement_has_hardcoded_platform_branch(
            node,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
        ):
            findings.append(
                _finding(
                    code="hardcoded_platform_branch",
                    message=f"hardcoded platform branch leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )
            continue

        if _statement_has_single_platform_semantic(
            node,
            statement_source,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
        ):
            findings.append(
                _finding(
                    code="single_platform_shared_semantic",
                    message=f"single-platform shared semantic leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )

    return findings


def _statement_line_numbers(node: ast.AST) -> range:
    line_number = getattr(node, "lineno", 0)
    end_line_number = getattr(node, "end_lineno", line_number)
    return range(line_number, end_line_number + 1)


def _statement_source_segment(source_text: str, node: ast.AST) -> str:
    return ast.get_source_segment(source_text, node) or ""


def _build_parent_index(module: ast.AST) -> dict[ast.AST, ast.AST]:
    parent_index: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(module):
        for child in ast.iter_child_nodes(parent):
            parent_index[child] = parent
    return parent_index


def _enclosing_scope(node: ast.AST, parent_index: Mapping[ast.AST, ast.AST]) -> ast.AST:
    current = node
    while True:
        parent = parent_index.get(current)
        if parent is None:
            return current
        if isinstance(parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent
        current = parent


def _is_branch_local_assignment(node: ast.AST, parent_index: Mapping[ast.AST, ast.AST], scope: ast.AST) -> bool:
    current = node
    branch_types: tuple[type[ast.AST], ...] = tuple(
        branch_type
        for branch_type in (ast.If, ast.For, ast.AsyncFor, ast.While, _AST_MATCH, ast.Try)
        if branch_type is not None
    )
    while True:
        parent = parent_index.get(current)
        if parent is None or parent is scope:
            return False
        if isinstance(parent, branch_types):
            return True
        current = parent


def _assignment_value_and_targets(node: ast.AST) -> tuple[ast.AST | None, Sequence[ast.expr]]:
    if isinstance(node, ast.Assign):
        return node.value, node.targets
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return node.value, [node.target]
    if isinstance(node, ast.NamedExpr):
        return node.value, [node.target]
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return node.iter, [node.target]
    return None, ()


def _build_platform_alias_histories(
    module: ast.AST,
    parent_index: Mapping[ast.AST, ast.AST],
) -> dict[ast.AST, dict[str, list[tuple[tuple[int, int], bool, bool]]]]:
    histories: dict[ast.AST, dict[str, list[tuple[tuple[int, int], bool, bool]]]] = {}
    assignment_nodes = sorted(
        (
            node
            for node in ast.walk(module)
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr, ast.For, ast.AsyncFor))
        ),
        key=lambda item: (getattr(item, "lineno", 0), getattr(item, "col_offset", 0)),
    )
    for node in assignment_nodes:
        value, targets = _assignment_value_and_targets(node)
        if value is None:
            continue
        scope = _enclosing_scope(node, parent_index)
        platform_aliases = _materialize_platform_aliases(
            histories,
            scope=scope,
            position=(getattr(node, "lineno", 0), getattr(node, "col_offset", 0)),
        )
        is_platform_alias = _expr_is_platformish(value, platform_aliases=platform_aliases)
        scope_history = histories.setdefault(scope, {})
        branch_local = isinstance(node, (ast.For, ast.AsyncFor)) or _is_branch_local_assignment(node, parent_index, scope)
        for target in targets:
            for name in _assignment_target_names(target):
                scope_history.setdefault(name, []).append(
                    ((getattr(node, "lineno", 0), getattr(node, "col_offset", 0)), is_platform_alias, branch_local)
                )
    return histories


def _materialize_platform_aliases(
    histories: Mapping[ast.AST, Mapping[str, Sequence[tuple[tuple[int, int], bool, bool]]]],
    *,
    scope: ast.AST,
    position: tuple[int, int],
) -> frozenset[str]:
    aliases: set[str] = set()
    for name, events in histories.get(scope, {}).items():
        if _resolve_boolean_alias(events, position):
            aliases.add(name)
    return frozenset(aliases)


def _build_key_signal_histories(
    module: ast.AST,
    parent_index: Mapping[ast.AST, ast.AST],
    platform_alias_histories: Mapping[ast.AST, Mapping[str, Sequence[tuple[tuple[int, int], bool, bool]]]],
) -> dict[ast.AST, dict[str, list[tuple[tuple[int, int], tuple[frozenset[str], bool], bool]]]]:
    histories: dict[ast.AST, dict[str, list[tuple[tuple[int, int], tuple[frozenset[str], bool], bool]]]] = {}
    assignment_nodes = sorted(
        (node for node in ast.walk(module) if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))),
        key=lambda item: (getattr(item, "lineno", 0), getattr(item, "col_offset", 0)),
    )
    for node in assignment_nodes:
        value, targets = _assignment_value_and_targets(node)
        if value is None:
            continue
        scope = _enclosing_scope(node, parent_index)
        position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        platform_aliases = _materialize_platform_aliases(
            platform_alias_histories,
            scope=scope,
            position=position,
        )
        key_signals = _materialize_key_signals(
            histories,
            scope=scope,
            position=position,
        )
        signal = _key_signal_for_expr(
            value,
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        )
        scope_history = histories.setdefault(scope, {})
        branch_local = _is_branch_local_assignment(node, parent_index, scope)
        for target in targets:
            for name in _assignment_target_names(target):
                scope_history.setdefault(name, []).append((position, signal, branch_local))
    return histories


def _materialize_key_signals(
    histories: Mapping[ast.AST, Mapping[str, Sequence[tuple[tuple[int, int], tuple[frozenset[str], bool], bool]]]],
    *,
    scope: ast.AST,
    position: tuple[int, int],
) -> dict[str, tuple[frozenset[str], bool]]:
    signals: dict[str, tuple[frozenset[str], bool]] = {}
    for name, events in histories.get(scope, {}).items():
        resolved = _resolve_key_signal(events, position)
        if resolved != _EMPTY_KEY_SIGNAL:
            signals[name] = resolved
    return signals


def _build_shared_result_container_histories(
    module: ast.AST,
    parent_index: Mapping[ast.AST, ast.AST],
) -> dict[ast.AST, dict[str, list[tuple[tuple[int, int], frozenset[str], bool]]]]:
    histories: dict[ast.AST, dict[str, list[tuple[tuple[int, int], frozenset[str], bool]]]] = {}
    assignment_nodes = sorted(
        (node for node in ast.walk(module) if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))),
        key=lambda item: (getattr(item, "lineno", 0), getattr(item, "col_offset", 0)),
    )
    for node in assignment_nodes:
        value, targets = _assignment_value_and_targets(node)
        if value is None:
            continue
        scope = _enclosing_scope(node, parent_index)
        container_aliases = _materialize_shared_result_container_aliases(
            histories,
            scope=scope,
            position=(getattr(node, "lineno", 0), getattr(node, "col_offset", 0)),
        )
        container_names = _root_shared_result_container_names(
            value,
            shared_result_container_aliases=container_aliases,
        )
        scope_history = histories.setdefault(scope, {})
        branch_local = _is_branch_local_assignment(node, parent_index, scope)
        for target in targets:
            for name in _assignment_target_names(target):
                scope_history.setdefault(name, []).append(
                    ((getattr(node, "lineno", 0), getattr(node, "col_offset", 0)), container_names, branch_local)
                )
    return histories


def _build_error_details_histories(
    module: ast.AST,
    parent_index: Mapping[ast.AST, ast.AST],
) -> dict[ast.AST, dict[str, list[tuple[tuple[int, int], frozenset[str], bool]]]]:
    histories: dict[ast.AST, dict[str, list[tuple[tuple[int, int], frozenset[str], bool]]]] = {}
    assignment_nodes = sorted(
        (node for node in ast.walk(module) if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))),
        key=lambda item: (getattr(item, "lineno", 0), getattr(item, "col_offset", 0)),
    )
    for node in assignment_nodes:
        value, targets = _assignment_value_and_targets(node)
        if value is None:
            continue
        scope = _enclosing_scope(node, parent_index)
        error_details_aliases = _materialize_error_details_aliases(
            histories,
            scope=scope,
            position=(getattr(node, "lineno", 0), getattr(node, "col_offset", 0)),
        )
        error_details_paths = _possible_error_details_paths(
            value,
            error_details_aliases=error_details_aliases,
        )
        scope_history = histories.setdefault(scope, {})
        branch_local = _is_branch_local_assignment(node, parent_index, scope)
        for target in targets:
            for name in _assignment_target_names(target):
                scope_history.setdefault(name, []).append(
                    ((getattr(node, "lineno", 0), getattr(node, "col_offset", 0)), error_details_paths, branch_local)
                )
    return histories


def _materialize_shared_result_container_aliases(
    histories: Mapping[ast.AST, Mapping[str, Sequence[tuple[tuple[int, int], frozenset[str], bool]]]],
    *,
    scope: ast.AST,
    position: tuple[int, int],
) -> dict[str, frozenset[str]]:
    alias_map: dict[str, frozenset[str]] = {}
    for name, events in histories.get(scope, {}).items():
        resolved = _resolve_container_aliases(events, position)
        if resolved:
            alias_map[name] = resolved
    return alias_map


def _materialize_error_details_aliases(
    histories: Mapping[ast.AST, Mapping[str, Sequence[tuple[tuple[int, int], frozenset[str], bool]]]],
    *,
    scope: ast.AST,
    position: tuple[int, int],
) -> dict[str, frozenset[str]]:
    aliases: dict[str, frozenset[str]] = {}
    for name, events in histories.get(scope, {}).items():
        resolved = _resolve_path_aliases(events, position)
        if resolved:
            aliases[name] = resolved
    return aliases


def _resolve_container_aliases(
    events: Sequence[tuple[tuple[int, int], frozenset[str], bool]],
    position: tuple[int, int],
) -> frozenset[str]:
    active_values: set[str] = set()
    for event_position, value, branch_local in events:
        if event_position >= position:
            break
        if branch_local:
            active_values.update(value)
            continue
        active_values = set(value)
    return frozenset(active_values)


def _resolve_boolean_alias(
    events: Sequence[tuple[tuple[int, int], bool, bool]],
    position: tuple[int, int],
) -> bool:
    active_values: set[bool] = set()
    for event_position, value, branch_local in events:
        if event_position >= position:
            break
        if branch_local:
            active_values.add(value)
            continue
        active_values = {value}
    return True in active_values


def _resolve_path_aliases(
    events: Sequence[tuple[tuple[int, int], frozenset[str], bool]],
    position: tuple[int, int],
) -> frozenset[str]:
    active_values: set[str] = set()
    for event_position, value, branch_local in events:
        if event_position >= position:
            break
        if branch_local:
            active_values.update(value)
            continue
        active_values = set(value)
    return frozenset(active_values)


def _resolve_key_signal(
    events: Sequence[tuple[tuple[int, int], tuple[frozenset[str], bool], bool]],
    position: tuple[int, int],
) -> tuple[frozenset[str], bool]:
    active_literals: frozenset[str] = frozenset()
    active_dynamic = False
    for event_position, value, branch_local in events:
        if event_position >= position:
            break
        literals, dynamic = value
        if branch_local:
            active_literals = active_literals.union(literals)
            active_dynamic = active_dynamic or dynamic
            continue
        active_literals = literals
        active_dynamic = dynamic
    return (active_literals, active_dynamic)


def _collect_platform_aliases(module: ast.AST) -> frozenset[str]:
    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(module):
            value = None
            targets: Sequence[ast.expr] = ()
            if isinstance(node, ast.Assign):
                value = node.value
                targets = node.targets
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                value = node.value
                targets = [node.target]
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                value = node.iter
                targets = [node.target]
            else:
                continue

            if not _expr_is_platformish(value, platform_aliases=frozenset(aliases)):
                continue
            for target in targets:
                for name in _assignment_target_names(target):
                    if name not in aliases:
                        aliases.add(name)
                        changed = True
    return frozenset(aliases)


def _assignment_target_names(target: ast.expr) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for item in target.elts:
            names.extend(_assignment_target_names(item))
        return tuple(names)
    return ()


def _statement_has_platform_specific_field(
    statement_source: str,
    node: ast.AST,
    *,
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
    platform_aliases: frozenset[str],
) -> bool:
    if _expr_contains_disallowed_shared_field(
        node,
        shared_result_container_aliases=shared_result_container_aliases,
        error_details_aliases=error_details_aliases,
        key_signals=key_signals,
        platform_aliases=platform_aliases,
    ):
        return True
    if _PLATFORM_FIELD_RE.search(statement_source) is not None:
        return True
    return any(_string_literal_has_platform_specific_fragment(literal) for literal in _string_literals(node))


def _statement_has_hardcoded_platform_branch(
    node: ast.stmt,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
) -> bool:
    if isinstance(node, ast.If):
        return _expr_has_platform_literal_compare(
            node.test,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
        )
    if _AST_MATCH is not None and isinstance(node, _AST_MATCH):
        return _match_has_platform_literal_branch(
            node,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
        )
    return _expr_has_platform_literal_compare(
        node,
        platform_aliases=platform_aliases,
        shared_result_container_aliases=shared_result_container_aliases,
        error_details_aliases=error_details_aliases,
        key_signals=key_signals,
    )


def _statement_has_single_platform_semantic(
    node: ast.stmt,
    statement_source: str,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
) -> bool:
    if isinstance(node, ast.Assign):
        return _assignment_has_single_platform_semantic(
            node.targets,
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
        )
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return _assignment_has_single_platform_semantic(
            [node.target],
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
        )
    if isinstance(node, ast.AugAssign):
        return _assignment_has_single_platform_semantic(
            [node.target],
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
        )
    if isinstance(node, ast.Return) and node.value is not None:
        return _expr_has_shared_platform_semantic(
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
        )
    if isinstance(node, ast.Raise) and node.exc is not None:
        return _expr_contains_platform_marker(node.exc)
    if isinstance(node, ast.Expr):
        return _expr_has_shared_platform_semantic(
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
        )
    return False


def _assignment_has_single_platform_semantic(
    targets: Sequence[ast.expr],
    value: ast.expr,
    statement_source: str,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
) -> bool:
    if _expr_has_platform_literal_compare(value, platform_aliases=platform_aliases):
        return True

    if targets and all(
        _target_is_approved_platform_carrier(
            target,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
        )
        for target in targets
    ):
        return False

    if _expr_contains_unapproved_platform_literal(value):
        return True

    if any(_expr_is_platformish(target, platform_aliases=platform_aliases) for target in targets) and _expr_contains_unapproved_platform_literal(value):
        return True

    return _statement_has_semantic_platform_literal(statement_source, value)


def _expr_has_shared_platform_semantic(
    value: ast.AST,
    statement_source: str,
    *,
    platform_aliases: frozenset[str],
) -> bool:
    if _expr_has_platform_literal_compare(value, platform_aliases=platform_aliases):
        return True
    return _statement_has_semantic_platform_literal(statement_source, value)


def _function_has_single_platform_semantic(
    node: ast.AST,
    function_source: str,
    *,
    platform_aliases: frozenset[str],
) -> bool:
    args = getattr(node, "args", None)
    if args is None:
        return False
    defaults = list(getattr(args, "defaults", ()))
    defaults.extend(default for default in getattr(args, "kw_defaults", ()) if default is not None)
    return any(
        _expr_has_shared_platform_semantic(
            default,
            function_source,
            platform_aliases=platform_aliases,
        )
        for default in defaults
    )


def _definition_has_platform_metadata(
    node: ast.AST,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
) -> bool:
    metadata_nodes: list[ast.AST] = list(getattr(node, "decorator_list", ()))
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = node.args
        metadata_nodes.extend(arg.annotation for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs) if arg.annotation is not None)
        if args.vararg is not None and args.vararg.annotation is not None:
            metadata_nodes.append(args.vararg.annotation)
        if args.kwarg is not None and args.kwarg.annotation is not None:
            metadata_nodes.append(args.kwarg.annotation)
        if node.returns is not None:
            metadata_nodes.append(node.returns)
    elif isinstance(node, ast.ClassDef):
        metadata_nodes.extend(node.bases)
        metadata_nodes.extend(keyword.value for keyword in node.keywords)

    return any(
        _expr_has_platform_literal_compare(
            metadata_node,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals={},
        )
        or _expr_contains_unapproved_platform_literal(metadata_node)
        or _expr_contains_platform_marker(metadata_node)
        for metadata_node in metadata_nodes
    )


def _target_is_approved_platform_carrier(
    target: ast.expr,
    *,
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
) -> bool:
    if isinstance(target, ast.Attribute):
        return target.attr == "platform" and _is_normalized_container(
            target.value,
            shared_result_container_aliases=shared_result_container_aliases,
            require_definite=True,
        )
    if not isinstance(target, ast.Subscript):
        return False
    if not any(literal == "platform" for literal in _string_literals(target.slice)):
        return False
    return _is_normalized_container(
        target.value,
        shared_result_container_aliases=shared_result_container_aliases,
        require_definite=True,
    ) or _is_error_details_container(
        target.value,
        error_details_aliases=error_details_aliases,
        require_definite=True,
    )


def _statement_has_semantic_platform_literal(statement_source: str, value: ast.AST) -> bool:
    normalized_source = statement_source.lower().replace("_", " ")
    if _SEMANTIC_CONTEXT_RE.search(normalized_source) is None:
        return False
    return _expr_contains_unapproved_platform_literal(value)


def _match_has_platform_literal_branch(
    node: ast.AST,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
) -> bool:
    subject_is_platformish = _expr_is_platformish(node.subject, platform_aliases=platform_aliases)
    subject_is_explicit_carrier = _expr_is_explicit_platform_carrier(
        node.subject,
        platform_aliases=platform_aliases,
        shared_result_container_aliases=shared_result_container_aliases,
        error_details_aliases=error_details_aliases,
        key_signals=key_signals,
    )
    subject_is_platform_container = _is_normalized_container(
        node.subject,
        shared_result_container_aliases=shared_result_container_aliases,
    ) or _is_error_details_container(
        node.subject,
        error_details_aliases=error_details_aliases,
    )

    for case in node.cases:
        case_platform_aliases = set(platform_aliases)
        if subject_is_platformish or subject_is_explicit_carrier:
            case_platform_aliases.update(_pattern_capture_names(case.pattern))
        if subject_is_platform_container:
            case_platform_aliases.update(_pattern_platform_capture_names(case.pattern))

        if subject_is_platformish and _pattern_contains_platform_literal(case.pattern):
            return True
        if subject_is_platform_container and _pattern_contains_platform_mapping_literal(case.pattern):
            return True
        if case.guard is None:
            continue
        if _expr_has_platform_literal_compare(
            case.guard,
            platform_aliases=frozenset(case_platform_aliases),
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
        ):
            return True
    return False


def _pattern_contains_platform_literal(pattern: ast.AST) -> bool:
    if _AST_MATCH_VALUE is not None and isinstance(pattern, _AST_MATCH_VALUE):
        return _expr_contains_platform_branch_literal(pattern.value)
    if _AST_MATCH_SINGLETON is not None and isinstance(pattern, _AST_MATCH_SINGLETON):
        return False
    if _AST_MATCH_SEQUENCE is not None and isinstance(pattern, _AST_MATCH_SEQUENCE):
        return any(_pattern_contains_platform_literal(item) for item in pattern.patterns)
    if _AST_MATCH_OR is not None and isinstance(pattern, _AST_MATCH_OR):
        return any(_pattern_contains_platform_literal(item) for item in pattern.patterns)
    if _AST_MATCH_AS is not None and isinstance(pattern, _AST_MATCH_AS):
        return pattern.pattern is not None and _pattern_contains_platform_literal(pattern.pattern)
    if _AST_MATCH_MAPPING is not None and isinstance(pattern, _AST_MATCH_MAPPING):
        return any(_pattern_contains_platform_literal(item) for item in pattern.patterns)
    return False


def _pattern_capture_names(pattern: ast.AST) -> frozenset[str]:
    names: set[str] = set()
    for child in ast.walk(pattern):
        if _AST_MATCH_AS is not None and isinstance(child, _AST_MATCH_AS) and child.name:
            names.add(child.name)
        if _AST_MATCH_STAR is not None and isinstance(child, _AST_MATCH_STAR) and child.name:
            names.add(child.name)
    return frozenset(names)


def _pattern_platform_capture_names(pattern: ast.AST) -> frozenset[str]:
    if _AST_MATCH_MAPPING is not None and isinstance(pattern, _AST_MATCH_MAPPING):
        names: set[str] = set()
        for key, value_pattern in zip(pattern.keys, pattern.patterns):
            if any(literal == "platform" for literal in _string_literals(key)):
                names.update(_pattern_capture_names(value_pattern))
            names.update(_pattern_platform_capture_names(value_pattern))
        return frozenset(names)
    if _AST_MATCH_SEQUENCE is not None and isinstance(pattern, _AST_MATCH_SEQUENCE):
        return frozenset().union(*(_pattern_platform_capture_names(item) for item in pattern.patterns))
    if _AST_MATCH_OR is not None and isinstance(pattern, _AST_MATCH_OR):
        return frozenset().union(*(_pattern_platform_capture_names(item) for item in pattern.patterns))
    if _AST_MATCH_AS is not None and isinstance(pattern, _AST_MATCH_AS) and pattern.pattern is not None:
        return _pattern_platform_capture_names(pattern.pattern)
    return frozenset()


def _pattern_contains_platform_mapping_literal(pattern: ast.AST) -> bool:
    if _AST_MATCH_MAPPING is not None and isinstance(pattern, _AST_MATCH_MAPPING):
        for key, value_pattern in zip(pattern.keys, pattern.patterns):
            if any(literal == "platform" for literal in _string_literals(key)) and _pattern_contains_platform_literal(
                value_pattern
            ):
                return True
            if _pattern_contains_platform_mapping_literal(value_pattern):
                return True
        return False
    if _AST_MATCH_SEQUENCE is not None and isinstance(pattern, _AST_MATCH_SEQUENCE):
        return any(_pattern_contains_platform_mapping_literal(item) for item in pattern.patterns)
    if _AST_MATCH_OR is not None and isinstance(pattern, _AST_MATCH_OR):
        return any(_pattern_contains_platform_mapping_literal(item) for item in pattern.patterns)
    if _AST_MATCH_AS is not None and isinstance(pattern, _AST_MATCH_AS) and pattern.pattern is not None:
        return _pattern_contains_platform_mapping_literal(pattern.pattern)
    return False


def _expr_has_platform_literal_compare(
    node: ast.AST,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]] | None = None,
    error_details_aliases: Mapping[str, frozenset[str]] | None = None,
    key_signals: Mapping[str, tuple[frozenset[str], bool]] | None = None,
) -> bool:
    shared_result_container_aliases = shared_result_container_aliases or {}
    error_details_aliases = error_details_aliases or {}
    key_signals = key_signals or {}
    if isinstance(node, ast.Call) and _call_has_platform_branch_signal(node, platform_aliases=platform_aliases):
        return True
    if isinstance(node, ast.Compare):
        current = node.left
        for operator, comparator in zip(node.ops, node.comparators):
            if _compare_pair_has_platform_literal(
                current,
                comparator,
                operator,
                platform_aliases=platform_aliases,
                shared_result_container_aliases=shared_result_container_aliases,
                error_details_aliases=error_details_aliases,
                key_signals=key_signals,
            ):
                return True
            current = comparator
    return any(
        _expr_has_platform_literal_compare(
            child,
            platform_aliases=platform_aliases,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
        )
        for child in ast.iter_child_nodes(node)
        if not (isinstance(node, ast.stmt) and isinstance(child, ast.stmt))
    )


def _compare_pair_has_platform_literal(
    left: ast.AST,
    right: ast.AST,
    operator: ast.AST,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
) -> bool:
    if isinstance(operator, (ast.Eq, ast.NotEq)):
        if (
            _expr_is_explicit_platform_carrier(
                left,
                platform_aliases=platform_aliases,
                shared_result_container_aliases=shared_result_container_aliases,
                error_details_aliases=error_details_aliases,
                key_signals=key_signals,
            )
            and _expr_is_platformish(right, platform_aliases=platform_aliases)
        ) or (
            _expr_is_explicit_platform_carrier(
                right,
                platform_aliases=platform_aliases,
                shared_result_container_aliases=shared_result_container_aliases,
                error_details_aliases=error_details_aliases,
                key_signals=key_signals,
            )
            and _expr_is_platformish(left, platform_aliases=platform_aliases)
        ):
            return True
        return (_expr_is_platformish(left, platform_aliases=platform_aliases) and _expr_contains_platform_branch_literal(right)) or (
            _expr_is_platformish(right, platform_aliases=platform_aliases) and _expr_contains_platform_branch_literal(left)
        )
    if isinstance(operator, (ast.In, ast.NotIn)):
        return (_expr_is_platformish(left, platform_aliases=platform_aliases) and _expr_contains_platform_branch_literal(right)) or (
            _expr_is_platformish(right, platform_aliases=platform_aliases) and _expr_contains_platform_branch_literal(left)
        )
    return False


def _expr_is_platformish(node: ast.AST, *, platform_aliases: frozenset[str]) -> bool:
    if isinstance(node, ast.NamedExpr):
        return _expr_is_platformish(node.value, platform_aliases=platform_aliases)
    if isinstance(node, ast.IfExp):
        return _expr_is_platformish(node.body, platform_aliases=platform_aliases) or _expr_is_platformish(
            node.orelse,
            platform_aliases=platform_aliases,
        )
    if isinstance(node, ast.Name):
        return node.id in platform_aliases or _identifier_matches(node.id, _PLATFORM_IDENTIFIER_RE)
    if isinstance(node, ast.Attribute):
        return _identifier_matches(node.attr, _PLATFORM_IDENTIFIER_RE) or _expr_is_platformish(
            node.value,
            platform_aliases=platform_aliases,
        )
    if isinstance(node, ast.Subscript):
        return _subscript_is_platformish(node, platform_aliases=platform_aliases)
    if isinstance(node, ast.Call):
        return _call_is_platformish(node, platform_aliases=platform_aliases)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return any(_expr_is_platformish(item, platform_aliases=platform_aliases) for item in node.elts)
    return False


def _subscript_is_platformish(node: ast.Subscript, *, platform_aliases: frozenset[str]) -> bool:
    if _expr_is_platformish(node.value, platform_aliases=platform_aliases):
        return True
    return any(_identifier_matches(literal, _PLATFORM_IDENTIFIER_RE) for literal in _string_literals(node.slice))


def _call_is_platformish(node: ast.Call, *, platform_aliases: frozenset[str]) -> bool:
    if _expr_is_platformish(node.func, platform_aliases=platform_aliases):
        return True
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "get":
        return False
    if not node.args:
        return False
    first_arg = node.args[0]
    return any(_identifier_matches(literal, _PLATFORM_IDENTIFIER_RE) for literal in _string_literals(first_arg))


def _call_has_platform_branch_signal(node: ast.Call, *, platform_aliases: frozenset[str]) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in {"startswith", "endswith", "removeprefix", "removesuffix"}:
        return False
    if not _expr_is_platformish(node.func.value, platform_aliases=platform_aliases):
        return False
    return any(_expr_contains_platform_branch_literal(argument) for argument in node.args)


def _expr_is_explicit_platform_carrier(
    node: ast.AST,
    *,
    platform_aliases: frozenset[str],
    shared_result_container_aliases: Mapping[str, frozenset[str]] | None = None,
    error_details_aliases: Mapping[str, frozenset[str]] | None = None,
    key_signals: Mapping[str, tuple[frozenset[str], bool]] | None = None,
) -> bool:
    shared_result_container_aliases = shared_result_container_aliases or {}
    error_details_aliases = error_details_aliases or {}
    key_signals = key_signals or {}
    if isinstance(node, ast.Attribute):
        return node.attr == "platform" and _is_normalized_container(
            node.value,
            shared_result_container_aliases=shared_result_container_aliases,
        )
    if isinstance(node, ast.Subscript):
        return _key_signal_matches_platform(
            _key_signal_for_expr(
                node.slice,
                key_signals=key_signals,
                platform_aliases=platform_aliases,
            )
        ) and (
            _is_normalized_container(
                node.value,
                shared_result_container_aliases=shared_result_container_aliases,
            )
            or _is_error_details_container(
                node.value,
                error_details_aliases=error_details_aliases,
            )
        )
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "get" or not node.args:
            return False
        if not _key_signal_matches_platform(
            _key_signal_for_expr(
                node.args[0],
                key_signals=key_signals,
                platform_aliases=platform_aliases,
            )
        ):
            return False
        return _is_normalized_container(
            node.func.value,
            shared_result_container_aliases=shared_result_container_aliases,
        ) or _is_error_details_container(
            node.func.value,
            error_details_aliases=error_details_aliases,
        )
    return False


def _is_normalized_container(
    node: ast.AST,
    *,
    shared_result_container_aliases: Mapping[str, frozenset[str]] | None = None,
    require_definite: bool = False,
) -> bool:
    shared_result_container_aliases = shared_result_container_aliases or {}
    container_names = _root_shared_result_container_names(
        node,
        shared_result_container_aliases=shared_result_container_aliases,
    )
    if require_definite:
        return container_names == frozenset({"normalized"})
    return "normalized" in container_names


def _is_error_details_container(
    node: ast.AST,
    *,
    error_details_aliases: Mapping[str, frozenset[str]] | None = None,
    require_definite: bool = False,
) -> bool:
    error_details_aliases = error_details_aliases or {}
    paths = _possible_error_details_paths(
        node,
        error_details_aliases=error_details_aliases,
    )
    if require_definite:
        return paths == frozenset({"error.details"})
    return "error.details" in paths


def _is_error_container(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return _identifier_matches(node.id, _ERROR_CONTAINER_RE)
    if isinstance(node, ast.Attribute):
        return _identifier_matches(node.attr, _ERROR_CONTAINER_RE) or _is_error_container(node.value)
    if isinstance(node, ast.Subscript):
        return any(_identifier_matches(literal, _ERROR_CONTAINER_RE) for literal in _string_literals(node.slice)) or _is_error_container(
            node.value
        )
    return False


def _expr_contains_string_literal(node: ast.AST) -> bool:
    return bool(_string_literals(node))


def _expr_contains_platform_literal(node: ast.AST) -> bool:
    return any(_is_common_platform_literal(literal) for literal in _string_literals(node))


def _expr_contains_platform_branch_literal(node: ast.AST) -> bool:
    return any(_string_literal_is_platform_branch_literal(literal) for literal in _string_literals(node))


def _string_literal_is_platform_branch_literal(value: str) -> bool:
    lowered = value.lower()
    return _is_common_platform_literal(lowered) or _PLATFORM_BRANCH_VARIANT_RE.match(lowered) is not None


def _expr_contains_unapproved_platform_literal(node: ast.AST, *, path: tuple[str, ...] = ()) -> bool:
    if isinstance(node, ast.Dict):
        return _dict_contains_unapproved_platform_literal(node, path=path)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return any(_expr_contains_unapproved_platform_literal(item, path=path) for item in node.elts)
    return _expr_contains_platform_literal(node)


def _dict_contains_unapproved_platform_literal(node: ast.Dict, *, path: tuple[str, ...]) -> bool:
    for key, value in zip(node.keys, node.values):
        key_name = _single_string_literal(key)
        next_path = path + ((key_name,) if key_name is not None else ())
        if key_name is not None and _is_approved_platform_carrier_path(next_path):
            continue
        if _expr_contains_unapproved_platform_literal(value, path=next_path):
            return True
    return False


def _expr_contains_disallowed_shared_field(
    node: ast.AST,
    *,
    path: tuple[str, ...] = (),
    shared_result_container_aliases: Mapping[str, frozenset[str]] | None = None,
    error_details_aliases: Mapping[str, frozenset[str]] | None = None,
    key_signals: Mapping[str, tuple[frozenset[str], bool]] | None = None,
    platform_aliases: frozenset[str] | None = None,
) -> bool:
    shared_result_container_aliases = shared_result_container_aliases or {}
    error_details_aliases = error_details_aliases or {}
    key_signals = key_signals or {}
    platform_aliases = platform_aliases or frozenset()
    if isinstance(node, ast.Dict):
        return _dict_contains_disallowed_shared_field(
            node,
            path=path,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        )
    if isinstance(node, ast.Call):
        return _call_contains_disallowed_shared_field(
            node,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        )
    if isinstance(node, ast.Subscript):
        return _subscript_contains_disallowed_shared_field(
            node,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        )
    return any(
        _expr_contains_disallowed_shared_field(
            child,
            path=path,
            shared_result_container_aliases=shared_result_container_aliases,
            error_details_aliases=error_details_aliases,
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        )
        for child in ast.iter_child_nodes(node)
    )


def _dict_contains_disallowed_shared_field(
    node: ast.Dict,
    *,
    path: tuple[str, ...],
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
    platform_aliases: frozenset[str],
) -> bool:
    for key, value in zip(node.keys, node.values):
        signal = _key_signal_for_expr(
            key,
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        )
        if path and _signal_causes_disallowed_shared_field(path, signal):
            return True
        exact_literals, dynamic_platform_key = signal
        next_paths = [path]
        if not dynamic_platform_key and len(exact_literals) == 1:
            next_paths = [path + (next(iter(exact_literals)),)]
        for next_path in next_paths:
            if _expr_contains_disallowed_shared_field(
            value,
                path=next_path,
                shared_result_container_aliases=shared_result_container_aliases,
                error_details_aliases=error_details_aliases,
                key_signals=key_signals,
                platform_aliases=platform_aliases,
            ):
                return True
    return False


def _call_contains_disallowed_shared_field(
    node: ast.Call,
    *,
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
    platform_aliases: frozenset[str],
) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    container_paths = _possible_shared_field_carrier_paths(
        node.func.value,
        shared_result_container_aliases=shared_result_container_aliases,
        error_details_aliases=error_details_aliases,
    )
    if not container_paths:
        return False
    if node.func.attr == "setdefault":
        if not node.args:
            return False
        signal = _key_signal_for_expr(
            node.args[0],
            key_signals=key_signals,
            platform_aliases=platform_aliases,
        )
        return any(_signal_causes_disallowed_shared_field(path, signal) for path in container_paths)
    if node.func.attr != "update":
        return False
    for argument in node.args:
        for path in container_paths:
            if _expr_contains_disallowed_shared_field(
                argument,
                path=path,
                shared_result_container_aliases=shared_result_container_aliases,
                error_details_aliases=error_details_aliases,
                key_signals=key_signals,
                platform_aliases=platform_aliases,
            ):
                return True
    for keyword in node.keywords:
        if keyword.arg is not None:
            signal = (frozenset({keyword.arg}), False)
            if any(_signal_causes_disallowed_shared_field(path, signal) for path in container_paths):
                return True
            continue
        for path in container_paths:
            if _expr_contains_disallowed_shared_field(
                keyword.value,
                path=path,
                shared_result_container_aliases=shared_result_container_aliases,
                error_details_aliases=error_details_aliases,
                key_signals=key_signals,
                platform_aliases=platform_aliases,
            ):
                return True
    return False


def _subscript_contains_disallowed_shared_field(
    node: ast.Subscript,
    *,
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
    platform_aliases: frozenset[str],
) -> bool:
    container_paths = _possible_shared_field_carrier_paths(
        node.value,
        shared_result_container_aliases=shared_result_container_aliases,
        error_details_aliases=error_details_aliases,
    )
    if not container_paths:
        return False
    signal = _key_signal_for_expr(
        node.slice,
        key_signals=key_signals,
        platform_aliases=platform_aliases,
    )
    return any(_signal_causes_disallowed_shared_field(path, signal) for path in container_paths)


def _root_shared_result_container_names(
    node: ast.AST,
    *,
    shared_result_container_aliases: Mapping[str, frozenset[str]] | None = None,
) -> frozenset[str]:
    shared_result_container_aliases = shared_result_container_aliases or {}
    if isinstance(node, ast.NamedExpr):
        return _root_shared_result_container_names(
            node.value,
            shared_result_container_aliases=shared_result_container_aliases,
        )
    if isinstance(node, ast.IfExp):
        return _root_shared_result_container_names(
            node.body,
            shared_result_container_aliases=shared_result_container_aliases,
        ).union(
            _root_shared_result_container_names(
                node.orelse,
                shared_result_container_aliases=shared_result_container_aliases,
            )
        )
    if isinstance(node, ast.Name):
        if node.id in {"normalized", "raw"}:
            return frozenset({node.id})
        return shared_result_container_aliases.get(node.id, frozenset())
    if isinstance(node, ast.Subscript):
        container_names = {literal for literal in _string_literals(node.slice) if literal in {"normalized", "raw"}}
        if container_names:
            return frozenset(container_names)
    if isinstance(node, ast.Attribute) and node.attr in {"normalized", "raw"}:
        return frozenset({node.attr})
    return frozenset()


def _possible_error_details_paths(
    node: ast.AST,
    *,
    error_details_aliases: Mapping[str, frozenset[str]] | None = None,
) -> frozenset[str]:
    error_details_aliases = error_details_aliases or {}
    if isinstance(node, ast.NamedExpr):
        return _possible_error_details_paths(node.value, error_details_aliases=error_details_aliases)
    if isinstance(node, ast.IfExp):
        return _possible_error_details_paths(node.body, error_details_aliases=error_details_aliases).union(
            _possible_error_details_paths(node.orelse, error_details_aliases=error_details_aliases)
        )
    if isinstance(node, ast.Name):
        return error_details_aliases.get(node.id, frozenset())
    if isinstance(node, ast.Attribute):
        if node.attr == "details" and _is_error_container(node.value):
            return frozenset({"error.details"})
        return frozenset()
    if isinstance(node, ast.Subscript):
        if any(literal == "details" for literal in _string_literals(node.slice)) and _is_error_container(node.value):
            return frozenset({"error.details"})
    return frozenset()


def _possible_shared_field_carrier_paths(
    node: ast.AST,
    *,
    shared_result_container_aliases: Mapping[str, frozenset[str]],
    error_details_aliases: Mapping[str, frozenset[str]],
) -> frozenset[tuple[str, ...]]:
    paths = {(container_name,) for container_name in _root_shared_result_container_names(
        node,
        shared_result_container_aliases=shared_result_container_aliases,
    )}
    if _is_error_details_container(node, error_details_aliases=error_details_aliases):
        paths.add(("error", "details"))
    return frozenset(paths)


def _key_signal_for_expr(
    node: ast.AST | None,
    *,
    key_signals: Mapping[str, tuple[frozenset[str], bool]],
    platform_aliases: frozenset[str],
) -> tuple[frozenset[str], bool]:
    if node is None:
        return _EMPTY_KEY_SIGNAL
    if isinstance(node, ast.NamedExpr):
        return _key_signal_for_expr(node.value, key_signals=key_signals, platform_aliases=platform_aliases)
    if isinstance(node, ast.IfExp):
        return _merge_key_signals(
            _key_signal_for_expr(node.body, key_signals=key_signals, platform_aliases=platform_aliases),
            _key_signal_for_expr(node.orelse, key_signals=key_signals, platform_aliases=platform_aliases),
        )
    if isinstance(node, ast.Name):
        return key_signals.get(node.id, _EMPTY_KEY_SIGNAL)
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
        return (frozenset({node.value}), False)
    if isinstance(node, ast.JoinedStr):
        return (
            frozenset(),
            any(
                isinstance(value, ast.FormattedValue) and _expr_is_platformish(value.value, platform_aliases=platform_aliases)
                for value in node.values
            ),
        )
    return _EMPTY_KEY_SIGNAL


def _merge_key_signals(
    left: tuple[frozenset[str], bool],
    right: tuple[frozenset[str], bool],
) -> tuple[frozenset[str], bool]:
    return (left[0].union(right[0]), left[1] or right[1])


def _key_signal_matches_platform(signal: tuple[frozenset[str], bool]) -> bool:
    return "platform" in signal[0]


def _signal_causes_disallowed_shared_field(path: tuple[str, ...], signal: tuple[frozenset[str], bool]) -> bool:
    literals, dynamic_platform_key = signal
    if dynamic_platform_key and _is_shared_field_carrier_path(path):
        return True
    return any(_is_disallowed_shared_result_field_path(path + (literal,)) for literal in literals)


def _is_shared_field_carrier_path(path: tuple[str, ...]) -> bool:
    return (len(path) >= 1 and path[0] in {"normalized", "raw"}) or (len(path) >= 2 and path[:2] == ("error", "details"))


def _is_approved_platform_carrier_path(path: tuple[str, ...]) -> bool:
    return path in {
        ("normalized", "platform"),
        ("error", "details", "platform"),
    }


def _is_disallowed_shared_result_field_path(path: tuple[str, ...]) -> bool:
    if len(path) >= 3 and path[:2] == ("error", "details"):
        return _is_disallowed_shared_field_name(path[-1]) and path[-1].lower() != "platform"
    if len(path) < 2 or path[0] not in {"normalized", "raw"}:
        return False
    field_name = path[-1].lower()
    if field_name == "x":
        return False
    if field_name == "platform":
        return path[0] == "raw"
    return _is_disallowed_shared_field_name(field_name)


def _is_disallowed_shared_field_name(field_name: str) -> bool:
    normalized_field_name = field_name.lower()
    if normalized_field_name in {"platform", "x"}:
        return False
    if _COMMON_PLATFORM_NAME_RE.search(normalized_field_name) is not None or _string_literal_has_platform_specific_fragment(
        normalized_field_name
    ):
        return True
    return any(
        literal != "x"
        and (
            normalized_field_name == literal
            or normalized_field_name.startswith(f"{literal}_")
            or normalized_field_name.startswith(f"{literal}-")
        )
        for literal in _COMMON_PLATFORM_LITERALS
    )


def _is_disallowed_field_key_literal(field_name: str) -> bool:
    normalized_field_name = field_name.lower()
    if _string_literal_has_platform_specific_fragment(normalized_field_name):
        return True
    return any(
        literal != "x"
        and (normalized_field_name.startswith(f"{literal}_") or normalized_field_name.startswith(f"{literal}-"))
        for literal in _COMMON_PLATFORM_LITERALS
    )


def _single_string_literal(node: ast.AST | None) -> str | None:
    literals = _string_literals(node) if node is not None else ()
    if len(literals) != 1:
        return None
    return literals[0]


def _expr_contains_platform_marker(node: ast.AST) -> bool:
    return any(
        _string_literal_has_platform_marker(literal)
        for literal in _string_literals(node)
    )


def _string_literals(node: ast.AST) -> tuple[str, ...]:
    literals: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str) and child.value:
            literals.append(child.value)
    return tuple(literals)


def _is_common_platform_literal(value: str) -> bool:
    return value.lower() in _COMMON_PLATFORM_LITERALS


def _is_docstring_statement(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def _identifier_matches(value: str, pattern: re.Pattern[str]) -> bool:
    return pattern.search(value.lower()) is not None


def _string_literal_has_platform_specific_fragment(value: str) -> bool:
    return _PLATFORM_STRING_FRAGMENT_RE.search(value.lower()) is not None


def _string_literal_has_platform_marker(value: str) -> bool:
    lowered = value.lower()
    return _is_common_platform_literal(lowered) or _COMMON_PLATFORM_NAME_RE.search(lowered) is not None or _string_literal_has_platform_specific_fragment(lowered)


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
