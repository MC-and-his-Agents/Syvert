# GOV-0015 执行计划

## 关联信息

- item_key：`GOV-0015-item-context-gate`
- Issue：`#19`
- item_type：`GOV`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（治理修补事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：待创建
- active 收口事项：`GOV-0015-item-context-gate`

## 目标

- 为 `open_pr` 和 `governance_status` 补齐事项上下文自动化闭环。

## 范围

- 本次纳入：`scripts/open_pr.py`、`scripts/governance_status.py`、PR 模板、治理入口文档、治理测试、当前 sprint / release 索引
- 本次不纳入：新增状态存储、重构既有 spec / release 模型、改造 guardian 审查协议

## 当前停点

- `open_pr` 已要求完整事项上下文并校验 active `exec-plan`，`governance_status` 已输出 `item_context`，当前停在提交前的 checkpoint 收口。

## 下一步动作

- 提交当前治理修补改动并通过受控入口创建治理 PR。
- 在 PR 上执行 guardian 审查并核对 merge gate。
- 通过受控入口完成 squash merge。

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

## 未决风险

- 需要兼容历史 `exec-plan` 文件名与当前新增 `item_key` 命名规则，避免误伤已有治理流程。
- `governance_status` 新增 `item_context` 后需保持无 active `exec-plan` 场景下的兼容输出。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项引入的脚本、模板、索引与测试改动。

## 最近一次 checkpoint 对应的 head SHA

- `3c0e3470b67d7cca320059fd95e41b7f5b2f6d11`
