# CHORE-0050-douyin-reference-adapter 执行计划

## 关联信息

- item_key：`CHORE-0050-douyin-reference-adapter`
- Issue：`#50`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md`
- active 收口事项：`CHORE-0050-douyin-reference-adapter`
- 关联 PR：`#51`

## 目标

- 为 `v0.1.0` 推进抖音参考适配器实现切片，在共享 Core 主路径上完成 `content_detail_by_url` 的 `API-first + adapter 私有回退` 最小闭环：`input.url -> aweme_id 解析 -> verify/sign/detail -> raw + normalized`，并保留浏览器页面态 fallback 作为 adapter 内部恢复策略。

## 范围

- 本次纳入：
  - 抖音参考适配器 `content_detail_by_url` 的主实现路径
  - `https://www.douyin.com/video/<aweme_id>` 与 `https://www.iesdouyin.com/share/video/<aweme_id>` 两种 URL 形态
  - adapter 内部的会话文件、签名调用、detail 请求、`raw + normalized` 映射
  - adapter 私有 browser-state fallback
  - 共享 registry、测试与当前回合 docs 聚合索引
- 本次不纳入：
  - `v.douyin.com` 短链解析
  - `#42` 双适配器验证收口
  - 评论、搜索、创作者等非 detail 能力
  - 通用资源系统、HTTP API、后台队列
  - `FR-0002` formal contract 语义变更

## 当前停点

- `main@6d7e2be24b9e37860939c5ad598e1e76e093e3af` 已具备 `FR-0002` formal spec、runtime / CLI 宿主、小红书参考适配器与抖音平台研究输入。
- 当前执行现场已通过 `python3 scripts/create_worktree.py --issue 50 --class implementation` 建立为独立 worktree：`issue-50-adapter-douyin-reference-adapter-on-shared-core-path`。
- 抖音 adapter、browser bridge、共享 registry 与新增测试已在工作树落地，并已形成 implementation checkpoint commit `ed27159`；在该实现回合中已完成全量 runtime 测试、docs guard、spec guard、governance gate 与真实 CLI 验收。
- 最新手动验收命令为 `python3 -m syvert.cli --adapter douyin --capability content_detail_by_url --url https://www.douyin.com/video/7580570616932224282 --adapter-module syvert.adapters:build_adapters`，结果 `status=success`，`normalized.content_id=7580570616932224282`，`normalized.canonical_url=https://www.douyin.com/video/7580570616932224282`，且 `raw` 同时含 `RENDER_DATA` 与 `AWEME_DETAIL`，当前证据归因为 adapter 私有 browser fallback 成功。
- 下一步需在当前 implementation PR `#51` 上推进 reviewer / guardian / merge gate，直到满足 squash merge 条件。

## 下一步动作

- 推进 implementation PR `#51` 的 reviewer / guardian / merge gate。
- 完成 squash merge，并核对 `Fixes #50` 已把 issue 状态自动收口。

## 当前 checkpoint 推进的 release 目标

- 让 `v0.1.0` 在“同一 Core 契约承载两个真实参考适配器”目标上补齐抖音侧实现切片，为后续 `#42` 的双适配器共享路径验证提供第二个真实平台。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0002` implementation 阶段的抖音参考适配器主实现事项。
- 阻塞：
  - 需要把当前工作树实现转化为已验证、已提交、已开 PR 的 checkpoint。
  - 需要在当前受审 head 上通过 reviewer / guardian / merge gate 后才能进入合并。

## 已验证项

- `python3 scripts/create_worktree.py --issue 50 --class implementation --dry-run`
- `python3 scripts/create_worktree.py --issue 50 --class implementation`
- `git worktree list`
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_xhs_adapter tests.runtime.test_xhs_browser_bridge tests.runtime.test_douyin_adapter tests.runtime.test_douyin_browser_bridge -v`
  - 结果：`Ran 142 tests in 3.470s OK`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：`docs-guard 通过。`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：`spec-guard 通过。`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：`governance-gate 通过。`
- `python3 -m syvert.cli --adapter douyin --capability content_detail_by_url --url https://www.douyin.com/video/7580570616932224282 --adapter-module syvert.adapters:build_adapters`
  - 结果：`status=success`
  - 来源判断：`fallback`
  - `normalized.content_id`：`7580570616932224282`
  - `normalized.canonical_url`：`https://www.douyin.com/video/7580570616932224282`

## 未决风险

- 抖音 detail API 依赖 `verifyFp`、`msToken`、`webid` 与 `a_bogus`，不同环境下仍可能受平台风控影响。
- browser-state fallback 当前只覆盖已打开、已登录的 Chrome 详情页；若标签页不存在或页面态结构漂移，仍会回到平台失败。
- 若后续为了支持更多 URL 形态把短链解析、页面抓取或平台前置误提升到 Core，会破坏 `FR-0002` 的边界。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项在 `syvert/adapters/`、`tests/runtime/`、`docs/releases/v0.1.0.md`、`docs/sprints/2026-S15.md` 与本 exec-plan 上的增量变更，保持 `FR-0002` formal spec 与既有小红书实现不受污染。

## 最近一次 checkpoint 对应的 head SHA

- 受审 diff 基线：`6d7e2be24b9e37860939c5ad598e1e76e093e3af`
- implementation checkpoint：`ed271590c70608bba4c5bc6958cb69da242dcd4f`
