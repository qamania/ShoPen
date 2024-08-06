from fastapi import Request, APIRouter, Response
from fastapi.responses import JSONResponse

router = APIRouter()
prefix = "/api/v1"


@router.get(f"{prefix}/pens")
async def list_pens():
    pass
