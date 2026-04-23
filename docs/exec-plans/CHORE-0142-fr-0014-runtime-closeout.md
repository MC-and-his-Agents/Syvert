# CHORE-0142-fr-0014-runtime-closeout 执行计划

## 关联信息

- item_key：`CHORE-0142-fr-0014-runtime-closeout`
- Issue：`#196`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0014-core-resource-capability-matching/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`待创建`
- 状态：`active`
- active 收口事项：`CHORE-0142-fr-0014-runtime-closeout`

## 目标

- 收口 `FR-0014` runtime implementation 回合中与 matcher truth、evidence baseline、declaration lookup 直接相关的执行证据。
- 确保 `#196` 在进入受控 PR 前具备可复验的 test truth：`FR-0014 matcher` 与 `FR-0015 approved capability baseline`、`#195 declaration lookup` 三者一致。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0142-fr-0014-runtime-closeout.md`
  - `tests/runtime/test_resource_capability_evidence.py`
- 本次不纳入：
  - CLI / contract harness 变更
  - formal spec 语义改写（`FR-0014` / `FR-0015`）
  - 非 `#196` 事项的执行计划与治理工件

## 当前停点

- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-196-fr-0014-core`
- 当前分支：`issue-196-fr-0014-core`
- 当前实现 checkpoint：`7fa2f9715f8e831fa6032b793287623f0d2f6e28`
- 当前状态：
  - `#196` 的 GitHub Work Item 元数据已存在（`item_key/item_type/release/sprint`），但此前缺少 active `exec-plan` 文件，导致 `open_pr` preflight 阻断。
  - `tests/runtime/test_resource_capability_evidence.py` 已覆盖 frozen evidence、runtime slots、matcher 对齐、以及 fail-closed 漂移路径。
  - 当前回合补充了“`#195` declaration lookup -> `FR-0014 matcher` -> `FR-0015 approved capability ids`”的直接联动断言，避免仅通过 helper baseline 间接验证。

## 下一步动作

- 基于当前 active `exec-plan` 继续补齐 `#196` implementation 变更与验证证据。
- 在当前分支形成可审查提交后，执行 `open_pr --class implementation --issue 196 ... --dry-run` 验证受控入口。
- 创建 implementation PR，进入 guardian review 与 merge gate。
- 合入后同步 `#196` / exec-plan / PR / guardian / main truth 一致性。

## 当前 checkpoint 推进的 release 目标

- 支撑 `v0.5.0`：确保 `FR-0014` 资源能力匹配实现可稳定消费 `FR-0015` 批准能力词汇，并与 `#195` 声明查找语义保持一致。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0014` implementation closeout Work Item，负责 matcher runtime 语义与证据消费链路收口。
- 阻塞：
  - 若 `#196` 的实现与 `#195` declaration carrier 或 `FR-0015` approved baseline 脱节，guardian 会持续给出同类阻断。
  - 若未维持 active `exec-plan` 与受控入口字段一致，`open_pr` 无法进入下一阶段。

## 已验证项

- `python3 -m unittest tests.runtime.test_resource_capability_evidence -v`
  - 结果：`Ran 25 tests`，`OK`
- `python3 -m unittest tests.runtime.test_resource_capability_matcher tests.runtime.test_adapter_resource_requirement_declaration tests.runtime.test_resource_capability_evidence -v`
  - 结果：`Ran 42 tests`，`OK`
- `python3 scripts/governance_status.py --issue 196 --format json`
  - 结果：当前分支/worktree 绑定到 `#196`，此前 `item_context` 为空（缺 active exec-plan）；本文件创建后可作为 `open_pr` 前置上下文载体。

## 未决风险

- 当前仓库存在并行未提交改动；若 `runtime/declaration` 实现继续变化，测试可能需再次同步断言细节。
- `FR-0015` evidence baseline 仍依赖 frozen pointer 与 formal research 对齐；上游符号或路径漂移会触发 fail-closed。
- 在 PR 收口阶段，仍需持续关注 guardian 是否重复同类阻断，避免只修单点症状。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项在 exec-plan 与 runtime evidence tests 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `7fa2f9715f8e831fa6032b793287623f0d2f6e28`
