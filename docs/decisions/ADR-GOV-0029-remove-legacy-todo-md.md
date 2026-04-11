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
- 对当前事项，formal spec 最小套件收敛为 `spec.md` + `plan.md`；模板、guard 与 policy 不得再把 legacy `TODO.md` 视为必需工件、状态镜像或恢复入口。
- 当前事项允许在绑定 `FR-0003` formal spec 的前提下，显式列出并清理仍保留 legacy `TODO.md` 规范入口的存量 formal spec 套件。
- 本 decision 在 `TODO.md` 退出 formal governance flow 这一窄范围内，替代 `ADR-0003` 历史文本里关于“不删除 `TODO.md` / 不调整 formal spec required files”的旧非目标表述。

## 影响

- `ADR-0003` 继续保留为 `FR-0003` 的 shared decision，不再承担当前 Work Item 的 machine-checkable 绑定。
- `GOV-0029` 的 exec-plan、guard、policy、测试与文档索引统一追溯到本 decision。
- 历史 `TODO.md` 文件可在未触碰时保留为 inert legacy，但后续 PR 不得继续维护、回写或把它当恢复入口。
