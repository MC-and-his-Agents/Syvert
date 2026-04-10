# GOV-0027 执行计划

## 关联信息

- item_key：`GOV-0027-governance-contract-rewrite`
- Issue：`#56`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`
- 关联 decision：`docs/decisions/ADR-0003-github-delivery-structure-and-repo-semantic-split.md`
- 关联 PR：待创建
- active 收口事项：`GOV-0027-governance-contract-rewrite`

## 目标

- 将仓库治理口径收敛为“GitHub 单一调度层 + 仓内单一语义层”。
- 明确 `Phase / FR / Work Item` 职责边界，并把 `Work Item` 固定为唯一执行入口。
- 补齐 `FR-0003` formal spec、`v0.2.0` / `2026-S15` 索引与 decision 工件，使当前 Work Item 可通过受控入口开 PR。

## 范围

- 本次纳入：
  - `AGENTS.md`
  - `WORKFLOW.md`
  - `docs/AGENTS.md`
  - `docs/process/delivery-funnel.md`
  - `docs/process/agent-loop.md`
  - `docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/**`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - `docs/decisions/ADR-0003-github-delivery-structure-and-repo-semantic-split.md`
  - 本 exec-plan
- 本次不纳入：
  - `scripts/**` 行为改造
  - `tests/**` 大改
  - 删除 `TODO.md`
  - 任何业务实现代码

## 当前停点

- 独立 worktree 已创建，`FR-0003` formal spec、`GOV-0027` exec-plan、顶层治理文档与 `v0.2.0` / `2026-S15` 索引已落盘；本地治理门禁与测试已通过，当前停在提交后重跑基于提交图的 preflight 并创建 PR。

## 下一步动作

- 提交当前治理改动并生成中文 Conventional Commit。
- 运行 `pr_scope_guard`、`commit_check` 与 `open_pr --dry-run` 的提交图版本校验。
- 开 PR、补齐 `refs #55` / `refs #54`，随后推进 review、guardian、checks 与 merge gate。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 建立 GitHub 调度层与仓内语义层的正式治理契约，使后续 governance / implementation 回合都围绕 `Phase -> FR -> Work Item` 统一收口。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#55 / FR-0003` 下的首个治理收口 Work Item，负责冻结层级语义、formal spec 绑定关系与唯一执行入口规则。
- 阻塞：无外部阻塞；必须严格避免越界到 `#57` 的 harness 兼容迁移与 `#58` 的 `TODO.md` 清理。

## 已验证项

- `python3 scripts/create_worktree.py --issue 56 --class governance`
- 已阅读：`AGENTS.md`
- 已阅读：`vision.md`
- 已阅读：`docs/roadmap-v0-to-v1.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`docs/process/agent-loop.md`
- 已核对 GitHub 真相：`#54=Phase`、`#55=FR`、`#56=Work Item`
- 已核对 GitHub 真相：`release=v0.2.0`、`sprint=2026-S15`
- `python3 scripts/open_pr.py --class governance --issue 56 --item-key GOV-0027-governance-contract-rewrite --item-type GOV --release v0.2.0 --sprint 2026-S15 --closing fixes --dry-run`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `python3 -m unittest discover -s tests/governance -p 'test_*.py'`
- 已确认 `pr_scope_guard` / `commit_check` 在未提交新增文件时不会看到当前 diff，需要在生成提交后按提交图重跑

## 未决风险

- 若文档仍保留并行分层定义，会继续造成 formal spec、exec-plan、release/sprint 索引的归属歧义。
- 若 `2026-S15` 的语义改写不够克制，可能误伤现有 `v0.1.0` 业务索引表达。
- 若 PR 描述缺少 `refs #55` / `refs #54`，上位事项引用链会不完整。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项在治理文档、formal spec、decision、release/sprint 索引与本 exec-plan 上的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `23579948019abc069e2dc9976311f80f9b01369f`
