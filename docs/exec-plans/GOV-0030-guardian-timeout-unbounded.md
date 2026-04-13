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
- 保留显式超时配置能力，并对非法配置给出明确错误。
- 为该行为补齐最小治理测试，避免后续回归为隐式硬编码。

## 范围

- 本次纳入：`scripts/pr_guardian.py`、`tests/governance/test_pr_guardian.py`、`docs/decisions/ADR-GOV-0030-guardian-timeout-unbounded.md`、本事项 `exec-plan`
- 本次不纳入：guardian verdict schema 调整、merge gate 语义调整、review 内核迁移、其他治理自动化主题

## 当前停点

- 已在 `issue-112-governance-remove-default-300s-guardian-timeout-cap` worktree 中完成 `pr_guardian` 默认超时行为调整、测试补齐、门禁验证与 PR 创建；当前停在等待 GitHub checks 与 guardian 审查。

## 下一步动作

- 观察 PR `#113` 的 GitHub checks，确认当前 head 上的自动化门禁通过。
- 对 PR `#113` 执行 guardian 审查，确认默认无超时策略没有破坏现有 merge gate 语义。
- 如出现阻断，仅在本事项范围内修复并回写验证与风险记录。

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

## 未决风险

- 若把空字符串或非正整数错误地继续传给 `subprocess.run(timeout=...)`，会造成新的运行时异常或重新引入隐式默认值。
- 若测试只覆盖超时异常而不覆盖默认无超时路径，后续重构容易把 300 秒默认值带回。
- 若改动扩大到 merge gate 或 reviewer prompt 语义，会越出当前治理修复事项边界。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `scripts/pr_guardian.py`、`tests/governance/test_pr_guardian.py` 与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `2d6b513e2306b7c592016b31774d5b7edbb6ff3a`
