#!/usr/bin/env python3
"""
快速选股脚本 - 演示用

用法:
    python3 scripts/run_selection.py
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from strategies import MultiFactorStrategy, IndustryLeaderStrategy
from utils.data_loader import DataLoader
from utils.risk_manager import RiskManager

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

logger.info("=" * 60)
logger.info("Stock Selector - 快速选股演示")
logger.info(f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 60)

# 1. 初始化
logger.info("\n【1/4】初始化...")
loader = DataLoader()
risk_manager = RiskManager(stop_loss=0.08, take_profit=0.15)

# 2. 获取数据（简化：前 30 只股票）
logger.info("\n【2/4】获取数据...")
stock_list = loader.get_stock_list().head(30)
logger.info(f"股票总数：{len(stock_list)}")

logger.info("获取股票基本信息...")
basic_info = {}
for _, row in stock_list.iterrows():
    code = row['code']
    try:
        info = loader.get_stock_basic_info(code)
        if info and info.get('pe', 0) > 0:
            basic_info[code] = info
    except:
        pass

logger.info(f"获取到 {len(basic_info)} 只股票的基本信息")

# 3. 运行策略
logger.info("\n【3/4】运行选股策略...")

# 策略 1: 多因子选股
logger.info("\n>>> 策略 1: 多因子选股策略")
strategy1 = MultiFactorStrategy()
strategy1.set_params({'top_n': 5})
result1 = strategy1.select(
    stock_data=pd.DataFrame(),
    basic_info=basic_info
)

if result1.stocks:
    logger.info(f"✅ 多因子策略选中 {len(result1.stocks)} 只股票")
    for stock in result1.stocks:
        logger.info(f"   {stock['code']} {stock['name']}: 得分 {stock['score']:.1f}")
else:
    logger.warning("⚠️ 多因子策略未选中股票")

# 策略 2: 行业龙头股
logger.info("\n>>> 策略 2: 行业龙头股策略")
strategy2 = IndustryLeaderStrategy()
result2 = strategy2.select(
    stock_data=pd.DataFrame(),
    basic_info=basic_info
)

if result2.stocks:
    logger.info(f"✅ 行业龙头策略选中 {len(result2.stocks)} 只股票")
    for stock in result2.stocks:
        logger.info(f"   {stock['code']} {stock['name']}: 得分 {stock['score']:.1f}")
else:
    logger.warning("⚠️ 行业龙头策略未选中股票")

# 4. 生成报告
logger.info("\n【4/4】生成报告...")

# 合并结果
all_stocks = result1.stocks + result2.stocks

# 去重
seen = set()
unique_stocks = []
for stock in all_stocks:
    if stock['code'] not in seen:
        seen.add(stock['code'])
        unique_stocks.append(stock)

logger.info(f"共推荐 {len(unique_stocks)} 只股票")

if unique_stocks:
    # 保存 CSV
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    df = pd.DataFrame(unique_stocks)
    csv_file = output_dir / f"selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    logger.info(f"✅ 结果已保存到：{csv_file}")
    
    # 打印表格
    logger.info("\n" + "=" * 60)
    logger.info("选股结果")
    logger.info("=" * 60)
    display_df = df[['code', 'name', 'score', 'reason']].copy()
    display_df.columns = ['代码', '名称', '得分', '理由']
    for _, row in display_df.iterrows():
        logger.info(f"{row['代码']} {row['名称']}: {row['得分']:.1f}分 - {row['理由'][:50]}...")
    logger.info("=" * 60)
else:
    logger.warning("⚠️ 未选中股票")

logger.info("\n✅ 选股完成！")
