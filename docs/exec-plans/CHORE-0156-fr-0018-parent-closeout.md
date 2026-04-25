# CHORE-0156 FR-0018 parent closeout 执行计划

## 关联信息

- item_key：`CHORE-0156-fr-0018-parent-closeout`
- Issue：`#232`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 父 FR：`#221`
- 关联 spec：`docs/specs/FR-0018-http-task-api-same-core-path/`
- 状态：`active`

## 目标

- 在不引入新 runtime 或 formal spec 语义的前提下，收口 `FR-0018` 父事项。
- 将 formal spec、HTTP endpoint runtime、CLI/API same-path evidence、GitHub issue / Project 状态与当前主干事实对齐。

## 范围

- 本次纳入：
  - `docs/exec-plans/CHORE-0156-fr-0018-parent-closeout.md`
  - `docs/exec-plans/FR-0018-http-task-api-same-core-path.md` 的 inactive requirement container closeout 索引
  - 合入后 GitHub `#221/#232` 状态与 Project closeout 对齐
- 本次不纳入：
  - `syvert/**` runtime 代码
  - `tests/**` 测试实现
  - `FR-0018` formal spec 语义变更
  - `FR-0019/#234` operability gate matrix
  - release / sprint 最终发布索引；该动作留给 `#236`

## 当前停点

- `#229` formal spec closeout 已由 PR `#241` squash merge，merge commit `212f479afab3712a70c7cd5390ef1346cb96ba04`。
- `#230` HTTP endpoint runtime 已由 PR `#245` squash merge，merge commit `64e3ece230f0c587ba4b809c17177b1f37665504`。
- `#231` CLI/API same-path regression evidence 已由 PR `#246` squash merge，merge commit `65657a49536eb7ad83ea1cf666d0a43f233f67fa`。
- `#229`、`#230` 与 `#231` GitHub issue 均已关闭。
- `#221` 仍为 `open`，等待本父事项 closeout 回写后关闭。
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-232-chore-fr-0018`
- 当前主干基线：`394d48a7be861de742aae439c38e18625cc44193`

## 下一步动作

- 当前 closeout PR：`#251 https://github.com/MC-and-his-Agents/Syvert/pull/251`
- 本 PR 为 docs-only closeout，PR class 必须保持 `docs`。
- 通过 CI、reviewer、guardian 与 merge gate。
- 合入后 fast-forward main。
- 更新 `#232` 正文为已完成并关闭，Project 状态切到 `Done`。
- 在 `#221` 发布 closeout 评论，引用 `#229/#230/#231/#232` 与 PR `#241/#245/#246`，随后关闭父 FR 并切 Project 到 `Done`。
- 退役 `issue-232-chore-fr-0018` 分支与 worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 完成 `http_submit_status_result` 与 `cli_api_same_path` 维度的父事项收口，使后续 `FR-0019/#234` operability gate matrix 可以直接引用 `FR-0018` 的 formal spec、runtime evidence、same-path evidence 与 GitHub closeout truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0018` parent closeout Work Item。
- 阻塞：
  - `#234` gate matrix 的 `http_submit_status_result` 与 `cli_api_same_path` 维度需要 `FR-0018` closeout truth。
  - `#236` release closeout 前必须完成 `#221` 父 FR 状态同步。

## closeout 证据

- formal spec 证据：
  - PR `#241`：冻结 `POST /v0/tasks`、`GET /v0/tasks/{task_id}`、`GET /v0/tasks/{task_id}/result`，以及 method / path / status mapping、shared failed envelope transport carrier 与 same-core-path acceptance criteria。
  - 主干路径：`docs/specs/FR-0018-http-task-api-same-core-path/`
- HTTP runtime 证据：
  - PR `#245`：新增 `syvert/http_api.py` 的 stdlib WSGI transport 与 `TaskHttpService`，并证明 submit / status / result 复用 `execute_task_with_record`、`TaskRecordStore`、`task_record_to_dict` 与 shared envelope。
  - 关键验证：`tests/runtime/test_http_api.py` 覆盖 ingress / routing / status mapping / result boundary / fail-closed JSON envelope。
