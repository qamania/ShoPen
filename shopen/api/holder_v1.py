from typing import Optional, List
import random
import asyncio
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from shopen.middleware.auth import get_api_key, get_user_by_token

router = APIRouter()


@router.get("", summary="List pen holders",
            description="List holders for pens in the system. No authentication required")
async def list_holders_api():
    data = {'list': [
        {
            'penId': 1,
            'name': 'holderMax',
            'capacity': 10
        },
        {
            'penId': 1,
            'name': 'Thule',
            'capacity': 25
        },
        {
            'penId': 3,
            'name': 'HELLo',
            'capacity': 666
        },
    ]}
    return JSONResponse(status_code=200, content=data)
