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
- 当前受审 runtime head：`230d845323109a1b9df9d42514a02bf0b1a8a3b1`
- 基线真相源：`origin/main@eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479`
- 当前 runtime-affecting 实现 checkpoint：`230d845323109a1b9df9d42514a02bf0b1a8a3b1`
- 当前 metadata-only follow-up 只允许同步 artifact / exec-plan / PR / issue 当前事实，不得改写 `230d845323109a1b9df9d42514a02bf0b1a8a3b1` 这条 runtime 真相。
- 当前实现已新增双参考适配器回归执行器模块，固定执行 `xhs` / `douyin` 的 success + allowed failure 矩阵。
- 当前实现只通过 `syvert.runtime.execute_task` 观察公开 runtime envelope，不直读 adapter 私有 helper。
- 当前实现已在公开入口对冻结 `xhs` / `douyin` reference adapter 执行 fail-closed 身份 / 来源校验，仅接受真实 `XhsAdapter` / `DouyinAdapter` 及其允许的 hermetic 实例。
- 当前实现已把 reference adapter 公开 surface 的冻结基线改为独立版本常量，不再读取当前类属性，避免适配器类定义漂移被误当成合法新基线。
- 当前实现已把 douyin allowed-failure case 收紧为 hermetic 失败路径：默认 browser page-state recovery 绑定会被 fail-closed 拒绝，测试与 gate 接入都显式注入确定性失败的 `page_state_transport`。
- 当前实现已把默认 browser recovery 的包装 / 转发调用一起纳入 fail-closed 检查，避免 wrapper 逃逸默认 `page_state_transport` 绑定限制。
- 当前实现已把默认 browser recovery 的别名转发调用一起纳入递归检测，避免 `alias = default_page_state_transport; lambda **kwargs: alias(**kwargs)` 这类绑定绕过 hermetic 约束。
- 当前实现已把逐 case `evidence_ref` 纳入真实回归公开 contract，并要求顶层 `evidence_refs` 与冻结矩阵的逐 case 证据绑定完全一致，缺失或错绑均 fail-closed。
- 当前实现已把冻结矩阵本身纳入 validator contract：每个 adapter 的 `case_id` / `expected_outcome` / `evidence_ref` 都必须与 `v0.2.0` 冻结矩阵完全一致，不能只满足粗粒度 coverage。
- 当前测试已补齐 payload 组装、fail-closed 行为，以及 source report 经 `orchestrate_version_gate()` 收口的端到端回归；本轮额外补了 shape-compatible spoofed adapter 冒充冻结 reference adapter 时的 fail-closed 回归。
- 本轮新增了真实 reference adapter 类属性漂移时必须 fail-closed 的回归测试。
- 本轮新增了 douyin 默认 browser recovery 绑定必须 fail-closed 的回归测试。
- 本轮新增了 douyin 包装 default browser recovery 绑定必须 fail-closed 的回归测试。
- 本轮新增了 douyin 别名转发 default browser recovery 绑定必须 fail-closed 的回归测试。
- 本轮新增了逐 case `evidence_ref` 缺失 / 错绑必须 fail-closed 的回归测试。
- 本轮新增了冻结矩阵 case identity 漂移必须 fail-closed 的回归测试。

## 下一步动作

- 在当前 PR / issue 当前事实中同步 `230d845323109a1b9df9d42514a02bf0b1a8a3b1` runtime checkpoint、artifact 收口与最新验证记录。
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
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：`Ran 99 tests`，`OK`
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：在 checkpoint `cfeb746bc6d99878dd1ab7220d2c220015937058` 上通过，`Ran 104 tests`，`OK`
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：在 checkpoint `56bc6d6500eebc15aba279d205c8854ece5efded` 上通过，`Ran 105 tests`，`OK`
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_version_gate`
  - 结果：在 checkpoint `230d845323109a1b9df9d42514a02bf0b1a8a3b1` 上通过，`Ran 107 tests`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：当前受审 head 复跑，通过。
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：当前受审 head 复跑，通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：当前受审 head 复跑，`PR scope` 校验通过。

## 未决风险

- 若回归执行器绕过 `execute_task()` 直接消费 adapter 私有返回值，会破坏共享 envelope 与错误分类边界。
- 若 success / allowed failure 矩阵缺任一 adapter 或缺任一 case，source report 将被 gate fail-closed。
- 若测试 wrapper 隐式补齐 `reference_pair`、surface 或 evidence refs，会复现 A 项已修过的入口洗白问题。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/real_adapter_regression.py`、相关测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`230d845323109a1b9df9d42514a02bf0b1a8a3b1`
- 当前受审 runtime head：`230d845323109a1b9df9d42514a02bf0b1a8a3b1`
