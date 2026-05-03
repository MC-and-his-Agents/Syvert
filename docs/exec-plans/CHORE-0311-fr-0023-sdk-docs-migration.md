# CHORE-0311-fr-0023-sdk-docs-migration 执行计划

## 关联信息

- item_key：`CHORE-0311-fr-0023-sdk-docs-migration`
- Issue：`#311`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0023-third-party-adapter-entry-path/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0311-fr-0023-sdk-docs-migration`
- 状态：`active`

## 目标

- 将 `FR-0023` formal spec、`#331` resource proof admission bridge 与 `#310` 已合入的 third-party contract entry 转成 Adapter SDK 作者指南与升级指引。
- 明确第三方 Adapter 作者如何准备 manifest、resource proof admission、fixtures 与 contract test profile。
- 明确 Adapter-only 与 Adapter + Provider 的边界，避免第三方 Adapter 文档提前定义 Provider offer、compatibility decision、selector、fallback 或 marketplace。

## 范围

- 本次纳入：
  - `adapter-sdk.md`
  - `docs/releases/v0.8.0.md`
  - `docs/sprints/2026-S21.md`
  - `docs/exec-plans/CHORE-0311-fr-0023-sdk-docs-migration.md`
- 本次不纳入：
  - `docs/specs/FR-0023-third-party-adapter-entry-path/**` formal spec 变更
  - `docs/specs/FR-0024-adapter-capability-requirement-contract/**`
  - `docs/specs/FR-0025-provider-capability-offer-contract/**`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/**`
  - `docs/specs/FR-0027-multi-profile-resource-requirement-contract/**`
  - `tests/**`
  - `syvert/**`
  - runtime behavior、contract harness implementation、Provider offer、compatibility decision 或真实外部 provider 样本

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-311-fr-0023-adapter-sdk`
- 分支：`issue-311-fr-0023-adapter-sdk`
- 原始 worktree 创建基线：`4e90953447e20b1fffaee0f8104f989bd043202e`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`#311` GitHub truth、`FR-0023` formal suite、`#331` bridge exec-plan、`#310` contract entry exec-plan 与 current third-party fixtures。
- 当前 checkpoint：已更新 Adapter SDK 文档，补充 `run_third_party_adapter_contract_test()`、`validate_third_party_adapter_manifest()`、`validate_third_party_adapter_fixtures()` 作者入口，展示与 `tests/runtime/contract_harness/third_party_fixtures.py` 一致的 `community_detail` manifest、resource proof admission 与 success / error_mapping fixture 示例；已同步 `v0.8.0` release 与 `2026-S21` sprint 索引，补齐 FR-0023 / #309 / #331 / #310 / #311 / #312 回链。

## 下一步动作

- 运行 docs class 本地门禁：docs、spec、workflow、governance 与 pr_scope。
- 提交中文 Conventional Commit，使用受控 `open_pr` 创建 docs PR。
- 等待 guardian review、GitHub checks 与受控 merge。
- 合入后 closeout `#311`，向父 FR `#295` 评论 docs evidence，并退役分支 / worktree。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 的第三方 Adapter 稳定接入路径补齐作者可执行文档，使 formal spec、contract test entry、SDK docs 与 release / sprint 索引保持一致。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0023` SDK docs / migration Work Item。
- 阻塞：
  - `#312` 父 FR closeout 需要本 docs evidence。
  - 后续第三方 Adapter 作者指南需要引用已合入的 `#310` contract entry truth。

## 已验证项

- `python3 scripts/create_worktree.py --issue 311 --class docs`
  - 结果：通过；创建 worktree `/Users/mc/code/worktrees/syvert/issue-311-fr-0023-adapter-sdk`，分支 `issue-311-fr-0023-adapter-sdk`，基线 `4e90953447e20b1fffaee0f8104f989bd043202e`。
- `gh api repos/:owner/:repo/issues/311 --jq '{number,title,state,body,labels:[.labels[].name],assignees:[.assignees[].login]}'`
  - 结果：通过；确认 `#311` open，item_key=`CHORE-0311-fr-0023-sdk-docs-migration`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，父 FR=`#295`。
- 已核对 `#310` merge commit `4e90953447e20b1fffaee0f8104f989bd043202e`，确认 third-party contract entry 与 fixture truth 已在主干。
- 已核对 `tests/runtime/contract_harness/third_party_entry.py` 的入口函数名与 `tests/runtime/contract_harness/third_party_fixtures.py` 的 manifest / admission / fixture 字段。
- `python3 scripts/pr_guardian.py review 337 --post-review`
  - 初次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：SDK docs 手写 `resource_proof_admission_refs` 示例 prefix，与 `FR-0023` formal spec 中的 scenario 示例命名不一致，容易形成第二套 admission ref 命名。
  - 修正：不修改 `FR-0023` formal spec；SDK docs 改为引用 `tests/runtime/contract_harness/third_party_fixtures.py` 中的 admission ref constants，并明确 SDK 文档不重新定义 admission ref 字符串命名。
  - 第二次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：分支基于旧 `origin/main`，会回滚 PR `#336` / commit `bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c` 已合入的 `FR-0024` closeout exec-plan 与 release / sprint 索引事实。
  - 修正：已 rebase 到 `origin/main@bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c`，手动合并 `docs/sprints/2026-S21.md` 冲突，保留 FR-0024 与 FR-0023 两组索引。
  - 第三次结果：`REQUEST_CHANGES`，`safe_to_merge=false`。
  - 阻断项：exec-plan 未记录 `adapter-sdk.md` 修复后的 final-head validation evidence，且 sprint `相关 Issue / PR` 缺少 `#331` resource proof bridge。
  - 修正：补充 `#331` 到 sprint GitHub 回链，并在本执行计划记录 PR head `4081dc959bb8cb52200f9ed83c2450fbabee81e6` 的本地门禁结果。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过；提交 `3f5f0ab` 后复跑通过；rebase 到 `bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c` 后复跑通过；PR head `4081dc959bb8cb52200f9ed83c2450fbabee81e6` 复跑通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过；提交 `3f5f0ab` 后复跑通过；rebase 到 `bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c` 后复跑通过；PR head `4081dc959bb8cb52200f9ed83c2450fbabee81e6` 复跑通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过；提交 `3f5f0ab` 后复跑通过；rebase 到 `bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c` 后复跑通过；PR head `4081dc959bb8cb52200f9ed83c2450fbabee81e6` 复跑通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-311-fr-0023-adapter-sdk`
  - 结果：通过；提交 `3f5f0ab` 后复跑通过；rebase 到 `bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c` 后复跑通过；PR head `4081dc959bb8cb52200f9ed83c2450fbabee81e6` 复跑通过。
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 提交前结果：未执行通过；提交前 `HEAD` 相对 `origin/main` 尚无已提交 diff，脚本报告“当前分支相对基线没有变更”。
  - 提交 `3f5f0ab` 后结果：通过，PR class=`docs`，变更类别=`docs`。
  - rebase 到 `bf004b6c6877cdbee4a1c8e69dbdbf1ea764431c` 后结果：通过，PR class=`docs`，变更类别=`docs`。
  - PR head `4081dc959bb8cb52200f9ed83c2450fbabee81e6` 结果：通过，PR class=`docs`，变更类别=`docs`。
- `git diff --check`
  - 结果：通过。
- 提交 `3f5f0abf85a4def80ddd1e23c3dd21f52738fbd0`
  - 结果：已生成 docs checkpoint，提交信息 `docs(adapter): 补齐 FR-0023 SDK 接入指引`。
- rebase 后提交 `a453ce762e9ef9434df999d9dd394c2634c0e53f`
  - 结果：保留同一 docs checkpoint 内容并同步到当前主干；提交信息 `docs(adapter): 补齐 FR-0023 SDK 接入指引`。

## 待验证项

- guardian review、GitHub checks、受控 merge、issue closeout、父 FR comment 与 worktree retirement。

## 未决风险

- 若 SDK docs 把 `resource_proof_admissions` 描述成全局 registry 或 fixture side channel，会破坏 `FR-0023` manifest-owned proof bridge truth。
- 若第三方作者指南把 Provider offer / compatibility decision 混入 Adapter-only contract entry，会越过 `FR-0025` / `FR-0026` formal ownership。
- 若 release / sprint 索引漏掉 FR-0023 事项链，`#312` 父 FR closeout 会缺少 docs evidence 回链。

## 回滚方式

- 通过独立 revert PR 撤销本事项对 Adapter SDK 文档、release / sprint 索引与本 exec-plan 的增量修改；不得通过文档回滚改写已批准 formal spec 或已合入 contract entry。

## 最近一次 checkpoint 对应的 head SHA

- docs checkpoint：`a453ce762e9ef9434df999d9dd394c2634c0e53f`
- 说明：后续若仅补 PR / guardian / merge gate / closeout 元数据，作为 review-sync follow-up，不把版本化 checkpoint SHA 退化为必须穷尽当前 PR head 的状态面。
