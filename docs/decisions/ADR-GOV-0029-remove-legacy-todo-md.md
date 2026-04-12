# ADR-GOV-0029 Remove legacy TODO.md from formal governance flow

## 关联信息

- Issue：`#58`
- item_key：`GOV-0029-remove-legacy-todo-md`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`

## 背景

`FR-0003` 已把 GitHub 单一调度层与仓内单一语义层收敛为正式治理基线，但仓内仍保留 legacy `TODO.md` 作为 formal spec 套件、模板与恢复入口的历史残留。

若继续沿用旧口径，会同时留下三类问题：

- formal spec 最小套件与治理 guard 对 `TODO.md` 的要求不一致
- 存量 formal spec 套件仍可能把 `TODO.md` 误当作可继续维护的状态镜像
- `ADR-0003` 作为 FR 级 shared decision 不适合直接充当当前 Work Item 的 machine-checkable `关联 decision`

## 决策

- `GOV-0029` 使用独立 Work Item decision 记录本轮 `TODO.md` 退出 formal governance flow 的收口语义。
- `GOV-0029` 分两步执行：先以独立 formal spec / governance contract PR 更新 `FR-0003` formal spec、当前事项工件，以及 `WORKFLOW.md`、`docs/AGENTS.md`、`spec_review.md`、`docs/specs/README.md` 与 `docs/process/agent-loop.md` 的权威口径；再以独立 `governance` 类 PR 落地 `docs/specs/_template/**`、guard、policy、`open_pr`、回归测试与存量 legacy `TODO.md` 清理。
- 对当前事项，formal spec 最小套件收敛为 `spec.md` + `plan.md`；workflow / review / template / guard / policy / `open_pr` / 测试工件不得再把 legacy `TODO.md` 视为必需工件、状态镜像或恢复入口。
- 当前 spec PR 可对 `FR-0003/TODO.md` 做一次受控的过渡性状态回写，用于统一 formal spec 套件内部的 active review truth；实体删除仍留在后续独立 governance PR。
- 当前事项仅允许在后续独立 governance PR 中把 `FR-0001` 与 `FR-0002` 作为额外 formal spec 套件纳入清理；每个套件都必须在当前 diff 中删除对应的 legacy `TODO.md`，并且只能触碰完成该清理所需的最小文件集合。
- 本 decision 在 `TODO.md` 退出 formal governance flow 这一窄范围内，替代 `ADR-0003` 历史文本里关于“不删除 `TODO.md` / 不调整 formal spec required files”的旧非目标表述。

## 影响

- `ADR-0003` 继续保留为 `FR-0003` 的 shared decision，不再承担当前 Work Item 的 machine-checkable 绑定。
- 当前 formal spec PR 合入后，`FR-0003` 将成为后续独立 governance 实现 PR 的批准输入。
- `GOV-0029` 的 exec-plan、guard、policy、测试与文档索引统一追溯到本 decision。
- 历史 `TODO.md` 文件可在未触碰时保留为 inert legacy，但后续 PR 不得继续维护、回写或把它当恢复入口。
