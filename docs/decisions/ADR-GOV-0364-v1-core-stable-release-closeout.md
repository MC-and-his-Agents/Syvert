# ADR-GOV-0364 Record v1.0.0 Core stable release closeout and published-truth plan

## 关联信息

- Issue：`#364`
- item_key：`GOV-0364-v1-core-stable-release-closeout`
- item_type：`GOV`
- release：`v1.0.0`
- sprint：`2026-S22`
- Parent Phase：`#363`

## 背景

`v1.0.0` 的 Core stable gate truth 已由 `FR-0351` 冻结，`v0.9.0` 也已为其提供 `provider_compatibility_sample` evidence。当前主干同时满足以下事实：

- `FR-0351 / #351` 已完成并关闭，定义 `v1.0.0` required gate items。
- `GOV-0360 / #360` 已完成并关闭，`v0.9.0` release truth 已回写。
- 当前 `main` 上，双参考回归、第三方 Adapter-only 入口、provider no-leakage、real provider sample 与 API / CLI same-path 关键验证可复验通过。

仍需补齐正式发布锚点与 closeout 对账：`docs/releases/v1.0.0.md`、closeout evidence、annotated tag、GitHub Release、published truth carrier 以及 Phase / Work Item GitHub 状态。

## 决策

- 使用 Phase `#363` 承接 `v1.0.0` Core stable release closeout。
- 使用治理 Work Item `#364 / GOV-0364-v1-core-stable-release-closeout` 承接 release closeout carrier 与 published truth 锚点。
- 本事项不新增 runtime、formal spec、Adapter、Provider 或 Python packaging 语义。
- 本事项采用串行 closeout：
  - 阶段 A：通过 docs PR 建立 release closeout carrier，包括 release index、sprint index、exec-plan、ADR 与 evidence artifact。
  - 发布锚点：阶段 A 合入后，在阶段 A merge commit 上创建 `v1.0.0` annotated tag 和 GitHub Release。
  - 阶段 B：通过 follow-up docs PR 回写 tag / GitHub Release published truth，并在合入后关闭 `#363/#364`。

## 影响

- `v1.0.0` 从“当前主干满足发布前 gate”推进到“Core stable 发布真相可版本化、可复验”。
- `v1.x -> v2.0.0` 可以在稳定 Core 锚点之上继续扩展 runtime capability contract，而不重解释 `v1.0.0`。
- 本事项不声明任何指定 provider 产品正式支持，不引入 Core provider registry、provider selector、fallback、ranking 或 marketplace。
