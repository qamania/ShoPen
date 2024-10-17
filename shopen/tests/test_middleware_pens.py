from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from tortoise.contrib import test
from tortoise.contrib.test import initializer, finalizer
from shopen.models.setup import set_default_users
from shopen.models.models import Pen, User, Transaction
from shopen.models.schemas import PenRequest, TransactionRequest
from shopen.middleware.pens import list_pens, get_pen, add_pen, restock_pen, delete_pen, get_transaction, \
    list_transactions, request_pens, cancel_transaction, refund_transaction

order = [{'penId': 1, 'number': 3}]


class TestMiddlewareAuth(test.TestCase):
    def setUp(self):
        initializer(['shopen.models.models'], db_url='sqlite://:memory:')

    def tearDown(self):
        finalizer()

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.admin = await set_default_users()

        random = await User.create(name='ololo', password='test', credit=12000)
        await Transaction.create(user=random, price=10, order=order)

        self.user = await User.create(name='test', password='test', credit=1000)
        self.admin_token = 'admin_token'
        self.user_token = 'user_token'
        self.pen = await Pen.create(brand='space', price=10, stock=1000, color='blue', length=5)

    async def test_list_pens(self):
        pens = await list_pens()
        self.assertEqual(len(pens), 1)
        self.assertEqual(pens[0].brand, 'space')

    async def test_filter_pens_brand(self):
        pens = await list_pens(brand=['space'])
        self.assertEqual(len(pens), 1)
        self.assertEqual(pens[0].brand, 'space')

    async def test_filter_pens_price(self):
        pens = await list_pens(min_price=5, max_price=15)
        self.assertEqual(len(pens), 1)
        self.assertEqual(pens[0].brand, 'space')

    async def test_filter_pens_stock(self):
        pens = await list_pens(min_stock=500)
        self.assertEqual(len(pens), 1)
        self.assertEqual(pens[0].brand, 'space')

    async def test_filter_pens_color(self):
        pens = await list_pens(color=['blue'])
        self.assertEqual(len(pens), 1)
        self.assertEqual(pens[0].brand, 'space')

    async def test_get_pen(self):
        pen = await get_pen(1)
        self.assertEqual(pen.brand, 'space')

    async def test_get_pen_not_found(self):
        with self.assertRaises(HTTPException):
            await get_pen(2)

    async def test_add_pen(self):
        pen = await add_pen(self.admin, 'start', 500, 10, 'black', 25)
        self.assertEqual(pen.brand, 'start')
        self.assertEqual(pen.price, 500)
        self.assertEqual(pen.stock, 10)

    async def test_add_pen_not_admin(self):
        with self.assertRaises(HTTPException):
            await add_pen(self.user, 'start', 500, 10, 'black', 25)

    async def test_restock_pen(self):
        pen = await restock_pen(self.admin, 1, 500)
        self.assertEqual(pen.stock, 1500)

    async def test_restock_pen_not_admin(self):
        with self.assertRaises(HTTPException):
            await restock_pen(self.user, 1, 500)

    async def test_delete_pen(self):
        new_pen = await Pen.create(brand='del', price=1, stock=1, color='red', length=8.5)
        try:
            await delete_pen(self.admin, new_pen.id)
            pen = await get_pen(new_pen.id)
            self.assertTrue(pen.is_deleted)
            self.assertEqual(pen.stock, 0)
        finally:
            new_pen.is_deleted = True
            new_pen.stock = 0
            await new_pen.save()

    async def test_get_transaction(self):
        transaction = await Transaction.create(user=self.user, price=10, order=order)
        result = await get_transaction(self.user, transaction.id)
        self.assertEqual(result.id, transaction.id)

    async def test_get_transaction_not_found(self):
        with self.assertRaises(HTTPException):
            await get_transaction(self.user, 2000)

    async def test_get_transaction_not_owner(self):
        transaction = await Transaction.create(user=self.admin, price=10, order=order)
        with self.assertRaises(HTTPException):
            await get_transaction(self.user, transaction.id)

    async def test_list_transactions(self):
        user = await User.create(name='test2', password='test2')
        await Transaction.create(user=user, price=1.2, order=order)
        transactions = await list_transactions(user, show_own=True)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].price, 1.2)

    async def test_list_transactions_user_not_own(self):
        user = await User.create(name='test3', password='test3')
        await Transaction.create(user=user, price=1.3, order=order)
        await Transaction.create(user=self.user, price=1.4, order=order)
        transactions = await list_transactions(user, show_own=False)
        self.assertEqual(len(transactions), 1)

    async def test_list_transactions_admin(self):
        user = await User.create(name='test4', password='test4', role='admin')
        await Transaction.create(user=user, price=1.5, order=order)
        await Transaction.create(user=self.user, price=1.6, order=order)
        transactions = await list_transactions(user, show_own=False)
        self.assertGreaterEqual(len(transactions), 2)

    async def test_list_transactions_status(self):
        user = await User.create(name='test5', password='test5')
        await Transaction.create(user=user, price=1.7, order=order, status='completed')
        await Transaction.create(user=user, price=1.8, order=order, status='requested')
        transactions = await list_transactions(user, show_own=True, status='completed')
        self.assertEqual(len(transactions), 1)

    async def test_request_pen(self):
        invoice = TransactionRequest(order=[
            PenRequest(id=self.pen.id, count=3)])
        transaction = await request_pens(self.user, invoice)
        self.assertEqual(transaction.price, 30)

    async def test_request_pen_not_enough_credit(self):
        invoice = TransactionRequest(order=[
            PenRequest(id=self.pen.id, count=110)])
        with self.assertRaises(HTTPException):
            await request_pens(self.user, invoice)

    async def test_request_pen_not_enough_stock(self):
        invoice = TransactionRequest(order=[
            PenRequest(id=self.pen.id, count=1100)])
        with self.assertRaises(HTTPException):
            await request_pens(self.user, invoice)

    async def test_request_pen_admin_discount(self):
        invoice = TransactionRequest(order=[
            PenRequest(id=self.pen.id, count=3)])
        self.user.role = 'admin'
        await self.user.save()
        transaction = await request_pens(self.user, invoice)
        self.assertEqual(transaction.price, 24)

    async def test_cancel_transaction(self):
        transaction = await Transaction.create(user=self.user, price=10, order=order)
        await cancel_transaction(self.user, transaction.id)
        transaction = await Transaction.get(id=transaction.id)
        self.assertEqual(transaction.status, 'cancelled')

    async def test_cancel_transaction_not_owner(self):
        transaction = await Transaction.create(user=self.admin, price=10, order=order)
        with self.assertRaises(HTTPException):
            await cancel_transaction(self.user, transaction.id)

    async def test_cancel_transaction_already_completed(self):
        transaction = await Transaction.create(user=self.user, price=10, order=order, status='completed')
        with self.assertRaises(HTTPException):
            await cancel_transaction(self.user, transaction.id)

    async def test_refund_transaction_expired(self):
        transaction = await Transaction.create(user=self.user,
                                               price=10,
                                               order=order,
                                               timestamp=datetime.now(timezone.utc) - timedelta(hours=50),
                                               status='completed')
        with self.assertRaises(HTTPException):
            await refund_transaction(self.user, transaction.id)

    async def test_refund_transaction_not_owner(self):
        transaction = await Transaction.create(user=self.admin, price=10, order=order)
        with self.assertRaises(HTTPException):
            await refund_transaction(self.user, transaction.id)

    async def test_refund_transaction_canceled(self):
        transaction = await Transaction.create(user=self.admin, price=10, order=order)
        await  cancel_transaction(transaction.user, transaction.id)
        # with self.assertRaises(HTTPException):
        #     await refund_transaction(self.user, transaction.id)
        await refund_transaction(self.user, transaction.id)

        actual = await get_transaction(transaction.user, transaction.id)

        self.assertEqual( 'refunded', actual.status)
