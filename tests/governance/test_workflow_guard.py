from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.workflow_guard import validate_repository


def valid_workflow_text() -> str:
    return """---
tracker:
  kind: github
  scope: current-repo
workspace:
  root: $SYVERT_WORKSPACE_ROOT
  naming: issue-{number}-{slug}
agent:
  max_turns: 20
codex:
  thread_sandbox: workspace-write
  approval_policy: never
---
## 任务输入来源
text

## Worktree / Bootstrap 规则
text

## Checkpoint / Resume / Compact 规则
text

## Stop Conditions
text

## 何时必须更新 exec-plan
text

## 何时允许进入 open_pr / merge_pr
text
"""


def write_required_process_docs(repo: Path) -> None:
    process = repo / "docs" / "process"
    process.mkdir(parents=True)
    (process / "agent-loop.md").write_text("# agent-loop\n", encoding="utf-8")
    (process / "worktree-lifecycle.md").write_text("# lifecycle\n", encoding="utf-8")


class WorkflowGuardTests(unittest.TestCase):
    def test_front_matter_missing_required_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_required_process_docs(repo)
            workflow = valid_workflow_text().replace("agent:\n  max_turns: 20\n", "")
            (repo / "WORKFLOW.md").write_text(workflow, encoding="utf-8")

            errors = validate_repository(repo)

        self.assertTrue(any("agent" in error for error in errors))

    def test_non_github_tracker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_required_process_docs(repo)
            workflow = valid_workflow_text().replace("kind: github", "kind: linear")
            (repo / "WORKFLOW.md").write_text(workflow, encoding="utf-8")

            errors = validate_repository(repo)

        self.assertTrue(any("tracker.kind" in error for error in errors))

    def test_missing_required_section_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_required_process_docs(repo)
            workflow = valid_workflow_text().replace("## Stop Conditions\ntext\n\n", "")
            (repo / "WORKFLOW.md").write_text(workflow, encoding="utf-8")

            errors = validate_repository(repo)

        self.assertTrue(any("Stop Conditions" in error for error in errors))

    def test_valid_workflow_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_required_process_docs(repo)
            (repo / "WORKFLOW.md").write_text(valid_workflow_text(), encoding="utf-8")

            errors = validate_repository(repo)

        self.assertEqual(errors, [])

    def test_legacy_exec_plan_todo_heading_no_longer_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_required_process_docs(repo)
            legacy = valid_workflow_text().replace("## 何时必须更新 exec-plan", "## 何时必须更新 exec-plan / TODO")
            (repo / "WORKFLOW.md").write_text(legacy, encoding="utf-8")

            errors = validate_repository(repo)

        self.assertTrue(any("何时必须更新" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
