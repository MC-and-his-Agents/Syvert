# Syvert Adapter SDK

## 目标

本文件定义 Syvert Adapter SDK 的职责、最小接口和实现约束。

Adapter SDK 的目标是：

- 让平台接入变成标准化工作
- 让 Core 与平台实现彻底解耦
- 让适配器开发者只关注平台逻辑
- 让任务、资源和数据治理由 Core 统一负责


## 适配器的职责

适配器只负责平台接入，不负责系统治理。

适配器负责：

- 将标准任务输入转换为平台请求
- 使用 Core 提供的资源上下文执行请求
- 处理平台响应
- 返回原始结果与标准化结果
- 将平台特定错误映射为标准错误

适配器不负责：

- 创建任务
- 推进任务状态
- 管理资源生命周期
- 直接写数据库
- 直接暴露 HTTP API
- 决定租户隔离规则


## 设计原则

- 单一职责：适配器只做平台接入
- 显式契约：输入、输出、错误必须结构化
- 资源注入：适配器只能消费 Core 提供的资源，不自己找资源
- 无副作用落盘：适配器不直接持久化共享内容数据
- 可测试：每个适配器都必须支持独立测试

## v0.7.0 兼容性基线

`v0.7.0` 稳定的是 Core-facing Adapter contract，而不是外部 provider contract。当前主干的最小运行时表面为：

- `adapter_key`
- `supported_capabilities`
- `supported_targets`
- `supported_collection_modes`
- `resource_requirement_declarations`
- `execute(request: AdapterExecutionContext) -> dict`

当前 approved capability metadata 仍只覆盖双参考验证切片：

- public operation：`content_detail_by_url`
- adapter-facing capability family：`content_detail`
- target type：`url`
- collection mode：`hybrid`
- reference adapters：`xhs`、`douyin`
- required resource capabilities：`account`、`proxy`
- success payload：`{"raw": ..., "normalized": ...}`

`content_detail_by_url` 是 Core/public operation id；进入 Adapter 前继续投影为 `content_detail` capability family。Adapter 作者不得把 `content_detail_by_url`、`xsec_token`、`verify_fp`、`ms_token`、browser page state、sign service 或 provider key 写入 `supported_capabilities` / `resource_requirement_declarations`。

## Adapter-Owned Provider Port

`FR-0021` 批准的 provider port 是 adapter-owned 内部执行边界：

```text
Core Runtime
  -> Adapter.execute(AdapterExecutionContext)
      -> Adapter-owned Provider Port
          -> Native Provider
      -> Adapter normalizer
```

该边界只允许 Adapter 把已验证 URL、已解析 target、已消费 resource bundle 后得到的平台 session config 与 legacy transport hooks 交给 native provider。Native provider 返回 raw platform payload 与 platform detail object；normalized result 仍由 Adapter 生成。

该边界明确不提供：

- 外部 provider SDK
- provider plugin registration
- Core provider registry
- provider selector
- provider fallback priority
- provider resource supply model

`provider=` constructor seam 只允许作为仓内测试/本地注入 seam；它不能被声明为第三方 provider 接入能力，也不能替代现有 `sign_transport`、`detail_transport`、`page_transport`、`page_state_transport` 等 legacy transport hooks。

## v1.0 前开放接入目标

`v1.0.0` 前，Adapter SDK 需要把两类接入路径解释清楚：

- Adapter-only：第三方直接实现 Syvert Adapter，承担目标系统语义、输入校验、资源需求、错误映射与 `raw + normalized` 输出责任。
- Adapter + Provider：Adapter 仍是 Syvert 接入入口，provider 只作为 Adapter 内部可替换执行能力，通过兼容性判断后被绑定。

Provider 产品若已经封装目标系统语义，可以选择构建 Adapter；若只提供浏览器、远程执行、CLI、agent 或其他通用执行能力，则应通过 Adapter-bound provider offer 接入。Syvert 不把 provider 直接接入 Core，也不要求某一个 provider 覆盖所有 Adapter capability。

`v1.0.0` 前需要冻结的最小判断模型是：

```text
Adapter capability requirement
  x Provider capability offer
  -> compatibility decision
```

该判断至少需要能表达：

- Adapter 需要的执行能力、资源前提、错误证据、生命周期与观测要求
- Provider 提供的执行能力、资源消费方式、错误 carrier、版本与 evidence 能力
- 不兼容、缺能力、版本不匹配或资源前提不满足时的 fail-closed 原因

该模型不代表：

- 指定 provider 产品获得正式支持
- Core 可以发现、选择或排序 provider
- provider 可以绕过 Adapter 生成 Syvert normalized result
- provider 可以绕过 Core 注入资源包自行获取账号、代理或会话资源


## 最小能力面

一个适配器最少必须声明：

