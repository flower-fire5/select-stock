#!/usr/bin/env python3
"""
选股系统 - 演示版 (使用模拟数据)

功能:
1. 使用模拟股票数据演示选股流程
2. 多因子选股策略
3. 输出选股结果

用法:
    python3 scripts/demo_pick.py
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from strategies import SimpleFactorStrategy, IndustryLeaderStrategy

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

# 模拟股票数据 (真实场景下从 AkShare 获取)
SIMULATED_STOCKS = {
    '000001': {'name': '平安银行', 'pe': 5.2, 'pb': 0.6, 'roe': 11.5, 'market_cap': 800e8},
    '600036': {'name': '招商银行', 'pe': 6.8, 'pb': 0.9, 'roe': 15.2, 'market_cap': 1200e8},
    '000858': {'name': '五粮液', 'pe': 18.5, 'pb': 4.2, 'roe': 22.3, 'market_cap': 6500e8},
    '600519': {'name': '贵州茅台', 'pe': 28.5, 'pb': 8.5, 'roe': 30.2, 'market_cap': 22000e8},
    '000651': {'name': '格力电器', 'pe': 8.2, 'pb': 2.1, 'roe': 18.5, 'market_cap': 3500e8},
    '601318': {'name': '中国平安', 'pe': 9.5, 'pb': 1.2, 'roe': 16.8, 'market_cap': 9000e8},
    '600030': {'name': '中信证券', 'pe': 12.3, 'pb': 1.5, 'roe': 10.2, 'market_cap': 2800e8},
    '002415': {'name': '海康威视', 'pe': 15.8, 'pb': 3.8, 'roe': 20.5, 'market_cap': 3200e8},
    '300750': {'name': '宁德时代', 'pe': 35.2, 'pb': 6.5, 'roe': 18.2, 'market_cap': 8500e8},
    '601888': {'name': '中国中免', 'pe': 25.6, 'pb': 5.2, 'roe': 22.8, 'market_cap': 4200e8},
    '000333': {'name': '美的集团', 'pe': 12.5, 'pb': 3.2, 'roe': 24.5, 'market_cap': 5500e8},
    '600276': {'name': '恒瑞医药', 'pe': 45.2, 'pb': 6.8, 'roe': 15.8, 'market_cap': 2800e8},
    '002594': {'name': '比亚迪', 'pe': 28.8, 'pb': 5.5, 'roe': 18.5, 'market_cap': 7200e8},
    '601012': {'name': '隆基绿能', 'pe': 18.5, 'pb': 3.8, 'roe': 22.5, 'market_cap': 2500e8},
    '300059': {'name': '东方财富', 'pe': 22.5, 'pb': 3.5, 'roe': 12.8, 'market_cap': 3000e8},
}

def main():
    logger.info("=" * 70)
    logger.info("Stock Selector - 智能选股系统 (演示版)")
    logger.info(f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # ========== 1. 初始化 ==========
    logger.info("\n【1/4】初始化模块...")
    logger.info("✅ 策略模块加载完成")
    
    # ========== 2. 加载模拟数据 ==========
    logger.info("\n【2/4】加载股票数据...")
    logger.info(f"股票池数量：{len(SIMULATED_STOCKS)} 只")
    logger.info("数据来源：模拟数据 (真实场景使用 AkShare)")
    
    # ========== 3. 运行选股策略 ==========
    logger.info("\n【3/4】运行选股策略...")
    
    # 策略 1: 简化多因子选股
    logger.info("\n>>> 策略 1: 简化多因子选股策略")
    logger.info("   评分维度：ROE(40%) + PE(25%) + PB(15%) + 市值 (20%)")
    
    strategy1 = SimpleFactorStrategy()
    strategy1.set_params({'top_n': 5})
    result1 = strategy1.select(basic_info=SIMULATED_STOCKS)
    
    if result1.stocks:
        logger.info(f"✅ 多因子策略选中 {len(result1.stocks)} 只股票")
        for stock in result1.stocks:
            logger.info(f"   {stock['code']} {stock['name']}: 得分 {stock['score']:.1f}")
    
    # 策略 2: 行业龙头股
    logger.info("\n>>> 策略 2: 行业龙头股策略")
    logger.info("   选股标准：市值 + 营收 + 净利润 + 机构持仓")
    
    strategy2 = IndustryLeaderStrategy()
    result2 = strategy2.select(
        stock_data=pd.DataFrame(),
        basic_info=SIMULATED_STOCKS
    )
    
    if result2.stocks:
        logger.info(f"✅ 行业龙头策略选中 {len(result2.stocks)} 只股票")
        for stock in result2.stocks:
            logger.info(f"   {stock['code']} {stock['name']}: 得分 {stock['score']:.1f}")
    
    # ========== 4. 合并结果并输出 ==========
    logger.info("\n【4/4】生成选股报告...")
    
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
        csv_file = output_dir / f"demo_selection_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        md_file = output_dir / f"demo_report_{timestamp}.md"
        generate_report(unique_stocks, md_file)
        
        # 打印结果表格
        logger.info("\n" + "=" * 70)
        logger.info("📊 选股结果")
        logger.info("=" * 70)
        
        for i, stock in enumerate(unique_stocks, 1):
            metrics = stock.get('metrics', {})
            logger.info(f"\n{i}. {stock['code']} - {stock['name']}")
            logger.info(f"   综合得分：{stock['score']:.1f}")
            logger.info(f"   ROE: {metrics.get('roe', 'N/A')}%")
            logger.info(f"   PE: {metrics.get('pe', 'N/A')}")
            logger.info(f"   PB: {metrics.get('pb', 'N/A')}")
            logger.info(f"   市值：{metrics.get('market_cap', 0)/100e8:.0f}亿")
            logger.info(f"   选股理由：{stock['reason'][:60]}...")
        
        logger.info("\n" + "=" * 70)
        logger.info(f"✅ 结果已保存到:")
        logger.info(f"   📁 CSV: {csv_file}")
        logger.info(f"   📄 报告：{md_file}")
        logger.info("=" * 70)
    else:
        logger.warning("⚠️ 未选中股票")
    
    logger.info("\n✅ 选股完成！")
    logger.info("\n💡 提示：真实场景使用 python3 scripts/stock_pick.py 获取真实数据")

def generate_report(stocks: list, output_file: Path):
    """生成 Markdown 报告"""
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = f"""# 选股报告 (演示版)

