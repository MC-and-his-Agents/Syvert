# FR-0403 Read-side collection result and cursor contract

## 关联信息

- item_key：`FR-0403-read-side-collection-result-cursor-contract`
- Issue：`#403`
- item_type：`FR`
- release：`v1.3.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#403`

## 背景与目标

- 背景：`v1.1.0` 已冻结 operation taxonomy foundation，`v1.2.0` 已冻结 resource governance foundation，但 `v1.x` 还没有稳定的 read-side collection result contract。当前仓库只能稳定承载 `content_detail_by_url` 单目标详情执行路径，尚未统一表达多 item、分页、cursor continuation、partial result、raw/normalized 双轨与 collection-level 错误边界。
- 目标：冻结 `v1.3.0` 首个 read-side collection formal spec，定义 `content_search_by_keyword` 与 `content_list_by_creator` 共享的 collection target、result envelope、cursor continuation、item envelope、dedup key、source trace、partial result 与平台中立错误分类，为后续 runtime carrier、consumer migration、evidence 与 release closeout 提供 formal spec 输入。

## 范围

- 本次纳入：
  - `content_search_by_keyword` 与 `content_list_by_creator` 的公共 operation contract。
  - collection target、request continuation、result envelope、item envelope、next continuation、raw payload reference、normalized item、dedup key、source trace、audit fields。
  - first page、next page、empty result、duplicate item、partial result、cursor/session invalidation、permission denied、rate limited、platform/provider failure、parse failure、credential invalid、verification required 的公共边界。
  - Adapter 对平台 query / sort / filter / cursor 字段的投影边界。
- 本次不纳入：
  - runtime carrier implementation。
  - fake/reference/raw fixture payload files。
  - comment hierarchy、deleted/invisible comment semantics、creator profile shape、media download/no-download boundary。
  - batch execution、dataset sink、scheduled execution、provider selector、fallback、marketplace、上层内容库或分析产品。
  - `content_detail_by_url` stable baseline 改写。

## 需求说明

- 功能需求：
  - Core 必须能表达 `content_search_by_keyword` 与 `content_list_by_creator` 的 collection target 与 continuation input，而不理解平台私有 query object、page object、search-session object 或 creator page object。
  - collection result 必须包含 `items`、`has_more`、`next_continuation`、`result_status`、`raw_payload_ref`、`source_trace` 与审计字段。
  - 每个 item 必须可同时保留 raw payload reference 与 normalized item projection；Core 只能消费 normalized envelope，不消费平台私有 raw 字段。
  - collection contract 必须能表达 `empty`、`complete`、`partial_result` 三种结果状态。
  - collection contract 必须能表达跨页 dedup key，并允许不同平台以不同原始标识生成相同公共 dedup 语义。
  - continuation 既可以来自 opaque cursor，也可以来自 page/offset/search-session 等平台私有组合，但 Core 只接收平台中立 continuation token。
- 契约需求：
  - `content_search_by_keyword` 投影到 `content_search + keyword + single + paginated`。
  - `content_list_by_creator` 投影到 `content_list + creator + single + paginated`。
  - Adapter requirement、Provider offer、compatibility decision、TaskRecord 与 result query 后续只能消费本 FR 定义的公共 collection envelope，不得直接消费平台 raw item shape。
  - collection-level错误分类必须至少覆盖：`empty_result`、`target_not_found`、`rate_limited`、`permission_denied`、`platform_failed`、`provider_or_network_blocked`、`cursor_invalid_or_expired`、`parse_failed`、`partial_result`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`。
  - `credential_invalid` 与 `verification_required` 必须保持 fail-closed，并与 `v1.2.0` resource governance 边界一致，不得被降级成普通 `platform_failed`。
  - `content_detail_by_url` baseline 不得因 collection contract 引入新的 Core 分支或平台私有字段。
- 非功能需求：
  - collection contract 必须 fail-closed；无法证明 continuation、target、raw/normalized 投影或错误分类合法时，不得返回伪稳定结果。
  - repository 与 GitHub truth 不得记录外部样本项目名或本地路径；所有 evidence source 只能使用脱敏 alias。
  - synthetic fixture 只能从 recorded raw shape family 派生，不得凭空发明平台字段。

## 约束

- 阶段约束：
  - `v1.3.0` 当前只绑定 `#403` 的首个 collection-contract batch，不绑定整个 Phase 3。
  - 本 Work Item 只交付 Batch 0 inventory 与 Batch 1 formal spec；runtime、consumer migration、evidence、release closeout 必须另建 Work Item。
- 架构约束：
  - Core 只理解 public operation、target、continuation、result envelope、dedup key、source trace、error classification 与 resource admission outcome。
  - Adapter 负责平台 query 参数、sort/filter 语义、平台 item shape、平台 continuation shape 与 normalized item projection。
  - Provider 负责实际 HTTP、浏览器、签名或第三方执行路径，不定义 Syvert 的 collection vocabulary。
  - raw payload 只能作为审计/调试引用存在，不能成为 Core public decision fields。

## GWT 验收场景

