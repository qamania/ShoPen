from datetime import datetime, timedelta, timezone
from tortoise.contrib import test
from tortoise.contrib.test import initializer, finalizer
from shopen.models.models import Pen, User, Transaction, Session


class TestModel(test.TestCase):
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

    async def test_create_user(self):
        user = await User.create(name="Test User", password="password")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.password, "password")

    async def test_create_transaction(self):
        user = await User.create(name="Test User", password="password")
        transaction = await Transaction.create(user=user, price=1.99, order=[1, 2, 3])
        self.assertEqual(transaction.user, user)
        self.assertEqual(transaction.price, 1.99)
        self.assertEqual(transaction.order, [1, 2, 3])

    async def test_create_session(self):
        user = await User.create(name="Test User", password="password")
        exp = datetime.now(timezone.utc) + timedelta(days=1)
        session = await Session.create(user=user, token="token", expiry=exp)
        self.assertEqual(session.user, user)
        self.assertEqual(session.token, "token")
        self.assertEqual(session.expiry, exp)

