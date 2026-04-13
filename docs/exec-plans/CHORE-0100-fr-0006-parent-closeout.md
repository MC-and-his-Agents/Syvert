# CHORE-0100-fr-0006-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0100-fr-0006-parent-closeout`
- Issue：`#110`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- 关联 PR：`#111`
- 状态：`active`
- active 收口事项：`CHORE-0100-fr-0006-parent-closeout`

## 目标

- 在不引入新实现、新 formal spec 语义或额外 implementation Work Item 的前提下，通过合法 Work Item `#110` 完成父 FR `#66` 的最终 closeout。
- 把 `FR-0006` 的 formal spec、`#102/#101/#103` 实现、release / sprint 索引与 GitHub issue 真相映射回同一条父事项证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0006-adapter-contract-test-harness.md`
  - `docs/exec-plans/CHORE-0100-fr-0006-parent-closeout.md`
  - `docs/exec-plans/CHORE-0051-fr-0006-formal-spec-closeout.md`
  - `docs/exec-plans/CHORE-0102-fr-0006-fake-adapter-harness.md`
  - `docs/exec-plans/CHORE-0101-fr-0006-validation-tooling.md`
  - `docs/exec-plans/CHORE-0103-fr-0006-contract-samples-minimal-automation.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - GitHub `#66` issue 正文修正
  - GitHub `#66` closeout 评论
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0006` formal spec 语义改写
  - `FR-0004`、`FR-0005`、`FR-0007` 或其它 FR 的事项状态调整

## 当前停点

- `origin/main@5fcdbf60885c988c1cf7817852195495547924da` 已包含 `FR-0006` closeout 所需的关键前提：PR `#76`、`#104`、`#108`、`#109`。
- `#74` 已由 PR `#76` 合入并关闭；`#102` 已由 PR `#104` 合入并关闭；`#101` 已由 PR `#108` 合入并关闭；`#103` 已由 PR `#109` 合入并关闭。
- 当前 `FR-0006` GitHub closeout 仍包含 Work Item `#110` 与父 FR `#66`；`#83` 为已关闭的历史镜像，不得重新打开。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-110-chore-fr-0006`。

## 下一步动作

- 把 `FR-0006` requirement container、`#102/#101/#103` 历史实现记录、release / sprint 索引与 `#110` 对齐到“唯一 active closeout 入口”后的主干真相。
- 当前受审 PR：`#111`
- 当前 head 已完成门禁与受控 PR 创建，下一步进入 reviewer / guardian / merge gate。
- 合并后先关闭当前 Work Item `#110`，再修正 GitHub `#66` 正文、发布 `#66` closeout 评论并关闭 `#66`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 完成 `FR-0006` 父事项收口，使 adapter contract test harness requirement 已被 formal spec、主干实现、验证证据与 GitHub 关闭语义完整消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0006` 父事项 closeout Work Item。
- 阻塞：
  - 必须先保证 `#74/#102/#101/#103` 全部关闭，且 release / sprint / exec-plan 不再把 `#103` 误表述为当前 active 实现入口。
  - 必须在关闭前修正 `#66` 正文，使其反映 formal spec、fake adapter / harness host、validator、contract samples / automation 与当前 parent closeout 入口的主干真相。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0006-adapter-contract-test-harness/`
- `gh issue view 66 --repo MC-and-his-Agents/Syvert --json state,body,title,url`
  - 结果：`#66` 当前为 `OPEN`，且正文尚未体现父事项 closeout Work Item `#110`
- `gh issue view 74 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#74` 为 `CLOSED`
- `gh issue view 101 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#101` 为 `CLOSED`
- `gh issue view 102 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#102` 为 `CLOSED`
- `gh issue view 103 --repo MC-and-his-Agents/Syvert --json state,closedAt,url`
  - 结果：`#103` 为 `CLOSED`
- `gh issue view 110 --repo MC-and-his-Agents/Syvert --json state,title,url`
  - 结果：`#110` 已建立为当前父事项 closeout Work Item
- `gh issue view 83 --repo MC-and-his-Agents/Syvert --json state,title,url`
  - 结果：`#83` 保持 `CLOSED`
