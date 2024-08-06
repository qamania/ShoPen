from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from tortoise import Tortoise
from fastapi.staticfiles import StaticFiles
from shopen.settings import STATIC_ROOT, DB_CONFIG
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager
from pydantic import ValidationError
from shopen.api.users import router as user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # do something before the application starts
    yield
    # do something after the application stops
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)
app.mount('/assets', StaticFiles(directory=STATIC_ROOT), name='assets')
app.include_router(user_router)

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
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
