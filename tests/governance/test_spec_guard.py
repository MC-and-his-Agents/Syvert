from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.spec_guard import validate_changed_paths, validate_suite


GOOD_SPEC = """# FR-0001-example

## 背景

test

## 范围

test

## GWT 验收场景

- Given 条件
  When 执行
  Then 结果

## 异常与边界场景

- 边界

## 验收标准

- 标准
"""


GOOD_PLAN = """# Plan

## 实施目标

目标

## 分阶段拆分

拆分

## 实现约束

约束

## 测试与验证策略

验证

## TDD 范围

范围

## 并行 / 串行关系

关系

## 进入实现前条件

条件
"""


class SpecGuardTests(unittest.TestCase):
    def test_valid_suite_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fr_dir = Path(temp_dir) / "docs" / "specs" / "FR-0001-example"
            fr_dir.mkdir(parents=True)
            (fr_dir / "spec.md").write_text(GOOD_SPEC, encoding="utf-8")
            (fr_dir / "plan.md").write_text(GOOD_PLAN, encoding="utf-8")
            errors = validate_suite(fr_dir)
        self.assertEqual(errors, [])

    def test_mixing_spec_and_implementation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            fr_dir = repo / "docs" / "specs" / "FR-0001-example"
            fr_dir.mkdir(parents=True)
            (fr_dir / "spec.md").write_text(GOOD_SPEC, encoding="utf-8")
            (fr_dir / "plan.md").write_text(GOOD_PLAN, encoding="utf-8")
            errors = validate_changed_paths(
                repo,
                [
                    "docs/specs/FR-0001-example/spec.md",
                    "src/core/runtime.py",
                ],
            )
        self.assertTrue(any("不得与实现代码混在同一 PR" in error for error in errors))

    def test_rejects_touched_legacy_todo_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            fr_dir = repo / "docs" / "specs" / "FR-0001-example"
            fr_dir.mkdir(parents=True)
            (fr_dir / "spec.md").write_text(GOOD_SPEC, encoding="utf-8")
            (fr_dir / "plan.md").write_text(GOOD_PLAN, encoding="utf-8")
            (fr_dir / "TODO.md").write_text("# TODO\n", encoding="utf-8")
            errors = validate_changed_paths(repo, ["docs/specs/FR-0001-example/TODO.md"])
        self.assertTrue(any("退出正式治理流" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