- `gh pr view 76 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 104 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 108 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 109 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=5fcdbf60885c988c1cf7817852195495547924da`

## closeout 证据

- formal spec 证据：PR `#76` 已把 adapter contract test harness formal spec 合入主干，对应 `docs/specs/FR-0006-adapter-contract-test-harness/`
- implementation 证据：
  - PR `#104` / `#102`：落地 fake adapter、adapter profile 声明与最小 harness host，经标准 registry / Core 路径执行
  - PR `#108` / `#101`：落地 validator 与 `pass`、`legal_failure`、`contract_violation`、`execution_precondition_not_met` 四类 verdict 分类
  - PR `#109` / `#103`：落地 contract samples、最小 automation 聚合执行与自动化断言，并固定四个最小样例 verdict
- 验证证据：`python3 -m unittest tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation`
- release / sprint 证据：`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 将在本回合回链 `#66/#74/#102/#101/#103/#110` 与 PR `#76/#104/#108/#109`
- GitHub closeout 证据：当前剩余 GitHub closeout issue 为 active Work Item `#110` 与父 FR `#66`；本回合合入后应先关闭 `#110`，再关闭 `#66`

## GitHub closeout 工件

- `#66` 正文修正目标：
  - 明确 formal spec 已由 PR `#76` 合入主干
  - 明确 fake adapter / harness host 已由 `#102` / PR `#104` 落地
  - 明确 validator 已由 `#101` / PR `#108` 落地
  - 明确 contract samples / automation 已由 `#103` / PR `#109` 落地
  - 将父事项 closeout 入口补为 `#110`
  - 子 Work Item 保持：`#74`、`#102`、`#101`、`#103`、`#110`
- `#66` closeout 评论草案：
  - `FR-0006` formal spec 已由 PR `#76` 合入主干，spec 真相位于 `docs/specs/FR-0006-adapter-contract-test-harness/`
  - `#102` / PR `#104` 已完成 fake adapter 与最小 harness host，经标准 adapter 宿主路径消费 capability 声明与合法/非法样例
  - `#101` / PR `#108` 已完成 validator 与四类 verdict 分类，且不改写 runtime 上位错误模型语义
  - `#103` / PR `#109` 已完成 contract samples、最小 automation 与四类最小样例断言
  - 验证命令：`python3 -m unittest tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_contract_harness_host tests.runtime.test_contract_harness_validation_tool tests.runtime.test_contract_harness_automation`
  - 当前父事项 closeout 已由 `#110` 承接，`docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 与 active exec-plan 已与 GitHub 真相一致

## 未决风险

- 若 `#66` 关闭前仍把 `#103` 或 release / sprint 索引标记为当前 active 实现入口，会留下双 active 执行语义。
- 若 `#66` 关闭前不修正 GitHub 正文与 closeout 评论，后续回溯 `FR-0006` 的 formal spec / implementation / closeout 证据仍需手工拼接。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 `docs/exec-plans/FR-0006-adapter-contract-test-harness.md`、`docs/exec-plans/CHORE-0100-fr-0006-parent-closeout.md`、`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的增量修改。
- GitHub 侧回滚：
  - 若已编辑 `#66` 正文但 PR 未合入，恢复 `#66` 到 closeout 前正文，并保留 `#66/#110` 为 `OPEN`
  - 若已发布 `#66` closeout 评论但发现仓内工件仍不一致，在 `#66` 追加纠正评论并停止关闭动作
  - 若 `#66` 已关闭后发现 closeout 事实错误，先重新打开 `#66`，再通过独立 revert PR 与新的 closeout 回合修复仓内 / GitHub 状态

## 最近一次 checkpoint 对应的 head SHA

- `5fcdbf60885c988c1cf7817852195495547924da`
- 说明：该 checkpoint 已包含 `FR-0006` formal spec、fake adapter / harness host、validation tool、contract samples / automation 与 release / sprint 的主干事实；当前回合仅补齐父事项 closeout 工件与 GitHub 关闭语义。
