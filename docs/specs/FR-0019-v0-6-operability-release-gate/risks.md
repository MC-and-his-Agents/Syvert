# FR-0019 v0.6 operability release gate 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| 重写或弱化 `FR-0007` 基础 gate | `v0.6.0` gate 与既有版本 gate 断裂，旧 gate 结果被新矩阵误替代 | 明确 `baseline_gate_ref` 为必需字段，旧 gate 未完成时 `FR-0019` verdict 必须 fail | 回滚 `FR-0019` 文档增量中与 `FR-0007` 冲突的段落，保留旧 gate 真相 |
| `FR-0016` 默认 policy 漂移或缺失字段级断言 | timeout/retry/concurrency case 变成“看起来通过”，无法稳定复验 | 在 matrix case 强制断言 `timeout_ms=30000`、`retry.max_attempts=1`、`retry.backoff_ms=0`、`concurrency.scope=global`、`max_in_flight=1`、`on_limit=reject` | 回滚漂移 case，恢复固定默认值断言并重跑 gate |
| HTTP 与 CLI 形成影子状态或影子结果 | same-path 证明失效，用户通过不同入口看到不同任务 truth | 要求 HTTP / CLI 都消费 Core / task-record / store / envelope，不允许入口私有 durable truth | 撤销相关实现入口或回到同一路径实现，保留 formal spec 的 fail-closed 判定 |
| retry predicate 过宽，掩盖不可重试失败 | contract violation、非法输入或 store corruption 被误报为成功 | 固定 retry 只允许 `execution_timeout` 或 `platform+details.retryable=true` 且通过 idempotency safety gate；其余全部 fail-closed | 禁用相关 retry case 或回滚 retry 实现，恢复 fail-closed 输出 |
| `execution_timeout` 分类漂移到 `runtime_contract` | 控制面超时与真实 runtime_contract 失败混淆，导致 FR-0016/FR-0019 语义冲突 | 固定 `execution_timeout` case 断言 `error.category=platform` 且 `error.details.control_code=execution_timeout` | 回滚错误映射，恢复 control_code 语义 |
| 并发拒绝 pre/post accepted 语义混写 | TaskRecord/attempt 终态被误改写，门禁结论不可追溯 | pre-accepted 固定 `invalid_input + 无 TaskRecord`；post-accepted reacquire reject 固定“仅追加 `ExecutionControlEvent.details`” | 回滚相关映射，恢复 pre/post accepted 边界 |
| 并发 case 产生双终态或状态回退 | durable truth 被破坏，status/result 不可信 | 把单一 `TaskRecord`、单向状态迁移、一个终态与幂等写入列为必选证据 | 回滚并发写入路径或隔离到后续实现修复，不把 gate 作为通过证据 |
| `FR-0017` 结构化日志/指标/refs 退化为文本描述 | failure/log/metrics 维度变成主观判断，CI 无法机判 | 强制 case evidence 使用结构化字段与计数断言，日志至少含 `task_id`/`entrypoint`/`stage`/`error.category` | 回滚文本化断言，恢复结构化字段契约 |
| metrics / logs 绑定外部 SaaS | 本地和 CI 无法复验，repo 语义真相依赖外部 dashboard | 要求 metrics / logs 证据本地可复验，外部 dashboard 只能作为附加材料 | 移除外部 SaaS 作为必需证据，改回本地结构化输出或测试聚合 |
| 把 operability gate 扩张为生产验收或分布式压测 | `v0.6.0` 范围失控，阻塞可交付实现 | 在 scope 中排除生产验收、线上 SLO/SLA、真实流量、分布式压测 | 将扩张内容拆出未来 FR，不纳入 `#234` 实现 |

## 合并前核对

- [ ] 高风险项已有缓解策略。
- [ ] 回滚路径可执行。
- [ ] `FR-0019` 只叠加 `v0.6.0` operability gate，不重写 `FR-0007`。
- [ ] `FR-0016` 默认 policy、retry predicate、pre/post accepted 并发拒绝语义已字段级固化。
- [ ] `FR-0017` 结构化日志/指标/refs 要求已字段级固化。
- [ ] 文档未把外部 SaaS、生产验收或分布式压测列为必需门禁。
