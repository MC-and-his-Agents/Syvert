# FR-0405 Creator profile and media asset read contract

## 关联信息

- item_key：`FR-0405-creator-profile-media-asset-read-contract`
- Issue：`#405`
- item_type：`FR`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`

## 背景与目标

- 背景：`v1.3.0` 已冻结并发布 read-side collection foundation，`#404` comment collection 正在独立推进。Phase 3 仍缺少单目标 creator profile 与 media asset fetch 的公共读侧 contract。当前风险是 Core 被迫理解平台私有 creator object、media URL list、download artifact 或 asset storage 行为。
- 目标：冻结 `v1.5.0` creator profile / media asset read formal spec，定义 `creator_profile_by_id` 与 `media_asset_fetch_by_ref` 的 target、result envelope、public profile result、media asset ref、content type、fetch policy、download/no-download boundary、raw/normalized 双轨、source trace 与平台中立错误分类，为后续 runtime carrier、consumer migration、evidence 与 release closeout 提供 formal spec 输入。

## 范围

- 本次纳入：
  - `creator_profile_by_id` 与 `media_asset_fetch_by_ref` 的公共 operation contract。
  - creator target、public creator profile result、media asset ref、media fetch result、content type、fetch policy、fetch outcome、raw payload reference、normalized result、source trace、audit fields。
  - public profile success、creator not found/unavailable、permission denied、rate limited、image media ref、video media ref、metadata-only fetch、source-ref-preserved result、download/no-download boundary、unavailable media、unsupported content type、platform/provider failure、parse failure、credential invalid、verification required 的公共边界。
  - Adapter 对平台 creator id、profile field、media ref、media URL、content type 与 fetch outcome 的投影边界。
- 本次不纳入：
  - runtime carrier implementation。
  - fake/reference/raw fixture payload files。
  - comment hierarchy、reply cursor、comment visibility semantics。
  - batch execution、dataset sink、scheduled execution、provider selector、fallback、marketplace、上层内容库、资产库或媒体存储产品。
  - `content_detail_by_url` stable baseline 或 `#403` collection envelope 的改写。

## 需求说明

- 功能需求：
  - Core 必须能表达 `creator_profile_by_id` 的 creator target，而不理解平台私有 creator page object、user model、profile response schema 或私有画像字段。
  - Core 必须能表达 `media_asset_fetch_by_ref` 的 media target、fetch policy 与 fetch outcome，而不理解平台私有 media URL list、签名 URL、下载器实现或对象存储策略。
  - creator profile result 必须只包含 public normalized profile fields、raw payload reference、source trace 与审计字段。
  - media fetch result 必须表达 `metadata_only`、`source_ref_preserved`、`downloaded_bytes` 三类 outcome boundary；`downloaded_bytes` 只能在 public metadata 中记录 byte/checksum 事实，下载证明如需保留只能进入 audit evidence，不使 Core 成为媒体库、资产存储或 bytes retrieval API。
  - fetch policy 必须固定优先级：先投影公共 content type，再执行 `allowed_content_types`、source ref preservation、`allow_download` 与 `max_bytes` 决策；无法投影公共 content type 返回 `unsupported_content_type`，可投影但不被 request policy 允许返回 `fetch_policy_denied`。
  - fetch mode 必须固定降级路径：`metadata_only` 不下载但必须保留脱敏 source ref lineage；`preserve_source_ref` 只保留 source ref，无法保留时返回 `fetch_policy_denied`；`download_if_allowed` 在 `allow_download=true` 且 cost/size boundary 允许时可以返回 `downloaded_bytes`，也可以在未执行 bytes transfer 且 source ref lineage 可保留时降级为 `source_ref_preserved`，无法保留 source ref 时返回 `fetch_policy_denied`；`download_required` 在下载不允许或超出边界时必须返回 `fetch_policy_denied`。
  - raw payload 与 normalized result 必须双轨保留；Core 只能消费 normalized envelope，不消费平台私有 raw 字段。
