from unittest import TestCase

from src.tushare_interface import TushareInterface


class TestTushareInterface(TestCase):
    def test_is_limit_up_past_days(self):
        tushare = TushareInterface()
        res = tushare.is_limit_up_past_days('300001.SZ', '20250920', 3)
        self.assertEqual(res, False)
        res = tushare.is_limit_up_past_days('002059.SZ', '20250920', 3)
        self.assertEqual(res, True)

    def test_get_recent_trade_dates(self):
        tushare = TushareInterface()
        res = tushare.get_recent_trade_dates('20250921', 10)
        print(res)
        self.assertEqual(len(res), 10)
