# Stock Selector - 智能选股系统

> 基于行业轮动 + 多因子 + 龙头股的量化选股系统

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](https://github.com/flower-fire5/select-stock)
[![Python](https://img.shields.io/badge/python-3.9+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📖 产品简介

面向个人投资者的智能选股系统，每周运行一次，为用户提供符合风险收益比的股票推荐。

**核心目标**：
- 📊 使用频率：每周运行一次
- 📅 持有周期：1 个月
- 🛡️ 风险控制：最大回撤 ≤ 10%
- 📈 收益目标：最高盈利 ≥ 10%
- ✅ 胜率目标：月度正收益概率 ≥ 70%

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd stock-selector
pip install -r requirements.txt
```

### 2. 运行选股

```bash
# 每周选股脚本
python scripts/weekly_run.py
```

### 3. 运行回测

```bash
# 回测系统
python backtest/run.py
```

### 4. 启动 Web 界面

```bash
# Web UI (Streamlit)
streamlit run web/app.py
```

浏览器访问：http://localhost:8501

---

## 📁 项目结构

```
stock-selector/
├── backtest/           # 回测系统
│   ├── engine.py       # 回测引擎
│   ├── report.py       # 报告生成
│   └── run.py          # 回测入口
├── strategies/         # 选股策略
│   ├── base.py         # 策略基类
│   ├── industry_momentum.py  # 行业动量策略
│   ├── multi_factor.py       # 多因子策略
│   └── industry_leader.py    # 行业龙头策略
├── utils/              # 工具模块
│   ├── data_loader.py  # 数据加载 (AkShare)
│   ├── stock_screener.py  # 龙头股识别
│   └── risk_manager.py    # 风险控制
├── scripts/            # 脚本
│   └── weekly_run.py   # 每周选股脚本
├── web/                # Web 界面
│   └── app.py          # Streamlit 应用
├── config/             # 配置文件
│   └── settings.py
├── data/               # 数据目录
│   ├── raw/            # 原始数据
│   └── processed/      # 处理后的数据
├── logs/               # 日志目录
├── output/             # 输出目录
│   └── weekly/         # 每周选股结果
├── requirements.txt    # 依赖
├── README.md           # 项目说明
└── CHANGELOG.md        # 变更日志
```

---

## 📊 策略说明

### 策略 1: 行业动量策略

**逻辑**：选择近 20 日强势行业中的龙头股

1. 计算各行业指数近 20 日涨跌幅
2. 排序选出前 5 个强势行业
3. 在每个行业中选择 2 只龙头股

### 策略 2: 多因子选股策略

**逻辑**：综合质量/动量/成长/估值四因子评分

- **质量因子 (30%)**: ROE、毛利率、资产负债率
- **动量因子 (25%)**: 20 日收益率、相对强度
- **成长因子 (25%)**: 营收增长率、净利润增长率
- **估值因子 (20%)**: PE 分位、PB 分位

### 策略 3: 行业龙头股策略

**逻辑**：选择强势行业中的龙头股

龙头股标准：
- 市值行业前 3
- 营收/净利润行业前 3
- 机构持仓比例高
- 行业指数权重股

---

## 🛡️ 风控规则

| 规则 | 参数 | 说明 |
|------|------|------|
| 单股最大仓位 | 30% | 单只股票不超过总资金的 30% |
| 行业最大仓位 | 50% | 单一行业不超过总资金的 50% |
| 止损线 | 8% | 亏损达到 8% 止损 |
| 止盈线 | 15% | 盈利达到 15% 止盈（可移动） |
| 最大回撤 | 15% | 总权益回撤达到 15% 清仓 |
| 黑名单 | 可配置 | 排除 ST、问题股 |

---

## 📈 回测指标

回测完成后输出以下指标：

| 指标 | 验收标准 | 说明 |
|------|----------|------|
| 年化收益率 | ≥ 30% | 年度化收益率 |
| 最大回撤 | ≤ 15% | 历史最大亏损幅度 |
| 夏普比率 | ≥ 1.5 | 风险调整后收益 |
| 月度胜率 | ≥ 70% | 正收益月份占比 |
| 交易次数 | - | 总交易笔数 |

---

## 📅 使用流程

```
每周五收盘后
    ↓
【运行选股脚本】
python scripts/weekly_run.py
    ↓
【查看选股结果】
output/weekly/selection_YYYYMMDD.csv
output/weekly/report_YYYYMMDD.md
    ↓
【分析决策】
查看推荐股票及行业逻辑
    ↓
【下周一执行】
开盘买入推荐股票
    ↓
【持有 1 个月】
监控止盈止损
    ↓
【复盘】
月度收益统计
```

---

## 🔧 配置说明

编辑 `config/settings.py` 修改配置：

```python
# 数据源
DATA_SOURCE = "akshare"  # akshare / tushare / joinquant

# 回测周期
DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = "2026-01-01"

# 初始资金
INITIAL_CAPITAL = 1000000  # 100 万

# 风控参数
MAX_POSITION_PER_STOCK = 0.30  # 单股 30%
STOP_LOSS = 0.08  # 止损 8%
TAKE_PROFIT = 0.15  # 止盈 15%
```

---

## 📝 输出示例

### 选股结果 (CSV)

| code | name | score | reason |
|------|------|-------|--------|
| 000001 | 平安银行 | 78.5 | 综合得分：78.5 (质量:80, 动量:75, 成长:72, 估值:85) |
| 600036 | 招商银行 | 82.3 | 综合得分：82.3 (质量:85, 动量:80, 成长:78, 估值:82) |

### 回测报告

```
==================================================
回测结果摘要
==================================================
初始资金：1,000,000
最终权益：1,355,000
总收益率：35.50%
年化收益：42.30%
最大回撤：-8.50%
夏普比率：1.80
胜率：72.50%
交易次数：50
==================================================
```

---

## ⚠️ 风险提示

> **本系统仅供参考，不构成投资建议。**
> 
> 股市有风险，投资需谨慎。
> 
> 过往业绩不代表未来表现，请独立判断并承担风险。

---

## 📄 许可证

MIT License

---

## 🤝 团队协作

- **程序员**: 虾米一号
- **产品经理/测试**: 产品经理和代码 review
- **协作文件**: `/Users/hwy/Documents/股票选股系统 - 协作对话记录.md`

---

*最后更新：2026-03-10 | Stock Selector v0.2.0*
