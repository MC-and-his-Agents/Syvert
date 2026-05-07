# Syvert Version Management

## 目标

本文定义 Syvert 的版本语义、版本事实源、发布锚点与 closeout 规则，避免 roadmap、release 索引、Git tag、GitHub Release、runtime schema version 与 SDK contract version 互相漂移。

## 版本层次

Syvert 同时存在多个版本层次，它们不能互相替代：

| 层次 | 示例 | 职责 | 事实源 |
|---|---|---|---|
| Roadmap milestone | `v1.0.0`、`v2.0.0` | 描述阶段目标与稳定性声明 | roadmap 系列文件 |
| Release index | `docs/releases/v0.8.0.md` | 聚合某个 release 要证明什么、纳入哪些事项、完成依据 | `docs/releases/` |
| Git tag | `v0.8.0` | 锚定发布提交 | Git annotated tag |
| GitHub Release | `releases/tag/v0.8.0` | 对外发布记录 | GitHub Release |
| Python package artifact | `.whl`、`.tar.gz` | 可安装分发物 | `docs/process/python-packaging.md` 与 GitHub Release artifact |
| Runtime / schema version | `v0.4.0` resource lifecycle schema | 描述某个内部 contract / schema 的冻结版本 | 对应 formal spec、代码常量与测试 |
| SDK / contract version | `v0.8.0` provider offer contract | 描述 Adapter / Provider contract 的兼容边界 | formal spec、SDK 文档、validator |

## 命名规则

- 对外 release、roadmap milestone 与 tag 使用 `vMAJOR.MINOR.PATCH`。
- `MAJOR` 表示一组底座契约成熟度声明，不由 minor 数字自然滚动触发。
- `MINOR` 表示一个受控能力阶段或一组兼容扩展完成。
- `PATCH` 表示不改变公共 contract 的修复、回写、发布真相同步或兼容性修补。
- Sprint、Phase、FR、Work Item 不得被当作版本号使用。
- `v1.x` 表示一组 minor 序列，不表示最多只能走到 `v1.9.0`。
- 可以存在 `v1.10.0`、`v1.11.0` 等版本；只有满足 major gate 时才进入下一个 major。

## 事实源边界

### Roadmap

Roadmap 只回答版本阶段要证明什么、明确不做什么、进入下一阶段的稳定性门槛是什么。

Roadmap 不承载：

- GitHub backlog 状态
- 已发布 tag 真相
- 某个 PR 的 live review 状态
- 某个 provider 产品正式支持清单

### Release Index

Release index 是仓内发布语义 carrier。它记录：

- release 目标
- 明确不在范围
- 目标判据
- 纳入事项
- 关联工件
- 已发布后的 published truth carrier

Release index 不替代 GitHub Phase / FR / Work Item 状态，也不复制 formal spec 正文。

### Git Tag 与 GitHub Release

Git tag 与 GitHub Release 是发布锚点。

- Tag 必须锚定已合入 `main` 的发布提交。
- 正式 release tag 应使用 annotated tag。
- GitHub Release 必须指向同名 tag。
- 新增或重写的 Release index published truth carrier 应记录 tag target、GitHub Release URL 与发布时间。
- 既有 `v0.1.0` 到 `v0.7.0` release index 允许保留历史 closeout / 发布状态表达，直到独立 legacy migration Work Item 统一回写。
- `v0.8.0` 及后续新增 release index 应使用 published truth carrier 三元组作为发布真相表达。

### Runtime / Schema / SDK Version

代码中的 schema version、matrix version、SDK contract version 只描述某个局部 contract 的版本，不等同于整个仓库 release。

修改这类版本时必须满足：

- 有对应 formal spec、decision 或 release gate 说明为什么需要变更。
- 有测试证明旧行为的兼容 / 拒绝边界。
- 不把局部 schema version 当作全仓版本 truth。

### Python Package Artifact

Python package 是可选分发物，不是默认 release truth source。

- 引入 Python packaging 的边界、版本来源、CI 与发布渠道见 `docs/process/python-packaging.md`。
- Python package version 必须从 Git tag 派生，不维护独立手写版本号。
- Package artifact 只有在对应 release 明确声明时，才成为 release closeout 的必需交付物。
- PyPI / GitHub Packages publish 必须由独立 FR 批准，不得在普通 release closeout 中顺手加入。

## Release 类型

### Major Release

Major release 是底座契约成熟度声明。

进入新的 major 前必须有明确 gate，例如：

