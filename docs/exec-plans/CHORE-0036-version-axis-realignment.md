# CHORE-0036 执行计划

## 关联信息

- item_key：`CHORE-0036-version-axis-realignment`
- Issue：`#36`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（文档收口事项）
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：待创建
- active 收口事项：`CHORE-0036-version-axis-realignment`

## 目标

- 基于当前 `main` 重新提交 `vision.md` 与 `docs/roadmap-v0-to-v1.md` 的版本主轴重排。
- 让本轮变更完整经过 `open_pr -> guardian -> merge_pr` 的受控审查链路后再合并。

## 范围

- 本次纳入：`vision.md`、`docs/roadmap-v0-to-v1.md`、当前 `exec-plan`
- 本次不纳入：治理协议主线修改、实现代码、额外产品方向讨论

## 当前停点

- 已恢复目标文档到 `97cd992` 对应文本，正在补齐当前事项上下文并准备通过受控入口创建 PR。

## 下一步动作

- 校验文档与当前事项工件。
- 推送 `issue-36-docs` 分支。
- 通过 `open_pr.py` 创建 docs 类 PR，随后回写 PR 链接与验证证据。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 文档基线重新落回“契约验证前移、服务面后移、稳定化后置”的版本主轴。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：文档重提与受控审查事项。
- 阻塞：无。

## 已验证项

- `git show 97cd992:vision.md`
- `git show 97cd992:docs/roadmap-v0-to-v1.md`
- 当前恢复目标：仅 `vision.md` 与 `docs/roadmap-v0-to-v1.md`

## 未决风险

- 若 PR 正文或 `exec-plan` 不补齐当前 head 的验证证据，guardian 仍可能拒绝合并。
- 若后续回合再次混入无关文件，可能触发 docs / governance 门禁失败。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `vision.md`、`docs/roadmap-v0-to-v1.md` 与当前 `exec-plan` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `81b94c2d5a6ae3acb28ef3c3d38213dabd09ad80`
