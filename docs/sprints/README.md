# Syvert Sprint 索引区

本目录用于承载 sprint 级协作索引与工件入口。

## 职责边界

- sprint 文档回答“本轮协作绑定到哪个 release、入口在哪里、退出判据是什么”。
- sprint 文档只承载索引与入口，不承载 GitHub backlog 的状态真相。
- sprint 文档通过 `item_key` 关联 `release`、`spec`、`exec-plan` 与 PR。

## 禁止承载的内容

- 不镜像 Project 看板状态。
- 不记录逐项阻塞、checkpoint 明细或执行中状态。
- 不替代 GitHub iteration / milestone 记录。
- 不复制 formal spec 正文或长任务完整执行日志。

## 模板

- 新 sprint 索引优先从 [./_template.md](./_template.md) 复制。
