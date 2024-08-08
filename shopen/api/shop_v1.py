from typing import Optional, List
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from shopen.middleware.pens import (list_pens, get_pen, add_pen,
                                    restock_pen, delete_pen)
from shopen.middleware.auth import get_api_key, get_user_by_token
from shopen.models.schemas import (PenRequest, NewPen)

router = APIRouter()
prefix = "/api/v1/pens"


@router.get(prefix + "")
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


@router.get(prefix + "/{pen_id}")
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


@router.post(prefix + "/add")
async def add_pen_api(pen_request: NewPen, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    pen = await add_pen(user, pen_request.brand, pen_request.price,
                        pen_request.stock, pen_request.color, pen_request.length)
    return JSONResponse(status_code=201, content={
        "id": pen.id,
        "brand": pen.brand,
        "price": pen.price,
        "stock": pen.stock,
        "color": pen.color,
        "length": pen.length
    })


@router.patch(prefix + "/restock")
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


@router.delete(prefix + "/{pen_id}")
async def delete_pen_api(pen_id: int, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    await delete_pen(user, pen_id)
