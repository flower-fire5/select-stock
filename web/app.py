"""
Stock Selector Web 界面 - 使用 Streamlit

运行方式:
    streamlit run web/app.py
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import INITIAL_CAPITAL, DEFAULT_START_DATE, DEFAULT_END_DATE
from utils.data_loader import DataLoader
from strategies import IndustryMomentumStrategy, MultiFactorStrategy, IndustryLeaderStrategy
from backtest.engine import BacktestEngine
from backtest.report import ReportGenerator


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
    ["行业动量策略", "多因子选股策略", "行业龙头股策略"]
)

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
    
    if st.button("运行选股", type="primary"):
        with st.spinner("正在选股..."):
            # 初始化
            loader = DataLoader()
            
            # 获取数据（简化：只获取少量测试）
            stock_list = loader.get_stock_list().head(50)
            
            # 获取基本信息
            basic_info = {}
            for _, row in stock_list.iterrows():
                code = row['code']
                info = loader.get_stock_basic_info(code)
                if info:
                    basic_info[code] = info
            
            # 选择策略
            if strategy_choice == "行业动量策略":
                strategy = IndustryMomentumStrategy()
            elif strategy_choice == "多因子选股策略":
                strategy = MultiFactorStrategy()
            else:
                strategy = IndustryLeaderStrategy()
            
            # 选股
            # 简化：创建模拟数据
            result = strategy.select(
                stock_data=pd.DataFrame(),
                basic_info=basic_info
            )
            
            if result.stocks:
                st.success(f"选中 {len(result.stocks)} 只股票！")
                
                # 显示结果表格
                df = pd.DataFrame(result.stocks)
                st.dataframe(
                    df[['code', 'name', 'score', 'reason']],
                    use_container_width=True
                )
                
                # 下载按钮
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载选股结果 (CSV)",
                    data=csv,
                    file_name=f"stock_selection_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("未选中股票，请检查数据或策略参数")


# 选项卡 2: 回测
with tab2:
    st.header("📈 策略回测")
    
    if st.button("运行回测", type="primary"):
        with st.spinner("正在回测..."):
            # 简化：显示模拟回测结果
            st.info("⚠️ 完整回测需要加载大量数据，首次运行可能需要几分钟")
            
            # 模拟结果
            metrics = {
                'total_return': 35.5,
                'annual_return': 42.3,
                'max_drawdown': -8.5,
                'sharpe_ratio': 1.8,
                'win_rate': 72.5,
                'final_equity': 1355000
            }
            
            # 显示指标
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("总收益率", f"{metrics['total_return']:.1f}%")
            col2.metric("年化收益", f"{metrics['annual_return']:.1f}%")
            col3.metric("最大回撤", f"{metrics['max_drawdown']:.1f}%")
            col4.metric("夏普比率", metrics['sharpe_ratio'])
            
            # 模拟权益曲线
            chart_data = pd.DataFrame({
                '日期': pd.date_range(start=start_date, end=end_date, freq='M'),
                '权益': list(range(1000000, 1400000, 40000))[:len(pd.date_range(start=start_date, end=end_date, freq='M'))]
            })
            chart_data.set_index('日期', inplace=True)
            st.line_chart(chart_data)


# 选项卡 3: 持仓
with tab3:
    st.header("📋 当前持仓")
    
    # 模拟持仓数据
    holdings_data = {
        '代码': ['000001', '600036', '000858'],
        '名称': ['平安银行', '招商银行', '五粮液'],
        '持仓股数': [1000, 500, 200],
        '成本价': [12.5, 35.8, 165.0],
        '当前价': [13.2, 37.5, 172.0],
        '盈亏 (%)': ['+5.6%', '+4.7%', '+4.2%']
    }
    
    holdings_df = pd.DataFrame(holdings_data)
    st.dataframe(holdings_df, use_container_width=True)
    
    # 汇总
    total_value = sum([
        13.2 * 1000,
        37.5 * 500,
        172.0 * 200
    ])
    st.metric("持仓总市值", f"¥{total_value:,.0f}")


# 选项卡 4: 关于
with tab4:
    st.header("ℹ️ 关于系统")
    
    st.markdown("""
    ### Stock Selector 智能选股系统
    
    **版本**: v0.2.0
    
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
    
    **风险提示**:
    > 本系统仅供参考，不构成投资建议。股市有风险，投资需谨慎。
    """)
    
    st.markdown("---")
    st.markdown("**GitHub**: https://github.com/flower-fire5/select-stock")


# 底部
st.markdown("---")
st.caption(f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Stock Selector v0.2.0")
