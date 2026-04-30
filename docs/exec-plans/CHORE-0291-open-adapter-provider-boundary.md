# CHORE-0291 open Adapter and provider compatibility boundary 执行计划

## 关联信息

- item_key：`CHORE-0291-open-adapter-provider-boundary`
- Issue：`#291`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：无（roadmap / SDK / positioning 文档校准）
- 关联 decision：`docs/decisions/ADR-CHORE-0291-open-adapter-provider-boundary.md`
- 状态：`active`

## 目标

- 修订 `v0.8.0`、`v0.9.0`、`v1.0.0` 与 `v1.x` 路线，明确 `v1.0.0` 前应具备第三方 Adapter 接入稳定路径、Adapter + Provider 兼容性判断与真实 provider 验证样本。
- 明确指定 provider 产品的正式支持不是 Syvert 主线目标；具体产品接入必须通过独立 FR、Adapter capability binding 与 evidence 批准。
- 保持 `v0.7.0` release truth、`FR-0021` formal spec 与既有执行证据不被反向改写。

## 范围

- 本次纳入：
  - `docs/roadmap-v0-to-v1.md`
  - `adapter-sdk.md`
  - `framework-positioning.md`
  - `vision.md`
  - `docs/decisions/ADR-CHORE-0291-open-adapter-provider-boundary.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
  - `docs/exec-plans/CHORE-0291-open-adapter-provider-boundary.md`
- 本次不纳入：
  - runtime / adapter / test 实现
  - `FR-0021` formal spec 或 `v0.7.0` release/sprint 历史 truth 改写
  - 指定外部 provider 产品的正式支持
  - Core provider registry、provider selector、provider fallback priority 或 provider marketplace

## 当前停点

- Issue `#291` 已创建，作为本次文档修订的 Work Item。
- 独立 worktree 已创建：`/Users/mc/code/worktrees/syvert/issue-291-docs-roadmap-adapter-provider`。
- 当前承载分支：`issue-291-docs-roadmap-adapter-provider`。
- 当前主干基线：`d2f22691804b27581d64cf3911ae446734c3f1a1`。

## 下一步动作

- 完成 roadmap、SDK、定位文档、decision、release/sprint 索引与本 exec-plan 修订。
- 运行 docs / workflow / context / governance / PR scope 相关门禁。
- 创建受控 PR，等待 guardian 与 GitHub checks 通过后按 `merge_pr.py` 合并。
- 合并后回写 Issue `#291` 状态并关闭。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 建立开放接入路线的入口 truth，使后续 formal spec / implementation Work Item 能围绕第三方 Adapter 接入与 Provider 兼容性判断继续推进。

## 最近一次 checkpoint 对应的 head SHA

- `ea786d10ed55e92a246cdf65dc9b220e99be71e6`

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 的 roadmap / SDK 边界校准 Work Item。
- 位置：本事项是 `v0.8.0` 开放接入稳定化主线的规划入口，不替代后续 formal spec。
- 阻塞：
  - 本事项合入前，不应把 `v1.0.0` 前的 provider 目标写成指定 provider 产品正式支持。
  - 本事项合入前，后续 provider compatibility formal spec 缺少 roadmap 与 SDK 入口依据。

## 已验证项

- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/context_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR class=docs`。
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。

## 风险与回滚

- 风险：若文档把真实 provider 验证样本写成指定 provider 产品正式支持，会偏离 Syvert 主线目标。
  - 缓解：roadmap 与 SDK 均使用“真实 provider 验证样本 / compatibility evidence”表述，不列产品白名单作为成功标准。
- 风险：若修订反向改写 `v0.7.0` 的历史范围，会破坏已发布 release truth。
  - 缓解：不修改 `docs/releases/v0.7.0.md`、`docs/sprints/2026-S20.md`、`FR-0021` formal spec 或既有 evidence。
- 回滚：通过独立 revert PR 撤销本 Work Item 的文档、decision、release/sprint 索引与 exec-plan 增量。
