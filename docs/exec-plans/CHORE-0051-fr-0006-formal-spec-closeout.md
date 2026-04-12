# CHORE-0051-fr-0006-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0051-fr-0006-formal-spec-closeout`
- Issue：`#74`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- 关联 PR：`#76`
- active 收口事项：`CHORE-0051-fr-0006-formal-spec-closeout`

## 目标

- 作为 `FR-0006` 的首个 Work Item，完成 formal spec PR 的受控入口、checks、guardian、merge 与 closeout，使 `FR-0006` formal spec 成为主干真相。

## 范围

- 本次纳入：
  - `FR-0006` formal spec 套件
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 当前 Work Item 的 active `exec-plan`
- 本次不纳入：
  - fake adapter、验证工具或 harness 的实现代码
  - 真实平台测试、双参考适配器回归与版本 gate 编排
  - `FR-0004`、`FR-0005`、`FR-0007` 的 formal spec 实质内容

## 当前停点

- 已在独立 worktree `issue-74-chore-0051-fr-0006-formal-spec-closeout` 中承接 `FR-0006` formal spec 文档增量，并把执行入口从 FR `#66` 纠正为当前 Work Item `#74`。
- `docs_guard`、`spec_guard --all` 与 `governance_gate --mode local --base-ref origin/main --head-ref HEAD` 已在前一轮文档增量上通过。
- guardian 首轮审查已指出 FR 不能直接作为执行入口；当前增量只修该阻断所要求的工件绑定与索引一致性。
- superseded PR `#71` 已关闭，当前合法受审入口为 Work Item `#74` 对应的 PR `#76`。

## 下一步动作

- 复跑 formal spec 门禁与受控 `open_pr`，确认当前 Work Item 绑定链路合法。
- 让 PR `#76` 的 checks 全绿，并在同一 head 上重跑 guardian。
- 等待 checks 全绿后重跑 guardian，并在通过后执行受控合并与 closeout。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 冻结 adapter contract test harness 的职责边界，并让 formal spec 审查链路符合“FR 绑定 spec、Work Item 绑定执行”的治理模型。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0006` formal spec closeout Work Item。
- 阻塞：
  - 需要先回收以 FR `#66` 直接开出的 superseded PR，再由当前 Work Item 重建合法 PR 链路。

## 已验证项

- `gh issue view 66 --json number,title,body,state,url`
  - 结果：确认 `#66` 是 `FR-0006` 的 requirement 容器
- `gh issue create --title "[CHORE-0051] FR-0006 formal spec closeout" ...`
  - 结果：已创建 Work Item `#74`
- `python3 scripts/create_worktree.py --issue 74 --class spec`
  - 结果：已创建工作区 `/Users/mc/code/worktrees/syvert/issue-74-chore-0051-fr-0006-formal-spec-closeout`
- `git cherry-pick 5c762f0 3a44515`
  - 结果：已把 `FR-0006` formal spec 文档增量迁移到当前 Work Item 分支
- `python3 scripts/pr_guardian.py review 71`
  - 结果：guardian 阻断，要求把执行入口从 FR `#66` 迁回真正的 Work Item，并补齐索引一致性
- `gh pr close 71 --comment "...Superseded by #76..."`
  - 结果：已关闭 superseded PR `#71`
- `python3 scripts/open_pr.py --class spec --issue 74 --item-key CHORE-0051-fr-0006-formal-spec-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --closing refs --title "spec: 收口 FR-0006 的适配器契约测试基座"`
  - 结果：成功创建 PR `#76`

## 未决风险

- 若当前修复没有完全消除 `FR` 与 `Work Item` 的绑定冲突，新的 spec PR 仍会被 guardian 阻断。
- 若 superseded PR `#71` 未及时回收，GitHub 审查面会同时存在两条竞争工件链。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销当前 Work Item 对 `docs/specs/FR-0006-adapter-contract-test-harness/`、`docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 与本 `exec-plan` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `04d675f7db500653a321e34f2633d227c72eb7ae`
- 说明：该 checkpoint 对应修正 Work Item 绑定后的当前合法受审 head；后续 guardian 与 merge gate 必须绑定该 head 或其后续显式 checkpoint。
