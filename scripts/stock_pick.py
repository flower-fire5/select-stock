#!/usr/bin/env python3
"""
选股系统 - 改良版

功能:
1. 获取真实 A 股数据
2. 多因子选股策略
3. 行业龙头股策略
4. 输出选股结果

用法:
    python3 scripts/stock_pick.py
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from strategies import SimpleFactorStrategy, IndustryLeaderStrategy
from utils.data_loader import DataLoader
from utils.risk_manager import RiskManager

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

def main():
    logger.info("=" * 70)
    logger.info("Stock Selector - 智能选股系统 (改良版)")
    logger.info(f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # ========== 1. 初始化 ==========
    logger.info("\n【1/5】初始化模块...")
    loader = DataLoader()
    risk_manager = RiskManager(
        stop_loss=0.08,
        take_profit=0.15,
        blacklist=['601313']  # 示例黑名单
    )
    
    # ========== 2. 获取股票列表 ==========
    logger.info("\n【2/5】获取 A 股股票列表...")
    stock_list = loader.get_stock_list()
    logger.info(f"全市场股票总数：{len(stock_list)}")
    
    # 简化：取前 50 只股票用于演示
    stock_list = stock_list.head(50)
    logger.info(f"本次处理：前 {len(stock_list)} 只股票")
    
    # ========== 3. 获取基本信息 ==========
    logger.info("\n【3/5】获取股票基本信息 (PE/PB/ROE/市值)...")
    basic_info = {}
    
    for i, (_, row) in enumerate(stock_list.iterrows()):
        code = row['code']
        try:
            info = loader.get_stock_basic_info(code)
            if info:
                basic_info[code] = info
                logger.info(f"  [{i+1}/{len(stock_list)}] {code} {info.get('name', '')}: PE={info.get('pe', 'N/A')}, ROE={info.get('roe', 'N/A')}%")
        except Exception as e:
            logger.debug(f"获取 {code} 信息失败：{e}")
    
    logger.info(f"\n✅ 成功获取 {len(basic_info)} 只股票的基本信息")
    
    if len(basic_info) == 0:
        logger.error("❌ 未获取到任何股票信息，无法继续选股")
        return
    
    # ========== 4. 运行选股策略 ==========
    logger.info("\n【4/5】运行选股策略...")
    
    # 策略 1: 简化多因子选股
    logger.info("\n>>> 策略 1: 简化多因子选股策略")
    logger.info("   评分维度：ROE(40%) + PE(25%) + PB(15%) + 市值 (20%)")
    
    strategy1 = SimpleFactorStrategy()
    strategy1.set_params({'top_n': 5})
    result1 = strategy1.select(
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
    logger.info("   选股标准：市值 + 营收 + 净利润 + 机构持仓")
    
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
    
    # ========== 5. 合并结果并输出 ==========
    logger.info("\n【5/5】生成选股报告...")
    
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
        # 保存结果
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        df = pd.DataFrame(unique_stocks)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = output_dir / f"selection_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        md_file = output_dir / f"report_{timestamp}.md"
        generate_report(unique_stocks, md_file)
        
        # 打印结果表格
        logger.info("\n" + "=" * 70)
        logger.info("选股结果")
        logger.info("=" * 70)
        
        for stock in unique_stocks:
            metrics = stock.get('metrics', {})
            logger.info(f"\n{stock['code']} - {stock['name']}")
            logger.info(f"  综合得分：{stock['score']:.1f}")
            logger.info(f"  ROE: {metrics.get('roe', 'N/A')}%")
            logger.info(f"  PE: {metrics.get('pe', 'N/A')}")
            logger.info(f"  PB: {metrics.get('pb', 'N/A')}")
            logger.info(f"  市值：{metrics.get('market_cap', 0)/100e8:.0f}亿")
            logger.info(f"  选股理由：{stock['reason'][:60]}...")
        
        logger.info("\n" + "=" * 70)
        logger.info(f"✅ 结果已保存到:")
        logger.info(f"   CSV: {csv_file}")
        logger.info(f"   报告：{md_file}")
        logger.info("=" * 70)
    else:
        logger.warning("⚠️ 未选中股票，请检查策略参数或数据源")
    
    logger.info("\n✅ 选股完成！")

def generate_report(stocks: list, output_file: Path):
    """生成 Markdown 报告"""
    date = datetime.now().strftime('%Y-%m-%d')
    
    content = f"""# 选股报告

**生成时间**: {date} {datetime.now().strftime('%H:%M:%S')}

---

## 推荐股票池

共推荐 {len(stocks)} 只股票

| 代码 | 名称 | 得分 | 选股理由 |
|------|------|------|----------|
"""
    
    for stock in stocks:
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

*Stock Selector v0.3.0 | 报告生成时间：{date}*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
