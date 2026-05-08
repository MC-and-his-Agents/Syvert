# FR-0355 风险

## 风险

- 如果 external provider sample 只是一份仓内 native fixture，`v0.9.0` 会退化为自证，不能满足 `FR-0351` 的 `provider_compatibility_sample` gate。
- 如果 evidence 依赖私密账号、token 或 provider 控制台，reviewer 和 guardian 无法复验。
- 如果 closeout 把 external provider sample 写成 provider 产品正式支持，会违反 Syvert 底座边界。
- 如果 implementation 只交付 decision matrix 而没有 Adapter-bound execution evidence，无法证明 `FR-0351` 要求的执行链路可执行。
- 如果 implementation 为了适配样本改写 Core routing、registry、TaskRecord 或 resource lifecycle，会破坏 Core / Adapter / Provider 边界。
- 如果 provider sample 通过但双参考、第三方 Adapter-only entry 或 API / CLI same-path 回归失败，`v0.9.0` 仍不能收口。

## 缓解

- 要求样本以脱敏 fixture / artifact 进入仓库，并绑定 tests / PR / issue evidence。
- 要求 `provider_support_claim=false` 并在 release index 中明确不支持 provider 产品清单。
- 要求 provider no-leakage guard 与 Core surface audit 同时作为 required evidence。
- 要求 implementation Work Item 保留 approved slice，不在 `v0.9.0` 引入新 public operation。
