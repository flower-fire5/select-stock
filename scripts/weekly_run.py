#!/usr/bin/env python3
"""
每周自动选股脚本

用法:
    python scripts/weekly_run.py

功能:
1. 获取最新数据
2. 运行选股策略
3. 生成选股报告
4. 保存结果到 output 目录
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR, PROCESSED_DATA_DIR
from utils.data_loader import DataLoader
from strategies import MultiFactorStrategy, IndustryLeaderStrategy
from utils.risk_manager import RiskManager


def setup_logger():
    """配置日志"""
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        level="INFO",
        format="{time:HH:mm:ss} | {level} | {message}"
    )
    
    # 文件日志
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "weekly_run.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )


def run_weekly_selection():
    """执行每周选股"""
    logger.info("=" * 60)
    logger.info("Stock Selector - 每周选股")
    logger.info(f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # 1. 初始化
    logger.info("\n[1/5] 初始化...")
    loader = DataLoader()
    risk_manager = RiskManager(
        stop_loss=0.08,
        take_profit=0.15,
        blacklist=['601313']  # 示例黑名单
    )
    
    # 2. 获取数据
    logger.info("\n[2/5] 获取数据...")
    
    # 获取股票列表（简化：前 100 只）
    stock_list = loader.get_stock_list()
    logger.info(f"股票总数：{len(stock_list)}")
    
    # 获取基本信息（简化测试：使用前 20 只股票）
    logger.info("获取股票基本信息（测试模式：前 20 只）...")
    basic_info = {}
    for _, row in stock_list.head(20).iterrows():
        code = row['code']
        try:
            info = loader.get_stock_basic_info(code)
            if info and info.get('pe', 0) > 0:
                basic_info[code] = info
        except Exception as e:
            logger.debug(f"获取 {code} 信息失败：{e}")
    
    logger.info(f"获取到 {len(basic_info)} 只股票的基本信息")
    
    # 3. 运行策略
    logger.info("\n[3/5] 运行选股策略...")
    
    # 策略 1: 多因子选股
    strategy1 = MultiFactorStrategy()
    strategy1.set_params({'top_n': 10})
    result1 = strategy1.select(
        stock_data=pd.DataFrame(),
        basic_info=basic_info
    )
    logger.info(f"多因子策略选中 {len(result1.stocks)} 只股票")
    
    # 策略 2: 行业龙头股
    strategy2 = IndustryLeaderStrategy()
    result2 = strategy2.select(
        stock_data=pd.DataFrame(),
        basic_info=basic_info
    )
    logger.info(f"行业龙头策略选中 {len(result2.stocks)} 只股票")
    
    # 4. 风控过滤
    logger.info("\n[4/5] 风控过滤...")
    
    # 合并结果
    all_stocks = result1.stocks + result2.stocks
    
    # 去重
    seen = set()
    unique_stocks = []
    for stock in all_stocks:
        if stock['code'] not in seen:
            seen.add(stock['code'])
            unique_stocks.append(stock)
    
    # 风控过滤
    filtered_stocks = risk_manager.filter_stocks(unique_stocks)
    logger.info(f"风控过滤后：{len(filtered_stocks)} 只股票")
    
    # 5. 生成报告
    logger.info("\n[5/5] 生成报告...")
    
    output_dir = PROCESSED_DATA_DIR / "weekly"
    output_dir.mkdir(exist_ok=True)
    
    # 保存 CSV
    if filtered_stocks:
        df = pd.DataFrame(filtered_stocks)
        csv_file = output_dir / f"selection_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"选股结果已保存到：{csv_file}")
        
        # 生成 Markdown 报告
        report_file = output_dir / f"report_{datetime.now().strftime('%Y%m%d')}.md"
        generate_report(filtered_stocks, report_file)
        logger.info(f"报告已保存到：{report_file}")
    else:
        logger.warning("未选中股票")
    
    logger.info("\n" + "=" * 60)
    logger.info("每周选股完成！")
    logger.info("=" * 60)
    
    return filtered_stocks


def generate_report(stocks: list, output_file: Path):
    """生成 Markdown 报告"""
    date = datetime.now().strftime('%Y-%m-%d')
    
    content = f"""# 选股周报

**生成时间**: {date}

---

## 推荐股票池

共推荐 {len(stocks)} 只股票

| 代码 | 名称 | 得分 | 选股理由 |
|------|------|------|----------|
"""
    
    for stock in stocks[:10]:  # 只显示前 10 只
        content += f"| {stock['code']} | {stock.get('name', '')} | {stock['score']:.1f} | {stock['reason'][:50]}... |\n"
    
    content += f"""

---

## 使用说明

1. **买入时机**: 下周一开盘执行
2. **持有周期**: 1 个月
3. **止损线**: -8%
4. **止盈线**: +15%
5. **仓位建议**: 单只股票不超过 30%

---

## 风险提示

> 本系统仅供参考，不构成投资建议。股市有风险，投资需谨慎。

---

*Stock Selector v0.2.0 | 报告生成时间：{date}*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    setup_logger()
    run_weekly_selection()
