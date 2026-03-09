#!/usr/bin/env python3
"""
策略模块单元测试

运行:
    pytest tests/test_strategies.py -v
"""
import pytest
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.base import BaseStrategy, StockSelectionResult
from strategies.industry_momentum import IndustryMomentumStrategy
from strategies.multi_factor import MultiFactorStrategy
from strategies.industry_leader import IndustryLeaderStrategy


class TestStockSelectionResult:
    """测试选股结果类"""
    
    def test_add_stock(self):
        """测试添加股票"""
        result = StockSelectionResult()
        result.add_stock(
            code='000001',
            name='平安银行',
            score=80.5,
            reason='测试理由',
            metrics={'pe': 10, 'pb': 1.2}
        )
        
        assert len(result.stocks) == 1
        assert result.stocks[0]['code'] == '000001'
        assert result.stocks[0]['name'] == '平安银行'
        assert result.stocks[0]['score'] == 80.5
    
    def test_to_dataframe(self):
        """测试转换为 DataFrame"""
        result = StockSelectionResult()
        result.add_stock('000001', '平安银行', 80.5, '理由 1')
        result.add_stock('600036', '招商银行', 85.2, '理由 2')
        
        df = result.to_dataframe()
        
        assert len(df) == 2
        assert 'code' in df.columns
        assert 'score' in df.columns


class TestIndustryMomentumStrategy:
    """测试行业动量策略"""
    
    def test_init(self):
        """测试初始化"""
        strategy = IndustryMomentumStrategy()
        
        assert strategy.name == "行业动量策略"
        assert strategy.lookback_days == 20
        assert strategy.top_industries == 5
    
    def test_get_params(self):
        """测试获取参数"""
        strategy = IndustryMomentumStrategy()
        params = strategy.get_params()
        
        assert 'lookback_days' in params
        assert 'top_industries' in params
        assert params['lookback_days'] == 20
    
    def test_select_empty_data(self):
        """测试空数据选股"""
        strategy = IndustryMomentumStrategy()
        result = strategy.select(
            stock_data=pd.DataFrame(),
            industry_data=pd.DataFrame()
        )
        
        assert isinstance(result, StockSelectionResult)
        assert len(result.stocks) == 0


class TestMultiFactorStrategy:
    """测试多因子策略"""
    
    def test_init(self):
        """测试初始化"""
        strategy = MultiFactorStrategy()
        
        assert strategy.name == "多因子选股策略"
        assert strategy.quality_weight == 0.30
        assert strategy.momentum_weight == 0.25
        assert strategy.growth_weight == 0.25
        assert strategy.value_weight == 0.20
    
    def test_get_params(self):
        """测试获取参数"""
        strategy = MultiFactorStrategy()
        params = strategy.get_params()
        
        assert 'quality_weight' in params
        assert params['quality_weight'] == 0.30
    
    def test_factor_weights_sum(self):
        """测试因子权重和为 1"""
        strategy = MultiFactorStrategy()
        total_weight = (
            strategy.quality_weight +
            strategy.momentum_weight +
            strategy.growth_weight +
            strategy.value_weight
        )
        
        assert abs(total_weight - 1.0) < 0.001


class TestIndustryLeaderStrategy:
    """测试行业龙头股策略"""
    
    def test_init(self):
        """测试初始化"""
        strategy = IndustryLeaderStrategy()
        
        assert strategy.name == "行业龙头股策略"
        assert strategy.top_industries == 5
        assert strategy.leaders_per_industry == 2


# 集成测试
class TestIntegration:
    """集成测试"""
    
    def test_strategy_interface(self):
        """测试策略接口一致性"""
        strategies = [
            IndustryMomentumStrategy(),
            MultiFactorStrategy(),
            IndustryLeaderStrategy()
        ]
        
        for strategy in strategies:
            # 所有策略都应该有这些方法
            assert hasattr(strategy, 'select')
            assert hasattr(strategy, 'get_params')
            assert hasattr(strategy, 'set_params')
            assert hasattr(strategy, 'validate')
            
            # 返回值类型检查
            params = strategy.get_params()
            assert isinstance(params, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
