"""
回测引擎 - 核心回测框架
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from strategies.base import BaseStrategy, StockSelectionResult


class BacktestResult:
    """回测结果"""
    
    def __init__(self):
        self.trades: List[Dict] = []  # 交易记录
        self.equity_curve: pd.Series = None  # 权益曲线
        self.metrics: Dict = {}  # 绩效指标
        self.positions: pd.DataFrame = None  # 持仓记录
    
    def add_trade(self, date: str, action: str, code: str, price: float, 
                  shares: int, reason: str = ""):
        """添加交易记录"""
        self.trades.append({
            'date': date,
            'action': action,  # buy/sell
            'code': code,
            'price': price,
            'shares': shares,
            'value': price * shares,
            'reason': reason
        })
    
    def calculate_metrics(self, initial_capital: float):
        """计算绩效指标"""
        if self.equity_curve is None or len(self.equity_curve) == 0:
            return
        
        equity = self.equity_curve
        
        # 基础指标
        total_return = (equity.iloc[-1] - initial_capital) / initial_capital * 100
        
        # 年化收益率
        days = (equity.index[-1] - equity.index[0]).days
        if days > 0:
            annual_return = ((equity.iloc[-1] / initial_capital) ** (365 / days) - 1) * 100
        else:
            annual_return = 0
        
        # 最大回撤
        peak = equity.expanding(min_periods=1).max()
        drawdown = (equity - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # 夏普比率
        daily_returns = equity.pct_change().dropna()
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 胜率
        buy_trades = [t for t in self.trades if t['action'] == 'buy']
        sell_trades = [t for t in self.trades if t['action'] == 'sell']
        
        profitable_trades = 0
        for sell in sell_trades:
            # 找到对应的买入
            for buy in buy_trades:
                if buy['code'] == sell['code'] and buy['date'] < sell['date']:
                    if sell['price'] > buy['price']:
                        profitable_trades += 1
                    break
        
        win_rate = profitable_trades / len(sell_trades) * 100 if sell_trades else 0
        
        self.metrics = {
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 2),
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'final_equity': round(equity.iloc[-1], 2)
        }


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, 
                 initial_capital: float = 1000000,
                 commission: float = 0.0003,  # 万三手续费
                 slippage: float = 0.001,  # 千一滑点
                 max_position_per_stock: float = 0.30,
                 max_position_per_industry: float = 0.50):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.max_position_per_stock = max_position_per_stock
        self.max_position_per_industry = max_position_per_industry
        
        self.positions: Dict[str, Dict] = {}  # 持仓 {code: {shares, avg_price, industry}}
        self.cash = initial_capital
        self.equity_curve: List[float] = []
        self.equity_dates: List[datetime] = []
        
        self.result = BacktestResult()
        self.logger = logger
    
    def run(self, 
            strategy: BaseStrategy,
            stock_data: pd.DataFrame,
            industry_data: pd.DataFrame = None,
            basic_info: Dict = None,
            start_date: str = None,
            end_date: str = None,
            rebalance_days: int = 20) -> BacktestResult:
        """
        运行回测
        
        Args:
            strategy: 选股策略
            stock_data: 股票日线数据
            industry_data: 行业数据
            basic_info: 股票基本信息
            start_date: 回测开始日期
            end_date: 回测结束日期
            rebalance_days: 调仓周期（默认 20 个交易日）
        """
        self.logger.info(f"开始回测：{start_date} ~ {end_date}")
        self.logger.info(f"初始资金：{self.initial_capital:,.0f}")
        
        # 日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
        
        last_rebalance = None
        
        for current_date in dates:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 检查是否需要调仓
            if last_rebalance is None or (current_date - last_rebalance).days >= rebalance_days:
                self.logger.info(f"\n[{date_str}] 执行选股...")
                
                # 获取当日数据
                try:
                    daily_stock = stock_data.xs(current_date, level='date')
                except KeyError:
                    continue
                
                # 执行策略选股
                selection = strategy.select(
                    stock_data=daily_stock,
                    industry_data=industry_data,
                    basic_info=basic_info,
                    date=date_str
                )
                
                if selection.stocks:
                    self.logger.info(f"选中 {len(selection.stocks)} 只股票")
                    self._rebalance(selection, current_date)
                
                last_rebalance = current_date
            
            # 更新权益
            self._update_equity(current_date)
        
        # 完成回测
        self.result.equity_curve = pd.Series(
            self.equity_curve, 
            index=self.equity_dates,
            name='equity'
        )
        self.result.calculate_metrics(self.initial_capital)
        
        self.logger.info("\n=== 回测完成 ===")
        self._print_summary()
        
        return self.result
    
    def _rebalance(self, selection: StockSelectionResult, date: datetime):
        """调仓换股"""
        date_str = date.strftime('%Y-%m-%d')
        
        # 1. 卖出不在选股列表中的股票
        selected_codes = {s['code'] for s in selection.stocks}
        
        for code in list(self.positions.keys()):
            if code not in selected_codes:
                self._sell(code, date_str, "调仓卖出")
        
        # 2. 买入新选中的股票
        # 计算每只股票的仓位
        num_stocks = len(selection.stocks)
        if num_stocks == 0:
            return
        
        position_value = self.cash * self.max_position_per_stock / num_stocks
        position_value = min(position_value, self.cash / num_stocks)
        
        for stock in selection.stocks:
            code = stock['code']
            
            if code in self.positions:
                continue  # 已持仓，跳过
            
            # 获取当日收盘价
            try:
                # 简化：假设能获取到价格
                price = self._get_price(code, date)
                if price <= 0:
                    continue
                
                # 计算可买股数
                shares = int(position_value / price / 100) * 100  # 100 股整数倍
                if shares < 100:
                    continue
                
                # 执行买入
                self._buy(code, shares, price, date_str, stock['reason'])
                
            except Exception as e:
                self.logger.warning(f"买入 {code} 失败：{e}")
    
    def _buy(self, code: str, shares: int, price: float, date: str, reason: str = ""):
        """买入操作"""
        # 考虑滑点
        actual_price = price * (1 + self.slippage)
        # 手续费
        commission = actual_price * shares * self.commission
        total_cost = actual_price * shares + commission
        
        if total_cost > self.cash:
            self.logger.warning(f"资金不足，无法买入 {code}")
            return
        
        # 更新持仓
        if code in self.positions:
            old_shares = self.positions[code]['shares']
            old_avg = self.positions[code]['avg_price']
            new_shares = old_shares + shares
            new_avg = (old_avg * old_shares + actual_price * shares) / new_shares
            self.positions[code] = {
                'shares': new_shares,
                'avg_price': new_avg
            }
        else:
            self.positions[code] = {
                'shares': shares,
                'avg_price': actual_price
            }
        
        self.cash -= total_cost
        
        self.result.add_trade(date, 'buy', code, actual_price, shares, reason)
        self.logger.info(f"买入 {code}: {shares}股 @ {actual_price:.2f}, 花费 {total_cost:,.0f}")
    
    def _sell(self, code: str, date: str, reason: str = ""):
        """卖出操作"""
        if code not in self.positions:
            return
        
        position = self.positions[code]
        shares = position['shares']
        
        # 获取价格（简化）
        price = self._get_price(code, pd.to_datetime(date))
        if price <= 0:
            return
        
        # 考虑滑点
        actual_price = price * (1 - self.slippage)
        # 手续费
        commission = actual_price * shares * self.commission
        total_value = actual_price * shares - commission
        
        self.cash += total_value
        
        self.result.add_trade(date, 'sell', code, actual_price, shares, reason)
        self.logger.info(f"卖出 {code}: {shares}股 @ {actual_price:.2f}, 收入 {total_value:,.0f}")
        
        del self.positions[code]
    
    def _get_price(self, code: str, date: pd.Timestamp) -> float:
        """获取股票价格（简化实现）"""
        # TODO: 实际应该从 stock_data 中查询
        # 这里返回一个模拟价格
        return 10.0
    
    def _update_equity(self, date: pd.Timestamp):
        """更新权益"""
        # 持仓市值
        portfolio_value = 0
        for code, position in self.positions.items():
            price = self._get_price(code, date)
            portfolio_value += price * position['shares']
        
        # 总权益
        total_equity = self.cash + portfolio_value
        self.equity_curve.append(total_equity)
        self.equity_dates.append(date)
    
    def _print_summary(self):
        """打印回测摘要"""
        metrics = self.result.metrics
        if not metrics:
            return
        
        print("\n" + "=" * 50)
        print("回测结果摘要")
        print("=" * 50)
        print(f"初始资金：    {self.initial_capital:,.0f}")
        print(f"最终权益：    {metrics.get('final_equity', 0):,.0f}")
        print(f"总收益率：    {metrics.get('total_return', 0):.2f}%")
        print(f"年化收益：    {metrics.get('annual_return', 0):.2f}%")
        print(f"最大回撤：    {metrics.get('max_drawdown', 0):.2f}%")
        print(f"夏普比率：    {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"胜率：        {metrics.get('win_rate', 0):.2f}%")
        print(f"交易次数：    {metrics.get('total_trades', 0)}")
        print("=" * 50)
