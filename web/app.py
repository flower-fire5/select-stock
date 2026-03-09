"""
Stock Selector Web 界面 - 使用 Streamlit

运行方式:
    python3 -m streamlit run web/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import INITIAL_CAPITAL
from strategies import IndustryMomentumStrategy, MultiFactorStrategy, IndustryLeaderStrategy
from backtest.engine import BacktestEngine, BacktestResult
from backtest.report import ReportGenerator
from utils.data_loader import DataLoader


# 页面配置
st.set_page_config(
    page_title="Stock Selector - 智能选股系统",
    page_icon="📈",
    layout="wide"
)

# 标题
st.title("📈 Stock Selector - 智能选股系统")
st.markdown("---")


# 侧边栏 - 配置
st.sidebar.header("⚙️ 配置")

# 策略选择
strategy_choice = st.sidebar.selectbox(
    "选择策略",
    ["多因子选股策略", "行业龙头股策略", "行业动量策略"]
)

# 选股数量
top_n = st.sidebar.slider("选股数量", 3, 10, 5)

# 回测参数
st.sidebar.header("📊 回测参数")
start_date = st.sidebar.date_input("开始日期", value=datetime(2023, 1, 1))
end_date = st.sidebar.date_input("结束日期", value=datetime(2026, 1, 1))
initial_capital = st.sidebar.number_input("初始资金 (元)", value=1000000, step=100000)

# 风控参数
st.sidebar.header("🛡️ 风控参数")
stop_loss = st.sidebar.slider("止损线 (%)", 5, 15, 8)
take_profit = st.sidebar.slider("止盈线 (%)", 10, 30, 15)
max_position = st.sidebar.slider("单股最大仓位 (%)", 10, 50, 30)


# 主界面 - 选项卡
tab1, tab2, tab3, tab4 = st.tabs(["🎯 选股", "📈 回测", "📋 持仓", "ℹ️ 关于"])


# 选项卡 1: 选股
with tab1:
    st.header("🎯 智能选股")
    st.info("💡 使用 AkShare 获取真实 A 股数据，首次运行可能需要几分钟")
    
    if st.button("运行选股", type="primary"):
        with st.spinner("正在获取数据并选股..."):
            try:
                # 初始化数据加载器
                loader = DataLoader()
                
                # 获取股票列表（简化：前 50 只）
                with st.spinner("获取股票列表..."):
                    stock_list = loader.get_stock_list().head(50)
                
                # 获取基本信息
                with st.spinner("获取股票基本信息..."):
                    basic_info = {}
                    progress_bar = st.progress(0)
                    for i, (_, row) in enumerate(stock_list.iterrows()):
                        code = row['code']
                        try:
                            info = loader.get_stock_basic_info(code)
                            if info and info.get('pe', 0) > 0:
                                basic_info[code] = info
                        except:
                            pass
                        progress_bar.progress((i + 1) / len(stock_list))
                
                st.write(f"✅ 获取到 {len(basic_info)} 只股票的基本信息")
                
                # 选择策略
                if strategy_choice == "行业动量策略":
                    strategy = IndustryMomentumStrategy()
                elif strategy_choice == "多因子选股策略":
                    strategy = MultiFactorStrategy()
                    strategy.set_params({'top_n': top_n})
                else:
                    strategy = IndustryLeaderStrategy()
                    strategy.set_params({'top_n': top_n})
                
                # 选股
                with st.spinner("执行选股策略..."):
                    result = strategy.select(
                        stock_data=pd.DataFrame(),
                        basic_info=basic_info
                    )
                
                if result.stocks:
                    st.success(f"✅ 选中 {len(result.stocks)} 只股票！")
                    
                    # 显示结果表格
                    df = pd.DataFrame(result.stocks)
                    
                    # 格式化显示
                    display_df = df[['code', 'name', 'score', 'reason']].copy()
                    display_df.columns = ['代码', '名称', '得分', '选股理由']
                    display_df['得分'] = display_df['得分'].round(1)
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # 详细指标
                    with st.expander("查看详细指标"):
                        for stock in result.stocks:
                            st.subheader(f"{stock['code']} - {stock['name']}")
                            metrics = stock.get('metrics', {})
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("ROE", f"{metrics.get('roe', 0):.1f}%" if metrics.get('roe') else "N/A")
                            col2.metric("PE", f"{metrics.get('pe', 0):.1f}" if metrics.get('pe') else "N/A")
                            col3.metric("PB", f"{metrics.get('pb', 0):.1f}" if metrics.get('pb') else "N/A")
                            col4.metric("市值", f"{metrics.get('market_cap', 0)/100e8:.0f}亿" if metrics.get('market_cap') else "N/A")
                            st.write(f"**选股理由**: {stock['reason']}")
                    
                    # 下载按钮
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 下载选股结果 (CSV)",
                        data=csv,
                        file_name=f"stock_selection_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ 未选中股票，请检查策略参数")
            
            except Exception as e:
                st.error(f"❌ 选股失败：{e}")
                st.code(str(e))


# 选项卡 2: 回测
with tab2:
    st.header("📈 策略回测")
    st.info("💡 使用模拟数据演示回测流程，完整回测请运行 `python backtest/run.py`")
    
    if st.button("运行回测", type="primary"):
        with st.spinner("正在回测..."):
            try:
                # 创建模拟回测结果
                result = BacktestResult()
                
                # 模拟交易记录
                result.trades = [
                    {'date': '2023-01-15', 'action': 'buy', 'code': '000001', 'price': 12.5, 'shares': 1000, 'reason': '选股买入'},
                    {'date': '2023-02-15', 'action': 'sell', 'code': '000001', 'price': 13.8, 'shares': 1000, 'reason': '调仓卖出'},
                    {'date': '2023-02-15', 'action': 'buy', 'code': '600036', 'price': 35.0, 'shares': 500, 'reason': '选股买入'},
                    {'date': '2023-03-15', 'action': 'sell', 'code': '600036', 'price': 38.5, 'shares': 500, 'reason': '止盈卖出'},
                    {'date': '2023-03-15', 'action': 'buy', 'code': '600519', 'price': 1650, 'shares': 100, 'reason': '选股买入'},
                    {'date': '2023-04-15', 'action': 'sell', 'code': '600519', 'price': 1820, 'shares': 100, 'reason': '止盈卖出'},
                ]
                
                # 模拟权益曲线
                days = 365
                dates = pd.date_range(start=start_date, periods=days, freq='D')
                base_return = 0.0003
                volatility = 0.015
                returns = np.random.normal(base_return, volatility, days)
                equity_values = initial_capital * np.cumprod(1 + returns)
                
                result.equity_curve = pd.Series(equity_values, index=dates)
                result.calculate_metrics(initial_capital)
                
                # 显示指标
                metrics = result.metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("总收益率", f"{metrics.get('total_return', 0):.1f}%")
                col2.metric("年化收益", f"{metrics.get('annual_return', 0):.1f}%")
                col3.metric("最大回撤", f"{metrics.get('max_drawdown', 0):.1f}%")
                col4.metric("夏普比率", f"{metrics.get('sharpe_ratio', 0):.2f}")
                
                # 权益曲线图
                st.subheader("权益曲线")
                chart_df = pd.DataFrame({
                    '日期': result.equity_curve.index,
                    '权益': result.equity_curve.values
                })
                chart_df.set_index('日期', inplace=True)
                st.line_chart(chart_df)
                
                # 详细指标
                with st.expander("查看详细指标"):
                    st.write(f"**总收益率**: {metrics.get('total_return', 0):.2f}%")
                    st.write(f"**年化收益率**: {metrics.get('annual_return', 0):.2f}%")
                    st.write(f"**最大回撤**: {metrics.get('max_drawdown', 0):.2f}%")
                    st.write(f"**夏普比率**: {metrics.get('sharpe_ratio', 0):.2f}")
                    st.write(f"**胜率**: {metrics.get('win_rate', 0):.2f}%")
                    st.write(f"**交易次数**: {metrics.get('total_trades', 0)}")
                
                # 交易记录
                with st.expander("查看交易记录"):
                    trades_df = pd.DataFrame(result.trades)
                    trades_df.columns = ['日期', '操作', '代码', '价格', '股数', '原因']
                    st.dataframe(trades_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ 回测失败：{e}")


# 选项卡 3: 持仓
with tab3:
    st.header("📋 模拟持仓")
    
    holdings_data = {
        '代码': ['000001', '600036', '600519'],
        '名称': ['平安银行', '招商银行', '贵州茅台'],
        '持仓股数': [1000, 500, 100],
        '成本价': [12.5, 35.8, 1650.0],
        '当前价': [13.2, 37.5, 1820.0],
        '盈亏 (%)': ['+5.6%', '+4.7%', '+10.3%']
    }
    
    holdings_df = pd.DataFrame(holdings_data)
    st.dataframe(holdings_df, use_container_width=True)
    
    total_value = 13.2 * 1000 + 37.5 * 500 + 1820.0 * 100
    st.metric("持仓总市值", f"¥{total_value:,.0f}")


# 选项卡 4: 关于
with tab4:
    st.header("ℹ️ 关于系统")
    
    st.markdown("""
    ### Stock Selector 智能选股系统
    
    **版本**: v0.3.0
    
    **核心功能**:
    - 📊 多因子选股策略
    - 🏭 行业轮动分析
    - 🐉 龙头股识别
    - 📈 历史回测
    - 🛡️ 风险控制
    
    **技术栈**:
    - Python 3.x
    - Streamlit (Web 界面)
    - AkShare (数据源)
    - Pandas/Numpy (数据分析)
    
    **使用流程**:
    1. 在"选股"选项卡运行选股策略
    2. 在"回测"选项卡查看历史表现
    3. 在"持仓"选项卡管理当前持仓
    4. 每周运行一次，获取最新推荐
    
    **命令行使用**:
    ```bash
    # 每周选股
    python scripts/weekly_run.py
    
    # 运行回测
    python backtest/run.py
    
    # 运行测试
    python scripts/self_test.py
    ```
    
    **风险提示**:
    > 本系统仅供参考，不构成投资建议。股市有风险，投资需谨慎。
    """)
    
    st.markdown("---")
    st.markdown("**GitHub**: https://github.com/flower-fire5/select-stock")


# 底部
st.markdown("---")
st.caption(f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Stock Selector v0.3.0")
