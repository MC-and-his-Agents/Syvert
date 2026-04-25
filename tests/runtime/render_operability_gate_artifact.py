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
from syvert.version_gate import (
    build_harness_source_report,
    orchestrate_version_gate,
    validate_platform_leakage_source_report,
    validate_real_adapter_regression_source_report,
)
from tests.runtime.test_version_gate import DEFAULT_REQUIRED_HARNESS_SAMPLE_IDS, VersionGateTests


DEFAULT_OUTPUT = Path("docs/exec-plans/artifacts/CHORE-0158-operability-gate-result.json")
SOURCE_EVIDENCE = Path("docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the FR-0019 v0.6 operability gate artifact.")
    parser.add_argument("--execution-revision", default="")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    revision = args.execution_revision.strip() or current_head()
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
    upstream_results = run_upstream_verifications() if run_upstream else default_upstream_results(revision)
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
    harness_report = build_harness_source_report(
        VersionGateTests.valid_harness_results(),
        required_sample_ids=DEFAULT_REQUIRED_HARNESS_SAMPLE_IDS,
        version="v0.2.0",
    )
    regression_report = validate_real_adapter_regression_source_report(
        VersionGateTests.valid_real_adapter_regression_payload(),
        version="v0.2.0",
        reference_pair=["xhs", "douyin"],
    )
    leakage_report = validate_platform_leakage_source_report(
        VersionGateTests.valid_platform_leakage_payload(),
        version="v0.2.0",
    )
    version_gate_result = orchestrate_version_gate(
        version="v0.2.0",
        reference_pair=["xhs", "douyin"],
        harness_report=harness_report,
        real_adapter_regression_report=regression_report,
        platform_leakage_report=leakage_report,
        required_harness_sample_ids=DEFAULT_REQUIRED_HARNESS_SAMPLE_IDS,
    )
    return {
        "baseline_gate_ref": f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
        "execution_revision": revision,
        "release": "v0.6.0",
        "verdict": version_gate_result["verdict"],
        "safe_to_release": version_gate_result["safe_to_release"],
        "evidence_refs": [
            f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
            f"tests:{revision}:tests.runtime.test_version_gate",
        ],
        "source_reports": version_gate_result["source_reports"],
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


def run_upstream_verifications() -> dict[str, Any]:
    modules = [
        "tests.runtime.test_execution_control",
        "tests.runtime.test_runtime_observability",
        "tests.runtime.test_http_api",
        "tests.runtime.test_cli_http_same_path",
        "tests.runtime.test_version_gate",
    ]
    subprocess.run([sys.executable, "-m", "unittest", *modules], check=True)
    revision = current_head()
    return {"evidence_refs": [f"tests:{revision}:{module}" for module in modules]}


if __name__ == "__main__":
    raise SystemExit(main())
