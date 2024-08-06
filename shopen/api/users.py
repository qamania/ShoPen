from fastapi import Request, APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from shopen.middleware.auth import (authenticate, create_user,
                                    promote_user, get_api_key, get_user_by_token,
                                    get_user, delete_session, list_users, edit_user)
from shopen.models.schemas import UserCredentials

router = APIRouter()
prefix = "/api/v1/users"


@router.post(prefix + "/login")
async def user_login(credentials: UserCredentials):
    token = await authenticate(credentials.username, credentials.password)
    return JSONResponse(status_code=200, content={"token": token})


@router.get(prefix + "/logout")
async def user_logout(api_key: str = Depends(get_api_key)):
    await delete_session(api_key)
    return JSONResponse(status_code=200, content={"message": "Logged out"})


@router.post(prefix + "/register")
async def user_register(credentials: UserCredentials):
    token = await create_user(credentials.username, credentials.password)
    return JSONResponse(status_code=201, content={"token": token})


@router.get(prefix + "")
async def user_list(api_key: str = Depends(get_api_key)):
    users = await list_users(api_key)
    return JSONResponse(status_code=200, content={
        "users": [{"id": user.id, "username": user.name, "role": user.role, "credit": user.credit} for user in users]
    })


@router.get(prefix + "/{user_id}")
async def user_get(user_id: int, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    if user.role == 'admin' or user.id == user_id:
        user = await get_user(id=user_id)
        return JSONResponse(status_code=200, content={
            "id": user.id,
            "username": user.name,
            "role": user.role,
            "credit": user.credit
        })
    else:
        return JSONResponse(status_code=403, content={"error": "Only admins can view other users"})


@router.put(prefix + "/{user_id}/promote")
async def user_promote(user_id: int, api_key: str = Depends(get_api_key)):
    promoter = await get_user_by_token(api_key)
    promotee = await get_user(id=user_id)
    await promote_user(promoter, promotee)
    return JSONResponse(status_code=200, content={"message": "User promoted"})


@router.patch(prefix + "/{user_id}/credit")
async def set_user_credit(user_id: int, credit: float, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    if user.role != 'admin':
        return JSONResponse(status_code=403, content={"error": "Only admins can set user credit"})

    user = await get_user(id=user_id)
    user.credit = credit
    await user.save()
    return JSONResponse(status_code=200, content={"message": "User credit set"})


@router.put(prefix + "/{user_id}/edit")
async def user_edit(user_id: int, credentials: UserCredentials, api_key: str = Depends(get_api_key)):
    supervisor = await get_user_by_token(api_key)
    await edit_user(supervisor, user_id, credentials.username, credentials.password)
    return JSONResponse(status_code=200, content={"message": "User edited"})