- `adapter_key`
- `supported_capabilities`
- `supported_targets`
- `supported_collection_modes`
- `resource_requirement_declarations`

其中：

- `supported_capabilities` 表示它支持哪些任务类型
- `supported_targets` 表示它支持哪些输入目标
- `supported_collection_modes` 表示它支持哪些采集模式
- `resource_requirement_declarations` 表示 Core 进入该 capability 前必须注入哪些共享资源能力


## 核心接口

以下接口是建议的最小 SDK 形态。

```python
from __future__ import annotations

from typing import Any, Protocol

from syvert.runtime import AdapterExecutionContext


class PlatformAdapter(Protocol):
    adapter_key: str
    supported_capabilities: frozenset[str]
    supported_targets: frozenset[str]
    supported_collection_modes: frozenset[str]
    resource_requirement_declarations: tuple[object, ...]

    def execute(self, request: AdapterExecutionContext) -> dict[str, Any]:
        ...
```


## 输入契约

Core 调用适配器时，只应传入一个 `AdapterExecutionContext`。

其中：

- `request` 描述 adapter-facing capability、target type、target value 与 collection mode
- `resource_bundle` 描述 Core 已 acquire 并注入给 Adapter 的资源包
- `task_id`、resource trace 与 failure envelope 由 Core 继续拥有

适配器不得自行推断：

- 当前租户是谁
- 当前任务是谁创建的
- 当前该用哪个资源池

这些信息必须由 Core 显式提供。


## 输出契约

适配器必须返回 `dict` success payload。

输出应至少包含：

- `raw`
- `normalized`

### raw

保存平台原始结果，用于：

- 审计
- 调试
- 回放
- 二次解析

### normalized

返回当前 capability family 的标准化结果。

在 `v0.7.0` 当前 approved slice 中，`normalized` 仍是 `content_detail` 结果对象，至少覆盖 `platform`、`content_id`、`content_type`、`canonical_url`、`title`、`body_text`、`published_at`、`author`、`stats` 与 `media`。


## 错误契约

适配器不能随意抛出底层异常到 Core。

所有平台错误都必须映射成 `PlatformAdapterError`。

错误最少需要提供：

- `code`
- `message`
- `category`
- `details`

这样 Core 才能统一处理：

- 状态推进
- 重试策略
- 失败分类
- 资源状态回写


## 资源契约

资源由 Core 提供，适配器只消费。

当前 `v0.7.0` approved resource capabilities 只有：

- account
- proxy

`cookies`、`user_agent`、`headers`、`xsec_token`、`verify_fp`、`ms_token`、browser page state 与 sign request 参数只能作为 Adapter 从 account material 或站点解析结果中抽取出的内部执行材料。它们不得进入：

- `resource_requirement_declarations`
- Adapter registry discovery
- Core routing metadata
- TaskRecord public envelope
- resource lifecycle state

适配器不可以：

- 自己从数据库查账号
- 自己决定租户隔离
- 自己修改资源所有权
- 自己写资源状态

如果平台执行中发现资源失败，适配器应通过标准错误或诊断信息告诉 Core，由 Core 回写资源状态。


## 生命周期

一个标准适配器调用流程应为：

```text
Core creates task
    -> Core resolves target and policy
    -> Core acquires resource bundle
    -> Core builds AdapterExecutionContext
    -> Adapter.execute()
    -> Adapter returns {"raw": ..., "normalized": ...} or PlatformAdapterError
    -> Core updates task state
    -> Core persists results
    -> Core releases resources
```

适配器只处在中间执行环节。


## 能力声明

适配器必须显式声明自己支持什么。

例如：

```python
from syvert.registry import baseline_required_resource_requirement_declaration


class ExampleAdapter(PlatformAdapter):
    adapter_key = "example"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        baseline_required_resource_requirement_declaration(
            adapter_key=adapter_key,
            capability="content_detail",
        ),
    )
```

Core 可以基于这些声明做：

- 路由
- 参数校验
- 兼容性检查
- 能力发现


## 适配器注册

Core 应支持适配器注册机制。

建议最小接口：

```python
class AdapterRegistry:
    @classmethod
    def from_mapping(cls, adapters: Mapping[str, object]) -> "AdapterRegistry": ...
    def lookup(self, adapter_key: str) -> AdapterDeclaration | None: ...
    def discover_capabilities(self, adapter_key: str) -> frozenset[str] | None: ...
    def discover_targets(self, adapter_key: str) -> frozenset[str] | None: ...
    def discover_collection_modes(self, adapter_key: str) -> frozenset[str] | None: ...
    def discover_resource_requirements(
        self,
        adapter_key: str,
    ) -> tuple[AdapterResourceRequirementDeclaration, ...] | None: ...
```

原则：

