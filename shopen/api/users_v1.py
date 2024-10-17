from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from shopen.middleware.auth import (authenticate, create_user,
                                    promote_user, get_api_key, get_user_by_token,
                                    get_user, delete_session, list_users, edit_user, set_user_credits)
from shopen.models.schemas import UserCredentials

router = APIRouter()

@router.get("/list", summary="List all users", description="List all users in the system")
async def user_list(api_key: str = Depends(get_api_key)):
    users = await list_users(api_key)
    return JSONResponse(status_code=200, content={
        "users": [{"id": user.id, "username": user.name, "role": user.role, "credit": user.credit} for user in users]
    })


@router.post("/login", summary="Login",
             description="Login to the system. Returns a token to be used in Authentication header")
async def user_login(credentials: UserCredentials):
    token = await authenticate(credentials.username, credentials.password)
    return JSONResponse(status_code=200, content={"token": token})


@router.get("/logout", summary="Logout", description="Logout from the system")
async def user_logout(api_key: str = Depends(get_api_key)):
    await delete_session(api_key)
    return JSONResponse(status_code=200, content={"message": "Logged out"})


@router.post("/register", summary="Register",
             description="Register to the system. Returns a token to be used in Authentication header")
async def user_register(credentials: UserCredentials):
    token = await create_user(credentials.username, credentials.password)
    return JSONResponse(status_code=201, content={"token": token})


@router.get("/me", summary="Get user info", description="Get info of the authenticated user by token")
async def user_me(api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    return JSONResponse(status_code=200, content={
        "id": user.id,
        "username": user.name,
        "role": user.role,
        "credit": user.credit
    })


@router.get("/user/{user_id}", summary="Get user info",
            description="Get info of a user by id. Admins can view all users info")
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


@router.put("/user/{user_id}/promote", summary="Promote user to admin",
            description="Promote 'customer' to 'admin'")
async def user_promote(user_id: int, api_key: str = Depends(get_api_key)):
    promoter = await get_user_by_token(api_key)
    promotee = await get_user(id=user_id)
    await promote_user(promoter, promotee)
    return JSONResponse(status_code=200, content={"message": "User promoted"})


@router.patch("/user/{user_id}/credit", summary="Set user credit",
              description="Set user credit by admin to make purchases")
async def set_user_credit(user_id: int, credit: float, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    if user.role != 'admin':
        return JSONResponse(status_code=403, content={"error": "Only admins can set user credit"})

    await set_user_credits(user_id, credit)
    return JSONResponse(status_code=200, content={"message": "User credit set"})


@router.put("/user/{user_id}/edit", summary="Edit user",
            description="Can change username and password. Admins can edit any user")
async def user_edit(user_id: int, credentials: UserCredentials, api_key: str = Depends(get_api_key)):
    supervisor = await get_user_by_token(api_key)
    await edit_user(supervisor, user_id, credentials.username, credentials.password)
    return JSONResponse(status_code=200, content={"message": "User edited"})
