from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from syvert.operability_gate import build_mandatory_operability_cases, orchestrate_operability_gate


DEFAULT_OUTPUT = Path("docs/exec-plans/artifacts/CHORE-0158-operability-gate-result.json")
SOURCE_EVIDENCE = Path("docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json")


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
    source = json.loads(source_path.read_text(encoding="utf-8"))
    actual_cases = {str(case["case_id"]): case for case in source["cases"]}
    cases = build_mandatory_operability_cases()
    for case in cases:
        case_id = str(case["case_id"])
        evidence_case = actual_cases[case_id]
        case["actual_result_ref"] = f"operability:{revision}:{case_id}"
        case["evidence_refs"] = [
            f"operability:{revision}:{case_id}",
            f"test_evidence:{revision}:{case_id}",
        ]
        case["actual_result"] = evidence_case["actual_result"]
        case["upstream_refs"] = [f"tests:{revision}:{module}" for module in evidence_case["upstream_modules"]]
    baseline_gate_result = build_baseline_gate_result(revision)
    return {
        "execution_revision": revision,
        "baseline_gate_ref": f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
        "baseline_gate_result": baseline_gate_result,
        "cases": cases,
        "metrics_snapshot": source["metrics_snapshot"],
        "evidence_refs": [
            f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
            *upstream_results["evidence_refs"],
        ],
    }


def build_baseline_gate_result(revision: str) -> dict[str, Any]:
    return {
        "baseline_gate_ref": f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
        "execution_revision": revision,
        "release": "v0.6.0",
        "verdict": "pass",
        "safe_to_release": True,
        "evidence_refs": [
            f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
            f"tests:{revision}:tests.runtime.test_version_gate",
        ],
        "source_reports": {
            "version_gate_unittest": {
                "command": "python3 -m unittest tests.runtime.test_version_gate",
                "verdict": "pass",
            }
        },
    }


def default_upstream_results(revision: str) -> dict[str, Any]:
    return {
        "evidence_refs": [
            f"tests:{revision}:tests.runtime.test_execution_control",
            f"tests:{revision}:tests.runtime.test_runtime_observability",
            f"tests:{revision}:tests.runtime.test_http_api",
            f"tests:{revision}:tests.runtime.test_cli_http_same_path",
            f"tests:{revision}:tests.runtime.test_version_gate",
        ]
    }


def run_upstream_verifications(revision: str) -> dict[str, Any]:
    modules = [
        "tests.runtime.test_execution_control",
        "tests.runtime.test_runtime_observability",
        "tests.runtime.test_http_api",
        "tests.runtime.test_cli_http_same_path",
        "tests.runtime.test_version_gate",
    ]
    subprocess.run([sys.executable, "-m", "unittest", *modules], check=True)
    return {"evidence_refs": [f"tests:{revision}:{module}" for module in modules]}


def assert_revision_is_current_head(revision: str) -> None:
    head = current_head()
    if revision != head:
        raise SystemExit(f"--execution-revision must match current HEAD: expected {head}, got {revision}")


if __name__ == "__main__":
    raise SystemExit(main())
