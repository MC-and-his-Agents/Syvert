# CHORE-0421 v1.5 creator profile / media asset spec 执行计划

## 关联信息

- item_key：`CHORE-0421-v1-5-creator-profile-media-asset-spec`
- Issue：`#421`
- item_type：`CHORE`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`
- 关联 spec：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec.md`
- 关联 decision：
- 关联 PR：`#428`（`https://github.com/MC-and-his-Agents/Syvert/pull/428`）
- 状态：`active`

## 目标

- 完成 `#405` 的 Batch 0 与 Batch 1。
- 交付脱敏 creator/profile/media fixture/error inventory、formal spec suite、`v1.5.0` release planning index 与 `2026-S25` sprint planning update。
- 只冻结 `creator_profile_by_id` 与 `media_asset_fetch_by_ref` 的 formal contract，不交付 runtime carrier、consumer migration、fake/reference tests implementation、release closeout 或 raw fixture payload files。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0421-v1-5-creator-profile-media-asset-fixture-inventory.md`
  - `docs/exec-plans/CHORE-0421-v1-5-creator-profile-media-asset-spec.md`
  - `docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec.md`
  - `docs/specs/FR-0405-creator-profile-media-asset-read-contract/plan.md`
  - `docs/specs/FR-0405-creator-profile-media-asset-read-contract/data-model.md`
  - `docs/specs/FR-0405-creator-profile-media-asset-read-contract/contracts/README.md`
  - `docs/specs/FR-0405-creator-profile-media-asset-read-contract/risks.md`
  - `docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec-review.md`
  - `docs/releases/v1.5.0.md`
  - `docs/sprints/2026-S25.md`
- 本次不纳入：
  - `syvert/**` runtime implementation
  - `tests/**` implementation or fixture payloads
  - canonical taxonomy / Adapter requirement / Provider offer / compatibility decision admission contract updates
  - `#422/#423/#424/#425/#426` execution
  - `#404` runtime/consumer/evidence implementation
  - release closeout, annotated tag, GitHub Release, published truth carrier
  - raw fixture payload files and any external source name/path mapping

## 当前停点

- Phase `#381`：open，作为 Phase container。
- FR `#405`：open，已显式绑定 `v1.5.0 / 2026-S25`，但只有 `#421` 被允许立即执行。
- Work Item `#421`：open，唯一进入 execution workspace 的 `#405` 事项。
- Workspace key：`issue-421-405-v1-5-0-creator-profile-media-asset-spec`
- Branch：`issue-421-405-v1-5-0-creator-profile-media-asset-spec`
- 主仓 baseline：`04314d6de9c008cccf5719e982fc7dde67652f83`
- 当前变更：Batch 0 artifact、`FR-0405` formal spec suite、`v1.5.0` release planning index、`2026-S25` sprint index update 已提交到 PR `#428`，当前处于 spec review / guardian merge gate 前检查。

## 下一步动作

- 根据 PR review / guardian finding 修正 #421 范围内的 spec、inventory 与 planning truth。
- 重新运行 spec/docs/workflow/version/governance 门禁、diff check、脱敏扫描与 PR guardian。
- 在 PR `#428` 达到 merge-ready 后，按仓库 merge gate 收口 #421；不得在本 PR 扩展到 `#422/#423/#424/#425/#426`。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.5.0` 明确 creator profile / media asset read contract 的 planning truth。
- `v1.5.0` 只绑定 `#405` release slice，不绑定整个 Phase `#381`。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#405` formal spec carrier，可与 `#404` 并行推进，因为本 Work Item 不触碰 runtime/consumer 实现路径。
- 阻塞：
  - 如 `spec review` 未通过，不得进入 `#422/#423` runtime carrier。
  - `#422/#423` 进入 runtime 前必须显式处理 `creator_profile` / `media_asset_fetch` 从 proposed-only 到 approved execution slice 的 taxonomy/admission 更新。
  - `#422/#423/#424/#425/#426` 必须等待 predecessor gates 与 `#404` shared runtime conflict-risk clearance。

## 已验证项

- `#381/#405/#421` GitHub truth 已对齐到本批次执行入口。
- `#405` 当前已显式绑定 `release=v1.5.0`、`sprint=2026-S25`。
- 独立 worktree 与 issue-scoped branch 已创建。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- 脱敏扫描
  - 结果：新增文档未包含外部项目名或本地路径。
- `governance_gate`
  - 命令：`BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-421-405-v1-5-0-creator-profile-media-asset-spec`
  - 结果：通过。
- `python3 scripts/open_pr.py --dry-run --class spec ...`
  - 结果：通过。
- PR `#428`
  - 结果：已创建并绑定 branch/workspace；当前 head SHA 由 PR `headRefOid` 与 guardian merge gate 判定。
- GitHub truth
  - 结果：`#405/#421` planning truth 已作为外部调度事实对齐；本仓内不新增 `docs/decisions/*.md`。

## 未决风险

- 若 `#405` spec 过早吸收 media library、asset storage 或 creator-private fields，Core 会被推向产品模型而不是 runtime contract。
- 若 `#405` runtime/consumer 在 `#404` shared paths 未稳定前启动，可能与 comment collection runtime 产生冲突。
- 若 planning release index 被误写成 published truth，`version_guard` 会将其视为发布事实。
- 若 repository 或 GitHub truth 出现外部项目名、本地路径或 source mapping，会污染后续 release evidence。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 新增的 spec/docs/artifact 增量。
- 保留 `#381/#405/#421` GitHub truth，并在 FR 下重新拆分下一步 Work Item。

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint：`04314d6de9c008cccf5719e982fc7dde67652f83`
- Spec freeze checkpoint：`b4f1616e1a824e6564e8a3f5f76e1a9149d131a8`
- Current live PR head is governed by PR `headRefOid` and guardian merge gate after PR creation.
