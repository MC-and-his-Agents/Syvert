# GOV-0364 v1 Core stable release closeout 执行计划

## 关联信息

- item_key：`GOV-0364-v1-core-stable-release-closeout`
- Issue：`#364`
- item_type：`GOV`
- release：`v1.0.0`
- sprint：`2026-S22`
- Parent Phase：`#363`
- 关联 spec：无（治理 / release closeout 事项）
- 关联 requirement：`docs/specs/FR-0351-v1-core-stable-release-gate/spec.md`
- 关联 decision：`docs/decisions/ADR-GOV-0364-v1-core-stable-release-closeout.md`
- active 收口事项：`GOV-0364-v1-core-stable-release-closeout`
- 状态：`active`

## 目标

- 完成 `v1.0.0` Core stable release closeout，并把 `FR-0351` required gate items 收口为可复验 release truth。
- 在阶段 A carrier 合入 main 后创建 `v1.0.0` annotated tag 与 GitHub Release。
- 通过阶段 B follow-up 回写 published truth carrier，并关闭 Phase `#363` 与 Work Item `#364`。

## 范围

- 本次纳入：
  - `docs/releases/v1.0.0.md`
  - `docs/sprints/2026-S22.md`
  - `docs/exec-plans/GOV-0364-v1-core-stable-release-closeout.md`
  - `docs/exec-plans/artifacts/GOV-0364-v1-core-stable-release-closeout-evidence.md`
  - `docs/decisions/ADR-GOV-0364-v1-core-stable-release-closeout.md`
- 本次不纳入：
  - runtime / Adapter / Provider 实现变更
  - formal spec 语义改写
  - 新 capability contract
  - provider selector、fallback、priority、ranking 或 marketplace
  - 上层应用能力
  - Python package publish

## 当前停点

- Phase `#363`：open。
- FR `#351`：closed completed；作为 gate truth 被当前事项消费。
- `v0.9.0` closeout链路已完成：`#355/#356/#358/#360` closed completed；PR `#357/#359/#361/#362` 已合入。
- 当前主仓 `main == origin/main == 21b30c347c11fc3e576db444cfc073108f512a35`。
- 当前 open PR 为空。
- 当前不存在 `v1.0.0` tag 或 GitHub Release。

## 下一步动作

- 阶段 A：提交 release / sprint / closeout evidence carrier，开 docs PR，等待 checks 与 guardian，通过后受控合入。
- 发布锚点：阶段 A carrier 合入后，在阶段 A merge commit 上创建 `v1.0.0` annotated tag 与 GitHub Release。
- 阶段 B：通过 docs follow-up PR 回写 published truth carrier，并关闭 `#363/#364`。

## 当前 checkpoint 推进的 release 目标

- 使 `v1.0.0` Core stable gate 在发布前具备完整可复验 evidence，并把 release index、main truth、tag、GitHub Release 与 GitHub issue truth 对齐。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S22` 的 `v1.0.0` release closeout / published truth Work Item。
- 阻塞：阶段 A 合入前不得创建 tag / GitHub Release；阶段 B published truth 回写前不得声明 `v1.0.0` 发布完成。

## 已验证项

- `gh api user --jq .login`
  - 结果：`mcontheway`。
- `git status --short --branch`
  - 结果：执行现场分支为 `issue-364-v1-0-0-core-stable-release-closeout`，当前无提交差异前的未跟踪业务改动。
- `git rev-parse HEAD && git rev-parse origin/main`
  - 结果：均为 `21b30c347c11fc3e576db444cfc073108f512a35`。
- `git tag --list 'v1.0.0*'`
  - 结果：无输出。
- `gh release view v1.0.0 --repo MC-and-his-Agents/Syvert --json tagName,name,url,isDraft,isPrerelease,publishedAt,targetCommitish`
  - 结果：`release not found`。
- `gh api 'repos/MC-and-his-Agents/Syvert/pulls?state=open&per_page=100'`
  - 结果：`[]`。
- `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence`
  - 结果：通过，`Ran 72 tests`。
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`
  - 结果：通过，`Ran 79 tests`。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。

## 待验证项

- 阶段 A PR guardian、GitHub checks 与受控 merge。
- 阶段 B PR published truth 回写、guardian、GitHub checks 与受控 merge。
- `#364` closeout comment / close issue。
- Phase `#363` closeout comment / close issue。
- worktree cleanup 与 branch retirement。

## closeout 证据

- 可复验 evidence artifact：`docs/exec-plans/artifacts/GOV-0364-v1-core-stable-release-closeout-evidence.md`
- Release index：`docs/releases/v1.0.0.md`
- Sprint index：`docs/sprints/2026-S22.md`

## 风险

- 若 `release_truth_alignment` 在 tag / GitHub Release 创建前被提前标为通过，会违反 `FR-0351` 场景 8。
- 若 `v1.0.0` closeout 把上层应用、provider 产品支持或 package publish 写成 required gate，会扩大发布范围并扭曲 Core stable 声明。
- 若 tag 指向未包含 closeout carrier 的提交，会降低 `v1.0.0` 发布真相的可复验性。
- 若 provider 字段泄漏检查或双参考回归在当前 head 漂移，`v1.0.0` gate 必须 fail-closed，不得用历史记录替代当前复验。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销 `GOV-0364` release closeout carrier。
- 仓外回滚：若 tag / GitHub Release 已建立但主干事实错误，先修正主干 truth，再通过独立治理 Work Item 决定是否删除 / 重建发布锚点。
- GitHub issue 回滚：若 closeout 后发现事实错误，使用 REST 重新打开 `#363/#364` 并追加纠正评论。

## 最近一次 checkpoint 对应的 head SHA

- 发布前基线：`21b30c347c11fc3e576db444cfc073108f512a35`
