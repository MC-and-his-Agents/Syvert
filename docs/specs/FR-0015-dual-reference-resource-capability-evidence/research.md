# Research

## 研究边界

- 本研究只服务 `FR-0015` 当前要冻结的双参考适配器资源能力证据基线。
- 证据边界固定为仓内当前共享执行路径：`content_detail_by_url + target_type=url + collection_mode=hybrid`。
- 研究目标不是发明更多能力名，而是证明在现有双参考适配器事实下，哪些候选能力可以被批准、哪些必须留在 adapter 私有层，哪些必须作为错误抽象方向被 `rejected` 收口。

## 证据登记项

| evidence_ref | 来源 | 结论 |
| --- | --- | --- |
| `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots` | `syvert/runtime.py` 中 `RESOURCE_SLOTS_BY_OPERATION_AND_COLLECTION_MODE` | 当前共享 Core 路径在 `content_detail_by_url + hybrid` 上统一请求 `account`、`proxy` 两个受管资源 slot |
| `fr-0015:xhs:content-detail:url:hybrid:account-material` | `syvert/adapters/xhs.py` 中 `build_session_config_from_context()` | 小红书 adapter 在共享路径上从 `resource_bundle.account.material` 提取 `cookies`、`user_agent`、`sign_base_url`、`timeout_seconds` |
| `fr-0015:douyin:content-detail:url:hybrid:account-material` | `syvert/adapters/douyin.py` 中 `build_session_config_from_context()` | 抖音 adapter 在共享路径上从 `resource_bundle.account.material` 提取 `cookies`、`user_agent`、`verify_fp`、`ms_token`、`webid`、`sign_base_url`、`timeout_seconds` |
| `fr-0015:xhs:content-detail:url:hybrid:url-request-tokens` | `syvert/adapters/xhs.py` 中 `build_detail_body()` | 小红书 adapter 只在平台私有 detail body 中透传 `xsec_token`、`xsec_source` 两个 URL / request token |
| `fr-0015:douyin:content-detail:url:hybrid:request-signature-token` | `syvert/adapters/douyin.py` 中 `DouyinAdapter._build_detail_params()` | 抖音 adapter 在平台私有签名步骤中生成并注入 `a_bogus` 请求 token |
| `fr-0015:xhs:content-detail:url:hybrid:page-state-fallback` | `syvert/adapters/xhs.py` 中 `XhsAdapter._recover_note_card_from_html()` | 小红书 adapter 在 detail / html 路径失败时会退回 browser page-state 恢复链路，这属于技术绑定回退 |
| `fr-0015:douyin:content-detail:url:hybrid:page-state-fallback` | `syvert/adapters/douyin.py` 中 `DouyinAdapter._recover_aweme_detail_from_page_state()` | 抖音 adapter 在 detail 路径失败时会退回 browser page-state 恢复链路，这属于技术绑定回退 |
| `fr-0015:regression:xhs:managed-proxy-seed` | `syvert/real_adapter_regression.py` 中 `seed_reference_regression_resources()` | 小红书真实适配器回归基线在共享路径上同时种入 `account` 与 `proxy` 资源 |
| `fr-0015:regression:douyin:managed-proxy-seed` | `syvert/real_adapter_regression.py` 中 `seed_reference_regression_resources()` | 抖音真实适配器回归基线在共享路径上同时种入 `account` 与 `proxy` 资源 |

## 共性资源语义

- 共享 Core 路径事实：当前 `content_detail_by_url + hybrid` 的共享运行时路径会统一请求 `account`、`proxy` 两个受管资源 slot。这证明 `account` 与 `proxy` 至少可以作为同一条共享路径上的最小能力标识进入 `v0.5.0` 讨论。
- 共享账号材料事实：小红书与抖音 adapter 都依赖 Core 注入的 `resource_bundle.account.material` 来构造自己的认证 / session 上下文。虽然各自材料内部字段不同，但“需要受管账号材料 carrier”这一层语义是共享的，因此 `account` 可以进入批准词汇。
- 共享代理前提事实：当前共享运行时路径与真实适配器回归种子都把 `proxy` 当作同一路径上的受管资源前提。`FR-0015` 因此只批准最小 `proxy` 能力，而不把它扩张成更高阶 network profile、provider taxonomy 或浏览器 profile 抽象。

