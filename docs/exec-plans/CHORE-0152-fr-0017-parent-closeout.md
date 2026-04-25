# CHORE-0152 FR-0017 parent closeout 执行计划

## 关联信息

- item_key：`CHORE-0152-fr-0017-parent-closeout`
- Issue：`#228`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 父 FR：`#220`
- 关联 spec：`docs/specs/FR-0017-runtime-failure-observability/`
- 状态：`active`

## 目标

- 在不引入新 runtime 或 formal spec 语义的前提下，收口 `FR-0017` 父事项。
- 将 formal spec、runtime implementation、验证证据、GitHub issue / Project 状态与当前主干事实对齐。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0152-fr-0017-parent-closeout.md`
  - `docs/exec-plans/FR-0017-runtime-failure-observability.md` 的 inactive requirement container closeout 索引
  - 合入后 GitHub `#220/#228` 状态与 Project closeout 对齐
- 本次不纳入：
  - `syvert/**` runtime 代码
  - `tests/**` 测试实现
  - `FR-0017` formal spec 语义变更
  - `FR-0019/#234` operability gate matrix
  - release / sprint 最终发布索引；该动作留给 `#236`

## 当前停点

- `#226` formal spec closeout 已由 PR `#239` squash merge，merge commit `3bff42393da63da3100a5a99dc0c16f043a6b180`。
- `#227` runtime implementation 已由 PR `#249` squash merge，merge commit `d0ae78b6c96789f0c16b541bac14694dd1ad9df4`。
- `#226` 与 `#227` GitHub issue 均已关闭。
- `#220` 仍为 `open`，等待本父事项 closeout 回写后关闭。
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-228-chore-fr-0017`
- 当前主干基线：`d0ae78b6c96789f0c16b541bac14694dd1ad9df4`

## 下一步动作

- 当前 closeout PR：`#250 https://github.com/MC-and-his-Agents/Syvert/pull/250`
- 本 PR 为 docs-only closeout，PR class 必须保持 `docs`。
- 通过 CI、reviewer、guardian 与 merge gate。
- 合入后 fast-forward main。
- 更新 `#228` 正文为已完成并关闭，Project 状态切到 `Done`。
- 在 `#220` 发布 closeout 评论，引用 `#226/#227/#228` 与 PR `#239/#249`，随后关闭父 FR 并切 Project 到 `Done`。
- 退役 `issue-228-chore-fr-0017` 分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 完成 `failure_log_metrics` 维度的父事项收口，使后续 `FR-0019/#234` operability gate matrix 可以直接引用 `FR-0017` 的 formal spec、runtime evidence 与 GitHub closeout truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0017` parent closeout Work Item。
- 阻塞：
  - `#234` gate matrix 的 `failure_log_metrics` 维度需要 `FR-0017` closeout truth。
  - `#236` release closeout 前必须完成 `#220` 父 FR 状态同步。

## closeout 证据

- formal spec 证据：
  - PR `#239`：冻结 `RuntimeFailureSignal`、`RuntimeStructuredLogEvent`、`RuntimeExecutionMetricSample`，以及它们与 failed envelope、TaskRecord、resource trace、`ExecutionAttemptOutcome` / `ExecutionControlEvent` 的关联规则。
  - 主干路径：`docs/specs/FR-0017-runtime-failure-observability/`
- runtime 证据：
  - PR `#249`：在 Core path 中实现失败信号、结构化日志、最小指标、TaskRecord additive carrier、append-only/idempotent observability replay、resource/runtime refs 校验，以及 success envelope 不改写边界。
  - 关键验证：`tests/runtime/test_runtime_observability.py`、`tests/runtime/test_task_record.py`、`tests/runtime/test_task_record_store.py`、`tests/runtime/test_execution_control.py` 覆盖 failure projection、retry / timeout / concurrency 投影、persistence / observability write failure、TaskRecord durable truth 与 refs 形状校验。

## 已验证项

- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/pulls/239`
  - 结果：`merged=true`，`merged_at=2026-04-23T17:31:48Z`，`merge_commit_sha=3bff42393da63da3100a5a99dc0c16f043a6b180`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/pulls/249`
  - 结果：`merged=true`，`merged_at=2026-04-25T08:05:15Z`，`merge_commit_sha=d0ae78b6c96789f0c16b541bac14694dd1ad9df4`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/226`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/227`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/220`
  - 结果：`state=open`，等待本 closeout PR 合入后关闭
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 220 --json projectItems --jq '.projectItems'`
  - 结果：Project `Syvert 主交付看板` status 为 `Todo`，等待本 closeout PR 合入后切到 `Done`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 228 --json projectItems --jq '.projectItems'`
  - 结果：Project `Syvert 主交付看板` status 为 `In Progress`
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过，`governance-gate 通过。`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过，`docs-guard 通过。`
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过，`workflow-guard 通过。`
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR class: docs`，`变更类别: docs`，`PR scope 校验通过。`

## 待完成

- 合入本 closeout PR。
- 合入后将 `#228` 正文更新为已完成并关闭，Project 切到 `Done`。
- 回写并关闭父 FR `#220`，说明 formal spec 与 runtime evidence 已合入主干。
- fast-forward main，退役 `issue-228-chore-fr-0017` 分支与 worktree。

## 未决风险

- 若 `#220` 关闭前未引用 `#226/#227/#228` 与 PR `#239/#249`，后续 `FR-0019/#234` gate matrix 回溯 `failure_log_metrics` 证据时需要手工拼接。
- 若误在本事项修改 runtime 或 formal spec，可能破坏 `#227` 已通过 guardian 的实现边界。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本事项对 `docs/exec-plans/*FR-0017*` closeout 元数据的修改。
- GitHub 侧回滚：若已关闭 `#220/#228` 后发现 closeout 事实错误，重新打开对应 issue，追加纠正评论，并通过新的 closeout Work Item 修复仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- 当前主干基线：`d0ae78b6c96789f0c16b541bac14694dd1ad9df4`。
- 当前可恢复 checkpoint：`410971a147897e5fbc8f5fdc2d5df1d1559db9e7`，包含本 exec-plan 首个版本化恢复工件与 `FR-0017` inactive requirement container closeout 索引。
- 后续 review-sync 若只更新验证记录或 GitHub 状态，不推进新的 formal spec / runtime 语义。
