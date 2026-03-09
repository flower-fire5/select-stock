"""
数据加载模块 - 使用 AkShare 获取 A 股数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR


class DataLoader:
    """A 股数据加载器"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("数据加载器初始化完成")
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取 A 股股票列表
        返回：股票代码、名称、上市日期等
        """
        self.logger.info("获取 A 股股票列表...")
        try:
            # 获取沪深 A 股列表
            df = ak.stock_info_a_code_name()
            df.columns = ['code', 'name']
            self.logger.info(f"获取到 {len(df)} 只股票")
            return df
        except Exception as e:
            self.logger.error(f"获取股票列表失败：{e}")
            raise
    
    def get_daily_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取个股日线数据
        
        Args:
            stock_code: 股票代码 (如：000001)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            DataFrame: 日期、开盘、最高、最低、收盘、成交量、成交额
        """
        self.logger.info(f"获取 {stock_code} 日线数据：{start_date} ~ {end_date}")
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq"  # 前复权
            )
            
            # 重命名列
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover', 
                         'amplitude', 'pct_change', 'change', 'turnover_rate']
            df['date'] = pd.to_datetime(df['date'])
            df['code'] = stock_code
            df.set_index(['date', 'code'], inplace=True)
            
            self.logger.info(f"获取到 {len(df)} 条记录")
            return df
        except Exception as e:
            self.logger.warning(f"获取 {stock_code} 数据失败：{e}")
            return pd.DataFrame()
    
    def get_industry_list(self) -> pd.DataFrame:
        """
        获取申万行业分类
        返回：行业代码、行业名称、成分股
        """
        self.logger.info("获取申万行业分类...")
        try:
            # 获取申万一级行业成分
            df = ak.stock_board_industry_name_em()
            self.logger.info(f"获取到 {len(df)} 个行业")
            return df
        except Exception as e:
            self.logger.error(f"获取行业列表失败：{e}")
            raise
    
    def get_industry_daily(self, industry_name: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取行业指数日线数据
        
        Args:
            industry_name: 行业名称 (如：银行)
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            DataFrame: 行业指数日线数据
        """
        self.logger.info(f"获取行业 {industry_name} 指数数据...")
        try:
            df = ak.stock_board_industry_hist_em(
                symbol=industry_name,
                period="3 个月",  # 最近 3 个月
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['日期'])
                df['close'] = pd.to_numeric(df['收盘'], errors='coerce')
                df['pct_change'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
                df['industry'] = industry_name
                df.set_index('date', inplace=True)
            
            return df
        except Exception as e:
            self.logger.warning(f"获取行业 {industry_name} 数据失败：{e}")
            return pd.DataFrame()
    
    def get_stock_basic_info(self, stock_code: str) -> dict:
        """
        获取股票基本信息（财务指标）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            dict: PE、PB、ROE、市值等
        """
        try:
            # 获取实时行情（包含 PE、PB 等）
            df = ak.stock_zh_a_spot_em()
            stock_info = df[df['代码'] == stock_code]
            
            if stock_info.empty:
                return {}
            
            info = stock_info.iloc[0]
            return {
                'code': stock_code,
                'name': info.get('名称', ''),
                'pe': float(info.get('市盈率 - 动态', 0)) if info.get('市盈率 - 动态') else 0,
                'pb': float(info.get('市净率', 0)) if info.get('市净率') else 0,
                'market_cap': float(info.get('总市值', 0)) if info.get('总市值') else 0,
                'roe': float(info.get('净资产收益率 - 加权', 0)) if info.get('净资产收益率 - 加权') else 0,
            }
        except Exception as e:
            self.logger.warning(f"获取 {stock_code} 基本信息失败：{e}")
            return {}
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """保存数据到本地"""
        filepath = RAW_DATA_DIR / filename
        if not df.empty:
            df.to_parquet(filepath, index=True)
            self.logger.info(f"数据已保存到 {filepath}")
    
    def load_data(self, filename: str) -> pd.DataFrame:
        """从本地加载数据"""
        filepath = RAW_DATA_DIR / filename
        if filepath.exists():
            return pd.read_parquet(filepath)
        return pd.DataFrame()


# 测试函数
if __name__ == "__main__":
    logger.add("logs/test_data_loader.log", rotation="1 MB")
    
    loader = DataLoader()
    
    # 测试获取股票列表
    print("\n=== 测试：获取股票列表 ===")
    stock_list = loader.get_stock_list()
    print(f"股票总数：{len(stock_list)}")
    print(stock_list.head())
    
    # 测试获取个股数据
    print("\n=== 测试：获取个股数据 ===")
    test_stock = "000001"  # 平安银行
    daily_data = loader.get_daily_data(test_stock, "2025-01-01", "2026-01-01")
    print(f"数据条数：{len(daily_data)}")
    print(daily_data.head())
    
    # 测试获取行业列表
    print("\n=== 测试：获取行业列表 ===")
    industry_list = loader.get_industry_list()
    print(f"行业数量：{len(industry_list)}")
    print(industry_list.head())
    
    print("\n=== 测试完成 ===")
