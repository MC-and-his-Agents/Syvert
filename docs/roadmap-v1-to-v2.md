# Syvert 路线图 v1.0.0 到 v2.0.0

## 目的

这份路线图定义 Syvert 在 `v1.0.0` Core stable 之后，到 `v2.0.0` 扩展运行时能力稳定化之前的预期演进方向。

它不替代 `docs/roadmap-v0-to-v1.md`。`v0.x -> v1.0.0` 的任务是稳定 Core、Adapter SDK、参考适配器与 Adapter / Provider 兼容性判断；`v1.x -> v2.0.0` 的任务是在稳定 Core 之上扩展可治理的 runtime capability contract。

版本命名、major / minor / patch 语义、release closeout、tag 与 GitHub Release 管理规则见 `docs/process/version-management.md`。

## 定位

`v1.x` 不是上层应用路线。

Syvert 主仓继续聚焦：

- Core runtime
- Adapter SDK
- Adapter-bound provider contract
- 参考适配器
- contract test / validation / operability tooling

账号管理控制台、内容库、发布中心、自动运营工作流、行业应用等上层产品应在独立仓库中消费 Syvert。它们可以反向提供场景压力，但不能成为 Syvert Core 的职责边界。

## 版本号与成熟度规则

`v1.x` 是能力扩展阶段，不是从 `v1.1` 数到 `v1.9` 后自动跳到 `v2.0.0` 的倒计时。

`v2.0.0` 只在满足成熟度 gate 后发生：

- 新增 runtime capability 的准入、声明、执行、结果、验证与兼容性判断已经形成稳定闭环。
- 至少一组读侧能力、批量 / dataset 能力、资源治理扩展与写侧安全契约经过真实 Adapter / Provider 证据验证。
- `v1.0.0` 的 Core / Adapter / Provider 边界没有被新增能力破坏。
- 上层应用仍保持独立仓库消费关系，没有被并入 Syvert 主仓职责。

因此，`v1.x` 可以自然出现 `v1.8`、`v1.9`、`v1.10` 或更长的 minor 序列。只有当上述 gate 全部满足，且需要对外声明“扩展 runtime capability contract 已稳定”时，才进入 `v2.0.0`。

`v2.0.0` 不是功能数量目标，也不是上层应用完整度目标。它是底座契约成熟度声明。

## 演进原则

- 先扩展公共 operation / capability contract，再让 Adapter 声明支持，最后由 adapter-bound provider 实现执行。
- Provider 只声明 capability offer 与资源支持，不定义 Syvert 的公共能力词汇、任务 schema 或产品工作流。
- 新能力必须通过 formal spec / contract test / 双参考或等价真实证据进入，不从单个目标系统或单个产品形态直接外推。
- 读操作优先于写操作；写操作必须先有安全门禁、幂等、审计与失败恢复边界。
- 批量、定时、dataset sink 属于运行时编排与结果治理能力，不等同于自动运营产品。
- 新增资源抽象必须来自实际 Adapter capability requirement 证据，不提前设计大全资源模型。

## Runtime Capability 判定标准

一个候选能力进入 Syvert runtime capability contract 前，至少应满足以下判断：

- 可以跨多个目标系统以相近语义表达。
- 属于任务运行时或结果治理，而不是上层产品工作流。
- 需要 Core 统一处理 admission、资源注入、执行控制、审计、错误分类或结果 envelope。
- 平台差异可以由 Adapter 归一化，不要求 Core 理解平台私有字段。
- 实际执行可以由不同 provider 实现，而不改变公共任务契约。

不满足这些条件的能力应留在 Adapter 私有层或上层应用仓库。

## 能力流与依赖

`v1.x` 由多个能力流组成。能力流可以并行研究，但进入实现时必须满足依赖顺序。

