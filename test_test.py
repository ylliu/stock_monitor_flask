from unittest import TestCase

from test import verity_code, app


class Test(TestCase):
    def test_verity_code(self):
        with app.app_context():
            verity_code('2025-01-08', 'main', '601226.SH')
