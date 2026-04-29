# FR-0021 data model

## Adapter Provider Port

用途：表达 Adapter 内部调用 native provider 的稳定边界。该边界只存在于 adapter implementation 内部，不进入 Core contract。

字段/语义：

- `owner_adapter_key`
  - 约束：固定为拥有该 provider port 的 adapter key，例如 `xhs` 或 `douyin`。
  - 不得用于 Core routing。
- `capability_family`
  - 约束：当前只允许 `content_detail`。
  - 不得新增搜索、评论、发布、通知或互动能力。
- `target_type`
  - 约束：当前只允许 `url`。
- `collection_mode`
  - 约束：当前只允许 `hybrid`。
- `native_provider`
  - 约束：仓内默认实现；不是外部 provider identity。

禁止字段：

- `provider_key`
- `provider_priority`
- `fallback_order`
- `external_provider_ref`
- `resource_provider`
- `provider_capabilities`

## Provider Execution Request

用途：Adapter 传给 native provider 的内部执行输入。

最小语义：

- `provider_context`
  - 来源：Adapter 在完成 `AdapterExecutionContext` 解析、request validation 与 resource bundle consumption 后构造的内部上下文。
  - 约束：不得直接携带 `AdapterExecutionContext`、`TaskRequest`、Core `resource_bundle`、resource lease 或 lifecycle store。
- `input_url`
  - 来源：Adapter 已验证的 request target。
- `parsed_target`
  - 来源：Adapter 已解析的站点目标对象，例如小红书 note id / xsec 参数或抖音 aweme id / canonical URL。
- `platform_session_config`
  - 来源：Adapter 从 Core 注入的 account resource material 中抽取并校验后的平台会话配置。
  - 约束：native provider 只能消费该最小平台配置，不得自行读取 account/proxy resource、不得 acquire/release resource、不得把 session material 提升为新的 Core resource type。
- `transport_hooks`
  - 来源：Adapter constructor 已接收的 legacy transport hooks 或默认 transport helper。
  - 约束：这是 adapter-owned 测试/本地注入 seam，不是 provider registry 或外部 provider binding。

## Provider Execution Result

用途：native provider 返回给 Adapter 的内部执行结果。

最小语义：

- `raw_payload`
  - 约束：平台原始响应、synthesized detail response 或等价 raw carrier。
- `platform_detail`
  - 约束：Adapter normalizer 所需的平台详情对象，例如 note card 或 aweme detail。
- `diagnostics`
  - 约束：可选内部诊断信息；不得进入 Core public envelope，除非 Adapter 已按既有契约显式投影。

禁止语义：

- 不返回 Syvert normalized result。
- 不返回 TaskRecord mutation。
- 不返回 resource disposition decision，除非仍通过既有 `PlatformAdapterError.resource_disposition_hint` 路径表达。

## Native Provider

用途：当前仓内实现，用于承载现有 HTTP/sign/browser bridge 执行细节。

当前批准实现：

- `NativeXhsProvider.fetch_content_detail(context, input_url)`
- `NativeDouyinProvider.fetch_content_detail(context, input_url)`

稳定性：

- 方法名可在实现中等价调整，但必须保持 Adapter public runtime surface 不变。
- Native provider 是仓内内部类型，不承诺第三方 import compatibility。
- 若现有 default transport helper 被移动，原 adapter module import path 必须 re-export。

## Adapter Surface Compatibility Snapshot

当前必须保持兼容的 public surface：

- `adapter_key`
- `supported_capabilities`
- `supported_targets`
- `supported_collection_modes`
- `resource_requirement_declarations`
- `execute(request: AdapterExecutionContext) -> dict`
- constructor transport hooks

当前冻结值：

- `xhs.supported_capabilities = {"content_detail"}`
- `douyin.supported_capabilities = {"content_detail"}`
- `supported_targets = {"url"}`
- `supported_collection_modes = {"hybrid"}`
- required resource capabilities remain `account` and `proxy`

## Approved Slice Compatibility Baseline

