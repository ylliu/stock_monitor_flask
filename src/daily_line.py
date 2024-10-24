class DailyLine:
    def __init__(self, trade_date, open_price, close_price, high_price, low_price, volume, turnover_rate, code,
                 average_price, max_pct_change, up_shadow_pct, volume_ratio, pre_close=None):
        self.trade_date = trade_date  # 交易日期
        self.open = open_price  # 开盘价
        self.close = close_price  # 收盘价
        self.high = high_price  # 最高价
        self.low = low_price  # 最低价
        self.vol = volume  # 交易量
        self.turnover_rate = turnover_rate  # 换手率
        self.code = code
        self.average_price = average_price
        self.max_pct_change = max_pct_change
        self.up_shadow_pct = up_shadow_pct
        self.volume_ratio = volume_ratio
        self.pre_close = pre_close

    def __repr__(self):
        return f"DailyLine(trade_date={self.trade_date}, open={self.open}, close={self.close}, " \
               f"high={self.high}, low={self.low}, vol={self.vol},turnover_rate={self.turnover_rate})," \
               f"code={self.code},average_price={self.average_price},pct_change={self.max_pct_change}," \
               f"up_shadow_pct={self.up_shadow_pct}"

    def is_positive(self):
        return self.close > self.open

    def is_negative(self):
        return self.close < self.open

    def is_volume_increased(self, volume, volume_rate_min, volume_rate_max):
        if volume < 1.0:
            return False
        res1 = self.vol / volume > volume_rate_min
        res2 = self.vol / volume < volume_rate_max
        return self.vol / volume > volume_rate_min and self.vol / volume < volume_rate_max

    def is_volume_decreased(self, volume):
        return self.vol < volume * 1.1

    def is_lowest_during_four_days(self, low_price):
        return self.low < min(low_price)

    def increase_with_volume_spike(self, volume, volume_rate):
        return self.is_positive() and self.is_volume_increased(volume, volume_rate)

    def retrace_with_low_volume(self, volume):
        return self.is_negative() and self.is_volume_decreased(volume)

    def is_higher_than_yesterday_close_price(self, pre_close_price):
        return self.close > pre_close_price

    def is_lower_than_volume_increased_max_price(self, max_price):
        return self.close < max_price

    def first_day_explode(self, vol, pre_vol, rate):
        if vol < 1.0:
            return False
        return vol / pre_vol > rate