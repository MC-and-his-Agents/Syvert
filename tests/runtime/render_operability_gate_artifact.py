from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from syvert.operability_gate import build_mandatory_operability_cases, orchestrate_operability_gate


DEFAULT_OUTPUT = Path("/tmp/CHORE-0158-operability-gate-result.json")
RUNTIME_EVIDENCE_OUTPUT = Path("/tmp/CHORE-0158-operability-runtime-evidence.json")
SOURCE_EVIDENCE = Path("docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json")
APPROVED_UPSTREAM_MODULES = frozenset(
    {
        "tests.runtime.test_execution_control",
        "tests.runtime.test_runtime_observability",
        "tests.runtime.test_http_api",
        "tests.runtime.test_cli_http_same_path",
        "tests.runtime.test_version_gate",
    }
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the FR-0019 v0.6 operability gate artifact.")
    parser.add_argument("--execution-revision", default="")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    revision = args.execution_revision.strip() or current_head()
    assert_revision_is_current_head(revision)
    gate_input = build_gate_input_from_source_evidence(revision=revision, run_upstream=True)
    result = orchestrate_operability_gate(**gate_input)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)
    print(f"verdict={result['verdict']} cases={len(result['cases'])} execution_revision={revision}")
    return 0 if result["verdict"] == "pass" else 1


