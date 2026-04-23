# FR-0019 执行计划（requirement container）

## 关联信息

- item_key：`FR-0019-v0-6-operability-release-gate`
- Issue：`#222`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0019-v0-6-operability-release-gate/`
- 关联 PR：`待创建`
- 状态：`inactive requirement container`

## 目标

- 冻结 `v0.6.0` operability release gate 与回归矩阵 formal contract，覆盖 timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path，并明确其只叠加 `FR-0007` 基础 gate，不重写旧 gate。

## 范围

- 本次纳入：
  - `docs/specs/FR-0019-v0-6-operability-release-gate/`
  - `docs/exec-plans/FR-0019-v0-6-operability-release-gate.md`
  - `docs/exec-plans/CHORE-0157-fr-0019-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - release closeout、tag、GitHub Release
  - 外部 SaaS 监控、生产验收、分布式压测

## 当前停点

- `issue-233-fr-0019-formal-spec` 已作为 `#233` 的独立 spec worktree 建立。
- 当前回合只允许修改 `FR-0019` formal spec 套件与两个 exec-plan，禁止越界到 runtime / tests / scripts / release / sprint 索引。
- 当前目标是形成可进入 spec review 的 formal spec checkpoint。

## 下一步动作

- 运行 formal spec、docs、workflow 三项 guard。
- 若 guard 通过，进入 spec review / PR 创建链路。
- spec review 通过后，由 `#234` 进入 release gate matrix implementation。
- `#235` 负责 parent closeout，把目标、文档、审查、门禁、主干真相与 GitHub 状态收成一致。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 把“可运维发布门禁与回归矩阵”收敛为 implementation-ready 的 formal contract，并确保后续实现能在同一 Core / task-record / store / envelope 语义下验证 HTTP 与 CLI 入口一致性。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0019` canonical requirement container；当前 active 执行回合由 `CHORE-0157-fr-0019-formal-spec-closeout` 承担。
- 阻塞：
  - 若本 spec 未通过，`#234` 不得开始 release gate matrix implementation。
  - 若 same-path、metrics/logs、retry/concurrency 边界未冻结，`#235` 不得把 `v0.6.0` operability gate 作为可收口证据。

## 已验证项

- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`docs/specs/README.md` 与 formal spec 模板。
- 已核对 `FR-0007` / `FR-0008` / `FR-0009` / `FR-0015` 的 formal spec 风格与相关语义边界。
- 已核对 `CHORE-0138-fr-0013-formal-spec-closeout.md` 的 active closeout exec-plan 结构。

## 未决风险

- 若后续实现把 `FR-0019` 当作 `FR-0007` 替代品，会破坏版本 gate 继承关系。
- 若 HTTP 与 CLI same-path 只比较展示输出，不比较 shared task truth，会遗漏影子状态风险。
- 若 metrics / logs 证据依赖外部 SaaS 或生产环境，当前 repo 无法复验发布门禁。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0019` formal spec 套件与两个 exec-plan 的文档增量，不回退相邻 Work Item 或 runtime 变更。

## 最近一次 checkpoint 对应的 head SHA

- `待生成`
