# FR-0023 风险记录

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| 第三方接入被误写成 provider 产品直接接 Core | Core registry、TaskRecord 或 resource lifecycle 会出现 provider 字段，破坏 Core / Adapter 分层 | formal spec 明确 canonical entry object 是 Adapter，Provider 只可作为 Adapter 内部实现细节 | 回滚 provider-facing 字段，恢复 Adapter-only contract |
| Adapter-only 接入路径与 Adapter / Provider compatibility decision 混写 | `#310/#311` 会把两个不同 FR 的验收目标塞进同一 contract test / SDK 文档 | out of scope 明确排除 Provider offer 与 compatibility decision，并在 manifest contract 中禁用相关字段 | 回滚混入字段，另建 compatibility decision FR |
| manifest 最小字段不足 | contract test 需要依赖 reviewer 口头上下文或真实外部服务才能判断准入 | 固定 required fields，并要求 fixture refs 与 contract test profile 可追溯 | 扩展 manifest required fields 后重新进入 spec review |
| resource requirement 被重新定义 | 第三方 Adapter 与 reference adapters 会出现第二套资源声明 truth | formal spec 要求直接消费 `FR-0027` 多 profile resource requirement contract | 回滚本 FR 中的资源声明扩张，回到 `FR-0027` 修复 |
| 第三方真实 `adapter_key` 裸借用双参考 proof | contract entry 会在 `xhs` / `douyin` proof 覆盖外放行第三方 Adapter，破坏 `FR-0027` fail-closed 边界 | formal spec 冻结 `ThirdPartyResourceProofAdmission`，要求 adapter-specific admission ref 绑定真实第三方 key、FR-0027 approved shared tuple 与 fixture / manifest evidence | 回滚裸借用路径，恢复 `invalid_resource_requirement`，补合法 admission evidence 后再进入实现 |
| admission 被放在完整 FR-0027 校验之后 | 真实第三方 `adapter_key` 会先因 `reference_adapters` 不覆盖而失败，bridge 成为不可达步骤 | formal spec 明确 admission 必须参与 proof binding 的 adapter coverage 子条件，FR-0027 shape / tuple / execution path 仍原样校验 | 回滚不可达顺序，改为 proof binding 阶段判定 direct coverage 或 admission coverage |
| admission 解析来源不固定 | `#310` 可能从 fixture side channel、全局 registry 或 adapter 私有代码补 admission，形成 contract drift | formal spec 固定 admission entries 只能来自当前 manifest-owned `resource_proof_admissions`，refs 必须唯一解析 | 回滚非 manifest-owned lookup，恢复 manifest primary carrier |
| 多 profile declaration 只验证部分 admission | 某些 profile 仍可能裸借用 reference proof 或出现多余 admission 误放行 | formal spec 要求每个 uncovered profile 必须有且只有一个 matching admission，且不得存在未消费的 admission | 回滚不完整 coverage，补逐 profile admission 校验 |
| 第三方通过样例伪装成 reference adapter key | `#310` 可能用 `xhs` / `douyin` 通过测试，实际没有证明第三方 Adapter identity | spec 明确第三方样例必须使用真实第三方 `adapter_key`，reference adapter key 只能作为 reference baseline，不能作为 third-party sample identity | 回滚伪装样例，改为真实第三方 key 与 admission ref |
| fixture 只覆盖 happy path | contract test 无法验证 error mapping 与失败 envelope 语义 | fixture contract 要求至少包含成功样本与失败映射样本 | 回滚不完整 fixture 准入，补齐失败样本要求 |
| reference adapter 升级破坏第三方 baseline | 小红书、抖音不再能作为第三方 Adapter 作者的最小参照 | formal spec 冻结 reference adapter 升级约束，要求 public metadata、manifest、fixture 与 contract test profile 保持可验证 | 回滚破坏 baseline 的升级，或在独立 PR 补齐 reference evidence |
| contract test profile 被误用为 provider 选择策略 | 测试矩阵名会被 runtime 当成 provider selector，造成隐式 routing | spec 明确 profile 只表达 Adapter contract test 准入组合，不表达 provider 选择 | 回滚 selector 语义，恢复纯测试准入含义 |
| 新业务 capability 借第三方接入路径偷渡 | `v0.8.0` 阶段边界扩大，缺少对应 evidence 与 formal spec | spec 明确本 FR 不批准新能力，超出 approved slice 必须另走 formal spec / evidence | 回滚越界 capability，另建 FR |

## 检查清单

- [ ] formal spec 已明确 Adapter 是第三方接入主入口。
- [ ] formal spec 已明确 public metadata required fields。
- [ ] formal spec 已明确 manifest / fixture / contract test 准入顺序。
- [ ] formal spec 已明确 resource requirement 消费 `FR-0027`。
- [ ] formal spec 已明确第三方 `adapter_key` proof admission bridge，不允许裸借用 reference proof。
- [ ] formal spec 已明确 Provider offer / compatibility decision /真实外部 provider 样本不在范围内。
- [ ] formal spec 已明确 reference adapter 升级约束。
