# CHORE-0268 FR-0021 adapter provider port formal spec closeout 执行计划

## 关联信息

- item_key：`CHORE-0268-fr-0021-formal-spec-closeout`
- Issue：`#268`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：`docs/specs/FR-0021-adapter-provider-port-boundary/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0268-fr-0021-formal-spec-closeout`
- 状态：`active`

## 目标

- 为 `FR-0021` 建立正式规约套件，冻结 adapter-owned provider port 与 native provider 拆分边界。
- 明确 Core 只调用 Adapter，不引入 Core provider registry、provider selector 或跨 provider fallback。
- 为后续 `#269` runtime implementation、`#270` SDK/capability metadata、`#271` evidence 和 `#272` parent closeout 提供 governing artifact。

## 范围

- 本次纳入：
  - 新建 `docs/specs/FR-0021-adapter-provider-port-boundary/` formal spec 套件。
  - 覆盖 provider port 所有权、稳定性、调用边界、错误/结果约束、Core 不感知边界与双参考兼容要求。
  - 明确当前只覆盖小红书、抖音 `content_detail_by_url` approved slice。
- 本次不纳入：
  - provider port runtime 或 native provider 代码拆分。
  - SDK metadata / migration 文档实现。
  - 双参考 evidence closeout。
  - 关闭 `#265` 或 `#264`。

## 当前停点

- `#264` Phase 与 `#265` FR 已建立并保持 open。
- `#266` 规划 Work Item 已完成，`docs/decisions/ADR-CHORE-0266-v0-7-adapter-provider-port-planning.md` 已合入主干。
- 本事项消费 `#266` 的 planning ADR 作为上游决策背景；该 ADR 不作为 `#268` 自身的关联 decision 元数据。
- 当前 worktree 绑定 `#268`，基线为 `4fff4c8104332cafa3a36c3421372e9b7af6f882`。

## 下一步动作

- 完成 formal spec 套件。
- 运行 spec/docs/workflow/governance 门禁。
- 创建 PR 并通过 spec review / guardian / merge gate。
- 合入后在 `#268` 留 closeout comment，并让 `#269/#270` 可以消费该 spec。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.7.0` 的 adapter surface 稳定化：先冻结 provider port 边界，再进入 runtime 与 evidence。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S20` 中 `FR-0021` 的 formal spec closeout Work Item。
- 阻塞：`#269`、`#270`、`#271`、`#272` 都依赖本 spec 合入主干。

## 已验证项

- `python3.11 scripts/create_worktree.py --issue 268 --class spec`
  - 结果：通过，创建 worktree `issue-268-fr-0021-adapter-provider-port-formal-spec`。
- `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3.11 scripts/pr_guardian.py review 282 --post-review --json-output /tmp/syvert-pr-282-guardian.json`
  - 结果：REQUEST_CHANGES。guardian 指出 provider request/resource 边界不闭合、双参考兼容基线不够可执行。
  - 处理：已收紧 `Provider Execution Request`，禁止 native provider 接收 `AdapterExecutionContext` / Core `resource_bundle`；已补齐小红书、抖音 approved slice compatibility baseline。

## 未决风险

- formal spec 若把 provider port 建模为 Core-facing provider SDK，会越过 `FR-0021` 边界并阻塞后续实现。
- formal spec 若新增业务能力或外部 provider 接入，会与 `#265` 明确不在范围冲突。

## 回滚方式

- 使用独立 revert PR 撤销 `docs/specs/FR-0021-adapter-provider-port-boundary/` 与本 exec-plan 的增量。
- 若需要改变 `FR-0021` 范围，必须先更新 `#265` 并记录原因。

## 最近一次 checkpoint 对应的 head SHA

- `4fff4c8104332cafa3a36c3421372e9b7af6f882`
- worktree 创建基线：`4fff4c8104332cafa3a36c3421372e9b7af6f882`
- 说明：该 checkpoint 对应 `#268` formal spec worktree 创建基线；当前 PR head 与 guardian state / merge gate 绑定，不要求本字段追写每次 review metadata。
