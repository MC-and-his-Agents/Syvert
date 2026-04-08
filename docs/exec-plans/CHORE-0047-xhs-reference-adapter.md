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
- 当前实现已接入 `#49` 的 Chrome browser bridge，但该路径只存在于 xhs adapter 私有 fallback 中，不向 Core 暴露任何浏览器资源提供方、资源调度器或新增运行时输入。
- 当前实现目标仍是 `API-first` 主路径；browser bridge 只作为 adapter 内部 fallback，用于在真实环境里补足平台阻断下的可达性验证，不改变 `FR-0002` 的 Core 输入和结果 envelope。
- 当前实现 checkpoint `fa0b5a0c4c0722134cec9e87d6625198af3e7332` 已进一步收口本轮 guardian findings：browser bridge / CDP fallback 统一返回页面原始 `note` 状态对象而不是 adapter 合成 note payload；`xhs_browser_javascript_disabled` 等 fallback 自身故障不再被原始 API/sign 错误完全覆盖；`xhs_browser_target_tab_missing` 仅作为 fallback 不可用信号保留原始顶层错误；browser tab 匹配按 `note_id` / canonical URL 做稳健匹配；页面态 fallback 现在会校验命中的真实 `note_id` 必须等于目标 `source_note_id`，不再因 `noteDetailMap` key 命中而误归一化错误内容。
- 最近一次手动验证使用的 detail URL 为：
  - `https://www.xiaohongshu.com/explore/69d33f6a000000001f0078b3?xsec_token=ABjzCcnPAF6N42MrShWFDtw9sYJB2IyR63WIic1pDjCO0=&xsec_source=`
- 当前受审 diff 基线：`origin/main@4edce18ae5f416e453eeca8dada9122c8b613f1a`
- 最近一次实现 checkpoint SHA：`fa0b5a0c4c0722134cec9e87d6625198af3e7332`

## 下一步动作

- 将 PR `#48` 的审查输入同步到实现 checkpoint `fa0b5a0c4c0722134cec9e87d6625198af3e7332`，并在 PR 正文显式写明 browser-state fallback 前置、验证入口和最新验证摘要。
- 基于当前分支最新 head 重新执行完整验证与 guardian / governance gates。
- 审查结论满足 merge gate 后走受控 `merge_pr` 合入。

## 当前 checkpoint 推进的 release 目标

- 让 `v0.1.0` 在“共享 Core 契约承载真实参考适配器”目标上完成小红书侧的实现推进，并为后续抖音侧并行收口提供可复用路径。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0002` implementation 阶段的小红书参考适配器主实现事项。
- 阻塞：
- 需要以当前受审 head 通过 guardian / governance gate 后方可进入合并。
- 当前实现侧 blocker 已收口到 checkpoint `fa0b5a0c4c0722134cec9e87d6625198af3e7332`；剩余阻塞只在审查输入同步与 guardian merge gate。

## 已验证项

- `gh issue view 47 --json number,title,body,labels,state,url`
- 已核对 `docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md` 的 `content_detail_by_url` contract 边界。
- 已核对 `docs/research/platforms/xhs-content-detail.md` 的小红书 URL 解析、detail API 与失败语义。
- `python3 -m unittest tests.runtime.test_xhs_adapter -v`
- `python3 -m unittest tests.runtime.test_xhs_browser_bridge -v`
- `python3 -m unittest tests.runtime.test_xhs_adapter.XhsAdapterTests.test_xhs_adapter_selects_matching_note_card_when_detail_returns_multiple_items tests.runtime.test_xhs_adapter.XhsAdapterTests.test_xhs_adapter_coerces_non_finite_float_stats_to_null tests.runtime.test_xhs_adapter.XhsAdapterTests.test_default_sign_transport_rejects_failed_sign_payload tests.runtime.test_xhs_adapter.XhsAdapterTests.test_default_sign_transport_rejects_missing_data_mapping tests.runtime.test_xhs_adapter.XhsAdapterTests.test_post_json_rejects_invalid_json_detail_response tests.runtime.test_xhs_adapter.XhsAdapterTests.test_post_json_rejects_non_object_sign_response tests.runtime.test_xhs_adapter.XhsAdapterTests.test_normalize_detail_response_rejects_success_without_mapping_data -v`
- `python3 -m unittest tests.runtime.test_models tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_cli tests.runtime.test_xhs_adapter tests.runtime.test_xhs_browser_bridge -v`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- 手动验证记录：
  - 在已登录浏览器现场获取带完整 `xsec_token` 的小红书 detail URL。
  - 执行 `python3 -m syvert.cli --adapter xhs --capability content_detail_by_url --url 'https://www.xiaohongshu.com/explore/69d33f6a000000001f0078b3?xsec_token=ABjzCcnPAF6N42MrShWFDtw9sYJB2IyR63WIic1pDjCO0=&xsec_source=' --adapter-module syvert.adapters.xhs:build_adapters`。
  - 结果摘要：返回 `status=success`，`normalized.content_id=69d33f6a000000001f0078b3`，`normalized.title=小红书新规！碰这8条红线全完⚠️`。
  - 行为摘要：此次成功经过 xhs adapter 内部 fallback；Core 输入、任务模型和结果 envelope 未变化。
- 当前回合审查输入以本文件记录的 `origin/main` 基线 SHA、实现 checkpoint SHA 与验证命令为准；PR 正文只做索引和外链补充。

## 未决风险

- 小红书 detail API 与签名服务仍然不稳定；当前实现通过 adapter 内部 browser bridge 为真实验证提供 fallback，但 API-first 主路径在别的环境里仍可能受风控影响。
- 若把 `xsec_token` / `xsec_source` 等平台前置误提升到 Core 输入，可能破坏 `FR-0002` 的 Core/Adapter 边界。
- 若 `normalized` 字段映射超出双平台公共最小集合，可能在本轮过早固化平台特有语义。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项在实现代码、测试与 docs 聚合索引上的增量变更，保持 `FR-0002` formal spec 与 release/sprint 主轴不被污染。

## 最近一次 checkpoint 对应的 head SHA

- 受审 diff 基线：`4edce18ae5f416e453eeca8dada9122c8b613f1a`
- 实现 checkpoint：`fa0b5a0c4c0722134cec9e87d6625198af3e7332`
