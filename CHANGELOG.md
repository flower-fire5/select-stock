# Changelog

所有重要的项目变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- 项目初始化
- 基础目录结构

### Changed

### Fixed

---

## [0.2.0] - 2026-03-10

### Added
- Phase 1 核心模块完成
- 数据加载模块 (utils/data_loader.py) - AkShare 数据源接入
- 策略基类 (strategies/base.py) - 统一策略接口
- 行业动量策略 (strategies/industry_momentum.py) - 第一个选股策略
- 回测引擎 (backtest/engine.py) - 核心回测框架
- 回测报告 (backtest/report.py) - 绩效分析和可视化
- 主入口脚本 (backtest/run.py) - 回测系统入口
- 依赖配置 (requirements.txt)
- 系统配置 (config/settings.py)

### Changed
- 完善开发规范文档

### Fixed

---

## [0.1.0] - 2026-03-09

### Added
- 初始版本
- 项目骨架创建
- Git 仓库初始化
