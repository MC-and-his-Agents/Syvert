# CHORE-0087-fr-0004-core-input-admission 执行计划

## 关联信息

- item_key：`CHORE-0087-fr-0004-core-input-admission`
- Issue：`#87`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0087-fr-0004-core-input-admission`

## 目标

- 为 `FR-0004` 的首个 implementation Work Item 落地 Core 共享输入模型接入点，使运行时能够显式接收 `InputTarget` 与 `CollectionPolicy`，并完成最小结构校验。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/cli.py`
  - `tests/runtime/test_models.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_cli.py`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
- 本次不纳入：
  - Core 到 Adapter 的投影与 admission 扩展
  - `FR-0002` legacy 兼容路径 closeout
  - adapter registry、错误模型、harness、version gate
  - 参考适配器内部平台解析逻辑

## 当前停点

- `FR-0004` formal spec 已由 PR `#82` 合入主干，但 `#87` 尚未建立 implementation 回合的 active `exec-plan`、代码实现与验证证据。
- 当前独立 worktree 已建立：`/Users/mc/code/worktrees/syvert/issue-87-fr-0004-core`。
- 当前回合从 `origin/main@366f0ac054483a93179eec8dbfac3b2da8a6abfb` 起步，后续仅围绕 Core 输入受理与共享模型接入推进。

## 下一步动作

- 在运行时引入 `InputTarget`、`CollectionPolicy` 与新的 Core 请求对象。
- 补齐最小结构校验与对应单元测试。
- 运行 implementation 相关验证、创建 PR，并完成 `#87` closeout。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 建立 `FR-0004` 共享输入模型的主干实现起点，使后续 `#89` 投影链路与 `#88` 兼容映射有稳定的 Core 承接面。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0004` implementation 子事项的第一步，负责把 formal spec 落到 Core 输入受理层。
- 阻塞：
  - 不得在当前回合引入 adapter-facing request 投影、legacy 映射 closeout 或任何平台特定字段。

## 已验证项

- `gh issue view 87 --repo MC-and-his-Agents/Syvert`
- `python3 scripts/create_worktree.py --issue 87 --class implementation`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 已核对：当前 `FR-0004` formal spec 已合入主干，而 `#87` 仍为 `OPEN`

## 未决风险

- 若 Core 输入模型在本回合提前混入平台派生字段，会直接违背 `FR-0004` 的 Core / Adapter 边界。
- 若在本回合把 `content_detail_by_url -> content_detail` 投影一起落地，会与 `#89` 的责任边界串线。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对运行时代码、测试、release/sprint 索引与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `366f0ac054483a93179eec8dbfac3b2da8a6abfb`
