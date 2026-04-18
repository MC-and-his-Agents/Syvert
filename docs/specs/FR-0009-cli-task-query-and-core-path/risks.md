# FR-0009 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| subcommand 改造破坏 legacy 平铺执行入口 | 现有 CLI 验收命令和测试回归 | 在 `#142` 保留 legacy 入口兼容，并增加 parse-failure 与 success path 回归测试 | 回滚 `#142/#143` 的 CLI 实现增量，但保留 `run/query` 作为批准的 public surface，并恢复到满足 formal spec 的上一版实现 |
| query 读取影子文件或重组影子 payload | durable truth 分叉，`FR-0008` contract 被绕过 | formal spec 明确 query 只能消费共享 durable record truth 与共享 JSON-safe 序列化 contract | 回滚 query 实现，恢复为只读共享 store 的版本 |
| 把 store 不可用与 task 不存在混为一类错误 | 调用方无法区分输入问题和 durable truth 失效 | 冻结 `task_record_not_found` 与 `task_record_unavailable` 的错误 contract | 回滚错误映射改动，恢复显式区分 |
| query 只允许终态记录被查询 | `accepted` / `running` durable history 无法被回读，破坏 `FR-0008` 可查询基线 | formal spec 明确允许回读任意合法 durable `TaskRecord` | 回滚终态限定逻辑，恢复全状态可查询 |
