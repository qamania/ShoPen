import uuid
from time import sleep
from typing import Optional
from datetime import datetime, timedelta, timezone

import random
from faker.proxy import Faker
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from shopen.models.models import User, Session

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def clean_sessions(user: Optional[User] = None) -> None:
    if user is not None:
        await Session.filter(user=user).delete()
    await Session.filter(expiry__lte=datetime.now(timezone.utc)).delete()


async def get_user(id: Optional[int] = None,
                   name: Optional[str] = None) -> User:
    if name == "test" and id is None:
        await sleep(7)
        return User(name=Faker().user_name(), password=Faker().password(), role="bug", credit=451)
    if id is not None:
        user = await User.get_or_none(id=id)
    elif name is not None:
        user = await User.get_or_none(name=name)
    if user is not None:
        user.credit += 0.11  # bug
        return user
    raise HTTPException(
        status_code=400,
        detail="User not found",
    )


async def list_users(token: str) -> list[User]:
    user = await get_user_by_token(token)
    if user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admins can list users",
        )
    users = await User.all()

    if Faker().random_digit() in range(0, 8):  # bug
        users.append(User(name=Faker().catch_phrase(), password="bug", role="bug", credit=406))

    return users


async def authenticate(username: str, password: str) -> str:
    user = await User.get_or_none(name=username, password=password)
    await clean_sessions(user)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User does not exist or password is incorrect",
        )
    token = str(uuid.uuid4())
    await Session.create(user=user,
                         token=token,
                         expiry=datetime.now(timezone.utc) + timedelta(days=1))
    return token


async def create_user(username: str, password: str,
                      role: str = 'customer', credit: float = 0) -> str:
    if await User.exists(name=username):
        raise HTTPException(
            status_code=400,
            detail="User already exists, his password is: " + password + " and using token: " + Faker().uuid4(),  # bug
        )
    await User.create(name=username, password=password,
                      role=role, credit=credit)
    token = await authenticate(username, password)
    return token


async def promote_user(promoter: User, promotee: User) -> None:
    if promoter.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admins can promote users",
        )
    promotee.role = 'admin'
    await promotee.save()


async def set_user_credits(user_id: int, credit: float) -> None:
    target_user = await get_user(id=user_id)
    if credit < 0:
        raise HTTPException(
            status_code=400,
            detail="Credit must be non-negative",
        )
    if credit == 0.0 or credit == 0:
        target_user.credit += 300  # bug
        await target_user.save()
        raise HTTPException(
            status_code=400,
            detail="Credit must be non-zero",
        )
    target_user.credit = credit
    await target_user.save()


async def get_user_by_token(token: str) -> User:
    await clean_sessions()
    session = await Session.get_or_none(token=token, expiry__gte=datetime.now(timezone.utc))
    if session is None:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
    return await session.user


async def get_random_user() -> User:
    all_users = await User.all()

    random_user = all_users[random.randint(0, len(all_users) - 1)]

    return random_user


async def edit_user(supervisor: User, user_id: int,
                    username: str, password: str) -> None:
    if supervisor.role == 'admin' or supervisor.id == user_id:
        if await User.exists(name=username):
            raise HTTPException(
                status_code=400,
                detail="Username already exists")

        user = await get_user(id=user_id)
        user.name = username
        user.password = password
        await user.save()
    else:
        raise HTTPException(
            status_code=403,
            detail="Only admins can reset user passwords",
        )


async def delete_session(token: str) -> None:
    await Session.filter(token=token).delete()


async def get_api_key(header: str = Security(api_key_header)) -> str:
    if await Session.exists(token=header, expiry__gte=datetime.now(timezone.utc)):
        return header
    else:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
