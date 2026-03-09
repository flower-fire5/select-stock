"""
回测报告生成模块
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from typing import Dict
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import PROCESSED_DATA_DIR


class ReportGenerator:
    """回测报告生成器"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else PROCESSED_DATA_DIR / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def generate(self, result, strategy_name: str, period: str) -> Dict:
        """
        生成完整回测报告
        
        Args:
            result: BacktestResult 对象
            strategy_name: 策略名称
            period: 回测周期
        
        Returns:
            Dict: 报告数据
        """
        self.logger.info("生成回测报告...")
        
        report = {
            'strategy': strategy_name,
            'period': period,
            'metrics': result.metrics,
            'trades': result.trades,
            'charts': {}
        }
        
        # 生成图表
        if result.equity_curve is not None:
            self._plot_equity_curve(result, strategy_name)
            report['charts']['equity_curve'] = str(self.output_dir / 'equity_curve.png')
        
        # 生成交易记录表
        if result.trades:
            trades_df = pd.DataFrame(result.trades)
            trades_df.to_csv(self.output_dir / 'trades.csv', index=False)
            report['charts']['trades'] = str(self.output_dir / 'trades.csv')
        
        # 生成文本报告
        self._generate_text_report(report)
        
        self.logger.info(f"报告已保存到 {self.output_dir}")
        return report
    
    def _plot_equity_curve(self, result, strategy_name: str):
        """绘制权益曲线"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        equity = result.equity_curve
        ax.plot(equity.index, equity.values, linewidth=1.5, label='策略权益')
        
        # 添加初始资金参考线
        ax.axhline(y=result.equity_curve.iloc[0], color='gray', linestyle='--', 
                   alpha=0.5, label='初始资金')
        
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('权益 (元)', fontsize=12)
        ax.set_title(f'{strategy_name} - 权益曲线', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 格式化 x 轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'equity_curve.png', dpi=150)
        plt.close()
        
        self.logger.info("权益曲线图已保存")
    
    def _generate_text_report(self, report: Dict):
        """生成文本格式报告"""
        metrics = report['metrics']
        
        content = f"""# 回测报告

## 基本信息
- **策略名称**: {report['strategy']}
- **回测周期**: {report['period']}
- **生成时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 绩效指标

| 指标 | 数值 |
|------|------|
| 初始资金 | {metrics.get('final_equity', 0) / (1 + metrics.get('total_return', 0) / 100):,.0f} 元 |
| 最终权益 | {metrics.get('final_equity', 0):,.0f} 元 |
| **总收益率** | **{metrics.get('total_return', 0):.2f}%** |
| **年化收益率** | **{metrics.get('annual_return', 0):.2f}%** |
| 最大回撤 | {metrics.get('max_drawdown', 0):.2f}% |
| 夏普比率 | {metrics.get('sharpe_ratio', 0):.2f} |
| 胜率 | {metrics.get('win_rate', 0):.2f}% |
| 交易次数 | {metrics.get('total_trades', 0)} |
| 买入次数 | {metrics.get('buy_trades', 0)} |
| 卖出次数 | {metrics.get('sell_trades', 0)} |

## 交易记录

共 {len(report['trades'])} 笔交易

"""
        # 添加前 20 笔交易
        if report['trades']:
            content += "| 日期 | 操作 | 代码 | 价格 | 股数 | 金额 | 原因 |\n"
            content += "|------|------|------|------|------|------|------|\n"
            
            for trade in report['trades'][:20]:
                content += f"| {trade['date']} | {trade['action']} | {trade['code']} | "
                content += f"{trade['price']:.2f} | {trade['shares']} | "
                content += f"{trade['value']:,.0f} | {trade['reason']} |\n"
            
            if len(report['trades']) > 20:
                content += f"\n... 还有 {len(report['trades']) - 20} 笔交易，详见 trades.csv\n"
        
        # 保存报告
        report_path = self.output_dir / 'backtest_report.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"文本报告已保存到 {report_path}")
    
    def print_metrics(self, metrics: Dict):
        """格式化打印绩效指标"""
        print("\n" + "=" * 60)
        print(" " * 20 + "回测绩效报告")
        print("=" * 60)
        
        print(f"\n{'总收益率:':<15} {metrics.get('total_return', 0):>10.2f}%")
        print(f"{'年化收益率:':<15} {metrics.get('annual_return', 0):>10.2f}%")
        print(f"{'最大回撤:':<15} {metrics.get('max_drawdown', 0):>10.2f}%")
        print(f"{'夏普比率:':<15} {metrics.get('sharpe_ratio', 0):>10.2f}")
        print(f"{'胜率:':<15} {metrics.get('win_rate', 0):>10.2f}%")
        print(f"{'交易次数:':<15} {metrics.get('total_trades', 0):>10d}")
        
        # 评估
        print("\n" + "-" * 60)
        print("策略评估:")
        
        if metrics.get('total_return', 0) > 30:
            print("  ✓ 收益率优秀 (>30%)")
        elif metrics.get('total_return', 0) > 15:
            print("  ✓ 收益率良好 (>15%)")
        else:
            print("  ✗ 收益率有待提高")
        
        if metrics.get('max_drawdown', 0) > -15:
            print("  ✓ 回撤控制良好 (<15%)")
        else:
            print("  ✗ 回撤较大，需优化风控")
        
        if metrics.get('sharpe_ratio', 0) > 1.5:
            print("  ✓ 夏普比率优秀 (>1.5)")
        elif metrics.get('sharpe_ratio', 0) > 1.0:
            print("  ✓ 夏普比率良好 (>1.0)")
        else:
            print("  ✗ 夏普比率有待提高")
        
        print("=" * 60)


# 使用示例
if __name__ == "__main__":
    # 测试报告生成
    from backtest.engine import BacktestResult
    
    result = BacktestResult()
    result.metrics = {
        'total_return': 35.5,
        'annual_return': 42.3,
        'max_drawdown': -8.5,
        'sharpe_ratio': 1.8,
        'win_rate': 72.5,
        'total_trades': 50,
        'buy_trades': 25,
        'sell_trades': 25,
        'final_equity': 1355000
    }
    
    generator = ReportGenerator()
    generator.print_metrics(result.metrics)
