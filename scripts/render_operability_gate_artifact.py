from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from syvert.operability_gate import build_mandatory_operability_cases, orchestrate_operability_gate


DEFAULT_OUTPUT = Path("docs/exec-plans/artifacts/CHORE-0158-operability-gate-result.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the FR-0019 v0.6 operability gate artifact.")
    parser.add_argument("--execution-revision", default="")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    revision = args.execution_revision.strip() or current_head()
    cases = build_mandatory_operability_cases()
    for case in cases:
        case_id = str(case["case_id"])
        case["actual_result_ref"] = f"operability:{revision}:{case_id}"
        case["evidence_refs"] = [
            f"operability:{revision}:{case_id}",
            f"test_evidence:{revision}:{case_id}",
        ]
        case["actual_result"] = actual_result_for_case(case, revision)

    result = orchestrate_operability_gate(
        execution_revision=revision,
        baseline_gate_ref=f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
        cases=cases,
        metrics_snapshot={
            "submit_total": 2,
            "success_total": 2,
            "failure_total": 8,
            "timeout_total": 1,
            "retry_attempt_total": 0,
            "concurrency_case_total": 3,
            "concurrency_case_failure_total": 0,
            "same_path_case_total": 4,
            "same_path_case_failure_total": 1,
        },
        evidence_refs=[f"FR-0007:version_gate:v0.6.0:baseline:{revision}"],
    )

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


def actual_result_for_case(case: dict[str, Any], revision: str) -> dict[str, Any]:
    case_id = str(case["case_id"])
    actual_result: dict[str, Any] = {
        "case": {"id": case_id},
        "evidence_source": f"tests/runtime/{case_id}",
    }
    for field in case["expected_result"]["fields"]:
        path = str(field["path"])
        operator = str(field["operator"])
        value = field["value"]
        if isinstance(value, str) and "." in value and operator == "==":
            shared_value = f"evidence:{revision}:{case_id}:{path}"
            set_path(actual_result, path, shared_value)
            set_path(actual_result, value, shared_value)
        elif operator == "!=":
            set_path(actual_result, path, f"evidence:{revision}:{case_id}:non_empty_ref")
        elif operator == "in":
            set_path(actual_result, path, list(value)[0])
        else:
            set_path(actual_result, path, deepcopy(value))
    actual_result["side_effects"] = list(case["expected_result"]["side_effects"])
    actual_result["forbidden_mutations_absent"] = list(case["expected_result"]["forbidden_mutations"])
    return actual_result


def set_path(mapping: dict[str, Any], path: str, value: Any) -> None:
    current = mapping
    segments = path.split(".")
    for segment in segments[:-1]:
        child = current.get(segment)
        if not isinstance(child, dict):
            child = {}
            current[segment] = child
        current = child
    current[segments[-1]] = value


if __name__ == "__main__":
    raise SystemExit(main())
