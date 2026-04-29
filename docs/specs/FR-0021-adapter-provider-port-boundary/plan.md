# FR-0021 Adapter provider port boundary 实施计划

## 关联信息

- item_key：`FR-0021-adapter-provider-port-boundary`
- Issue：`#265`
- item_type：`FR`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 exec-plan：`docs/exec-plans/CHORE-0268-fr-0021-formal-spec-closeout.md`

## 实施目标

- 本次 FR 要交付的能力：在不改变 Core / Adapter public contract 的前提下，把小红书、抖音当前 provider-like 执行细节拆到 adapter-owned provider port 与 native provider 后面。

## 分阶段拆分

- 阶段 1：`#268` formal spec closeout
  - 创建本 formal spec 套件。
  - 冻结 provider port 所有权、非目标、数据边界、验收与回滚方式。
- 阶段 2：`#269` runtime implementation
  - 新增或等价抽取小红书、抖音内部 provider port / native provider。
  - Adapter public runtime surface 与 existing constructor hooks 保持兼容。
  - 补测试证明 Core 与 registry 不感知 provider。
- 阶段 3：`#270` SDK compatibility / capability metadata
  - 更新 `adapter-sdk.md`、release/sprint 索引与迁移说明。
  - 明确 provider port 是 adapter-owned 内部边界。
- 阶段 4：`#271` dual reference evidence
  - 运行小红书、抖音 current approved slice 回归。
  - 记录可追溯 evidence，证明 `content_detail_by_url` 行为兼容。
- 阶段 5：`#272` FR parent closeout
  - 汇总 spec、runtime、metadata、evidence 与 GitHub 状态。
  - 关闭 `#265`，但不关闭 Phase `#264`。
- 阶段 6：后续 Phase / release closeout Work Item
  - 在 `#265` 完成后创建或执行最终 closeout，关闭 `#264` 并同步 `v0.7.0` release/sprint/GitHub truth。

## 实现约束

- 不允许触碰的边界：
  - 不新增 Core provider registry、provider selector、provider routing 或 fallback priority。
  - 不新增外部 provider 接入。
  - 不新增小红书/抖音业务能力。
  - 不扩展资源模型。
  - 不改变 `content_detail_by_url` adapter-facing input/output/error/resource behavior。
- 与上位文档的一致性约束：
  - 必须符合 `#264` Phase 与 `#265` FR 正文。
  - 必须符合 `docs/decisions/ADR-CHORE-0266-v0-7-adapter-provider-port-planning.md` 的分阶段决策。
  - 必须继续尊重 `FR-0013`、`FR-0014`、`FR-0015` 的 resource boundary。

## 测试与验证策略

- 单元测试：
  - `tests.runtime.test_xhs_adapter`
  - `tests.runtime.test_douyin_adapter`
  - 新增 provider delegation / compatibility tests。
- 集成/契约测试：
  - `tests.runtime.test_registry`
  - `tests.runtime.test_real_adapter_regression`
  - `tests.runtime.test_version_gate`
  - 需要断言 registry / Core output 不暴露 provider 字段。
- 文档与治理验证：
  - `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3.11 scripts/docs_guard.py --mode ci`
  - `python3.11 scripts/workflow_guard.py --mode ci`
  - `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`

## TDD 范围

- 先写测试的模块：
  - `#269` 应先补测试证明 Adapter 委托 native provider，legacy constructor hooks 仍可用。
  - `#269` 应先补测试证明 registry discovery 不含 provider 字段。
- 暂不纳入 TDD 的模块与理由：
  - `#268` 只建立 formal spec，不修改 runtime。
  - `#270` 主要是文档/metadata closeout，可通过 docs 与 governance gates 验证。

## 并行 / 串行关系

- 可并行项：
  - `#270` 可在 `#268` 合入后与 `#269` 部分并行，但不得假设未合入的 runtime 事实已经完成。
- 串行依赖项：
  - `#269` 必须在 `#268` 合入后开始。
  - `#271` 必须在 `#269` 合入后开始。
  - `#272` 必须在 `#268/#269/#270/#271` 全部完成后开始。
- 阻塞项：
  - formal spec 未合入前，不得开始 provider port runtime implementation。

## 进入实现前条件

- [ ] `#268` formal spec PR 已通过 spec review
- [ ] 本 formal spec 套件已合入主干
- [ ] `#269` active exec-plan 绑定 `docs/specs/FR-0021-adapter-provider-port-boundary/`
- [ ] 关键风险已记录并有缓解策略
- [ ] GitHub issue 关系与 release/sprint 索引未出现冲突
