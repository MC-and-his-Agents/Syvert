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
- 状态：`inactive (historical implementation round; merged via PR #90 and issue #87 closed)`
- 历史收口事项：`CHORE-0087-fr-0004-core-input-admission`

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

- `FR-0004` formal spec 已由 PR `#82` 合入主干，`#87` 已由 PR `#90` 合入并关闭。
- 历史 worktree / 分支：`/Users/mc/code/worktrees/syvert/issue-87-fr-0004-core` / `issue-87-fr-0004-core`；对应实现回合已完成并退役。
- `#87` 的最终主干行为已收口为：Core 显式接收 `InputTarget` 与 `CollectionPolicy`，完成最小结构校验，并保持平台特定字段不提升到 Core。
- guardian 多轮阻断已全部在 PR `#90` 中收口；最近一次行为 checkpoint `3f8444d342298193c63518725edcb74ecdff1418` 仅保留为历史追溯锚点，不再承载 active 审查语义。

## 下一步动作

- 无 active 动作。
- `#87` 的主干实现、测试与 closeout 证据已由 `#68` implementation 聚合 closeout 继续消费；本文件仅保留为历史实现记录。

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
- 已核对：当前 `FR-0004` formal spec 已合入主干，`#87` 已由 PR `#90` 合入并关闭
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_executor tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在最近一次行为 checkpoint `3f8444d342298193c63518725edcb74ecdff1418` 上执行，`Ran 120 tests in 4.289s`，`OK`
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
- guardian 三轮审查：`REQUEST_CHANGES`
  - 阻断项：native `CoreTaskRequest` 在 fail-closed 前先触发了 adapter admission，越过了 `#87` 的边界
  - 收口结果：native shared-input 现在在 adapter lookup / shared-axis admission 前直接 fail-close；legacy URL 路径继续承担本回合允许的最小可执行语义
- 已完成最终收口：PR `#90` merged，Issue `#87` closed

## 未决风险

- 若 Core 输入模型在本回合提前混入平台派生字段，会直接违背 `FR-0004` 的 Core / Adapter 边界。
- 若在本回合把 `content_detail_by_url -> content_detail` 投影一起落地，会与 `#89` 的责任边界串线。
- 当前实现对非 `url` 的合法 `target_type` 采取“结构上可受理、执行时在 legacy 投影前 fail-closed”的过渡策略；该缺口需由 `#89` 的正式 adapter-facing 契约承接完成收口。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对运行时代码、测试、release/sprint 索引与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `3f8444d342298193c63518725edcb74ecdff1418`
