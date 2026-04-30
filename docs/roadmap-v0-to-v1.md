# Syvert 路线图 v0.1.0 到 v1.0.0

## 目的

这份路线图定义了 Syvert 从第一个可运行的 Core 里程碑到稳定 `v1.0.0` 的预期演进路径。

它基于当前的方向决策：

- Syvert 是一个承载互联网操作任务与资源的 Core 框架，而不是围绕单一采集切片堆叠实现的仓库。
- 真实验证应来自少量参考适配器。
- 前两个参考适配器已固定：
  - 小红书
  - 抖音


## 跨版本产品目标

早期版本的目的不是最大化功能。

它的目的在于证明一件事：

**Syvert Core 能否在一个稳定的运行时契约下承载多个真实适配器，而不会把 Core 变成目标系统特定代码？**

`v0.x` 中的一切都应该服务于这个问题。

当前以 `content_detail_by_url` 与双参考适配器作为验证切片，只是为了先压实 Core 边界；这不应被误读为 Syvert 的长期定位只服务内容采集。


## 版本策略

- `v0.1.0`：跑通最小 Core
- `v0.2.0`：把“能跑”变成“可验证”
- `v0.3.0` 到 `v0.6.0`：补齐运行时闭环（先闭环再暴露服务面）
- `v0.7.0`：仓内拆出 adapter-owned provider port，稳定适配器表面
- `v0.8.0`：清理边界，稳定第三方 Adapter 接入路径与 Adapter / Provider 兼容性判断模型
- `v0.9.0`：在真实外部 provider 验证样本上压测兼容性判断，并完成 SDK / 文档稳定化
- `v1.0.0`：宣布 Core 稳定
- `v1.x`：在稳定契约之后产品化扩展 provider 接入、更多能力与 adapter 仓库边界

## 跨版本强制 gate（自 v0.2.0 起）

从 `v0.2.0` 开始，每个版本在进入下一版本前都必须通过：

- 假适配器契约测试（验证 Core 契约语义）
- 双参考适配器回归（小红书 + 抖音）
- 平台泄漏检查（Core 主路径不得引入平台特定分支）

这些 gate 是持续门禁，不是 `v0.9.0` 的一次性清债动作。

自 `v0.8.0` 起，开放接入稳定化还必须额外满足：

- 第三方 Adapter 接入路径可被文档、SDK 表面与 contract test 一致解释。
- Adapter + Provider 不以“某个 provider 覆盖所有能力”为前提，而以 `Adapter capability requirement x Provider capability offer -> compatibility decision` 判断绑定合法性。
- 至少一个真实外部 provider 验证样本必须在 `v1.0.0` 前证明兼容性判断链路可执行；该样本不构成指定 provider 产品的正式支持承诺。


## v0.1.0

### 目标

创建第一个可运行的 Core。

### 必须具备

- 本地单进程运行时
- CLI 入口
- 最小任务模型
- 最小适配器接口
- 最小执行引擎
- 标准化任务输入
- 标准化任务输出
- `raw + normalized` 适配器结果契约

### 范围

以下范围只定义 `v0.1.0` 的当前验证切片，不定义 Syvert 的长期能力上限。

只支持一个能力：

- `content_detail_by_url`

只支持同步、进程内执行：

- 提交
- 执行
- 返回结果

### 明确不在范围内

- HTTP API
- 多租户支持
- 后台队列
- 重试
- 取消
- 浏览器资源提供方
- 高级资源调度器
- 通用搜索/评论/创作者能力

### 成功标准

- 同一个 Core 可以运行：
  - 小红书适配器
  - 抖音适配器
- 两个适配器都遵循同一契约
- Core 的主执行路径不需要平台特定分支


## v0.2.0

### 目标

把可运行的 Core 变成一个可验证的契约驱动 Core。

### 必须具备

- `InputTarget` 模型
- `CollectionPolicy` 模型
- 标准化错误模型
- 适配器注册表
- 适配器契约测试
- 用于测试 Core 行为的假适配器
- 适配器验证工具
- 参考适配器测试框架
- 双参考适配器回归 gate
- 平台泄漏检查 gate

### 明确不在范围内

- 完整的资源管理 UI/API
- 浏览器资源实现
- 多租户隔离
- 分布式执行

### 成功标准

- 适配器能力可被发现
- 错误分类保持一致
- Core 测试可以在不执行真实平台的情况下验证契约
- 小红书与抖音回归验证进入每版本固定流程


## v0.3.0

### 目标

建立最小任务与结果持久化闭环。

### 必须具备

- 任务状态模型
- 任务结果持久化
- 执行日志模型
- 共享任务/结果序列化
- CLI 查询任务状态与结果的能力
- CLI 仍走同一条 Core 执行路径