| 能力流 | 主要问题 | 关键依赖 |
|---|---|---|
| Operation taxonomy | 新公共能力如何命名、投影、声明和测试 | `v1.0.0` Core / Adapter contract |
| Resource governance | 账号、凭据、会话健康与资源证据如何被治理 | Operation taxonomy |
| Read-side capabilities | 搜索、列表、评论、创作者信息、媒体获取如何统一承载 | Operation taxonomy、Resource governance |
| Batch / dataset | 一组 target、部分成功、结果沉淀和重放如何表达 | Read-side capabilities |
| Scheduled execution | 延迟 / 周期触发如何复用 Core 主路径 | Batch / dataset、TaskRecord 稳定性 |
| Write-side capabilities | 上传、发布等写操作如何安全执行 | Resource governance、Scheduled execution、Safety gate |
| Ecosystem boundary | 外部 Adapter / Provider 如何独立接入与验证 | 上述能力的 contract test 与 evidence |
| Stabilization | 何时可以宣布扩展能力契约稳定 | 全部关键能力流的成熟度 gate |

任何能力流进入执行前，都必须通过 GitHub Phase / FR / Work Item 与正式规约流程确认。路线图只定义方向和依赖，不直接创建 backlog truth。

## Phase 1 Operation Taxonomy

### 目标

建立 `v1.x` 新 runtime capability 的命名、分层与准入机制。

这是 `v1.x` 的首要前置工作。没有公共 operation taxonomy，后续搜索、评论、发布、批量或 dataset 都会退化为 Adapter 私有接口集合。

### 进入条件

- `v1.0.0` 已冻结 Core / Adapter / Provider 兼容性基础。
- `content_detail_by_url` 仍作为回归基线可稳定执行。
- 新能力候选已经证明不是单个平台私有操作。

### 必须具备

- operation / adapter-facing capability family 的扩展规则
- target type 与 collection / execution mode 的扩展规则
- public operation 到 Adapter capability 的投影规则
- 新 capability 的 formal spec 模板与 contract test 准入规则
- 新 capability 不得污染既有 `content_detail_by_url` 基线的回归规则
- capability lifecycle：`proposed`、`experimental`、`stable`、`deprecated`
- operation 命名冲突、语义重叠与向后兼容处理规则
- Adapter declaration 与 Provider offer 对新增 capability 的扩展规则

### 候选能力族

- `content_detail`
- `content_search`
- `content_list`
- `comment_collection`
- `creator_profile`
- `media_asset_fetch`
- `media_upload`
- `content_publish`
- `batch_execution`
- `scheduled_execution`
- `dataset_sink`

### 验证要求

- 假适配器覆盖所有新增 capability contract 的 happy path 与 fail-closed path。
- 至少两个真实或等价参考适配器证明公共语义不是单点外推。
- 平台泄漏检查覆盖新增 operation / target / mode。
- Adapter / Provider compatibility decision 对新增 capability 可以表达 `matched`、`unmatched`、`invalid_contract`。

### 退出条件

- 新 capability 准入规则稳定。
- 所有后续能力流可以复用同一套声明、验证和兼容性判断机制。
- `content_detail_by_url` 基线没有被新 taxonomy 改写。

### 明确不在范围内

- 上层应用 workflow
- 平台私有业务对象直接进入 Core
- provider selector / fallback / marketplace

## Phase 2 Resource Governance

### 目标

把 `account` / `proxy` 的最小资源生命周期推进到更可治理的资源前提模型，同时保持 Core 不理解平台私有账号字段。

这个阶段解决“能力执行需要什么资源前提，以及资源状态如何影响任务执行”的问题。它不是账号矩阵产品。

### 进入条件

- Operation taxonomy 可以表达新增 capability 的资源需求上下文。
- 现有 `account` / `proxy` 资源生命周期仍可回归通过。
- 至少一个真实 Adapter capability 暴露出凭据 / 会话健康不足以用当前 opaque material 表达。

### 必须具备

- credential material 的通用边界
- session / credential health 的通用状态与证据
- resource lease 与 task trace 的增强观测
- Adapter capability requirement 对资源 profile 的更细粒度声明
- 账号凭据失效、资源不满足与 provider 不可用之间的错误边界
- credential material 的敏感字段最小暴露规则
- resource profile 与 provider offer 的资源支持对齐规则
- health check 的触发、证据、状态变更与 task admission 关系
- resource invalidation 与 lease release 的一致语义
- 资源状态与 retry / concurrency / timeout 的交互边界

### 候选模型

- `CredentialMaterial`
- `SessionHealth`
- `ResourceHealthEvidence`
- `ResourceProfileRequirement`
- `CredentialRefreshExpectation`
- `ResourceInvalidationReason`

