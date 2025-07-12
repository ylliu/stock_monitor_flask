import os
from datetime import datetime

import pandas
import pandas as pd

from src.daily_line import DailyLine
from src.data_interface_base import DataInterfaceBase
from src.tushare_interface import TushareInterface


class LocalCsvInterface(DataInterfaceBase):
    def __init__(self):
        self.realtime_daily_lines = {}
        self.daily_line_dict = {}

    def get_all_realtime_data(self, stock_list):
        tushare = TushareInterface()
        self.realtime_daily_lines.clear()
        self.realtime_daily_lines = tushare.get_all_stock_realtime_lines(stock_list)

    def get_daily_lines(self, code, end_date, back_days):

        # start = time.time()
        # df_basic_filtered = self.data_between_from_csv(code, end_date, back_days)
        df_basic_filtered = self.data_between_from_memory(code, end_date, back_days)
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
                                   code, average_price, max_pct_change, up_shadow_pct, volume_ratio)
            daily_lines.append(daily_line)

        today = self.get_today_date()
        if not isinstance(end_date, str):
            end_date = end_date.strftime("%Y%m%d")
        if self.is_a_stock_trading_day(today) and today == end_date and self.is_between_9_30_and_19_00():
            daily_realtime = self.realtime_daily_lines[code]
            daily_lines.append(daily_realtime)
        # end = time.time()
        # print('cost:', end - start)
        return daily_lines

    def get_daily_lines_from_csv(self, code, end_date, back_days):

        # start = time.time()
        # df_basic_filtered = self.data_between_from_csv(code, end_date, back_days)
        pre_date = self.find_nearest_trading_day2(end_date.strftime("%Y%m%d"))
        df_basic_filtered = self.data_between_from_csv(code, pre_date, back_days)
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
                                   code, average_price, max_pct_change, up_shadow_pct, volume_ratio)
            daily_lines.append(daily_line)

        today = self.get_today_date()
        if not isinstance(end_date, str):
            end_date = end_date.strftime("%Y%m%d")
        if self.is_a_stock_trading_day(today) and today == end_date and self.is_between_9_30_and_19_00():
            # daily_realtime = self.realtime_daily_lines[code]
            tushare_interface = TushareInterface()
            daily_line_value = tushare_interface.gat_realtime_data_of_split_stocks(code)
            daily_lines_realtime = daily_line_value[code]
            date = str(datetime.strptime(daily_lines_realtime.trade_date, "%Y%m%d"))

            daily_lines_realtime.trade_date = date
            # daily_line_real = DailyLine(daily_lines_realtime["DATE"], daily_lines_realtime["OPEN"],
            #                             daily_lines_realtime["PRICE"], daily_lines_realtime["HIGH"],
            #                             daily_lines_realtime["LOW"],
            #                             daily_lines_realtime["VOLUME"],
            #                             0,
            #                             code, 0, 0, 0, 0)
            daily_lines.append(daily_lines_realtime)
        # end = time.time()
        # print('cost:', end - start)
        return daily_lines

    def get_name(self, code):
        basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path)
        if not df_basic.empty:
            return df_basic.iloc[0]['name']
        return "名字不存在"

    def get_average_price(self, code, start_date, end_date):
        basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] <= end_date)]
        weight_avg_list = df_basic_filtered['weight_avg'].tolist()
        return weight_avg_list

    def get_close_price_of_day(self, code, date):
        basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
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
        df_basic_filtered = self.data_between_from_memory(code, end_date, back_days)
        up_times = 0
        for index, row in df_basic_filtered.iterrows():
            # 提取每一行的数据
            limit = str(row['limit'])
            if limit == 'U':
                up_times += 1
        return up_times

    def data_between_from_csv(self, code, end_date, back_days):
        basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        if not os.path.exists(basic_csv_path):
            return None
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        # print(df_basic)
        selected_row = df_basic[df_basic['trade_date'] == end_date]
        if not selected_row.empty:
            index = selected_row.index[0]
            result = df_basic.iloc[index - back_days + 1:index + 1]
            # print(result)
            return result
        # trade_dates = pd.bdate_range(end=end_date, periods=back_days)
        # start_date = trade_dates[0].strftime('%Y%m%d')
        # df_basic_filtered = df_basic.loc[(df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] <= end_date)]
        # return df_basic_filtered

    def get_before_days_down_times(self, code, end_date, back_days):
        df_basic_filtered = self.data_between_from_csv(code, end_date, back_days)
        down_times = 0
        for index, row in df_basic_filtered.iterrows():
            # 提取每一行的数据
            limit = str(row['limit'])
            if limit == 'D':
                down_times += 1
        return down_times

    def find_sideways_trading(self, code, max_vol, date):
        diff = 0
        # basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        # df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        df_basic = self.daily_line_dict[code]
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] < date)]
        df = df_basic_filtered.sort_values(by='trade_date', ascending=False)
        # date = date.strftime('%Y%m%d')
        for index, row in df.iterrows():
            if row['vol'] > max_vol:
                found_date = row['trade_date']
                days = pd.bdate_range(found_date, date)
                diff = len(days)
                return diff
        if diff == 0:
            diff = 300
        return diff

    def get_history_mean_price(self, code, end_date, how_many_days):
        df_basic_filtered = self.data_between_from_csv(code, end_date, how_many_days)
        # print(df_basic_filtered['close_qfq'].to_list())
        mean = df_basic_filtered['close_qfq'].mean()
        return round(mean, 2)

    def get_history_close_price(self, code, end_date, how_many_days):
        df = self.data_between_from_csv(code, end_date, how_many_days)
        # print(df)
        ts_code_list = df['close_qfq'].to_list()
        return ts_code_list

    def is_limit_down(self, code, date):
        # basic_csv_path = f'data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        #
        # dtype_dict = {'trade_date': str}
        # df = pd.read_csv(basic_csv_path, dtype=dtype_dict)
        df = self.daily_line_dict[code]
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            if str(row['limit'].values[0]) == 'D':
                return True
            else:
                return False
        else:
            return None

    def get_local_neg_count(self, date):
        # todo 盘中通过接口获取
        basic_csv_path = f'history_neg_count.csv'  # 基础数据的CSV文件路径
        dtype_dict = {'Date': str}
        df = pd.read_csv(basic_csv_path, dtype=dtype_dict)
        row = df[df['Date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            return row['NegCount'].values[0]

        else:
            return 0

    def load_csv_data(self, stock_list):
        index = 0
        for code in stock_list:
            index = index + 1
            basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
            if not os.path.exists(basic_csv_path):
                continue
            df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
            self.daily_line_dict[code] = df_basic

            progress = (index) / len(stock_list) * 100
            if index % 30 == 0:
                print(f"Load progress: {progress:.2f}%")

    def data_between_from_memory(self, code, end_date, back_days):
        if code in self.daily_line_dict:
            df_basic = self.daily_line_dict[code]
            trade_dates = pd.bdate_range(end=end_date, periods=back_days)
            start_date = trade_dates[0].strftime('%Y%m%d')
            df_basic_filtered = df_basic.loc[
                (df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] <= end_date)]
            return df_basic_filtered
        return None

    def get_circ_mv(self, code, date):
        df = self.daily_line_dict[code]
        date = self.find_pre_data_publish_date(date, 10)
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            return row.iloc[0]['circ_mv']
        # return 100

    def get_circ_mv3(self, code, date):
        df = self.daily_line_dict[code]
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            return row.iloc[0]['circ_mv']
        return None

    def get_circ_mv4(self, code, date):
        df = self.daily_line_dict[code]
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            return row.iloc[0]['normal_circ_mv']
        return None

    def get_circ_mv_2(self, code, date):
        basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        dtype_dict = {'trade_date': str}
        df = pd.read_csv(basic_csv_path, dtype=dtype_dict)
        # df = self.daily_line_dict[code]
        row = df[df['trade_date'] == date]
        if not row.empty:
            # 获取close_qfq的值
            return round(row.iloc[0]['circ_mv'] / 1e4, 2)
        return None

    def get_buy_price(self, code, date):
        if len(self.daily_line_dict) > 0:
            df = self.daily_line_dict[code]
        else:
            basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
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

    def data_before_days(self, code, end_date, back_days):
        if len(self.daily_line_dict) > 0:
            df_basic = self.daily_line_dict[code]
        else:
            basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
            df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        trade_dates = pd.bdate_range(end=end_date, periods=back_days + 1)
        start_date = trade_dates[0].strftime('%Y%m%d')
        df_basic_filtered = df_basic.loc[(df_basic['trade_date'] >= start_date) & (df_basic['trade_date'] < end_date)]
        return df_basic_filtered

    def average_turnover_rate_of(self, code, end_date, days):
        df = self.data_before_days(code, end_date, days)
        if len(df) == 0:
            return 0.0
        sum_turnover_rate = 0
        for index, row in df.iterrows():
            sum_turnover_rate += row['turnover_rate_f']
        average = sum_turnover_rate / len(df)
        return average

    def is_break_days_high(self, code, end_date, days):
        df = self.data_between_from_csv(code, end_date, days)
        # print(df)
        ts_code_list = df['close_qfq'].to_list()
        return ts_code_list[-1] == max(ts_code_list)
        # return ts_code_list

    def is_vol_break_days_high(self, code, end_date, days, max_vol):
        df = self.data_between_from_csv(code, end_date, days)
        # print("vol_df",df)
        ts_code_list = df['vol'].to_list()
        return max_vol == max(ts_code_list)
        # return ts_code_list

    def is_pct_up_not_more_than(self, code, end_date, days, max_pct):
        df = self.data_between_from_csv(code, end_date, days)

        # 确保数据足够
        if len(df) < days:
            return False  # 数据不足，无法计算涨幅

        # 计算第5天相对于第1天的涨幅
        start_price = df.iloc[0]['close_qfq']  # 第1天的收盘价
        end_price = df.iloc[-1]['close_qfq']  # 第5天的收盘价

        pct_change = (end_price - start_price) / start_price * 100  # 计算涨幅（%）

        return pct_change <= max_pct

    def get_single_day_data(self, code, date):
        current_dir = os.getcwd()
        basic_csv_path = os.path.join(current_dir, f'src/data/{code}_daily_data.csv')
        if not os.path.exists(basic_csv_path):
            return None
        df_basic = pd.read_csv(basic_csv_path, parse_dates=['trade_date'])
        selected_row = df_basic[df_basic['trade_date'] == date]
        if not selected_row.empty:
            return selected_row.iloc[0]
        else:
            print(f"No data found for {code} on {date}")
            return None

    def get_dates_between(self, start_date, end_date):
        # 将字符串日期转换为datetime对象
        start = datetime.strptime(start_date, '%Y%m%d').date()
        end = datetime.strptime(end_date, '%Y%m%d').date()

        # 使用pd.bdate_range生成工作日范围，不包括end_date
        trading_days = pd.bdate_range(start=start, end=end).strftime('%Y%m%d').tolist()

        return trading_days[1:]
