"""
简化多因子选股策略

基于基本面的简单打分策略，不依赖历史行情数据
"""
import pandas as pd
from typing import Dict
from loguru import logger

from .base import BaseStrategy, StockSelectionResult


class SimpleFactorStrategy(BaseStrategy):
    """简化多因子策略"""
    
    def __init__(self):
        super().__init__(
            name="简化多因子策略",
            description="基于 PE/PB/ROE/市值 的简单打分策略"
        )
        self.top_n = 5
    
    def get_params(self) -> Dict:
        return {'top_n': self.top_n}
    
    def select(self,
               stock_data: pd.DataFrame = None,
               industry_data: pd.DataFrame = None,
               basic_info: Dict = None,
               date: str = None) -> StockSelectionResult:
        """
        选股逻辑：
        1. ROE 越高越好 (40 分)
        2. PE 越低越好 (25 分)
        3. PB 越低越好 (15 分)
        4. 市值越大越好 (20 分)
        """
        result = StockSelectionResult()
        result.reason = "简化多因子策略 - ROE+PE+PB+ 市值综合评分"
        
        if not basic_info:
            logger.warning("缺少基本信息，无法选股")
            return result
        
        scores = []
        
        for code, info in basic_info.items():
            pe = info.get('pe', 0) or 0
            pb = info.get('pb', 0) or 0
            roe = info.get('roe', 0) or 0
            market_cap = info.get('market_cap', 0) or 0
            
            # ROE 得分 (0-40)
            if roe > 20:
                roe_score = 40
            elif roe > 15:
                roe_score = 35
            elif roe > 10:
                roe_score = 30
            elif roe > 5:
                roe_score = 20
            else:
                roe_score = 10
            
            # PE 得分 (0-25) - 越低越好
            if pe > 0 and pe < 10:
                pe_score = 25
            elif pe < 20:
                pe_score = 20
            elif pe < 30:
                pe_score = 15
            elif pe < 50:
                pe_score = 10
            else:
                pe_score = 5
            
            # PB 得分 (0-15) - 越低越好
            if pb > 0 and pb < 1:
                pb_score = 15
            elif pb < 2:
                pb_score = 12
            elif pb < 5:
                pb_score = 8
            else:
                pb_score = 5
            
            # 市值得分 (0-20) - 越大越好
            if market_cap > 5000e8:
                cap_score = 20
            elif market_cap > 1000e8:
                cap_score = 15
            elif market_cap > 500e8:
                cap_score = 10
            else:
                cap_score = 5
            
            total_score = roe_score + pe_score + pb_score + cap_score
            
            scores.append({
                'code': code,
                'name': info.get('name', ''),
                'score': total_score,
                'roe': roe,
                'pe': pe,
                'pb': pb,
                'market_cap': market_cap,
                'reason': f"ROE:{roe}%, PE:{pe}, PB:{pb}, 市值:{market_cap/100e8:.0f}亿"
            })
        
        # 排序
        df = pd.DataFrame(scores)
        df.sort_values('score', ascending=False, inplace=True)
        
        # 选中前 N 只
        selected = df.head(self.top_n)
        
        for _, row in selected.iterrows():
            result.add_stock(
                code=row['code'],
                name=row['name'],
                score=row['score'],
                reason=row['reason'],
                metrics={
                    'roe': row['roe'],
                    'pe': row['pe'],
                    'pb': row['pb'],
                    'market_cap': row['market_cap']
                }
            )
        
        result.industry = "多行业"
        result.score = selected['score'].mean() if len(selected) > 0 else 0
        
        logger.info(f"选股完成：选中 {len(result.stocks)} 只股票")
        return result