该 baseline 是 `#269` runtime split 与 `#271` evidence 的最小可判定输入；实现不得只以 public metadata 不变替代行为兼容验证。

公共投影：

- Core public operation `content_detail_by_url` 必须继续投影到 adapter capability family `content_detail`。
- request target type 继续只接受 `url`，collection mode 继续只声明 `hybrid`。
- 成功 payload 继续由 Adapter 返回 `{"raw": raw_payload, "normalized": normalized_content_detail}`。
- `normalized` 继续由 Adapter normalizer 生成，provider result 不得绕过 Adapter 直接返回 Syvert normalized result。

小红书兼容基线：

- URL parsing 继续只批准小红书详情页 URL，例如 `www.xiaohongshu.com/explore/{note_id}`；`xhslink` 短链、非小红书域名与非详情路径继续按既有 `invalid_xhs_url` 语义拒绝。
- `xsec_token` 与 `xsec_source` 继续只是 Adapter/Provider 内部 detail request 参数，不得提升为 resource 字段、provider selector 字段或 Core routing hint。
- account material 继续由 Adapter 从 injected account resource 中抽取并校验，最小字段为 `cookies`、`user_agent`，可选字段为 `sign_base_url`、`timeout_seconds`；native provider 不得直接读取 Core resource bundle。
- HTTP/sign/browser fallback 可以移入 native provider，但 `raw` 仍必须是当前 API detail response、HTML-derived page state carrier 或 browser-derived page state carrier 的等价 raw payload；不得向 Core envelope 暴露 provider identity。
- XHS normalized 字段兼容性至少覆盖 `platform`、`content_id`、`content_type`、`canonical_url`、`title`、`body_text`、`published_at`、`author`、`stats` 与 `media`。
- 既有错误优先级必须保持：结构化 detail error 不得被 HTML/browser fallback 掩盖；browser tab missing 时继续保留更精确 HTML error；非 tab-missing browser error 继续外抛。

抖音兼容基线：

- URL parsing 继续批准 `www.douyin.com/video/{aweme_id}` 与 `www.iesdouyin.com/share/video/{aweme_id}`；`v.douyin.com` 短链、非抖音域名、非详情路径与非数字 aweme id 继续按既有 `invalid_douyin_url` 语义拒绝。
- canonical URL 继续归一为 `https://www.douyin.com/video/{aweme_id}`。
- account material 继续由 Adapter 从 injected account resource 中抽取并校验，最小字段为 `cookies`、`user_agent`，可选字段为 `verify_fp`、`ms_token`、`webid`、`sign_base_url`、`timeout_seconds`；native provider 不得直接读取 Core resource bundle。
- HTTP/sign/browser recovery 可以移入 native provider，但 browser fallback 的 `raw` 仍必须是 synthesized detail response 等价形态，不能泄漏 `SSR_RENDER_DATA`、`AWEME_DETAIL` 或其他页面态 provider-internal 键。
- Douyin normalized 字段兼容性至少覆盖 `platform`、`content_id`、`content_type`、`canonical_url`、`title`、`body_text`、`published_at`、`author`、`stats` 与 `media`。
- 既有错误优先级必须保持：当 browser page state 未命中目标内容时继续保留原 detail error；browser target tab missing / content not found 的 fallback 语义不得被 provider selector 或 fallback priority 字段替代。

技术字段边界：

- `cookies`、`user_agent`、`sign_base_url`、`verify_fp`、`ms_token`、`webid`、browser page state、sign request headers、xsec 参数、aweme detail params 都只能作为 adapter/provider 内部执行材料。
- 这些字段不得进入 `resource_requirement_declarations`、Adapter registry discovery、TaskRecord public envelope、resource lifecycle state 或 Core routing metadata。

## Error Boundary

用途：规定 provider 内部错误如何回到 Adapter / Core failure model。

约束：

- Native provider 可以抛出现有 `PlatformAdapterError`。
- Adapter 必须继续负责把平台失败映射到现有 failed envelope。
- 不新增 provider-specific error category。
- 不把 provider failure 暴露为 provider selector 或 fallback outcome。