### 场景 1：搜索第一页返回完整 collection result

Given `content_search_by_keyword` 使用合法 keyword target，且 Adapter 可以从 reference platform A 投影 recorded first-page raw response
When Core 执行 collection request
Then result 返回 `items`、`has_more=true`、`next_continuation`、`result_status=complete`、`raw_payload_ref` 与 normalized item list，且不暴露平台私有 query 或 item object name

### 场景 2：下一页 continuation 保持公共语义稳定

Given `content_list_by_creator` 已返回第一页并生成 `next_continuation`
When Core 使用该 continuation 请求下一页，且平台实际需要 page/offset/search-session 组合
Then Adapter 负责还原平台 continuation，Core 仍只接收平台中立 continuation token，且 item envelope 与错误边界保持不变

### 场景 3：空结果不会伪装成错误

Given `content_search_by_keyword` 命中合法但无结果的 target
When Core 执行 collection request
Then result 返回 `items=[]`、`result_status=empty`，且不得被分类为 `target_not_found` 或 `platform_failed`

### 场景 4：跨页重复 item 可以被稳定去重

Given 同一逻辑内容 item 出现在连续两页 raw response 中
When Adapter 为两页 item 分别投影 normalized item
Then collection contract 必须能生成稳定 dedup key，且不要求 Core 理解平台私有 ID 体系

### 场景 5：部分 item 解析失败时返回 partial result

Given 一页 raw response 中部分 item 可投影，部分 item 因 shape drift 解析失败
When Core 处理该页 collection result
Then result 返回 `result_status=partial_result`，保留成功 normalized items，并将失败归类为 `parse_failed` 而不是直接丢失整页结果

### 场景 6：continuation 失效有独立错误边界

Given collection request 使用的 continuation token 已失效或关联的平台 search session 已过期
When Adapter 还原 continuation 并请求下一页
Then result 必须归类为 `cursor_invalid_or_expired`，而不是 generic `platform_failed`

### 场景 7：resource health 与 verification 保持 fail-closed

Given collection request 依赖的 account session 已 invalid，或平台要求验证码/安全验证
When Core 处理 admission 或 Adapter 返回 verification-required signal
Then result 必须分别归类为 `credential_invalid` 或 `verification_required`，并保持 fail-closed，不得继续返回伪正常 collection items

## 异常与边界场景

- 异常场景：
  - raw response 缺少 `items` family、continuation family 或 collection status family 时，必须 `invalid_contract` 或 `parse_failed` fail-closed，不得伪造 `complete`。
  - continuation token 与 target 上下文不匹配时，必须返回 `cursor_invalid_or_expired`。
  - rate-limit、permission-denied、provider/network-blocked、signature/request-invalid 必须保持为独立公共错误分类。
  - raw payload present 但 normalized item 缺少最小必需字段时，必须进入 `parse_failed` 或 `partial_result` 路径。
- 边界场景：
  - `target_not_found` 与 `empty_result` 必须区分；合法 target 没有 item 不是 not found。
  - collection contract 不要求两个平台拥有完全一致的 raw source shape，只要求 Adapter 能把它们投影到同一公共 envelope。
  - `has_more=false` 且 `next_continuation` 为空时视为 collection 终点；不得强制所有平台必须返回 opaque cursor。
  - `content_list_by_creator` 与 `content_search_by_keyword` 共享 collection envelope，但可以有不同 target shape。

## 验收标准

- [ ] formal spec 冻结 `content_search_by_keyword` 与 `content_list_by_creator` 的共享 collection contract。
- [ ] formal spec 冻结 collection result envelope、item envelope、continuation、dedup key、source trace、raw payload reference 与 result status。
- [ ] formal spec 明确 `empty_result`、`target_not_found`、`rate_limited`、`permission_denied`、`platform_failed`、`provider_or_network_blocked`、`cursor_invalid_or_expired`、`parse_failed`、`partial_result`、`credential_invalid`、`verification_required`、`signature_or_request_invalid` 的公共边界。
- [ ] formal spec 明确 synthetic fixture 只能从 recorded raw shape 派生，且所有 evidence source 只能使用脱敏 alias。
- [ ] formal spec 明确 Adapter 负责平台 query/sort/filter/cursor 与 raw item projection，Core 不得接收平台私有对象。
- [ ] formal spec 明确 `content_detail_by_url` baseline 不受本 FR 改写。
- [ ] 本事项不修改 runtime、tests implementation、raw fixture payload files 或 release closeout truth。

## 依赖与外部前提

- 外部依赖：
  - `v1.1.0` operation taxonomy foundation 已发布。
  - `v1.2.0` resource governance foundation 已发布。
  - `#403` 已显式绑定 `v1.3.0 / 2026-S25`。
- 上下游影响：
  - 后续 runtime carrier Work Item 必须消费本 FR，而不是重新定义 collection envelope 或错误分类。
  - `#404` comment collection contract 与 `#405` creator/media contract 应复用本 FR 的 collection result、dedup、source trace 与 raw/normalized 基础边界。
