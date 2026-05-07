# ADR-GOV-0348 Govern roadmap, version management, and packaging boundaries

## 关联信息

- Issue：`#348`
- item_key：`GOV-0348-roadmap-version-management`
- item_type：`GOV`
- release：`v0.9.0`
- sprint：`2026-S21`

## 背景

Syvert 在 `v0.8.0` 之后需要同时回答三类边界问题：

- `v1.0.0` 是否应继续表示 Core stable，而不是上层应用完成版。
- `v1.x -> v2.0.0` 是否需要更细路线，且不由 `v1.9.0` 自动触发 major 升级。
- 版本、release closeout、tag、GitHub Release、runtime schema version、SDK contract version 与未来 Python package artifact 如何避免互相漂移。

同时，外部场景和上层应用可能倒逼 search / list / comment / batch / dataset / publish 等能力扩展。这些能力应先被表达为 Syvert runtime capability contract、resource governance 与 Adapter / Provider 执行表面，而不是直接把某个不成熟上层产品形态写入主仓路线图。

## 决策

- `v1.0.0` 继续定义为 Core stable，不把账号矩阵、内容库、发布中心或自动运营应用纳入完成条件。
- 新增 `docs/roadmap-v1-to-v2.md`，把 `v1.x -> v2.0.0` 定义为扩展 runtime capability contract 稳定化路线。
- 明确 `v1.x` 不是 `v1.1.0` 到 `v1.9.0` 的倒计时；不满足 major gate 时可以继续 `v1.10.0`、`v1.11.0` 等 minor。
- 新增 `docs/process/version-management.md`，固定 roadmap milestone、release index、Git tag、GitHub Release、runtime / schema version、SDK / contract version 与 Python package artifact 的职责边界。
- 新增 `scripts/version_guard.py` 与 CI workflow，把可机械检查的版本规则纳入 PR gate。
- 新增 `docs/process/python-packaging.md`，把 Python packaging 作为长期可安装分发物规划，但不作为当前 release 默认完成条件。
- 修正 `scripts/policy/policy.json`，让 `docs/roadmap-v1-to-v2.md` 被治理/文档 PR class 正确识别。

## 影响

- 后续路线讨论有正式的 `v0 -> v1` 与 `v1 -> v2` 分界载体。
- 版本发布不再只靠文档约束；release 索引、version guard、CI 与 governance tests 共同防止关键边界被遗忘。
- Python packaging 被纳入规划和自动化检查，但不会提前引入 `pyproject.toml`、PyPI / GitHub Packages publish 或 package release gate。
- 上层应用仍应在独立仓库消费 Syvert，不进入 Syvert 主仓职责边界。

## 回滚

如该治理方向需要撤回，使用独立 revert PR 撤销本事项新增的 roadmap、version management、version guard、Python packaging 规划、policy 分类与对应测试增量。
