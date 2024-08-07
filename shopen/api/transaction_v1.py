from typing import Optional, List
from fastapi import Request, APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from shopen.middleware.pens import (get_transaction,
                                    list_transactions, request_pens, complete_transaction,
                                    cancel_transaction, refund_transaction)
from shopen.middleware.auth import get_api_key, get_user_by_token
from shopen.models.schemas import TransactionRequest

router = APIRouter()
prefix = "/api/v1/transactions"


@router.get(prefix + "")
async def list_transactions_api(
        show_own: Optional[bool] = Query(None, alias='showOwn', description='show only transactions of the user'),
        status: Optional[str] = Query(None, alias='status',
                                      description='filter by status: requested, completed, cancelled, refunded'),
        api_key: str = Depends(get_api_key)):
    if show_own is None:
        show_own = True
    user = await get_user_by_token(api_key)
    transactions = await list_transactions(user, show_own, status)
    return JSONResponse(status_code=200, content={
        "transactions": [{"id": t.id,
                          "userId": t.user.id,
                          "status": t.status,
                          "price": t.price,
                          "timestamp": t.timestamp,
                          "order": t.order}
                         for t in transactions]
    })


@router.get(prefix + "/{transaction_id}")
async def get_transaction_api(transaction_id: int, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    transaction = await get_transaction(user, transaction_id)
    return JSONResponse(status_code=200, content={
        "id": transaction.id,
        "userId": transaction.user.id,
        "status": transaction.status,
        "price": transaction.price,
        "timestamp": transaction.timestamp,
        "order": transaction.order
    })


@router.post(prefix + "/request")
async def request_pens_api(invoice: TransactionRequest, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    transaction = await request_pens(user, invoice)
    return JSONResponse(status_code=201, content={
        "id": transaction.id,
        "userId": transaction.user.id,
        "status": transaction.status,
        "price": transaction.price,
        "timestamp": transaction.timestamp,
        "order": transaction.order
    })


@router.post(prefix + "/{transaction_id}/complete")
async def complete_transaction_api(transaction_id: int, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    await complete_transaction(user, transaction_id)
    return JSONResponse(status_code=200, content={"message": "Transaction completed"})


@router.post(prefix + "/{transaction_id}/cancel")
async def cancel_transaction_api(transaction_id: int, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    await cancel_transaction(user, transaction_id)
    return JSONResponse(status_code=200, content={"message": "Transaction cancelled"})


@router.post(prefix + "/{transaction_id}/refund")
async def refund_transaction_api(transaction_id: int, api_key: str = Depends(get_api_key)):
    user = await get_user_by_token(api_key)
    await refund_transaction(user, transaction_id)
    return JSONResponse(status_code=200, content={"message": "Transaction refunded"})
