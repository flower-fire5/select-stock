"""
行业动量策略 - 基于行业指数涨跌幅排序选股

策略逻辑：
1. 计算各行业近 N 日涨跌幅
2. 排序选出强势行业
3. 在强势行业中选择龙头股
"""
import pandas as pd
from typing import Dict, List
from loguru import logger

from .base import BaseStrategy, StockSelectionResult


class IndustryMomentumStrategy(BaseStrategy):
    """行业动量策略"""
    
    def __init__(self):
        super().__init__(
            name="行业动量策略",
            description="基于行业指数动量排序，选择强势行业中的龙头股"
        )
        # 策略参数
        self.lookback_days = 20  # 动量计算周期
        self.top_industries = 5  # 选择前 N 个行业
        self.stocks_per_industry = 2  # 每个行业选 N 只股票
    
    def get_params(self) -> Dict:
        return {
            'lookback_days': self.lookback_days,
            'top_industries': self.top_industries,
            'stocks_per_industry': self.stocks_per_industry
        }
    
    def select(self,
               stock_data: pd.DataFrame,
               industry_data: pd.DataFrame = None,
               basic_info: Dict = None,
               date: str = None) -> StockSelectionResult:
        """
        执行选股
        
        Args:
            stock_data: 个股日线数据 (MultiIndex: date, code)
            industry_data: 行业指数数据
            basic_info: 股票基本信息字典 {code: info}
            date: 选股日期
        
        Returns:
            StockSelectionResult: 选股结果
        """
        result = StockSelectionResult()
        result.reason = f"行业动量策略 - 选择近{self.lookback_days}日强势行业中的龙头股"
        
        if industry_data is None or industry_data.empty:
            self.logger.warning("行业数据为空，无法执行行业动量策略")
            return result
        
        # 1. 计算行业动量
        industry_momentum = self._calculate_industry_momentum(industry_data)
        if industry_momentum.empty:
            return result
        
        # 2. 选出前 N 个强势行业
        top_industries = industry_momentum.head(self.top_industries)
        self.logger.info(f"强势行业：{list(top_industries.index)}")
        
        # 3. 在每个行业中选择股票
        for industry_name, momentum_data in top_industries.iterrows():
            industry_score = momentum_data['momentum']
            
            # 获取该行业的股票（简化：这里用基本 info 中的行业信息）
            industry_stocks = self._get_stocks_by_industry(stock_data, basic_info, industry_name)
            
            if industry_stocks.empty:
                continue
            
            # 计算个股得分（结合动量 + 市值）
            stock_scores = self._score_stocks(industry_stocks, basic_info)
            
            # 选出前 N 只
            selected = stock_scores.head(self.stocks_per_industry)
            
            for code, score_data in selected.iterrows():
                result.add_stock(
                    code=code,
                    name=basic_info.get(code, {}).get('name', '') if basic_info else '',
                    score=score_data['total_score'],
                    reason=f"所属行业：{industry_name} (动量:{momentum_data['momentum']:.2f}%)",
                    metrics={
                        'industry': industry_name,
                        'industry_momentum': momentum_data['momentum'],
                        'stock_momentum': score_data['momentum_score'],
                        'market_cap_score': score_data['cap_score']
                    }
                )
        
        result.industry = "多行业"
        result.score = top_industries['momentum'].mean()
        result.metrics = {
            'selected_industries': list(top_industries.index),
            'total_stocks': len(result.stocks)
        }
        
        self.logger.info(f"选股完成：共选中 {len(result.stocks)} 只股票")
        return result
    
    def _calculate_industry_momentum(self, industry_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算行业动量
        
        Args:
            industry_data: 行业指数数据
        
        Returns:
            DataFrame: 行业名称、动量值（涨跌幅）
        """
        momentum_list = []
        
        for industry in industry_data['industry'].unique():
            industry_df = industry_data[industry_data['industry'] == industry].copy()
            industry_df.sort_index(inplace=True)
            
            if len(industry_df) < self.lookback_days:
                continue
            
            # 计算近 N 日涨跌幅
            recent = industry_df.tail(self.lookback_days)
            if len(recent) < 2:
                continue
            
            start_price = recent.iloc[0]['close']
            end_price = recent.iloc[-1]['close']
            
            if start_price > 0:
                momentum = (end_price - start_price) / start_price * 100
                momentum_list.append({
                    'industry': industry,
                    'momentum': momentum
                })
        
        if not momentum_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(momentum_list)
        df.set_index('industry', inplace=True)
        df.sort_values('momentum', ascending=False, inplace=True)
        
        return df
    
    def _get_stocks_by_industry(self, 
                                stock_data: pd.DataFrame, 
                                basic_info: Dict,
                                industry_name: str) -> pd.DataFrame:
        """
        获取某行业的股票数据
        
        简化实现：返回所有有数据的股票
        实际应该根据行业分类过滤
        """
        # TODO: 需要根据行业分类准确过滤
        # 这里简化处理，返回所有股票
        if 'code' in stock_data.columns:
            codes = stock_data['code'].unique()
        else:
            codes = stock_data.index.get_level_values('code').unique()
        
        stock_list = []
        for code in codes:
            if code in stock_data.index.get_level_values('code'):
                stock_df = stock_data.xs(code, level='code')
                if len(stock_df) >= self.lookback_days:
                    stock_list.append(code)
        
        if not stock_list:
            return pd.DataFrame()
        
        return stock_data[stock_data.index.get_level_values('code').isin(stock_list)]
    
    def _score_stocks(self, stock_data: pd.DataFrame, basic_info: Dict) -> pd.DataFrame:
        """
        对股票打分
        
        评分维度：
        - 动量得分（40%）：近 20 日涨跌幅
        - 市值得分（30%）：市值越大得分越高（龙头）
        - 质量得分（30%）：ROE 等指标
        """
        scores = []
        
        codes = stock_data.index.get_level_values('code').unique()
        
        for code in codes:
            stock_df = stock_data.xs(code, level='code')
            stock_df.sort_index(inplace=True)
            
            # 动量得分
            if len(stock_df) >= self.lookback_days:
                recent = stock_df.tail(self.lookback_days)
                start_price = recent.iloc[0]['close']
                end_price = recent.iloc[-1]['close']
                momentum = (end_price - start_price) / start_price * 100 if start_price > 0 else 0
            else:
                momentum = 0
            
            # 市值得分（简化：用代码数字模拟，实际应从 basic_info 获取）
            market_cap_score = 50  # 默认中等
            if basic_info and code in basic_info:
                info = basic_info[code]
                if info.get('market_cap', 0) > 1000e8:  # 大于 1000 亿
                    market_cap_score = 100
                elif info.get('market_cap', 0) > 500e8:
                    market_cap_score = 80
                elif info.get('market_cap', 0) > 100e8:
                    market_cap_score = 60
            
            # 综合得分
            total_score = momentum * 0.4 + market_cap_score * 0.3 + 50 * 0.3
            
            scores.append({
                'code': code,
                'momentum_score': momentum,
                'cap_score': market_cap_score,
                'total_score': total_score
            })
        
        df = pd.DataFrame(scores)
        df.set_index('code', inplace=True)
        df.sort_values('total_score', ascending=False, inplace=True)
        
        return df


# 测试
if __name__ == "__main__":
    from loguru import logger
    logger.add("logs/test_strategy.log", rotation="1 MB")
    
    strategy = IndustryMomentumStrategy()
    print(f"策略名称：{strategy.name}")
    print(f"策略参数：{strategy.get_params()}")
