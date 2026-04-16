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
_PLATFORM_IDENTIFIER_RE = re.compile(r"(?:^|_)(adapter|adapter_key|platform|platforms|platform_key|reference_pair)(?:_|$)")
_AST_MATCH = getattr(ast, "Match", None)
_AST_MATCH_VALUE = getattr(ast, "MatchValue", None)
_AST_MATCH_SINGLETON = getattr(ast, "MatchSingleton", None)
_AST_MATCH_SEQUENCE = getattr(ast, "MatchSequence", None)
_AST_MATCH_OR = getattr(ast, "MatchOr", None)
_AST_MATCH_AS = getattr(ast, "MatchAs", None)


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
    platform_aliases = _collect_platform_aliases(module)
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line_number = getattr(node, "lineno", None)
            if line_number is None:
                continue
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
            continue

        if not isinstance(node, ast.stmt) or isinstance(node, (ast.ClassDef, ast.Module)):
            continue
        line_number = getattr(node, "lineno", None)
        if line_number is None:
            continue

        statement_lines = _statement_line_numbers(node)
        if statement_lines and all(line in allowed_exception_lines for line in statement_lines):
            continue

        boundary = boundary_resolver(line_number)
        evidence_ref = f"platform_leakage:{boundary}:{relative_name}:{line_number}"
        statement_source = _statement_source_segment(source_text, node)
        if _is_docstring_statement(node):
            continue
        if _statement_has_platform_specific_field(statement_source, node):
            findings.append(
                _finding(
                    code="platform_specific_field_leak",
                    message=f"platform-specific field leaked into shared layer at `{relative_name}:{line_number}`",
                    boundary=boundary,
                    evidence_ref=evidence_ref,
                )
            )
            continue

        if _statement_has_hardcoded_platform_branch(node, platform_aliases=platform_aliases):
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


def _statement_has_platform_specific_field(statement_source: str, node: ast.AST) -> bool:
    if _PLATFORM_FIELD_RE.search(statement_source) is not None:
        return True
    return any(_string_literal_has_platform_specific_fragment(literal) for literal in _string_literals(node))


def _statement_has_hardcoded_platform_branch(
    node: ast.stmt,
    *,
    platform_aliases: frozenset[str],
) -> bool:
    if isinstance(node, ast.If):
        return _expr_has_platform_literal_compare(node.test, platform_aliases=platform_aliases)
    if _AST_MATCH is not None and isinstance(node, _AST_MATCH):
        return _match_has_platform_literal_branch(node, platform_aliases=platform_aliases)
    return _expr_has_platform_literal_compare(node, platform_aliases=platform_aliases)


def _statement_has_single_platform_semantic(
    node: ast.stmt,
    statement_source: str,
    *,
    platform_aliases: frozenset[str],
) -> bool:
    if isinstance(node, ast.Assign):
        return _assignment_has_single_platform_semantic(
            node.targets,
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
        )
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return _assignment_has_single_platform_semantic(
            [node.target],
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
        )
    if isinstance(node, ast.AugAssign):
        return _assignment_has_single_platform_semantic(
            [node.target],
            node.value,
            statement_source,
            platform_aliases=platform_aliases,
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
) -> bool:
    if _expr_has_platform_literal_compare(value, platform_aliases=platform_aliases):
        return True

    if _expr_contains_platform_literal(value):
        return True

    if any(_expr_is_platformish(target, platform_aliases=platform_aliases) for target in targets) and _expr_contains_platform_literal(value):
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


def _statement_has_semantic_platform_literal(statement_source: str, value: ast.AST) -> bool:
    normalized_source = statement_source.lower().replace("_", " ")
    if _SEMANTIC_CONTEXT_RE.search(normalized_source) is None:
        return False
    return any(_is_common_platform_literal(literal) for literal in _string_literals(value))


def _match_has_platform_literal_branch(node: ast.AST, *, platform_aliases: frozenset[str]) -> bool:
    if not _expr_is_platformish(node.subject, platform_aliases=platform_aliases):
        return False
    return any(_pattern_contains_platform_literal(case.pattern) for case in node.cases)


def _pattern_contains_platform_literal(pattern: ast.AST) -> bool:
    if _AST_MATCH_VALUE is not None and isinstance(pattern, _AST_MATCH_VALUE):
        return _expr_contains_platform_literal(pattern.value)
    if _AST_MATCH_SINGLETON is not None and isinstance(pattern, _AST_MATCH_SINGLETON):
        return False
    if _AST_MATCH_SEQUENCE is not None and isinstance(pattern, _AST_MATCH_SEQUENCE):
        return any(_pattern_contains_platform_literal(item) for item in pattern.patterns)
    if _AST_MATCH_OR is not None and isinstance(pattern, _AST_MATCH_OR):
        return any(_pattern_contains_platform_literal(item) for item in pattern.patterns)
    if _AST_MATCH_AS is not None and isinstance(pattern, _AST_MATCH_AS):
        return pattern.pattern is not None and _pattern_contains_platform_literal(pattern.pattern)
    return False


def _expr_has_platform_literal_compare(node: ast.AST, *, platform_aliases: frozenset[str]) -> bool:
    if isinstance(node, ast.Compare):
        current = node.left
        for operator, comparator in zip(node.ops, node.comparators):
            if _compare_pair_has_platform_literal(
                current,
                comparator,
                operator,
                platform_aliases=platform_aliases,
            ):
                return True
            current = comparator
    return any(
        _expr_has_platform_literal_compare(child, platform_aliases=platform_aliases)
        for child in ast.iter_child_nodes(node)
    )


def _compare_pair_has_platform_literal(
    left: ast.AST,
    right: ast.AST,
    operator: ast.AST,
    *,
    platform_aliases: frozenset[str],
) -> bool:
    if isinstance(operator, (ast.Eq, ast.NotEq)):
        return (_expr_is_platformish(left, platform_aliases=platform_aliases) and _expr_contains_platform_literal(right)) or (
            _expr_is_platformish(right, platform_aliases=platform_aliases) and _expr_contains_platform_literal(left)
        )
    if isinstance(operator, (ast.In, ast.NotIn)):
        return (_expr_is_platformish(left, platform_aliases=platform_aliases) and _expr_contains_platform_literal(right)) or (
            _expr_is_platformish(right, platform_aliases=platform_aliases) and _expr_contains_platform_literal(left)
        )
    return False


def _expr_is_platformish(node: ast.AST, *, platform_aliases: frozenset[str]) -> bool:
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


def _expr_contains_string_literal(node: ast.AST) -> bool:
    return bool(_string_literals(node))


def _expr_contains_platform_literal(node: ast.AST) -> bool:
    return any(_is_common_platform_literal(literal) for literal in _string_literals(node))


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
