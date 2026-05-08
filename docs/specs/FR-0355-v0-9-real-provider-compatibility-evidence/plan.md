# FR-0355 v0.9.0 real provider compatibility evidence 实施计划

## 关联信息

- item_key：`FR-0355-v0-9-real-provider-compatibility-evidence`
- Issue：`#355`
- item_type：`FR`
- release：`v0.9.0`
- sprint：`2026-S22`
- 关联 exec-plan：`docs/exec-plans/CHORE-0356-v0-9-provider-compatibility-spec.md`

## 实施目标

- 为 `v0.9.0` 冻结真实外部 provider compatibility evidence 的 formal spec，使后续实现事项可以交付可被 `FR-0351` 消费的 `provider_compatibility_sample` evidence。

## 分阶段拆分

- 阶段 1：`#356` 收口本 formal spec suite、ADR、exec-plan 与 roadmap 引用。
- 阶段 2：创建 implementation / evidence Work Item，新增 external provider sample fixture、decision tests 与 closeout evidence artifact。
- 阶段 3：创建 release closeout Work Item，汇总 `v0.9.0` release index、GitHub Phase / FR / Work Item、PR、checks、guardian 与 published truth carrier。
- 阶段 4：发布 `v0.9.0` annotated tag 与 GitHub Release，并回写 release index published truth。

## 实现约束

- `#356` 只修改 formal spec、roadmap、ADR 与 exec-plan。
- `#356` 不修改 runtime、Adapter、Provider、tests、scripts 或 CI。
- implementation / evidence Work Item 不得重定义 `FR-0024`、`FR-0025`、`FR-0026` 或 `FR-0027` carrier。
- release closeout 不得声明 `v1.0.0` Core stable，也不得声明 provider 产品正式支持。

## 测试与验证策略

- spec PR：
  - `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - `git diff --check origin/main..HEAD`
- implementation / evidence PR：
  - compatibility decision runtime tests
  - provider no-leakage guard tests
  - dual reference regression tests
  - third-party adapter contract entry tests
  - API / CLI same Core path tests
  - docs / governance / version guards

## TDD 范围

- `#356` 是 formal spec closeout，不涉及 runtime TDD。
- 后续 implementation Work Item 必须先补 external provider sample fixture 与 failing tests，再补 runtime / evidence 代码。

## 并行 / 串行关系

- 可并行项：
  - 在 spec review 期间，只读梳理现有 `FR-0026` decision runtime、fixtures 与 no-leakage guard。
- 串行依赖项：
  - implementation / evidence Work Item 必须等待本 spec 合入 main。
  - release closeout Work Item 必须等待 implementation / evidence PR 合入 main。
- 阻塞项：
  - 如果本 FR 不先冻结，`v0.9.0` implementation 将缺少对“真实 provider sample 到底证明什么”的可审查边界。

## 进入实现前条件

- [ ] 本 formal spec 已通过 spec review、GitHub checks 与 guardian。
- [ ] roadmap 已引用本 FR。
- [ ] implementation Work Item 已绑定 `Issue`、`item_key`、`item_type`、`release` 与 `sprint`。
- [ ] implementation Work Item 的 exec-plan 明确验证命令、evidence artifact、release closeout 与回滚策略。
