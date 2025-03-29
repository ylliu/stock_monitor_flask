from unittest import TestCase

from src.data_interface_base import DataInterfaceBase


class TestDataInterfaceBase(TestCase):
    def test_find_last_date_in_csv(self):
        interface = DataInterfaceBase()
        file_path = "002698.SZ_daily_data.csv"
        res = interface.find_last_date_in_csv(file_path)
        print(res)
