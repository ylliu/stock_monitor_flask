from unittest import TestCase

from src.tushare_interface import TushareInterface


class TestTushareInterface(TestCase):
    def test_get_five_days_mean(self):
        tushare_interface = TushareInterface()
        ma5 = tushare_interface.get_five_days_mean(10.4, '300001.SZ')
        self.assertEqual(22.29, ma5)

    def test_get_ten_days_mean(self):
        tushare_interface = TushareInterface()
        ma10 = tushare_interface.get_ten_days_mean(10.4, '300001.SZ')
        self.assertEqual(22.42, ma10)

    def test_get_history_mean_price(self):
        tushare_interface = TushareInterface()
        pre_date = tushare_interface.find_pre_nearest_trading_day(tushare_interface.get_today_date())
        ma10 = tushare_interface.get_history_mean_price('300001.SZ', pre_date, 5)
        self.assertEqual(22.42, ma10)

    def test_get_normal_circ_mv(self):
        tushare_interface = TushareInterface()
        pre_date = tushare_interface.find_pre_nearest_trading_day(tushare_interface.get_today_date()).strftime('%Y%m%d')
        print(pre_date)
        normal_circ_mv = tushare_interface.get_normal_circ_mv('300001.SZ', pre_date)
        print(normal_circ_mv)

    def test_get_circ_mv(self):
        tushare_interface = TushareInterface()
        pre_date = tushare_interface.find_pre_nearest_trading_day(tushare_interface.get_today_date()).strftime('%Y%m%d')
        print(pre_date)
        circ_mv = tushare_interface.get_circ_mv('300001.SZ', pre_date)
        print(circ_mv)
