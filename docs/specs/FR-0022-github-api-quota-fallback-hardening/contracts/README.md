# FR-0022 contracts

## Contract surfaces

- `cached_non_merge` integration live state lookup。
- `uncached_live_gate` integration live state lookup。
- `NonMergeFallbackStatus` for status / preflight output。
- `MergeGateLiveCheck` for guardian merge gate。
- `SpecMirrorIssueIndex` for spec issue sync。
- `RepoRulesetReadResult` for repository settings sync.

## GitHub API cost contract

- REST 和 GraphQL quota 不共享 primary limit，但都受 GitHub secondary rate limit、并发、CPU time 与内容写入限制影响。
- GraphQL 不因为是单 query 就天然更便宜；重复查询同一 project item / issue projectItems 仍然是浪费。
- `search/issues` 是高风险 REST endpoint，不能作为每个 changed spec 的默认 lookup。
- polling 允许保留，但必须受 state 约束，不能无差别触发 guardian。

## Integration live state lookup contract

- `cached_non_merge`：
  - 允许当前进程缓存。
  - cache key 使用 normalized integration ref。
  - 读取失败返回 `verification_status=unverified` 或保留 `error`。
  - 调用方可以继续渲染状态面或完成预检错误报告。
- `uncached_live_gate`：
  - 不使用 stale cache 放行。
  - 读取失败、解析失败、字段缺失、状态不允许或 joint acceptance 未就绪时必须 hard fail。
  - 只能用于 merge gate / final recheck。

## Fallback contract

- 允许 fallback 的路径：
  - `open_pr` canonicalization / preflight error reporting。
  - `governance_status` status rendering。
  - review / diagnostics output。
- 禁止 fallback 的路径：
  - `pr_guardian merge-if-safe` final integration recheck。
  - final PR head/body/checks consistency check。
  - `sync_repo_settings` 远端 rulesets 读取失败后的写入决策。

## PR metadata and checks contract

- 中间步骤可以复用当前回合已经读取的 PR metadata / checks。
- 合并前必须重新读取 GitHub 当前 PR metadata，并验证：
  - `headRefOid` 未变化。
  - PR body 未变化，或变化已通过当前回合明确处理。
  - checks 当前通过。
- 任何最终读取失败必须阻断合并。

## Spec mirror issue sync contract

- 同一 sync 进程必须优先建立本地 issue index 或复用 lookup cache。
- `search/issues` 只能作为 index 缺失、异常修复或向后兼容 fallback。
- 创建/更新 mirror issue 仍使用 REST。

## Repo settings sync contract

- `current_rulesets()` 或等价读取函数失败时必须返回 hard failure。
- 读取失败不得投影为 empty list。
- 写入 ruleset 前必须有可信当前 rulesets snapshot。
