# FR-0022 data model

## GithubLiveStateCacheKey

- 字段：
  - `normalized_ref`：使用 `normalize_integration_ref_for_comparison()` 得到的 canonical key。
- 约束：
  - 空 ref、`none`、不可核查 ref 不进入缓存。
  - 同一 issue ref 的不同 URL / shorthand 形式必须归一到同一 key。
  - project item URL 只有在 normalized ref 相同的情况下共享缓存；project item 与 issue ref 的语义等价仍需 live state 验证。

## GithubLiveStateSnapshot

- 字段：
  - `integration_ref`
  - `normalized_ref`
  - `source`
  - `verification_status`：`verified` / `unverified`
  - `error`
  - `status`
  - `dependency_order`
  - `joint_acceptance`
  - `owner_repo`
  - `contract_status`
  - `content_repo`
  - `content_issue_number`
  - `project_url`
  - `project_title`
  - `project_number`
  - `organization`
  - `item_id`
- 约束：
  - `verification_status=verified` 只能用于成功读取并解析 live state 的结果。
  - 读取失败、解析失败、缺少 required field 或远端错误必须返回 `verification_status=unverified` 或包含可消费 `error`。
  - merge gate 不得把 `unverified` 当作通过。
  - 返回给调用方的 snapshot 必须是缓存内容的 copy。

## GithubApiReadMode

- 取值：
  - `cached_non_merge`
  - `uncached_live_gate`
- 语义：
  - `cached_non_merge`：用于 `open_pr`、`governance_status` 等非合并路径；允许复用当前进程 cache，失败时可返回 `unverified`。
  - `uncached_live_gate`：用于 `pr_guardian merge-if-safe` 的 merge gate；必须直接读取当前 GitHub live state，失败时 hard fail。

## MergeGateLiveCheck

- 字段：
  - `pr_number`
  - `headRefOid`
  - `body_hash` 或等价 body 绑定
  - `integration_ref`
  - `live_state`
  - `errors`
- 约束：
  - 必须发生在合并前。
  - 必须使用 `uncached_live_gate`。
  - `errors` 非空时不得 merge。
  - final PR metadata / checks 复核仍以 GitHub 当前状态为准。

## NonMergeFallbackStatus

- 字段：
  - `verification_status`
  - `live_errors`
  - `fallback_source`
- 约束：
  - `fallback_source` 可以是 `issue_canonical`、`pr_body`、`cached_process_state` 或 `none`。
  - 非合并 fallback 只用于展示、预检或解释，不得作为 merge gate 放行依据。

## SpecMirrorIssueIndex

- 字段：
  - `repo`
  - `mirror_title_prefix`
  - `issue_number`
  - `state`
- 约束：
  - 同一 sync 进程应先构建可复用 index。
  - `search/issues` 只能在 index 不完整或修复路径中使用。

## RepoRulesetReadResult

- 字段：
  - `ok`
  - `rulesets`
  - `error`
- 约束：
  - `ok=false` 时调用方必须停止。
  - 不得把 `ok=false` 投影为 `rulesets=[]`。
