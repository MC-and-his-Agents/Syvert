# FR-0404 Comment collection contract

## 关联信息

- item_key：`FR-0404-comment-collection-contract`
- Issue：`#404`
- item_type：`FR`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`

## 背景与目标

- 背景：`v1.3.0` 已冻结 `content_search_by_keyword` 与 `content_list_by_creator` 的 collection result contract，但评论读取仍停留在 proposed taxonomy candidate，尚未统一表达 comment target、reply hierarchy、reply cursor、deleted/invisible visibility、raw/normalized 双轨与 comment-level collection failure boundary。
- 目标：冻结 `v1.4.0` 首个 comment collection formal spec，定义 `comment_collection` 的公共 target、result envelope、page continuation、reply cursor、comment item envelope、visibility status、root/parent/target linkage、source trace 与平台中立错误分类，为后续 runtime carrier、consumer migration、evidence 与 release closeout 提供 formal spec 输入。

## 范围

- 本次纳入：
  - `comment_collection` 的公共 operation contract。
  - comment target、page continuation、comment result envelope、comment item envelope、reply cursor、raw payload reference、normalized comment item、dedup key、source trace、audit fields。
  - first page、next page、empty result、target not found、reply hierarchy、deleted/invisible/unavailable comments、duplicate comment item、continuation invalidation、permission denied、rate limited、platform/provider failure、parse failure、partial result、credential invalid、verification required 的公共边界。
  - Adapter 对平台 comment identity、parent/reply identifiers、cursor fields与 visibility flags 的投影边界。
- 本次不纳入：
  - runtime carrier implementation。
  - fake/reference/raw fixture payload files。
  - creator profile shape、media download/no-download boundary。
  - batch execution、dataset sink、scheduled execution、provider selector、fallback、marketplace、上层内容库或分析产品。
  - `content_detail_by_url` stable baseline 改写。
  - `FR-0403` collection public behavior 改写。

## 需求说明

- 功能需求：
  - Core 必须能表达 `comment_collection` 的 content-scoped target 与 page continuation input，而不理解平台私有 comment page object、reply cursor object、moderation object 或 platform-private thread model。
  - `comment_collection` 的后续请求输入固定为 `target + request_cursor` 组合：`request_cursor` 可以为空、可以设置 `page_continuation`，也可以设置某条 comment item 产出的 `reply_cursor`。
  - result envelope 的 `next_continuation` 是下一次 request 的 `request_cursor.page_continuation` 的唯一来源；consumer 必须原样转交公共 carrier，不得重命名、拆解或替换为平台私有 cursor 字段。
  - comment result 必须包含 `items`、`has_more`、`next_continuation`、`result_status`、`error_classification`、`raw_payload_ref`、`source_trace` 与审计字段，并复用 `FR-0403` 的 collection envelope 基础语义。
  - 每个 comment item 必须可同时保留 raw payload reference 与 normalized comment projection；Core 只能消费 normalized envelope，不消费平台私有 raw 字段。
  - 每个 comment item 必须能表达 `visibility_status`、`root_comment_ref`、`parent_comment_ref`、`target_comment_ref` 与可选 `reply_cursor`。
  - comment contract 必须能表达 `complete`、`empty`、`partial_result` 三种结果状态。
  - top-level page continuation 与 item-level reply cursor 既可以来自 opaque cursor，也可以来自 page/offset/thread-session 等平台私有组合，但 Core 只接收平台中立 token carrier。
- 契约需求：
  - `comment_collection` 投影到 `comment_collection + content + single + paginated`，不额外引入 thread-scoped admission target。
  - `comment_collection` 同时沿用当前 canonical taxonomy candidate 的 public operation 名称与 adapter-facing capability family；后续若要拆分为更具体的 operation 名，必须另走 taxonomy promotion / compatibility migration，不在本 Work Item 中完成。
  - comment result envelope 复用 `FR-0403` 的 `result_status` 与 `error_classification` 基础 vocabulary，并为 `comment_collection` 新增 comment-specific success sentinel：`success`。`success` 只表示非空正常成功页，不进入 `FR-0403` 共享 collection vocabulary。
  - `visibility_status` 至少支持：`visible`、`deleted`、`invisible`、`unavailable`。
  - 请求侧 `request_cursor` 在同一请求中只能二选一：要么通过 `page_continuation` 继续上一页 result 的 `next_continuation`，要么继续某条 comment item 的 `reply_cursor`；两者同时出现必须 fail-closed 到 `signature_or_request_invalid`。
  - collection-level错误分类 vocabulary 继承 `FR-0403`，至少保留：`empty_result`、`target_not_found`、`rate_limited`、`permission_denied`、`platform_failed`、`provider_or_network_blocked`、`cursor_invalid_or_expired`、`parse_failed`、`partial_result`、`credential_invalid`、`verification_required`、`signature_or_request_invalid`；`comment_collection` 额外允许 emitted `success` 作为非错误 success sentinel。
  - `result_status=complete` 既可表示成功页面，也可表示 fail-closed 的 collection-level failure envelope。非空正常成功页必须使用 `result_status=complete` 与 `error_classification=success`；`success` 不得用于 `empty`、`partial_result`、零 item success 或任何 fail-closed envelope。
  - `target_not_found`、`permission_denied`、`rate_limited`、`platform_failed`、`provider_or_network_blocked`、`cursor_invalid_or_expired`、`credential_invalid`、`verification_required`、`signature_or_request_invalid` 都固定使用 `result_status=complete`。
  - collection-level failure envelope 必须统一返回 `items=[]`、`has_more=false`、`next_continuation=null`；不得在 failure envelope 中继续携带可执行 continuation 或伪正常 comment item。
  - collection-level failure envelope 仍必须保留 `raw_payload_ref` 与 `source_trace` 审计载体；若失败发生在稳定 raw payload 之前，这些字段必须指向 failure evidence / provider trace alias，而不是平台 raw object。
  - 本 FR 允许 emitted 的 `error_classification` 集合不单独发出 `partial_result`；partial page 固定使用 `result_status=partial_result` 与 `error_classification=parse_failed` 的组合语义。`partial_result` 继续保留在继承词表中作为兼容 vocabulary entry。
  - `credential_invalid` 与 `verification_required` 必须保持 fail-closed，并与 `v1.2.0` resource governance 边界一致，不得被降级成普通 `platform_failed`。
  - item-level `reply_cursor` 只用于进入某条 comment 的首个 reply window；若 reply window 仍有更多数据，后续续拉必须通过 `next_continuation` 完成。
  - public comment ref 的唯一绑定对象是 `NormalizedCommentItem.canonical_ref`；`reply_cursor.resume_comment_ref`、reply-window `next_continuation.resume_comment_ref`、`root_comment_ref`、`parent_comment_ref` 与 `target_comment_ref` 都必须引用该 ref。
  - `source_id` 继续保留为 `FR-0403` collection item identity 基线；deleted/invisible/unavailable placeholder 缺少稳定平台 id 时，不得伪造平台原生 id，必须使用 public placeholder namespace 的确定性 `source_id` 与 `canonical_ref`。
  - `source_ref` 只用于 source trace / audit，不得作为 reply resume、hierarchy linkage 或 dedup 的规范绑定对象。
  - `reply_cursor` 与 reply-window `next_continuation` 都只能恢复同一 content target 下、同一 `canonical_ref` comment item 的 replies；跨 comment 或跨 content target 复用必须视为 invalid/expired。
  - `content_detail_by_url` baseline 与 `FR-0403` collection public behavior 不得因 comment contract 引入新的 Core 分支或平台私有字段。
- 非功能需求：
  - comment contract 必须 fail-closed；无法证明 hierarchy、continuation、reply cursor、visibility 或 raw/normalized 投影合法时，不得返回伪稳定结果。
  - malformed comment response 不得引入新的未定义公共错误分类；本 FR 中此类 fail-closed 路径统一收敛到已定义的 `parse_failed`。
  - repository 与 GitHub truth 不得记录外部样本项目名或本地路径；所有 evidence source 只能使用脱敏 alias。
  - synthetic fixture 只能从 recorded raw shape family 派生，不得凭空发明平台字段。
  - `model_covered_raw_gap` 只能作为 research input 与 `#419` evidence planning 输入，不得作为当前 formal spec 的第二参考平台 recorded proof，也不得支撑 implementation-ready claim。

