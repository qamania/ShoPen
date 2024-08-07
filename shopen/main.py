from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from tortoise import Tortoise
from fastapi.staticfiles import StaticFiles
from shopen.settings import STATIC_ROOT, DB_CONFIG, SUPER_ADMIN_TOKEN
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager
from pydantic import ValidationError
from shopen.api.users_v1 import router as user_router
from shopen.api.shop_v1 import router as shop_router
from shopen.api.transaction_v1 import router as transaction_router
from shopen.models.setup import (is_db_empty, setup_reset,
                                 set_default_stock, set_default_users)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if await is_db_empty():
        await set_default_users()
        await set_default_stock()
    yield
    # do something after the application stops
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)
# app.mount('/assets', StaticFiles(directory=STATIC_ROOT), name='assets')
app.include_router(user_router)
app.include_router(shop_router)
app.include_router(transaction_router)

register_tortoise(app=app,
                  config=DB_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=418,
        content={"message": exc.errors()},
    )


@app.get("/")
async def root():
    return {"shopen": "Шо? Pen?",
            "apiUrl": "/docs"}


@app.get("/factoryReset/{key}")
async def factory_reset(key: str):
    await setup_reset()
    await set_default_users()
    await set_default_stock()
    return {"message": "Factory reset done"}
