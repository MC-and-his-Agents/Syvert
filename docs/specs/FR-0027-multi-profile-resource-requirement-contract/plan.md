# FR-0027 实施计划

## 关联信息

- item_key：`FR-0027-multi-profile-resource-requirement-contract`
- Issue：`#294`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 exec-plan：
  - `docs/exec-plans/FR-0027-multi-profile-resource-requirement-contract.md`
  - `docs/exec-plans/CHORE-0298-fr-0027-formal-spec-closeout.md`

## 实施目标

- 在进入 evidence、runtime 与 reference adapter migration 之前，先冻结 `v0.8.0` 当前双参考 slice 的 multi-profile declaration carrier、matcher `one-of` 语义与 profile evidence 消费边界，使 `FR-0027` 成为后续三类实现 Work Item 的 governing artifact。

## 分阶段拆分

- 阶段 1：`#299` 收口 `FR-0027` formal spec 套件，冻结 declaration/profile/matcher/error boundary 与 `v0.8.0` version boundary。
- 阶段 2：`#300` 基于本 spec 刷新 `FR-0015` 的 profile-level `shared / adapter_only / rejected` evidence truth，并产出 `ApprovedSharedResourceRequirementProfileEvidenceEntry` 对应的主干 carrier。
- 阶段 3：`#301` 与 `#302` 分别按本 spec 落地 matcher/runtime 和 reference adapter declaration migration。
- 阶段 4：`#303` 汇总 spec、evidence、runtime、adapter baseline 与 GitHub 状态，完成 FR parent closeout。

## 实现约束

- 不允许触碰的边界：
  - 不得在本事项中修改 `syvert/**`、`tests/**`、reference adapters 或 runtime 代码
  - 不得在本事项中新增 provider capability offer / compatibility decision 语义
  - 不得在本事项中引入 profile 优先级、排序、自动 fallback 或技术实现字段
  - 不得把 `FR-0010` / `FR-0012` 相邻 contract 改写进本 FR
- 与上位文档的一致性约束：
  - 必须满足 `vision.md` 对 “Core 负责运行时语义、Adapter 负责目标系统语义” 的边界
  - 必须满足 `docs/roadmap-v0-to-v1.md` 对 `v0.8.0` “稳定第三方 Adapter 接入路径与 Adapter / Provider 兼容性判断模型” 的阶段目标
  - 必须把 `FR-0013` / `FR-0014` / `FR-0015` 作为 `v0.5.0` 历史基线引用，而不是在本 PR 中混合重写多个旧 formal spec 套件
  - 必须避免在仓内形成两个并行的 `v0.8.0` canonical truth：`FR-0027` 是当前双参考 slice 的 multi-profile declaration / matcher / proof binding 的唯一正式规约入口

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha \"$BASE\" --head-sha \"$HEAD_SHA\" --head-ref issue-299-fr-0027-formal-spec`
- implementation 阶段：
  - `#300` 必须验证 evidence artifact / research / registry 能表达 shared / adapter_only / rejected profile
  - `#301` 必须补 matcher / runtime tests，覆盖 `matched`、`unmatched`、`invalid_resource_requirement` 与 `resource_unavailable`
  - `#302` 必须补 reference adapter regression / declaration fixtures，证明新 carrier 被 matcher 正确消费
- 手动验证：
  - 核对 spec 中是否只有 `none`、`account`、`proxy` 组合空间，没有偷渡新能力词汇
  - 核对 `one-of` 语义是否未退化为排序 / fallback 机制
  - 核对 `FR-0027` 与 `FR-0015` 的 evidence status 词汇没有漂移，继续使用 `shared / adapter_only / rejected`，同时 profile-level `decision` 已明确切换为 `approve_profile_for_v0_8_0`
  - 核对 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref` 的唯一性、proof tuple shape、proof execution path、单 proof 绑定、declaration adapter 覆盖与 `available_resource_capabilities` 的 fail-closed 口径都已明文冻结
  - 核对 version boundary 是否明确：`FR-0027` 只治理 `v0.8.0` multi-profile truth，`FR-0013` / `FR-0014` / `FR-0015` 保留历史语义

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不涉及运行时代码或测试文件变更
- 暂不纳入 TDD 的模块与理由：
  - matcher/runtime tests 属于 `#301`
  - reference adapter regression 与 fixtures 属于 `#302`
  - evidence artifact / registry 验证属于 `#300`

## 并行 / 串行关系

- 可并行项：
  - 在 `#299` 合入前，可并行摸清 runtime matcher、reference adapter 声明与 evidence 现状，以便后续 Work Item 直接接续
- 串行依赖项：
  - `#300`、`#301`、`#302` 进入正式执行前，必须先消费本 FR 已冻结的 declaration/profile/matcher boundary
  - `#303` 必须等待前三个 Work Item 主干事实齐备后再收口
- 阻塞项：
  - 若 `FR-0027` 没有先冻结 multi-profile contract，后续实现会各自发明 declaration 形状、matcher 语义与 profile 合法性判断

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] `FR-0027` 已明确 declaration/profile carrier、`one-of` matcher 语义与 evidence 边界
- [ ] `FR-0027` 已明确 proof carrier 的唯一性、approved execution path、单 proof 绑定、tuple canonicalization、adapter 覆盖与 matcher 输入 fail-closed 口径
- [ ] `#300/#301/#302` 的进入条件均可直接回指 `FR-0027` formal spec
