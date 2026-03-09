"""
风险控制模块

风控规则：
1. 单只股票最大仓位限制
2. 单一行业最大仓位限制
3. 止损策略
4. 止盈策略
5. 黑名单过滤
6. 最大回撤监控
"""
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger


class RiskManager:
    """风险控制器"""
    
    def __init__(self,
                 max_position_per_stock: float = 0.30,  # 单股最大 30%
                 max_position_per_industry: float = 0.50,  # 行业最大 50%
                 stop_loss: float = 0.08,  # 止损 8%
                 take_profit: float = 0.15,  # 止盈 15%
                 max_drawdown: float = 0.15,  # 最大回撤 15%
                 blacklist: List[str] = None):  # 黑名单
        self.max_position_per_stock = max_position_per_stock
        self.max_position_per_industry = max_position_per_industry
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.max_drawdown = max_drawdown
        self.blacklist = set(blacklist or [])
        
        self.logger = logger
        self.logger.info("风控模块初始化完成")
    
    def filter_stocks(self, 
                      stocks: List[Dict], 
                      positions: Dict = None,
                      industry_map: Dict = None) -> List[Dict]:
        """
        过滤股票（黑名单 + 风控）
        
        Args:
            stocks: 待选股票列表
            positions: 当前持仓 {code: {shares, avg_price, industry}}
            industry_map: 股票行业映射 {code: industry}
        
        Returns:
            List[Dict]: 过滤后的股票列表
        """
        filtered = []
        
        for stock in stocks:
            code = stock.get('code')
            
            # 1. 黑名单过滤
            if code in self.blacklist:
                self.logger.debug(f"黑名单过滤：{code}")
                continue
            
            # 2. ST 股票过滤（简化：代码中包含 ST）
            name = stock.get('name', '')
            if 'ST' in name or '*' in name:
                self.logger.debug(f"ST 股票过滤：{code}")
                continue
            
            # 3. 仓位限制检查
            if positions:
                # 检查单股仓位
                if code in positions:
                    current_value = positions[code].get('value', 0)
                    if current_value > self.max_position_per_stock:
                        self.logger.debug(f"单股仓位超限：{code}")
                        continue
                
                # 检查行业仓位
                if industry_map and code in industry_map:
                    industry = industry_map[code]
                    industry_value = sum(
                        pos.get('value', 0) 
                        for c, pos in positions.items() 
                        if industry_map.get(c) == industry
                    )
                    if industry_value > self.max_position_per_industry:
                        self.logger.debug(f"行业仓位超限：{industry}")
                        continue
            
            filtered.append(stock)
        
        self.logger.info(f"风控过滤：{len(stocks)} -> {len(filtered)}")
        return filtered
    
    def check_stop_loss(self, 
                        code: str, 
                        current_price: float, 
                        avg_cost: float) -> bool:
        """
        检查是否触发止损
        
        Returns:
            bool: True 表示需要止损
        """
        if avg_cost <= 0:
            return False
        
        loss_rate = (current_price - avg_cost) / avg_cost
        
        if loss_rate <= -self.stop_loss:
            self.logger.warning(f"{code} 触发止损：{loss_rate:.2%} (止损线：-{self.stop_loss:.0%})")
            return True
        
        return False
    
    def check_take_profit(self,
                          code: str,
                          current_price: float,
                          avg_cost: float,
                          use_trailing: bool = True) -> bool:
        """
        检查是否触发止盈
        
        Args:
            use_trailing: 是否使用移动止盈
        
        Returns:
            bool: True 表示需要止盈
        """
        if avg_cost <= 0:
            return False
        
        profit_rate = (current_price - avg_cost) / avg_cost
        
        if use_trailing:
            # 移动止盈：最高价回撤 5% 止盈
            peak_price = avg_cost * (1 + self.take_profit)
            if current_price >= peak_price:
                trailing_stop = peak_price * 0.95  # 从最高点回撤 5%
                if current_price <= trailing_stop:
                    self.logger.info(f"{code} 触发移动止盈：{profit_rate:.2%}")
                    return True
        else:
            # 固定止盈
            if profit_rate >= self.take_profit:
                self.logger.info(f"{code} 触发止盈：{profit_rate:.2%} (止盈线：{self.take_profit:.0%})")
                return True
        
        return False
    
    def check_max_drawdown(self, 
                           current_equity: float, 
                           peak_equity: float) -> bool:
        """
        检查是否触发最大回撤
        
        Returns:
            bool: True 表示需要清仓风控
        """
        if peak_equity <= 0:
            return False
        
        drawdown = (peak_equity - current_equity) / peak_equity
        
        if drawdown >= self.max_drawdown:
            self.logger.error(f"触发最大回撤风控：{drawdown:.2%} (风控线：{self.max_drawdown:.0%})")
            return True
        
        return False
    
    def calculate_position_size(self,
                                total_capital: float,
                                num_positions: int,
                                current_positions: Dict = None) -> float:
        """
        计算单只股票的仓位大小
        
        Args:
            total_capital: 总资金
            num_positions: 计划持仓数量
            current_positions: 当前持仓
        
        Returns:
            float: 单只股票的目标仓位（元）
        """
        # 考虑仓位限制
        max_per_stock = total_capital * self.max_position_per_stock
        
        # 平均分配
        if num_positions > 0:
            target_position = min(
                total_capital / num_positions,
                max_per_stock
            )
        else:
            target_position = 0
        
        return target_position
    
    def get_blacklist(self) -> List[str]:
        """获取黑名单"""
        return list(self.blacklist)
    
    def add_to_blacklist(self, codes: List[str]):
        """添加到黑名单"""
        self.blacklist.update(codes)
        self.logger.info(f"添加到黑名单：{codes}")
    
    def remove_from_blacklist(self, codes: List[str]):
        """从黑名单移除"""
        self.blacklist -= set(codes)
        self.logger.info(f"从黑名单移除：{codes}")


