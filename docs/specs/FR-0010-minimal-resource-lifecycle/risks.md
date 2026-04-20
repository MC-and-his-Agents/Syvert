# FR-0010 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| 把部分 slot 成功也视为 acquire 成功 | Core 与 Adapter 对“是否拿到完整执行资源”产生分叉真相 | formal spec 明确 acquire 只能整包成功或整包失败 | 回滚实现，恢复为整包 fail-closed 语义 |
| 在 lifecycle 主 contract 中提前引入能力匹配或浏览器资源 | `v0.4.0` scope 漂移，后续 FR 边界失控 | 只冻结 `account` / `proxy` 与最小 slot 语义，其他能力留到后续 FR | 回滚超范围字段与规则，恢复到最小资源模型 |
| `release` 的幂等与冲突语义不明确 | 重试、补偿与失败恢复时可能重复回收或错误失效资源 | formal spec 明确“相同语义 no-op，冲突语义 fail-closed” | 回滚冲突 release 行为，恢复单一一致的 lease 收口规则 |
| `INVALID` 被实现层偷偷恢复为 `AVAILABLE` | 失效资源可能被再次注入执行路径，破坏最小安全边界 | formal spec 把 `INVALID` 定义为 `v0.4.0` 终态 | 回滚非法恢复路径，后续如需恢复机制则通过新 FR 显式引入 |
| snapshot 写入 / bootstrap 并发语义不明确 | stale write、同值 replay 与冲突 bootstrap 可能覆写 durable truth | formal spec 明确 `revision` compare-and-swap、same-value replay/no-op 与 `resource_state_conflict` fail-closed 语义 | 回滚写入扩张，恢复到仅围绕 canonical snapshot truth 的最小约束 |
| bootstrap 允许写入无 active lease 可解释的 `IN_USE` 资源 | snapshot 可能出现无法被 lease truth 解释的占用态，导致生命周期真相自相矛盾 | formal spec 明确 `seed_resources(records)` 只允许注入 `AVAILABLE` / `INVALID`，并要求任何 `IN_USE` seed 在触达 durable truth 前 fail-closed | 回滚宽松 bootstrap 状态入口，恢复到“`IN_USE` 只能由 acquire + active lease 建立”的单一路径 |
| 空 store 读取若不回落 canonical 空 snapshot | lifecycle 默认本地入口可能在首次读取时分叉成 `null`、`{}` 或其他影子 carrier | formal spec 明确空 durable truth 固定回落 `ResourceLifecycleSnapshot(schema_version=v0.4.0, revision=0, resources=[], leases=[])` | 回滚影子初始化逻辑，恢复单一空快照基线 |
| bootstrap 单批重复 `resource_id` 未在触达 durable truth 前被拒绝 | 同一批次输入可能被静默去重、误判 replay，或留下部分写入结果 | formal spec 明确同批重复 `resource_id` 必须 pre-write fail-closed，不得去重、不得解释为 replay | 回滚宽松 bootstrap 行为，恢复到输入批次先校验、后写入的最小约束 |
| 把当前默认本地 JSON store 误写成唯一长期后端 | 后续 backend/path 演进被错误视为生命周期主 contract 破坏 | formal spec 只冻结默认本地入口的 traceability，不把单文件 JSON store 提升为唯一长期实现 | 回滚过强的 backend/path 表述，恢复到“默认入口可追溯、长期后端待后续 formal spec 扩张”的口径 |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] acquire / release 的 fail-closed 行为已冻结
- [x] `INVALID` 终态语义已冻结
- [x] snapshot / bootstrap 写入与并发风险已有缓解策略
