# CHORE-0120-fr-0007-platform-leakage-check 执行计划

## 关联信息

- item_key：`CHORE-0120-fr-0007-platform-leakage-check`
- Issue：`#120`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0007-release-gate-and-regression-checks/`
- 关联 PR：`#123`
- 状态：`active`
- active 收口事项：`CHORE-0120-fr-0007-platform-leakage-check`

## 目标

- 落地 `FR-0007` 平台泄漏检查器，并让结果可直接被 `validate_platform_leakage_source_report()` 与 `orchestrate_version_gate()` 消费。
- 固定扫描面为 `syvert/runtime.py`、`syvert/registry.py`、`syvert/version_gate.py` 三个共享层文件。
- 对平台名硬编码分支、平台专属字段泄漏、单平台共享语义分叉维持 fail-closed。

## 范围

- 本次纳入：
  - `syvert/platform_leakage.py`
  - `tests/runtime/test_platform_leakage.py`
  - `tests/runtime/test_version_gate.py`
  - 当前 active `exec-plan`
- 本次不纳入：
  - adapter 私有实现
  - browser bridge / research 文档
  - `FR-0007` formal spec 改写
  - release / sprint closeout 索引

## 当前停点

- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-120-fr-0007`
- 当前执行分支：`issue-120-fr-0007`
- 基线真相：`origin/main@eb5bbc3d0bf0dc5b91fe64a8a63aa24c34ba8479`
- 当前 runtime-affecting 实现 checkpoint：`f7de3de924745cce410f2fdad7de7b7021f90bbc`
- 当前实现约束：
  - 默认不改 `syvert/version_gate.py`
  - 公开入口先验形再验值，缺失即 fail-closed
  - 允许例外仅限 `normalized.platform`、统一 `error.details`、冻结 reference pair
- 当前代码停点：
  - 已新增 `syvert.platform_leakage`，固定扫描 `runtime.py` / `registry.py` / `version_gate.py`
  - 已补 `tests/runtime/test_platform_leakage.py`
  - 已在 `tests/runtime/test_version_gate.py` 增加真实 checker 输出进入 orchestrator 的接入回归
  - 受审 PR 已创建：`#123`
  - 当前 PR latest head / 当前 metadata-only head：`当前分支最新 head（metadata-only follow-up）`
  - 运行时语义仍锚定在实现 checkpoint `f7de3de924745cce410f2fdad7de7b7021f90bbc`
  - 下一步动作：在当前 head 上发起 guardian 审查，并通过 merge gate 收口；本 worktree 不执行 merge

## 实现要点

- 新增 `syvert.platform_leakage`，固定 `boundary_scope` 为六个共享边界，并把 caller 输入与 payload surface 绑定到同一份 boundary scope。
- 扫描结果直接输出为 `platform_leakage` source report payload，再由公开 validator 收口。
- 新增独立 runtime 测试，覆盖：
  - 真实共享层扫描 clean pass
  - caller boundary scope 缺项 / 越界 fail-closed
  - 三类 finding 的命中行为
  - adapter 私有实现与 research 文档不进入扫描面
- 在 `test_version_gate` 补一条真实 checker 输出进入 orchestrator 的接入回归。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 提供可复用的平台泄漏 gate 输入，使 `FR-0007` 的第三类固定 gate 能以 hermetic 方式进入版本级收口。

## 已验证项

- 已阅读：`syvert/version_gate.py`
- 已阅读：`syvert/runtime.py`
- 已阅读：`syvert/registry.py`
- 已阅读：`tests/runtime/test_version_gate.py`
- `python3 -m py_compile syvert/platform_leakage.py tests/runtime/test_platform_leakage.py tests/runtime/test_version_gate.py`
  - 结果：通过
- `python3 -m unittest tests.runtime.test_platform_leakage`
  - 结果：`Ran 8 tests`，`OK`
- `python3 -m unittest tests.runtime.test_version_gate`
  - 结果：`Ran 85 tests`，`OK`
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate tests.runtime.test_runtime tests.runtime.test_registry`
  - 结果：`Ran 138 tests`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：当前 metadata-only head 已复跑，通过。
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：当前 metadata-only head 已复跑，`PR scope` 校验通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：当前 metadata-only head 已复跑，`docs-guard` 通过。

## 未决风险

- 若扫描范围扩展到 adapter 私有实现、browser bridge 或 research 文档，会把允许的平台语义误判成共享层泄漏。
- 若把共享层中的 `xhs` / `douyin` 字面量一概视为 finding，会误伤 `normalized.platform`、统一 `error.details` 和冻结 reference pair。
- 若 caller `boundary_scope` 与 payload 自带 `boundary_scope` 不保持同一对象，版本 gate ingress 会出现 surface 洗白风险。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/platform_leakage.py`、相关测试与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`f7de3de924745cce410f2fdad7de7b7021f90bbc`
- 最近一次重跑目标测试的 head：`当前分支最新 head（metadata-only follow-up）`
- 最近一次门禁复跑的 head：`当前分支最新 head（metadata-only follow-up）`
- 当前 metadata-only head：`当前分支最新 head（metadata-only follow-up）`
