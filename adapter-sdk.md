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


## 最小能力面

一个适配器最少必须声明：

- `adapter_id`
- `platform_name`
- `supported_capabilities`
- `supported_targets`
- `supported_collection_modes`

其中：

- `supported_capabilities` 表示它支持哪些任务类型
- `supported_targets` 表示它支持哪些输入目标
- `supported_collection_modes` 表示它支持哪些采集模式


## 核心接口

以下接口是建议的最小 SDK 形态。

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class Capability(str, Enum):
    CONTENT_DETAIL = "content_detail"
    CREATOR_DETAIL = "creator_detail"
    SEARCH = "search"
    COMMENTS = "comments"
    FEED = "feed"


class TargetType(str, Enum):
    URL = "url"
    CONTENT_ID = "content_id"
    CREATOR_ID = "creator_id"
    KEYWORD = "keyword"


class CollectionMode(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    HYBRID = "hybrid"


@dataclass(slots=True)
class AdapterRequest:
    task_id: str
    capability: Capability
    target_type: TargetType
    target_value: str
    collection_mode: CollectionMode
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResourceHandle:
    account_id: str | None = None
    proxy_id: str | None = None
    cookie_ref: str | None = None
    user_agent: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AdapterContext:
    client_id: str
    request_id: str
    resource: ResourceHandle | None
    deadline_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AdapterRawResult:
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | str | bytes
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedEntity:
    entity_type: str
    entity_id: str
    data: dict[str, Any]


@dataclass(slots=True)
class AdapterResult:
    raw: AdapterRawResult
    normalized: list[NormalizedEntity]
    diagnostics: dict[str, Any] = field(default_factory=dict)


class AdapterErrorCode(str, Enum):
    AUTH_REQUIRED = "auth_required"
    ACCESS_DENIED = "access_denied"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    TEMPORARY_BLOCK = "temporary_block"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    INVALID_REQUEST = "invalid_request"
    PLATFORM_ERROR = "platform_error"
    PARSE_ERROR = "parse_error"


class AdapterError(Exception):
    def __init__(
        self,
        code: AdapterErrorCode,
        message: str,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}


class PlatformAdapter(ABC):
    adapter_id: str
    platform_name: str
    supported_capabilities: set[Capability]
    supported_targets: set[TargetType]
    supported_collection_modes: set[CollectionMode]

    @abstractmethod
    async def collect(
        self,
        request: AdapterRequest,
        context: AdapterContext,
    ) -> AdapterResult:
        raise NotImplementedError
```


## 输入契约

Core 调用适配器时，只应传入两类对象：

- `AdapterRequest`
- `AdapterContext`

其中：

- `AdapterRequest` 描述任务想做什么
- `AdapterContext` 描述任务运行时可用什么

适配器不得自行推断：

- 当前租户是谁
- 当前任务是谁创建的
- 当前该用哪个资源池

这些信息必须由 Core 显式提供。


## 输出契约

适配器必须返回 `AdapterResult`。

输出应至少包含：

- `raw`
- `normalized`
- `diagnostics`

### raw

保存平台原始结果，用于：

- 审计
- 调试
- 回放
- 二次解析

### normalized

返回标准化实体列表。

这些实体是 Core 后续持久化和查询的基础。

### diagnostics

用于返回执行附加信息，例如：

- 实际使用的模式
- 是否使用认证资源
- 请求次数
- 分页信息
- 平台特定警告


## 错误契约

适配器不能随意抛出底层异常到 Core。

所有平台错误都必须映射成 `AdapterError`。

错误最少需要提供：

- `code`
- `message`
- `retryable`
- `details`

这样 Core 才能统一处理：

- 状态推进
- 重试策略
- 失败分类
- 资源状态回写


## 资源契约

资源由 Core 提供，适配器只消费。

适配器可以依赖：

- account
- cookie
- proxy
- user-agent
- extra headers

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
    -> Core builds AdapterRequest + AdapterContext
    -> Adapter.collect()
    -> Adapter returns AdapterResult or AdapterError
    -> Core updates task state
    -> Core persists results
    -> Core releases resources
```

适配器只处在中间执行环节。


## 能力声明

适配器必须显式声明自己支持什么。

例如：

```python
class ExampleAdapter(PlatformAdapter):
    adapter_id = "example.xhs"
    platform_name = "xhs"
    supported_capabilities = {
        Capability.CONTENT_DETAIL,
        Capability.SEARCH,
        Capability.CREATOR_DETAIL,
    }
    supported_targets = {
        TargetType.URL,
        TargetType.CONTENT_ID,
        TargetType.KEYWORD,
        TargetType.CREATOR_ID,
    }
    supported_collection_modes = {
        CollectionMode.PUBLIC,
        CollectionMode.AUTHENTICATED,
        CollectionMode.HYBRID,
    }
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
    def register(self, adapter: PlatformAdapter) -> None: ...
    def get(self, platform_name: str, capability: Capability) -> PlatformAdapter: ...
    def list(self) -> list[PlatformAdapter]: ...
```

原则：

- 一个适配器可以支持多个 capability
- 一个平台可以存在多个适配器实现
- Core 应允许按策略选择具体适配器


## 版本兼容

Adapter SDK 必须有清晰版本边界。

建议：

- Core 主版本变化可以打破 SDK 契约
- Core 次版本变化应保持 SDK 向后兼容
- 适配器应声明自己兼容的 SDK 版本

例如：

```python
SDK_VERSION = "1.0"
COMPATIBLE_CORE_RANGE = ">=1.0,<2.0"
```


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


## 实现约束

为防止适配器侵入 Core，建议强制以下约束：

- 不直接访问 Core 数据库
- 不直接修改任务状态
- 不直接修改资源状态
- 不直接依赖 Entry Layer
- 不直接返回平台私有异常
- 不把平台专有字段扩散到共享模型中


## 推荐开发流程

接入一个新平台的建议路径：

1. 定义 capability 与 target 支持范围
2. 定义平台原始结果到 `NormalizedEntity` 的映射
3. 实现 `collect()`
4. 实现错误映射
5. 补齐适配器测试
6. 注册到 Core
7. 用 API/CLI 跑通任务


## 一句话总结

Adapter SDK 的目标是让平台接入成为一项有边界的工程工作：

适配器只负责平台，
Core 负责系统。
