# FR-0015 实施计划

## 关联信息

- item_key：`FR-0015-dual-reference-resource-capability-evidence`
- Issue：`#191`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 exec-plan：
  - `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md`
  - `docs/exec-plans/CHORE-0140-fr-0015-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0144-fr-0015-evidence-registry-reconciliation.md`

## 实施目标

- 在进入 `FR-0013` / `FR-0014` 的实现前，先冻结双参考适配器资源能力证据载体、批准规则与最小能力词汇，确保所有后续声明与匹配都基于同一份 evidence baseline。

## 分阶段拆分

- 阶段 1：`#194` 收口 formal spec，冻结 `DualReferenceResourceCapabilityEvidenceRecord`、批准规则与 `research.md` 入口。
- 阶段 1.1：`#206` 作为 formal-spec follow-up，补齐 `research.md` 中 implementation closeout 需要消费的 stable evidence ref registry 与示例基线，避免 formal truth 与 evidence closeout 漂移。
- 阶段 2：后续 evidence closeout Work Item 消费本 formal spec，把双参考适配器事实沉淀到稳定 evidence registry，而不是继续依赖会话判断。
- 阶段 3：`FR-0013` 与 `FR-0014` 在不反向改写证据规则的前提下，分别消费本 FR 的批准词汇与引用边界。

## 实现约束

- 不允许触碰的边界：
  - 不得在本事项中实现 matcher、provider selector、scheduler 或浏览器桥接逻辑
  - 不得把字段级 session material 漂移成独立共享能力词汇
  - 不得修改 `FR-0010` / `FR-0012` 已冻结的 slot、bundle、lease 与注入边界
- 与上位文档的一致性约束：
  - 与 `AGENTS.md` 对“formal spec 绑定 FR、Work Item 才是执行入口”的规则保持一致
  - 与 `docs/roadmap-v0-to-v1.md` 对 `v0.5.0` 的资源抽象收口目标保持一致
  - 与 `FR-0010` 的 `account / proxy` 资源类型、`FR-0012` 的注入 boundary 保持一致，不另建影子资源轴

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-194-fr-0015-formal-spec`
- implementation 阶段：
  - 双参考 evidence registry 验证：同一候选能力必须同时存在 `xhs` / `douyin` 的稳定证据记录，才能被投影到批准词汇
  - review 验证：对 `adapter_only` / `rejected` 候选进行抽查，确保没有被下游 FR 误消费
- 手动验证：
  - 核对 runtime、reference adapters 与 regression 种子，确认当前共享能力词汇仅保留 `account`、`proxy`
  - 核对 `research.md` 是否显式列出共性资源语义、单平台特例与被拒绝候选

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不涉及运行时代码或测试文件变更
- 暂不纳入 TDD 的模块与理由：
  - evidence registry runtime / tooling 尚未进入当前 Work Item 范围，本轮只冻结正式规约真相

## 并行 / 串行关系

- 可并行项：
  - `#192 / #193` 可以并行起草 spec 文档骨架，因为主要写集分离
- 串行依赖项：
  - `#192 / #193` 进入 spec review 前，必须消费本 FR 已冻结的能力词汇与 evidence rule
- 阻塞项：
  - 若 `FR-0015` 不先收口，`FR-0013 / FR-0014` 会被迫在声明或 matcher 中重新发明能力名

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] `account / proxy` 以外的候选能力已明确收口为 `adapter_only` 或 `rejected`
