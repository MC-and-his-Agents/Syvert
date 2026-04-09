# CHORE-0042 执行计划

## 关联信息

- item_key：`CHORE-0042-dual-reference-adapters-validation-closeout`
- Issue：`#42`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`#52`
- active 收口事项：`CHORE-0042-dual-reference-adapters-validation-closeout`

## 目标

- 收口 `#42`“dual reference adapters on shared core path”的剩余状态同步工作。
- 为 release / sprint 聚合索引补齐 `#42` 的工件入口与关联关系。
- 把双适配器共享 Core 路径验证的最小 closeout 证据落入版本控制。

## 范围

- 本次纳入：`docs/releases/v0.1.0.md`、`docs/sprints/2026-S15.md`、本事项 `exec-plan`
- 本次不纳入：Core / Adapter 实现改动、formal spec 语义变更、额外平台扩展、真实平台能力扩面

## 当前停点

- `main@92a333309090a77ec7619ff70a66622977c03b96` 已包含 PR `#48` 与 PR `#51`，对应的小红书 / 抖音参考适配器实现都已合入主干。
- `docs/releases/v0.1.0.md`、`docs/sprints/2026-S15.md` 与本事项 `exec-plan` 已补齐 `#42` 的索引入口与事项上下文。
- 已完成本事项 worktree 创建：`/Users/claw/code/worktrees/syvert/issue-42-validation-dual-reference-adapters-on-shared-core-path`。
- 当前受审 PR 为 `#52`；当前受审 head 以 PR 最新提交与 guardian state 绑定为准，本工件只记录最近一次显式 checkpoint SHA。

## 下一步动作

- 等待 guardian 对 PR `#52` 的最新 head 给出可合并 verdict。
- 通过受控 `merge_pr` 完成 squash merge。
- 合并后核对 `Fixes #42` 已收口 GitHub Issue 状态。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 补齐“双参考适配器共享 Core 契约验证”这一 closing signal 的索引与状态一致性。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：双参考适配器验证 closeout 事项
- 阻塞：无实现侧阻塞；当前仅需完成文档同步、受控 PR 与 GitHub 状态收口。

## 已验证项

- `gh issue view 42 --repo MC-and-his-Agents/Syvert --json number,title,state,body,url`
- `gh issue view 47 --repo MC-and-his-Agents/Syvert --json number,title,state,url`
- `gh issue view 50 --repo MC-and-his-Agents/Syvert --json number,title,state,url`
- `gh pr view 48 --repo MC-and-his-Agents/Syvert --json number,state,mergedAt,mergeCommit,closingIssuesReferences,url`
- 结果：`state=MERGED`，`mergeCommit=6d7e2be24b9e37860939c5ad598e1e76e093e3af`
- `gh pr view 51 --repo MC-and-his-Agents/Syvert --json number,state,mergedAt,mergeCommit,closingIssuesReferences,url`
- 结果：`state=MERGED`，`mergeCommit=92a333309090a77ec7619ff70a66622977c03b96`
- `git rev-parse HEAD`
- 结果：当前收口分支受审 head 以 PR 最新提交与 guardian state 绑定为准；该绑定不在本工件内自举记录
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- 结果：`Ran 128 tests in 1.846s`，`OK`
- `python3 scripts/open_pr.py --class docs --issue 42 --item-key CHORE-0042-dual-reference-adapters-validation-closeout --item-type CHORE --release v0.1.0 --sprint 2026-S15 --title "docs: 收口双参考适配器验证状态" --dry-run`
- 结果：dry-run 通过，closing 语义为 `Fixes #42`
- 双适配器共享 Core 路径 closeout 证据入口：
  - `tests/runtime/test_xhs_adapter.py`
  - `tests/runtime/test_douyin_adapter.py`
  - `tests/runtime/test_cli.py`

## 未决风险

- 若继续保留 release / sprint 索引中的旧口径，仓内会持续表现为“适配器已合入但验证事项未收口”的失配状态。
- 若关闭 `#42` 时不补充 closeout 依据，后续回溯双适配器验证时仍需要重新拼接 PR、测试与文档证据。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `docs/releases/v0.1.0.md`、`docs/sprints/2026-S15.md` 与本 `exec-plan` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `33d12ef070e4aa45030df2713c532b1a92163412`
- 说明：后续增量仅用于补齐 guardian 阻断与 PR 绑定信息；当前受审 head 由 PR 最新提交与 guardian state 绑定，不单独在本工件内自举记录。
