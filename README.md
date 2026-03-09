# Stock Selector - 选股系统

## 项目简介
量化选股策略实现与回测框架

## 技术栈
- Python 3.x
- pandas / numpy
- backtrader (回测)
- tushare / akshare (数据源)

## 目录结构
```
stock-selector/
├── data/          # 数据文件
├── strategies/    # 选股策略
├── backtest/      # 回测脚本
├── utils/         # 工具函数
└── config/        # 配置文件
```

## 快速开始
```bash
pip install -r requirements.txt
python backtest/run.py
```

## 待办
- [ ] 数据接入
- [ ] 策略实现
- [ ] 回测框架
- [ ] 实盘对接