# 风控报告
class RiskReport:
    """风控报告生成器"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.logger = logger
    
    def generate(self, 
                 positions: Dict, 
                 current_prices: Dict,
                 equity: float,
                 peak_equity: float) -> Dict:
        """
        生成风控报告
        
        Args:
            positions: 当前持仓
            current_prices: 当前价格 {code: price}
            equity: 当前权益
            peak_equity: 权益峰值
        
        Returns:
            Dict: 风控报告
        """
        report = {
            'total_equity': equity,
            'peak_equity': peak_equity,
            'current_drawdown': (peak_equity - equity) / peak_equity if peak_equity > 0 else 0,
            'positions_count': len(positions),
            'warnings': [],
            'actions': []
        }
        
        # 检查每个持仓
        for code, position in positions.items():
            current_price = current_prices.get(code, 0)
            avg_cost = position.get('avg_price', 0)
            
            if current_price <= 0 or avg_cost <= 0:
                continue
            
            profit_rate = (current_price - avg_cost) / avg_cost
            
            # 止损检查
            if self.risk_manager.check_stop_loss(code, current_price, avg_cost):
                report['warnings'].append(f"{code} 触发止损 ({profit_rate:.2%})")
                report['actions'].append({'action': 'sell', 'code': code, 'reason': 'stop_loss'})
            
            # 止盈检查
            elif self.risk_manager.check_take_profit(code, current_price, avg_cost):
                report['warnings'].append(f"{code} 触发止盈 ({profit_rate:.2%})")
                report['actions'].append({'action': 'sell', 'code': code, 'reason': 'take_profit'})
            else:
                report['warnings'].append(f"{code}: {profit_rate:.2%}")
        
        # 最大回撤检查
        if self.risk_manager.check_max_drawdown(equity, peak_equity):
            report['warnings'].append("触发最大回撤风控！")
            report['actions'].append({'action': 'clear_all', 'reason': 'max_drawdown'})
        
        return report