- 契约需求：
  - 本 FR 定义 `creator_profile_by_id` 到 `creator_profile + creator + single + direct` 的 formal spec projection；在 canonical taxonomy / admission contracts 更新前，该 projection 不等同于 stable executable slice。
  - 本 FR 定义 `media_asset_fetch_by_ref` 到 `media_asset_fetch + media_ref + single + direct` 的 formal spec projection；在 canonical taxonomy / admission contracts 更新前，该 projection 不等同于 stable executable slice。
  - `creator_profile` 与 `media_asset_fetch` 在本 Work Item 合入后仍不得绕过 `FR-0368` taxonomy lifecycle 与 `FR-0024/FR-0025/FR-0026` admission chain；后续 runtime Work Item 必须先把 requirement / offer / compatibility decision 输入域扩展到这些 approved slices。
  - compatibility decision 只能消费 Adapter requirement 与 Provider offer 的 admission inputs，不消费 result carriers；TaskRecord 与 result query 后续只能消费本 FR 定义的公共 result carriers，不得直接消费平台 creator/media raw shape。
  - creator/media 错误分类必须至少覆盖：`target_not_found`、`profile_unavailable`、`media_unavailable`、`unsupported_content_type`、`permission_denied`、`rate_limited`、`platform_failed`、`provider_or_network_blocked`、`parse_failed`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`、`fetch_policy_denied`。
  - `credential_invalid` 与 `verification_required` 必须保持 fail-closed，并与 `v1.2.0` resource governance 边界一致，不得被降级成普通 `platform_failed`。
  - `content_detail_by_url` baseline 与 `#403` collection envelope 语义不得因本 contract 被改写；`#404` comment collection 的 shared runtime conflict risk 由后续 runtime Work Item 单独评估。
- 非功能需求：
  - creator/media contract 必须 fail-closed；无法证明 target、raw/normalized 投影、content type、fetch policy 或错误分类合法时，不得返回伪稳定结果。
  - malformed creator/media response 不得引入未定义公共错误分类；无法投影时统一收敛到 `parse_failed`，可识别媒体类型边界时优先使用 `unsupported_content_type`。
  - repository 与 GitHub truth 不得记录外部样本项目名或本地路径；所有 evidence source 只能使用脱敏 alias。
  - synthetic fixture 只能从 recorded raw shape family 派生，不得凭空发明平台字段。

## 约束

- 阶段约束：
  - `v1.5.0` 当前只绑定 `#405` creator-profile/media-asset release slice，不绑定整个 Phase 3。
  - 本 Work Item 只交付 Batch 0 inventory 与 Batch 1 formal spec；runtime、consumer migration、evidence、release closeout 必须由 `#422/#423/#424/#425/#426` 承接。
  - 本 Work Item 不把 `creator_profile` 或 `media_asset_fetch` 从 `proposed` 提升为 executable lifecycle；taxonomy / admission truth 由后续 runtime Work Item 在进入实现前显式更新。
  - `#421` 可与 `#404` 并行，因为它不触碰 runtime/consumer 实现；`#422/#423/#424` 必须等待 predecessor gates 与 shared runtime conflict-risk clearance。
- 架构约束：
  - Core 只理解 public operation、target、result envelope、source trace、error classification 与 resource admission outcome；`fetch_policy` 与 `fetch_outcome` 只属于 `media_asset_fetch_by_ref`。
  - Adapter 负责平台 creator id/profile 字段、平台 media ref/URL/content type、平台下载或 metadata fetch 的 normalized projection。
  - Provider 负责实际 HTTP、浏览器、签名、第三方执行路径或 bytes transfer，不定义 Syvert 的 creator/media vocabulary。
  - raw payload 只能作为审计/调试引用存在，不能成为 Core public decision fields。
  - Core 不拥有 media bytes storage、asset lifecycle、thumbnail generation、media transcoding 或 content library semantics。

## GWT 验收场景

### 场景 1：公开 creator profile 成功返回 normalized public result

