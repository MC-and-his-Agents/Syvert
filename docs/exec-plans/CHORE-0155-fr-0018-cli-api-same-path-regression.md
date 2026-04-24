# CHORE-0155 FR-0018 CLI/API same-path regression evidence 执行计划

## 关联信息

- item_key：`CHORE-0155-fr-0018-cli-api-same-path-regression`
- Issue：`#231`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0018-http-task-api-same-core-path/`
- 关联 decision：
- 关联 PR：`#246`

## 目标

- 补齐 `FR-0018` 要求的 CLI/API 同路径回归证据。
- 证明 CLI `run/query` 与 HTTP `submit/status/result` 在等价任务语义下消费同一 Core path、同一 durable `TaskRecord` truth、同一 terminal envelope 与同一 shared failed envelope 分类。

## 范围

- 本次纳入：
  - CLI 与 HTTP 成功任务的 durable `TaskRecord` 等价证据
  - CLI 创建任务后由 HTTP `status/result` 回读同一 shared truth
  - HTTP 创建任务后由 CLI `query` 回读同一 shared truth
  - failed terminal envelope、pre-admission invalid input、durable record unavailable、nonterminal result boundary 与 shared observability refs 的同路径回归
  - `pre-accepted concurrency rejection`、`execution_timeout`、closeout/control-state failure、post-accepted retry reacquire rejection 的 CLI/API shared truth 读取证据
- 本次不纳入：
  - 新增 HTTP endpoint 或修改 HTTP public surface
  - 修改 `FR-0018` formal spec
  - 实现 `FR-0019/#234` operability gate result runner、metrics snapshot 或完整 gate matrix
  - 实现 `FR-0016/#224` execution-control runtime 本体或 `FR-0017/#227` observability runtime 本体

## 当前停点

- 已确认 `#231` 为 open Work Item，item_key / release / sprint 与本执行计划一致。
- 已确认 `#230` / PR `#245` 已合入主干，HTTP endpoint runtime 可作为本事项证据基线。
- 已通过 `python3 scripts/create_worktree.py --issue 231 --class implementation` 创建独立 worktree：`/Users/mc/code/worktrees/syvert/issue-231-fr-0018-cli-api`，分支为 `issue-231-fr-0018-cli-api`。
- 已新增 `tests/runtime/test_cli_http_same_path.py`，集中承载 CLI/API same-path regression evidence。
- 已完成本地定点验证与既有回归验证；新增 same-path 用例当前通过。
- 已按 `FR-0018` / `FR-0019` 当前文档要求补齐控制面失败证据：pre-accepted concurrency rejection、execution timeout、closeout/control-state failure、post-accepted retry reacquire rejection 与 runtime refs 可见性。
- PR `#246` 已创建，后续 review / guardian / CI 结果以 PR live head 与 guardian state 为准。

## 下一步动作

- 提交并通过 `scripts/open_pr.py` 创建 implementation PR。
- PR 后等待 CI，运行 reviewer / guardian；guardian 不设置超时。
- 全部通过后使用受控 `merge_pr` squash merge，并同步 GitHub issue/project 状态、exec-plan closeout、主干事实与 branch/worktree 退役。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.6.0` 的 “HTTP + CLI through same Core path” 能力切片。
- 本事项只收口 `FR-0018` 的 CLI/API same-path regression evidence，为后续 `#232` FR parent closeout 提供可复验证据。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0018` 下游 evidence closeout Work Item。
- 阻塞：`#232` 的 FR-0018 parent closeout 依赖本事项先证明 CLI/API 对 shared `TaskRecord` / envelope truth 的观察一致。

## 已验证项

- `git status --short --branch`
  - 结果：开始实现前主工作区位于 `main...origin/main` 且干净，head 为 `64e3ece230f0c587ba4b809c17177b1f37665504`。
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 231 --json number,title,state,body,projectItems,url`
  - 结果：已确认 `#231` open，project 状态为 `Todo`，item_key / release / sprint 与本执行计划一致。