## 约束

- 阶段约束：
  - `v1.4.0` 当前只绑定 `#404` 的 comment-collection slice，不绑定整个 Phase 3。
  - 本 Work Item 只交付 Batch 0 inventory 与 Batch 1 formal spec；runtime、consumer migration、evidence、release closeout 必须另建 Work Item。
- 架构约束：
  - Core 只理解 public operation、comment target、page continuation、reply cursor、result envelope、visibility status、dedup key、source trace 与 error classification。
  - Adapter 负责平台 comment identifiers、parent/reply semantics、platform cursor shape、platform visibility shape 与 normalized comment projection。
  - Provider 负责实际 HTTP、浏览器、签名或第三方执行路径，不定义 Syvert 的 comment vocabulary。
  - raw payload 只能作为审计/调试引用存在，不能成为 Core public decision fields。

## GWT 验收场景

### 场景 1：评论第一页返回完整 collection result

Given `comment_collection` 使用合法 content target，且 Adapter 可以从 reference platform A 投影 recorded first-page comment response
When Core 执行 comment collection request
Then result 返回 `items`、`has_more=true`、`next_continuation`、`result_status=complete`、`error_classification=success`、`raw_payload_ref` 与 normalized comment list，且不暴露平台私有 thread 或 moderation object

### 场景 2：下一页 continuation 保持公共语义稳定

