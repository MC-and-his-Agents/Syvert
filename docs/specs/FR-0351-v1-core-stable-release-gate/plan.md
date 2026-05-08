# FR-0351 v1.0.0 Core stable release gate 实施计划

## 关联信息

- item_key：`FR-0351-v1-core-stable-release-gate`
- Issue：`#351`
- item_type：`FR`
- release：`v1.0.0`
- sprint：`2026-S22`
- 关联 exec-plan：`docs/exec-plans/CHORE-0352-v1-core-stable-release-gate-spec.md`

## 实施目标

- 在推进 `v0.9.0` 真实 provider 样本之前，冻结 `v1.0.0` Core stable release gate checklist，使 `v0.9.0` 的输出可以被明确映射到 `v1.0.0` 发布准入。

## 分阶段拆分

- 阶段 1：`#352` 收口本 formal spec suite，并更新 roadmap 引用。
- 阶段 2：`v0.9.0` Phase / FR / Work Item 消费本 gate 中的 `provider_compatibility_sample` 要求，交付真实 provider 样本 evidence。
- 阶段 3：`v1.0.0` release closeout Work Item 汇总除 `release_truth_alignment` 外的所有 required evidence，并准备 release index 草稿。
- 阶段 4：如果发布前 required gate item 全部通过，创建 `v1.0.0` release index、annotated tag 与 GitHub Release，并回写 published truth carrier。
- 阶段 5：最终验证 `release_truth_alignment`；只有 release index、tag、GitHub Release、closeout Issue / PR 与 published truth carrier 对齐后，才允许声明 `v1.0.0` 发布完成。

## 实现约束

- `#352` 只修改 formal spec、roadmap、ADR 与 exec-plan。
- `#352` 不修改 runtime、Adapter、Provider、tests、scripts 或 CI。
- 本 FR 不批准 `v0.9.0` provider sample 的具体实现方案；该样本必须由独立 Phase / FR / Work Item 承接。
- 本 FR 不批准 provider selector、fallback、marketplace、provider 产品白名单或上层应用能力。
- 本 FR 不要求 Python packaging；如需 package artifact，必须另建 FR。

## 测试与验证策略

- `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- `git diff --check`

## TDD 范围

- 本事项是 formal spec closeout，不涉及 runtime TDD。
- `v0.9.0` provider sample implementation 必须在后续事项中补 runtime / contract / evidence tests。
- `v1.0.0` release closeout 可在后续事项中补 release gate artifact 或 guard 自动化。

## 并行 / 串行关系

- 可并行项：
  - 在本 spec review 期间，可以只读梳理 v0.9.0 provider sample 候选和 existing compatibility decision runtime。
- 串行依赖项：
  - `v0.9.0` provider sample Phase 应消费本 spec 的 `provider_compatibility_sample` gate item。
  - `v1.0.0` release closeout 必须等待 `v0.9.0` evidence 入主干。
- 阻塞项：
  - 如果本 gate 不先冻结，`v1.0.0` 是否满足 Core stable 会继续依赖人工解释。

## 进入实现前条件

- [ ] 本 formal spec 已通过 spec review。
- [ ] roadmap 已引用本 gate。
- [ ] `v0.9.0` 真实 provider 样本进入执行前可以直接消费本 gate。
- [ ] `v1.0.0` release closeout 可以直接引用本 gate checklist。
