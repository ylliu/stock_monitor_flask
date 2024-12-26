import os.path
import time as atime
from datetime import datetime

import pandas as pd
import tushare as ts

from src.daily_line import DailyLine
from src.data_interface_base import DataInterfaceBase


class TushareInterface(DataInterfaceBase):
    def __init__(self):
        self.token = 'c632fdfffc18c3b68ba65351dde6638ff8ff147d6033b12da8d2be86'  # 替换为你的tushare token
        ts.set_token(self.token)
        self.count = 0
        self.max_retries = 1000000

    def get_daily_lines(self, code, end_date, periods):
        for attempt in range(self.max_retries):
            try:
                daily_lines = []
                # start = time.time()
                pro = ts.pro_api()
                # 设置股票代码和查询的时间范围
                ts_code = code  # 示例股票代码，
                end_date = end_date  # 当前日期或你选择的日期
                today = self.get_today_date()

                if end_date == today and self.is_between_9_30_and_19_00():
                    end_date_new = pd.to_datetime(end_date)
                    end_date_new = end_date_new - pd.Timedelta(days=1)
                    end_date_new = end_date_new.strftime('%Y%m%d')
                    trade_dates = pd.bdate_range(end=end_date_new, periods=periods - 1)
                    start_time = trade_dates[0].strftime('%Y%m%d')
                    df = pro.stk_factor(ts_code=ts_code, start_date=start_time, end_date=end_date_new)

                else:
                    trade_dates = pd.bdate_range(end=end_date, periods=periods)
                    start_time = trade_dates[0].strftime('%Y%m%d')
                    df = pro.stk_factor(ts_code=ts_code, start_date=start_time, end_date=end_date)

                df = df[
                    ['ts_code', 'trade_date', 'open_qfq', 'close_qfq', 'high_qfq', 'low_qfq', 'vol', 'pre_close_qfq']]
                if not df['trade_date'].is_monotonic_increasing:
                    # 如果不是，则按日期排序

                    df = df.sort_values(by='trade_date')
                daily_basic = pro.daily_basic(ts_code=code, start_date=start_time, end_daZte=end_date)
                if not daily_basic['trade_date'].is_monotonic_increasing:
                    # 如果不是，则按日期排序
                    daily_basic = daily_basic.sort_values(by='trade_date')

                df = df.merge(daily_basic[['trade_date', 'turnover_rate_f', 'volume_ratio']], on='trade_date',
                              how='left')
                for index, row in df.iterrows():
                    # 提取每一行的数据
                    trade_date = row['trade_date']
                    open_price = row['open_qfq']
                    close_price = row['close_qfq']
                    high_price = row['high_qfq']
                    low_price = row['low_qfq']
                    volume = row['vol']
                    turnover_rate_f = row['turnover_rate_f']
                    code = row['ts_code']
                    pre_close = row['pre_close_qfq']
                    volume_ratio = row['volume_ratio']
                    max_pct_change = self.change_pct_of_day(high_price, pre_close, low_price)
                    up_shadow_pct = self.up_shadow_pct_of_day(high_price, pre_close, close_price, open_price)
                    # 创建一个新的DailyLine对象并添加到列表中
                    daily_line = DailyLine(trade_date, open_price, close_price, high_price, low_price, volume,
                                           turnover_rate_f,
                                           code, 0.0, max_pct_change, up_shadow_pct, volume_ratio)
                    daily_lines.append(daily_line)
                # end = time.time()
                # print('cost:', end - start)
                # print(daily_lines)
                # 获取实时数据
                today = self.get_today_date()
                if self.is_a_stock_trading_day(today) and today == end_date and self.is_between_9_30_and_19_00():
                    daily_realtime = self.gat_realtime_data(code)
                    daily_lines.append(daily_realtime)
                return daily_lines
            except Exception as e:
                print(f"发生异常: {e}", code)
                atime.sleep(1)

    # def change_pct_of_day(self, high_price, pre_close, low_price):
    #     under_water = 0.0
    #     if low_price < pre_close:
    #         under_water = abs(round(((low_price - pre_close) / pre_close) * 100, 2))
    #
    #     return round(((high_price - pre_close) / pre_close) * 100, 2) + under_water

    def get_turnover_rate_f(self, code, start_date, end_date):
        for attempt in range(self.max_retries):
            try:
                pro = ts.pro_api()
                df = pro.daily_basic(ts_code=code, start_date=start_date, end_date=end_date)
                return df['turnover_rate_f'].tolist()
            except Exception as e:
                print(f"发生异常: {e}", code)
                atime.sleep(1)

    def get_average_price(self, code, start_date, end_date):
        for attempt in range(self.max_retries):
            try:
                pro = ts.pro_api()
                df = pro.cyq_perf(ts_code=code, start_date=start_date, end_date=end_date)
                return df['weight_avg'].tolist()
            except Exception as e:
                print(f"发生异常: {e}", code)
                atime.sleep(1)

    def get_name(self, code):
        for attempt in range(self.max_retries):
            try:
                pro = ts.pro_api()
                df = pro.stock_basic(ts_code=code)
                return df.iloc[0]['name']
            except Exception as e:
                print(f"发生异常: {e}", code)
                atime.sleep(1)

    def get_names(self, code):
        for attempt in range(self.max_retries):
            try:
                pro = ts.pro_api()
                df = pro.stock_basic(ts_code=code, fields=['ts_code', 'name'])
                if not df['ts_code'].is_monotonic_increasing:
                    # 如果不是，则按日期排序
                    df = df.sort_values(by='ts_code')
                return df['name']
            except Exception as e:
                print(f"发生异常: {e}", code)
                atime.sleep(1)

    def get_all_stocks(self, market):
        for attempt in range(self.max_retries):
            try:
                pro = ts.pro_api()
                # 获取股票基本信息
                df_basic = pro.stock_basic(exchange='', market=market, list_status='L', fields='ts_code,name')
                # 过滤掉名称中包含'ST'或'*ST'的股票
                filtered_basic = df_basic[~df_basic['name'].str.contains('ST', na=False, case=False)]
                filtered_basic = filtered_basic[~filtered_basic['name'].str.contains('退', na=False, case=False)]

                # 提取过滤后的股票代码
                filtered_codes = filtered_basic['ts_code'].tolist()
                stopped_codes = ['000040.SZ', '000413.SZ', '000982.SZ', '002308.SZ', '002505.SZ', '300630.SZ',
                                 '603285.SH', '603350.SH', '600543.SH']
                filtered_codes_cleaned = [code for code in filtered_codes if code not in stopped_codes]
                return filtered_codes_cleaned
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_all_stocks_less_than50e(self):
        for attempt in range(self.max_retries):
            try:
                pro = ts.pro_api()
                # 获取股票基本信息
                df = pro.daily_basic(ts_code='',
                                     trade_date=self.find_nearest_trading_day(self.get_today_date()).strftime('%Y%m%d'),
                                     fields='ts_code,circ_mv')
                stock_list = df['ts_code'].to_list()

                print(df)
                df_gem_stocks = df[df['ts_code'].str.startswith(('301', '300'))]
                print(df_gem_stocks)
                # print(len(df_gem_stocks))
                # # 筛选出流通市值小于50亿的股票（注意：total_mv单位是元，需要转换成万元进行比较）
                # # 假设total_mv已经是亿元单位，如果实际单位是元，则需要除以10000进行转换
                # df_gem_stocks['circ_mv_b'] = df_gem_stocks['circ_mv'] / 1e4
                # circ_mv = df_gem_stocks[df_gem_stocks['circ_mv_b'] < 50]
                # return circ_mv['ts_code'].to_list()
                break
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_back_trade_date_of(self, end_date, periods):
        pro = ts.pro_api()
        trade_dates = pd.bdate_range(end=end_date, periods=periods)
        print(trade_dates)

    def save_data_to_csv(self, stock_list):
        pro = ts.pro_api()
        print(len(stock_list))
        index = 0
        for stock in stock_list:
            for attempt in range(self.max_retries):
                try:
                    # 设置股票代码和查询的时间范围
                    print(stock)
                    end_date = self.get_today_date()  # 当前日期或你选择的日期
                    trade_dates = pd.bdate_range(end=end_date, periods=365)
                    start_time = trade_dates[0].strftime('%Y%m%d')
                    df = self.get_data_between_dates(pro, start_time, end_date, stock)
                    # 将DataFrame保存到CSV文件
                    csv_file_path = f'data/{stock}_daily_data.csv'  # 可以根据你的需要调整文件路径和文件名
                    print('path:', csv_file_path)
                    df.to_csv(csv_file_path, index=False)  # 不包含索引保存
                    index += 1
                    progress = index / len(stock_list) * 100
                    if index % 5 == 0:
                        print(f"Processing progress: {progress:.2f}%")
                    break
                except Exception as e:
                    print(f"发生异常: {e}")
                    atime.sleep(1)

    def get_data_between_dates(self, pro, start_time, end_date, stock):
        df = pro.stk_factor(ts_code=stock, start_date=start_time, end_date=end_date)
        df['name'] = self.get_name(stock)
        df = df[['ts_code', 'name', 'trade_date', 'open_qfq', 'close_qfq', 'high_qfq', 'low_qfq', 'vol',
                 'pre_close_qfq']]
        if not df['trade_date'].is_monotonic_increasing:
            # 如果不是，则按日期排序

            df = df.sort_values(by='trade_date')
        daily_basic = pro.daily_basic(ts_code=stock, start_date=start_time, end_daZte=end_date)
        if not daily_basic['trade_date'].is_monotonic_increasing:
            # 如果不是，则按日期排序
            daily_basic = daily_basic.sort_values(by='trade_date')
        df = df.merge(daily_basic[['trade_date', 'turnover_rate_f', 'volume_ratio']], on='trade_date', how='left')
        averages = pro.cyq_perf(ts_code=stock, start_date=start_time, end_date=end_date)
        if not averages['trade_date'].is_monotonic_increasing:
            # 如果不是，则按日期排序
            averages = averages.sort_values(by='trade_date')
        df = df.merge(averages[['trade_date', 'weight_avg']], on='trade_date', how='left')
        limits = pro.limit_list_d(ts_code=stock, start_date=start_time, end_date=end_date)
        if not limits['trade_date'].is_monotonic_increasing:
            # 如果不是，则按日期排序
            limits = limits.sort_values(by='trade_date')
        df = df.merge(limits[['trade_date', 'limit']], on='trade_date', how='left')

        circ_mvs = pro.daily_basic(ts_code=stock,
                                   start_date=start_time, end_date=end_date,
                                   fields=['ts_code', 'trade_date', 'free_share', 'close', 'circ_mv'])
        circ_mvs = circ_mvs.sort_values(by='trade_date')
        circ_mvs = circ_mvs.assign(circ_mv=circ_mvs['free_share'] * circ_mvs['close'] / 1e4,
                                   normal_circ_mv=circ_mvs['circ_mv'] / 1e4).round(2)
        circ_mvs = circ_mvs.sort_values(by='trade_date')
        df = pd.merge(df, circ_mvs[['trade_date', 'circ_mv', 'normal_circ_mv']], on='trade_date', how='left')
        return df

    def get_data_between_dates_fast(self, pro, start_time, end_date, stock):
        df = pro.stk_factor(ts_code=stock, start_date=start_time, end_date=end_date,
                            fields=['ts_code', 'trade_date', 'open_qfq', 'close_qfq', 'high_qfq', 'low_qfq', 'vol',
                                    'pre_close_qfq'])
        df = df.sort_values(by=['ts_code', 'trade_date'])
        df_names = pro.stock_basic(ts_code=stock, fields=['ts_code', 'name'])
        if not df_names['ts_code'].is_monotonic_increasing:
            # 如果不是，则按日期排序
            df_names = df_names.sort_values(by='ts_code')
        merged_df = pd.merge(df, df_names[['ts_code', 'name']], on='ts_code', how='left')

        df = merged_df[['ts_code', 'name', 'trade_date', 'open_qfq', 'close_qfq', 'high_qfq', 'low_qfq', 'vol',
                        'pre_close_qfq']]

        daily_basic = pro.daily_basic(ts_code=stock, start_date=start_time, end_date=end_date,
                                      fields=['ts_code', 'trade_date', 'turnover_rate_f', 'volume_ratio'])
        daily_basic = daily_basic.sort_values(by=['ts_code', 'trade_date'])

        df = pd.merge(df, daily_basic, on=['ts_code', 'trade_date'], how='left')

        averages = pro.cyq_perf(ts_code=stock, start_date=start_time, end_date=end_date,
                                fields=['ts_code', 'trade_date', 'weight_avg'])
        averages = averages.sort_values(by=['ts_code', 'trade_date'])
        df = pd.merge(df, averages, on=['ts_code', 'trade_date'], how='left')
        limits = pro.limit_list_d(ts_code=stock, start_date=start_time, end_date=end_date,
                                  fields=['ts_code', 'trade_date', 'limit'])
        limits = limits.sort_values(by=['ts_code', 'trade_date'])
        df = pd.merge(df, limits, on=['ts_code', 'trade_date'], how='left')
        return df

    # def up_shadow_pct_of_day(self, high_price, pre_close, close_price, open_price):
    #     return round((high_price - max(open_price, close_price)) / pre_close * 100, 2)
    #     pass

    def gat_realtime_data(self, code):
        for attempt in range(self.max_retries):
            try:
                df = ts.realtime_quote(ts_code=code)
                if len(df) == 0:
                    continue
                data = df.iloc[0]
                # print(data)
                daily_line = DailyLine(data['DATE'], data['OPEN'], data['PRICE'], data['HIGH'], data['LOW'],
                                       data['VOLUME'],
                                       0.0, code, data['PRE_CLOSE'], 0.0, 0.0, 0.0)
                # print(daily_line)
                return daily_line
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_dates_between(self, start_date, end_date):
        # 将字符串日期转换为datetime对象
        start = datetime.strptime(start_date, '%Y%m%d').date()
        end = datetime.strptime(end_date, '%Y%m%d').date()

        # 使用pd.bdate_range生成工作日范围，不包括end_date
        trading_days = pd.bdate_range(start=start, end=end).strftime('%Y%m%d').tolist()

        return trading_days[1:]

    def update_csv_data(self, stock_list, periods):
        pro = ts.pro_api()
        print(len(stock_list))
        index = 0
        for stock in stock_list:
            print(stock)
            index += 1
            progress = index / len(stock_list) * 100
            if index % 10 == 0:
                print(f"save data to local progress: {progress:.2f}%")
            if self.is_data_updated(stock):
                continue
            print('to_update', stock)
            for attempt in range(self.max_retries):
                try:
                    today = datetime.now().date().strftime('%Y%m%d')
                    file_path = f'src/data/{stock}_daily_data.csv'
                    if os.path.exists((file_path)):
                        last_date = self.find_last_date_in_csv(file_path).strftime('%Y%m%d')
                    else:
                        last_date = pd.bdate_range(end=today, periods=periods).strftime('%Y%m%d')[0]
                    dates_to_fetch = self.get_dates_between(last_date, today)
                    if len(dates_to_fetch) == 0:
                        break
                    # print(dates_to_fetch)
                    new_data_frames = self.get_data_between_dates(pro, dates_to_fetch[0], dates_to_fetch[-1], stock)

                    if len(new_data_frames) == 0:
                        break
                    if not os.path.exists((file_path)):
                        new_data_frames.to_csv(file_path, index=False)
                        break

                    # 否则，先读取现有数据，然后添加新数据
                    df_existing = pd.read_csv(file_path)
                    df_updated = pd.concat([df_existing, new_data_frames],
                                           ignore_index=True)
                    df_updated.to_csv(file_path, index=False)

                    break
                except Exception as e:
                    print(f"发生异常: {e}")
                    atime.sleep(1)

    def update_csv_data_one_time(self, stock_str, stock_list):
        pro = ts.pro_api()
        trade_date = self.find_nearest_trading_day2(today=self.get_today_date()).strftime('%Y%m%d')
        new_data_frames = self.get_data_between_dates_fast(pro, trade_date, trade_date, stock_str)
        for stock in stock_list:
            if self.is_data_updated(stock):
                continue
            file_path = f'src/data/{stock}_daily_data.csv'
            filtered_df = new_data_frames[new_data_frames['ts_code'] == stock]
            if len(filtered_df) == 0:
                break
            if not os.path.exists((file_path)):
                filtered_df.to_csv(file_path, index=False)
                break

                # 否则，先读取现有数据，然后添加新数据
            df_existing = pd.read_csv(file_path)
            df_updated = pd.concat([df_existing, filtered_df],
                                   ignore_index=True)
            df_updated.to_csv(file_path, index=False)

    def update_local_csv_data_fast(self, stock_list):
        # stock_list = ['000001.SZ']
        print('start update local csv data')
        groups = [stock_list[i:i + 100] for i in range(0, len(stock_list), 100)]
        grouped_strings = [','.join(group) for group in groups]
        index = 0
        for group_str in grouped_strings:
            for attempt in range(self.max_retries):
                try:
                    self.update_csv_data_one_time(group_str, groups[index])
                    break
                except Exception as e:
                    print(f"发生异常: {e}")
                    atime.sleep(1)
            index += 1
            progress = index / len(grouped_strings) * 100
            print(f"update local csv data progress: {progress:.2f}%")

    def gat_realtime_data_of_split_stocks(self, code):
        daily_lines = {}
        for attempt in range(self.max_retries):
            try:
                df = ts.realtime_quote(ts_code=code)
                if len(df) == 0:
                    continue
                for index, data in df.iterrows():
                    daily_line = DailyLine(data['DATE'], data['OPEN'], data['PRICE'], data['HIGH'], data['LOW'],
                                           data['VOLUME'] / 100.0,
                                           0.0, data['TS_CODE'], data['PRE_CLOSE'], 0.0, 0.0, 0.0, data['PRE_CLOSE'])
                    daily_lines[data['TS_CODE']] = daily_line

                return daily_lines
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_all_stock_realtime_lines(self, stock_list):
        daily_lines = {}
        index = 0
        groups = [stock_list[i:i + 50] for i in range(0, len(stock_list), 50)]
        if len(groups) > 1:
            grouped_strings = [','.join(group) for group in groups]
        else:
            grouped_strings = stock_list
        for stock_str in grouped_strings:
            daily_lines_split = self.gat_realtime_data_of_split_stocks(stock_str)
            daily_lines.update(daily_lines_split)
            index += 1
            progress = index / len(grouped_strings) * 100
            print(f"update realtime data progress: {progress:.2f}%")

        return daily_lines

    def get_circ_mv(self, code, lower_date):
        pro = ts.pro_api()
        for attempt in range(self.max_retries):
            try:
                df = pro.daily_basic(ts_code=code,
                                     trade_date=self.find_nearest_trading_day(lower_date).strftime('%Y%m%d'),
                                     fields='ts_code,free_share,close')
                if len(df) > 0:
                    return round((df['free_share'].to_list()[0] * df['close'].to_list()[0]) / 1e4, 2)
                return 100000
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_normal_circ_mv(self, code, date):
        pro = ts.pro_api()
        for attempt in range(self.max_retries):
            try:
                df = pro.daily_basic(ts_code=code,
                                     trade_date=self.find_nearest_trading_day(date).strftime('%Y%m%d'),
                                     fields='ts_code,circ_mv')
                if len(df) > 0:
                    return round(df['circ_mv'].iloc[0] / 1e4, 2)
                return 100000
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_concept(self, code):
        pro = ts.pro_api()
        for attempt in range(self.max_retries):
            try:
                df = pro.concept_detail(ts_code=code)
                # 如果需要，确保concept_name是字符串类型
                df['concept_name'] = df['concept_name'].astype(str)

                # 使用str.cat拼接，sep参数用于指定拼接的分隔符，这里使用空字符串表示无缝拼接
                concatenated_string = df['concept_name'].str.cat(sep=',')
                return concatenated_string
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_70_percent_chips_concentration(self, code, date):
        pro = ts.pro_api()
        for attempt in range(self.max_retries):
            try:
                df = pro.cyq_perf(ts_code=code,
                                  trade_date=date,
                                  fields='ts_code,cost_15pct,cost_85pct')
                # print(df)
                if len(df) > 0:
                    concentration = (df.iloc[0]['cost_85pct'] - df.iloc[0]['cost_15pct']) / (
                            df.iloc[0]['cost_85pct'] + df.iloc[0]['cost_15pct'])
                    return round(concentration * 100, 2)
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_realtime_price(self, code):
        for attempt in range(self.max_retries):
            try:
                df = ts.realtime_quote(ts_code=code)
                if len(df) == 0:
                    continue
                data = df.iloc[0]
                return data['PRICE']
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_realtime_info(self, code):
        for attempt in range(self.max_retries):
            try:
                print(code)
                df = ts.realtime_quote(ts_code=code)
                if len(df) == 0:
                    continue

                return df[['NAME', 'TS_CODE', 'PRE_CLOSE', 'LOW', 'PRICE']]
            except Exception as e:
                print(f"发生异常_realtime_info: {e}")
                atime.sleep(1)

    def get_realtime_change(self, code):
        for attempt in range(self.max_retries):
            try:
                df = ts.realtime_quote(ts_code=code)
                if len(df) == 0:
                    continue
                data = df.iloc[0]
                change = round((data['PRICE'] - data['PRE_CLOSE']) / data['PRE_CLOSE'] * 100, 2)
                return change
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)

    def get_five_days_mean(self, price, code):
        if self.is_between_9_30_and_19_00() and self.is_a_stock_trading_day(self.get_today_date()):
            pre_date = self.find_pre_nearest_trading_day(self.get_today_date())
            before_four_price = self.get_history_close_price(code, pre_date, 4)
            if before_four_price is None:
                return None
            before_four_price.append(price)
            five_mean_price = sum(before_four_price) / len(before_four_price)
        else:
            pre_date = self.find_pre_nearest_trading_day(self.get_today_date())
            # print(code)
            five_mean_price = self.get_history_mean_price(code, pre_date, 5)
        return five_mean_price

    def get_ten_days_mean(self, price, code):
        if self.is_between_9_30_and_19_00() and self.is_a_stock_trading_day(self.get_today_date()):
            pre_date = self.find_pre_nearest_trading_day(self.get_today_date())
            before_nine_price = self.get_history_close_price(code, pre_date, 9)
            if before_nine_price is None:
                return None
            before_nine_price.append(price)
            ten_mean_price = sum(before_nine_price) / len(before_nine_price)
        else:
            pre_date = self.find_pre_nearest_trading_day(self.get_today_date())
            ten_mean_price = self.get_history_mean_price(code, pre_date, 10)
        return ten_mean_price

    def get_history_close_price(self, code, end_date, how_many_days):
        df = self.data_between_from_csv(code, end_date, how_many_days)
        # print(df)
        if df is None:
            return None
        ts_code_list = df['close_qfq'].to_list()
        return ts_code_list

    def data_between_from_csv(self, code, end_date, back_days):
        basic_csv_path = f'src/data/{code}_daily_data.csv'  # 基础数据的CSV文件路径
        cur = (os.getcwd())
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

    def get_history_mean_price(self, code, end_date, how_many_days):
        df_basic_filtered = self.data_between_from_csv(code, end_date, how_many_days)
        # print(end_date)
        # print(df_basic_filtered['close_qfq'].to_list())
        if df_basic_filtered is None:
            return None
        mean = df_basic_filtered['close_qfq'].mean()
        return round(mean, 2)

    def get_realtime_low(self, code):
        for attempt in range(self.max_retries):
            try:
                df = ts.realtime_quote(ts_code=code)
                if len(df) == 0:
                    continue
                data = df.iloc[0]
                return data['LOW']
            except Exception as e:
                print(f"发生异常: {e}")
                atime.sleep(1)
