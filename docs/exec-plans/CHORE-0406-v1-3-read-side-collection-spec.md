# CHORE-0406 v1.3 read-side collection spec 执行计划

## 关联信息

- item_key：`CHORE-0406-v1-3-read-side-collection-spec`
- Issue：`#406`
- item_type：`CHORE`
- release：`v1.3.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#403`
- 关联 spec：`docs/specs/FR-0403-read-side-collection-result-cursor-contract/spec.md`
- 关联 decision：无
- 关联 PR：待创建
- 状态：`active`

## 目标

- 完成 `#403` 的 Batch 0 与 Batch 1。
- 交付脱敏 fixture/error inventory、formal spec suite、release planning index 与 sprint index。
- 只冻结 read-side collection result and cursor contract，不交付 runtime carrier、consumer migration、fake/reference tests implementation、release closeout 或 raw fixture payload files。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0406-v1-3-read-side-collection-fixture-inventory.md`
  - `docs/exec-plans/CHORE-0406-v1-3-read-side-collection-spec.md`
  - `docs/specs/FR-0403-read-side-collection-result-cursor-contract/spec.md`
  - `docs/specs/FR-0403-read-side-collection-result-cursor-contract/plan.md`
  - `docs/specs/FR-0403-read-side-collection-result-cursor-contract/data-model.md`
  - `docs/specs/FR-0403-read-side-collection-result-cursor-contract/contracts/README.md`
  - `docs/specs/FR-0403-read-side-collection-result-cursor-contract/risks.md`
  - `docs/releases/v1.3.0.md`
  - `docs/sprints/2026-S25.md`
- 本次不纳入：
  - `syvert/**` runtime implementation
  - `tests/**` implementation or fixture payloads
  - `#404` / `#405` Work Item creation
  - release closeout, annotated tag, GitHub Release, published truth carrier
  - raw fixture payload files and any external source name/path mapping

## 当前停点

- Phase `#381`：open，作为 Phase container。
- FR `#403`：open，已显式绑定 `v1.3.0 / 2026-S25`，但只覆盖首个 collection-contract batch。
- Work Item `#406`：open，唯一进入 execution workspace 的事项。
- Workspace：`/Users/mc/code/worktrees/syvert/issue-406-403-v1-3-0-read-side-collection-spec`
- Branch：`issue-406-403-v1-3-0-read-side-collection-spec`
- 主仓 baseline：`016a1759f16cc5f75f63a7bd37b920dae82b82b0`
- 当前变更：Batch 0 artifact、`FR-0403` formal spec suite、`v1.3.0` release planning index、`2026-S25` sprint index 已写入 worktree，待受控 PR preflight 与提交。

## 下一步动作

- 完成 Batch 0 artifact，冻结 fixture matrix 与错误边界映射。
- 完成 `FR-0403` formal spec suite。
- 创建 `v1.3.0` release planning index 与 `2026-S25` sprint index。
- 运行 spec/docs/workflow/version/governance 门禁。
- 创建 spec PR，进入 `spec review`。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.3.0` 明确首个 read-side collection contract batch 的 planning truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#403` 首批 formal spec carrier。
- 阻塞：如 `spec review` 未通过，不得进入 runtime carrier 或后续 Work Item。

## 已验证项

- `#381/#403/#406` GitHub truth 已对齐到本批次执行入口。
- `#403` 当前已显式绑定 `release=v1.3.0`、`sprint=2026-S25`。
- 独立 worktree 与 issue-scoped branch 已创建。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `git diff --check --cached`
  - 结果：通过。
- 脱敏扫描
  - 结果：新增文档未包含外部项目名或本地路径。

## 未决风险

- 若 collection contract 过早吸收 comment/media/profile 特有语义，后续 `#404/#405` 会失去边界。
- 若错误分类未与 `v1.2.0` resource governance health contract 对齐，`credential_invalid` 与 `platform_failed` 会混淆。
- 若 planning release index 被误写成 published truth，`version_guard` 会将其视为发布事实。
- `governance_gate` 与 `open_pr --dry-run` 在未生成提交前仍按 `HEAD` diff 判断，不能代表最终 PR preflight 结果；需在提交后重新验证。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 新增的 spec/docs/artifact 增量。
- 保留 `#381/#403/#406` truth，并在 FR 下重新拆分下一步 Work Item。

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint：`016a1759f16cc5f75f63a7bd37b920dae82b82b0`
- Current live PR head is governed by PR `headRefOid` and guardian merge gate after PR creation.
