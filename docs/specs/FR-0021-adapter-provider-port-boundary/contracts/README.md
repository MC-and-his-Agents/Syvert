# adapter-provider-port contract（v0.7.0）

## Contract 名称

`adapter-owned-provider-port`

## Contract 角色

- Adapter：唯一 Core-facing 执行对象。
- Adapter Provider Port：Adapter 内部执行端口。
- Native Provider：当前仓内默认实现，承载 HTTP/sign/browser bridge 等执行细节。
- Core：只感知 Adapter，不感知 provider port 或 native provider。

## 调用方向

```text
Core Runtime
  -> Adapter.execute(AdapterExecutionContext)
      -> Adapter-owned Provider Port
          -> Native Provider
      -> Adapter normalizer
  -> Core success / failed envelope
```

禁止调用方向：

- Core -> Provider Port
- Core -> Native Provider
- Registry -> Provider Port
- Resource lifecycle -> Provider selector

## 输入 contract

Provider port 输入由 Adapter 构造，必须来源于：

- Adapter 已完成解析后的 provider-internal context
- 已验证的 target URL
- Adapter 从 injected account resource 中抽取并校验后的 platform session config
- Adapter 解析出的站点目标信息

Provider port 输入不得包含：

- `AdapterExecutionContext` 或 `TaskRequest`
- Core `resource_bundle`、resource lease 或 lifecycle store
- provider priority
- external provider id
- fallback order
- resource acquisition request
- Core routing hint

## 输出 contract

Provider port 输出只能返回：

- raw platform payload
- platform detail object
- adapter-internal diagnostics

Provider port 不得返回：

- Syvert normalized result
- TaskRecord patch
- Core envelope
- provider routing decision
- resource lifecycle mutation

## 兼容性 contract

实现 `#269` 时必须保持：

- `XhsAdapter` 与 `DouyinAdapter` public metadata 不变
- existing constructor transport hooks 可用
- existing default transport helper import path 可用
- `content_detail_by_url` public operation 到 `content_detail` adapter family 的投影不变
- `raw` 与 `normalized` 成功 payload shape 不因 provider port 拆分改变
- 小红书 / 抖音 URL parsing、account material extraction、raw carrier、normalized fields 与既有错误优先级符合 `data-model.md` 的 approved slice compatibility baseline

## 非目标 contract

本 contract 不提供：

- 外部 provider SDK
- provider plugin registration
- Core provider registry
- provider selector
- 跨 provider fallback
- 新业务 capability approval