Given `comment_collection` 已返回第一页并生成 result `next_continuation`
When Core 将该 carrier 作为下一次 request 的 `request_cursor.page_continuation` 请求下一页，且平台实际需要 page/offset/thread-session 组合
Then Adapter 负责还原平台 continuation，Core 仍只接收平台中立 continuation token，且 comment item envelope 与错误边界保持不变

### 场景 3：reply cursor 只恢复同一 comment 的 replies

Given 某个 top-level comment item 返回 `reply_cursor`
When Core 继续拉取该 comment 的 replies
Then Adapter 只允许在同一 comment 上恢复 nested reply window，且 `reply_cursor.resume_comment_ref` 与当前 comment 的 `canonical_ref` 保持一致

### 场景 3B：reply cursor 请求与 top-level continuation 互斥

Given 同一请求的 `request_cursor` 同时携带 `page_continuation` 与某条 comment item 的 `reply_cursor`
When Core 尝试执行该 comment request
Then request 必须 fail-closed 到 `result_status=complete` 与 `error_classification=signature_or_request_invalid`，而不是让 Adapter 自行猜测优先级

### 场景 3C：reply page 的后续翻页通过 next_continuation 继续

Given 某条 comment 的首个 reply page 返回后仍有更多 replies
When Adapter 返回下一次可用的公共 continuation
Then result 必须通过 `next_continuation` 返回后续翻页 carrier，并保留与同一 `resume_target_ref` / `resume_comment_ref` 的绑定

### 场景 4：空评论结果不会伪装成错误

Given `comment_collection` 命中合法 content target，但当前无评论
When Core 执行 comment collection request
Then result 返回 `items=[]`、`result_status=empty`、`error_classification=empty_result`，且不得被分类为 `target_not_found` 或 `platform_failed`

### 场景 5：目标不存在必须独立分类

Given `comment_collection` 使用的 content target 在平台上不存在或已不可解析
When Core 执行 comment collection request
Then result 必须返回 `result_status=complete` 与 `error_classification=target_not_found`，且不得被降级成 `empty_result`

### 场景 6：deleted/invisible comment 作为 item-level visibility 保留

Given 一页评论中同时包含正常 comment item 与 deleted/invisible placeholder
When Core 处理该页 comment result
Then deleted/invisible item 通过 `visibility_status` 表达，且合法页面仍可返回 `result_status=complete` 与 `error_classification=success`

