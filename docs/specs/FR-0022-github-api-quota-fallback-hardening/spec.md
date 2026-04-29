# FR-0022 GitHub API quota and fallback hardening

## 关联信息

- item_key：`FR-0022-github-api-quota-fallback-hardening`
- Issue：`#274`
- item_type：`FR`
- release：`v0.7.0`
- sprint：`2026-S20`

## 背景与目标

- 背景：Syvert 的治理脚本已经集中消费 GitHub REST、GraphQL 与 `gh` 高层 CLI。当前风险不在于“是否显示 API 类型”，而在于同一执行回合内重复远端读取、search endpoint 默认使用、polling 放大效应、GraphQL live state 失败时缺少分场景 fallback，以及 repository settings 读取失败时可能被误解释为空状态。
- 目标：冻结一组 quota-aware governance contract，使后续实现能减少 REST / GraphQL 浪费，同时保持 GitHub 作为调度真相源、保持 merge gate 的 live recheck fail-closed 语义，并为非合并展示/预检路径提供显式 `unverified` fallback。

## 范围

- 本次纳入：
  - `scripts/integration_contract.py` 中 integration live state 的当前进程缓存语义。
  - `scripts/open_pr.py`、`scripts/governance_status.py` 的非合并路径 fallback 语义。
  - `scripts/pr_guardian.py` merge gate 与 merge-if-safe 的 live recheck / 快照复用边界。
  - `scripts/spec_issue_sync.py` 对 GitHub search endpoint 的使用收敛。
  - `scripts/sync_repo_settings.py` rulesets 读取失败时的 fail-closed 要求。
  - `scripts/review_poller.py` 的最小 polling 收敛边界。
- 本次不纳入：
  - 不新增持久 integration live state cache、TTL、跨命令恢复或本地 stale truth。
  - 不接入 GitHub webhook 或外部调度服务。
  - 不降低 merge gate 对 live integration recheck 的阻断要求。
  - 不改变 GitHub Issue / PR / Project 作为调度真相源的定位。
  - 不修改业务 runtime、adapter SDK 或参考 adapter 行为。
  - 不把 `gh issue` / `gh pr` 高层 CLI 迁移作为本 FR 的 mandatory requirement；后续可在实现中 opportunistic 收敛为 REST。

## 需求说明

- 功能需求：
  - integration live state lookup 必须提供当前进程内缓存。缓存 key 必须基于 canonical normalized integration ref，而不是原始 URL 字符串。
  - 缓存必须只在当前 Python 进程内有效；命令结束后不得把 live state 写入仓库、`$CODEX_HOME/state/syvert/` 或其他持久位置。
  - 缓存命中返回的 payload 必须是 copy；调用方不得通过修改返回 dict 污染缓存中的 canonical payload。
  - 同一进程内，同一 normalized integration ref 的重复查询不得重复触发 `gh api graphql`，除非调用方显式选择 uncached live recheck。
  - merge gate 路径必须继续使用 live verified state。任何 GraphQL / REST 读取失败、解析失败、缺少必需字段或 live state error 都必须阻断合并。
  - 非合并路径可以消费 cached live state；当远端读取失败时，必须显式输出 `unverified` 或等价字段，并保留 live error，不得把失败解释为通过。
  - `open_pr` 在 canonicalize 等价 integration ref 时可以使用 cached lookup；若 live lookup 不可用，必须保留原始用户输入并继续通过现有 contract validation 报告错误或不一致，不得静默改写。
  - `governance_status` 必须把 live state 不可用表达为状态面信息，而不是把 live check 失败升级为无法渲染整个状态面。
  - `pr_guardian merge-if-safe` 可以复用当前回合中已经读取的 PR metadata / checks 快照，但必须保留合并前最终 `headRefOid`、PR body 与 checks 复核。
  - `pr_guardian` 在 `merge_gate=integration_check_required` 时必须保留 merge 前 live integration recheck；该 recheck 不得使用 stale fallback 放行。
  - `spec_issue_sync` 不得对每个 changed spec 默认调用 `search/issues`；实现必须优先批量读取已有 mirror issue 或复用本回合 lookup 结果，search 只能作为修复 fallback。
  - `sync_repo_settings` 读取 rulesets 失败时必须 fail closed；不得把读取失败返回为空列表后继续 POST / PUT ruleset。
  - `review_poller` 本 FR 只要求最小收敛：复用 state、过滤已知无变化 PR、避免扩大 polling 范围；webhook 不属于本 FR mandatory scope。
- 契约需求：
  - 后续实现必须提供两个语义清晰的 lookup surface：cached/non-merge lookup 与 uncached/live gate lookup。
  - cached/non-merge lookup 的结果必须携带可机判的 verification status：`verified`、`unverified` 或等价字段。
  - uncached/live gate lookup 的错误必须能被 `validate_integration_ref_live_state()` 或 merge gate 消费并转化为阻断项。
  - PR/checks 快照复用不得替代最终 merge 前一致性检查；最终检查仍以 GitHub 当前状态为准。
- 非功能需求：
  - 实现必须降低同一命令进程内的重复 GraphQL / REST 消耗，不追求跨进程缓存。
  - 失败信息必须保留具体 API 读取失败、解析失败、live field 缺失或 fallback status，避免把 quota/rate limit 问题伪装成业务状态。
  - 所有新增逻辑必须可通过本地 governance 单元测试验证，不要求真实 GitHub API 集成测试。

