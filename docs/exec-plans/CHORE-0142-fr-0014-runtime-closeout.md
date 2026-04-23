# CHORE-0142-fr-0014-runtime-closeout 执行计划

## 关联信息

- item_key：`CHORE-0142-fr-0014-runtime-closeout`
- Issue：`#196`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0014-core-resource-capability-matching/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`#214`
- 状态：`active`
- active 收口事项：`CHORE-0142-fr-0014-runtime-closeout`

## 目标

- 收口 `FR-0014` runtime implementation 回合，确保 Core 只基于 `#195` 已冻结的声明 carrier 与当前 runtime 能力集合执行纯粹的 `matched / unmatched` 判断。
- 把 `#196` 的执行真相统一沉淀到单一 active `exec-plan`，使 matcher truth、error taxonomy、测试证据、PR head 与后续 guardian / merge gate 可以对齐到同一上下文。

## 范围

- 本次纳入：
  - `syvert/registry.py`
  - `syvert/runtime.py`
  - `docs/exec-plans/CHORE-0142-fr-0014-runtime-closeout.md`
  - `tests/runtime/test_resource_capability_matcher.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_task_record.py`
  - `tests/runtime/test_task_record_store.py`
  - `tests/runtime/test_cli.py`
  - `tests/runtime/test_resource_capability_evidence.py`
  - `tests/runtime/test_xhs_adapter.py`
  - `tests/runtime/test_douyin_adapter.py`
  - `tests/runtime/test_real_adapter_regression.py`
  - 与 runtime-reaching matcher 回归直接相关的 test fixture / contract harness 文件
- 本次不纳入：
  - `FR-0013` / `FR-0014` / `FR-0015` formal spec 语义改写
  - acquire contract 改写或 `requested_slots` 真相迁移
  - provider 选择、排序、偏好、fallback 语义
  - 非 `#196` 事项的治理工件

## 当前停点

- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-196-fr-0014-core`
- 当前分支：`issue-196-fr-0014-core`
- 当前实现 checkpoint：`5f9d5d821882490071ec624979840d75c36311a5`
- 当前状态：
  - `syvert/runtime.py` 已新增 canonical matcher surface：`ResourceCapabilityMatcherInput`、`ResourceCapabilityMatchResult`、`match_resource_capabilities(...)`、`resolve_runtime_available_resource_capabilities(...)`。
  - `execute_task_internal()` 已消费 `lookup_resource_requirement(adapter_key, capability_family)`，并在 acquire 前完成 matcher gate：缺声明、坏声明以及未批准 capability projection 收口为 `invalid_resource_requirement`，合法但不满足声明的情况收口为 `resource_unavailable`。
  - runtime-reaching stub / CLI / contract harness 夹具已统一迁移到可追溯的 `xhs` canonical declaration truth，避免继续依赖无效 `stub`/`fake:*` baseline。
  - `syvert/registry.py` 已补充 matcher 复用的 approved evidence refs 入口，使 pure matcher 可以消费 `FR-0015` 批准词汇与共享证据，同时不改变 production declaration materialization 的 current baseline。
  - matcher unit tests、runtime / task-record / CLI / evidence / dual-reference adapter / contract harness 回归已覆盖：required/unmatched、未批准 projection fail-closed、pure matcher `none` 语义，以及 runtime entrypoint 在当前 registry baseline 下对 `none` declaration 继续 fail-closed 的边界。
  - 当前 implementation PR 已创建为 `#214`，本文件用于绑定 `5f9d5d821882490071ec624979840d75c36311a5` 对应的 implementation checkpoint 与后续 review / merge gate 真相。

## 下一步动作

- 对 `#214` 运行 guardian review，并以当前 PR head 为准收口 verdict / `safe_to_merge`。
- 等待 GitHub checks 绑定到当前 PR head 全绿后，经 `merge_pr` 执行受控 squash merge。
- 合入后同步 `#196` / exec-plan / guardian / main truth 一致性。

## 当前 checkpoint 推进的 release 目标

- 支撑 `v0.5.0`：确保 `FR-0014` 资源能力匹配实现可稳定消费 `FR-0015` 批准能力词汇，并与 `#195` 声明查找语义保持一致。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0014` implementation closeout Work Item，负责 matcher runtime 语义与证据消费链路收口。
- 阻塞：
  - 若 `#196` 的实现与 `#195` declaration carrier 或 `FR-0015` approved baseline 脱节，guardian 会持续给出同类阻断。
  - 若未维持 active `exec-plan` 与受控入口字段一致，`open_pr` 无法进入下一阶段。

## 已验证项

- `python3 -m unittest tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_registry tests.runtime.test_resource_capability_matcher tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_task_record_store tests.runtime.test_cli tests.runtime.test_resource_capability_evidence tests.runtime.test_executor tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_real_adapter_regression tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_automation tests.runtime.test_contract_harness_validation_tool`
  - 结果：`Ran 288 tests in 5.837s`，`OK`
- `python3 -m unittest tests.runtime.test_resource_capability_matcher tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_task_record_store tests.runtime.test_cli tests.runtime.test_resource_capability_evidence tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter tests.runtime.test_real_adapter_regression`
  - 结果：当前受审实现已覆盖 matcher / runtime / 未批准 projection / adapter regression 路径；最新本地复跑 `Ran 250 tests in 6.493s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过（`PR class: implementation` / `变更类别: docs, implementation`）
- `python3 scripts/governance_gate.py --mode ci --base-sha \"$(git merge-base origin/main HEAD)\" --head-sha \"$(git rev-parse HEAD)\" --head-ref issue-196-fr-0014-core`
  - 结果：通过
- `python3 scripts/open_pr.py --class implementation --issue 196 --item-key CHORE-0142-fr-0014-runtime-closeout --item-type CHORE --release v0.5.0 --sprint 2026-S18 --title 'feat(runtime): 落地 FR-0014 Core 资源能力匹配' --base main --closing fixes --dry-run`
  - 结果：通过
- `python3 scripts/open_pr.py --class implementation --issue 196 --item-key CHORE-0142-fr-0014-runtime-closeout --item-type CHORE --release v0.5.0 --sprint 2026-S18 --title 'feat(runtime): 落地 FR-0014 Core 资源能力匹配' --base main --closing fixes`
  - 结果：已创建当前受审 implementation PR `#214 https://github.com/MC-and-his-Agents/Syvert/pull/214`

## 未决风险

- 当前仓库存在并行未提交改动；若 `runtime/declaration` 实现继续变化，测试可能需再次同步断言细节。
- `FR-0015` evidence baseline 仍依赖 frozen pointer 与 formal research 对齐；上游符号或路径漂移会触发 fail-closed。
- 在 PR 收口阶段，仍需持续关注 guardian 是否重复同类阻断，避免只修单点症状。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项在 exec-plan 与 runtime evidence tests 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `5f9d5d821882490071ec624979840d75c36311a5`
