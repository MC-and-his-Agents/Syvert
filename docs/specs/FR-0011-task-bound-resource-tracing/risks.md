# FR-0011 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| tracing truth 与 usage log 各自维护不同 schema | 审计面分裂，release gate 无法基于单一真相判断 | formal spec 明确 usage log 只是 canonical tracing truth 的投影 | 回滚影子日志 schema，恢复单一事件 truth |
| 缺少 `task_id / lease_id / bundle_id / resource_id` 任一关联轴 | 无法证明 task 与资源之间的真实占用关系 | formal spec 把四轴都定义为 task-bound tracing 必填字段 | 回滚不完整事件并恢复强制字段校验 |
| 事件允许原地覆写或冲突重放 | 资源时间线失真，无法可靠审计 | formal spec 明确 append-only 与冲突 fail-closed | 回滚可变历史实现，恢复只追加事件 |
| 状态迁移成功但 tracing 写入失败仍被放行 | 资源状态与审计面分叉，最小审计闭环失效 | formal spec 明确 tracing 与生命周期迁移必须同成同败 | 回滚 best-effort tracing 路径，恢复 fail-closed |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 事件真相与日志投影的单一来源已冻结
- [ ] task/resource/lease/bundle 四轴关联已冻结
