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

- 为 `v0.1.0` 推进小红书参考适配器实现切片，先在共享 Core 路径上完成 `API-first` 的 `content_detail_by_url` 最小闭环：`input.url -> note_id/xsec 解析 -> detail API -> raw + normalized`，并以自动化证据验证 Core/Adapter 接缝。

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
- 最近一次实现收口已针对 reviewer findings 修复：detail 结构化失败保留为平台错误、成功态 `raw` 保留平台原始 success wrapper、Live Photo 归一化为 `mixed_media`、origin 视频 URL 改为 `https`、异常时间戳 / 计数字段降级为 `null`、`xhslink` 在当前阶段显式拒绝。
- 最新一轮 guardian 阻断已进一步收口：detail 返回多 item 时按 `source_note_id` 选中目标 note，不再盲取 `items[0]`；`nullable_int` 对 `inf` / `nan` fail-close 为 `null`；并补了 `default_sign_transport`、`post_json` 与 malformed success wrapper 的定点回归测试。
- 默认会话文件 `$HOME/.config/syvert/xhs.session.json` 在当前环境缺失，因此“至少一条真实小红书 URL 手动验证”仍被环境前置阻塞，需在 PR 风险区显式记录。
- 当前 PR 仅声称交付“实现切片 + 自动化验证证据”；Issue `#47` 的 real URL 手动验证闭环仍待运行前置满足后继续推进。
- 最近一次 checkpoint SHA：`31e06224fc4c72f769d43a7f315b9d3d3105c45a`。

## 下一步动作

- 在具备小红书 session / sign 运行前置后，补至少一条真实 `content_detail_by_url` 手动验证记录，再决定是否关闭 Issue `#47`。
- 将当前实现 checkpoint、PR 正文与 guardian 审查输入持续同步到最新受审 head。
- 以最新受审 head 重新执行 guardian / governance gates，并在 PR 正文同步验证记录。
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
- `python3 -m unittest tests.runtime.test_xhs_adapter.XhsAdapterTests.test_xhs_adapter_selects_matching_note_card_when_detail_returns_multiple_items tests.runtime.test_xhs_adapter.XhsAdapterTests.test_xhs_adapter_coerces_non_finite_float_stats_to_null tests.runtime.test_xhs_adapter.XhsAdapterTests.test_default_sign_transport_rejects_failed_sign_payload tests.runtime.test_xhs_adapter.XhsAdapterTests.test_default_sign_transport_rejects_missing_data_mapping tests.runtime.test_xhs_adapter.XhsAdapterTests.test_post_json_rejects_invalid_json_detail_response tests.runtime.test_xhs_adapter.XhsAdapterTests.test_post_json_rejects_non_object_sign_response tests.runtime.test_xhs_adapter.XhsAdapterTests.test_normalize_detail_response_rejects_success_without_mapping_data -v`
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

- 实现 checkpoint：`31e06224fc4c72f769d43a7f315b9d3d3105c45a`
- 当前受审 head：以 PR `#48` 的最新 `headRefOid` 为准
