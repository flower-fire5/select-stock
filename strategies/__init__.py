"""
选股策略包
"""
from .base import BaseStrategy, StockSelectionResult
from .industry_momentum import IndustryMomentumStrategy
from .multi_factor import MultiFactorStrategy
from .industry_leader import IndustryLeaderStrategy
from .simple_factor import SimpleFactorStrategy

__all__ = [
    'BaseStrategy',
    'StockSelectionResult',
    'IndustryMomentumStrategy',
    'MultiFactorStrategy',
    'IndustryLeaderStrategy',
    'SimpleFactorStrategy'
]
