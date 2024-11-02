from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from tortoise import Tortoise
from shopen.settings import DB_CONFIG, SUPER_ADMIN_TOKEN, VERSION
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager
from pydantic import ValidationError
from shopen.api.users_v1 import router as user_router
from shopen.api.shop_v1 import router as shop_router
from shopen.api.transaction_v1 import router as transaction_router
from shopen.api.service_v1 import router as service_router
from shopen.api.holder_v1 import router as holder_router
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


app = FastAPI(title="Shopen API",
              description="Web app shop to buy pens, expose API to manage users, shop and transactions",
              version=VERSION,
              openapi_url="/api/v1/openapi.json",
              docs_url="/api/v1/docs",
              lifespan=lifespan)
# app.mount('/assets', StaticFiles(directory=STATIC_ROOT), name='assets')
app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
app.include_router(shop_router, prefix="/api/v1/pens", tags=["shop"])
app.include_router(transaction_router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(service_router, prefix="/api/v1/service", tags=["service"])
app.include_router(holder_router, prefix='/api/v1/holders', tags=['holders'])

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
    with open('index.html', 'r') as file:
        return HTMLResponse(content=file.read(), status_code=200)

@app.get("/factoryReset/{key}")
async def factory_reset(key: str):
    if key != SUPER_ADMIN_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Only super admin can reset the database")
    await setup_reset()
    await set_default_users()
    await set_default_stock()
    return {"message": "Factory reset done"}
