"""
系统配置文件
"""
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
RAW_DATA_DIR.mkdir(exist_ok=True)
PROCESSED_DATA_DIR.mkdir(exist_ok=True)

# 数据源配置
DATA_SOURCE = "akshare"  # akshare / tushare / joinquant

# 市场配置
MARKET = "A"  # A 股
CURRENCY = "CNY"

# 回测配置
DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = "2026-01-01"
INITIAL_CAPITAL = 1000000  # 初始资金 100 万

# 风控配置
MAX_POSITION_PER_STOCK = 0.30  # 单只股票最大仓位 30%
MAX_POSITION_PER_INDUSTRY = 0.50  # 单一行业最大仓位 50%
STOP_LOSS = 0.08  # 止损线 8%
TAKE_PROFIT = 0.15  # 止盈线 15%

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "logs" / "stock_selector.log"

# 行业分类标准
INDUSTRY_STANDARD = "sw"  # 申万行业分类
