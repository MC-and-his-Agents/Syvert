# FR-0445 风险记录

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| batch contract 漂移成 scheduler | Core 会提前承载调度语义 | spec 明确 resume token 只恢复 runtime position | 删除 scheduler 字段与场景 |
| dataset sink 漂移成内容库或 BI 产品 | Core 职责边界扩大到上层应用 | sink 只保留 write、dataset-id readback、batch-id readback、audit replay | 回滚产品字段 |
| read-side envelope 被 batch 重写 | 破坏 `v1.3.0`-`v1.5.0` published contracts | BatchItemOutcome 只封装既有 envelope | 回滚重定义字段，单独开 remediation |
| raw/source/path/storage 泄漏 | evidence 与 dataset record 污染发布 truth | 所有 evidence ref 使用 sanitized alias | 删除污染 artifact 并重跑 leakage scan |
| duplicate dedup key 语义不稳定 | dataset record 重复或审计不一致 | first-wins，duplicate item 标记 `duplicate_skipped` | 回滚 duplicate policy |
| batch 绕过 resource governance | 真实账号/登录态边界被 Core batch 直接持有 | batch 本身不要求资源，item operation 仍走 existing resource governance | 回滚 batch-level resource fields |
| provider selector/fallback 被混入 batch | Core 变成 provider routing/marketplace 层 | forbidden carrier fields 与 compatibility rules 明确拒绝 | 删除 selector/fallback 字段并重跑 guards |

## 当前残余风险

- Runtime Work Item 需要谨慎设计 batch wrapper，避免绕过 `execute_task` 的 TaskRecord 与 resource lifecycle。
- Dataset evidence Work Item 必须覆盖 replay 与 leakage scan，不能只验证 happy path。
- Closeout Work Item 需要明确 `v1.6.0` release target commit、annotated tag、GitHub Release 与 published truth carrier。
