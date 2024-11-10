from unittest import TestCase

from test import get_monitor_records, get_stock_price, app, concat_code, get_stock_k_line


class Test(TestCase):
    def test_get_monitor_records(self):
        get_monitor_records('2024-11-03')
        self.fail()

    def test_get_stock_price(self):
        with app.app_context():
            price = get_stock_price()
            print(price)

    def test_get_stock_price(self):
        with app.app_context():
            price = get_stock_price()

    def test_concat_code(self):
        with app.app_context():
            list = concat_code(['300001.SZ', '300002.SZ', '300003.SZ'])
            print(list)

    def test_get_stock_k_line(self):
        with app.app_context():
            json = get_stock_k_line('300001.SZ')
            print(json)
