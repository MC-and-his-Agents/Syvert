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
    gate_input = build_gate_input_from_source_evidence(revision=revision)
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


def build_gate_input_from_source_evidence(*, revision: str, source_path: Path = SOURCE_EVIDENCE) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source_revision = str(source["execution_revision"])
    rewritten_source = rewrite_revision(source, old=source_revision, new=revision)
    actual_cases = {str(case["case_id"]): case for case in rewritten_source["cases"]}
    cases = build_mandatory_operability_cases()
    for case in cases:
        case_id = str(case["case_id"])
        evidence_case = actual_cases[case_id]
        case["actual_result_ref"] = evidence_case["actual_result_ref"]
        case["evidence_refs"] = evidence_case["evidence_refs"]
        case["actual_result"] = evidence_case["actual_result"]
        case["upstream_refs"] = evidence_case["upstream_refs"]
    return {
        "execution_revision": revision,
        "baseline_gate_ref": f"FR-0007:version_gate:v0.6.0:baseline:{revision}",
        "baseline_gate_result": rewritten_source["baseline_gate_result"],
        "cases": cases,
        "metrics_snapshot": rewritten_source["metrics_snapshot"],
        "evidence_refs": [f"FR-0007:version_gate:v0.6.0:baseline:{revision}"],
    }


def rewrite_revision(value: Any, *, old: str, new: str) -> Any:
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [rewrite_revision(item, old=old, new=new) for item in value]
    if isinstance(value, dict):
        return {str(key): rewrite_revision(item, old=old, new=new) for key, item in value.items()}
    return value


if __name__ == "__main__":
    raise SystemExit(main())