**生成时间**: {date}

---

## 推荐股票池

共推荐 {len(stocks)} 只股票

| 排名 | 代码 | 名称 | 得分 | ROE | PE | PB | 市值 (亿) |
|------|------|------|------|-----|----|----|-----------|
"""
    
    for i, stock in enumerate(stocks, 1):
        metrics = stock.get('metrics', {})
        content += f"| {i} | {stock['code']} | {stock.get('name', '')} | {stock['score']:.1f} | "
        content += f"{metrics.get('roe', 'N/A')}% | {metrics.get('pe', 'N/A')} | "
        content += f"{metrics.get('pb', 'N/A')} | {metrics.get('market_cap', 0)/100e8:.0f} |\n"
    
    content += f"""

---

## 使用说明

1. **买入时机**: 下周一开盘执行
2. **持有周期**: 1 个月
3. **止损线**: -8%
4. **止盈线**: +15%
5. **仓位建议**: 单只股票不超过 30%

---

## 策略说明

### 简化多因子策略
- **ROE 得分 (40%)**: 净资产收益率，越高越好
- **PE 得分 (25%)**: 市盈率，越低越好
- **PB 得分 (15%)**: 市净率，越低越好
- **市值得分 (20%)**: 总市值，越大越好

### 行业龙头股策略
- 市值行业领先
- 营收/净利润行业前 3
- 机构持仓比例高
- 行业指数权重股

---

## 风险提示

> ⚠️ 本系统仅供参考，不构成投资建议。
> 
> 📉 股市有风险，投资需谨慎。
> 
> 💡 演示数据仅供测试，真实场景请使用 AkShare 获取实时数据。

---

*Stock Selector v0.3.0 | 报告生成时间：{date}*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
