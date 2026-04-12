# FR-0007 Release gate and regression checks

## 关联信息

- item_key：`FR-0007-release-gate-and-regression-checks`
- Issue：`#67`
- item_type：`FR`
- release：`v0.2.0`
- sprint：`2026-S15`

## 背景与目标

- 背景：`v0.2.0` 的目标已经从“能跑”推进到“可验证”。路线图要求自 `v0.2.0` 起，每个版本在进入下一版本前都必须经过假适配器契约测试、双参考适配器回归与平台泄漏检查；但仓库当前尚未把这组三类门禁的职责边界、覆盖范围、失败语义与版本触发时机冻结为 formal spec。
- 目标：为 `v0.2.0` 冻结版本级 gate 的 formal spec，明确版本 gate、双参考适配器回归检查与平台泄漏检查的职责、对象、依赖、失败语义与与下游实现边界，使后续 Work Item 可以在不改写 requirement 的前提下实现具体 harness、脚本或 CI 入口。

## 范围

- 本次纳入：
  - 定义 `v0.2.0` 版本 gate 的必选检查集合与版本触发语义
  - 定义双参考适配器回归检查的对象、覆盖范围、失败语义与固定版本流程地位
  - 定义平台泄漏检查在本仓库中的判定边界与失败语义
  - 定义 `FR-0007` 与 `FR-0006` contract harness 的关系
  - 定义与共享输入模型、标准化错误模型、adapter registry、contract harness 的依赖关系
- 本次不纳入：
  - 任何具体 CI 工作流、脚本参数、目录结构或 GitHub Actions 编排
  - `FR-0004`、`FR-0005`、`FR-0006` 的 formal spec 语义本体
  - 参考适配器、Core 运行时、测试脚本或检查器的实现代码
  - `v0.3.0+` 的版本策略或结果存储能力

## 需求说明

- 功能需求：
  - `v0.2.0` 起的每个版本都必须定义并执行版本级固定 gate；至少包含 contract harness 结果消费、双参考适配器回归检查、平台泄漏检查三类验证。
  - 版本 gate 的 mandatory trigger 至少包括：声明当前版本已完成并准备结束当前版本回合之前，以及声明可以进入下一版本主线之前。实现可以在 PR、nightly 或人工回归中更早执行，但不得替代这两个版本级必选触发点。
  - 双参考适配器回归检查在 `v0.2.0` 范围内必须固定覆盖小红书与抖音两个参考适配器，并验证它们继续通过同一套 Core 契约与共享主路径完成 `v0.2.0` 已批准能力的版本级回归；若后续版本要调整 reference pair，必须通过新的 formal spec 明确冻结。
  - 平台泄漏检查必须固定覆盖 Core 主路径、共享 contract、共享结果 contract 与共享模型边界，判断是否把平台特定语义引入本应平台无关的层。
- 契约需求：
  - `FR-0006` 预期定义 contract test harness 与 fake adapter 的验证基座；`FR-0007` 定义的是版本级 gate 将来如何消费 harness 结论、如何叠加真实参考适配器回归与平台泄漏检查。二者不得互相替代。
  - 双参考适配器回归检查的 gate object 至少包括：
    - `v0.2.0` 冻结的 reference pair；该集合固定为 adapter registry 中登记的小红书与抖音两条真实参考实现。若后续版本要调整 reference pair，必须通过新的 formal spec 明确冻结。
    - 它们在未来共享输入模型约束下可构造的标准输入与执行策略
    - 它们在未来错误模型与 registry 语义下产生的成功态 / 失败态结果
  - 本 FR 只要求版本 gate 在实现时消费上游已落盘并获批准的共享输入模型、错误模型、registry 与 harness 结论；不在此处冻结这些上游 contract 的字段、状态机或 payload 细节。
  - 平台泄漏检查的判定边界必须固定为：
    - 允许平台语义存在于 reference adapter、自身平台研究文档与 adapter 私有实现边界
    - 禁止平台语义渗入 Core 主路径、共享输入模型、共享错误模型、adapter registry 共享契约、共享结果 contract（含 `raw` / `normalized` 的共享结果语义）、以及版本 gate 自身的共享判定逻辑
    - “平台语义”包括但不限于平台名硬编码分支、平台专属 URL/selector/签名细节、平台特定错误码解释、以及只能服务单一平台的共享字段、`normalized` 结果字段或状态语义
  - 版本 gate 的失败语义必须固定为 fail-closed：任一必选 gate 未执行、执行失败、结果不完整或结论不可信时，当前版本都不得被声明为完成，也不得作为进入下一版本主线的已通过基线。
    - “结果不完整”至少包括缺少版本标识、缺少 reference pair 覆盖证明、缺少 contract harness / real-adapter regression / platform leakage 三类检查中的任一结论。
    - “结论不可信”至少包括无法追溯到当前版本目标、无法追溯到当前 reference pair 集合、或无法说明失败 / 通过依据来自哪一类 gate。
  - formal spec 必须只冻结“需要被验证的对象与结论语义”，不得把唯一合法实现形式绑定到某个脚本、某个 CI 文件或某条命令。
- 非功能需求：
  - gate 定义必须保持实现无关，可同时支持本地执行、CI 执行或 release closeout 执行
  - gate 结论必须可追溯到对应版本、参考适配器集合与被验证的共享契约边界
  - gate 失败输出必须能区分 contract harness failure、real-adapter regression failure、platform leakage failure 三类来源，避免混淆定位责任

