# ADR-CHORE-0291 Stabilize open Adapter entry and provider compatibility before v1.0

## 关联信息

- Issue：`#291`
- item_key：`CHORE-0291-open-adapter-provider-boundary`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`

## 背景

`v0.7.0` 已完成 adapter-owned provider port 与 native provider 拆分。该版本的决策仍然成立：`FR-0021` 不批准外部 provider 接入，也不把 provider port 建模为 Core-facing provider SDK。

但 `v1.0.0` 若要声明 Core / Adapter contract 稳定，不能只证明主仓参考适配器可运行。Syvert 还需要证明第三方可以以 Adapter 方式接入，并且复杂执行能力可以通过受控的 Adapter + Provider 兼容性判断进入 Adapter 内部，而不是通过 Core provider registry、指定 provider 产品白名单或隐式运行时约定进入系统。

## 决策

- 本 ADR 与 `docs/roadmap-v0-to-v1.md` 是 `v0.8.0+` 开放 Adapter / Provider compatibility 路线的 canonical carrier。
- `FR-0021` formal spec 继续只约束 `v0.7.0` adapter-owned provider port 与 native provider 拆分范围；它不是 `v0.8.0+` provider compatibility 路线的 canonical carrier。
- 本 ADR 不改写 `FR-0021` formal spec，不改写 `v0.7.0` 的 approved scope，也不把外部 provider 接入反向纳入 `FR-0021`。
- `ADR-CHORE-0266` 中关于“外部 provider 接入放到 `v1.0.0` 稳定之后”的表述继续作为 `v0.7.0` scope guard；自本 ADR 起，`v0.8.0+` 后续路线以本 ADR 与 roadmap 为准。
- `v1.0.0` 前必须具备稳定的第三方 Adapter 接入路径，包括 Adapter public metadata、resource requirement、`execute()`、`raw + normalized`、错误映射与 contract test。
- `v1.0.0` 前必须冻结 Adapter + Provider 的最小兼容性判断模型：`Adapter capability requirement x Provider capability offer -> compatibility decision`。
- `v1.0.0` 前必须使用至少一个真实外部 provider 验证样本证明兼容性判断链路可执行；该样本只作为 contract evidence，不代表指定 provider 产品获得正式支持。
- Syvert 不承诺某一个 provider 覆盖所有 Adapter capability。任何 provider 只能声明自己可服务哪些 Adapter 的哪些 capability，并由兼容性判断与 evidence 决定是否允许绑定。
- 具体 provider 产品的正式支持、产品化接入、selector、fallback、compatibility matrix 与 provider SDK 扩展均属于 `v1.x` 或后续独立 FR，不进入 `v1.0.0` 主线成功标准。
- `v0.7.0` 的 release truth、`FR-0021` formal spec 的批准范围与 `ADR-CHORE-0266` 的 `v0.7.0` 决策不回写改写；本决策只建立 `v0.8.0+` 的后续路线真相。

## 历史时间边界解释

- `ADR-CHORE-0266` 中“WebEnvoy、OpenCLI、bb-browser、agent-browser 等外部 provider 接入放到 `v1.0.0` 稳定之后的后续 FR”继续说明 `v0.7.0` 不接入外部 provider；它不再作为 `v0.8.0+` 的路线 carrier。
- `FR-0021` 中“外部 provider 接入、更多站点能力、adapter 独立仓库评估均留到 `v1.0.0` 稳定之后或后续独立 FR”继续约束 `FR-0021` 自身不批准外部 provider 接入；它不再作为 provider compatibility contract 与真实 provider 验证样本时间线的后续路线 carrier。
- 后续如需正式支持某个 provider 产品，仍必须通过新的 FR，而不是复用本 ADR 或 `FR-0021`。

## 影响

- roadmap 应从“`v1.x` 才决定是否需要 provider compatibility contract”调整为“`v1.0.0` 前冻结最小兼容性判断并以真实 provider 样本验证”。
- Adapter SDK 文档应明确社区接入主入口仍是 Adapter；provider 产品可以通过构建 Adapter 或提供 Adapter-bound provider offer 接入，但不能绕过 Adapter 直接接 Core。
- 框架定位应强调 Syvert 的主线目标是标准化接入与治理，不是把 OpenCLI、bb-browser、agent-browser 或任何指定 provider 产品列为官方支持目标。
