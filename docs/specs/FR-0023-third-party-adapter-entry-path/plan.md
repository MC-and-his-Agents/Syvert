# FR-0023 Third-party Adapter entry path 实施计划

## 关联信息

- item_key：`FR-0023-third-party-adapter-entry-path`
- Issue：`#295`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 exec-plan：`docs/exec-plans/CHORE-0309-fr-0023-formal-spec-closeout.md`

## 实施目标

- 在 contract test entry、SDK docs / migration 与父 FR closeout 之前，先冻结第三方 Adapter 的最小 public metadata、manifest / fixture / contract test 准入、Adapter-only 接入边界和 reference adapter 升级约束，使 `FR-0023` 成为后续 Work Item 的 governing artifact。

## 分阶段拆分

- 阶段 1：`#309` 收口 `FR-0023` formal spec 套件，冻结 Adapter-only 接入路径、最小 metadata、manifest / fixture / contract test 准入与非目标。
- 阶段 1A：`#331` 收口第三方真实 `adapter_key` 与 `FR-0027` proof coverage 之间的 formal/evidence bridge，冻结 adapter-specific resource proof admission。
- 阶段 2：`#310` 基于本 spec 落地 contract test entry，校验 manifest、metadata、`FR-0027` resource declaration、第三方 resource proof admission、fixtures 与 Adapter execute 行为。
- 阶段 3：`#311` 基于本 spec 更新 SDK docs / migration，说明第三方 Adapter 作者如何准备 manifest、fixtures、contract test profile 与 reference baseline。
- 阶段 4：`#312` 汇总 formal spec、contract test entry、SDK docs / migration、reference adapter baseline 与 GitHub 状态，完成 `FR-0023` parent closeout。

## 实现约束

- 不允许触碰的边界：
  - 不得在 `#309` 中修改 `syvert/**`、`tests/**`、reference adapters、runtime、SDK 代码或 contract test harness 实现。
  - 不得定义 Provider capability offer。
  - 不得定义 Adapter / Provider compatibility decision。
  - 不得接入真实外部 provider 样本。
  - 不得引入 provider registry、provider selector、provider marketplace、provider fallback priority、打分或排序。
  - 不得重写 `FR-0027` 已冻结的多 profile resource requirement contract。
  - 不得让真实第三方 `adapter_key` 裸借用只覆盖 `xhs` / `douyin` 的 `FR-0027` proof；必须通过 adapter-specific `ThirdPartyResourceProofAdmission` 建立 proof coverage。
- 与上位文档的一致性约束：
  - 必须满足 `AGENTS.md` 对 Core / Adapter 分层、formal spec 与实现分离、Work Item 执行入口的约束。
  - 必须满足 `WORKFLOW.md` 对 active exec-plan、release / sprint / item_key 绑定、checkpoint 与门禁记录的要求。
  - 必须满足 `spec_review.md` 对 `spec.md`、`plan.md`、GWT、异常 / 边界场景、验收标准与进入实现前条件的要求。
  - 必须消费 `FR-0021` 的 provider port 内部边界和 `FR-0027` 的多 profile resource requirement 前提，不创建并行 truth。

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-331-fr-0023-adapter-resource-proof-admission`
  - `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- implementation 阶段：
  - `#310` 必须补 contract test entry 自动化，覆盖 manifest shape、最小 metadata、`FR-0027` resource declaration、fixture refs、success payload 与 error mapping。
  - `#310` 必须使用真实第三方 `adapter_key` 作为通过样例，并覆盖 adapter-specific `resource_proof_admission_refs`；不得把第三方样例伪装为 `xhs` / `douyin`。
  - `#310` 必须把 `ThirdPartyResourceProofAdmission` 纳入 resource proof binding 判定本身；不得先调用会因 `reference_adapters` 不含第三方 key 而失败的完整 `FR-0027` adapter coverage 校验，再尝试后置补救。
  - `#310` 必须从当前 manifest-owned `resource_proof_admissions` 解析 admission，并逐 profile 校验 uncovered declaration profile 与 admission 的一一对应关系。
  - `#311` 必须补 SDK docs / migration 的可审查示例，展示第三方 Adapter 如何准备 manifest、fixtures 与 contract test profile。
  - `#312` 必须核对主干事实、GitHub issue 状态、release / sprint 语义与 parent closeout comment。
