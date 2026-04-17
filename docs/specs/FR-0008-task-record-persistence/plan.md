# FR-0008 实施计划

## 关联信息

- item_key：`FR-0008-task-record-persistence`
- Issue：`#127`
- item_type：`FR`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 exec-plan：`docs/exec-plans/CHORE-0122-fr-0008-formal-spec-closeout.md`

## 实施目标

- 为 `v0.3.0` 冻结最小任务记录聚合、状态机、终态结果、执行日志与共享序列化边界，使 `FR-0008` 从 GitHub 意图进入可实现的 formal contract 状态。
- 明确 `#138` 与 `#139` 的实现分工：前者负责共享模型，后者负责本地持久化与序列化管线。
- 为 `FR-0009` 的 CLI 查询与同路径执行闭环提供稳定的持久化前提，而不在当前 formal spec 中提前定义查询 surface。

## 分阶段拆分

- 阶段 1：冻结 `FR-0008` formal spec 套件，明确任务状态模型、终态结果、执行日志与 fail-closed 持久化边界。
- 阶段 2：补齐 `contracts/README.md`、`data-model.md`、`risks.md`，把共享 payload、聚合根实体与高风险写入约束显式落盘。
- 阶段 3：通过 `#137` 的独立 spec PR 完成 spec review、guardian、checks 与 squash merge，使 `FR-0008` 成为 `implementation-ready` 的 formal input。
- 阶段 4：在独立实现 Work Item 中按 formal spec 推进：
  - `#138` 落地共享任务状态/结果/日志模型
  - `#139` 落地本地持久化与共享序列化管线
  - `#140` 负责父事项 closeout

## 实现约束

- 不允许触碰的边界：
  - 当前 PR 只允许修改 `docs/specs/FR-0008-task-record-persistence/`、当前事项 exec-plan，以及与其绑定的最小 release / sprint 索引
  - 不修改 `syvert/**`、`tests/**`、`scripts/**`
  - 不把 `FR-0009` 的 CLI 查询参数、展示格式或 UX 语义提前写进 `FR-0008`
  - 不把唯一合法实现形式绑定到某个固定文件名、某个固定目录布局或某个固定嵌入式存储引擎
- 与上位文档的一致性约束：
  - 与 `vision.md`、`docs/roadmap-v0-to-v1.md` 对 `v0.3.0`“最小任务与结果持久化闭环”的目标保持一致
  - 与 `AGENTS.md`、`WORKFLOW.md`、`docs/AGENTS.md` 对“formal spec 绑定 FR、Work Item 为唯一执行入口、formal spec 与实现分离”的契约保持一致
  - 与 `FR-0002`、`FR-0004`、`FR-0005` 已批准的共享 contract 保持兼容，不在持久化层重写 success / failed envelope 语义

## 测试与验证策略

- 单元测试：
  - 无。当前 PR 只收口 formal spec 与索引工件，不引入运行时代码
- 集成/契约测试：
  - `python3 scripts/spec_guard.py --mode ci --base-sha <merge-base> --head-sha <head>`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/governance_gate.py --mode ci --base-sha <merge-base> --head-sha <head> --head-ref issue-137-fr-0008-formal-spec`
  - `python3 scripts/open_pr.py --class spec --issue 137 --item-key CHORE-0122-fr-0008-formal-spec-closeout --item-type CHORE --release v0.3.0 --sprint 2026-S16 --title "spec: 收口 FR-0008 的 formal spec" --closing fixes --dry-run`
- 手动验证：
  - 对照 `docs/roadmap-v0-to-v1.md` 的 `v0.3.0` 目标、`#127` / `#137` 的 GitHub 说明与 `spec_review.md` rubric，确认任务状态、终态结果、执行日志、共享序列化与持久化边界已冻结
  - 确认 `FR-0008` 与 `FR-0009` 的边界清晰，未把 CLI 查询 surface 提前混入当前 formal spec

## TDD 范围

- 先写测试的模块：
  - 无。formal spec PR 本身不引入运行时代码
- 暂不纳入 TDD 的模块与理由：
  - `#138` 与 `#139` 的实现测试会在各自 implementation PR 中完成；当前 formal spec PR 只负责提供可执行 contract，不直接落地模型或存储代码

## 并行 / 串行关系

- 可并行项：
  - `spec.md`、`plan.md`、`contracts/README.md`、`data-model.md`、`risks.md` 的起草
  - `docs/releases/v0.3.0.md` 与 `docs/sprints/2026-S16.md` 的最小索引补齐
- 串行依赖项：
  - 必须先完成 `FR-0008` formal spec 冻结，`#138` / `#139` 才能进入实现 PR
  - `#138` 共享模型应先于或至少与 `#139` 的持久化管线 contract 对齐；`#139` 不应自行扩张状态或结果 schema
  - `#140` 父事项 closeout 必须等待 `#137/#138/#139` 完成并合入主干
- 阻塞项：
  - 若 formal spec 没有把状态/结果/日志的共享语义和 fail-closed 边界写清楚，后续实现会不可避免地在模型层重新做 requirement 决策
  - 若 `FR-0008` 与 `FR-0009` 边界不清，后续实现容易把查询 surface 和持久化 contract 混在同一 PR

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
- [ ] `accepted -> running -> succeeded | failed` 的最小状态语义、终态结果复用规则与 fail-closed 写入边界已冻结
- [ ] `FR-0008` 与 `FR-0009` 的责任边界已冻结

## spec review 结论

- 结论目标：把 `FR-0008` 从“需要任务结果可持久化”的 issue 意图推进到可直接指导实现的 formal contract。
- 审查关注：状态/结果/日志是否仍围绕一条共享任务记录聚合；持久化失败是否真正 fail-closed；是否把 CLI 查询 surface 错误混入本 FR。
- implementation-ready 判定：当前 PR 通过 spec review 并满足进入实现前条件后，`#138` 与 `#139` 才可以把模型与持久化实现推进到独立 implementation PR。
