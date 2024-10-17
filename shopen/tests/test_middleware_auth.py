from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from tortoise.contrib import test
from tortoise.contrib.test import initializer, finalizer
from shopen.models.setup import set_default_users
from shopen.middleware.auth import User, Session, create_user, \
    authenticate, list_users, promote_user, get_user, \
    set_user_credits, get_user_by_token, edit_user


class TestMiddlewareAuth(test.TestCase):
    def setUp(self):
        initializer(['shopen.models.models'], db_url='sqlite://:memory:')

    def tearDown(self):
        finalizer()

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.admin = await set_default_users()
        self.user = await User.create(name='test', password='test')
        self.admin_token = 'admin_token'
        self.user_token = 'user_token'
        await Session.create(user=self.admin,
                             token=self.admin_token,
                             expiry=datetime.now(timezone.utc) + timedelta(days=1))
        await Session.create(user=self.user,
                             token=self.user_token,
                             expiry=datetime.now(timezone.utc) + timedelta(days=1))

    async def test_register(self):
        try:
            token = await create_user('test2', 'test2')
            self.assertIsNotNone(token)
            self.assertTrue(await User.exists(name='test2'))
        finally:
            await User.filter(name='test2').delete()

    async def test_register_existing(self):
        with self.assertRaises(HTTPException):
            await create_user('test', 'test')

    async def test_authenticate(self):
        old_token = self.user_token
        self.user_token = await authenticate('test', 'test')
        self.assertIsNotNone(self.user_token)
        self.assertNotEqual(old_token, self.user_token)
        self.assertTrue(await Session.exists(token=self.user_token))

    async def test_authenticate_invalid(self):
        with self.assertRaises(HTTPException):
            await authenticate('test', 'wrong')

    async def test_authenticate_nonexistent(self):
        with self.assertRaises(HTTPException):
            await authenticate('nonexistent', 'wrong')

    async def test_list_users_admin(self):
        users = await list_users(self.admin_token)
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].name, 'admin')
        self.assertEqual(users[1].name, 'test')

    async def test_list_users_user(self):
        with self.assertRaises(HTTPException):
            await list_users(self.user_token)

    async def test_promote_user(self):
        try:
            await promote_user(self.admin, self.user)
            self.assertEqual(self.user.role, 'admin')
        finally:
            self.user.role = 'customer'
            await self.user.save()

    async def test_promote_user_nonadmin(self):
        with self.assertRaises(HTTPException):
            await promote_user(self.user, self.user)

    async def test_get_user_id(self):
        user = await get_user(id=self.user.id)
        self.assertEqual(user.name, 'test')

    async def test_get_user_name(self):
        user = await get_user(name='test')
        self.assertEqual(user.id, self.user.id)

    async def test_get_user_nonexistent(self):
        with self.assertRaises(HTTPException):
            await get_user(id=1000)

    async def test_get_user_set_credit(self):
        await set_user_credits(self.admin, self.user, 100)
        user = await get_user(id=self.user.id)
        self.assertEqual(user.credit, 100)

    async def test_get_user_set_credit_nonadmin(self):
        with self.assertRaises(HTTPException):
            await set_user_credits(self.user, self.user, 100)

    async def test_get_uer_by_token(self):
        user = await get_user_by_token(self.user_token)
        self.assertEqual(user.id, self.user.id)

    async def test_get_user_by_token_expired(self):
        try:
            await Session.filter(token=self.user_token).update(expiry=datetime.now(timezone.utc) - timedelta(days=1))
            with self.assertRaises(HTTPException):
                await get_user_by_token(self.user_token)
        finally:
            await Session.filter(token=self.user_token).update(expiry=datetime.now(timezone.utc) + timedelta(days=1))

    async def test_get_user_by_token_nonexistent(self):
        with self.assertRaises(HTTPException):
            await get_user_by_token('nonexistent_token')

    async def test_edit_user(self):
        try:
            await edit_user(self.user, self.user.id, 'edited_name', 'test')
            user = await get_user(id=self.user.id)
            self.assertEqual(user.name, 'edited_name')
        finally:
            self.user.name = 'test'
            await self.user.save()

    async def test_edit_user_nonadmin(self):
        with self.assertRaises(HTTPException):
            await edit_user(self.user, self.admin.id, 'edited_name', 'test')
