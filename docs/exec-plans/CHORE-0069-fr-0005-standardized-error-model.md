# CHORE-0069-fr-0005-standardized-error-model 执行计划

## 关联信息

- item_key：`CHORE-0069-fr-0005-standardized-error-model`
- Issue：`#69`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- 关联 decision：
- 关联 PR：`#97`
- 状态：`inactive (historical implementation round; merged via PR #97 and issue #69 closed)`
- 历史收口事项：`CHORE-0069-fr-0005-standardized-error-model`

## 目标

- 在 `FR-0005` 范围内落地标准化错误模型，把 Core / Adapter 的失败路径统一映射到 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 四类运行时语义。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/cli.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_executor.py`
  - `tests/runtime/test_cli.py`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
- 本次不纳入：
  - adapter registry materialization / discovery / registration
  - fake adapter、harness、validator、version gate
  - `FR-0004` 的输入建模语义改写
  - 平台适配器内部平台逻辑

## 当前停点

- `FR-0005` formal spec 已由 PR `#78` 合入主干，`#69` 已由 PR `#97` 合入并关闭。
- 历史 worktree / 分支：`/Users/mc/code/worktrees/syvert/issue-69-task` / `issue-69-task`；对应实现回合已完成并退役，不再承担 active 审查语义。
- 当前主干已统一 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 四类错误语义；本文件仅保留为历史实现记录。

## 下一步动作

- 无 active 动作。
- `#69` 的主干实现与 closeout 证据由 `docs/exec-plans/CHORE-0099-fr-0005-parent-closeout.md` 继续消费；本文件仅保留为历史实现记录。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 把共享错误分类从“能跑即可”推进到“契约可验证”，为后续 `#70` registry contract 与 `FR-0006/#0007` 的上层复用提供稳定失败语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0005` 的第一个 implementation Work Item，负责先把错误模型从 formal spec 落到主干运行时。
- 阻塞：
  - 不得把 adapter registry、harness、gate、fake adapter 或额外 FR 范围并入当前回合。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- `gh issue view 69 --repo MC-and-his-Agents/Syvert`
- `python3 scripts/create_worktree.py --issue 69 --class implementation`
  - 结果：已创建 worktree `/Users/mc/code/worktrees/syvert/issue-69-task`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_executor`
  - 结果：`Ran 48 tests in 1.726s`，`OK`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_executor`
  - 结果：在修正真实 adapter pre-platform 输入分类后重跑，`Ran 50 tests in 1.729s`，`OK`
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_executor tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter`
  - 结果：在引入 `PlatformAdapterError(category=\"invalid_input\")` 显式 contract 后重跑，`Ran 106 tests in 3.291s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：已校验 1 条提交信息，全部通过
- `python3 scripts/open_pr.py --class implementation --issue 69 --item-key CHORE-0069-fr-0005-standardized-error-model --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'feat(runtime): 落地 FR-0005 标准化错误模型' --closing fixes --dry-run`
  - 结果：通过
- 已创建当前受审 PR：`#97 https://github.com/MC-and-his-Agents/Syvert/pull/97`
- GitHub checks：
  - `Validate Commit Messages`：通过
  - `Validate Docs And Guard Scripts`：通过
  - `Validate Governance Tooling`：通过
  - `Validate Spec Review Boundaries`：通过
- guardian 首轮审查：`REQUEST_CHANGES`
  - 阻断项：active exec-plan 仍停留在 pre-PR 状态，`关联 PR` 为空，且“下一步动作”仍写着创建 PR，导致仓内执行上下文与当前受审 PR `#97` 不一致
  - 收口动作：更新 active exec-plan，使其与当前 PR / head / merge gate 状态对齐
- guardian 次轮审查：`REQUEST_CHANGES`
  - 阻断项：真实 adapter 在 pre-platform 输入失败时抛出的 `invalid_xhs_url` / `invalid_douyin_url` 仍被 runtime 映射到 `platform`
  - 收口动作：runtime 新增 adapter pre-platform invalid-input 分类逻辑，并补充真实 xhs / douyin invalid URL 回归测试
- guardian 三轮审查：`REQUEST_CHANGES`
  - 阻断项：Core 仍依赖 error code 后缀启发式识别 adapter pre-platform invalid input，未形成显式 Core / Adapter contract
  - 收口动作：为 `PlatformAdapterError` 增加显式 `category` 字段，并在 xhs / douyin 的 pre-platform request/url 校验路径上标记 `invalid_input`；同时补充一条不依赖 `*_request` / `*_url` 命名的回归测试

## 未决风险

- 若把 adapter target / collection admission 的失败误判为 `unsupported`，会模糊 `invalid_input` 与 “adapter 前置输入约束不满足” 的 spec 边界。
- 若在本回合顺手引入 registry 结构，会与 `#70` 的职责切分串线。
- 若 CLI 参数错误仍保留为 `runtime_contract`，则主干 CLI 与 formal spec 的 `invalid_input` 边界不一致。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 runtime、CLI、tests、release/sprint 索引与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `491fe7e81c50b2f7d8cb4b51cbcab9cb1e7f72f8`
