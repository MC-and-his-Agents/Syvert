# FR-0022 risks

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| stale cache 被用于 merge gate | 可能在 integration 状态已变化时错误放行合并 | spec 明确 `uncached_live_gate` 与 `cached_non_merge` 分离；测试覆盖 merge gate 失败仍阻断 | 回滚 cache 接入，恢复所有 live lookup hard fail |
| 非合并 fallback 被误展示为通过 | status 面会掩盖 quota / GraphQL 失败 | fallback 必须标记 `unverified` 并保留 live error | 回滚非合并 fallback 展示，恢复 fail-closed |
| 持久 cache 被后续实现引入 | GitHub 调度真相源被本地 stale truth 替代 | spec 禁止持久 cache、TTL、跨命令恢复 | 删除持久 cache 与对应 state 文件 |
| search endpoint 仍被批量默认调用 | 容易触发 REST search 限制或 secondary rate limit | spec 要求先建本回合 index，search 只作 fallback | 回滚到单 spec sync 或禁用批量 sync |
| rulesets 读取失败被当成空列表 | 可能错误创建/覆盖 repository ruleset | 读取失败 hard fail；写入前必须有可信 snapshot | 回滚写入逻辑或手工恢复 GitHub ruleset |
| PR/checks 快照复用过度 | 可能漏掉合并前状态变化 | 保留 final PR metadata / checks re-read | 回滚快照复用，仅保留原多次读取 |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
- [ ] merge gate 不使用 stale cache
- [ ] 非合并 fallback 有 `unverified` 或等价状态
- [ ] rulesets 读取失败不会触发写入
