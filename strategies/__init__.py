"""
选股策略包
"""
from .base import BaseStrategy, StockSelectionResult
from .industry_momentum import IndustryMomentumStrategy

__all__ = [
    'BaseStrategy',
    'StockSelectionResult',
    'IndustryMomentumStrategy'
]
