# FR-0403 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| collection contract 吸收 comment/media/profile 特有语义 | `#404/#405` 边界失真，FR-0403 变成 Phase 3 大一统 contract | spec 明确 FR-0403 只覆盖 search/list collection foundation，评论层级与媒体边界另建 FR | revert 越界 spec 段落，并在 #404/#405 重新冻结对应 contract |
| 平台 continuation shape 泄漏到 Core | Core 被迫理解 page、offset、search session 或 cursor object，破坏平台中立性 | spec 明确 continuation token 只允许平台中立 carrier，Adapter 负责 encode/decode | revert runtime consumer 或 spec drift，恢复 continuation token 边界 |
| `empty_result` 与 `target_not_found` 混淆 | 上层 consumer 无法区分“合法无结果”和“目标不存在” | spec 明确两者是不同公共结果边界，并要求 fixture matrix 独立覆盖 | 回退错误 consumer 实现，补充独立测试与 evidence |
| `credential_invalid` 被降级为 `platform_failed` | Phase 2 resource governance 边界被打穿，read-side admission 与平台失败混杂 | spec 明确 `credential_invalid` 与 `verification_required` 必须 fail-closed 并对齐 `v1.2.0` | revert 错误映射，实现回到 resource-governance 边界 |
| 脱敏失败导致外部来源名或路径进入仓库/GitHub truth | 后续 release/sprint/spec truth 被污染，增加治理噪音 | artifact/spec/release/sprint 统一使用 source alias，并在验证中加入 sanitization search | revert 污染文档与 PR/issue 文本，重写为 alias-only 版本 |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
- [ ] spec 未修改 runtime、tests implementation 或 release closeout truth
- [ ] spec 未记录外部项目名或本地路径
- [ ] spec 未把 `v1.3.0` 写成整个 Phase 3 的 release 绑定
