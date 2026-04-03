# CHORE-0047-xhs-reference-adapter 执行计划

## 关联信息

- item_key：`CHORE-0047-xhs-reference-adapter`
- Issue：`#47`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md`
- active 收口事项：`CHORE-0047-xhs-reference-adapter`
- 关联 PR：`#48`

## 目标

- 为 `v0.1.0` 推进小红书参考适配器实现回合，先在共享 Core 路径上完成 `API-first` 的 `content_detail_by_url` 最小闭环：`input.url -> note_id/xsec 解析 -> detail API -> raw + normalized`。

## 范围

- 本次纳入：
  - 小红书参考适配器 `content_detail_by_url` 的 `API-first` 实现路径
  - `input.url` 到 `note_id`、`xsec_token`、`xsec_source` 的 adapter 内部解析
  - 小红书 detail API 返回到统一结果 envelope 的 `raw + normalized` 映射
  - 当前实现回合的 docs 聚合索引与 active exec-plan 追溯入口
- 本次不纳入：
  - 抖音参考适配器（含 Issue `#42`）
  - 评论、搜索、创作者等非 detail 能力
  - 资源系统、队列、多进程、HTTP API
  - `FR-0002` formal contract 语义变更

## 当前停点

- `FR-0002` formal spec 已达到 `implementation-ready`，可作为 `#47` 的实现输入。
- `CHORE-0039` 已沉淀小红书平台事实，当前回合聚焦把研究结论落入参考适配器实现路径。
- 当前事项以小红书单适配器先行，不在本轮宣称“双适配器已交付”；双适配器验证仍以 release 判据与后续事项收口为准。
- `syvert/adapters/xhs.py` 与 `tests/runtime/test_xhs_adapter.py` 已落地，当前自动化验证已覆盖 URL 解析、session/sign/detail 失败语义、`raw + normalized` 映射，以及 `--adapter-module syvert.adapters.xhs:build_adapters` 的共享 Core 路径加载。
- 默认会话文件 `$HOME/.config/syvert/xhs.session.json` 在当前环境缺失，因此“至少一条真实小红书 URL 手动验证”仍被环境前置阻塞，需在 PR 风险区显式记录。
- 最近一次 checkpoint SHA：`b885999abfecb390a387816dc6f38c4086d7d853`。

## 下一步动作

- 在 `#47` 当前实现分支补齐 `input.url` 解析与小红书 detail API 调用链。
- 完成小红书响应到 `raw + normalized` 的最小字段映射，并对齐 `FR-0002` contract。
- 以最新受审 head 重新执行 guardian / governance gates，并在 PR 正文与本 exec-plan 同步 checkpoint 与验证记录。
- 审查结论满足 merge gate 后走受控 `merge_pr` 合入。

## 当前 checkpoint 推进的 release 目标

- 让 `v0.1.0` 在“共享 Core 契约承载真实参考适配器”目标上完成小红书侧的实现推进，并为后续抖音侧并行收口提供可复用路径。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0002` implementation 阶段的小红书参考适配器主实现事项。
- 阻塞：
  - 需要以当前受审 head 通过 guardian / governance gate 后方可进入合并。
  - 若小红书签名或登录态前置失效，可能导致 API-first 链路验证受阻。

## 已验证项

- `gh issue view 47 --json number,title,body,labels,state,url`
- 已核对 `docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md` 的 `content_detail_by_url` contract 边界。
- 已核对 `docs/research/platforms/xhs-content-detail.md` 的小红书 URL 解析、detail API 与失败语义。
- `python3 -m unittest tests.runtime.test_xhs_adapter -v`
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_xhs_adapter -v`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- 默认会话文件探测：`$HOME/.config/syvert/xhs.session.json` 当前不存在，因此未执行真实 URL 手动验证命令。
- 当前回合 checkpoint 与 guardian 结论以受审 PR 正文验证区块、review 记录与状态面工件为准。

## 未决风险

- 小红书 detail API 依赖 `x-s`、`x-t`、`x-s-common`、`X-B3-Traceid` 与有效登录态，环境前置不稳定会影响回归一致性。
- 当前机器缺少默认小红书会话文件，导致真实 URL 手动验证尚未完成；若 PR 合并前仍无运行前置，只能以自动化 stub 验证作为当前证据上限。
- 若把 `xsec_token` / `xsec_source` 等平台前置误提升到 Core 输入，可能破坏 `FR-0002` 的 Core/Adapter 边界。
- 若 `normalized` 字段映射超出双平台公共最小集合，可能在本轮过早固化平台特有语义。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项在实现代码、测试与 docs 聚合索引上的增量变更，保持 `FR-0002` formal spec 与 release/sprint 主轴不被污染。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`b885999abfecb390a387816dc6f38c4086d7d853`
- 当前受审 head：`9879964093ec887db40e53f6118de11b5fcd14e7`
