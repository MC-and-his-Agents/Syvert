# FR-0006 实施计划

## 关联信息

- item_key：`FR-0006-adapter-contract-test-harness`
- Issue：`#66`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 exec-plan：`无（当前 formal spec PR 直接绑定 FR）`

## 实施目标

- 为 `v0.2.0` 冻结 adapter contract test harness 的最小实施边界，使后续实现 PR 能在不触碰真实平台回归与版本 gate 的前提下，独立交付 fake adapter、验证工具和 Core contract 验证宿主。

## 分阶段拆分

- 阶段 1：冻结 harness、fake adapter、验证工具三者的职责边界，以及可验证 contract 面与排除范围。
- 阶段 2：实现受控 fake adapter 与最小 harness 宿主，使 Core 能通过标准 adapter 路径执行契约样例。
- 阶段 3：补齐验证工具、契约样例与最小自动化验证，覆盖成功态、合法失败态与 contract violation。
- 阶段 4：在不引入真实平台依赖的前提下收口实现 PR 的审查证据，并为后续参考适配器回归事项提供稳定输入。

## 实现约束

- 不允许触碰的边界：
  - 不在本事项实现中重新定义 `InputTarget`、`CollectionPolicy`、错误模型或 adapter registry 正式语义
  - 不把真实平台测试、双参考适配器回归 gate、平台泄漏检查 gate 混入同一实现 PR
  - 不为了 fake adapter 修改 Core 主路径中的平台边界或引入生产期假适配器依赖
  - 不把 harness 实现耦合到唯一测试框架、唯一 CLI 入口或唯一目录结构
- 与上位文档的一致性约束：
  - `vision.md` 与 `docs/roadmap-v0-to-v1.md` 中 `v0.2.0` 的“可验证”目标必须保持不变
  - `FR-0002` 已冻结的统一 adapter contract 是本 FR 的上位输入；若需改写正式 contract，必须回到 spec review
  - formal spec 与实现默认分 PR；本轮 formal spec PR 只更新 spec 套件与最小 release / sprint 索引

## 测试与验证策略

- 单元测试：
  - fake adapter 受控返回分支的样例装配
  - harness 对 contract violation 与合法失败的判定
  - 验证工具的结果分类与样例级归因
- 集成/契约测试：
  - Core 通过标准 adapter 宿主路径加载 fake adapter 并执行契约样例
  - success envelope、合法 failed envelope、非法结果 envelope 的最小 contract 验证
  - 在不访问真实平台的条件下复现稳定 contract 判定
- 手动验证：
  - 检查 harness 执行不要求真实网络、Cookie、签名或真实平台响应
  - 检查验证输出能区分通过、contract violation、执行前置失败

## TDD 范围

- 先写测试的模块：
  - harness 对 contract 样例的执行与判定
  - fake adapter 样例装配接口
  - 验证工具的结果分级与归因
- 暂不纳入 TDD 的模块与理由：
  - 真实平台回归流程、版本 gate 编排与 CI 拓扑不属于本 FR 主体，留给后续独立事项处理

## 并行 / 串行关系

- 可并行项：
  - fake adapter 样例设计
  - harness 宿主接入
  - 验证工具结果格式与断言组织
- 串行依赖项：
  - 必须先冻结本 FR formal spec，再进入 harness 实现 PR
  - 必须先有 fake adapter + harness 的最小宿主，才能叠加更高层的验证工具与样例集
  - 参考适配器回归与版本 gate 只能在本 FR 产出稳定后消费其结果
- 阻塞项：
  - 若 `FR-0002` 的上位 adapter contract 发生变更，本 FR 实现必须等待对应 formal spec 更新完成后再推进

## 进入实现前条件

- [x] `spec review` 已通过
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用
- [x] harness、fake adapter、验证工具与真实平台回归的边界已冻结
- [x] 后续实现 PR 的范围已限制在 contract harness 基座，不要求同轮处理版本 gate 或双参考适配器回归

## spec review 结论

- 结论：通过
- 未决问题与风险：
  - 需要在实现阶段继续防止 fake adapter 语义膨胀成影子平台适配器
  - 需要确保 harness 判定 contract violation 时不偷偷重写上位 contract 语义
- implementation-ready 判定：
  - 当前 formal spec 已把 contract harness 的职责、fake adapter 的角色、可验证保证级别与边界约束冻结到足以进入实现；后续应以独立 implementation PR 落地最小宿主、样例与自动化验证