Given `creator_profile_by_id` 使用合法 creator target，且 Adapter 可以从 reference platform A 投影 recorded public profile raw response
When Core 执行 creator profile request
Then result 返回 normalized public profile、`raw_payload_ref`、`source_trace` 与 `result_status=complete`，且不暴露平台私有 user object、profile schema 或 private fields

### 场景 2：两个 reference creator model 投影到同一 public profile envelope

Given reference platform A 与 reference platform B 使用不同 creator id、nickname、avatar、counter 字段命名
When Adapter 分别投影 normalized creator profile
Then Core 只看到同一 public profile envelope，且 optional public counters 缺失不会使 profile invalid

### 场景 3：creator 不存在与 profile 不可用保持独立边界

Given `creator_profile_by_id` 使用的 creator target 不存在或已不可解析
When Core 执行 request
Then result 必须返回 `error_classification=target_not_found`

Given creator target 存在但公开 profile 不可查看
When Core 执行 request
Then 若平台语义表示该 profile 对所有公共读取不可用、已停用、已删除或不可公开展示，result 必须返回 `error_classification=profile_unavailable`

Given creator target 存在但当前资源、权限或登录状态无权查看该 profile
When Core 执行 request
Then result 必须返回 `error_classification=permission_denied`

### 场景 4：image media ref 只保留 source ref 与 content type

Given `media_asset_fetch_by_ref` 使用 image-like media ref
When fetch policy 要求 metadata-only 或 source-ref-preserved
Then result 返回 `content_type=image`、`fetch_outcome=metadata_only` 或 `source_ref_preserved`，并保留 source ref 与 raw payload ref，不下载 bytes

### 场景 5：video media ref 可以表达下载边界但不进入资产库

Given `media_asset_fetch_by_ref` 使用 video-like media ref，且 fetch policy 允许下载
When Provider 完成 bytes transfer
Then public result 只能记录 `fetch_outcome=downloaded_bytes`、content type、`byte_size`、`checksum_digest`、`checksum_family` 与 source trace；下载证明如需保留只能进入 audit evidence，且不得创建 Core media storage lifecycle、bytes retrieval API 或 storage handle 公共语义

### 场景 6：unsupported content type fail-closed

Given media ref 指向 recognized live-photo-like 或 mixed media shape
When 当前 FR 未定义对应公共 content type 与组件 carrier
Then result 必须返回 `error_classification=unsupported_content_type`，不得伪装成 image/video 或用扩展区承载平台私有 media object

Given media ref 指向 unsupported 或无法稳定识别的 content type
When Adapter 无法投影到公共 content type set
Then result 必须返回 `error_classification=unsupported_content_type`，不得伪装成 image/video 或 generic parse failure

Given media ref 可以投影为公共 content type，但该类型不在 request 的 `allowed_content_types` 内
When Adapter/Provider 应用 fetch policy
Then result 必须返回 `error_classification=fetch_policy_denied`，不得返回 `unsupported_content_type`

### 场景 7：media unavailable 与 permission denied 分离

Given media ref 已失效、过期或不可解析
When Core 执行 media fetch request
Then result 返回 `error_classification=media_unavailable`

Given media ref 存在但当前资源无权访问
When Core 执行 media fetch request
Then result 返回 `error_classification=permission_denied`，且不得暴露 raw credential/session details

### 场景 8：fetch policy 阻止大文件或高成本下载

Given media ref 需要下载大文件或高成本资源，且 fetch policy 不允许该行为
When Adapter/Provider 评估 fetch policy
Then 若 request 使用 `download_required`，result 必须返回 `error_classification=fetch_policy_denied`

Given media ref 需要下载大文件或高成本资源，且 fetch policy 使用 `download_if_allowed`
When Adapter/Provider 可以在不下载 bytes 的情况下保留 source ref 或 metadata
Then result 必须降级为 `source_ref_preserved`，且不得隐式下载 bytes

Given fetch policy 使用 `download_if_allowed`
When Adapter/Provider 不能保留脱敏 source ref lineage
Then result 必须返回 `error_classification=fetch_policy_denied`，不得返回 metadata-only 成功结果

