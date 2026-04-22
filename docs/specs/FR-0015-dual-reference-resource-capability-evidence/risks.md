# FR-0015 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| 单平台事实被误提升为共享能力 | `FR-0013 / FR-0014` 会围绕错误能力名扩张 Core 抽象 | 要求所有共享能力都必须有 `xhs + douyin` 双侧证据记录，并通过 `shared + approve_for_v0_5_0` 才能进入词汇表 | 回滚错误能力名，恢复到仅 `account / proxy` 的批准基线 |
| 字段级材料被误当成独立能力 | `cookies`、`user_agent` 等 account 子字段会污染共享能力层 | 明确把字段级材料收口为 `account` 的内部 material，单独候选统一 `rejected` | 回滚字段级能力条目，恢复到单一 `account` 能力 |
| 技术绑定字段渗入能力词汇 | 下游实现会被 `sign_base_url`、`browser_state` 等实现细节锁死 | 明确技术绑定候选统一 `rejected`，并在 research.md 保留拒绝理由 | 回滚技术绑定候选，恢复实现无关的能力命名 |
| `proxy` 被误扩张成更高阶网络 profile 抽象 | `FR-0013 / FR-0014` 可能提前引入 provider 选择或代理档位语义 | 只批准“最小受管代理能力前提”，禁止在本 FR 中引入 richer proxy taxonomy | 回滚超范围 proxy 抽象，恢复最小 `proxy` 语义 |
| `research.md` 与 formal spec 形成第二套真相 | review 时无法判断到底哪个文档才是 canonical baseline | 明确 `research.md` 只提供证据补充，批准规则与词汇表以 formal spec / contract 为准 | 回滚重复定义段落，恢复 research 作为证据附录 |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] `account / proxy` 之外的候选已给出 `adapter_only` 或 `rejected` 方向
- [x] 下游不得自行新增能力标识的边界已冻结
