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

- `v1.0.0` 前必须具备稳定的第三方 Adapter 接入路径，包括 Adapter public metadata、resource requirement、`execute()`、`raw + normalized`、错误映射与 contract test。
- `v1.0.0` 前必须冻结 Adapter + Provider 的最小兼容性判断模型：`Adapter capability requirement x Provider capability offer -> compatibility decision`。
- `v1.0.0` 前必须使用至少一个真实外部 provider 验证样本证明兼容性判断链路可执行；该样本只作为 contract evidence，不代表指定 provider 产品获得正式支持。
- Syvert 不承诺某一个 provider 覆盖所有 Adapter capability。任何 provider 只能声明自己可服务哪些 Adapter 的哪些 capability，并由兼容性判断与 evidence 决定是否允许绑定。
- 具体 provider 产品的正式支持、产品化接入、selector、fallback、compatibility matrix 与 provider SDK 扩展均属于 `v1.x` 或后续独立 FR，不进入 `v1.0.0` 主线成功标准。
- `v0.7.0` 的 release truth、`FR-0021` formal spec 与 `ADR-CHORE-0266` 不回写改写；本决策只校准 `v0.8.0+` 的路线。

## 影响

- roadmap 应从“`v1.x` 才决定是否需要 provider compatibility contract”调整为“`v1.0.0` 前冻结最小兼容性判断并以真实 provider 样本验证”。
- Adapter SDK 文档应明确社区接入主入口仍是 Adapter；provider 产品可以通过构建 Adapter 或提供 Adapter-bound provider offer 接入，但不能绕过 Adapter 直接接 Core。
- 框架定位应强调 Syvert 的主线目标是标准化接入与治理，不是把 OpenCLI、bb-browser、agent-browser 或任何指定 provider 产品列为官方支持目标。
