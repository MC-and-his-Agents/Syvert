# FR-0387 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| secret 泄漏到 public metadata | cookie、token、header、session dump 或 sign payload 可能进入 registry、TaskRecord、AdapterRequirement 或 ProviderOffer | spec 明确 public carrier 默认脱敏，credential/session 私有字段不得进入 metadata 或 Core routing | revert 本 spec PR，并在后续 spec 中重新冻结 redaction boundary |
| health status 被误用为 provider SLA | `SessionHealth` 可能被错误理解为 provider 产品支持、成功率、routing 或 marketplace 信号 | spec 明确 health evidence 只用于 resource admission / invalidation，不参与 provider offer 或 compatibility matched | revert 错误 consumer migration，并保留本 spec 的 provider metadata 禁止边界 |
| invalidation 与既有 lifecycle 状态机冲突 | `SessionHealth=invalid` 可能被实现成第四种 resource status，破坏 `AVAILABLE / IN_USE / INVALID` | spec 明确 `SessionHealth` 是 evidence projection，最终状态仍通过 Core-owned release/invalidation 进入 `INVALID` | revert runtime carrier 中的状态集合扩张，恢复 FR-0010 状态机 |
| spec 越界进入自动恢复机制 | 本 FR 可能提前定义登录刷新、重新验证或后台修复，扩大 v1.2.0 scope | spec 明确 stale / invalid 只定义 admission 与 invalidation 边界，不定义修复流程 | revert 越界段落，后续恢复机制另建 FR |
| evidence 绑定不足 | 缺少 lease/task/resource 关联会导致错误资源被 invalidated | spec 要求 evidence 绑定 `resource_id`，并在执行上下文中绑定 lease/task/adapter/capability | revert 或修正 runtime implementation，使不完整 evidence fail-closed |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
- [ ] spec 未修改 runtime、tests、SDK 文档或 release index
- [ ] spec 未预创建后续 runtime/evidence/release Work Item
