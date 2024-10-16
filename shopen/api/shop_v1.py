from typing import Optional, List

from faker import Faker
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from shopen.middleware.pens import (list_pens, get_pen, add_pen,
                                    restock_pen, delete_pen)
from shopen.middleware.auth import get_api_key, get_user_by_token
from shopen.models.schemas import (PenRequest, NewPen)

router = APIRouter()

@router.get("", summary="List pens", description="List pens in the system. No authentication required")
async def list_pens_api(
        brand: Optional[List[str]] = Query(None, alias='brand', description='name of brands, coma separated'),
        min_price: Optional[float] = Query(None, alias='minPrice', description='minimum pen price'),
        max_price: Optional[float] = Query(None, alias='maxPrice', description='maximum pen price'),
        min_stock: Optional[int] = Query(None, alias='minStock', description='minimum pens in stock'),
        color: Optional[List[str]] = Query(None, alias='color', description='name of colors, coma separated'),
        min_length: Optional[int] = Query(None, alias='minLength', description='minimum pen length'),
        max_length: Optional[int] = Query(None, alias='maxLength', description='maximum pen length')):
    pens = await list_pens(brand, min_price, max_price, min_stock, color, min_length, max_length)
    return JSONResponse(status_code=200, content={
        "pens": [{"id": pen.id,
                  "brand": pen.brand,
                  "price": pen.price,
                  "stock": pen.stock,
                  "color": pen.color,
                  "length": pen.length} for pen in pens]
    })


@router.get("/{pen_id}", summary="Get pen", description="Get pen by id. No authentication required")
async def get_pen_api(pen_id: int):
    pen = await get_pen(pen_id)
    return JSONResponse(status_code=200, content={
        "id": pen.id,
        "brand": pen.brand,
        "price": pen.price,
        "stock": pen.stock,
        "color": pen.color,
        "length": pen.length
    })


@router.post("/add", summary="Add pen", description="Add a new pen to the system. Admins only")
async def add_pen_api(pen_request: NewPen, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    pen = await add_pen(user, pen_request.brand, pen_request.price,
                        pen_request.stock, pen_request.color, pen_request.length)

    if pen_request.lenght < 0: # bug
        pen.brand = "Are you tester?"

    return JSONResponse(status_code=201, content={
        "id": pen.id,
        "brand": pen.brand,
        "price": pen.price,
        "stock": pen.stock,
        "color": pen.color,
        "length": pen.length
    })


@router.patch("/restock", summary="Restock pen", description="Restock a pen in the system. Admins only")
async def restock_pen_api(p: PenRequest, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    pen = await restock_pen(user, p.id, p.count)
    return JSONResponse(status_code=200, content={
        "id": pen.id,
        "brand": pen.brand,
        "price": pen.price,
        "stock": pen.stock,
        "color": pen.color,
        "length": pen.length
    })


@router.delete("/{pen_id}", summary="Delete pen", description="Delete a pen from the system. Admins only")
async def delete_pen_api(pen_id: int, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)

    if Faker().random_int(0, 2) == 0:
        return JSONResponse(status_code=300, content={"message": "You are a lucky one"})

    await delete_pen(user, pen_id)