## 约束

- 阶段约束：
  - `#275` 只冻结 formal spec；实现必须在 `#276` 或后续实现 Work Item 中完成。
  - `#277` 只做 parent closeout，不得引入新的 API 行为。
  - Phase `#273` 关闭前必须确认 `#274` 已关闭，且主干中存在本 FR 的 spec、实现证据与 closeout 证据。
- 架构约束：
  - GitHub 仍是 Phase / FR / Work Item / PR 状态真相源；任何 cache 都不能成为调度真相源。
  - merge gate 的安全性优先于 quota 节省；不能为了省 API 调用而用 stale state 放行合并。
  - 当前进程缓存只优化同一命令内重复 lookup；不得把缓存扩张成 governance 状态数据库。
  - formal spec 与实现 PR 必须分离；本 PR 不修改 `scripts/**` 或 `tests/**` 实现。

## GWT 验收场景

### 场景 1

Given 同一 Python 命令进程内两次请求语义相同的 integration ref  
When 第二次请求 live state 且使用 cached/non-merge lookup  
Then 它必须复用第一次结果，不再次调用 `gh api graphql`，并返回与第一次等价的 copy payload

### 场景 2

Given 调用方修改了第一次 cached lookup 返回的 dict  
When 后续调用以同一 normalized ref 获取 cached live state  
Then 返回结果不得包含调用方对第一次返回值的本地污染

### 场景 3

Given `merge_gate=integration_check_required` 且 integration live state 的 GraphQL 查询失败  
When `pr_guardian merge-if-safe` 执行 merge 前 recheck  
Then 它必须 fail closed 并阻断合并，不得使用 cached / stale / unverified 状态放行

### 场景 4

Given `governance_status` 渲染某个需要 integration check 的 PR 或 Issue  
When integration live state 读取失败  
Then 状态面必须显示 `unverified` 或等价状态并保留 live error，同时继续渲染其他 guardian、checks、worktree 与 item context 信息

### 场景 5

Given `open_pr` 需要比较 issue canonical ref 与 CLI raw ref 是否语义等价  
When project item lookup 因 quota 或 GraphQL error 不可用  
Then `open_pr` 不得静默把 raw ref 改写成错误 canonical ref；它必须保留原始输入并通过现有 validation surface 暴露不一致或不可验证状态

### 场景 6

Given `sync_repo_settings` 无法读取 `repos/{repo}/rulesets`  
When 同步逻辑准备 diff 并写入 ruleset  
Then 它必须停止并报告读取失败，不得把 rulesets 当作空集合后创建或覆盖远端 ruleset

### 场景 7

Given 一次 spec mirror sync 涉及多个 changed spec  
When `spec_issue_sync` 查找已有 mirror issue  
Then 它必须优先使用批量读取或本回合缓存结果，不能对每个 spec 都默认调用 `search/issues`

## 异常与边界场景

- 异常场景：
  - GraphQL 返回 malformed JSON 时，merge gate 必须阻断；非合并状态面必须标记 unverified。
  - REST 读取 PR metadata 或 checks 失败时，merge gate 必须阻断；不得用旧快照继续 merge。
  - cached result 中缺少 required live fields 时，不得被视作 verified。
  - rulesets endpoint 因权限、网络或 rate limit 失败时，同步不得写入。
- 边界场景：
  - 不同原始 URL 形式但 normalized identity 相同的 issue ref 可以共享同一缓存条目。
  - project item URL 与 issue ref 只有在 live state 可验证同一 content issue 时才能语义等价。
  - `integration_ref=none`、空 ref 或不可核查 ref 不进入 GraphQL lookup。
  - review_poller 的 polling 仍可存在；本 FR 只要求不扩大 polling 面和不重复触发已知无变化 PR。

## 验收标准

- [ ] formal spec 明确进程内缓存、不新增持久 cache、不接入 webhook。
- [ ] formal spec 明确 cached/non-merge lookup 与 uncached/live gate lookup 的区别。
- [ ] formal spec 明确 merge gate live recheck 失败必须 hard fail。
- [ ] formal spec 明确非合并路径可返回 unverified/fallback，但不得误判通过。
- [ ] formal spec 明确 rulesets 读取失败不得 fallback 为空列表。
- [ ] formal spec 明确 search endpoint 只能作为 fallback，不得每个 spec 默认 search。
- [ ] formal spec 明确 `#275` 为 spec Work Item、`#276` 为 implementation Work Item、`#277` 为 parent closeout Work Item。

## 依赖与外部前提

- 外部依赖：
  - GitHub REST API rate limits 文档。
  - GitHub GraphQL rate limits and query limits 文档。
  - GitHub GraphQL API overview 文档。
  - `#273` Phase、`#274` FR、`#275` spec Work Item、`#276` implementation Work Item、`#277` closeout Work Item。
- 上下游影响：
  - `#276` 必须消费本 FR 的 spec，不得在实现中扩张持久 cache、TTL 或 webhook。
  - `#277` 必须在 `#275` 和 `#276` 的 PR 合入后再执行父事项关闭。
