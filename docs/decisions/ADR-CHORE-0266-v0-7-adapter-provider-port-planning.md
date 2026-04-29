# ADR-CHORE-0266 Stage adapter provider port before external providers

## 关联信息

- Issue：`#266`
- item_key：`CHORE-0266-v0-7-adapter-provider-port-planning`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`

## 背景

当前小红书、抖音 adapter 没有引入外部 provider。adapter 内部的 HTTP/sign/browser bridge 同时承担目标系统语义适配与 provider-like 执行职责，这会让后续接入 WebEnvoy、OpenCLI、bb-browser 等 provider 时缺少明确落点。

`v0.7.0` 的目标是稳定适配器表面，而不是扩张站点业务能力或接入外部 provider。如果在同一版本同时做 provider port、外部 provider、新能力和 adapter 仓库拆分，Core / Adapter contract 的稳定化会被执行 provider 选择和站点能力扩张污染。

## 决策

- `v0.7.0` 先建立仓内 `Syvert Adapter -> Syvert-owned Provider Port -> Native Provider` 边界。
- 当前小红书、抖音 adapter 内部的 HTTP/sign/browser bridge 先按 native provider 实现细节处理。
- Core 继续只调用 Adapter，不引入 Core 级 provider registry、provider selector 或跨 provider fallback 策略。
- WebEnvoy、OpenCLI、bb-browser、agent-browser 等外部 provider 接入放到 `v1.0.0` 稳定之后的后续 FR。
- 搜索结果采集、评论采集、账号信息、发布、通知、浏览/点赞/收藏/评论等新增能力放到独立后续 FR，不进入 `v0.7.0` provider port 稳定化范围。
- adapter 是否拆出独立仓库只在主仓 Core / Adapter contract 稳定后评估。

## 影响

- `v0.7.0` 的 GitHub Phase / FR / Work Item 与仓内 roadmap / release / sprint 索引可以一致表达 provider port 的时间线。
- `FR-0021` 后续 formal spec 可以聚焦 adapter-owned provider port 与 native provider 拆分，不需要同时批准外部 provider 或更多站点能力。
- 后续外部 provider 接入拥有明确 extension point，但不能反向改变 `v0.7.0` 的 approved capability baseline。