Given media fetch 返回成功结果
When Adapter/Provider 返回成功 media result
Then `source_ref_lineage.preservation_status` 必须为 `preserved`，并能把 request `media_ref` 追溯到 normalized `source_media_ref` / `canonical_ref`

### 场景 9：resource health 与 verification 保持 fail-closed

Given creator/media request 依赖的 account session 已 invalid，或平台要求验证码/安全验证
When Core 处理 admission 或 Adapter 返回 verification-required signal
Then result 必须分别归类为 `credential_invalid` 或 `verification_required`，并保持 fail-closed，不得继续返回伪正常 profile/media result

### 场景 10：raw payload present 但 normalized projection 失败

Given creator/media raw payload 已获取，但 minimum public profile fields 或 media ref projection 不满足 contract
When Adapter 投影 normalized result
Then result 必须归类为 `parse_failed`，保留 raw payload reference，并不得把平台 raw fields 提升为 Core public fields

### 场景 11：rate limit 与平台失败边界独立表达

Given creator profile 或 media asset request 返回 access-frequency、anti-abuse 或 throttling signal
When Adapter 投影公共失败结果
Then result 必须返回 `error_classification=rate_limited`，且 `profile` 或 `media` 必须为 `null`

Given platform 返回无法归入更强分类的 upstream failure
When Adapter 投影公共失败结果
Then result 必须返回 `result_status=failed` 与 `error_classification=platform_failed`，且不得伪造 normalized profile 或 media result

### 场景 12：Provider / network blocked 不污染平台语义

Given Provider、browser、network 或 third-party path 在稳定平台响应前被 blocked
When Core 接收失败结果
Then result 必须返回 `error_classification=provider_or_network_blocked`，`raw_payload_ref=null`，且不暴露 provider routing、fallback 或 selector details

### 场景 13：signature/request invalid 优先于 generic failure

Given Adapter 或 Provider 能识别 signed request、request body 或 request contract 不合法
When Core 接收失败结果
Then result 必须返回 `result_status=failed` 与 `error_classification=signature_or_request_invalid`，且不得降级为 `parse_failed`、`platform_failed` 或 `provider_or_network_blocked`

## 异常与边界场景

- 异常场景：
  - raw creator response 缺少 creator identity 或 public display family 时，必须按 `parse_failed` fail-closed，不得伪造 public profile。
  - raw media response 缺少 media ref、content type 或 fetch outcome family 时，必须按 `parse_failed` fail-closed。
  - unsupported 或无法稳定识别的 content type 必须优先归类为 `unsupported_content_type`，不得伪装成 image/video。
  - 已识别且受支持的 content type 被 `allowed_content_types` 排除时，必须归类为 `fetch_policy_denied`，不得误报 `unsupported_content_type`。
  - fetch policy 不允许下载时，必须返回 `fetch_policy_denied` 或 allowed non-download outcome，不得隐式下载。
  - `download_required` 被 policy/cost boundary 拒绝时必须返回 `fetch_policy_denied`；`download_if_allowed` 不下载时只能降级为 `source_ref_preserved`。
  - 不能满足 source ref lineage 的请求必须 fail-closed 为 `fetch_policy_denied`。
  - rate-limit、permission-denied、provider/network-blocked、signature/request-invalid 必须保持为独立公共错误分类。
