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

## 实施目标

- 在进入实现前冻结双参考适配器资源能力证据记录 contract，使 `v0.5.0` 的资源需求声明、资源能力匹配与后续证据收口都消费同一份正式证据 truth。

## 分阶段拆分

- 阶段 1：`#194` 收口 formal spec，冻结 evidence record carrier、共享词汇表与研究边界。
- 阶段 2：`#197` 基于该 formal spec 落盘双参考适配器真实证据，并把每个候选抽象映射到 formal evidence record。
- 阶段 3：`#192` 与 `#193` 在不改写共享词汇表的前提下，分别落地 adapter 资源需求声明与 Core 资源能力匹配。

## 实现约束

- 不允许触碰的边界：
  - 不得在本事项中加入 `FR-0013` 的需求声明 carrier 或 `FR-0014` 的匹配算法
  - 不得提前引入第三个平台、provider 生态或具体浏览器技术绑定
  - 不得重写 `FR-0010` / `FR-0011` / `FR-0012` 已冻结的运行时 contract
- 与上位文档的一致性约束：
  - 与 `docs/roadmap-v0-to-v1.md` 对 `v0.5.0` 的“证据不足时保持最小资源模型”约束保持一致
  - 与 `AGENTS.md` 对“Core 负责运行时语义，Adapter 负责平台语义”的规则保持一致
  - 与 `FR-0004` 的 `adapter_key / capability` 共享输入语义保持一致
  - 与 `#188/#189/#190/#191` 的阶段 / FR 边界保持一致

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-194-fr-0015-formal-spec`
- implementation 阶段：
  - evidence record schema 验证：检查 `DualReferenceResourceCapabilityEvidenceRecord` 字段完备性、`shared_status` 枚举与 `decision` 约束
  - evidence coverage 验证：检查双参考适配器的共性语义、单平台特例与被拒绝候选都能映射到正式记录
  - consumer regression：检查 `#192/#193` 不会消费 `managed_account / managed_proxy` 之外的新标识
- 手动验证：
  - 逐条核对 `FR-0015` 与 `FR-0013 / FR-0014` 的边界，确保 evidence record 不长成第二套需求声明或匹配算法
  - 逐条核对 research 中的共性 / 特例 / rejected candidate 与 `v0.4.0` reference adapter 真实运行事实一致

## TDD 范围

- 先写测试的模块：
  - `DualReferenceResourceCapabilityEvidenceRecord` 的字段与枚举校验
  - `shared_status` / `decision` 与批准词汇表的一致性校验
  - `#192/#193` 仅消费已批准词汇表的治理回归
- 暂不纳入 TDD 的模块与理由：
  - 第三个平台扩张、provider 生态与复杂匹配策略不属于 `v0.5.0` 当前 formal spec 范围

## 并行 / 串行关系

- 可并行项：
  - `#194` 可与 `#192/#193` 的只读准备并行推进，因为当前主要写集仍在 `FR-0015` formal spec 目录与两个 exec-plan
- 串行依赖项：
  - `#192` 与 `#193` 必须在本 FR 冻结共享词汇表之后再进入 formal spec 实质收口
  - `#197` 必须复用本 FR 的 evidence record contract，而不是另建新 schema
- 阻塞项：
  - 若共享能力词汇表未先冻结，`#192/#193` 会各自长出不同能力标识，导致 `v0.5.0` 再次出现影子抽象

## 进入实现前条件

- [ ] `FR-0015` formal spec 已通过 spec review
- [ ] `DualReferenceResourceCapabilityEvidenceRecord` 最小字段集合已冻结
- [ ] `managed_account / managed_proxy` 作为唯一批准共享能力标识已冻结
- [ ] `#192/#193` 只能消费已批准词汇表的上游约束已冻结

## spec review 结论

- 结论目标：把“所有新增资源能力抽象都必须由双参考适配器证据解释”的 GitHub 意图推进到 implementation-ready 的 formal evidence contract。
- 审查关注：
  - 是否形成单一 evidence record carrier，而不是 issue 评论、笔记和实现夹具各自保存一套事实
  - 是否把批准词汇表压到有限集合，而不是给后续事项留下无限扩张空间
  - 是否把共性语义、单平台特例与 rejected candidate 清楚切开
  - 是否明确要求 `#192/#193` 只能消费 `FR-0015` 已批准的共享能力标识
- implementation-ready 判定：formal spec 通过 spec review 且进入实现前条件满足后，`#197`、`#192` 与 `#193` 才可继续推进各自回合。
