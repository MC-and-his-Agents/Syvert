# FR-0025 风险记录

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| offer carrier 被 manifest、SDK、validator 或 docs 各自实现成不同形状 | 后续 compatibility decision 无法稳定消费 Provider offer truth | formal spec 冻结 `ProviderCapabilityOffer` 为唯一 canonical carrier | 回滚分叉 carrier，恢复单一 formal spec 入口 |
| 合法 offer 被误解释为 compatibility approved | 未经过 `FR-0026` decision 的 provider 被错误绑定执行 | spec 明确合法 offer 仅代表 declared，不代表 compatible、selected 或可执行 | 回滚兼容性暗示文案，等待 `FR-0026` |
| provider key 被提升为 Core provider registry / routing key | Core、registry、TaskRecord 或 resource lifecycle 被 provider 概念污染 | adapter binding 固定 `adapter_bound`，Core-facing surface 禁止 provider 字段 | 回滚 Core-facing provider 文案或字段，恢复 Adapter-bound 边界 |
| resource support 重新定义 `FR-0027` profile truth | profile tuple、proof binding、matcher 或 fail-closed 口径出现第二套规则 | spec 明确 `resource_support` 只消费 `FR-0027`，不改写其规则 | 回滚重复定义，改为引用 `FR-0027` |
| profile 多选被写成优先级或 fallback | provider 层会越过 `FR-0027` 与 `FR-0026` 的边界，形成隐式选择策略 | formal spec 明确禁止 `priority`、`score`、`fallback`、`preferred_profile` 等字段 | 回滚排序 / fallback 字段与文案 |
| error carrier 新增 Core-facing provider 失败类别 | Core failed envelope、TaskRecord 与 Adapter 错误语义被 provider-specific 分类污染 | error carrier 只定义 offer 内部口径，外显必须经 Adapter 映射 | 回滚 provider-specific Core 失败字段，恢复 Adapter 映射 |
| lifecycle 字段扩张为 provider-owned resource runtime | `FR-0010` / `FR-0012` lifecycle truth 被旁路，资源池或账号池语义泄漏 | lifecycle 只表达 Adapter 调用与既有 resource bundle 视图消费 | 回滚 acquire/release/pool/provider-owned lifecycle 文案或字段 |
| observability 字段泄漏 selector、marketplace 或技术实现 | tracing / docs 可能被误用为 routing、产品认证或 browser/network 技术契约 | observability 只允许 offer id、provider key、adapter key、profile key、proof refs 与 validation outcome fields | 回滚泄漏字段，恢复最小审计字段 |
| `#319` 混入实现或父 FR closeout | formal spec PR 破坏规约/实现分离，也会提前关闭 `#297` truth | exec-plan 与 spec 明确 out of scope：不做 runtime、validator、SDK docs evidence，不关闭 `#297` | 回滚越界文件，保留 formal spec 套件 |

## 检查清单

- [ ] formal spec 已明确 `ProviderCapabilityOffer` 是唯一 canonical carrier
- [ ] formal spec 已明确 provider key / adapter binding / capability offer / resource support / error carrier / version / evidence / lifecycle / observability / fail-closed 字段边界
- [ ] formal spec 已明确消费 `FR-0024` requirement input 与 `FR-0027` resource profiles / proof binding
- [ ] formal spec 已明确合法 offer 不等于 Provider compatibility approved
- [ ] formal spec 已明确禁止 compatibility decision、provider selector、priority、fallback、marketplace、真实 provider 产品支持与 Core discovery / routing
- [ ] formal spec 已明确 `#319` 不做 runtime / validator / SDK docs evidence / 父 FR closeout