- `adapter_key` 是 Core-facing adapter lookup identity
- registry discovery 只返回 Adapter public metadata
- registry 不暴露 provider key、provider priority、native provider 或 provider resource requirement
- 多 adapter / 多 capability 扩展必须先获得新的 formal spec 批准
- provider 兼容性判断不得改写 registry discovery 为 provider selector 或 provider 产品目录


## 版本兼容

Adapter SDK 必须有清晰版本边界。

`v0.7.0` 的兼容性声明：

- Adapter SDK contract id：`syvert-adapter-sdk/v0.7`
- Core runtime compatibility range：`>=0.7,<1.0`
- `#269` native provider 拆分不改变 Core / Adapter runtime contract。
- Adapter public metadata、resource requirement declaration、`execute()` 输入输出、`raw + normalized` success payload 与错误分类保持兼容。
- 小红书、抖音当前 only-approved capability baseline 仍是 `content_detail_by_url -> content_detail`。
- registry / TaskRecord / resource lifecycle 不暴露 provider 字段。
- 任何外部 provider 接入、新业务能力、provider selector 或新资源模型都必须通过后续独立 FR。

第三方 adapter 的最小兼容性声明建议写在 adapter 包文档或 manifest 中；`v0.7.0` 不要求 AdapterRegistry 读取这些字段：

```python
ADAPTER_COMPATIBILITY = {
    "adapter_sdk_contract": "syvert-adapter-sdk/v0.7",
    "core_runtime": ">=0.7,<1.0",
    "adapter_surface": "adapter_key+execute+resource_requirement_declarations",
    "capability_baseline": "content_detail_by_url->content_detail",
    "provider_port": "internal-only",
}
```

通用建议：

- Core 主版本变化可以打破 SDK 契约
- Core 次版本变化应保持 SDK 向后兼容
- 适配器应声明自己兼容的 SDK 版本
- provider offer 只能声明可服务的 Adapter capability 范围，不能声明“支持 Syvert 全部能力”


## 测试要求

每个适配器最少应具备以下测试：

1. capability 声明测试
2. 输入校验测试
3. 成功路径测试
4. 平台错误映射测试
5. 认证资源缺失测试
6. 解析失败测试

可选测试：

- 分页测试
- 限流测试
- 降级测试
- 资源失败测试
- Adapter / Provider compatibility decision 测试
- 真实 provider 验证样本的 evidence 回归测试


## 实现约束

为防止适配器侵入 Core，建议强制以下约束：

- 不直接访问 Core 数据库
- 不直接修改任务状态
- 不直接修改资源状态
- 不直接依赖 Entry Layer
- 不直接返回平台私有异常
- 不把平台专有字段扩散到共享模型中


## v0.7.0 最小迁移说明

第三方 adapter 从旧草案迁移到当前 `v0.7.0` 表面时，至少需要完成：

1. 将 `adapter_id` / `platform_name` 收敛为单一 `adapter_key`。
2. 将 `collect(request, context)` 改为 `execute(request: AdapterExecutionContext) -> dict`。
3. 将 success result 改为 `{"raw": ..., "normalized": ...}`，不要返回旧 `AdapterResult` / `NormalizedEntity` 列表。
4. 将 capability metadata 收敛到已批准 baseline：`supported_capabilities=frozenset({"content_detail"})`、`supported_targets=frozenset({"url"})`、`supported_collection_modes=frozenset({"hybrid"})`。
5. 新增或确认 `resource_requirement_declarations` 只声明 `account` 与 `proxy`，不得写入 cookie、user-agent、headers、provider key、browser provider、sign service 或 fallback priority。
6. 如果 adapter 内部拆出 provider port，只能作为 adapter-owned 内部边界；Core / registry / TaskRecord / resource lifecycle 不得发现或选择 provider。
7. 保留 legacy transport hooks 的测试注入能力；新增 provider test seam 时必须标注为 internal test seam，不得作为外部 provider 接入文档发布。


## 推荐开发流程

接入一个新平台的建议路径：

1. 定义 capability 与 target 支持范围
2. 定义平台原始结果到当前 `normalized` shape 的映射
3. 实现 `execute()`
4. 实现错误映射
5. 补齐适配器测试
6. 注册到 Core
7. 用 API/CLI 跑通任务

如果接入方已有 provider 产品：

1. 若产品已具备目标系统语义，优先包装成 Syvert Adapter。
2. 若产品只提供通用执行能力，先声明 Provider capability offer，再绑定到具体 Adapter capability。
3. 任何 Adapter + Provider 绑定都必须产出 compatibility decision 与 evidence。
4. 不得把 provider 产品名写成全局能力承诺；只能声明它通过验证的 Adapter capability 范围。


## 一句话总结

Adapter SDK 的目标是让平台接入成为一项有边界的工程工作：

适配器只负责平台，
Core 负责系统。
