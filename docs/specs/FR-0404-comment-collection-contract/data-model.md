# FR-0404 数据模型

## CommentTarget

- 用途：表达 `comment_list_by_content` 的公共 target。
- 最小字段：
  - `operation`
  - `target_type`
  - `target_ref`
  - `target_display_hint`（可选）
  - `policy_ref`（可选）
- 约束：
  - `comment_list_by_content` 的 target 必须表达 content public identifier，而不暴露平台 comment page object。
  - thread-scoped reply loading 必须通过 item-level `reply_cursor` 继续，不得扩展出新的 target admission surface。

## CommentContinuation

- 用途：表达 top-level page 或 reply window 的 continuation input/output。
- 最小字段：
  - `continuation_token`
  - `continuation_family`
  - `resume_target_ref`
  - `resume_comment_ref`（可选）
  - `issued_at`（可选）
- 约束：
  - 可以承载 opaque cursor，也可以承载 page/offset/thread-session 等平台私有组合的 Adapter-encoded token。
  - Core 不得直接理解平台私有 continuation 字段。
  - continuation 与 target 必须绑定；跨 target 复用必须视为 invalid/expired。
  - `resume_comment_ref` 为空时表示 top-level page continuation。
  - `resume_comment_ref` 非空时表示 reply-window continuation，并必须与同一 comment thread 绑定。

## CommentRequestCursor

- 用途：表达 `comment_list_by_content` 请求侧的可选 cursor 输入。
- 最小字段：
  - `cursor_kind`
  - `cursor_payload`
- 约束：
  - `cursor_kind` 只能是 `page_continuation` 或 `reply_cursor`。
  - `cursor_payload` 分别承载 `CommentContinuation` 或 `CommentReplyCursor`。
  - 同一请求最多只能携带一个 `CommentRequestCursor`。
  - `cursor_kind=reply_cursor` 时，请求仍必须保留 content-scoped `CommentTarget`。
  - `cursor_kind=page_continuation` 可同时用于 top-level page 与 reply-window continuation。

## CommentReplyCursor

- 用途：表达某个 comment item 的 nested reply continuation。
- 最小字段：
  - `reply_cursor_token`
  - `reply_cursor_family`
  - `resume_target_ref`
  - `resume_comment_ref`
  - `issued_at`（可选）
- 约束：
  - reply cursor 只用于进入某条 comment 的首个 reply window。
  - reply cursor 可以由 comment-id、reply-offset、thread-session 等平台私有字段组合编码，但 Core 只消费平台中立 token。
  - `resume_target_ref` 必须与请求 target 的 `target_ref` 一致。
  - `resume_comment_ref` 与 comment item public ref 不一致时必须视为 invalid/expired。

## CommentCollectionResultEnvelope

- 用途：表达 read-side comment collection 的公共结果。
- 最小字段：
  - `operation`
  - `target`
  - `items`
  - `has_more`
  - `next_continuation`
  - `result_status`
  - `error_classification`
  - `raw_payload_ref`
  - `source_trace`
  - `audit`
- 约束：
  - `result_status` 至少支持 `complete`、`empty`、`partial_result`。
  - `error_classification` 复用 `FR-0403` vocabulary，不新增 comment-only collection-level 分类。
  - 合法空结果必须显式使用 `result_status=empty` 且 `error_classification=empty_result`。
  - `empty_result` 不等于 `target_not_found`。
  - `has_more=false` 时允许 `next_continuation` 为空。
  - reply window 如仍有更多数据，必须通过 `next_continuation` 继续，而不是要求再次消费旧的 item-level `reply_cursor`。
  - `raw_payload_ref` 只能引用原始载荷，不承载 raw payload 内联内容。

## CommentItemEnvelope

- 用途：表达 comment collection 内每个 item 的公共封装。
- 最小字段：
  - `item_type`
  - `dedup_key`
  - `source_id`
  - `source_ref`
  - `visibility_status`
  - `normalized`
  - `raw_payload_ref`
  - `source_trace`
  - `reply_cursor`（可选）
