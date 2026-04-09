# FR-0002-content-detail-runtime-v0-1 执行计划

## 关联信息

- item_key：`FR-0002-content-detail-runtime-v0-1`
- Issue：`#38`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：`#53`
- active 收口事项：`FR-0002-content-detail-runtime-v0-1`

## 目标

- 在不引入新主题、新实现或仓内状态镜像的前提下，为父事项 `#38` 形成可关闭的收口状态。
- 把 `FR-0002` 的 formal contract、runtime/CLI、双参考适配器与 `#42` closeout 证据映射回父事项、release 与 sprint 索引。

## 范围

- 本次纳入：
  - `docs/specs/FR-0002-content-detail-runtime-v0-1/TODO.md`
  - `docs/exec-plans/FR-0002-content-detail-runtime-v0-1.md`
  - `docs/releases/v0.1.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - 新的 formal contract 语义
  - Core / Adapter 实现改动
  - release / sprint 的 GitHub 状态镜像
  - HTTP API、队列、资源系统等超范围功能

## 当前停点

- `origin/main@dca85ef22fa420ac420b893254449c658fd01b05` 已包含 `FR-0002` 当前主线所需的关键前提：PR `#43`、`#44`、`#48`、`#51`、`#52`。
- PR `#53` 已打开，当前受审 head 已把父事项 closeout 文档、release 完成依据与 sprint closeout 结果落入本轮 docs-only diff。
- 首轮 guardian 已指出三处工件一致性问题：`TODO.md` 的成熟度过早推进到 `merge-ready`、active `exec-plan` 未绑定当前 PR、`#44` 的 runtime / CLI 证据链尚未回指 `CHORE-0041`。
- 当前执行现场为独立 docs closeout worktree：`/Users/claw/code/worktrees/syvert/issue-38-fr-0002-content-detail-runtime-v0-1-fr-0002-v0-1-0-content-detail-runtime`。

## 下一步动作

- 收口 guardian 首轮 findings，并保持父事项 / release / sprint 工件一致。
- 在 PR `#53` 的最新 head 上重跑验证、guardian 与 merge gate。
- 合并后关闭 `#38`，并退役当前 branch / worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 完成业务主线 `FR-0002` 的父事项收口，使“双参考适配器共享 Core 契约”从已合入子事项证据提升为可正式关闭的版本完成依据。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：父事项收口项。
- 阻塞：
  - 无实现侧阻塞；当前只需完成 docs closeout、guardian、merge gate 与 GitHub Issue 收口。

## 已验证项

- `gh issue view 38`
- `gh issue view 39`
- `gh issue view 40`
- `gh issue view 41`
- `gh issue view 42`
- `gh issue view 47`
- `gh issue view 50`
- `gh issue view 14`
- `gh issue view 19`
- `gh pr view 43`
  - 结果：`state=MERGED`，`mergeCommit=130d51f7f1a5a6e9e7d91bd910827851a27305ea`
- `gh pr view 44`
  - 结果：`state=MERGED`，`mergeCommit=f667913173bb22057ef9a865717256f1374d8c62`
- `gh pr view 48`
  - 结果：`state=MERGED`，`mergeCommit=6d7e2be24b9e37860939c5ad598e1e76e093e3af`
- `gh pr view 51`
  - 结果：`state=MERGED`，`mergeCommit=92a333309090a77ec7619ff70a66622977c03b96`
- `gh pr view 52`
  - 结果：`state=MERGED`，`mergeCommit=dca85ef22fa420ac420b893254449c658fd01b05`
- `gh pr view 53`
  - 结果：`state=OPEN`，`headRefOid=3aea852b2890ddff73a32545f3916254b77655b2`，当前为父事项 closeout PR
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter -v`
  - 结果：`Ran 88 tests in 2.794s`，`OK`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
  - 结果：`Ran 128 tests in 2.140s`，`OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `#38` 关闭条件 -> 证据映射：
  - formal contract 已由 PR `#43` 入主干，对应 `docs/specs/FR-0002-content-detail-runtime-v0-1/`
  - runtime / CLI 宿主已由 PR `#44` 入主干，对应 `docs/exec-plans/CHORE-0041-runtime-cli-skeleton.md`、`tests.runtime.test_runtime`、`tests.runtime.test_cli`
  - 小红书参考适配器已由 PR `#48` 入主干，对应 `docs/exec-plans/CHORE-0047-xhs-reference-adapter.md`
  - 抖音参考适配器已由 PR `#51` 入主干，对应 `docs/exec-plans/CHORE-0050-douyin-reference-adapter.md`
  - 双参考适配器共享 Core 路径验证已由 PR `#52` / `#42` closeout 入主干，对应 `docs/exec-plans/CHORE-0042-dual-reference-adapters-validation-closeout.md`

## 未决风险

- 若父事项 `#38` 不把子事项证据重新映射回自身关闭条件，GitHub 真相与仓内主干事实会继续失配。
- 若 release / sprint 文档在本轮收口时回退成状态镜像，会破坏“GitHub 为真相源、仓内只保留索引与证据”的治理边界。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `docs/specs/FR-0002-content-detail-runtime-v0-1/TODO.md`、`docs/exec-plans/FR-0002-content-detail-runtime-v0-1.md`、`docs/releases/v0.1.0.md` 与 `docs/sprints/2026-S15.md` 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `3aea852b2890ddff73a32545f3916254b77655b2`
- 说明：后续如仅补充 guardian findings 收口与审查态元数据，可保留该 checkpoint，并由 guardian state 绑定当前受审 head。
