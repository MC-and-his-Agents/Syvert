# FR-0014 实施计划

## 关联信息

- item_key：`FR-0014-core-resource-capability-matching`
- Issue：`#190`
- item_type：`FR`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 exec-plan：
  - `docs/exec-plans/FR-0014-core-resource-capability-matching.md`
  - `docs/exec-plans/CHORE-0139-fr-0014-formal-spec-closeout.md`

## 实施目标

- 在进入 runtime 实现前，先冻结 Core 资源能力匹配的最小 input / output / error boundary，确保 matcher 只做“能力是否满足”的前置判断，不把 scope 漂移成 scheduler 或 provider selector。

## 分阶段拆分

- 阶段 1：`#193` 收口 formal spec，冻结 matcher 输入、输出、`matched / unmatched` 语义与错误边界。
- 阶段 2：后续实现 Work Item 基于本 formal spec 落 runtime matcher，并把 `unmatched` 与 `resource_unavailable` 外显口径接到 shared runtime 上。
- 阶段 3：后续实现 Work Item 在不改写本 FR 的前提下，与 `FR-0010` acquire 路径和 `FR-0012` 注入边界完成串联。

## 实现约束

- 不允许触碰的边界：
  - 不得在本事项中实现 provider 选择、资源编排、排序打分或 fallback 逻辑
  - 不得重新定义 `FR-0010` 的 bundle / lease / slot contract
  - 不得重新定义 `FR-0012` 的 Core 注入 boundary
  - 不得新增 `account / proxy` 之外的能力词汇
- 与上位文档的一致性约束：
  - 与 `AGENTS.md` 对“Core 负责运行时语义、formal spec 绑定 FR”的规则保持一致
  - 与 `docs/roadmap-v0-to-v1.md` 对 `v0.5.0` 资源能力匹配目标保持一致
  - 与 `FR-0013` 的声明形状、`FR-0015` 的批准词汇与错误边界保持一致

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-193-fr-0014-formal-spec`
- implementation 阶段：
  - matcher unit tests：验证 `matched` / `unmatched`、`none` 路径直通、非法声明 fail-closed
  - runtime contract tests：验证合法声明但能力不足时继续走 `resource_unavailable`，而不是误报 `invalid_resource_requirement`
- 手动验证：
  - 核对 matcher 文档中是否完全禁止 partial match、排序、打分、偏好、fallback、provider 选择与技术绑定字段
  - 核对 matcher 没有反向重写 `FR-0010` / `FR-0012` 的语义边界

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不涉及运行时代码或测试文件变更
- 暂不纳入 TDD 的模块与理由：
  - runtime matcher 仍属于后续实现 Work Item，本轮只冻结 requirement truth

## 并行 / 串行关系

- 可并行项：
  - `#192` 与 `#193` 可并行起草 formal spec，因为主要写集分离
- 串行依赖项：
  - `#193` 进入 spec review 前，必须消费 `FR-0015` 已冻结词汇与 `FR-0013` 已冻结声明形状
- 阻塞项：
  - 若 matcher contract 未先冻结，runtime 实现将被迫自行决定 partial match、错误口径与 scope 边界

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] matcher 已明确只消费 `account / proxy` 与 `AdapterResourceRequirementDeclaration`
