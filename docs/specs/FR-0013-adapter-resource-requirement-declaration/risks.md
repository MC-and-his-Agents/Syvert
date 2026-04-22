# FR-0013 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| 把声明 carrier 扩写成 provider / fallback / 优先级系统 | `v0.5.0` scope 漂移，后续实现会被迫围绕未批准抽象扩张 | formal spec 只允许 `none|required` 与固定字段集合，显式禁止 `preferred_capabilities`、`optional_capabilities`、`fallback`、`priority`、`provider_selection` | 回滚超范围字段与叙述，恢复到最小声明 carrier |
| 把单平台私有前置参数误写成共享能力词汇 | Core 资源抽象被平台事实污染，双参考适配器共同语义失真 | `required_capabilities[]` 只允许 `FR-0015` 已批准词汇 `account`、`proxy` | 回滚越界词汇，恢复到共享词汇表 |
| `evidence_refs[]` 退化成描述性备注 | 声明无法证明自己来自共享证据，formal review 无法 fail-closed | formal spec 要求 `evidence_refs[]` 非空、去重且只能引用 `FR-0015` 共享证据 | 回滚非 canonical evidence 绑定，恢复到共享证据引用 |
| `none` 语义不明确 | 后续实现可能把空数组、缺字段或 `null` 混作“无资源依赖” | formal spec 明确 `none => required_capabilities=[]`，且固定字段不可缺省 | 回滚宽松形状，恢复到单一 canonical 表达 |
| requirement container 被相邻 FR 反向改写 | `FR-0013` 的主语义与 closeout 输入漂移，后续事项无稳定 requirement container 可消费 | requirement container 明确 `FR-0013` 只被新 formal spec 推进，不被 `FR-0014/FR-0015` 侧写改写 | 回滚跨 FR 语义渗透，恢复 requirement container 单一真相 |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] `none|required` 的最小声明面已冻结
- [x] `required_capabilities[]` 与 `FR-0015` 共享词汇绑定已冻结
- [x] `evidence_refs[]` 只引用 `FR-0015` 共享证据的约束已冻结
