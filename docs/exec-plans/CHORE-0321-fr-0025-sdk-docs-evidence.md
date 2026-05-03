# CHORE-0321-fr-0025-sdk-docs-evidence 执行计划

## 关联信息

- item_key：`CHORE-0321-fr-0025-sdk-docs-evidence`
- Issue：`#321`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0025-provider-capability-offer-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0321-fr-0025-sdk-docs-evidence`
- 状态：`active`

## 目标

- 把 `#319/#320` 已合入主干的 `ProviderCapabilityOffer` formal spec、validator 与 fixture 结果转成 SDK 作者文档和 evidence 口径。
- 明确 Provider offer 是 Adapter-bound 能力声明，只能由后续 `FR-0026` compatibility decision 消费，不是 Core provider registry、selector、fallback、marketplace 或真实 provider 产品支持承诺。

## 范围

- 本次纳入：
  - `adapter-sdk.md`
  - `docs/exec-plans/CHORE-0321-fr-0025-sdk-docs-evidence.md`
  - `docs/exec-plans/artifacts/CHORE-0321-fr-0025-provider-offer-sdk-evidence.md`
  - 必要的 `docs/releases/v0.8.0.md` 与 `docs/sprints/2026-S21.md` 索引入口
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `docs/specs/FR-0025-provider-capability-offer-contract/**` formal spec 正文
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/**`
  - runtime decision、provider no-leakage guard、真实 provider 样本
  - Core provider registry、selector、routing、priority、fallback 或 marketplace
  - 关闭父 FR `#297`

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-321-fr-0025-provider-offer-sdk`
- 分支：`issue-321-fr-0025-provider-offer-sdk`
- 原始 worktree 创建基线：`4e90953447e20b1fffaee0f8104f989bd043202e`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`#321`、父 FR `#297`、`#319` / PR `#328` 与 `#320` / PR `#335` 的主干事实。
- 当前 checkpoint：已将 Adapter SDK 中的 Provider offer 示例更新为 `ProviderCapabilityOffer` canonical carrier，并新增 evidence artifact 解释 fixture refs、validator 结论、Adapter-bound 边界与后续 `FR-0026` 消费关系。

## 下一步动作

- 运行 `docs_guard`、`spec_guard`、`workflow_guard`、`governance_gate` 与 `pr_scope_guard --class docs` 门禁。
- 使用中文 Conventional Commit 提交 docs checkpoint。
- 使用 `scripts/open_pr.py --class docs` 受控创建 PR，并绑定 `Fixes #321`。
- 运行 guardian review；guardian 不设置超时。
- guardian、GitHub checks 与 merge gate 通过后，使用受控 merge 入口合入。
- closeout `#321`，在父 FR `#297` comment 记录 SDK docs / evidence 主干事实，并清理 worktree / 退役分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 补齐 Provider capability offer 的作者可消费文档与证据口径，使 `FR-0025` 不只停留在 formal spec / validator，而能被后续 compatibility decision 与父 FR closeout 直接引用。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0025` 的 SDK docs / evidence Work Item。
- 阻塞：
  - `#322` 父 FR closeout 需要本事项提供的 docs / evidence 主干事实。
  - 后续 `FR-0026` docs / migration 需要本事项明确 offer 是 Provider-side input，不反向定义 decision。

## 已验证项

- `python3 scripts/create_worktree.py --issue 321 --class docs`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-321-fr-0025-provider-offer-sdk`，分支 `issue-321-fr-0025-provider-offer-sdk`，基线 `4e90953447e20b1fffaee0f8104f989bd043202e`。
- `gh api user --jq .login`
  - 结果：通过；确认本机 `gh` keyring 可用，登录用户为 `mcontheway`，未全局导出 `GH_TOKEN` / `GITHUB_TOKEN`。
- 已核对 `#321` GitHub truth：item_key=`CHORE-0321-fr-0025-sdk-docs-evidence`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，integration fields 为 `none/no/local_only`。
- 已核对父 FR `#297`：本事项不得关闭父 FR，不得引入 Core provider registry、provider selector、fallback priority、marketplace、真实 provider 产品支持或 compatibility decision。
- 已核对 PR `#328` 已合入：`FR-0025` formal spec / data model / contracts 已作为 Provider offer carrier truth 进入主干。
- 已核对 PR `#335` 已合入：`syvert/provider_capability_offer.py`、`tests/runtime/provider_capability_offer_fixtures.py` 与 `tests/runtime/test_provider_capability_offer.py` 已作为 validator / fixture truth 进入主干。
- `git commit -m 'docs(sdk): 补齐 FR-0025 provider offer 证据'`
  - 结果：已生成 docs checkpoint `91f1d18dfc9b9bc5d5c765ca9e8ea848c5b8a823`。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过，`docs-guard 通过。`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过，`spec-guard 通过。`
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过，`workflow-guard 通过。`
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-321-fr-0025-provider-offer-sdk`
  - 结果：通过，`governance-gate 通过。`
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`docs`，变更类别=`docs`。

## 待验证项

- PR guardian review、GitHub checks、受控 merge 与 closeout reconciliation

## 未决风险

- 若文档把 `declared` offer 解释成 `matched` 或 selected provider，会提前越过 `FR-0026` compatibility decision。
- 若文档把 provider key 或 provider port ref 解释成 Core registry / routing / discovery 入口，会破坏 Core / Adapter / Provider 边界。
- 若 fixture evidence refs 被改写成临时日志、marketplace 文案或 provider 私有材料，会破坏 `FR-0025` evidence contract。

## 回滚方式

- 使用独立 revert PR 撤销本次 docs / evidence / exec-plan / release-sprint index 增量。
- 若需要改变 `ProviderCapabilityOffer` carrier 本体，必须回到 `FR-0025` formal spec 或 validator Work Item，不得在 docs PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- docs checkpoint：`91f1d18dfc9b9bc5d5c765ca9e8ea848c5b8a823`
- validation result follow-up checkpoint：`a4a77ddd70309fe970f9db17e4cd8612f2582036`
- 说明：后续若仅补 PR / guardian / merge gate / closeout metadata，不自动推进上述语义 checkpoint；当前 live review head 由 PR head 与 guardian state 绑定。
- worktree 创建基线：`4e90953447e20b1fffaee0f8104f989bd043202e`
