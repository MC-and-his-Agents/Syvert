# CHORE-0119-fr-0007-dual-reference-adapter-regression 执行计划

## 关联信息

- item_key：`CHORE-0119-fr-0007-dual-reference-adapter-regression`
- Issue：`#119`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：
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
- 基线真相源：`origin/main@eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479`
- 当前实现已新增双参考适配器回归执行器模块，固定执行 `xhs` / `douyin` 的 success + allowed failure 矩阵。
- 当前实现只通过 `syvert.runtime.execute_task` 观察公开 runtime envelope，不直读 adapter 私有 helper。
- 当前测试已补齐 payload 组装、fail-closed 行为，以及 source report 经 `orchestrate_version_gate()` 收口的端到端回归。

## 下一步动作

- 在当前 worktree 提交实现 commit，并把本 exec-plan checkpoint 绑定到该 runtime-affecting head。
- 由主线程创建受控 PR，更新 `#119` issue / PR body 当前事实，并在发 guardian 前核对 head / exec-plan / PR body / 验证记录一致性。
- 在 commit 之后补跑 `pr_scope_guard`，再进入 PR / guardian / merge gate。

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
  - 结果：`Ran 6 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：`Ran 85 tests`，`OK`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：`Ran 93 tests`，`OK`
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：当前 worktree 尚无提交，脚本返回 `未检测到需要校验的提交信息。`
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：当前 worktree 尚无提交，脚本返回 `当前分支相对基线没有变更，无法创建或校验 PR。`

## 未决风险

- 若回归执行器绕过 `execute_task()` 直接消费 adapter 私有返回值，会破坏共享 envelope 与错误分类边界。
- 若 success / allowed failure 矩阵缺任一 adapter 或缺任一 case，source report 将被 gate fail-closed。
- 若测试 wrapper 隐式补齐 `reference_pair`、surface 或 evidence refs，会复现 A 项已修过的入口洗白问题。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/real_adapter_regression.py`、相关测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`待当前代码提交后回填`
- 最近一次重跑目标测试的代码 head：`未提交工作树（基线 HEAD 为 eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479）`
- 当前 metadata-only head：`无`
