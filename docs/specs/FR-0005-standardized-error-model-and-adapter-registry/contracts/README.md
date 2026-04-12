# FR-0005 contracts

本目录用于记录 `FR-0005` 的稳定契约入口。

当前 FR 的正式契约结论如下：

- Core 统一承载失败 envelope，`error` 最小字段固定为 `category`、`code`、`message`、`details`
- `category` 的最小集合固定为：
  - `invalid_input`
  - `unsupported`
  - `runtime_contract`
  - `platform`
- `invalid_input` 表示请求形状或语义不合法；即使 adapter 已被成功选中，只要失败仍发生在任何真实平台调用之前，也属于 `invalid_input`
- `unsupported` 表示请求合法，但当前 adapter / capability 集合不满足
- `runtime_contract` 表示 registry、adapter 声明、成功 payload 或 host-side 运行时契约失配，必须 fail-closed
- `platform` 表示 adapter 已进入平台语义边界，但被平台事实或平台资源条件阻断
- adapter 已选中但仍处于真实平台调用前的输入失败，归入 `invalid_input`
- adapter 抛出的未映射宿主异常，归入 `runtime_contract`
- adapter registry 只冻结以下语义职责：
  - materialize 明确的 adapter 绑定集合
  - 以稳定 `adapter_key` 做唯一查找
  - 暴露 capability 声明结果，供 Core 做分发前判断
  - 对歧义注册、无效声明、无效 capability 元数据按 `runtime_contract` fail-closed
- adapter registry 不冻结以下实现细节：
  - 模块扫描、插件市场、import 约定
  - registry 的类结构、方法名、缓存策略或实例化时机
  - fake adapter、harness、validator 或 gate 的目录和运行方式
- capability discovery 的正式约束是 side-effect-free：不得依赖真实平台网络、登录态或浏览器执行
- 与 `FR-0002` 的覆盖关系：
  - `FR-0002` 继续保留 `v0.1.0` 的失败 envelope 顶层结构与历史语义
  - 自 `v0.2.0+` 起，如 `FR-0002` 的历史 contract 入口与本目录对 `error.category` 的闭集或边界描述冲突，应以 `FR-0005` 为权威来源解释
