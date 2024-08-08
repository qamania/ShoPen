import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from shopen.models.models import User, Session

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def clean_sessions(user: User = None) -> None:
    if user is not None:
        await Session.filter(user=user).delete()
    await Session.filter(expiry__lte=datetime.now(timezone.utc)).delete()


async def get_user(id: int = None, name: str = None) -> User:
    if id is not None:
        user = await User.get_or_none(id=id)
    elif name is not None:
        user = await User.get_or_none(name=name)
    if user is not None:
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
    return await User.all()


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
            detail="User already exists",
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


async def set_user_credit(supervisor: User, user: User, credit: float) -> None:
    if supervisor.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admins can set user credit balance")
    if credit < 0:
        raise HTTPException(
            status_code=400,
            detail="Credit must be non-negative",
        )
    user.credit = credit
    await user.save()


async def get_user_by_token(token: str) -> User:
    await clean_sessions()
    session = await Session.get_or_none(token=token, expiry__gte=datetime.now(timezone.utc))
    if session is None:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
    return await session.user


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
