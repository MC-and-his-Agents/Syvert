# CHORE-0087-fr-0004-core-input-admission 执行计划

## 关联信息

- item_key：`CHORE-0087-fr-0004-core-input-admission`
- Issue：`#87`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0004-input-target-and-collection-policy/`
- 关联 decision：
- 关联 PR：`#90`
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

- `FR-0004` formal spec 已由 PR `#82` 合入主干，`#87` 当前已完成 Core 共享输入模型接入、最小结构校验与对应测试补强。
- 当前独立 worktree 已建立：`/Users/mc/code/worktrees/syvert/issue-87-fr-0004-core`；实现分支 `issue-87-fr-0004-core` 已推送远端，并打开 implementation PR `#90`。
- 首轮 guardian 针对 PR `#90` / head `727cf564c58094b99d60d90bf739b39aaf368f6a` 给出 `REQUEST_CHANGES`：指出 `CollectionPolicy` 在 legacy adapter 投影前被静默丢失。
- 第二轮收口已把显式 `CoreTaskRequest` 的执行路径收紧为 fail-closed：`#87` 只负责 shared model 受理与校验，不提前开放 adapter admission / execution happy path。
- 第三轮实现收口已把 legacy `TaskRequest(input.url)` 路径纳入 shared-axis admission：adapter 现在必须显式声明 `supported_targets` 包含 `url` 且 `supported_collection_modes` 包含 `hybrid`，否则 legacy URL 流量在进入 adapter 前 fail-closed。
- 最近一次行为 checkpoint 固定为 `3ff22df48d7a3f710c4eba67cf37437dd7f145e1`；其后若只追加 PR / exec-plan 审查态元数据，不改写运行时行为。当前受审 head 以 PR `#90` 与 guardian state 绑定为准。

## 下一步动作

- 基于当前 head 重跑 guardian 审查与受控 merge。
- 合并后关闭 `#87`，并退役当前 branch / worktree。

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
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_executor tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在最近一次行为 checkpoint `3ff22df48d7a3f710c4eba67cf37437dd7f145e1` 上执行，`Ran 120 tests in 3.877s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/open_pr.py --class implementation --issue 87 --item-key CHORE-0087-fr-0004-core-input-admission --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'feat(runtime): 接入 FR-0004 Core 共享输入模型' --closing fixes --dry-run`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：已校验 1 条提交信息，全部通过
- `python3 -m unittest tests.runtime.test_douyin_browser_bridge.DouyinBrowserBridgeTests.test_extract_page_state_falls_back_to_authenticated_detail_request_when_page_state_misses_target`
  - 结果：在当前分支与 `main` 基线均因本地签名服务未启动而失败，不作为本回合阻断性回归结论
- 已创建当前受审 PR：`#90 https://github.com/MC-and-his-Agents/Syvert/pull/90`
- guardian 首轮审查：`REQUEST_CHANGES`
  - 阻断项：`CollectionPolicy` 在执行前被 legacy 投影静默丢弃
  - 收口结果：显式 shared-input 请求在进入 adapter 前 fail-closed，避免绕过 `#89` 才应落地的 shared-axis admission
- guardian 次轮审查：`REQUEST_CHANGES`
  - 阻断项：legacy URL 可执行路径仍绕过 shared-axis admission，且缺少对应回归测试
  - 收口结果：legacy `TaskRequest(input.url)` 现在也必须命中 `supported_targets=url` 与 `supported_collection_modes=hybrid` 检查；真实 adapter、test fixtures 与回归用例已同步补齐

## 未决风险

- 若 Core 输入模型在本回合提前混入平台派生字段，会直接违背 `FR-0004` 的 Core / Adapter 边界。
- 若在本回合把 `content_detail_by_url -> content_detail` 投影一起落地，会与 `#89` 的责任边界串线。
- 当前实现对非 `url` 的合法 `target_type` 采取“结构上可受理、执行时在 legacy 投影前 fail-closed”的过渡策略；该缺口需由 `#89` 的正式 adapter-facing 契约承接完成收口。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对运行时代码、测试、release/sprint 索引与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `3ff22df48d7a3f710c4eba67cf37437dd7f145e1`
