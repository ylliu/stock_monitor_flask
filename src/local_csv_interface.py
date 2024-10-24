import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from daily_line import DailyLine
from data_interface_base import DataInterfaceBase
from tushare_interface import TushareInterface


class LocalCsvInterface(DataInterfaceBase):
    def __init__(self):
        self.realtime_daily_lines = {}

    def get_all_realtime_data(self, stock_list):
        tushare = TushareInterface()
        self.realtime_daily_lines.clear()
        self.realtime_daily_lines = tushare.get_all_stock_realtime_lines(stock_list)

    def get_daily_lines(self, code, end_date, back_days):

        # start = time.time()
        df_basic_filtered = self.data_between(code, end_date, back_days)
        if df_basic_filtered is None:
            return None
        # print(df_basic_filtered)
        daily_lines = []
        for index, row in df_basic_filtered.iterrows():
            # 提取每一行的数据
            trade_date = str(row['trade_date'])
            open_price = row['open_qfq']
            close_price = row['close_qfq']
            high_price = row['high_qfq']
            low_price = row['low_qfq']
            volume = row['vol']
            turnover_rate_f = row['turnover_rate_f']
            code = row['ts_code']
            average_price = row['weight_avg']
            pre_close = 0
            volume_ratio = 0
            if 'pre_close_qfq' in row:
                pre_close = row['pre_close_qfq']
            if 'volume_ratio' in row:
                volume_ratio = row['volume_ratio']
            max_pct_change = self.change_pct_of_day(high_price, pre_close, low_price)
            up_shadow_pct = self.up_shadow_pct_of_day(high_price, pre_close, close_price, open_price)
            # 创建一个新的DailyLine对象并添加到列表中
            daily_line = DailyLine(trade_date, open_price, close_price, high_price, low_price, volume,
                                   turnover_rate_f,
                                   code, average_price, max_pct_change, up_shadow_pct, volume_ratio, pre_close)
            daily_lines.append(daily_line)

        today = self.get_today_date()
        if self.is_a_stock_trading_day(today) and today == end_date and self.is_between_9_30_and_19_00():
            daily_realtime = self.realtime_daily_lines[code]
            daily_lines.append(daily_realtime)
        # end = time.time()
        # print('cost:', end - start)
        return daily_lines

    def get_name(self, code):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path)
        if not df_basic.empty:
            return df_basic.iloc[0]['name']
        return "名字不存在"

    def get_average_price(self, code, start_date, end_date):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] <= end_date)]
        weight_avg_list = df_basic_filtered['weight_avg'].tolist()
        return weight_avg_list

    def get_close_price_of_day(self, code, date):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        dtype_dict = {'trade_date': str}
        df = pd.read_csv(basic_csv_path, dtype=dtype_dict)
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            close_qfq_value = row['close_qfq'].iloc[0]
            print(f"The close_qfq value for {date} is: {close_qfq_value}")
        else:
            print(f"No data found for the date {date}.")
            close_qfq_value = None
        return close_qfq_value

    def get_before_days_up_times(self, code, end_date, back_days):
        df_basic_filtered = self.data_between(code, end_date, back_days)
        up_times = 0
        for index, row in df_basic_filtered.iterrows():
            # 提取每一行的数据
            limit = str(row['limit'])
            if limit == 'U':
                up_times += 1
        return up_times

    def data_between(self, code, end_date, back_days):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        if not os.path.exists(basic_csv_path):
            return None
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        trade_dates = pd.bdate_range(end=end_date, periods=back_days)
        start_date = trade_dates[0].strftime('%Y%m%d')
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] <= end_date)]
        return df_basic_filtered

    def data_before_days(self, code, end_date, back_days):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        trade_dates = pd.bdate_range(end=end_date, periods=back_days + 1)
        start_date = trade_dates[0].strftime('%Y%m%d')
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] < end_date)]
        return df_basic_filtered

    def data_of_days_include_end_date(self, code, end_date, back_days):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        trade_dates = pd.bdate_range(end=end_date, periods=back_days)
        start_date = trade_dates[0].strftime('%Y%m%d')
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] <= end_date)]
        return df_basic_filtered

    def get_before_days_down_times(self, code, end_date, back_days):
        df_basic_filtered = self.data_between(code, end_date, back_days)
        down_times = 0
        for index, row in df_basic_filtered.iterrows():
            # 提取每一行的数据
            limit = str(row['limit'])
            if limit == 'D':
                down_times += 1
        return down_times

    def find_sideways_trading(self, code, max_vol, date):
        diff = 0
        found_date = None
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] < date)]
        df = df_basic_filtered.sort_values(by='trade_date', ascending=False)
        # date = date.strftime('%Y%m%d')
        for index, row in df.iterrows():
            if row['close_qfq'] < row['open_qfq']:
                continue
            if row['vol'] > max_vol:
                found_date = row['trade_date']
                days = pd.bdate_range(found_date, date)
                diff = len(days)
                return diff
        if found_date == None:
            return 300
        return diff

    def find_days_of_new_high(self, code, max_high, date):
        diff = 0
        found_date = None
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] < date)]
        df = df_basic_filtered.sort_values(by='trade_date', ascending=False)
        # date = date.strftime('%Y%m%d')
        for index, row in df.iterrows():
            if row['high_qfq'] > max_high:
                found_date = row['trade_date']
                days = pd.bdate_range(found_date, date)
                diff = len(days)
                return diff
        if found_date == None:
            return 9999999
        return diff

    def get_history_mean_price(self, code, end_date, how_many_days):
        df_basic_filtered = self.data_between(code, end_date, how_many_days)
        mean = df_basic_filtered['close_qfq'].mean()
        return round(mean, 3)

    def average_turnover_rate_of(self, code, end_date, days):
        df = self.data_before_days(code, end_date, days)
        if len(df) == 0:
            print(code)
            return 100
        sum_turnover_rate = 0
        for index, row in df.iterrows():
            sum_turnover_rate += row['turnover_rate_f']
        average = sum_turnover_rate / len(df)
        return average

    def moving_average(self, prices, window=10):
        return np.convolve(prices, np.ones(window) / window, 'valid')

    def slope_of_ma10(self, code, end_date, days):
        df = self.data_of_days_include_end_date(code, end_date, days)
        if len(df) == 0:
            print(code)
            return 0
        closes = df['close_qfq'].to_list()
        # print(closes)
        ma10 = self.moving_average(closes, 10)
        # print(ma10)
        days = np.arange(len(ma10))  # 创建一个天数数组，与MA10对齐
        slope, intercept = np.polyfit(days, ma10, 1)
        # print(slope)

        # 给定数据
        data = np.array(ma10)

        # 创建与数据对应的x轴（索引）
        x = np.arange(len(data))

        # 使用numpy的polyfit进行线性拟合，返回斜率和截距
        slope, intercept = np.polyfit(x, data, 1)
        return slope
        # 计算拟合的y值
        fitted_line = slope * x + intercept

        # 打印斜率和截距
        print(f"拟合的直线方程: y = {slope:.4f}x + {intercept:.4f}")

        # 绘制原始数据和拟合直线
        plt.scatter(x, data, color='blue', label='原始数据')
        plt.plot(x, fitted_line, color='red', label='拟合直线')
        plt.xlabel('数据点索引')
        plt.ylabel('数据值')
        plt.title('数据的线性拟合')
        plt.legend()
        plt.show()

    def slope_of_ma5(self, code, end_date, days):
        df = self.data_of_days_include_end_date(code, end_date, days)
        if len(df) == 0:
            print(code)
            return 0
        closes = df['close_qfq'].to_list()
        # print(closes)
        ma5 = self.moving_average(closes, 5)
        # print(ma5)
        days = np.arange(len(ma5))  # 创建一个天数数组，与MA10对齐

        slope, intercept = np.polyfit(days, ma5, 1)
        # print(slope)
        return slope

        # 给定数据
        data = np.array(ma5)

        # 创建与数据对应的x轴（索引）
        x = np.arange(len(data))

        # 使用numpy的polyfit进行线性拟合，返回斜率和截距
        slope, intercept = np.polyfit(x, data, 1)

        # 计算拟合的y值
        fitted_line = slope * x + intercept

        # 打印斜率和截距
        print(f"拟合的直线方程: y = {slope:.4f}x + {intercept:.4f}")

        # 绘制原始数据和拟合直线
        plt.scatter(x, data, color='blue', label='原始数据')
        plt.plot(x, fitted_line, color='red', label='拟合直线')
        plt.xlabel('数据点索引')
        plt.ylabel('数据值')
        plt.title('数据的线性拟合')
        plt.legend()
        plt.show()

    def get_circ_mv(self, code, date):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        dtype_dict = {'trade_date': str}
        df = pd.read_csv(basic_csv_path, dtype=dtype_dict)
        # df = self.daily_line_dict[code]
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            return row.iloc[0]['circ_mv']
        # return 100

    def get_buy_price(self, code, date):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        dtype_dict = {'trade_date': str}
        df = pd.read_csv(basic_csv_path, dtype=dtype_dict)
        # 将日期列转换为日期时间类型
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        # 筛选指定日期之前3天的数据
        filtered_df = df[df['trade_date'] < date]

        recent_two_days = filtered_df.tail(2)
        tow_min_low_price = round(recent_two_days['low_qfq'].min(), 2)
        today = df[df['trade_date'] == date]
        if not today.empty:
            today_open_price = today.iloc[0]['open_qfq']
            if today_open_price < tow_min_low_price:
                return round(today_open_price, 2)
            else:
                return tow_min_low_price
        return tow_min_low_price

    def is_limit_down(self, code, date):
        basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径

        dtype_dict = {'trade_date': str}
        df = pd.read_csv(basic_csv_path, dtype=dtype_dict)
        # df = self.daily_line_dict[code]
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            if str(row['limit'].values[0]) == 'D':
                return True
            else:
                return False
        else:
            return None
