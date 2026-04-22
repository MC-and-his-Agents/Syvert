# Research

## 共性资源语义

- `managed_account`
  - 小红书与抖音都要求 Core 在 hybrid 执行路径上注入 account 资源，且该资源都承载可直接进入 adapter 执行面的账号 / 会话材料。
  - 两个平台都要求 account truth 受 `managed_adapter_key` 约束，说明“账号执行材料必须按 adapter 作用域隔离”是共享语义，而不是单平台特例。
  - 这支持把“受管账号能力”冻结为共享标识 `managed_account`，但不把平台私有字段名升格为共享 contract。
- `managed_proxy`
  - 小红书与抖音在 reference adapter 的 hybrid 真实路径上都依赖 Core 注入 proxy 资源，说明“受管网络出口能力”是双参考适配器共享语义。
  - 这支持把“受管代理能力”冻结为共享标识 `managed_proxy`，但不冻结 provider、协议或具体网络栈实现。
- 共享 execution baseline
  - 两个平台当前共同被 formal evidence 覆盖的路径是 `content_detail_by_url` 的 hybrid 执行链路；因此 `FR-0015` 的证据入口固定为 `hybrid_content_detail_by_url`，避免把其他尚未被双参考适配器共同证明的路径偷渡进来。

## 单平台特例

- 小红书特例：
  - xhs account material 允许携带 `sign_base_url`，且 adapter 侧存在 HTML / page-state fallback 与签名服务相关执行细节。
  - 这些信号可以证明“小红书账号执行材料比共享层更具体”，但它们不能单独成为共享资源能力标识，只能留在 adapter 私有 material 或 `adapter_only` evidence 中。
- 抖音特例：
  - douyin account material 允许携带 `verify_fp`、`ms_token`、`webid` 等单平台执行字段。
  - 这些信号说明抖音账号材料与小红书账号材料并不等形，但它们仍然属于 `managed_account` 下的 adapter 私有 material 细节，不应扩张成新的共享能力词汇。
- reference adapter material 形状不一致：
  - 双参考适配器共同证明了“需要 account / proxy 能力”，但没有共同证明“需要统一的 platform session schema”；因此共享层只冻结能力身份，不冻结 material 形状。

## 被拒绝抽象候选

- `managed_browser_runtime`
  - 原因：当前双参考适配器证据并未共同证明需要浏览器 runtime 作为共享资源能力；若提前引入，会直接绑定具体技术与 provider 生态。
- `managed_sign_service`
  - 原因：签名服务相关信号只在小红书侧出现，属于单平台执行细节；应保持 `adapter_only`，不得提升为共享能力。
- `managed_douyin_verification_tokens`
  - 原因：`verify_fp / ms_token / webid` 只在抖音侧出现，且属于 account material 私有字段；应保持 `adapter_only`，不得成为共享能力标识。
- `playwright_context` / `cdp_session` / `chromium_profile`
  - 原因：这些候选直接绑定具体技术实现，违反 `v0.5.0`“不应硬编码具体技术实现”的上位约束，因此必须被正式拒绝。

## 研究结论

- `v0.5.0` 当前被双参考适配器共同证明的共享资源能力只包括：`managed_account` 与 `managed_proxy`。
- 其余单平台信号必须继续留在 adapter 私有边界，或作为 rejected candidate 记录下来阻止抽象漂移。
- 因此 `#192/#193` 只能围绕 `managed_account / managed_proxy` 继续 formal spec，不得扩张第三个共享能力标识。
