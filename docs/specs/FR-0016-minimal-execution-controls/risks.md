# FR-0016 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| timeout 被实现为 adapter 私有参数 | CLI / HTTP / TaskRecord 无法共享同一控制真相 | spec 明确 timeout 必须由 Core control path 建立 deadline，adapter 私有 timeout 只能作为实现细节 | 独立 revert 该实现 PR，保留 formal spec，重新实现 Core 侧 timeout |
| retry 被扩张为策略 DSL | v0.6.0 过早承担复杂调度、错误 predicate 与配置兼容负担 | spec 固定 `max_attempts`、固定 Core retryable predicate、idempotency safety gate 与固定 `backoff_ms`，禁止 caller 自定义 predicate | revert DSL 相关实现，回到最小 RetryPolicy |
| concurrency 被扩张为队列或公平调度 | HTTP API 会提前引入后台 worker / queue 语义，破坏最小服务面 | spec 固定 `on_limit=reject`，队列、优先级、公平性留给未来 FR | revert queue / scheduler 变更，恢复 fail-fast gate |
| timeout 后 late completion 改写终态 | TaskRecord durable truth 出现第二个终态或成功覆盖失败 | spec 要求 deadline 后结果隔离，终态写入保持幂等和 fail-closed | revert unsafe executor；在实现中引入 late result quarantine |
| retry attempt 泄漏资源或 slot | 后续 attempt 或其他任务继承不可信资源状态，导致资源追踪失真 | spec 要求每个 attempt 结束必须释放 slot，并按既有资源生命周期释放或失效资源 | revert retry 实现；补资源释放与 trace fail-closed 测试后重提 |
| 新增错误 category | 与 `FR-0005` 错误模型冲突，破坏既有 failed envelope consumer | spec 明确 timeout/retry/concurrency 只新增 code / details，不新增 category | revert category 扩张并把信号迁回 details / FR-0017 观测模型 |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
- [ ] 当前 PR 未混入 runtime、tests、scripts 或 HTTP API 实现
- [ ] 当前 PR 未新增 `FR-0005` 之外的错误 category
