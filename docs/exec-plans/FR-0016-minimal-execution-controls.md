# FR-0016 执行计划（requirement container）

## 关联信息

- item_key：`FR-0016-minimal-execution-controls`
- Issue：`#219`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0016-minimal-execution-controls/`
- 关联 PR：`N/A`
- 状态：`inactive requirement container`

## 说明

- `FR-0016` 作为 canonical requirement 容器，不直接承载 worktree、PR 或 active 执行回合。
- formal spec closeout 已由 `#223` / PR `#237` 合入主干；runtime implementation 已由 `#224` / PR `#247` 合入主干。
- 当前父事项 closeout 由 `#225` / `CHORE-0149-fr-0016-parent-closeout` 承担；本 requirement container 保持 inactive，只记录主干事实索引，不直接承载 worktree、PR 或 active 执行回合。
- `FR-0016` 冻结 Core 最小执行控制 contract：`ExecutionControlPolicy`、attempt timeout、基础 retry 与 fail-fast concurrency gate。
- `FR-0016` 不实现 runtime，不定义 HTTP API，不建立 observability 平台，不重写 `FR-0005` 错误分类闭集，不扩张 `FR-0013` 到 `FR-0015` 的资源能力与 provider 边界。
- 若后续需要队列、优先级、公平性、取消、恢复、复杂 backoff 或分布式 slot，必须通过新的 formal spec 推进。

## closeout 证据

- `#223` / PR `#237`：formal spec closeout，merge commit `295b565adae2a384d3a314755706d66c5ea59b09`
- `#224` / PR `#247`：runtime timeout / retry / concurrency implementation，merge commit `6590801d561a44db21fc07014948d33f427fd3a0`
- `#225` / PR `#248`：父事项 closeout 入口

## 最近一次 checkpoint 对应的 head SHA

- `8d1b56183fc18c21454c461f1102baa26123bedf`
- 说明：本次 `#225` 只补 closeout metadata，不推进 `FR-0016` requirement semantic checkpoint。
