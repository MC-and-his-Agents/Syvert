# FR-0368 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| 候选能力被误声明为 stable | `v1.1.0` 范围膨胀，后续能力绕过独立 FR | spec 固定 proposed candidate 只能 `runtime_delivery=false` | 回滚错误 lifecycle，恢复 proposed |
| `content_detail_by_url` baseline 被改写 | 破坏 `v1.0.0` Core stable truth | stable baseline 独立列出并作为 release gate | 回滚 taxonomy 改动并恢复旧 baseline |
| provider selector / fallback 偷渡进 taxonomy | Core 边界漂移到 provider routing | forbidden fields 与 leakage gate 明确禁止 | 回滚字段并补 no-leakage evidence |
| 上层应用 workflow 被写成 operation | Syvert 主仓职责扩大 | Runtime Capability 判定标准要求属于 Core runtime | 移出上层 workflow 字段，另建应用仓库事项 |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
- [ ] 候选能力没有被写成 executable runtime capability
- [ ] `content_detail_by_url` baseline 未被改写
