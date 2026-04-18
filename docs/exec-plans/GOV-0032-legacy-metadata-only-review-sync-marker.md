# GOV-0032 执行计划

## 关联信息

- item_key：`GOV-0032-legacy-metadata-only-review-sync-marker`
- Issue：`#152`
- item_type：`GOV`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：无（治理脚本事项）
- 关联 decision：`docs/decisions/ADR-GOV-0032-legacy-metadata-only-review-sync-marker.md`
- 关联 PR：
- active 收口事项：`GOV-0032-legacy-metadata-only-review-sync-marker`

## 目标

- 为 guardian 的 legacy `metadata-only review sync` marker 兼容路径补一条专门回归。
- 锁定历史 closeout `exec-plan` 在未迁移到新 marker 前仍能被正确识别。
- 不改写 `#150` 已合入的 contract 边界，也不新增新的 metadata 例外。

## 范围

- 本次纳入：`tests/governance/test_pr_guardian.py`、本事项 `decision` / `exec-plan`、必要的 release / sprint 索引
- 本次不纳入：`scripts/pr_guardian.py` 逻辑改写、merge gate 调整、`#150` contract 改动、历史 `exec-plan` 的批量迁移

## 当前停点

- `#150` 已合入主干，当前实现继续兼容 `metadata-only review sync` marker，但缺少独立回归。
- 当前工作树已创建：`/Users/mc/code/worktrees/syvert/issue-152-gov-legacy-metadata-only-review-sync-marker`。
- 下一步是在不改动实现逻辑的前提下补齐专门测试和 bootstrap 工件。

## 下一步动作

- 补一条 legacy marker 正向回归。
- 运行治理测试与 guard，确认只增加保护，不改变现有 contract。
- 创建受控 PR，推进 guardian / merge gate / issue closeout。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 的 guardian 治理链补齐 legacy marker 兼容回归，避免历史 closeout marker 在后续重构中静默失效。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#150` 合入后的治理补强项，负责锁死 legacy marker 兼容路径。
- 阻塞：无；只需确保改动停留在测试与治理工件层。

## 已验证项

- `gh issue create --title "[GOV] 锁定 legacy metadata-only review sync marker 兼容回归" ...`
- `python3 scripts/create_worktree.py --issue 152 --class governance`
- 已创建 worktree：`/Users/mc/code/worktrees/syvert/issue-152-gov-legacy-metadata-only-review-sync-marker`
- 已阅读：`docs/exec-plans/GOV-0031-guardian-live-head-binding.md`
- 已阅读：`docs/decisions/ADR-GOV-0031-guardian-live-head-binding.md`
- 已阅读：`tests/governance/test_pr_guardian.py`

## 未决风险

- 若只保留新 marker 的测试而不锁住 legacy marker，后续重构可能在无意中删除兼容支持。
- 若本事项误扩展到实现逻辑，会把一个纯测试锁定项演化成新的治理语义变更。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对测试、decision、exec-plan 与 release / sprint 索引的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `c1ec5cf4f353568fa4c7e85b368d550678f4f744`
- 说明：该 checkpoint 是 `#151` 合入后的主干基线；当前事项仅在其上补齐 legacy marker 兼容回归，不改写 guardian contract。
