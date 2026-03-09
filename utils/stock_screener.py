"""
龙头股识别模块
"""
import pandas as pd
from typing import Dict, List
from loguru import logger


class LeaderStockIdentifier:
    """龙头股识别器"""
    
    def __init__(self):
        self.logger = logger
        # 龙头股评分权重
        self.weights = {
            'market_cap': 0.25,      # 市值
            'revenue': 0.20,         # 营收
            'profit': 0.20,          # 净利润
            'institution_hold': 0.15,  # 机构持仓
            'analyst_rating': 0.10,   # 分析师评级
            'brand': 0.10            # 品牌/技术壁垒
        }
    
    def identify(self, 
                 stocks: List[Dict],
                 industry: str = None,
                 basic_info: Dict = None) -> List[Dict]:
        """
        识别龙头股
        
        Args:
            stocks: 股票列表 [{code, name, ...}]
            industry: 所属行业
            basic_info: 股票基本信息
        
        Returns:
            List[Dict]: 龙头股列表（已评分排序）
        """
        if not stocks:
            return []
        
        self.logger.info(f"识别 {industry or '全市场'} 龙头股...")
        
        scored_stocks = []
        
        for stock in stocks:
            code = stock.get('code')
            if not code:
                continue
            
            info = basic_info.get(code, {}) if basic_info else {}
            
            # 计算龙头股得分
            score = self._calculate_leader_score(stock, info)
            
            scored_stocks.append({
                **stock,
                'leader_score': score,
                'is_leader': score >= 70  # 得分>=70 视为龙头
            })
        
        # 按得分排序
        scored_stocks.sort(key=lambda x: x['leader_score'], reverse=True)
        
        leaders = [s for s in scored_stocks if s['is_leader']]
        self.logger.info(f"识别到 {len(leaders)} 只龙头股")
        
        return leaders
    
    def _calculate_leader_score(self, stock: Dict, info: Dict) -> float:
        """
        计算龙头股得分 (0-100)
        """
        score = 50.0  # 基础分
        
        # 1. 市值得分 (25%)
        market_cap = info.get('market_cap', 0)
        if market_cap > 2000e8:  # >2000 亿
            score += 25 * self.weights['market_cap'] * 4
        elif market_cap > 1000e8:
            score += 20 * self.weights['market_cap'] * 4
        elif market_cap > 500e8:
            score += 15 * self.weights['market_cap'] * 4
        elif market_cap > 100e8:
            score += 10 * self.weights['market_cap'] * 4
        
        # 2. 营收得分 (20%) - 简化：用市值近似
        if market_cap > 1000e8:
            score += 20 * self.weights['revenue'] * 4
        elif market_cap > 500e8:
            score += 15 * self.weights['revenue'] * 4
        elif market_cap > 100e8:
            score += 10 * self.weights['revenue'] * 4
        
        # 3. 净利润得分 (20%) - 简化：用 ROE 近似
        roe = info.get('roe', 0)
        if roe > 20:
            score += 20 * self.weights['profit'] * 4
        elif roe > 15:
            score += 15 * self.weights['profit'] * 4
        elif roe > 10:
            score += 10 * self.weights['profit'] * 4
        
        # 4. 机构持仓得分 (15%) - 简化：默认中等
        score += 12 * self.weights['institution_hold'] * 4
        
        # 5. 分析师评级得分 (10%) - 简化：默认有评级
        score += 15 * self.weights['analyst_rating'] * 4
        
        # 6. 品牌/技术壁垒得分 (10%) - 简化：默认中等
        score += 12 * self.weights['brand'] * 4
        
        return min(100, max(0, score))
    
    def get_top_leaders(self, 
                        stocks: List[Dict], 
                        industry: str = None,
                        basic_info: Dict = None,
                        top_n: int = 3) -> List[Dict]:
        """
        获取前 N 只龙头股
        
        Args:
            stocks: 股票列表
            industry: 所属行业
            basic_info: 基本信息
            top_n: 前 N 只
        
        Returns:
            List[Dict]: 前 N 只龙头股
        """
        leaders = self.identify(stocks, industry, basic_info)
        return leaders[:top_n]