- 边界场景：
  - `target_not_found` 与 `profile_unavailable` 必须区分；creator 存在但不可查看不是 not found。
  - `profile_unavailable` 与 `permission_denied` 必须互斥；前者表示 profile 的公共可用性边界，后者表示当前 requester/resource 的访问权限边界。
  - `media_unavailable` 与 `unsupported_content_type` 必须区分；media 存在但类型不支持不是 unavailable。
  - `mixed_media`、live-photo-like 或 component media shape 不在本 FR 的 stable public content type 范围；如无法投影为 `image` 或 `video`，必须 fail-closed 到 `unsupported_content_type`。
  - `unsupported_content_type` 表示 Adapter 无法稳定投影为公共 content type；`fetch_policy_denied` 表示公共 content type 已识别但被 request policy、download policy 或 source-ref preservation policy 拒绝。
  - `metadata_only`、`source_ref_preserved` 与 `downloaded_bytes` 是 fetch outcome，不是 storage lifecycle。
  - `metadata_only` 与 `source_ref_preserved` 不得返回 `byte_size`、`checksum_digest`、`checksum_family`、storage handle 或下载证明；这些下载事实只能出现在 `downloaded_bytes`。
  - public media metadata 只能使用 data model 白名单字段；平台 media schema、provider routing、storage handle、raw headers/body、signed URL、session 或 credential 字段不得进入 public metadata。
  - creator profile 与 media asset fetch 可共享 source trace、raw payload ref 与 error classification vocabulary，但不能强迫两个 operation 共享同一个 normalized result schema。
  - `result_status=unavailable` 或 `failed` 时，`profile` / `media` 字段必须存在且为 `null`；`raw_payload_ref` 在没有稳定 raw payload 时也必须为 `null`。
  - `error_classification` 到 `result_status` 必须遵守 data model 的强制映射；success 必须使用 `error_classification=null`。
  - `source_ref_lineage` 是 media result 的公共审计 carrier；`source_trace` 只表达执行来源，不替代 media ref lineage。
  - `provider_or_network_blocked` 必须使用脱敏 blocked-path alias 填充 `source_trace.provider_path`，不得暴露 provider routing、fallback 或 selector details。
  - `fetch_outcome=downloaded_bytes` 必须具备 `byte_size`、`checksum_digest` 与 `checksum_family`；可审计下载证明只能进入 audit evidence，不能成为 normalized media descriptor 或 result-query consumer 可依赖的 bytes handle。
  - `#405` 不要求两个平台拥有完全一致 raw creator/media shape，只要求 Adapter 能把它们投影到同一公共 envelope。

## 验收标准

- [ ] formal spec 冻结 `creator_profile_by_id` 与 `media_asset_fetch_by_ref` 的 public read contract。
- [ ] formal spec 冻结 creator target、public profile result、media asset ref、media fetch result、content type、fetch policy、fetch outcome、source trace、raw payload reference 与 result status。
- [ ] formal spec 明确 `target_not_found`、`profile_unavailable`、`media_unavailable`、`unsupported_content_type`、`permission_denied`、`rate_limited`、`platform_failed`、`provider_or_network_blocked`、`parse_failed`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`、`fetch_policy_denied` 的公共边界。
- [ ] formal spec 明确 synthetic fixture 只能从 recorded raw shape 派生，且所有 evidence source 只能使用脱敏 alias。
- [ ] formal spec 明确 Adapter 负责平台 creator/profile/media/content-type/fetch projection，Core 不得接收平台私有对象。
- [ ] formal spec 明确 Core 不拥有 media storage、asset lifecycle、thumbnail/transcode 或内容库产品行为。
- [ ] formal spec 明确 `content_detail_by_url` 与 `#403` collection envelope 语义不受本 FR 改写。
- [ ] 本事项不修改 runtime、tests implementation、raw fixture payload files 或 release closeout truth。

## 依赖与外部前提

- 外部依赖：
  - `v1.1.0` operation taxonomy foundation 已发布。
  - `v1.2.0` resource governance foundation 已发布。
  - `v1.3.0` read-side collection foundation 已发布。
  - `#405` 已显式绑定 `v1.5.0 / 2026-S25`。
- 上下游影响：
  - 后续 `#422/#423` runtime carrier Work Item 必须消费本 FR，并先补齐 canonical taxonomy / requirement / offer / compatibility decision admission 输入域，而不是重新定义 creator/media result envelope 或错误分类。
  - 后续 `#424` consumer migration 必须保留 `#403` collection 与 `content_detail_by_url` regression，并在执行前消费 `#404` shared runtime conflict-risk clearance。
  - 后续 `#425` evidence Work Item 必须使用本 FR 的 sanitized fixture matrix，不得提交 raw payload files 或 source mapping。
