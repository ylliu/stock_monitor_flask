import os.path
from datetime import datetime, time, timedelta

from pandas import Timestamp
from holidays import country_holidays

import pandas as pd


class DataInterfaceBase:

    def get_daily_lines(self, code, end_date, periods):
        # 这里只是一个示例，实际实现应该根据具体的数据源来编写
        raise NotImplementedError("This method must be implemented in a subclass.")

    def get_name(self, code):
        raise NotImplementedError("This method must be implemented in a subclass.")

    def get_average_price(self, code, start_date, end_date):
        raise NotImplementedError("This method must be implemented in a subclass.")

    def change_pct_of_day(self, high_price, pre_close, low_price):
        under_water = 0.0
        if low_price < pre_close:
            under_water = abs(round(((low_price - pre_close) / pre_close) * 100, 2))

        return round(((high_price - pre_close) / pre_close) * 100, 2) + under_water

    def up_shadow_pct_of_day(self, high_price, pre_close, close_price, open_price):
        return round((high_price - max(open_price, close_price)) / pre_close * 100, 2)

    def is_between_9_30_and_19_00(self):
        # 获取当前时间
        now = datetime.now()

        # 创建表示早上9:30和下午3:00的时间对象
        start_time = time(9, 30)
        end_time = time(19, 0)

        # 比较当前时间是否在指定时间范围内
        # 注意：我们需要将当前时间的日期部分剥离，只比较时间部分
        # datetime.time()对象没有直接的比较方法，所以我们需要将它们转换为datetime对象进行比较
        # 但这里我们只需要比较时间，所以可以直接使用time对象进行比较

        # 注意：我们还需要考虑跨日的情况（虽然在这个特定的例子中不太可能出现）
        # 但为了更通用，我们可以将时间转换为一天中的分钟数进行比较
        now_minutes = now.hour * 60 + now.minute
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute

        # 考虑到时间的循环性，如果现在时间小于开始时间，可能是因为已经过了午夜
        # 所以我们还需要检查是否小于开始时间且大于结束时间，但这在这个特定情况下不适用

        # 直接比较分钟数
        if start_minutes <= now_minutes < end_minutes:
            return True
        else:
            return False

    def find_nearest_trading_day(self, today=None):
        """
        找到距离今天最近的一个交易日
        """
        if today is None:
            today = datetime.now().date()

            # 向前查找直到找到交易日
        current_date = datetime.strptime(today, '%Y%m%d')
        while not self.is_a_stock_trading_day(current_date):
            current_date -= timedelta(days=1)

        return current_date

    def find_nearest_trading_day2(self, today=None):
        """
        找到距离今天最近的一个交易日 今天19：00之前都不算
        """
        if today is None:
            today = datetime.now().date()

            # 向前查找直到找到交易日
        current_date = datetime.strptime(today, '%Y%m%d')
        while not self.is_a_stock_trading_day(current_date):
            current_date -= timedelta(days=1)
        # todo add before 19:00之前，都使用前一个交易日
        if self.is_between_00_00_and_18_59():
            current_date -= timedelta(days=1)
            while not self.is_a_stock_trading_day(current_date):
                current_date -= timedelta(days=1)
        return current_date

    def is_between_00_00_and_18_59(self):
        # 获取当前时间
        now = datetime.now()

        # 创建表示早上9:30和下午3:00的时间对象
        start_time = time(0, 0)
        end_time = time(18, 59)

        # 比较当前时间是否在指定时间范围内
        # 注意：我们需要将当前时间的日期部分剥离，只比较时间部分
        # datetime.time()对象没有直接的比较方法，所以我们需要将它们转换为datetime对象进行比较
        # 但这里我们只需要比较时间，所以可以直接使用time对象进行比较

        # 注意：我们还需要考虑跨日的情况（虽然在这个特定的例子中不太可能出现）
        # 但为了更通用，我们可以将时间转换为一天中的分钟数进行比较
        now_minutes = now.hour * 60 + now.minute
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute

        # 考虑到时间的循环性，如果现在时间小于开始时间，可能是因为已经过了午夜
        # 所以我们还需要检查是否小于开始时间且大于结束时间，但这在这个特定情况下不适用

        # 直接比较分钟数
        if start_minutes <= now_minutes < end_minutes:
            return True
        else:
            return False

    def find_pre_data_publish_date(self, today, hour):
        if self.is_a_stock_trading_day(today):
            if hour < 19:
                date = self.find_pre_nearest_trading_day(today)
                return self.find_pre_nearest_trading_day(date.strftime("%Y%m%d"))
            else:
                return self.find_pre_nearest_trading_day(today)
        else:
            return self.find_pre_nearest_trading_day(today)

    def find_pre_nearest_trading_day(self, today=None):
        """
        找到距离今天最近的一个交易日 今天如果是交易日 不算
        """
        if today is None:
            today = datetime.now().date()

            # 向前查找直到找到交易日
        current_date = datetime.strptime(today, '%Y%m%d')
        if self.is_a_stock_trading_day(current_date):
            current_date -= timedelta(days=1)
        while not self.is_a_stock_trading_day(current_date):
            current_date -= timedelta(days=1)

        return current_date

    def is_data_updated(self, stock):
        file_path = f'src/data/{stock}_daily_data.csv'
        if not os.path.exists(file_path):
            return False
        last_date = self.find_last_date_in_csv(file_path)
        today = self.get_today_date()
        now = datetime.now()
        # 获取当前小时数（24小时制）
        current_hour = now.hour
        published_date = self.get_published_date(today, current_hour)
        return published_date == last_date

    def get_published_date(self, today, hour):
        if self.is_a_stock_trading_day(today):
            if hour < 19:
                return self.find_pre_nearest_trading_day(today)
            else:
                return self.find_nearest_trading_day(today)
        else:
            return self.find_nearest_trading_day(today)

    def find_last_date_in_csv(self, file_path):
        try:
            df = pd.read_csv(file_path, parse_dates=['trade_date'])
            last_date = df['trade_date'].max()
        except FileNotFoundError:
            last_date = None
        return last_date

    def get_today_date(self):
        now = datetime.now()
        formatted_date = now.strftime('%Y%m%d')
        return formatted_date

    def is_a_stock_trading_day(self, date):
        # 创建A股交易日历对象
        # 将字符串转换为pandas的Timestamp对象
        date = Timestamp(date)
        cn_holidays = country_holidays('CN')
        if date.weekday() >= 5:  # 周六是5，周日是6
            return False

            # 判断是否是公众节假日
        if date in cn_holidays:
            return False
        return True

    def is_data_already_publish(self):
        today = self.get_today_date()
        if not self.is_a_stock_trading_day(today):
            return True
        # 获取当前时间
        now = datetime.now()

        # 设置当天的19:00和次日凌晨3:00的时间对象
        today_1900 = now.replace(hour=19, minute=0, second=0, microsecond=0)
        # 注意：为了判断小于次日凌晨3点，我们创建了一个表示次日0点的时间，并加上3小时
        next_day_0300 = (now + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)

        # 如果当前时间大于当天的19:00且小于次日凌晨3:00
        if today_1900 < now < next_day_0300:
            return True
        else:
            return False

    def is_updated_last_trade_date(self, code):
        latest_date_in_csv = self.find_last_date_in_csv(f'src/data/{code}_daily_data.csv')
        pre_trade_date = self.find_pre_nearest_trading_day(self.get_today_date())
        return latest_date_in_csv == pre_trade_date
