# FR-0445 Batch / Dataset Core Contract 实施计划

## 关联信息

- item_key：`FR-0445-batch-dataset-core-contract`
- Issue：`#445`
- item_type：`FR`
- release：`v1.6.0`
- sprint：`2026-S25`
- 关联 exec-plan：`docs/exec-plans/CHORE-0446-v1-6-batch-dataset-spec.md`
- spec review：`docs/specs/FR-0445-batch-dataset-core-contract/spec-review.md`

## 实施目标

- 本次 FR 要让 Core 具备 batch / dataset public contract 输入：batch request、target set、item outcome、resume token、audit trace、dataset record 与 dataset sink 最小模型。
- `#446` 只交付 formal spec、sanitized inventory、release planning index 与 sprint index；runtime、consumer migration、evidence 与 closeout 由后续 Work Items 承接。

## 分阶段拆分

- 阶段 1：`#446` 冻结 sanitized fixture/error/evidence inventory 与 formal spec suite。
- 阶段 2：`#447` 实现 batch/dataset carrier、validators、reference dataset sink 与 batch item execution wrapper。
- 阶段 3：`#448` 迁移 TaskRecord、result query、runtime admission 与 compatibility consumers。
- 阶段 4：`#449` 交付 sanitized fake/reference evidence 与 replayable proof。
- 阶段 5：`#450` 完成 release/sprint/FR/Phase closeout truth 与 explicit `v1.6.0` release decision。

## 实现约束

- 不允许复用 `#382` 作为执行入口或 release truth。
- 不允许把 scheduler、write-side、content library、BI、UI、provider selector/fallback/marketplace 混入本 FR。
- 不允许提交 raw payload files、source names、本地路径、storage handles、private account/media/creator fields。
- 不允许在 batch item 中重新定义 `FR-0403`、`FR-0404`、`FR-0405` 已稳定的 read-side result entity fields。
- 不允许要求真实账号/登录态作为 Core batch admission 前置条件。

## 测试与验证策略

- 单元测试：
  - `#447` 覆盖 all success、partial success、all failed、duplicate target、resume token、dataset sink readback。
  - `#448` 覆盖 TaskRecord/result query/compatibility consumers。
  - `#449` 覆盖 sanitized evidence、dataset replay、resource boundary。
- 集成/契约测试：
  - `python3 -m unittest discover`
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/version_guard.py --mode ci`
  - `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `git diff --check`
- 手动验证：
  - 核对 GitHub `#444/#445/#446-#450` 与 release/sprint index 的 truth 一致。
  - 核对 `v1.6.0` planning index 未声明 published truth。
  - 运行脱敏扫描，确认新增文档不含 raw/source/path/storage/private 字段。

## TDD 范围

- 先写测试的模块：`syvert/batch_dataset.py`、TaskRecord consumer、compatibility consumer、dataset evidence replay。
- 暂不纳入 TDD 的模块与理由：`#446` 是 spec-only，不新增 runtime code。

## 并行 / 串行关系

- 可并行项：`#446` 内的 spec suite、inventory、release planning index、sprint index。
- 串行依赖项：`#447` 等待 `#446`；`#448` 等待 `#447`；`#449` 等待 `#447/#448`；`#450` 等待 `#446/#447/#448/#449`。
- 阻塞项：若发现 read-side result envelope 需要修补，必须创建单独 remediation Work Item，不得混入 `#445` batch implementation。

## 进入实现前条件

- [x] Read-side release slices `v1.3.0`、`v1.4.0`、`v1.5.0` 已发布，可作为 Batch / Dataset item result envelope 输入。
- [x] Phase `#381` closeout 仍由独立事项收口，本 FR 不声明其 completed truth。
- [x] `#382` 已确认为 deferred-roadmap / not planned / not completed。
- [x] `#444/#445/#446-#450` 已完成 GitHub admission。
- [ ] `#446` spec review 已通过。
- [ ] `#446` planning index 与 sprint index 已合入 main。
