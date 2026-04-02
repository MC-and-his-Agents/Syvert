# CHORE-0032 执行计划

## 关联信息

- item_key：`CHORE-0032-vision-roadmap-boundary`
- Issue：`#32`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S14`
- 关联 spec：无（文档收口事项）
- 关联 decision：无
- 关联 PR：待补充
- active 收口事项：`CHORE-0032-vision-roadmap-boundary`

## 目标

- 收紧 `vision.md` 的当前阶段边界，避免长期目标提前侵入近期范围。
- 重排 `docs/roadmap-v0-to-v1.md` 的版本节奏，落实“契约验证前移、服务面后移、稳定化后置”。

## 范围

- 本次纳入：`vision.md`、`docs/roadmap-v0-to-v1.md`、本事项 `exec-plan`。
- 本次不纳入：Core/Adapter 实现、多租户与认证能力落地、治理流程主线改写。

## 当前停点

- 已完成 `vision.md` 与 `docs/roadmap-v0-to-v1.md` 文档收口，正在补齐受控 PR 必需上下文并准备开 PR。

## 下一步动作

- 提交本事项 `exec-plan` 文件。
- 通过受控入口创建 docs 类 PR，关联 Issue `#32`。
- 进入后续 review / guardian / squash merge 流程。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 文档基线收紧阶段边界，确保 roadmap 与 vision 对齐当前 Core 证明路径。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：文档收口事项，负责把战略叙事与版本节奏对齐。
- 阻塞：无。

## 已验证项

- `python3 scripts/docs_guard.py`
- `git status --short --branch`
- `python3 scripts/open_pr.py --class docs --issue 32 --item-key CHORE-0032-vision-roadmap-boundary --item-type CHORE --release v0.1.0 --sprint 2026-S14 --title "docs: 收紧 vision 与 roadmap 阶段边界" --closing refs --dry-run`

## 未决风险

- 若后续 roadmap 再次引入服务化能力前置，可能造成版本目标漂移。
- 若未来事项未持续使用双参考适配器回归 gate，边界约束可能再次弱化。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `vision.md`、`docs/roadmap-v0-to-v1.md` 与本 `exec-plan` 的改动。

## 最近一次 checkpoint 对应的 head SHA

- `4901f52`