### 明确不在范围内

- HTTP API
- 生产级认证模型
- 分布式工作队列
- 高级任务控制
- 丰富查询层

### 成功标准

- 任务在执行完成后仍可查询
- 任务状态、结果与日志语义保持一致
- 持久化没有绕过 Core 内部机制


## v0.4.0

### 目标

建立最小资源系统。

### 必须具备

- 账号资源模型
- 代理资源模型
- 资源获取接口
- 资源释放接口
- 资源状态跟踪
- 资源使用日志
- 最小资源状态集合：
  - `AVAILABLE`
  - `IN_USE`
  - `INVALID`

### 明确不在范围内

- 完整资源控制台
- 高级健康恢复循环
- 浏览器资源管理
- 跨租户策略复杂性

### 成功标准

- 适配器不会自行来源化执行资源
- Core 可以向适配器执行注入资源包
- 资源使用可以按任务追踪


## v0.5.0

### 目标

在真实参考适配器压力下收敛资源能力抽象。

### 必须具备

- 适配器资源需求声明
- Core 对资源能力匹配的支持
- 资源能力抽象的证据记录（来自小红书/抖音实际运行差异）

### 重要约束

这个版本可以收敛抽象，但不能凭空扩展抽象。

- 只有当两个参考适配器都暴露出同类资源语义时，才引入对应抽象
- 不应硬编码具体技术实现（例如 Playwright、CDP、Chromium）
- 若证据不足，优先保持最小资源模型而不是提前设计“大全抽象”

### 成功标准

- 资源能力匹配可在不绑定具体实现技术的前提下完成
- 新增抽象都能被双参考适配器场景验证到


## v0.6.0

### 目标

让系统具备最小可运维性，并在闭环后暴露第一个外部服务面。

### 必须具备

- 超时控制
- 基础重试策略
- 并发限制
- 失败分类
- 结构化日志
- 最小执行指标
- HTTP API
- 任务提交端点
- 任务状态端点
- 任务结果端点
- CLI 和 API 使用相同的执行路径

### 明确不在范围内

- 生产级认证模型
- 完整分布式调度
- 复杂策略 DSL

### 成功标准

- 失败是可见且可分类的
- 任务可以按预期失败，而不是静默崩溃
- 运维人员可以检查执行期间发生了什么
- API 不绕过 Core 内部机制
- API 与 CLI 的任务语义保持一致


## v0.7.0

### 目标

稳定适配器表面，并在仓内拆清 Adapter 与 provider-like 执行逻辑的边界。

`v0.7.0` 的边界目标是：

```text
Syvert Adapter
  -> Syvert-owned Provider Port
      -> Native Provider
```

当前小红书、抖音 adapter 内部的 HTTP/sign/browser bridge 属于 native provider 实现细节。`v0.7.0` 只把这个边界拆清并稳定下来，不把 WebEnvoy、OpenCLI、bb-browser 或其他外部 provider 纳入交付范围。

### 必须具备

- SDK 版本标识
- 适配器兼容性声明
- 适配器能力元数据
- adapter-owned provider port 边界
- 当前 native provider 拆分约束
- 稳定化文档与迁移约束

### 明确不在范围内

- 外部 provider 接入
- 新增小红书/抖音采集、发布、通知、互动等业务能力
- Core 级 provider registry、provider selector 或跨 provider fallback 策略
- adapter 独立仓库拆分

### 成功标准

- 第三方适配器作者可以面向稳定契约开发
- Core 继续只调用 Adapter，不感知 provider 实现、外部工具或 provider 选择策略
- 小红书、抖音当前已批准 `content_detail_by_url` 验证切片保持兼容
- Core 的变更不再轻易破坏适配器


## v0.8.0

### 目标

清理系统边界并收敛可演进约束，同时把开放接入路径从“能本地加载 Adapter”推进到“第三方 Adapter 与 Adapter + Provider 兼容性可以被稳定判断”。

### 必须具备

- Core / Adapter 责任边界回归检查
- 关键状态语义一致性检查
- 非兼容变更策略与弃用策略
- 参考适配器升级指引
- 第三方 Adapter 接入路径说明与 contract test 进入条件
- Adapter capability requirement 声明
- Provider capability offer 声明
- Adapter / Provider compatibility decision 模型
- 不兼容、缺能力、版本不匹配与资源前提不满足时的 fail-closed 语义
- provider 字段不得进入 Core routing、TaskRecord、resource lifecycle 或 registry discovery 的边界检查

### 明确不在范围内

- 指定外部 provider 产品的正式支持
- 多 provider 自动选择、排序、fallback 或打分策略
- Core provider registry、provider marketplace 或 provider 产品白名单
- 多租户身份模型
- 最小认证模型
- RBAC 与组织层级能力