- CLI/API same-path 证据：
  - PR `#246`：新增 `tests/runtime/test_cli_http_same_path.py`，证明 CLI `run/query` 与 HTTP `submit/status/result` 在等价任务语义下观察同一 durable `TaskRecord`、terminal envelope、shared failed envelope、execution-control truth 与 observability refs。
  - 关键验证：success shared truth、CLI-created HTTP-read、HTTP-created CLI-read、terminal failed envelope、pre-admission invalid input、durable record unavailable、nonterminal result boundary、runtime refs preserved。

## 已验证项

- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/pulls/241`
  - 结果：`merged=true`，`merged_at=2026-04-23T18:17:59Z`，`merge_commit_sha=212f479afab3712a70c7cd5390ef1346cb96ba04`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/pulls/245`
  - 结果：`merged=true`，`merged_at=2026-04-24T11:29:36Z`，`merge_commit_sha=64e3ece230f0c587ba4b809c17177b1f37665504`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/pulls/246`
  - 结果：`merged=true`，`merged_at=2026-04-24T12:59:53Z`，`merge_commit_sha=65657a49536eb7ad83ea1cf666d0a43f233f67fa`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/229`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/230`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/231`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/221`
  - 结果：`state=open`，等待本 closeout PR 合入后关闭
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 221 --json projectItems --jq '.projectItems'`
  - 结果：Project `Syvert 主交付看板` status 为 `Todo`，等待本 closeout PR 合入后切到 `Done`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 232 --json projectItems --jq '.projectItems'`
  - 结果：Project `Syvert 主交付看板` status 为 `Todo`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过，`docs-guard 通过。`
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过，`workflow-guard 通过。`
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过，`governance-gate 通过。`
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，`PR class: docs`，`变更类别: docs`，`PR scope 校验通过。`
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/open_pr.py --class docs --issue 232 --item-key CHORE-0156-fr-0018-parent-closeout --item-type CHORE --release v0.6.0 --sprint 2026-S19 --title 'docs(closeout): 收口 FR-0018 父事项' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：通过，创建 PR `#251`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/commits/2f6878d094000ba5b19725af82f33de5ac610956/check-runs`
  - 结果：PR `#251` head `2f6878d094000ba5b19725af82f33de5ac610956` 的 required checks 全部通过

## 待完成

- 通过 PR `#251` guardian / merge gate 并合入。
- 合入后将 `#232` 正文更新为已完成并关闭，Project 切到 `Done`。
- 回写并关闭父 FR `#221`，说明 formal spec、HTTP runtime 与 same-path evidence 已合入主干。
- fast-forward main，退役 `issue-232-chore-fr-0018` 分支与 worktree。

## 未决风险

- 若 `#221` 关闭前未引用 `#229/#230/#231/#232` 与 PR `#241/#245/#246`，后续 `FR-0019/#234` gate matrix 回溯 `http_submit_status_result` / `cli_api_same_path` 证据时需要手工拼接。
- 若误在本事项修改 runtime、tests 或 formal spec，可能破坏 `#230/#231` 已通过 guardian 的实现与证据边界。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本事项对 `docs/exec-plans/*FR-0018*` closeout 元数据的修改。
- GitHub 侧回滚：若已关闭 `#221/#232` 后发现 closeout 事实错误，重新打开对应 issue，追加纠正评论，并通过新的 closeout Work Item 修复仓内事实。

## 最近一次 checkpoint 对应的 head SHA

- 当前主干基线：`394d48a7be861de742aae439c38e18625cc44193`。
- 当前可恢复 checkpoint：`2f6878d094000ba5b19725af82f33de5ac610956`，包含本 exec-plan 首个版本化恢复工件与 `FR-0018` inactive requirement container closeout 索引。
- 后续 review-sync 若只更新验证记录或 GitHub 状态，不推进新的 formal spec / runtime 语义。
