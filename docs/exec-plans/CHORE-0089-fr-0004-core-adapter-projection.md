# CHORE-0089-fr-0004-core-adapter-projection 执行计划

## 关联信息

- item_key：`CHORE-0089-fr-0004-core-adapter-projection`
- Issue：`#89`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0089-fr-0004-core-adapter-projection`

## 目标

- 在 `#87` 已合入的 Core 共享输入模型之上，打通 Core 到 adapter-facing contract 的正式投影链路，使 adapter request 显式承接 `target_type`、`target_value`、`collection_mode`，并把调用侧 operation `content_detail_by_url` 投影为 adapter-facing capability family `content_detail`。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/adapters/xhs.py`
  - `syvert/adapters/douyin.py`
  - `tests/runtime/test_models.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_executor.py`
  - `tests/runtime/adapter_fixtures.py`
  - 受影响的 adapter 单测
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
- 本次不纳入：
  - `FR-0002` 兼容路径的 closeout 证据收口
  - 错误模型、registry、harness、version gate
  - 平台特定签名、cookie、headers、fallback 或派生字段上浮到 Core

## 当前停点

- `FR-0004` formal spec 已由 PR `#82` 合入主干，`#87` 已由 PR `#90` 合入并关闭。
- 当前行为 checkpoint 已落盘到 `72858bfc4c14e7d763b47c1c37c784aee8d4dbf8`：
  - Runtime 新增 `AdapterTaskRequest(capability, target_type, target_value, collection_mode)`，由 Core 统一把 legacy `TaskRequest` 与 native `CoreTaskRequest` 投影到 adapter-facing request
  - 调用侧 operation `content_detail_by_url` 已在进入 adapter 前投影为 capability family `content_detail`
  - native `CoreTaskRequest` 不再在 `#87` 的 fail-closed 位置提前返回，而是与 legacy 路径一起命中 shared admission 与 adapter projection
  - unsupported `target_type` / `collection_mode` 现在统一在 shared admission 层失败
  - in-tree adapters 与 runtime fixtures 已把 `supported_capabilities` 同步到 `content_detail`，并承接显式 `target_type` / `target_value` / `collection_mode`
- 当前独立 worktree：`/Users/mc/code/worktrees/syvert/issue-89-fr-0004-core-adapter`
- 当前执行分支：`issue-89-fr-0004-core-adapter`

## 下一步动作

- 运行 `pr_scope_guard`、`open_pr --dry-run` 与 `commit_check`，补齐进入 PR 的受控门禁记录。
- 打开 implementation PR，完成 guardian / merge gate。
- 合并后关闭 `#89`，并把 release / sprint / closeout 工件回链到该 PR。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 收口 `FR-0004` 的第二个实现子事项，保证主干上的 Core 与 adapter 之间围绕同一组 shared input / adapter-facing contract 运行。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0004` implementation 第二步，负责 shared input 到 adapter-facing contract 的承接。
- 阻塞：
  - 不得在本回合吞并 `#88` 的 closeout 证据职责。
  - 不得把平台派生字段或 `FR-0005` 的错误/registry 语义混入 runtime Core 层。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0004-input-target-and-collection-policy/`
- `gh issue view 64 --repo MC-and-his-Agents/Syvert`
- `gh issue view 68 --repo MC-and-his-Agents/Syvert`
- `gh issue view 87 --repo MC-and-his-Agents/Syvert`
- `gh issue view 88 --repo MC-and-his-Agents/Syvert`
- `gh issue view 89 --repo MC-and-his-Agents/Syvert`
- 已核对：`#87` 已关闭，`#89/#88/#68/#64` 仍为 `OPEN`
- 已核对：`#64` 正文仍保留过期的 `formal spec：待创建`
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_runtime tests.runtime.test_executor tests.runtime.test_cli tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：`Ran 120 tests in 3.315s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过

## 未决风险

- 若 capability projection 与 adapter 支持声明顺序处理不当，可能把调用侧 operation 与 adapter-facing family 混为一层，导致 admission 语义漂移。
- 若直接把 legacy `TaskRequest` 升格为 adapter-facing request，容易把 `adapter_key` Core 路由语义继续带入 adapter contract。
- 直接改写 adapter 单测时需防止把 `#88` 的兼容证据与 `#89` 的契约承接混成一次 closeout。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 runtime、adapter、tests、release/sprint 索引与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `72858bfc4c14e7d763b47c1c37c784aee8d4dbf8`
