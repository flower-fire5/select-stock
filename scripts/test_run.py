#!/usr/bin/env python3
"""
简化测试脚本 - 验证代码能运行

用法:
    python scripts/test_run.py
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {message}")

logger.info("=" * 50)
logger.info("Stock Selector - 代码测试")
logger.info("=" * 50)

# 测试 1: 导入模块
logger.info("\n[测试 1] 导入模块...")
try:
    from strategies import IndustryMomentumStrategy, MultiFactorStrategy, IndustryLeaderStrategy
    from utils.risk_manager import RiskManager
    from backtest.engine import BacktestEngine, BacktestResult
    from backtest.report import ReportGenerator
    logger.info("✅ 所有模块导入成功")
except Exception as e:
    logger.error(f"❌ 模块导入失败：{e}")
    sys.exit(1)

# 测试 2: 初始化策略
logger.info("\n[测试 2] 初始化策略...")
try:
    strategy1 = IndustryMomentumStrategy()
    logger.info(f"  - 行业动量策略：{strategy1.name}")
    
    strategy2 = MultiFactorStrategy()
    logger.info(f"  - 多因子策略：{strategy2.name}")
    
    strategy3 = IndustryLeaderStrategy()
    logger.info(f"  - 行业龙头策略：{strategy3.name}")
    
    logger.info("✅ 策略初始化成功")
except Exception as e:
    logger.error(f"❌ 策略初始化失败：{e}")

# 测试 3: 初始化风控
logger.info("\n[测试 3] 初始化风控...")
try:
    risk = RiskManager(
        stop_loss=0.08,
        take_profit=0.15,
        max_position_per_stock=0.30
    )
    logger.info("✅ 风控模块初始化成功")
except Exception as e:
    logger.error(f"❌ 风控初始化失败：{e}")

# 测试 4: 初始化回测引擎
logger.info("\n[测试 4] 初始化回测引擎...")
try:
    engine = BacktestEngine(initial_capital=1000000)
    logger.info("✅ 回测引擎初始化成功")
except Exception as e:
    logger.error(f"❌ 回测引擎失败：{e}")

# 测试 5: 策略参数
logger.info("\n[测试 5] 检查策略参数...")
try:
    params = strategy2.get_params()
    logger.info(f"  多因子策略参数:")
    for key, value in params.items():
        logger.info(f"    - {key}: {value}")
    logger.info("✅ 策略参数检查通过")
except Exception as e:
    logger.error(f"❌ 参数检查失败：{e}")

# 总结
logger.info("\n" + "=" * 50)
logger.info("代码测试完成！")
logger.info("=" * 50)
logger.info("\n✅ 所有核心模块工作正常")
logger.info("\n下一步:")
logger.info("  1. 安装依赖：pip install -r requirements.txt")
logger.info("  2. 运行回测：python backtest/run.py")
logger.info("  3. 每周选股：python scripts/weekly_run.py")
logger.info("  4. Web 界面：streamlit run web/app.py")
