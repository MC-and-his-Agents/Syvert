# CHORE-0159 FR-0019 parent closeout 执行计划

## 关联信息

- item_key：`CHORE-0159-fr-0019-parent-closeout`
- Issue：`#235`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 父 FR：`#222`
- 关联 spec：`docs/specs/FR-0019-v0-6-operability-release-gate/`
- 状态：`active`

## 目标

- 在不引入新 runtime 或 formal spec 语义的前提下，收口 `FR-0019` 父事项。
- 将 formal spec、operability gate runtime、source evidence / renderer、GitHub issue / Project 状态与当前主干事实对齐。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0159-fr-0019-parent-closeout.md`
  - `docs/exec-plans/FR-0019-v0-6-operability-release-gate.md` 的 inactive requirement container closeout 索引
  - 合入后 GitHub `#222/#235` 状态与 Project closeout 对齐
- 本次不纳入：
  - `syvert/**` runtime 代码
  - `tests/**` 测试实现
  - `FR-0019` formal spec 语义变更
  - upstream actual_result extraction layer 或外部 evidence pipeline
  - release / sprint 最终发布索引；该动作留给 `#236`

## 当前停点

- `#233` formal spec closeout 已由 PR `#243` squash merge，merge commit `151a6ee9debebb07c77196ab44b9145f2a39becb`。
- `#234` operability gate runtime 已由 PR `#252` squash merge，merge commit `71983563b48d2712248754fc3f56ead0c135fd5f`。
- `#233` 与 `#234` GitHub issue 均已关闭。
- `#222` 仍为 `open`，等待本父事项 closeout 回写后关闭。
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-235-chore-fr-0019`
- 当前主干基线：`71983563b48d2712248754fc3f56ead0c135fd5f`

## 下一步动作

- 本 PR 为 docs-only closeout，PR class 必须保持 `docs`。
- 通过 CI、reviewer、guardian 与 merge gate。
- 合入后 fast-forward main。
- 更新 `#235` 正文为已完成并关闭，Project 状态切到 `Done`。
- 在 `#222` 发布 closeout 评论，引用 `#233/#234/#235` 与 PR `#243/#252`，随后关闭父 FR 并切 Project 到 `Done`。
- 退役 `issue-235-chore-fr-0019` 分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 完成 `FR-0019` 父事项收口，使 `#236` release / sprint closeout 可以直接引用 operability gate formal spec、runtime、source evidence artifact、renderer 与 GitHub closeout truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0019` parent closeout Work Item。
- 阻塞：
  - `#236` release closeout 前必须完成 `#222` 父 FR 状态同步。

## closeout 证据

- formal spec 证据：
  - PR `#243`：冻结 `v0.6.0` operability release gate 与 mandatory matrix，覆盖 `timeout_retry_concurrency`、`failure_log_metrics`、`http_submit_status_result`、`cli_api_same_path`，并明确其叠加 `FR-0007` baseline gate。
  - 主干路径：`docs/specs/FR-0019-v0-6-operability-release-gate/`
- runtime / gate evidence：
  - PR `#252`：新增 `syvert/operability_gate.py`、`tests/runtime/test_operability_gate.py`、`tests/runtime/render_operability_gate_artifact.py` 与 `docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json`。
  - generated gate result 不入库；review / merge 时通过 `python3 -m tests.runtime.render_operability_gate_artifact --execution-revision $(git rev-parse HEAD)` 生成 `/tmp/CHORE-0158-operability-gate-result.json`。
  - `#252` 采用人工裁决：`#234` 保持 source evidence + renderer 范围，不扩展 upstream actual_result extractor；裁决记录已写入 PR comment 与 `CHORE-0158` exec-plan。
- upstream parent truth：
  - `FR-0016` parent closeout：`#225`，为 `timeout_retry_concurrency` 维度提供 runtime truth。
  - `FR-0017` parent closeout：`#228`，为 `failure_log_metrics` 维度提供 runtime truth。
  - `FR-0018` parent closeout：`#232`，为 `http_submit_status_result` 与 `cli_api_same_path` 维度提供 runtime / same-path truth。

## 已验证项

- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/pulls/243`
  - 结果：`merged=true`，`merged_at=2026-04-23T19:08:24Z`，`merge_commit_sha=151a6ee9debebb07c77196ab44b9145f2a39becb`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/pulls/252`
  - 结果：`merged=true`，`merged_at=2026-04-26T04:50:13Z`，`merge_commit_sha=71983563b48d2712248754fc3f56ead0c135fd5f`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/233`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/234`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/222`
  - 结果：`state=open`，等待本 closeout PR 合入后关闭
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/235`
  - 结果：`state=open`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 222 --json projectItems --jq '.projectItems'`
  - 结果：Project `Syvert 主交付看板` status 为 `Todo`，等待本 closeout PR 合入后切到 `Done`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 235 --json projectItems --jq '.projectItems'`
  - 结果：Project `Syvert 主交付看板` status 为 `In Progress`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过，`docs-guard 通过。`
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过，`workflow-guard 通过。`
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR class: docs`，`变更类别: docs`，`PR scope 校验通过。`
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过，`governance-gate 通过。`

## 待完成

- 创建并合入本 closeout PR。
- 合入后将 `#235` 正文更新为已完成并关闭，Project 切到 `Done`。
- 回写并关闭父 FR `#222`，说明 formal spec 与 operability gate runtime / evidence 已合入主干。
- fast-forward main，退役 `issue-235-chore-fr-0019` 分支与 worktree。

## 未决风险

- 若 `#222` 关闭前未引用 `#233/#234/#235` 与 PR `#243/#252`，后续 `#236` release closeout 需要手工拼接 FR-0019 closeout truth。
- 若误在本事项修改 runtime、tests 或 formal spec，可能破坏 `#234` 已合入的 gate runtime / evidence 边界。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本事项对 `docs/exec-plans/*FR-0019*` closeout 元数据的修改。
- GitHub 侧回滚：若已关闭 `#222/#235` 后发现 closeout 事实错误，重新打开对应 issue，追加纠正评论，并通过新的 closeout Work Item 修复仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- 当前主干基线：`71983563b48d2712248754fc3f56ead0c135fd5f`。
- 当前可恢复 checkpoint：`fdcd227b3d895596a62d073d42046e59c50ec1d2`，包含本 exec-plan 首个版本化恢复工件与 `FR-0019` inactive requirement container closeout 索引。
- 后续 review-sync 若只更新验证记录或 GitHub 状态，不推进新的 formal spec / runtime 语义。
