# CHORE-0088-fr-0004-fr-0002-compat-closeout 执行计划

## 关联信息

- item_key：`CHORE-0088-fr-0004-fr-0002-compat-closeout`
- Issue：`#88`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 decision：
- 关联 PR：`#92`
- 状态：`inactive (historical implementation round; merged via PR #92 and issue #88 closed)`
- 历史收口事项：`CHORE-0088-fr-0004-fr-0002-compat-closeout`

## 目标

- 在 `#87` 与 `#89` 已合入的主干实现之上，完成 `FR-0002` legacy URL 入口到 `InputTarget / CollectionPolicy` 的兼容路径 closeout，补齐 legacy/native 不分叉的 admission 证据、反例证据与 release / sprint / GitHub 回链。

## 范围

- 本次纳入：
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_cli.py`（如需补兼容回归）
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan（兼作 closeout 证据入口）
- 本次不纳入：
  - 新的 shared input / adapter-facing contract 语义
  - 错误模型、registry、harness、version gate
  - 平台特定签名、cookie、headers、fallback 逻辑

## 当前停点

- `#87` 已完成 legacy `TaskRequest(adapter_key, capability, input.url)` 到 shared input 的基础归一。
- `#89` 已通过 PR `#91` 合入主干，完成 `content_detail_by_url -> content_detail` capability family 投影，以及 legacy/native 共用 `AdapterTaskRequest` 的执行链。
- `#88` 已由 PR `#92` 合入并关闭；最终主干行为 checkpoint 固定为 `10f5b5a5bfdcb1913ace9b5eb8c1985e90e44045`：
  - legacy URL 请求与 native `CoreTaskRequest(url + hybrid)` 命中同一 `AdapterTaskRequest(url + hybrid)` 投影，并返回等价结果
  - adapter 未声明 `hybrid` 时，legacy/native 命中同一 `collection_mode_not_supported` 失败
  - release / sprint 已登记 `#88` 的兼容证据入口，并可被 `#68 / #64` closeout 直接回链
- 历史 worktree / 分支：`/Users/mc/code/worktrees/syvert/issue-88-fr-0004-fr-0002` / `issue-88-fr-0004-fr-0002`；对应实现回合已完成并退役

## 下一步动作

- 无 active 动作。
- `#88` 的兼容证据、反例证据与 closeout 回链已由 `#68` implementation 聚合 closeout 继续消费；本文件仅保留为历史实现记录。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 收口 `FR-0004` 的第三个 implementation 子事项，使 `FR-0002` 旧入口仍可被主干实现和验证证据直接追溯。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0004` implementation 第三步，负责 legacy `FR-0002` 入口的兼容证据与反例收口。
- 阻塞：
  - 不得把 `#68` / `#64` 的聚合 closeout 提前混入本回合。
  - 不得借兼容证据之名扩写新的 shared input 语义。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 已核对：`#88` 已由 PR `#92` 合入并关闭，`#89` 已关闭，`#68/#64` 仍为 `OPEN`
- 已核对：当前 `#88` worktree 基于 `main@e2b6b53d9a73f22b8e2f36ba9c4069a79ae45a08`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_executor tests.runtime.test_models`
  - 结果：`Ran 69 tests in 1.779s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：已校验 2 条提交信息，全部通过
- `python3 scripts/open_pr.py --class implementation --issue 88 --item-key CHORE-0088-fr-0004-fr-0002-compat-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'test(runtime): 补齐 FR-0004 的 FR-0002 兼容证据' --closing fixes --dry-run`
  - 结果：通过
- 已创建当前受审 PR：`#92 https://github.com/MC-and-his-Agents/Syvert/pull/92`
- 已完成最终收口：PR `#92` merged，Issue `#88` closed

## 兼容 closeout 证据

- legacy success 证据：
  - `tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_maps_legacy_and_native_requests_to_same_adapter_projection`
  - 证明 `TaskRequest(adapter_key, capability, input.url)` 与 native `CoreTaskRequest(target_type=url, target_value=input.url, collection_mode=hybrid)` 命中同一 adapter-facing request，并返回等价结果
- admission 统一反例：
  - `tests.runtime.test_runtime.RuntimeExecutionTests.test_execute_task_rejects_legacy_and_native_requests_with_same_hybrid_admission_error`
  - 证明 adapter 未声明 `hybrid` 时，legacy/native 都返回同一 `collection_mode_not_supported`
- old entry 仍可用：
  - `tests.runtime.test_cli.CliTests.test_cli_module_path_can_load_adapter_source`
  - `tests.runtime.test_cli.CliTests.test_cli_module_path_can_load_shared_adapter_registry`
  - 证明 CLI 旧入口 `--adapter + --capability + --url` 仍能驱动当前主干实现路径

## 未决风险

- 若只补 success path 而不补反例证据，`#88` 的 closeout 仍无法证明 legacy/native admission 不分叉。
- 若在本回合再次改 runtime 共享语义，容易与已关闭的 `#87/#89` 责任边界串线。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项新增的兼容回归测试、索引与 closeout 工件。

## 最近一次 checkpoint 对应的 head SHA

- `10f5b5a5bfdcb1913ace9b5eb8c1985e90e44045`