### 验证要求

- 凭据失效必须映射为稳定错误分类，不暴露 raw secret。
- 合法资源不足与非法资源声明必须能区分。
- Adapter 不得绕过 Core resource lease 自行来源化共享资源。
- Provider offer 不得把资源池、账号池或平台私有轮换策略泄漏给 Core。

### 退出条件

- 读侧和写侧 capability 都可以声明所需资源 profile。
- 资源健康影响任务 admission / execution / release 的边界明确。
- 上层应用可以消费资源状态，但不能反向写入 Core 私有 truth。

### 明确不在范围内

- 账号矩阵 UI
- 用户运营分组
- 平台账号画像产品模型
- 平台私有风控策略进入 Core

## Phase 3 Read-Side Capabilities

### 目标

在稳定详情采集能力之后，扩展读侧公共 operation，使 Syvert 能承载搜索、列表、评论、创作者公开信息与媒体资产获取等可治理任务。

读侧能力是 `v1.x` 中风险较低、最适合扩展公共契约的方向。它应先证明“多结果、分页、游标、部分失败、normalized item”这些运行时语义。

### 进入条件

- Operation taxonomy 已定义新增读侧 capability family。
- Resource governance 可以表达读侧能力所需账号 / 代理 / 会话前提。
- 至少两个目标系统或等价参考样本具备相近读侧语义。

### 候选 operation

- `content_search_by_keyword`
- `content_list_by_creator`
- `comment_list_by_content`
- `creator_profile_by_id`
- `media_asset_fetch_by_ref`

### 分层要求

- Core 只理解 target、policy、resource、execution control、result envelope。
- Adapter 负责平台查询参数、排序、筛选、分页字段与 normalized item。
- Provider 负责实际 HTTP、浏览器、第三方服务或签名执行路径。
- 上层应用负责选题、筛选策略、内容库或分析 UI。

### 必须具备

- 分页 / cursor / partial result 的公共语义
- raw payload 与 normalized result 的双轨输出
- 重试、超时、并发与资源租约行为保持统一
- 结果项去重键、来源追溯与审计字段
- 参考适配器或等价真实证据验证
- 空结果、平台限流、目标不存在、权限不足与解析失败的错误边界
- 多 item normalized result 的最小字段集合与扩展字段规则
- cursor continuation 与 task record / result query 的一致语义

### 验证要求

- 搜索 / 列表类 operation 至少覆盖第一页、下一页、空结果、平台失败。
- 评论类 operation 至少覆盖分页、回复层级、删除 / 不可见评论。
- 媒体资产获取必须保留来源 ref、content type、下载 / 不下载边界。
- 所有结果继续保留 raw 与 normalized。

### 退出条件

- 至少一组读侧 capability 达到 `stable`。
- batch / dataset 阶段可以消费读侧 item result。
- 新能力没有引入平台特定 Core 分支。

### 明确不在范围内

- 内容库产品
- 数据分析产品
- 选题策略或运营策略

## Phase 4 Batch And Dataset

### 目标

让 Core 能承载一组 target 的受控执行，并把结果沉淀为统一 dataset record，而不是把批量采集逻辑留给每个上层应用重复实现。

这个阶段关注运行时和结果治理，不关注产品形态。批量执行不是采集工具，dataset sink 不是内容库。

### 进入条件

- 至少一个读侧 capability 已稳定到可作为 batch item operation。
- TaskRecord 与 result envelope 可以安全表达 item-level outcome。
- 资源治理已能处理 batch 中的资源租约、释放与失败状态。

### 必须具备

- batch request / target set contract
- partial success / partial failure 语义
- item-level result envelope
- dataset record / dataset sink 最小模型
- 去重键、游标、resume token 与失败重放边界
- batch 级与 item 级审计追踪

### 设计要求

- batch 本身是 Core 任务，item outcome 仍复用单任务 envelope 语义。
- partial failure 不得吞掉 item 级错误。
- dataset record 必须保留 source operation、adapter key、target ref、raw ref、normalized payload 与 evidence ref。
- dataset sink 可以是本地 store、文件或外部 sink，但 sink contract 不得绑定产品数据库 schema。
- resume token 只能恢复运行时位置，不代表上层业务策略。

