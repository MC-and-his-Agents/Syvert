# GOV-0030 执行计划

## 关联信息

- item_key：`GOV-0030-guardian-timeout-unbounded`
- Issue：`#112`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S16`
- 关联 spec：无（治理脚本事项）
- 关联 decision：`docs/decisions/ADR-GOV-0030-guardian-timeout-unbounded.md`
- 关联 PR：`#113`
- active 收口事项：`GOV-0030-guardian-timeout-unbounded`

## 目标

- 移除 guardian 审查在未显式配置 `SYVERT_GUARDIAN_TIMEOUT_SECONDS` 时默认 300 秒超时的限制。
- 保留显式超时配置能力，并对 `0`、负数、非整数等非法配置给出明确错误。
- 为该行为补齐最小治理测试，避免后续回归为隐式硬编码。

## 范围

- 本次纳入：`scripts/pr_guardian.py`、`tests/governance/test_pr_guardian.py`、`docs/decisions/ADR-GOV-0030-guardian-timeout-unbounded.md`、本事项 `exec-plan`
- 本次不纳入：guardian verdict schema 调整、merge gate 语义调整、review 内核迁移、其他治理自动化主题

## 当前停点

- 最近一次实现 checkpoint 绑定到 head `ae12b60da3c1f1dfb6cffb3d05a78ba3294a76cb`，已覆盖默认无超时、显式正整数超时与非法配置报错的代码/测试收口。
- 当前 PR head 为 `df79c4075c722ffd27d6c88fbe06a8f55198c7ac`；该增量提交仅补充审查态 `exec-plan` 元数据，用于对齐当前停点与 guardian 输入，不构成新的实现 checkpoint。
- 当前停在等待 PR `#113` 的最新 GitHub checks 与 guardian 复核，确认审查工件与当前受审 head 描述一致。

## 下一步动作

- 等待 PR `#113` 当前 head `df79c4075c722ffd27d6c88fbe06a8f55198c7ac` 的 GitHub checks 全绿。
- 对 PR `#113` 当前 head 重新执行 guardian 审查，确认其绑定的 guardian state 与最近一次实现 checkpoint `ae12b60da3c1f1dfb6cffb3d05a78ba3294a76cb` 之间关系描述清晰且一致。
- guardian 通过后按受控入口推进 squash merge，并同步分支/worktree 退役。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 治理工具链移除 guardian 长时审查的默认硬性截断，降低审查闭环因默认 300 秒超时而中断的风险。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：guardian 治理脚本的小范围修复项，负责把超时策略从隐式默认上限改为显式配置。
- 阻塞：无外部阻塞；需确保改动不改变显式超时配置与现有错误提示语义边界。

## 已验证项

- `gh issue view 112 --repo MC-and-his-Agents/Syvert`
- `python3 scripts/create_worktree.py --issue 112 --class governance`
- 已创建 worktree：`/Users/mc/code/worktrees/syvert/issue-112-governance-remove-default-300s-guardian-timeout-cap`
- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/agent-loop.md`
- 已阅读：`docs/process/worktree-lifecycle.md`
- 已阅读：`docs/process/branch-retirement.md`
- 已阅读：`code_review.md`
- 已阅读：`scripts/pr_guardian.py`
- 已阅读：`tests/governance/test_pr_guardian.py`
- 已完成最小改动文件：`scripts/pr_guardian.py`
- 已完成最小改动文件：`tests/governance/test_pr_guardian.py`
- 已完成最小改动文件：`docs/decisions/ADR-GOV-0030-guardian-timeout-unbounded.md`
- 已完成最小改动文件：`docs/exec-plans/GOV-0030-guardian-timeout-unbounded.md`
- `python3 -m unittest tests.governance.test_pr_guardian`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/open_pr.py --class governance --issue 112 --item-key GOV-0030-guardian-timeout-unbounded --item-type GOV --release v0.2.0 --sprint 2026-S16 --title "fix(governance): 移除 guardian 默认 300 秒超时" --dry-run`
- `git push -u origin issue-112-governance-remove-default-300s-guardian-timeout-cap`
- `python3 scripts/open_pr.py --class governance --issue 112 --item-key GOV-0030-guardian-timeout-unbounded --item-type GOV --release v0.2.0 --sprint 2026-S16 --title "fix(governance): 移除 guardian 默认 300 秒超时"`
- 已创建 PR：`#113 https://github.com/MC-and-his-Agents/Syvert/pull/113`
- guardian 初次审查结论：`REQUEST_CHANGES`；阻断项为显式非法超时配置与测试契约不一致
- 已按 guardian 阻断收口：显式拒绝 `0` / 负数超时配置，并补齐正向透传断言
- `git push`
- guardian 二次审查结论：`REQUEST_CHANGES`；阻断项为 active `exec-plan` 错把 checkpoint head 写成当前受审 head
- 已按 guardian 阻断收口：区分最近一次实现 checkpoint `ae12b60da3c1f1dfb6cffb3d05a78ba3294a76cb` 与当前 PR head `df79c4075c722ffd27d6c88fbe06a8f55198c7ac`

## 未决风险

- 若把 `0`、负数或非整数错误地继续传给 `subprocess.run(timeout=...)`，会造成新的运行时异常，或把非法配置静默解释为“关闭超时”。
- 若测试只覆盖超时异常而不覆盖默认无超时路径，后续重构容易把 300 秒默认值带回。
- 若改动扩大到 merge gate 或 reviewer prompt 语义，会越出当前治理修复事项边界。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `scripts/pr_guardian.py`、`tests/governance/test_pr_guardian.py` 与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `ae12b60da3c1f1dfb6cffb3d05a78ba3294a76cb`