## 约束

- 阶段约束：
  - 本事项服务于 `v0.2.0`“把能跑推进到可验证”的阶段目标，不提前扩展到 `v0.3.0+`
  - 本事项只冻结版本级验证 requirement，不提前决定具体实现调度或运维编排
- 架构约束：
  - Core 负责运行时语义，Adapter 负责平台语义；版本 gate 不得反向批准平台逻辑进入 Core
  - formal spec 与实现 PR 默认分离；本事项的 formal spec PR 不混入 gate 实现、测试实现或 CI 改造
  - 参考适配器回归检查必须建立在共享输入模型、共享错误模型、shared registry 与 contract harness 已批准的 formal spec 之上，不得以 ad-hoc 平台脚本替代共享契约

## GWT 验收场景

### 场景 1

Given `v0.2.0` 已冻结共享输入模型、错误模型、adapter registry 与 contract harness  
When 团队判断当前版本是否可以结束当前版本回合并进入下一版本  
Then formal spec 必须要求同时通过 contract harness 结果消费、双参考适配器回归检查与平台泄漏检查，且任一缺失都视为 gate 未通过

### 场景 2

Given 某个实现仅运行 fake adapter harness  
When 它试图据此宣称 `v0.2.0` 已完成版本验证  
Then formal spec 必须判定这仍然不满足 `FR-0007`，因为版本 gate 还要求真实双参考适配器回归与平台泄漏检查

### 场景 3

Given adapter registry 中登记的小红书与抖音是当前版本的双参考适配器  
When 版本 gate 执行真实回归检查  
Then formal spec 必须要求两者都在共享 Core 契约下被验证，而不是只抽检单个平台或允许其中一个适配器跳过

### 场景 4

Given Core 主路径、共享模型或共享结果 contract 中出现平台名分支、平台专属 URL 规则、平台特定错误解释或平台专属 `normalized` 字段  
When 平台泄漏检查评估该改动  
Then formal spec 必须把它判定为平台泄漏并使版本 gate fail-closed

### 场景 5

Given 某次版本 gate 的检查结果缺少可信结论，或无法确认覆盖了当前 reference adapter 集合  
When release closeout 试图引用该结果  
Then formal spec 必须把该状态视为 gate 未完成，而不是默认放行

### 场景 6

Given 后续实现团队希望改用新的脚本、CI 编排或本地执行入口  
When 它们仍然满足 `FR-0007` 已冻结的检查对象、触发语义与失败语义  
Then formal spec 必须允许该实现替换，而不要求沿用某个固定脚本或工作流文件

## 异常与边界场景

- 异常场景：
  - 若双参考适配器回归只验证 happy path，而不验证共享错误模型中的失败语义，版本 gate 仍不完整。
  - 若平台泄漏检查只扫描 adapter 私有实现，而不检查 Core 主路径与共享模型，无法满足本 FR。
  - 若 gate 只能在单一 CI 入口执行，导致本地或 release closeout 无法复验，会削弱版本 gate 的可追溯性与实现弹性。
- 边界场景：
  - `FR-0007` 不负责定义 fake adapter harness 的具体接口、fixture 组织或工具命令，这些属于 `FR-0006`。
  - `FR-0007` 可以引用 `FR-0004`、`FR-0005`、`FR-0006` 作为依赖前提，但不得改写它们的共享模型语义。
  - 平台研究文档、reference adapter 私有代码、平台特定测试数据可以包含平台语义；只要这些语义未穿透到 Core 主路径与共享 contract，就不构成平台泄漏。

## 验收标准

- [ ] formal spec 明确把 contract harness 结果消费、双参考适配器回归检查、平台泄漏检查定义为版本级固定 gate
- [ ] formal spec 明确写出版本 gate 的 mandatory trigger、覆盖对象与 fail-closed 失败语义
- [ ] formal spec 明确写出平台泄漏检查在 Syvert 中的允许边界与禁止边界，且显式覆盖共享结果 contract
- [ ] formal spec 明确区分 `FR-0006` 的 harness 基座职责与 `FR-0007` 的版本 gate 职责
- [ ] formal spec 明确写出未来共享输入模型、错误模型、adapter registry 与 harness 结果对版本 gate 的依赖关系
- [ ] formal spec 不把唯一实现形式绑定到某个脚本、CI 文件或命令行参数

## 数据模型与迁移说明

- 本 FR 不新增也不修改共享输入模型、共享错误模型、adapter registry 或 contract harness 的数据字段与状态机。
- 本 PR 只落盘 `FR-0007` requirement、契约摘要、风险与索引入口，不涉及任何数据迁移步骤。

## 依赖与外部前提

- 外部依赖：
  - `#63` 作为 `v0.2.0` 当前 Phase 已建立
  - `#64`、`#65`、`#66` 分别承载共享输入模型、错误模型/registry、contract harness 的上游 FR；这些 formal spec / contract 已作为当前 `spec-ready` 审查输入的入库基线存在，并将作为后续实现 Work Item 的依赖前提被消费
- 上下游影响：
  - 后续 `FR-0007` 下属 Work Item 需基于本 formal spec 实现 gate 编排、结果收口与 closeout
  - `FR-0006` 的实现必须提供可被版本 gate 消费的 contract harness 结论