## 单平台特例

- 抖音账号材料特例：`verify_fp`、`ms_token`、`webid` 只在抖音账号材料中出现，属于 adapter 私有前置，不能提升为共享能力。
- 抖音请求签名特例：`a_bogus` 只属于抖音 detail 请求签名细节，必须保持 platform-private；对应证据 ref 为 `fr-0015:douyin:content-detail:url:hybrid:request-signature-token`。
- 小红书 URL / 请求特例：`xsec_token`、`xsec_source` 属于小红书 URL 与请求链路细节，不能进入共享能力命名；对应证据 ref 为 `fr-0015:xhs:content-detail:url:hybrid:url-request-tokens`。
- 浏览器回退特例：两侧 adapter 都有各自的页面 / browser bridge 回退路径，但这些都属于执行实现细节，而不是共享能力本身；对应证据 refs 为 `fr-0015:xhs:content-detail:url:hybrid:page-state-fallback` 与 `fr-0015:douyin:content-detail:url:hybrid:page-state-fallback`。

## 被拒绝的抽象候选

- `sign_base_url`
  - 拒绝原因：虽然两侧都出现该字段，但它表达的是签名服务部署 / 技术接线，而不是可供 Core 匹配的共享资源能力。
- `browser_state`
  - 拒绝原因：该候选把浏览器桥接与页面状态恢复路径直接提升为能力名，技术绑定过重。
- `cookies`、`user_agent`
  - 拒绝原因：它们属于 `account.material` 的内部字段；单独提升会把字段形状误当成资源能力 taxonomy。
- `a_bogus`、`xsec_token`、`xsec_source`
  - 拒绝原因：这些都是平台私有 token 或 URL / 请求链路细节，虽然存在稳定证据，但不满足双参考共享抽象条件。
- `verify_fp`、`ms_token`、`webid`
  - 拒绝原因：这些字段目前只被抖音账号材料证明成立，因此只能作为 `adapter_only` 保留在 adapter 私有层。

## 冻结的 `v0.5.0` 最小能力词汇

| capability_id | 结论 | evidence_refs |
| --- | --- | --- |
| `account` | `shared + approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`、`fr-0015:xhs:content-detail:url:hybrid:account-material`、`fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `proxy` | `shared + approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`、`fr-0015:regression:xhs:managed-proxy-seed`、`fr-0015:regression:douyin:managed-proxy-seed` |

## 冻结的 evidence record 基线示例

| adapter_key | capability | execution_path | candidate_abstract_capability | shared_status | decision | evidence_refs |
| --- | --- | --- | --- | --- | --- | --- |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `account` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`、`fr-0015:xhs:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `account` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`、`fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `proxy` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`、`fr-0015:regression:xhs:managed-proxy-seed` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `proxy` | `shared` | `approve_for_v0_5_0` | `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`、`fr-0015:regression:douyin:managed-proxy-seed` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `verify_fp` | `adapter_only` | `keep_adapter_local` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `ms_token` | `adapter_only` | `keep_adapter_local` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `webid` | `adapter_only` | `keep_adapter_local` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `a_bogus` | `rejected` | `reject_for_v0_5_0` | `fr-0015:douyin:content-detail:url:hybrid:request-signature-token` |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `xsec_token` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:url-request-tokens` |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `xsec_source` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:url-request-tokens` |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `sign_base_url` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `sign_base_url` | `rejected` | `reject_for_v0_5_0` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `cookies` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `cookies` | `rejected` | `reject_for_v0_5_0` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `user_agent` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:account-material` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `user_agent` | `rejected` | `reject_for_v0_5_0` | `fr-0015:douyin:content-detail:url:hybrid:account-material` |
| `xhs` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `browser_state` | `rejected` | `reject_for_v0_5_0` | `fr-0015:xhs:content-detail:url:hybrid:page-state-fallback` |
| `douyin` | `content_detail` | `target_type=url, collection_mode=hybrid, operation=content_detail_by_url` | `browser_state` | `rejected` | `reject_for_v0_5_0` | `fr-0015:douyin:content-detail:url:hybrid:page-state-fallback` |