def current_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def build_gate_input_from_source_evidence(
    *,
    revision: str,
    source_path: Path = SOURCE_EVIDENCE,
    run_upstream: bool = False,
) -> dict[str, Any]:
    if run_upstream:
        assert_revision_is_current_head(revision)
    upstream_results = run_upstream_verifications(revision) if run_upstream else default_upstream_results(revision)
    executed_modules = set(APPROVED_UPSTREAM_MODULES)
    try:
        source = materialize_revision(json.loads(source_path.read_text(encoding="utf-8")), revision=revision)
    except (OSError, JSONDecodeError) as exc:
        return fail_closed_gate_input(
            revision=revision,
            failures=[{"code": "unreadable_source_evidence", "field": str(source_path), "message": str(exc)}],
        )
    failures = validate_source_evidence(source)
    if failures:
        return fail_closed_gate_input(revision=revision, failures=failures)
    runtime_evidence = build_runtime_evidence(source, revision=revision)
    RUNTIME_EVIDENCE_OUTPUT.write_text(
        json.dumps(runtime_evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    actual_cases = {str(case["case_id"]): case for case in source["cases"]}
    runtime_cases = runtime_evidence["cases"]
    cases = build_mandatory_operability_cases()
    for case in cases:
        case_id = str(case["case_id"])
        evidence_case = actual_cases.get(case_id)
        runtime_case = runtime_cases.get(case_id, {})
        if not isinstance(evidence_case, dict):
            return fail_closed_gate_input(
                revision=revision,
                failures=[{"code": "missing_source_evidence_case", "field": case_id}],
            )
        case["actual_result_ref"] = f"local:{revision}:{RUNTIME_EVIDENCE_OUTPUT}:{case_id}:actual_result"
        case["evidence_refs"] = [f"local:{revision}:{RUNTIME_EVIDENCE_OUTPUT}:{case_id}:source_case"]
        case["actual_result"] = runtime_case.get("actual_result", {})
        upstream_modules = evidence_case.get("upstream_modules")
        if (
            not isinstance(upstream_modules, list)
            or not all(isinstance(module, str) and module for module in upstream_modules)
            or not set(upstream_modules) <= executed_modules
        ):
            return fail_closed_gate_input(
                revision=revision,
                failures=[{"code": "invalid_source_evidence_upstream_modules", "field": case_id}],
            )
        case["upstream_refs"] = [f"tests:{revision}:{module}" for module in upstream_modules]
    return {
        "execution_revision": revision,
        "baseline_gate_ref": f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
        "baseline_gate_result": source["baseline_gate_result"],
        "cases": cases,
        "metrics_snapshot": runtime_evidence["metrics_snapshot"],
        "policy_snapshot": runtime_evidence["policy_snapshot"],
        "evidence_refs": [
            f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
            *upstream_results["evidence_refs"],
        ],
    }


def build_runtime_evidence(source: dict[str, Any], *, revision: str) -> dict[str, Any]:
    cases = {}
    for source_case in source["cases"]:
        case_id = str(source_case["case_id"])
        cases[case_id] = {
            "case_id": case_id,
            "actual_result": source_case.get("actual_result", {}),
            "observed_by": sorted(source_case.get("upstream_modules", [])),
            "revision": revision,
        }
    return {
        "revision": revision,
        "policy_snapshot": source["policy_snapshot"],
        "metrics_snapshot": source["metrics_snapshot"],
        "cases": cases,
    }


def validate_source_evidence(source: Any) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    if not isinstance(source, dict):
        return [{"code": "invalid_source_evidence_root", "field": "source"}]
    mandatory_case_ids = {str(case["case_id"]) for case in build_mandatory_operability_cases()}
    for key in ("baseline_gate_result", "policy_snapshot", "metrics_snapshot", "cases"):
        if key not in source:
            failures.append({"code": "missing_source_evidence_field", "field": key})
    if "cases" in source and not isinstance(source["cases"], list):
        failures.append({"code": "invalid_source_evidence_cases", "field": "cases"})
    elif isinstance(source.get("cases"), list):
        observed_case_ids = set()
        for index, case in enumerate(source["cases"]):
            if not isinstance(case, dict):
                failures.append({"code": "invalid_source_evidence_case", "field": f"cases[{index}]"})
                continue
            case_id = case.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                failures.append({"code": "missing_source_evidence_case_id", "field": f"cases[{index}].case_id"})
                continue
            if case_id in observed_case_ids:
                failures.append({"code": "duplicate_source_evidence_case_id", "field": case_id})
            observed_case_ids.add(case_id)
            if case_id not in mandatory_case_ids:
                failures.append({"code": "unexpected_source_evidence_case", "field": case_id})
            if "actual_result" not in case:
                failures.append({"code": "missing_source_evidence_actual_result", "field": case_id})
            if "actual_result_ref" not in case:
                failures.append({"code": "missing_source_evidence_actual_result_ref", "field": case_id})
            if "evidence_refs" not in case:
                failures.append({"code": "missing_source_evidence_refs", "field": case_id})
            if "upstream_modules" not in case:
                failures.append({"code": "missing_source_evidence_upstream_modules", "field": case_id})
            elif not isinstance(case["upstream_modules"], list) or not set(case["upstream_modules"]) <= APPROVED_UPSTREAM_MODULES:
                failures.append({"code": "unapproved_source_evidence_upstream_module", "field": case_id})
        for case_id in sorted(mandatory_case_ids):
            if case_id not in observed_case_ids:
                failures.append({"code": "missing_source_evidence_case", "field": case_id})
    return failures


def fail_closed_gate_input(*, revision: str, failures: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "execution_revision": revision,
        "baseline_gate_ref": f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
        "baseline_gate_result": {
            "baseline_gate_ref": f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
            "execution_revision": revision,
            "release": "v0.6.0",
            "verdict": "fail",
            "safe_to_release": False,
            "evidence_refs": [f"local:{revision}:source-evidence-invalid"],
        },
        "cases": [],
        "metrics_snapshot": {},
        "policy_snapshot": {},
        "evidence_refs": [f"local:{revision}:source-evidence-invalid"],
    }


def default_upstream_results(revision: str) -> dict[str, Any]:
    return {"evidence_refs": [f"tests:{revision}:{module}" for module in sorted(APPROVED_UPSTREAM_MODULES)]}


def run_upstream_verifications(revision: str) -> dict[str, Any]:
    modules = sorted(APPROVED_UPSTREAM_MODULES)
    subprocess.run([sys.executable, "-m", "unittest", *modules], check=True)
    return {"evidence_refs": [f"tests:{revision}:{module}" for module in modules]}


def materialize_revision(value: Any, *, revision: str) -> Any:
    if isinstance(value, str):
        return value.replace("{revision}", revision)
    if isinstance(value, list):
        return [materialize_revision(item, revision=revision) for item in value]
    if isinstance(value, dict):
        return {str(key): materialize_revision(item, revision=revision) for key, item in value.items()}
    return value


def assert_revision_is_current_head(revision: str) -> None:
    head = current_head()
    if revision != head:
        raise SystemExit(f"--execution-revision must match current HEAD: expected {head}, got {revision}")


if __name__ == "__main__":
    raise SystemExit(main())
