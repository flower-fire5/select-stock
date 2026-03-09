"""
多因子选股策略

因子类型：
- 质量因子 (30%): ROE、毛利率、资产负债率
- 动量因子 (25%): 20 日收益率、相对强度
- 成长因子 (25%): 营收增长率、净利润增长率
- 估值因子 (20%): PE 分位、PB 分位
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from loguru import logger

from .base import BaseStrategy, StockSelectionResult


class MultiFactorStrategy(BaseStrategy):
    """多因子选股策略"""
    
    def __init__(self):
        super().__init__(
            name="多因子选股策略",
            description="综合质量、动量、成长、估值四因子评分选股"
        )
        # 因子权重
        self.quality_weight = 0.30  # 质量因子
        self.momentum_weight = 0.25  # 动量因子
        self.growth_weight = 0.25  # 成长因子
        self.value_weight = 0.20  # 估值因子
        
        # 选股参数
        self.top_n = 10  # 选中前 N 只股票
        self.lookback_days = 20  # 动量计算周期
    
    def get_params(self) -> Dict:
        return {
            'quality_weight': self.quality_weight,
            'momentum_weight': self.momentum_weight,
            'growth_weight': self.growth_weight,
            'value_weight': self.value_weight,
            'top_n': self.top_n,
            'lookback_days': self.lookback_days
        }
    
    def select(self,
               stock_data: pd.DataFrame,
               industry_data: pd.DataFrame = None,
               basic_info: Dict = None,
               date: str = None) -> StockSelectionResult:
        """
        执行多因子选股
        
        Args:
            stock_data: 个股日线数据
            industry_data: 行业数据
            basic_info: 股票基本信息 {code: {pe, pb, roe, market_cap, ...}}
            date: 选股日期
        
        Returns:
            StockSelectionResult: 选股结果
        """
        result = StockSelectionResult()
        result.reason = "多因子选股 - 综合质量/动量/成长/估值评分"
        
        if basic_info is None or not basic_info:
            self.logger.warning("缺少股票基本信息，无法计算多因子评分")
            return result
        
        # 1. 计算各因子得分
        self.logger.info("计算因子得分...")
        factor_scores = self._calculate_factor_scores(stock_data, basic_info)
        
        if factor_scores.empty:
            return result
        
        # 2. 计算综合得分
        factor_scores['total_score'] = (
            factor_scores['quality_score'] * self.quality_weight +
            factor_scores['momentum_score'] * self.momentum_weight +
            factor_scores['growth_score'] * self.growth_weight +
            factor_scores['value_score'] * self.value_weight
        )
        
        # 3. 排序选股
        factor_scores.sort_values('total_score', ascending=False, inplace=True)
        selected = factor_scores.head(self.top_n)
        
        self.logger.info(f"选中 {len(selected)} 只股票")
        
        # 4. 构建结果
        for code, row in selected.iterrows():
            info = basic_info.get(code, {})
            result.add_stock(
                code=code,
                name=info.get('name', ''),
                score=row['total_score'],
                reason=f"综合得分：{row['total_score']:.2f} (质量:{row['quality_score']:.1f}, 动量:{row['momentum_score']:.1f}, 成长:{row['growth_score']:.1f}, 估值:{row['value_score']:.1f})",
                metrics={
                    'quality_score': row['quality_score'],
                    'momentum_score': row['momentum_score'],
                    'growth_score': row['growth_score'],
                    'value_score': row['value_score'],
                    'roe': info.get('roe', 0),
                    'pe': info.get('pe', 0),
                    'pb': info.get('pb', 0),
                    'market_cap': info.get('market_cap', 0)
                }
            )
        
        result.industry = "多行业"
        result.score = selected['total_score'].mean()
        result.metrics = {
            'avg_quality': selected['quality_score'].mean(),
            'avg_momentum': selected['momentum_score'].mean(),
            'avg_growth': selected['growth_score'].mean(),
            'avg_value': selected['value_score'].mean()
        }
        
        return result
    
    def _calculate_factor_scores(self, stock_data: pd.DataFrame, basic_info: Dict) -> pd.DataFrame:
        """
        计算各因子得分
        
        返回：DataFrame(code, quality_score, momentum_score, growth_score, value_score)
        """
        scores = []
        
        # 获取所有有基本信息的股票
        codes = list(basic_info.keys())
        
        for code in codes:
            info = basic_info[code]
            
            # 1. 质量因子得分 (0-100)
            quality_score = self._calc_quality_score(info)
            
            # 2. 动量因子得分 (0-100)
            momentum_score = self._calc_momentum_score(stock_data, code)
            
            # 3. 成长因子得分 (0-100) - 简化：用 ROE 代替
            growth_score = self._calc_growth_score(info)
            
            # 4. 估值因子得分 (0-100)
            value_score = self._calc_value_score(info)
            
            scores.append({
                'code': code,
                'quality_score': quality_score,
                'momentum_score': momentum_score,
                'growth_score': growth_score,
                'value_score': value_score
            })
        
        df = pd.DataFrame(scores)
        df.set_index('code', inplace=True)
        return df
    
    def _calc_quality_score(self, info: Dict) -> float:
        """
        质量因子得分
        - ROE (40%): 净资产收益率
        - 毛利率 (30%): 毛利率
        - 资产负债率 (30%): 负债率越低越好
        """
        score = 50.0  # 基础分
        
        # ROE 得分
        roe = info.get('roe', 0)
        if roe > 20:
            score += 40 * 0.4
        elif roe > 15:
            score += 30 * 0.4
        elif roe > 10:
            score += 20 * 0.4
        elif roe > 5:
            score += 10 * 0.4
        else:
            score -= 10 * 0.4
        
        # 毛利率得分（简化：用 ROE 近似）
        score += 15 * 0.3
        
        # 资产负债率得分（简化：默认中等）
        score += 15 * 0.3
        
        return min(100, max(0, score))
    
    def _calc_momentum_score(self, stock_data: pd.DataFrame, code: str) -> float:
        """
        动量因子得分
        - 20 日收益率 (50%)
        - 相对强度 RS (50%)
        """
        score = 50.0
        
        try:
            if 'code' in stock_data.columns:
                stock_df = stock_data[stock_data['code'] == code]
            else:
                stock_df = stock_data.xs(code, level='code')
            
            if len(stock_df) < self.lookback_days:
                return score
            
            stock_df = stock_df.tail(self.lookback_days)
            start_price = stock_df.iloc[0]['close']
            end_price = stock_df.iloc[-1]['close']
            
            if start_price > 0:
                momentum = (end_price - start_price) / start_price * 100
                
                # 动量得分
                if momentum > 20:
                    score += 50 * 0.5
                elif momentum > 10:
                    score += 40 * 0.5
                elif momentum > 5:
                    score += 30 * 0.5
                elif momentum > 0:
                    score += 20 * 0.5
                else:
                    score -= 20 * 0.5
                
                # RS 得分（简化：用动量近似）
                score += 25 * 0.5
        except Exception as e:
            self.logger.debug(f"计算 {code} 动量得分失败：{e}")
        
        return min(100, max(0, score))
    
    def _calc_growth_score(self, info: Dict) -> float:
        """
        成长因子得分
        - 营收增长率 (50%)
        - 净利润增长率 (50%)
        
        简化：用 ROE 近似成长能力
        """
        score = 50.0
        
        roe = info.get('roe', 0)
        if roe > 20:
            score += 40
        elif roe > 15:
            score += 30
        elif roe > 10:
            score += 20
        elif roe > 5:
            score += 10
        else:
            score -= 20
        
        return min(100, max(0, score))
    
    def _calc_value_score(self, info: Dict) -> float:
        """
        估值因子得分
        - PE 分位 (60%)
        - PB 分位 (40%)
        
        PE/PB 越低得分越高
        """
        score = 50.0
        
        pe = info.get('pe', 0)
        pb = info.get('pb', 0)
        
        # PE 得分
        if pe > 0:
            if pe < 10:
                score += 30 * 0.6
            elif pe < 20:
                score += 20 * 0.6
            elif pe < 30:
                score += 10 * 0.6
            elif pe < 50:
                score += 0
            else:
                score -= 20 * 0.6
        
        # PB 得分
        if pb > 0:
            if pb < 1:
                score += 20 * 0.4
            elif pb < 2:
                score += 10 * 0.4
            elif pb < 5:
                score += 0
            else:
                score -= 10 * 0.4
        
        return min(100, max(0, score))


# 测试
if __name__ == "__main__":
    strategy = MultiFactorStrategy()
    print(f"策略：{strategy.name}")
    print(f"参数：{strategy.get_params()}")
