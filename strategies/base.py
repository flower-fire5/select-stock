"""
策略基类 - 所有选股策略的父类
"""
from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd
from loguru import logger


class StockSelectionResult:
    """选股结果"""
    
    def __init__(self):
        self.stocks: List[Dict] = []  # 选中的股票列表
        self.reason: str = ""  # 选股理由
        self.industry: str = ""  # 所属行业
        self.score: float = 0.0  # 综合得分
        self.metrics: Dict = {}  # 各项指标
    
    def add_stock(self, code: str, name: str, score: float, reason: str, metrics: Dict = None):
        """添加选中股票"""
        self.stocks.append({
            'code': code,
            'name': name,
            'score': score,
            'reason': reason,
            'metrics': metrics or {}
        })
    
    def to_dataframe(self) -> pd.DataFrame:
        """转换为 DataFrame"""
        if not self.stocks:
            return pd.DataFrame()
        return pd.DataFrame(self.stocks)


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logger
        self.logger.info(f"策略初始化：{name}")
    
    @abstractmethod
    def select(self, 
               stock_data: pd.DataFrame, 
               industry_data: pd.DataFrame = None,
               basic_info: Dict = None,
               date: str = None) -> StockSelectionResult:
        """
        选股核心方法
        
        Args:
            stock_data: 股票日线数据
            industry_data: 行业数据
            basic_info: 股票基本信息
            date: 选股日期
        
        Returns:
            StockSelectionResult: 选股结果
        """
        pass
    
    @abstractmethod
    def get_params(self) -> Dict:
        """获取策略参数"""
        pass
    
    def set_params(self, params: Dict):
        """设置策略参数"""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证数据是否满足策略要求"""
        if stock_data.empty:
            self.logger.warning("数据为空")
            return False
        if len(stock_data) < 60:
            self.logger.warning(f"数据量不足 60 条，当前：{len(stock_data)}")
            return False
        return True
