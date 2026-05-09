# FR-0404 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| comment contract 直接复用 content item shape | comment hierarchy、visibility 与 reply cursor 无法进入公共 contract，后续 runtime 只能继续走平台私有字段 | spec 明确 comment item envelope、reply cursor 与 visibility status 是独立公共 surface | revert 错误 spec 段落，并在 `FR-0404` 重新冻结 comment-specialized data model |
| root/parent/target linkage 语义不清 | Adapter 可能为不同平台投影出互相不兼容的 reply hierarchy，consumer 无法稳定消费 | spec 明确 `canonical_ref` 是唯一公共 comment ref，`root_comment_ref`、`parent_comment_ref`、`target_comment_ref` 与 cursor resume 均绑定到该 ref | revert 含糊字段定义，补充更严格的 model/test requirement |
| placeholder 强制要求平台 source id | Adapter 会被迫伪造 unavailable/deleted/invisible 平台原生身份，或把可保留的 placeholder 错误降级成 parse failure | spec 保持 `source_id` 为 FR-0403 最小字段，但允许缺少平台稳定 id 的 placeholder 使用 public placeholder namespace 派生稳定 `source_id` 与 `canonical_ref` | revert 伪造平台 id 规则，补充 placeholder identity fixture/evidence |
| deleted/invisible 被误设计成 collection-level error | 混合页面无法保留有效 comments，runtime 会过度 fail-closed | spec 把 deleted/invisible/unavailable 固定为 item-level visibility 状态 | revert collection-level error drift，并补 item-level visibility 测试 |
| reply cursor shape 泄漏到 Core | Core 被迫理解 comment-id、reply-offset 或 thread-session 字段，破坏平台中立性 | spec 明确 reply cursor 只允许平台中立 carrier，Adapter 负责 encode/decode | revert runtime consumer 或 spec drift，恢复 reply cursor 边界 |
| comment dedup key 不稳定 | 跨页或跨 reply window 去重漂移，result query 与 evidence 难以复验 | spec 明确 dedup key 来自稳定公共语义，而非平台私有 comment object | revert 不稳定 dedup 设计，并补 duplicate fixture/evidence |
| 第二参考平台 raw gap 被误当作 recorded proof | 后续 evidence replay 可能推翻已冻结的跨平台 hierarchy / continuation 假设 | inventory 将 `model_covered_raw_gap` 限定为 research input，不作为 implementation-ready proof；`#419` 必须补齐 recorded 或等价 replayable evidence | revert 跨平台 proof claim，将差异回退到后续规约/evidence Work Item |
| 脱敏失败导致外部来源名或路径进入仓库/GitHub truth | 后续 release/sprint/spec truth 被污染，增加治理噪音 | artifact/spec/release/sprint 统一使用 source alias，并在验证中加入 sanitization search | revert 污染文档与 PR/issue 文本，重写为 alias-only 版本 |
| `FR-0403` 行为被顺手改写 | 已发布的 search/list contract 漂移，导致 `v1.3.0` published truth 失真 | spec 明确 `FR-0404` 只在 `FR-0403` collection foundation 上扩展 comment surface | revert 越界语义改动，并在 `#417/#418` 回归中保留 `FR-0403` tests |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
- [ ] spec 未修改 runtime、tests implementation 或 release closeout truth
- [ ] spec 未记录外部项目名或本地路径
- [ ] spec 未把 `v1.4.0` 写成整个 Phase 3 的 release 绑定
