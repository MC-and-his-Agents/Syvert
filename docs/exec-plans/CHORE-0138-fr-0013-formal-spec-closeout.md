# CHORE-0138-fr-0013-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0138-fr-0013-formal-spec-closeout`
- Issue：`#192`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0013-adapter-resource-requirement-declaration/`
- 关联 PR：`#200`
- 状态：`active`
- active 收口事项：`CHORE-0138-fr-0013-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0013` formal spec 套件，冻结 `AdapterResourceRequirementDeclaration` 的最小 formal contract，并把它约束在 `FR-0015` 已批准的共享能力词汇与共享证据之内。

## 范围

- 本次纳入：
  - `docs/specs/FR-0013-adapter-resource-requirement-declaration/`
  - `docs/exec-plans/FR-0013-adapter-resource-requirement-declaration.md`
  - `docs/exec-plans/CHORE-0138-fr-0013-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - `FR-0010` / `FR-0012` / `FR-0014` / `FR-0015` 正文
  - runtime、resource matching、provider 实现与 release gate 逻辑

## 当前停点

- `issue-192-fr-0013-formal-spec` 已作为 `#192` 的独立 spec worktree 建立。
- 当前回合只允许修改 `FR-0013` formal spec 套件与两个 exec-plan，禁止越界到 runtime / tests / 相邻 FR。
- 最新 formal spec 语义 checkpoint `1199c85cfeb57c9f8d6a17f3c4ba70f44cca25e6` 已生成，当前受审 spec PR 为 `#200`；当前停点是把最新门禁结果与 PR 真相同步回 exec-plan，并等待 review / guardian / merge gate。

## 下一步动作

- 在当前受审 PR `#200` 上继续消费 review / guardian / merge gate 反馈。
- 若后续只追加 PR / checks / checkpoint metadata，则保持 review-sync follow-up 口径，不伪装成新的语义 checkpoint。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 把“适配器资源需求声明”收敛为 implementation-ready 的最小 formal contract，并确保该 contract 只消费双参考适配器已被共享证据证明的 `account` / `proxy` 语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0013` 的 formal spec closeout Work Item。
- 阻塞：
  - 若声明 carrier 不冻结，后续实现容易把资源匹配扩写成 provider / fallback / 优先级系统。
  - 若声明词汇与共享证据边界不收紧，后续事项可能把单平台私有前置误写成共享资源能力。

## 已验证项

- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md` 的上位边界。
- 已核对 `FR-0010` / `FR-0012` formal spec 与 closeout 风格，确认 `FR-0013` 只新增声明层，不反写生命周期与注入边界。
- `git commit -m 'docs(spec): 冻结 FR-0013 适配器资源需求声明 contract'`
  - 结果：已生成最新语义 checkpoint `1199c85cfeb57c9f8d6a17f3c4ba70f44cca25e6`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-192-fr-0013-formal-spec`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 192 --item-key CHORE-0138-fr-0013-formal-spec-closeout --item-type CHORE --release v0.5.0 --sprint 2026-S18 --title 'docs(spec): 收口 FR-0013 适配器资源需求声明 formal spec' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建当前受审 spec PR `#200 https://github.com/MC-and-his-Agents/Syvert/pull/200`

## 未决风险

- 若 `resource_dependency_mode` 扩张到 `preferred`、`fallback` 或 provider 选择语义，会直接越过 `v0.5.0` 边界。
- 若 `evidence_refs` 被写成描述性备注而不是共享证据绑定，`FR-0013` 将失去“只来自 FR-0015 已批准共享事实”的约束。
- 若 `required_capabilities[]` 允许出现 `account` / `proxy` 之外的词汇，后续实现会被迫围绕未被双参考适配器共同验证的能力扩张。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0013` formal spec 套件与当前 closeout exec-plan 的文档增量，不回退其他 FR 或 runtime 变更。

## 最近一次 checkpoint 对应的 head SHA

- `1199c85cfeb57c9f8d6a17f3c4ba70f44cca25e6`
- review-sync 说明：当前 live head 已包含 checkpoint SHA、门禁结果与 PR metadata；后续若只追加同类同步，不把 metadata-only follow-up 伪装成新的语义 checkpoint。
