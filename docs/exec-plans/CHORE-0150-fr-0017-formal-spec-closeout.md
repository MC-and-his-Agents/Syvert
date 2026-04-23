# CHORE-0150-fr-0017-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0150-fr-0017-formal-spec-closeout`
- Issue：`#226`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0017-runtime-failure-observability/`
- 关联 PR：`待创建`
- 状态：`active`
- active 收口事项：`CHORE-0150-fr-0017-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0017` formal spec 套件，冻结运行时失败可观测性的最小 failure signal、structured log、execution metric contract，并明确其与 `task_id`、TaskRecord、failed envelope、resource trace、`FR-0016` timeout / retry / concurrency 结果的关联规则。

## 范围

- 本次纳入：
  - `docs/specs/FR-0017-runtime-failure-observability/`
  - `docs/exec-plans/FR-0017-runtime-failure-observability.md`
  - `docs/exec-plans/CHORE-0150-fr-0017-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - runtime observability implementation
  - 日志采集后端、指标存储、dashboard
  - `docs/releases/**`
  - `docs/sprints/**`
  - 相邻 FR formal spec 或 implementation 文件

## 当前停点

- `issue-226-fr-0017-formal-spec` 已作为 `#226` 的独立 spec worktree 建立。
- 当前回合只允许修改 `FR-0017` formal spec 套件与两个 exec-plan，禁止越界到 runtime / tests / scripts / release / sprint 索引或相邻 FR。
- `FR-0017` formal spec 套件与 requirement container / Work Item exec-plan 已在当前分支首次落盘；当前 PR 尚未创建。

## 下一步动作

- 指定 formal spec / docs / workflow guard 已通过；下一步进入 spec review / PR 创建流程，并保持 `关联 PR` 与 GitHub 真相同步。
- `spec review` 通过后，按 `plan.md` 进入 `#227` runtime implementation，再由 `#228` parent closeout 收口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 把“运行时失败如何最小可观测、可关联、可计数”推进为 implementation-ready 的 formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0017` 的 formal spec closeout Work Item。
- 阻塞：
  - 若失败分类投影不先冻结，`#227` runtime implementation 可能把 timeout / retry / concurrency 误写成新的错误分类。
  - 若 TaskRecord、failed envelope、resource trace 与 runtime result 的关联规则不先冻结，后续失败排查会继续依赖不可审查的 adapter 私有日志。

## 已验证项

- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`docs/specs/README.md` 与 formal spec 模板要求。
- 已核对 `FR-0005`、`FR-0008`、`FR-0011`、`FR-0013` 与 `CHORE-0138` 的相关边界和 closeout 风格。
- 已确认当前 worktree 初始状态未存在 `FR-0017` formal spec 套件或目标 exec-plan。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过

## 未决风险

- `FR-0016` formal spec 当前不在本 worktree 可见范围内；本 FR 只能以“消费 timeout / retry / concurrency 运行时结果引用”的方式表达关联，不能替代其本体 contract。
- 若后续审查要求更严格的字段命名或 runtime result ref 形状，需要在本 formal spec 内调整，但仍不得越界到实现文件。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0017` formal spec 套件与当前 closeout exec-plan 的文档增量，不回退其他 worker 的文件或相邻 FR。

## checkpoint 记录方式

- semantic checkpoint：使用通过全部 formal-spec 门禁后的 commit SHA 作为语义 checkpoint。
- review-sync follow-up：若后续只回填当前受审 PR、checks 或 checkpoint metadata，不把 metadata-only 修改伪装成新的语义 checkpoint。

## 最近一次 checkpoint 对应的 head SHA

- `4a7eec234e322f10100acb328d37623cd7c16538`