- 约束：
  - `dedup_key` 必须稳定，且不要求两个平台使用相同原始 comment ID 字段。
  - `visibility_status` 至少支持 `visible`、`deleted`、`invisible`、`unavailable`。
  - `reply_cursor` 仅在 comment item 可继续加载 replies 时出现。
  - `unavailable` item 仍必须能提供最小 normalized placeholder projection，例如稳定的 `canonical_ref`、`root_comment_ref` 与 placeholder `body_text_hint`。
  - `normalized` 是 Core 可消费内容；平台私有字段不得直接进入 item envelope 顶层。

## NormalizedCommentItem

- 用途：表达跨平台最小稳定 comment 字段集合。
- 最小字段：
  - `source_platform`
  - `source_type`
  - `source_id`
  - `canonical_ref`
  - `body_text_hint`
  - `root_comment_ref`
  - `author_ref`（可选）
  - `parent_comment_ref`（可选）
  - `target_comment_ref`（可选）
  - `published_at`（可选）
- 约束：
  - top-level comment 的 `root_comment_ref` 必须等于自身 `canonical_ref`。
  - reply comment 的 `root_comment_ref` 必须稳定指向 thread root。
  - `parent_comment_ref` 指向直接 parent comment；top-level comment 不要求该字段。
  - `target_comment_ref` 仅在 reply 明确指向某个目标 comment 时出现。
  - `body_text_hint` 对 `unavailable` item 也必须存在，但允许是平台 unavailable placeholder 的最小公共投影，而不是完整正文。
  - 缺少可选字段不会使 item invalid。

## CommentVisibilityStatus

- 用途：表达 item-level 可见性与删除边界。
- 最小分类：
  - `visible`
  - `deleted`
  - `invisible`
  - `unavailable`
- 约束：
  - `deleted` 表示 comment existed but platform marks it deleted。
  - `invisible` 表示 comment exists but is hidden for current viewer。
  - `unavailable` 表示 comment slot exists，但只保留最小 public placeholder projection，完整正文不可用。
  - visibility status 不是 collection-level error classification 的替代物。

## SourceTrace

- 用途：表达 item 与 collection 的来源追溯信息。
- 最小字段：
  - `adapter_key`
  - `provider_path`
  - `resource_profile_ref`（可选）
  - `fetched_at`
  - `evidence_alias`
- 约束：
  - 只能记录脱敏 alias，不得记录外部项目名或本地路径。
  - 必须足以追溯到本次 comment result 所属的 raw payload family。

## CommentErrorClassification

- 用途：表达 comment collection-level 公共错误分类。
- 最小分类：
  - `empty_result`
  - `target_not_found`
  - `rate_limited`
  - `permission_denied`
  - `platform_failed`
  - `provider_or_network_blocked`
  - `cursor_invalid_or_expired`
  - `parse_failed`
  - `partial_result`
  - `credential_invalid`
  - `verification_required`
  - `signature_or_request_invalid`
- 约束：
  - deleted/invisible/unavailable 必须留在 item-level visibility，而不是提升为 collection-level error classification。
  - `credential_invalid` 与 `verification_required` 必须与 `v1.2.0` resource governance 边界兼容。
  - partial page 固定使用 `result_status=partial_result` 与 `error_classification=parse_failed`；`partial_result` 继续保留为继承词表的兼容 entry，但不是本 FR 新增的 emitted error classification。

## 生命周期

- 创建：
  - `CommentTarget` 由 task admission 输入创建。
  - `CommentCollectionResultEnvelope` 由 Adapter 完成 raw-to-normalized projection 后返回。
  - `CommentContinuation` 在 `has_more=true` 时由 Adapter 生成平台中立 token。
  - `CommentReplyCursor` 在 comment item 允许进入 replies 时由 Adapter 生成。
- 更新：
  - 新页面结果使用新的 `next_continuation`；不得原地篡改历史 continuation 以伪造跨页稳定性。
  - 进入首个 reply window 使用 `reply_cursor`；后续 reply page 使用新的 `next_continuation`，不得把某个 comment 的 cursor/continuation 迁移到另一 comment。
  - `partial_result` 允许追加 item-level parse-failure evidence，但固定搭配 `error_classification=parse_failed`，且不得改写成功 normalized comments 的公共字段。
- 失效/归档：
  - invalid/expired continuation、reply cursor 或 reply-window continuation 只能导向 `cursor_invalid_or_expired`，不应被当作普通 platform failure。
  - raw payload refs 的持久化/归档策略不在本 FR 范围内。