### 场景 6B：unavailable comment 保留为 item-level visibility

Given 一页评论中出现 comment placeholder，当前 payload 无法提供完整 body projection，但仍保留稳定 unavailable marker 与最小 placeholder text
When Adapter 仍能证明该 comment slot 属于同一合法页面
Then item 必须返回 `visibility_status=unavailable` 与最小 normalized placeholder projection；若平台未提供稳定 comment id，`source_id` 必须使用 public placeholder namespace，并由 operation、target、visibility 与独立稳定 placeholder marker 派生，且不得依赖 continuation、window slot、raw payload ref、source trace 或 fetched timestamp

### 场景 7：reply hierarchy 保留 root/parent/target linkage

Given 一条 reply 同时能识别 root comment、直接 parent comment 与 target comment
When Adapter 投影 normalized comment item
Then public item 必须保留 `root_comment_ref`、`parent_comment_ref` 与 `target_comment_ref`，这些 ref 都绑定到对应 comment 的 `canonical_ref`，而不要求 Core 理解平台私有 reply object

### 场景 7B：duplicate comment item 保持稳定 dedup 语义

Given 同一逻辑 comment item 出现在连续页面或 reply window 中
When Adapter 为这些 comment item 分别投影 public envelope
Then comment contract 必须生成稳定 `dedup_key`，且不要求 Core 理解平台私有 comment object name 或 comment ID 体系

### 场景 8：部分 comment 解析失败时返回 partial result

Given 一页 raw response 中部分 comment 可投影，部分 comment 因 shape drift 解析失败
When Core 处理该页 comment result
Then result 返回 `result_status=partial_result` 与 `error_classification=parse_failed`，保留成功 normalized comments

### 场景 9：continuation 或 reply cursor 失效有独立错误边界

Given next-page continuation token 或 reply cursor 已失效
When Adapter 还原 continuation 并请求后续页面
Then result 必须返回 `result_status=complete` 与 `error_classification=cursor_invalid_or_expired`，而不是 generic `platform_failed`

### 场景 9B：reply cursor 跨 target 复用必须失败

Given 某条 comment item 产出的 `reply_cursor` 被拿去请求另一 content target 的 replies
When Core 或 Adapter 校验请求上下文
Then result 必须返回 `result_status=complete` 与 `error_classification=cursor_invalid_or_expired`

### 场景 10：permission denied 保持独立 collection-level 错误

Given content target 存在，但当前 viewer 或 account 不具备评论访问权限
When Core 执行 comment collection request
Then result 必须返回 `result_status=complete` 与 `error_classification=permission_denied`，且不得伪装成 `empty_result`

### 场景 11：rate limited 保持独立 collection-level 错误

Given 平台在加载评论时触发访问频率或 anti-abuse 限流
When Core 执行 comment collection request
Then result 必须返回 `result_status=complete` 与 `error_classification=rate_limited`，且不得与 `platform_failed` 混淆

### 场景 12：platform/provider failure 保持独立 collection-level 错误

Given 平台上游失败或 provider/network path 被阻断，且不存在更强分类
When Core 执行 comment collection request
Then result 必须固定使用 `result_status=complete`，并分别归类为 `platform_failed` 或 `provider_or_network_blocked`

### 场景 13：整页 parse failure 使用 fail-closed envelope

Given comment response 缺少 comment identity、items family，或在 `has_more=true` 时缺少 continuation family，导致整页无法建立任何 public projection
When Core 处理该页 comment result
Then result 必须 fail-closed 到 `result_status=complete`、`error_classification=parse_failed`、`items=[]`、`has_more=false`，且不得返回 `next_continuation`

### 场景 14：resource health 与 verification 保持 fail-closed

Given comment request 依赖的 account session 已 invalid，或平台要求验证码/安全验证
When Core 处理 admission 或 Adapter 返回 verification-required signal
Then result 必须分别返回 `result_status=complete` 与 `error_classification=credential_invalid` 或 `verification_required`，并保持 fail-closed，不得继续返回伪正常 comment items

