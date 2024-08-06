from tortoise.contrib import test
from pytest import fixture, mark
from tortoise.contrib.test import initializer, finalizer
from shopen.models.models import Pen, User, Transaction


class TestMock(test.TestCase):
    def setUp(self):
        initializer(['shopen.models.models'], db_url='sqlite://:memory:')

    def tearDown(self):
        finalizer()

    async def asyncSetUp(self):
        await super().asyncSetUp()

    async def test_create_pen(self):
        pen = await Pen.create(brand="Test Pen", color="Blue", price=1.99, stock=100)
        self.assertEqual(pen.brand, "Test Pen")
        self.assertEqual(pen.color, "Blue")
        self.assertEqual(pen.price, 1.99)
        self.assertEqual(pen.stock, 100)

