# FR-0024 风险记录

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| requirement carrier 被 manifest、SDK、adapter migration 各自实现成不同形状 | 后续 compatibility decision 无法稳定消费 Adapter requirement truth | formal spec 冻结 `AdapterCapabilityRequirement` 为唯一 canonical carrier | 回滚分叉 carrier，恢复单一 formal spec 入口 |
| 本 FR 重新定义 resource profile truth | 与 `FR-0027` 的 profile tuple、proof binding 或 fail-closed 口径冲突 | spec 明确 `resource_requirement` 只消费 `FR-0027`，不改写其规则 | 回滚重复定义，改为引用 `FR-0027` |
| 合法 requirement 被误解释为 provider compatibility approved | 未经过 Provider offer / decision 的组合被错误绑定执行 | spec 明确合法 requirement 仅代表 declared，不代表 offer 或 compatible | 回滚兼容性暗示文案，等待 Provider offer / decision FR |
| profile 多选被写成优先级或 fallback | runtime / provider 层会越过 `FR-0027` 的 one-of 合法集合语义 | formal spec 明确禁止 `priority`、`fallback`、`preferred_profile` 等字段 | 回滚排序 / fallback 字段与文案 |
| lifecycle 字段扩张为新的 resource runtime | `FR-0010` / `FR-0012` lifecycle truth 被旁路，Core / Adapter 边界漂移 | lifecycle 只表达消费预期，禁止 acquire/release/pool/provider-owned lifecycle | 回滚 lifecycle runtime 字段，恢复引用既有 contract |
| observability 字段泄漏 provider 或技术实现 | Core registry、TaskRecord 或 requirement surface 被 provider / browser / transport 字段污染 | observability 只允许 requirement id、profile key、proof refs 与 admission outcome fields | 回滚泄漏字段，恢复最小审计字段 |
| fail-closed 边界不一致 | validator、runtime admission 与 spec review 对同一非法 carrier 得出不同结论 | spec/data-model/contracts 统一把缺字段、不一致、proof 非法、禁止字段归类为 `invalid_resource_requirement` 或阻断 | 回滚漂移口径，重新对齐三类载体 |
| `#313` 混入实现或父 FR closeout | formal spec PR 破坏规约/实现分离，也会提前关闭 `#296` truth | exec-plan 与 spec 明确 out of scope：不做 runtime、validator、adapter migration，不关闭 `#296` | 回滚越界文件，保留 formal spec 套件 |

## 检查清单

- [ ] formal spec 已明确 `AdapterCapabilityRequirement` 是唯一 canonical carrier
- [ ] formal spec 已明确消费 `FR-0027` resource profiles / proof binding
- [ ] formal spec 已明确 capability / execution requirement / evidence / lifecycle / observability / fail-closed 字段边界
- [ ] formal spec 已明确合法 requirement 不等于 Provider compatibility approved
- [ ] formal spec 已明确禁止 Provider offer、compatibility decision、priority、fallback 与新共享能力词汇
- [ ] formal spec 已明确 `#313` 不做 runtime / validator / reference adapter migration / 父 FR closeout