## 异常与边界场景

- 异常场景：
  - raw response 缺少 `items` family 或 comment identity family 时，必须按 `parse_failed` fail-closed。
  - raw response 声明 `has_more=true` 但缺少 page continuation family 时，必须按 `parse_failed` fail-closed；`has_more=false` 的终页不得因缺少 continuation 被视为 malformed。
  - comment item 声明可以继续 replies 但缺少 reply cursor family 时，必须按 `parse_failed` fail-closed；不可继续 replies 的叶子 comment 不要求 `reply_cursor`。
  - page continuation、reply cursor 或 reply-window continuation 与 target/comment 上下文不匹配时，必须返回 `cursor_invalid_or_expired`。
  - rate-limit、permission-denied、provider/network-blocked、signature/request-invalid 必须保持为独立公共错误分类。
  - raw payload present 但部分 normalized comment 缺少最小必需字段，且该页至少保留一个成功 normalized comment 时，必须进入 `result_status=partial_result + error_classification=parse_failed` 路径。
  - raw payload present 但零成功投影时，必须进入 `result_status=complete + error_classification=parse_failed` fail-closed 路径，返回 `items=[]` 且不得携带 `next_continuation`。
- 边界场景：
  - `target_not_found` 与 `empty_result` 必须区分；合法 content target 没有评论不是 not found。
  - deleted/invisible/unavailable 是 item-level visibility，不等于 collection-level failure。
  - top-level page continuation 与 reply cursor 可以拥有不同 token family，但都必须保持平台中立 carrier。
  - `comment_collection` 复用 `FR-0403` 的 collection envelope、source trace、raw/normalized、result status 与 error classification 语义，但不得回写或改写 `content_search_by_keyword` / `content_list_by_creator` 的 public behavior。

## 验收标准

- [ ] formal spec 冻结 `comment_collection` 的 comment collection contract。
- [ ] formal spec 冻结 comment target、page continuation、reply cursor、comment item envelope、visibility status、source trace、raw payload reference 与 result status。
- [ ] formal spec 冻结 `comment_collection` 的请求侧 cursor 规则，明确 result `next_continuation` 到 request `page_continuation` 的映射，以及 `page_continuation` 与 `reply_cursor` 的组合/互斥边界。
- [ ] formal spec 冻结 `visible`、`deleted`、`invisible`、`unavailable` 四类 item-level visibility 语义。
- [ ] formal spec 明确继承 vocabulary 与允许 emitted 的 `error_classification` 边界，写清 `success` 只作为 `comment_collection` 非空 `complete` 成功页 sentinel，且 `partial_result` 只作为结果状态组合语义保留。
- [ ] formal spec 明确 `duplicate comment item` 与 `dedup_key` 的稳定去重边界，至少覆盖跨页与 reply window。
- [ ] formal spec 明确 synthetic fixture 只能从 recorded raw shape 派生，且所有 evidence source 只能使用脱敏 alias。
- [ ] formal spec 明确第二参考平台 raw gap 由 `#419` 关闭，当前 Work Item 不宣称跨平台 recorded proof 已完成。
- [ ] formal spec 明确 Adapter 负责平台 comment hierarchy/cursor/visibility projection，Core 不得接收平台私有对象。
- [ ] formal spec 明确 `content_detail_by_url` baseline 与 `FR-0403` collection public behavior 不受本 FR 改写。
- [ ] 本事项不修改 runtime、tests implementation、raw fixture payload files 或 release closeout truth。

## 依赖与外部前提

- 外部依赖：
  - `v1.1.0` operation taxonomy foundation 已发布。
  - `v1.2.0` resource governance foundation 已发布。
  - `v1.3.0` read-side collection foundation 已发布。
- 上下游影响：
  - 后续 runtime carrier Work Item 必须消费本 FR，而不是重新定义 comment envelope 或 visibility 语义。
  - `#405` creator/media contract 应继续复用 `FR-0403` 的 collection-level基础边界，但不复用本 FR 的 comment hierarchy surface。
