# FR-0026 风险记录

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| decision carrier 被 runtime、docs 或 guard 各自实现成不同形状 | 后续 compatibility 判断无法稳定复验 | formal spec 冻结 `AdapterProviderCompatibilityDecision` 为唯一 canonical carrier | 回滚分叉 carrier，恢复单一 formal spec 入口 |
| `unmatched` 与 `invalid_contract` 混淆 | 合法但不兼容的输入可能被误报为 contract violation，或非法输入被宽松放行 | spec 明确合法无 profile 交集为 `unmatched`，输入 / proof / leakage 违法为 `invalid_contract` | 回滚混淆口径，恢复三状态边界 |
| decision 反向改写 requirement / offer carrier | `FR-0024` / `FR-0025` truth 被破坏，形成循环依赖 | spec 明确只消费输入 carrier，不定义或修改本体 | 回滚 carrier 扩写，回到对应 FR 更新 truth |
| resource profile matching 重写 `FR-0027` matcher | profile tuple、proof binding 或 one-of 语义出现第二套规则 | spec 只消费 `FR-0027` canonical tuple 与 proof validity | 回滚重复定义，改为引用 `FR-0027` |
| matched 被误解释为 provider selector 或 runtime binding | Core routing 或 Adapter runtime 可能自动选择 provider | spec 明确 `matched` 不代表 selected provider、priority、fallback、score 或 Core routing | 回滚 selector / routing 文案和字段 |
| provider key 泄漏到 Core-facing surface | Core registry、TaskRecord、routing 或 resource lifecycle 被 provider 概念污染 | no-leakage contract 明确 Core-facing surface 禁止 provider 字段 | 回滚泄漏字段，恢复 Adapter-bound evidence 边界 |
| fail-closed 不完整 | proof 漂移、adapter mismatch 或 execution mismatch 可能被误判为 `matched` | spec 明确任何 ambiguity 必须 `invalid_contract` | 回滚宽松判断，恢复 fail-closed |
| `#323` 混入实现或父 FR closeout | formal spec PR 破坏规约/实现分离，也会提前关闭 `#298` truth | exec-plan 与 spec 明确 out of scope：不做 runtime、guard、docs evidence 或父 FR closeout | 回滚越界文件，保留 formal spec 套件 |

## 检查清单

- [ ] formal spec 已明确 `AdapterProviderCompatibilityDecision` 是唯一 canonical carrier
- [ ] formal spec 已明确只消费 `FR-0024`、`FR-0025` 与 `FR-0027`
- [ ] formal spec 已明确 `matched`、`unmatched`、`invalid_contract` 三状态边界
- [ ] formal spec 已明确 proof 不合法、adapter mismatch、execution mismatch 或禁止字段出现时必须 fail-closed
- [ ] formal spec 已明确 provider key 不得泄漏到 Core routing、registry discovery、TaskRecord 或 resource lifecycle
- [ ] formal spec 已明确禁止 provider selector、priority、score、fallback、marketplace、真实 provider 产品支持与 Core discovery / routing
- [ ] formal spec 已明确 `#323` 不做 runtime / no-leakage guard / docs evidence / 父 FR closeout
