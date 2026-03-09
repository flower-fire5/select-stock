"""
行业龙头股策略

策略逻辑：
1. 分析行业动量，选出强势行业
2. 在每个强势行业中识别龙头股
3. 买入龙头股
"""
import pandas as pd
from typing import Dict, List
from loguru import logger

from .base import BaseStrategy, StockSelectionResult
from utils.stock_screener import LeaderStockIdentifier


class IndustryLeaderStrategy(BaseStrategy):
    """行业龙头股策略"""
    
    def __init__(self):
        super().__init__(
            name="行业龙头股策略",
            description="选择强势行业中的龙头股"
        )
        self.leader_identifier = LeaderStockIdentifier()
        self.top_industries = 5  # 前 5 个行业
        self.leaders_per_industry = 2  # 每个行业选 2 只龙头
    
    def get_params(self) -> Dict:
        return {
            'top_industries': self.top_industries,
            'leaders_per_industry': self.leaders_per_industry
        }
    
    def select(self,
               stock_data: pd.DataFrame,
               industry_data: pd.DataFrame = None,
               basic_info: Dict = None,
               date: str = None) -> StockSelectionResult:
        """选股逻辑"""
        result = StockSelectionResult()
        result.reason = "行业龙头股策略 - 强势行业 + 龙头股"
        
        if basic_info is None:
            return result
        
        # 简化：直接从基本 info 中选市值最大的几只股票
        stocks = []
        for code, info in basic_info.items():
            stocks.append({
                'code': code,
                'name': info.get('name', ''),
                'industry': info.get('industry', '')
            })
        
        # 识别龙头股
        leaders = self.leader_identifier.get_top_leaders(
            stocks=stocks,
            basic_info=basic_info,
            top_n=self.leaders_per_industry * self.top_industries
        )
        
        for leader in leaders:
            result.add_stock(
                code=leader['code'],
                name=leader.get('name', ''),
                score=leader['leader_score'],
                reason=f"龙头股得分：{leader['leader_score']:.1f}",
                metrics={'leader_score': leader['leader_score']}
            )
        
        result.industry = "多行业"
        result.score = sum(l['leader_score'] for l in leaders) / len(leaders) if leaders else 0
        
        return result
