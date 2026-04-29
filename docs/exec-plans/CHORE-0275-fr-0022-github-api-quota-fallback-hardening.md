# CHORE-0275 FR-0022 GitHub API quota fallback hardening formal spec

## 关联信息

- item_key：`CHORE-0275-fr-0022-github-api-quota-fallback-hardening`
- Issue：`#275`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：`docs/specs/FR-0022-github-api-quota-fallback-hardening/`
- 关联 decision：
- 关联 PR：

## 目标

- 本次执行要交付的能力：
  - 为 `FR-0022` 建立 formal spec 套件，冻结 GitHub REST / GraphQL quota-aware 行为、当前进程缓存、非合并 fallback 与 merge gate hard-fail 边界。
  - 将 `#275` 明确收口为 spec-only Work Item，为 `#276` 实现与 `#277` parent closeout 提供可执行前提。

## 范围

- 本次纳入：
  - 新增 `docs/specs/FR-0022-github-api-quota-fallback-hardening/`。
  - 记录 `#273` / `#274` / `#275` / `#276` / `#277` 的执行关系。
  - 运行 spec guard 与必要 governance 边界校验。
- 本次不纳入：
  - 不修改 `scripts/**` 或 `tests/**`。
  - 不实现 integration live state cache、PR/checks 快照复用、spec issue sync 或 repo settings hardening。
  - 不关闭 `#274` 或 `#273`。

## 当前停点

- 已创建 `#276` implementation Work Item 与 `#277` parent closeout Work Item。
- 已将 `#275` GitHub body 收敛为 spec-only。
- 当前工作树正在落地 FR-0022 formal spec suite。

## 下一步动作

- 运行 spec guard 与 governance gate。
- 提交并打开 spec PR。
- 等待 spec review；通过并合入后，`#276` 才能开始实现。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.7.0` 下治理脚本 GitHub API quota / fallback hardening 的 formal spec 前置条件。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0022` formal spec closeout。
- 阻塞：阻塞 `#276` implementation Work Item 与 `#277` parent closeout Work Item。

## 已验证项

- 待运行：
  - `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`

## 未决风险

- spec review 可能要求把 implementation Work Item 进一步拆分；若发生，只更新 `#274` 子事项关系，不在 `#275` 中混入实现。
- 若 spec guard 要求额外 suite 文件，补齐后再进入 PR。

## 回滚方式

- 使用独立 revert PR 撤销 FR-0022 formal spec suite 与本 exec-plan。
- GitHub 事项若需回滚，使用 REST PATCH 恢复 `#275`、`#274` 关系文案，不影响当前主干代码。

## 最近一次 checkpoint 对应的 head SHA

- `950b4126fa3139ed03849e24a2c64758a0e95ce7`
- 当前为 formal spec 建立 checkpoint；后续 review metadata 不自动刷新该 SHA。