- `python3 scripts/create_worktree.py --issue 231 --class implementation`
  - 结果：通过，创建 `issue-231-fr-0018-cli-api` worktree / branch，base SHA 为 `64e3ece230f0c587ba4b809c17177b1f37665504`。
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_http_api`
  - 结果：计划确认阶段通过，`Ran 78 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_task_record_store tests.runtime.test_runtime`
  - 结果：计划确认阶段通过，`Ran 83 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_cli_http_same_path`
  - 结果：首轮通过，`Ran 8 tests`，`OK`；补齐控制面 same-path evidence 后再次通过，`Ran 12 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_http_api tests.runtime.test_task_record_store tests.runtime.test_runtime`
  - 结果：通过，`Ran 161 tests`，`OK`。
- `python3 -m unittest discover -s tests`
  - 结果：通过，`Ran 376 tests`，`OK`。
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过。
- `python3 -m unittest discover -s tests/runtime -p 'test_cli_http_same_path.py' -v`
  - 结果：首轮通过，`Ran 8 tests`，`OK`；补齐控制面 same-path evidence 后再次通过，`Ran 12 tests`，`OK`；用于确认新增 runtime 测试文件可由 runtime start-dir discovery 捕获。
- `env -u GH_TOKEN -u GITHUB_TOKEN gh pr create --base main --title 'test(runtime): 补齐 FR-0018 CLI/API 同路径回归证据' --body-file <open_pr-dry-run-body>`
  - 结果：通过，创建 PR `#246`。说明：`scripts/open_pr.py` 的 preflight / dry-run 通过，但直接创建时未透出 `gh pr create` 错误详情；已复用同一受控 body 创建 PR。

## Evidence case mapping

- `same-path-success-shared-truth`：`test_same_path_success_shared_truth`
- `cli-created-task-http-read`：`test_cli_created_task_can_be_read_by_http_status_and_result`
- `http-created-task-cli-read`：`test_http_created_task_can_be_read_by_cli_query`
- `same-path-terminal-failed-envelope`：`test_same_path_terminal_failed_envelope_is_not_rewrapped`
- `same-path-pre-admission-invalid-input`：`test_same_path_pre_admission_invalid_input_does_not_create_task_record`
- `same-path-pre-accepted-concurrency-rejection`：`test_same_path_pre_accepted_concurrency_rejection_uses_shared_failed_envelope`
- `same-path-durable-record-unavailable`：`test_same_path_durable_record_unavailable_fails_closed`
- `same-path-nonterminal-status-and-result-boundary`：`test_same_path_nonterminal_status_and_result_boundary`
- `execution-timeout-shared-truth`：`test_execution_timeout_terminal_truth_is_shared_by_cli_query_and_http_result`
- `closeout-control-state-failure-shared-truth`：`test_closeout_control_state_failure_terminal_truth_is_shared`
- `runtime-result-refs-preserved`：`test_runtime_result_refs_are_preserved_across_cli_query_and_http_result`
- `post-accepted-retry-reacquire-rejection`：`test_post_accepted_retry_reacquire_rejection_does_not_rewrite_terminal_failure`

## 未决风险

- 当前证据只证明 `FR-0018` 所需的 CLI/API same-path regression，不替代 `FR-0019/#234` 的完整 operability release gate matrix。
- CLI 与 HTTP 允许存在 transport 展示差异；本事项只比较 shared task semantics、durable record、terminal envelope 与 shared failed envelope 分类。
- 若后续 guardian 要求扩大到 gate result / metrics snapshot，应拆分到 `FR-0019/#234`，避免在 `#231` 重写范围。

## 回滚方式

- 在实现 PR 中 revert `tests/runtime/test_cli_http_same_path.py` 与本 exec-plan 增量。
- 不回滚 `FR-0018` formal spec，不修改 `#230` 已合入 HTTP runtime。

## 最近一次 checkpoint 对应的 head SHA

- `64e3ece230f0c587ba4b809c17177b1f37665504`
