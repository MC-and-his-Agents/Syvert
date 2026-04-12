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
- 当前 `main` / 本 worktree 仍处于 `#87` 结束时的过渡态：
  - `CoreTaskRequest` 已可显式受理，但 native 路径在 adapter admission 前 fail-closed
  - legacy `TaskRequest(input.url)` 已统一归一到 shared input 并命中 `supported_targets` / `supported_collection_modes`
  - `project_to_adapter_request()` 仍投影回 legacy `TaskRequest(adapter_key, capability, input.url)` 形状
  - in-tree adapters 仍以 `request.input.url` 与 `supported_capabilities={content_detail_by_url}` 工作
- 当前独立 worktree：`/Users/mc/code/worktrees/syvert/issue-89-fr-0004-core-adapter`
- 当前执行分支：`issue-89-fr-0004-core-adapter`

## 下一步动作

- 引入最小 adapter-facing request 形状，并把 runtime admission / projection 顺序调整为“共享轴校验 -> capability family 投影 -> adapter 执行”。
- 同步参考 adapter、fixtures 与回归测试到新请求契约。
- 通过实现门禁后打开 implementation PR，完成 guardian / merge / closeout。

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

## 未决风险

- 若 capability projection 与 adapter 支持声明顺序处理不当，可能把调用侧 operation 与 adapter-facing family 混为一层，导致 admission 语义漂移。
- 若直接把 legacy `TaskRequest` 升格为 adapter-facing request，容易把 `adapter_key` Core 路由语义继续带入 adapter contract。
- 直接改写 adapter 单测时需防止把 `#88` 的兼容证据与 `#89` 的契约承接混成一次 closeout。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 runtime、adapter、tests、release/sprint 索引与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `c4df7d26893f86771285e98314ec0df29b75921b`