- 手动验证：
  - 核对 spec 中第三方接入主入口是否始终为 Adapter，而不是 Provider 或 Core plugin。
  - 核对最小 public metadata 是否足以让 contract test 不依赖会话上下文或真实外部服务。
  - 核对所有 resource declaration 语义是否回指 `FR-0027`，没有创建第二套资源声明模型。
  - 核对 third-party resource proof admission 是否只桥接 `adapter_key` coverage，不放宽 `FR-0027` approved shared profile proof、tuple 或 execution path。
  - 核对准入顺序是否保证 admission 参与 adapter coverage 子条件，而不是被放在不可达的完整 `FR-0027` 校验之后。
  - 核对 `resource_proof_admission_refs` 是否只解析当前 manifest 的 `resource_proof_admissions`，且每个 uncovered profile 都有且只有一个 matching admission。
  - 核对 out of scope 是否明确排除 provider offer、compatibility decision、真实 provider 样本、provider registry / selector / marketplace 与 runtime 实现。
  - 核对 reference adapter 升级约束是否保持小红书、抖音作为第三方 Adapter 接入 baseline。

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不修改 runtime 或测试文件。
  - `#310` 应先写 contract test entry tests，再实现 manifest / fixture / metadata 校验。
  - `#310` 应先写真实第三方 `adapter_key` + adapter-specific proof admission 的通过测试，以及裸借用 reference proof 的 fail-closed 测试。
- 暂不纳入 TDD 的模块与理由：
  - runtime implementation、contract test harness implementation 属于 `#310`。
  - SDK docs / migration 示例属于 `#311`。
  - parent closeout 与 GitHub 状态 reconciliation 属于 `#312`。
  - Provider offer、compatibility decision 与真实 provider 样本明确不属于 `FR-0023`。

## 并行 / 串行关系

- 可并行项：
  - 在 `#309` spec review 期间，可以只读盘点当前 adapter SDK 文档与 reference adapter metadata 现状，为 `#310/#311` 准备实现输入。
- 串行依赖项：
  - `#310`、`#311` 进入正式执行前，必须消费已通过 spec review 并合入主干的 `FR-0023` formal spec。
  - `#310` 若要在真实第三方 `adapter_key` 下通过 resource declaration 准入，必须先消费 `#331` 合入后的 `ThirdPartyResourceProofAdmission` truth。
  - `#312` 必须等待 `#309/#310/#311` 主干事实齐备后再收口。
- 阻塞项：
  - 若 `FR-0023` 未先冻结 Adapter-only 接入路径，后续 contract test 与 SDK docs 可能各自发明 manifest、fixture 或 provider 边界。
  - 若 `FR-0027` 前提不可用，第三方 Adapter resource requirement 准入不能在本 FR 下重新定义，必须回到 `FR-0027` truth 修复。
  - 若缺少 adapter-specific proof admission，`#310` 不得通过删除 `FR-0027` `reference_adapters` 覆盖校验来 unblock。

## 进入实现前条件

- [ ] `spec review` 已通过。
- [ ] `FR-0023` 已明确第三方 Adapter 最小 public metadata 与 manifest / fixture / contract test 准入。
- [ ] `FR-0023` 已明确 Adapter-only 接入路径和 provider 非目标边界。
- [ ] `FR-0023` 已明确消费 `FR-0027` 多 profile resource requirement contract，不重写资源声明模型。
- [ ] `FR-0023` 已明确第三方真实 `adapter_key` 的 adapter-specific proof admission bridge。
- [ ] `FR-0023` 已明确 reference adapter 升级约束。
- [ ] `#310/#311/#312` 的进入条件均可直接回指本 formal spec。
