# FR-0013 实施计划

## 关联信息

- item_key：`FR-0013-adapter-resource-requirement-declaration`
- Issue：`#189`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 exec-plan：`docs/exec-plans/CHORE-0138-fr-0013-formal-spec-closeout.md`

## 实施目标

- 本次实施要交付的能力：
  - 把 adapter 资源依赖声明收敛为单一 canonical carrier `AdapterResourceRequirementDeclaration`
  - 把 `none|required`、`required_capabilities[]` 与 `evidence_refs[]` 的最小 contract 冻结到 formal suite
  - 为后续实现 Work Item 提供可直接消费的共享声明基线，而不要求本轮交付 runtime 改造

## 分阶段拆分

- 阶段 1：确认 `FR-0010`、`FR-0012` 与 `v0.5.0` 路线图对 `FR-0013` 的边界，防止声明层越界成 provider / fallback 抽象。
- 阶段 2：冻结 `AdapterResourceRequirementDeclaration` 字段、枚举、约束、GWT 与风险，形成完整 formal spec。
- 阶段 3：把双参考适配器共享声明基线与 `FR-0015` 共享证据映射补齐到 research / contracts 文档，形成 implementation-ready 输入。

## 实现约束

- 不允许触碰的边界：
  - `syvert/**`
  - `tests/**`
  - release / sprint docs
  - `FR-0010` / `FR-0012` / `FR-0014` / `FR-0015` 正文
- 与上位文档的一致性约束：
  - 必须满足 `docs/roadmap-v0-to-v1.md` 对 `v0.5.0` “只能收敛抽象、不能凭空扩张抽象”的约束
  - 必须复用 `FR-0015` 已批准的共享能力词汇 `account`、`proxy`
  - 必须把 `FR-0015` 作为共享证据真相源，而不是在本 FR 中另建第二套 evidence truth

## 测试与验证策略

- 单元测试：
  - 本 formal spec 回合不新增单元测试；验证重点是 formal spec / docs / workflow 守卫
- 集成/契约测试：
  - 本 formal spec 回合不新增 runtime 契约测试；通过 GWT 与 contracts/README 明确后续实现应消费的 contract
- 手动验证：
  - 核对双参考适配器共享声明基线是否只使用 `account`、`proxy`
  - 核对所有新增字段、禁止项与 `FR-0015` 证据绑定是否一致

## TDD 范围

- 先写测试的模块：
  - 无；本轮只交付 formal spec 套件
- 暂不纳入 TDD 的模块与理由：
  - runtime matcher / validator 实现与相应测试属于后续实现 Work Item，不属于 formal spec closeout 范围

## 并行 / 串行关系

- 可并行项：
  - requirement container 与 formal spec 正文可在同一回合同步编写
  - research.md 与 contracts/README 可在主 spec 定稿后补充细节
- 串行依赖项：
  - 必须先冻结 carrier 与字段，再写风险、research 与 contracts/README
- 阻塞项：
  - 若 `FR-0015` 共享词汇 / 共享证据边界无法被稳定引用，则 `FR-0013` 无法完成最小声明 contract 收口

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
