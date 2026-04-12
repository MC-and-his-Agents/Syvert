# FR-0005 实施计划

## 关联信息

- item_key：`FR-0005-standardized-error-model-and-adapter-registry`
- Issue：`#65`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 exec-plan：`docs/exec-plans/CHORE-0051-fr-0005-formal-spec.md`

## 实施目标

- 为 `FR-0005` 建立 formal spec 套件，冻结标准化错误模型与 adapter registry 的 requirement、边界与验收语义。
- 让 `#69` 与 `#70` 能以清晰分工进入后续实现，而不在 formal spec PR 中提前进入执行态。

## 分阶段拆分

- 阶段 1：建立 `FR-0005` formal spec 套件，冻结错误分类、registry 职责、discovery 约束与 fail-closed 语义。
- 阶段 2：由 `#69` 独立实现标准化错误模型，把 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 的分类与 envelope 映射落入 Core / Adapter 运行时。
- 阶段 3：由 `#70` 独立实现 adapter registry，把注册、查找、capability discovery 与 fail-closed 行为落入运行时。
- 阶段 4：由 `FR-0006` 在已批准的 error model 与 registry contract 上建立 harness、fake adapter 与验证工具契约。
- 阶段 5：由 `FR-0007` 在已批准的 contract 与 harness 能力上定义 gate、回归检查与平台泄漏检查流程。

## 实现约束

- 不允许触碰的边界：
  - 当前 PR 只允许修改 `FR-0005` formal spec 套件、必要的风险/契约文档、当前执行回合所需的最小 `exec-plan`，以及 `v0.2.0` / `2026-S15` 的最小索引更新
  - 不在本 PR 中修改 `src/**`、`scripts/**`、`tests/**`
  - 不把 harness、fake adapter、validator、gate、双参考适配器回归或平台泄漏检查提前并入本 FR
  - 不把 registry 的代码结构、模块路径、类名或 import 机制冻结成 formal contract
- 与上位文档的一致性约束：
  - 与 `vision.md`、`docs/roadmap-v0-to-v1.md` 的 `v0.2.0` 边界保持一致
  - 与 `FR-0004`、`FR-0006`、`FR-0007` 保持职责切分，不制造交叉 requirement
  - formal spec 与实现默认分 PR

## 测试与验证策略

- 单元测试：
  - 无。当前 formal spec PR 不引入实现代码；`#69` 与 `#70` 再为错误分类映射、registry fail-closed 与 discovery 语义补测试
- 集成/契约测试：
  - 当前 formal spec PR 运行 `docs_guard`、`spec_guard`、`context_guard` 与 `open_pr --class spec --dry-run`
  - `#69` 后续覆盖错误 envelope、分类映射与失败路径回归
  - `#70` 后续覆盖 registry materialization、lookup、capability discovery 与 fail-closed 回归
- 手动验证：
  - 核对 `#65`、`#69`、`#70` 与 `FR-0004`、`FR-0006`、`FR-0007` 的 GitHub 边界
  - 核对 `docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 与 `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/` 的索引映射一致

## TDD 范围

- 先写测试的模块：
  - `#69`：错误 envelope 分类映射、invalid / unsupported / runtime_contract / platform 边界
  - `#70`：registry lookup、capability discovery、重复 key / 非法声明 / fail-closed 行为
- 暂不纳入 TDD 的模块与理由：
  - formal spec 文档本身不产生运行时代码；harness / fake adapter / gate 的测试策略属于 `FR-0006`、`FR-0007`

## 并行 / 串行关系

- 可并行项：
  - formal spec 套件编写
  - 风险文档与 contracts 文档整理
  - release / sprint 最小索引更新
- 串行依赖项：
  - `#69` 与 `#70` 必须等待当前 formal spec 合入 `main`
  - `FR-0006` 与 `FR-0007` 必须消费已批准的错误模型与 registry contract，而不是反向定义本 FR
  - merge 前必须完成当前 PR 的 checks、guardian 与 merge gate
- 阻塞项：
  - 若 formal spec 没有把 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 的边界写清，后续实现将无法稳定拆分到 `#69` 与 `#70`

## 进入实现前条件

- [ ] `spec review` 已通过
- [x] 关键风险已记录并有缓解策略
- [x] 关键依赖可用
- [x] `#69` 与 `#70` 的职责切分已明确

## spec review 结论

- 结论：当前 formal spec 目标清晰，已把错误模型、registry、discovery 与 fail-closed 语义收敛到 `FR-0005`，且未吞并相邻 FR 的 formal scope
- 未决问题：
  - `#69` 需要在实现前把现存 `runtime_contract` / `platform` 错误映射迁移到新分类集合
  - `#70` 需要在实现前决定 registry 的具体承载方式，但该选择不得反向改写本 spec 的语义边界
- implementation-ready 判定：待当前 formal spec PR 完成 checks、guardian、merge gate 后，`#69` 与 `#70` 可据此进入各自实现回合
