# GOV-0262 spec mirror issue cleanup 执行计划

## 关联信息

- item_key：`GOV-0262-spec-mirror-issue-cleanup`
- Issue：`#262`
- item_type：`GOV`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：
- 关联 decision：`docs/decisions/ADR-GOV-0262-spec-mirror-issue-cleanup.md`
- 关联 PR：`#263`
- active 收口事项：`GOV-0262-spec-mirror-issue-cleanup`
- 状态：`active`

## 目标

- 清理 `spec_issue_sync.py` 自动维护的 spec mirror issue 对 GitHub open issue 调度真相的污染。
- 让后续 spec mirror 同步在创建或更新 issue 后保持 closed，避免它们被误判为可执行 Phase / FR / Work Item。

## 范围

- 本次纳入：
  - 修改 `scripts/spec_issue_sync.py` 的 GitHub issue upsert 行为，使 mirror issue 新建或更新后自动关闭。
  - 为该行为补充 governance 单测。
  - 关闭当前已存在的 open spec mirror issues，并记录 closeout comment。
- 本次不纳入：
  - 建立 `v0.7.0` Phase / FR / Work Item 正式交付树。
  - 改写 formal spec 正文或历史 release truth。
  - 改写 `spec_issue_sync.py` 对仓内 `docs/specs/**/spec.md` 的 canonical contract 来源判断。

## 当前停点

- `#260` 已收口，`v0.6.0` runtime baseline residual 已从主干清理。
- 当前 GitHub open issues 中仍有多个 `spec_issue_sync.py` 自动维护的 spec mirror issue；它们不是调度入口。
- `#262` 已建立为本治理清理 Work Item，绑定 `GOV-0262-spec-mirror-issue-cleanup`。

## 下一步动作

- 完成脚本与测试变更。
- 创建 PR，完成本地门禁、review、guardian 与合并。
- 合并后关闭现存 open spec mirror issues，并关闭 `#262`。

## 当前 checkpoint 推进的 release 目标

- 作为进入 `v0.7.0` 交付漏斗前的 GitHub 调度真相 hygiene，确保 open issue 列表只保留真实待处理事项。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.7.0 / 2026-S20` 启动前治理清理。
- 阻塞：若 spec mirror issue 继续保持 open，后续 `v0.7.0` Phase / FR / Work Item 识别会受到噪音干扰。

## 已验证项

- `python3.11 -m unittest tests.governance.test_spec_issue_sync tests.governance.test_cli_smoke.CliSmokeTests.test_help_commands_exit_zero`
  - 结果：通过，`Ran 4 tests`，`OK`。
- `python3.11 -m py_compile scripts/spec_issue_sync.py`
  - 结果：通过。
- `python3.11 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref issue-262-gov-spec-mirror-open-issue`
  - 结果：通过。
- `existing_issue_number("FR-0009-cli-task-query-and-core-path", "MC-and-his-Agents/Syvert")`
  - 结果：通过，返回已存在 mirror issue `#155`，证明脚本能复用 closed mirror 而不是重复创建。

## 未决风险

- `spec_issue_sync.py` 仍需能找到已关闭的 mirror issue，避免下次同步重复创建。
- 当前治理清理不能把 spec mirror issue 误描述为 canonical FR 或 Work Item；formal spec truth 仍只在仓内 `docs/specs/**/spec.md`。

## 回滚方式

- 使用独立 revert PR 撤销 `scripts/spec_issue_sync.py`、`tests/governance/test_spec_issue_sync.py`、`docs/decisions/ADR-GOV-0262-spec-mirror-issue-cleanup.md` 与本 exec-plan 的变更。
- 若需要恢复 mirror issue open 状态，必须另建治理事项说明其调度语义，不能隐式重新进入 open issue 列表。

## 最近一次 checkpoint 对应的 head SHA

- `44fad265e5bc51f47d16b828b3472856d4d7aa85`
- worktree 创建基线：`7640550afce821d637c7c7edfa0d79f68e21462b`
- 说明：`44fad265e5bc51f47d16b828b3472856d4d7aa85` 包含本轮 `spec_issue_sync.py` 行为变更、治理测试、ADR 与 exec-plan 首次完整版本；后续若仅修正 review 指出的 exec-plan 元数据，不改写脚本和测试语义 checkpoint。
