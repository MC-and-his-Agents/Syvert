# FR-0006-adapter-contract-test-harness 执行计划

## 关联信息

- item_key：`FR-0006-adapter-contract-test-harness`
- Issue：`#66`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- 关联 PR：
- active 收口事项：`FR-0006-adapter-contract-test-harness`

## 目标

- 为 `#66` 完成独立 formal spec PR 所需的最小执行上下文、审查与 closeout 收口，使 `FR-0006` 作为 `v0.2.0` 的 formal spec 真相入主干。

## 范围

- 本次纳入：
  - `FR-0006` formal spec 套件
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 当前事项的 active `exec-plan`
- 本次不纳入：
  - fake adapter、验证工具或 harness 的实现代码
  - 真实平台测试、双参考适配器回归与版本 gate 编排
  - `FR-0004`、`FR-0005`、`FR-0007` 的 formal spec 实质内容

## 当前停点

- 已在独立 worktree `issue-66-fr-0006-v0-2-0` 中创建 `FR-0006` formal spec 套件初稿，并同步最小 release / sprint 索引。
- `docs_guard`、`spec_guard --all` 已通过。
- `open_pr --dry-run` 首次校验暴露出当前仓库要求 active `exec-plan` 的受控入口约束，故补建本执行计划以继续受控 PR 流程。

## 下一步动作

- 复核 `FR-0006` formal spec 文案边界，确保不混入回归 gate 或相邻 FR 语义。
- 通过受控入口创建 spec PR，等待 checks 通过后执行 guardian。
- guardian 通过后受控合并，并完成 issue / PR / main 真相一致性收口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结 adapter contract test harness 的职责边界，使 Core “可验证”目标具备不依赖真实平台的 formal spec 输入。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.2.0` contract harness formal spec 收口项。
- 阻塞：
  - 无外部阻塞；当前主要剩余受控 PR、checks、guardian 与 merge gate。

## 已验证项

- `gh issue view 66 --json number,title,body,state,url`
  - 结果：确认 `#66` 为 `FR-0006`，目标是建立 adapter contract test harness formal spec
- `python3 scripts/create_worktree.py --issue 66 --class spec`
  - 结果：已创建工作区 `/Users/mc/code/worktrees/syvert/issue-66-fr-0006-v0-2-0`
- `python3 scripts/docs_guard.py`
  - 结果：通过
- `python3 scripts/spec_guard.py --all`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 66 --item-key FR-0006-adapter-contract-test-harness --item-type FR --release v0.2.0 --sprint 2026-S15 --dry-run`
  - 结果：首次失败，原因是缺少 active `exec-plan`；已据此补齐当前执行上下文工件

## 未决风险

- 若 fake adapter、验证工具与真实平台回归边界写得不够清楚，后续实现 PR 容易越界。
- 若当前 formal spec PR 未把受控入口、guardian 与 issue closeout 一并收口，主干真相与 GitHub 状态会再次失配。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `docs/specs/FR-0006-adapter-contract-test-harness/`、`docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 与本 `exec-plan` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `f9bf12ad92f6f9afab3d3761c7df8c8b48a07ef9`
- 说明：当前 checkpoint 基于创建 worktree 时的 `origin/main` head；待本轮 formal spec 变更形成提交后，再把新的受审 head 交由 guardian 与 merge gate 绑定。
