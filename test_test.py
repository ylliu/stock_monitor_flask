from unittest import TestCase

from test import verity_code, app


class Test(TestCase):
    def test_verity_code(self):
        with app.app_context():
            verity_code('2024-11-15', 'chiNext', '300997.SZ')
