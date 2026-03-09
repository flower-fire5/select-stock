#!/usr/bin/env python3
"""
回测系统主入口

用法:
    python backtest/run.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from datetime import datetime

from config.settings import (
    INITIAL_CAPITAL, 
    DEFAULT_START_DATE, 
    DEFAULT_END_DATE,
    MAX_POSITION_PER_STOCK,
    MAX_POSITION_PER_INDUSTRY
)
from utils.data_loader import DataLoader
from strategies import IndustryMomentumStrategy
from backtest.engine import BacktestEngine
from backtest.report import ReportGenerator


def setup_logger():
    """配置日志"""
    logger.remove()
    logger.add(
        "logs/stock_selector.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        sys.stdout,
        level="INFO",
        format="{time:HH:mm:ss} | {level} | {message}"
    )


def main():
    """主函数"""
    setup_logger()
    logger.info("=" * 50)
    logger.info("Stock Selector 回测系统")
    logger.info("=" * 50)
    
    # 1. 初始化数据加载器
    logger.info("\n[1/4] 初始化数据加载器...")
    loader = DataLoader()
    
    # 2. 获取数据
    logger.info("\n[2/4] 获取数据...")
    start_date = DEFAULT_START_DATE
    end_date = DEFAULT_END_DATE
    
    # 获取股票列表
    stock_list = loader.get_stock_list()
    logger.info(f"股票总数：{len(stock_list)}")
    
    # 获取行业列表
    industry_list = loader.get_industry_list()
    logger.info(f"行业数量：{len(industry_list)}")
    
    # 测试：获取前 10 只股票的数据（实际应该获取全部）
    logger.info("\n加载测试数据（前 10 只股票）...")
    all_stock_data = []
    
    for _, row in stock_list.head(10).iterrows():
        code = row['code']
        try:
            daily_data = loader.get_daily_data(code, start_date, end_date)
            if not daily_data.empty:
                all_stock_data.append(daily_data)
        except Exception as e:
            logger.warning(f"获取 {code} 数据失败：{e}")
    
    if all_stock_data:
        stock_data = pd.concat(all_stock_data)
        logger.info(f"成功加载 {len(stock_data)} 条日线数据")
    else:
        logger.error("未能获取到股票数据，回测无法继续")
        return
    
    # 获取行业数据
    industry_data_list = []
    for industry in industry_list.head(5):  # 测试前 5 个行业
        try:
            ind_data = loader.get_industry_daily(industry, start_date, end_date)
            if not ind_data.empty:
                industry_data_list.append(ind_data)
        except Exception as e:
            logger.warning(f"获取行业 {industry} 数据失败：{e}")
    
    industry_data = pd.concat(industry_data_list) if industry_data_list else pd.DataFrame()
    
    # 3. 初始化策略
    logger.info("\n[3/4] 初始化策略...")
    strategy = IndustryMomentumStrategy()
    strategy.set_params({
        'lookback_days': 20,
        'top_industries': 3,
        'stocks_per_industry': 2
    })
    logger.info(f"策略：{strategy.name}")
    logger.info(f"参数：{strategy.get_params()}")
    
    # 4. 运行回测
    logger.info("\n[4/4] 运行回测...")
    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL,
        max_position_per_stock=MAX_POSITION_PER_STOCK,
        max_position_per_industry=MAX_POSITION_PER_INDUSTRY
    )
    
    result = engine.run(
        strategy=strategy,
        stock_data=stock_data,
        industry_data=industry_data,
        start_date=start_date,
        end_date=end_date,
        rebalance_days=20
    )
    
    # 5. 生成报告
    logger.info("\n生成回测报告...")
    generator = ReportGenerator()
    report = generator.generate(
        result=result,
        strategy_name=strategy.name,
        period=f"{start_date} ~ {end_date}"
    )
    
    # 打印摘要
    generator.print_metrics(result.metrics)
    
    logger.info("\n" + "=" * 50)
    logger.info("回测完成!")
    logger.info(f"报告保存位置：{generator.output_dir}")
    logger.info("=" * 50)


if __name__ == "__main__":
    import pandas as pd
    main()
