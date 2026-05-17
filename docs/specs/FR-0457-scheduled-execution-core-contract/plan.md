# FR-0457 Scheduled Execution Core Contract Plan

## 关联信息

- item_key：`FR-0457-scheduled-execution-core-contract`
- Issue：`#457`
- item_type：`FR`
- release：`unbound`
- sprint：`unbound`
- 关联 exec-plan：`docs/exec-plans/CHORE-0458-scheduled-execution-spec.md`

## 实施目标

本 Work Item 只建立 formal spec admission 和边界骨架，后续 PR 才能进入 runtime carrier、consumer migration、evidence 或 closeout。Scheduled Execution 的核心目标是定义 Core 延迟 / 周期触发如何复用现有 Core 主路径。

## 分阶段拆分

- spec：完善 formal spec suite、数据模型、contract README、risk inventory、fixture/error/evidence inventory。
- runtime：实现 schedule carriers、validators、due claiming 与 Core main-path execution wrapper。
- consumers：迁移 TaskRecord、result query、runtime admission、compatibility 与 observability consumers。
- evidence：交付 delayed、recurring、missed、duplicate claim、retry exhausted、unknown outcome、manual recovery 的 sanitized evidence。
- closeout：按显式 release/sprint 绑定完成 release index、sprint index、GitHub issue 与 published truth reconciliation。

## 实现约束

- schedule target 必须复用现有 single-task 或 batch request，不重新定义 item result envelope。
- schedule record 只表达触发时间、触发规则、目标任务请求与执行策略。
- due claiming 必须防止多 worker 重复执行同一 occurrence。
- 本 admission 不实现 runtime、不创建 scheduler service、不定义上层 workflow DSL。
- release 与 sprint 仍未绑定，后续执行必须显式决定。

## 测试与验证策略

- spec guard 覆盖 formal spec 最小结构。
- docs guard / governance gate / git diff check 覆盖仓内 truth 与 admission 一致性。
- 后续 runtime Work Item 必须增加 delayed、recurring、missed、duplicate claim、retry exhausted、unknown outcome、manual recovery 的 focused tests。

## TDD 范围

本 Work Item 不进入 runtime TDD。后续 runtime Work Item 的首批 TDD 范围应覆盖 schedule admission validation、occurrence claiming、missed run policy 与 Core main-path execution handoff。

## 并行 / 串行关系

- 当前 spec admission 是首个串行入口。
- runtime、consumer、evidence、closeout Work Items 均阻塞于 formal spec PR 合入。
- write-side capability 仍阻塞于 Scheduled Execution 与 safety gate 的后续成熟度，不在当前范围内。

## 进入实现前条件

- `#456/#457/#458` GitHub issue 链可定位且 scope/non-goals/依赖/验证方式明确。
- `v1.6.0` post-release truth 已对齐，Batch / Dataset Foundation 可作为 Scheduled Execution 依赖。
- formal spec suite 与 fixture / error / evidence inventory 已建立；后续 runtime implementation 必须以这些 public vocabulary 和 sanitized cases 为输入。
- `docs/specs/FR-0457-scheduled-execution-core-contract/spec-review.md` 已记录 admission-ready / implementation-not-ready 结论。

## Spec Review Gate

- 当前 admission PR 合入不等于 runtime implementation 可以开始；它只建立 `FR-0457` 的 formal spec 入口和最小 public vocabulary。
- 进入 runtime Work Item 前必须具备本 PR 的 spec review / guardian 通过结论，并确认没有未解决的 request-changes finding。
- 未决风险必须在后续 runtime Work Item admission 中重新消费：release/sprint 仍未绑定，runtime behavior 未实现，scheduler service / UI / BI / write-side / provider selector 仍不在范围内。
- 后续 runtime Work Item 必须重新运行 spec/docs/governance gates，并以 `docs/exec-plans/artifacts/CHORE-0458-scheduled-execution-fixture-inventory.md` 作为 TDD 和 evidence 输入。