- `v1.0.0`：Core stable。
- `v2.0.0`：扩展 runtime capability contract stable。

Major release 不因 minor 序列耗尽自动发生。

### Minor Release

Minor release 用于兼容扩展或阶段性能力稳定化，例如：

- 新 runtime capability contract 达到 stable。
- 新资源治理边界完成 formal spec、runtime 与验证。
- 新 Adapter / Provider 兼容性扩展完成 evidence。

Minor release 可以多于 9 个。

### Patch Release

Patch release 用于不改变公共 contract 的修复或回写，例如：

- release truth 回写
- 文档链接修正
- gate 误报修复
- 兼容性修补

Patch release 不得引入新的公共 operation、资源词汇、Adapter contract 或 provider compatibility 语义。

## Release Closeout 流程

一个 release 只有在以下事实一致后，才可视为发布完成：

1. GitHub Phase / FR / Work Item closeout 已完成或有明确 pending 边界。
2. 所有 release gate、contract test、双参考或等价真实证据已通过。
3. `docs/releases/` 下的 `vX.Y.Z.md` release 索引已记录目标判据、纳入事项、关联工件与 closeout evidence。
4. 发布提交已合入 `main`。
5. `vX.Y.Z` annotated tag 已创建并推送。
6. GitHub Release 已创建并指向同名 tag。
7. Release index 已回写 published truth carrier。
8. 对应 closeout Issue / Work Item 与 PR 状态已经对账。

若 tag / GitHub Release 已创建，但 release index 尚未回写 published truth，该 release 仍处于发布真相待对齐状态。

## 自动化门禁

版本管理规则同时由文档和 CI 共同约束。

`scripts/version_guard.py` 负责可机械校验的版本一致性：

- release 索引文件必须放在 `docs/releases/` 下，使用 `vMAJOR.MINOR.PATCH.md` 命名，并以同名 `# Release vMAJOR.MINOR.PATCH` 标题开头。
- release 模板必须包含版本类型、公共 contract 变更、tag / GitHub Release 与 published truth carrier 字段。
- Python packaging 规划文档必须存在，并被版本管理规则引用。
- roadmap 必须引用版本管理规则，`v1.x -> v2.0.0` 路线必须保留 `Stabilization Gate` 与 `v1.10.0` 语义。
- 声明 tag / GitHub Release / 发布完成事实的 release 文档必须有 published truth carrier 类章节。
- 顶层定位文档不得重新引入含混应用化定位短语。

`.github/workflows/version-guard.yml` 在 PR 中执行该门禁。

CI 不能替代人工判断以下事项：

- 某个 major gate 是否已经实质满足。
- 某个能力是否应进入 Core public contract，还是留在 Adapter / Provider 私有表面。
- GitHub Phase / FR / Work Item 是否已经完成语义 closeout。
- tag 与 GitHub Release 是否应在当前提交创建。

## v1.x 到 v2.0.0 规则

`v1.x` 是稳定 Core 之后的底座能力扩展阶段。

`v2.0.0` 只在 `docs/roadmap-v1-to-v2.md` 的 Stabilization Gate 满足后发生。以下情况不得触发 `v2.0.0`：

- 只是已经发布到 `v1.9.0`。
- 某个上层应用已经能运行。
- 某个 provider 产品覆盖了多个能力。
- 只完成读侧能力，但写侧安全契约、batch / dataset 或 compatibility evidence 未成熟。

不满足 gate 时继续发布 `v1.x` minor 或 patch。

## 禁止事项

- 禁止把上层应用产品完整度写成 Syvert 主仓版本完成条件。
- 禁止把某个 provider 产品支持写成全局 release 承诺。
- 禁止把 runtime schema version 当作仓库 release version。
- 禁止在未完成 release closeout 对账时声明发布完成。
- 禁止为追求版本号推进而降低写操作安全门槛。

## 与其他文档的关系

- `vision.md` 定义长期定位与边界。
- `docs/roadmap-v0-to-v1.md` 定义 `v0.x -> v1.0.0` Core stable 路线。
- `docs/roadmap-v1-to-v2.md` 定义 `v1.x -> v2.0.0` runtime capability contract 扩展路线。
- `docs/process/python-packaging.md` 定义 Python package distribution artifact 的引入边界。
- `docs/releases/` 承载 release 索引与 published truth carrier。
- `docs/sprints/` 承载 sprint 执行轮次索引。
- `docs/process/delivery-funnel.md` 定义交付漏斗。
