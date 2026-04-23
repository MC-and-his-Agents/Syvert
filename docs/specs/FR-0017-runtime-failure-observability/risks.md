# FR-0017 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| observability 层重新发明错误分类 | 与 `FR-0005` 冲突，导致同一失败在 envelope、日志与指标中分类不一致 | 明确 `error_category` 只能从 failed envelope 投影，timeout / retry / concurrency 只能进入 `failure_phase` 或引用 | 回滚私有分类字段，恢复 `FR-0005` 分类投影 |
| 结构化日志脱离 `task_id` / TaskRecord | 失败无法从 GitHub / repo 语义真相追溯到具体任务历史 | 所有 signal、event、metric 均强制携带 `task_id`；进入 `accepted` 后必须引用 TaskRecord | 回滚不可关联日志，恢复 task-bound carrier |
| observability 写入失败吞掉原始业务失败 | 排查时只能看到日志失败，看不到真正业务失败 envelope | 规定 observability 自身失败必须暴露 `observability_write_failed`，且不得丢弃原始 failed envelope | 回滚吞错路径，恢复原始 failed envelope 优先 |
| 与 `FR-0016` timeout / retry / concurrency 本体边界混淆 | 本 FR 反向定义调度、重试、锁或并发策略，造成相邻 FR 冲突 | 本 FR 只消费 `FR-0016` 运行时结果引用，不定义策略或状态机 | 回滚策略性语句，只保留结果引用与可观测投影 |
| 指标 contract 被误扩张成完整 metrics platform | spec review 范围失控，后续实现被迫建设后端或 dashboard | 明确只冻结本地可判定 carrier、metric name 与计数口径，不绑定存储或展示 | 回滚后端、dashboard、采集协议相关语义 |
| 资源追踪引用缺失 | 资源相关失败无法关联 `lease_id / bundle_id / resource_id`，破坏 `FR-0011` 审计面 | 资源 acquire 成功后的失败必须引用已有 resource trace；acquire 前显式空集合 | 回滚不可追溯信号，恢复 resource trace refs |

## 合并前核对

- [ ] 未新增 `FR-0005` 之外的顶层错误分类
- [ ] 所有 carrier 都有 `task_id` 关联语义
- [ ] TaskRecord、failed envelope、resource trace、FR-0016 runtime result 的引用边界已写清
- [ ] 未引入日志后端、指标存储、dashboard 或 adapter 私有平台 taxonomy
- [ ] formal spec 与实现代码保持分离
