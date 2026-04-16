# CHORE-0119-fr-0007-dual-reference-adapter-regression 执行计划

## 关联信息

- item_key：`CHORE-0119-fr-0007-dual-reference-adapter-regression`
- Issue：`#119`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：`#124`
- 状态：`active`
- active 收口事项：`CHORE-0119-fr-0007-dual-reference-adapter-regression`

## 目标

- 在 `FR-0007` 范围内落地双参考适配器回归执行器。
- 固定覆盖 `xhs` 与 `douyin` 两个参考适配器，并冻结 `v0.2.0` 的最小回归矩阵。
- 产出可被 `validate_real_adapter_regression_source_report()` 与 `orchestrate_version_gate()` 直接消费的 source report。

## 范围

- 本次纳入：
  - `syvert/real_adapter_regression.py`
  - `tests/runtime/test_real_adapter_regression.py`
  - `tests/runtime/test_version_gate.py`
  - 当前 active exec-plan
- 本次不纳入：
  - `syvert/version_gate.py` 结果模型重定义
  - 平台泄漏检查器本体
  - release / sprint 索引更新
  - `FR-0004/0005/0006` contract 重定义

## 当前停点

- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-119-fr-0007`
- 当前执行分支：`issue-119-fr-0007`
- 当前受审 PR：`#124`
- 基线真相源：`origin/main@eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479`
- 当前 runtime-affecting 实现 checkpoint：`22617661a06dcfa9584a1e068c2cd604aab7c8bf`
- 当前 metadata-only follow-up：当前分支最新 head（仅回填 guardian P1 修复后的 exec-plan checkpoint / 验证追踪，不改运行时语义）。
- 当前实现已新增双参考适配器回归执行器模块，固定执行 `xhs` / `douyin` 的 success + allowed failure 矩阵。
- 当前实现只通过 `syvert.runtime.execute_task` 观察公开 runtime envelope，不直读 adapter 私有 helper。
- 当前实现已在公开入口对冻结 `xhs` / `douyin` reference adapter 执行 fail-closed 身份 / 来源校验，仅接受真实 `XhsAdapter` / `DouyinAdapter` 及其允许的 hermetic 实例。
- 当前测试已补齐 payload 组装、fail-closed 行为，以及 source report 经 `orchestrate_version_gate()` 收口的端到端回归；本轮额外补了 shape-compatible spoofed adapter 冒充冻结 reference adapter 时的 fail-closed 回归。

## 下一步动作

- 在当前 metadata-only head 上同步 PR body / issue body 当前事实，并明确 `22617661a06dcfa9584a1e068c2cd604aab7c8bf` runtime checkpoint 与当前受审 head 的对应关系。
- 重新发起 guardian 审查；若审查通过，再进入 merge gate。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 落地 `FR-0007` 的第二个 implementation 子事项，使版本 gate 能消费真实双参考适配器回归结论。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0007` implementation Work Item `#119`
- 阻塞：
  - 不得信任上游自报 pass；source report 必须由 runtime envelope 真实观测构造
  - 不得把 fake/stub adapter 冒充真实参考适配器
  - 不得扩展到平台泄漏检查或 parent closeout

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- `python3 -m py_compile syvert/real_adapter_regression.py tests/runtime/test_real_adapter_regression.py tests/runtime/test_version_gate.py`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_real_adapter_regression`
  - 结果：`Ran 9 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：`Ran 85 tests`，`OK`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：`Ran 93 tests`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate tests.runtime.test_runtime tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：`Ran 187 tests`，`OK`
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：当前 metadata-only head 已复跑，通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：当前 metadata-only head 已复跑，`PR scope` 校验通过。
- `python3 -m unittest tests.runtime.test_real_adapter_regression`
  - 结果：`Ran 11 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：`Ran 86 tests`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：当前 metadata-only head 复跑，通过。
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：当前 metadata-only head 复跑，通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：当前 metadata-only head 复跑，`PR scope` 校验通过。

## 未决风险

- 若回归执行器绕过 `execute_task()` 直接消费 adapter 私有返回值，会破坏共享 envelope 与错误分类边界。
- 若 success / allowed failure 矩阵缺任一 adapter 或缺任一 case，source report 将被 gate fail-closed。
- 若测试 wrapper 隐式补齐 `reference_pair`、surface 或 evidence refs，会复现 A 项已修过的入口洗白问题。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/real_adapter_regression.py`、相关测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`22617661a06dcfa9584a1e068c2cd604aab7c8bf`
- 当前 metadata-only head：`当前分支最新 head（仅回填 guardian P1 修复后的 exec-plan checkpoint / 验证追踪，不改运行时语义）`
