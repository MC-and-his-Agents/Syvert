# Syvert Python Packaging

## 目标

本文记录 Syvert 引入 Python packaging 的决策边界，防止未来把 package publish 遗忘为临时补丁，也防止过早把包发布变成 `v1.0.0` release gate。

## 当前结论

Syvert 长期应具备可安装的 Python 分发物，但当前 package publish 不是 release 完成的默认条件。

当前阶段的正式结论：

- `v1.0.0` 前不要求发布 PyPI / GitHub Packages 包。
- Python packaging 可以作为独立 FR 进入规划与实现。
- 引入 packaging 前必须先冻结 package boundary、版本来源、CI 与发布回滚策略。
- package publish 是 distribution artifact，不是 Syvert release truth source。

## 包边界

首个 Python package 只应包含 Syvert runtime 与 SDK-facing API：

- `syvert/`
- runtime task / resource / result contract
- Adapter SDK-facing 类型与 helper
- contract test / validation helper 中明确批准进入外部分发的部分
- CLI entrypoint，例如 `syvert = syvert.cli:main`

默认不进入首个 package：

- `scripts/` 治理工具
- `docs/`
- `tests/`
- `.loom/`
- `.github/`
- reference adapter 的真实账号、会话、私有 provider 配置

参考适配器是否进入同一个 package 需要独立判断。默认策略是先保留为 proof / sample，不把目标系统支持误表达为 package 的产品承诺。

## 版本来源

Python package version 必须从 Git tag 派生，不维护第二套手写版本号。

允许的实现方向：

- `hatchling` + `hatch-vcs`
- `setuptools` + `setuptools-scm`

禁止事项：

- 禁止在 `syvert/__init__.py` 手写与 release tag 独立漂移的 `__version__`。
- 禁止让 Python package version 反向决定 repo release。
- 禁止把 runtime schema version、SDK contract version 或 compatibility matrix version 当作 Python package version。

## 发布渠道

推荐分阶段引入：

1. 只增加 `pyproject.toml`、build CI 与 wheel smoke test。
2. GitHub Release 附加 `.whl` 与 `.tar.gz` artifact。
3. 外部 Adapter 或上层应用出现真实安装消费后，再批准 PyPI / GitHub Packages publish。

PyPI / GitHub Packages 发布必须作为独立 FR 批准，不得在普通 release closeout 中顺手加入。

## CI 门禁

Packaging 实现 PR 至少需要：

- `python -m build`
- 安装生成的 wheel 后执行 CLI smoke test
- 校验 wheel 不包含 `docs/`、`tests/`、`.loom/`、`.github/` 与未批准的治理脚本
- 校验 package version 来源于 Git tag 或被明确标记为 local/dev version

如果某个 release 明确声明 package artifact 是交付物，则该 release 的 closeout 必须记录 build artifact、校验结果与发布渠道。

## 进入实现条件

引入 `pyproject.toml` 前必须满足：

- `v1.0.0` Core public contract 已经接近稳定，或已有真实外部 Adapter / 上层应用需要安装消费。
- 已明确 package 名称、入口点、包含 / 排除范围。
- 已明确依赖策略与 Python 版本支持范围。
- 已明确 package artifact 是否进入对应 release closeout。

## 与版本管理的关系

- `docs/process/version-management.md` 定义 repo release truth。
- 本文只定义 Python package distribution artifact。
- Git tag 与 GitHub Release 仍是 Syvert release 发布锚点。
- Python package 发布可以跟随 GitHub Release，但不得替代 GitHub Release。