### 成功标准

- Core 边界在文档和实现上都可被一致解释
- 适配器升级路径可预测且可验证
- 社区接入的默认入口被明确为 Adapter；provider 只能作为 Adapter-bound 执行能力参与兼容性判断
- 后续真实 provider 验证样本可以在不改写 Core / Adapter 主契约的前提下进入 `v0.9.0`


## v0.9.0

### 目标

为 Core 稳定化做准备，并用真实 provider 验证样本检验 `v0.8.0` 冻结的兼容性判断模型。

### 必须具备

- 契约清理
- 错误码清理
- 文档重建
- SDK 清理
- 借助两个参考适配器进行更强的端到端验证与稳定性回归
- 至少一个真实外部 provider 验证样本
- 至少覆盖一个已批准 Adapter capability 的端到端兼容性 evidence
- provider 错误、资源、生命周期与观测证据在真实执行边界中的验证
- 明确真实 provider 验证样本不等于指定 provider 产品正式支持

### 成功标准

- Core 与适配器职责之间不再存在重大歧义
- 两个参考适配器不再需要 Core 中的特殊处理支持
- Adapter / Provider compatibility decision 在真实 provider 样本中可执行、可审计、可失败关闭
- `v1.0.0` 前的开放接入证据不依赖纸面 contract 或仓内 native provider 自证


## v1.0.0

### 目标

宣布 Syvert Core 稳定。

### v1.0.0 的要求

- Core 边界稳定
- 适配器契约稳定
- 任务模型稳定
- 资源模型稳定
- API 和 CLI 共享同一运行时路径
- 两个参考适配器运行在稳定的 Core 契约之下
- 新适配器拥有受限且有文档说明的接入路径
- 第三方 Adapter 可以通过稳定 SDK 表面、contract test 与 registry 校验接入
- Adapter / Provider 兼容性判断链路稳定，且已有真实 provider 验证样本作为 evidence
- Core 不承担 provider selector、fallback、routing 或指定 provider 产品适配职责

### v1.0.0 不代表什么

它不代表：

- 每个平台都已支持
- 每项能力都已实现
- 每种资源类型都有提供方
- OpenCLI、bb-browser、agent-browser 或任何指定 provider 产品已被正式支持
- 某一个 provider 可以覆盖所有 Adapter capability
- 已具备 provider marketplace、自动 provider selector 或跨 provider fallback 策略

它代表：

- Core 已经足够稳定，可以承载一个生态


## v1.x

### 目标

在 `v1.0.0` 稳定契约之后扩展生态接入，而不是把指定 provider 产品支持写成 Core 稳定化主线目标。

### 候选方向

- 基于 `v1.0.0` 已稳定的兼容性判断，产品化接入具体外部 provider
- 为小红书、抖音新增搜索结果采集、评论采集、账号信息、发布、通知、浏览/点赞/收藏/评论等能力
- 评估 adapter 是否从主仓拆出独立仓库
- 扩展 provider SDK、compatibility matrix、selector / fallback 策略；这些都必须通过独立 FR 批准

### 成功标准

- 新 provider 接入不改变 `v1.0.0` 已冻结的 Core / Adapter contract
- 新能力通过独立 FR 批准，不反向污染 `content_detail_by_url` 基线
- adapter 仓库边界只在主仓 contract 稳定后调整
- 任一 provider 产品的正式支持都绑定到明确的 Adapter capability、compatibility decision 与 evidence，而不是成为全局支持承诺


## 所有 v0.x 版本的开发规则

当真实适配器暴露出弱点时，响应应当是：

- 先判断这是否是 Core 契约问题，
- 再修改 Core，
- 除非抽象真的需要，否则不要把平台特定设计引入 Core。

这条规则至关重要。

如果没有它，参考适配器就会停止验证框架，而开始把它塑造成平台特定软件。

## 延后方向（v1.x 候选）

以下方向保留为 `v1.x` 候选，不作为 `v0.x -> v1.0.0` 主路径承诺：

- 多租户边界模型
- 最小认证模型
- 企业级 RBAC / 组织层级语义
- 尚未被双参考适配器真实压力验证的高级资源抽象
- 指定 provider 产品的官方支持清单与 provider marketplace


## 总结

这份路线图最简短的描述是：

- `v0.1.0` 证明 Core 能运行
- `v0.2.0` 证明 Core 可被持续验证
- `v0.6.0` 证明 Core 既能运维也能通过服务面被使用
- `v0.8.0` 到 `v0.9.0` 证明开放接入路径与 Provider 兼容性判断可被验证
- `v1.0.0` 证明 Core 值得依赖
