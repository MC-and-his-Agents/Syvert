# GOV-0015 执行计划

## 关联信息

- item_key：`GOV-0015-item-context-gate`
- Issue：`#19`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理修补事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`#20`
- active 收口事项：`GOV-0015-item-context-gate`

## 目标

- 为 `open_pr` 和 `governance_status` 补齐事项上下文自动化闭环。

## 范围

- 本次纳入：`scripts/open_pr.py`、`scripts/governance_status.py`、PR 模板、治理入口文档、治理测试、当前 sprint / release 索引
- 本次不纳入：新增状态存储、重构既有 spec / release 模型、改造 guardian 审查协议

## 当前停点

- guardian 已连续指出历史兼容性、唯一 active 工件、PR body 对齐、状态面约束与执行现场一致性五类阻断项；当前已补齐对应修复并推送到最新受审 head，停在最终 guardian 审查与 merge gate 核对。

## 下一步动作

- 在 PR `#20` 上执行下一轮 guardian 审查并核对 checks / head SHA。
- 若 guardian 通过，使用受控入口完成 squash merge。
- 合并后按流程确认分支与 worktree 后续退役安排。

## 当前 checkpoint 推进的 release 目标

- 让 `v0.1.0` 治理栈中的事项上下文从文档约定升级为受控入口硬约束。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：收口项
- 阻塞：无外部阻塞；依赖当前 worktree 中完成脚本、模板和测试的同步更新

## 已验证项

- 已创建独立 Issue `#19`
- 已创建独立 worktree 与分支 `issue-19-governance-close-item-context-gate-for-open-pr-and-governance-status`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/spec_guard.py --all`
- `python3 -m unittest discover -s tests/governance -p 'test_*.py'`
- `python3 scripts/open_pr.py --class governance --issue 19 --item-key GOV-0015-item-context-gate --item-type GOV --release v0.1.0 --sprint 2026-S14 --title "治理: 补齐事项上下文自动化闭环" --dry-run`
- `python3 scripts/governance_status.py --issue 19 --format text`
- `python3 scripts/governance_status.py --issue 6 --format text`
- `python3 scripts/governance_status.py --pr 20 --format text`

## 未决风险

- 下一轮 guardian 审查仍可能发现未覆盖的治理边界或文档/实现漂移。
- 需确保重新推送后的 CI checks 与 guardian 审查使用同一 head SHA。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项引入的脚本、模板、索引与测试改动。

## 最近一次 checkpoint 对应的 head SHA

- `aa8a45c620e776523be4b0c4a4407bdc68f2e709`