### 验证要求

- 覆盖全部成功、部分成功、全部失败、重复 target、resume、cancel / timeout 边界。
- dataset record 可被独立回读和审计。
- batch 执行不得绕过资源生命周期。

### 退出条件

- 上层应用可以基于 dataset sink 构建内容库或分析产品，但 Syvert 不内置这些产品。
- Scheduled execution 可以调度 batch 或单任务，且仍走 Core 主路径。

### 明确不在范围内

- 内容数据库产品
- BI / 报表 / 监控看板
- 上层采集任务配置 UI

## Phase 5 Scheduled Execution

### 目标

为延迟执行、周期触发与后台运行建立底座契约，但不实现上层自动运营 workflow。

这个阶段只回答“任务何时被 Core 执行，以及错过、重试、并发如何治理”。它不回答“业务上为什么每天执行什么策略”。

### 进入条件

- TaskRecord、资源租约、批量结果与 dataset sink 对后台执行可回放。
- 至少一个单任务或 batch operation 可以作为 schedule target。
- 执行控制策略已经覆盖 timeout / retry / concurrency。

### 必须具备

- scheduled task admission
- durable schedule record
- due task claiming / execution semantics
- missed run / coalescing / retry policy
- scheduler observability
- CLI / API 与 Core 主路径一致性

### 设计要求

- schedule record 只表达触发时间、触发规则、目标任务请求与执行策略。
- due task claiming 必须防止多 worker 重复执行同一触发。
- missed run 必须有明确策略：skip、coalesce 或 catch-up。
- schedule execution 的结果仍写入 TaskRecord / dataset / resource trace。
- 周期任务不得内置业务 workflow DSL。

### 验证要求

- 覆盖单次延迟、周期触发、错过触发、重复 claiming、执行失败、重试耗尽。
- CLI / HTTP / scheduler 三个入口的 Core path 一致。
- scheduler 停止和恢复不会破坏任务 truth。

### 退出条件

- 上层应用可以用 schedule contract 构建自动化产品，但 Syvert 不内置自动运营策略。
- 写侧 capability 可以复用 schedule 与 safety gate，而不是自建定时发布逻辑。

### 明确不在范围内

- 自动运营策略
- 多步骤业务 workflow DSL
- 产品级任务编排 UI

## Phase 6 Write-Side Capabilities

### 目标

在资源治理、读侧能力、批量与调度边界稳定之后，引入写操作 runtime capability，例如媒体上传与内容发布。

写操作是 `v1.x` 中风险最高的能力流，必须晚于资源治理、执行控制和审计能力。写操作不能以“能调用平台 API”为完成标准。

### 进入条件

- Resource governance 已能表达写操作凭据、权限与健康前提。
- Scheduled execution 与 TaskRecord 能表达 unknown outcome、retry exhausted 与人工恢复。
- Operation taxonomy 已定义写侧 capability 的 safety level。

### 候选 operation

- `media_upload`
- `content_publish`
- `content_publish_status`
- `content_publish_cancel`

### 必须具备

- write operation safety gate
- idempotency key
- dry-run / validate-only 语义
- human approval 或 policy approval 的公共边界
- media asset bundle contract
- platform publish ref 与 publish result contract
- retry / cancel / already-submitted / unknown-outcome 错误分类
- 写操作审计与不可逆动作风险记录

### 安全要求

- 默认 fail-closed。
- 每个写操作必须有 idempotency key 或明确说明不可幂等。
- 每个不可逆动作必须记录 approval evidence。
- dry-run / validate-only 不得产生平台侧写入。
- unknown outcome 必须作为一等状态处理，不能被宽松视为成功或失败。
- Adapter 必须把 provider 错误映射到共享错误模型。

### 验证要求

- 覆盖 dry-run、approval missing、重复提交、平台已提交但回包失败、取消失败、状态查询不一致。
- 写操作必须产生可审计 result envelope 与 resource trace。
- provider offer 必须声明支持的写侧 profile，且 compatibility decision 可 fail-closed。

### 退出条件

- 至少一个写侧 capability 达到 experimental，并通过真实 Adapter / Provider evidence。
- 写侧能力没有引入上层发布中心、内容工作台或运营策略。

### 明确不在范围内

