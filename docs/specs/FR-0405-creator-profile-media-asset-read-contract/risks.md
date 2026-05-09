# FR-0405 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| creator profile contract 吸收平台私有画像字段 | Core 被迫理解平台账号画像或风控字段，破坏 public profile boundary | spec 明确只允许 public normalized profile fields，私有字段只能保留在 raw payload 或 Adapter-managed extension | revert 越界 spec/runtime consumer，并恢复 public-only profile result |
| media asset fetch 演化成媒体库或资产存储产品 | Core 产生 storage lifecycle、retention、thumbnail/transcode 等产品责任 | spec 明确 fetch outcome 只表达 metadata/source-ref/download boundary，不拥有 storage lifecycle | revert storage/product 语义，拆成单独 FR 重新评审 |
| unsupported content type 被伪装成 image/video | consumer 得到错误媒体类型，后续 dataset/batch 产生不可恢复污染 | spec 明确 `unsupported_content_type` 独立分类，并要求 fail-closed | 回退错误投影，实现回到 unsupported boundary |
| fetch policy 被 Provider 私有策略覆盖 | Core 无法治理 download/no-download 与大文件成本边界 | spec 明确 fetch policy 是公共 request boundary，Provider 只能执行不定义 vocabulary | revert provider-driven policy drift，补充 compatibility test |
| `credential_invalid` 被降级为 `platform_failed` | Phase 2 resource governance 边界被打穿，read-side admission 与平台失败混杂 | spec 明确 `credential_invalid` 与 `verification_required` 必须 fail-closed 并对齐 `v1.2.0` | revert 错误映射，实现回到 resource-governance 边界 |
| 与并行 `#404` runtime/consumer 改动冲突 | shared TaskRecord/result query/compatibility paths 产生重复或不兼容 migration | `#421` 仅做 spec；`#422/#423/#424` 必须等待 predecessor gates 与 shared runtime conflict-risk clearance | 暂停 runtime Work Item，等待 #404 closeout 或创建专门 reconciliation Work Item |
| 脱敏失败导致外部来源名或路径进入仓库/GitHub truth | 后续 release/sprint/spec truth 被污染，增加治理噪音 | artifact/spec/release/sprint 统一使用 source alias，并在验证中加入 sanitization search | revert 污染文档与 PR/issue 文本，重写为 alias-only 版本 |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
- [ ] spec 未修改 runtime、tests implementation 或 release closeout truth
- [ ] spec 未记录外部项目名或本地路径
- [ ] spec 未把 `v1.5.0` 写成整个 Phase 3 的 release 绑定
- [ ] spec 未把 media fetch 写成 Core media storage/product lifecycle