- 发布中心 UI
- 内容创作工作台
- 平台运营策略
- 未经安全门禁的自动写入

## Phase 7 Ecosystem Boundary

### 目标

在扩展 runtime capability 后，稳定 Adapter / Provider 独立仓库、SDK 版本、contract test 与 compatibility evidence 的生态边界。

这个阶段把 `v1.x` 新增能力的接入路径稳定下来，避免能力扩展只能依赖主仓参考适配器。

### 进入条件

- 至少一组读侧能力、一组资源治理扩展、一组 batch / dataset 能力和一个写侧实验能力有 contract test。
- Adapter / Provider compatibility decision 能覆盖新增能力。
- SDK 表面对新增能力没有明显破坏性漂移。

### 必须具备

- Adapter 独立仓库接入规则
- Provider offer fixture 与 compatibility evidence 扩展规则
- SDK 版本兼容策略
- contract test host 稳定化
- reference adapter 与 external adapter 的验证职责边界

### 验证要求

- 第三方 Adapter 可以只依赖 SDK、contract test 与文档完成新增 capability 声明。
- 外部 provider offer 可以被 validator 判定为 matched / unmatched / invalid_contract。
- Core registry、TaskRecord、resource lifecycle 仍不出现 provider selector、provider priority 或 product whitelist。

### 退出条件

- 新增 capability 的生态接入路径不依赖主仓私有知识。
- 参考适配器从“唯一实现来源”退回“边界验证样本”。
- `v2.0.0` gate 可以被客观检查。

### 明确不在范围内

- Core provider marketplace
- 全局 provider selector
- provider 产品白名单
- provider 覆盖所有 capability 的承诺

## Stabilization Gate

### 目标

判断是否可以从 `v1.x` 进入 `v2.0.0`。

### 必须同时满足

- Operation taxonomy 已稳定，新增 capability 的准入流程不再依赖临时例外。
- Resource governance 能支持读侧、批量、定时与写侧能力。
- 至少一组读侧 capability 达到 stable。
- Batch / dataset contract 达到 stable，且可以承载读侧 item result。
- Scheduled execution 至少达到 experimental，并证明不绕过 Core 主路径。
- 至少一个写侧 capability 达到 experimental，并通过安全门禁、幂等与 unknown outcome 验证。
- Adapter / Provider compatibility decision 覆盖新增能力。
- 平台泄漏检查、契约测试、双参考或等价真实证据持续通过。
- 上层应用仍独立于 Syvert 主仓。

### 不满足时的处理

- 如果只有部分能力稳定，继续发布 `v1.x` minor，不进入 `v2.0.0`。
- 如果写侧能力尚未成熟，可以继续停留在 `v1.x`，不为了版本号推进牺牲安全门禁。
- 如果某个能力被证明是 Adapter 私有语义，应从 Core roadmap 退出，转入 Adapter 私有文档或上层应用仓库。

## v2.0.0

### 目标

宣布 Syvert 的扩展 runtime capability contract 稳定。

### v2.0.0 的要求

- `v1.x` 新增公共 operation 的 contract 已通过 formal spec 与 contract test 稳定。
- 读侧能力、资源治理、批量 / dataset、定时执行、写侧安全契约之间的边界可被一致解释。
- Adapter / Provider compatibility decision 可以覆盖新增能力。
- Core 主路径仍不包含平台特定分支。
- 上层应用仍通过独立仓库消费 Syvert，不进入 Core / Adapter SDK 职责边界。

### v2.0.0 不代表什么

它不代表：

- Syvert 变成上层应用产品。
- Syvert 主仓内置账号矩阵、内容库、发布中心或自动运营产品。
- 每个目标系统都支持所有新增 operation。
- 每个 provider 都覆盖所有 Adapter capability。
- Core 具备全局 provider selector、marketplace 或产品白名单。

它代表：

- Syvert 在稳定 Core 之上，已经具备扩展多类互联网操作能力的稳定底座契约。

## 总结

`v0.x -> v1.0.0` 证明 Core 值得依赖。

`v1.x -> v2.0.0` 证明 Syvert 可以在不变成上层应用、不绑定具体目标系统、不承诺 provider 产品白名单的前提下，持续扩展可治理的 runtime capability。
