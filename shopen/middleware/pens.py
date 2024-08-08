from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from tortoise.transactions import in_transaction
from shopen.models.models import User, Pen, Transaction
from shopen.models.schemas import TransactionRequest
from shopen.settings import (ADMIN_DISCOUNT, WHOLESALE_DISCOUNT,
                             WHOLESALE_THRESHOLD,
                             TRANSACTION_REQUEST_THRESHOLD,
                             TRANSACTION_REFUND_THRESHOLD)


async def list_pens(
        brand: Optional[list[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_stock: Optional[float] = None,
        color: Optional[list[str]] = None,
        min_length: Optional[float] = None,
        max_length: Optional[float] = None) -> list[Pen]:
    filters = {"is_deleted": False}

    if brand:
        filters["brand__in"] = brand
    if min_price is not None:
        filters["price__gte"] = min_price
    if max_price is not None:
        filters["price__lte"] = max_price
    if min_stock is not None:
        filters["stock__gt"] = min_stock
    if color:
        filters["color__in"] = color
    if min_length is not None:
        filters["length__gte"] = min_length
    if max_length is not None:
        filters["length__lte"] = max_length
    return await Pen.filter(**filters)


async def get_pen(id: int) -> Pen:
    pen = await Pen.get_or_none(id=id)
    if pen is None:
        raise HTTPException(
            status_code=404,
            detail="Pen not found",
        )
    return pen


async def add_pen(user: User, brand: str, price: float,
                  stock: int, color: str = None, length: int = None) -> Pen:
    if user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admins can add pens")
    return await Pen.create(brand=brand, price=price, stock=stock,
                            color=color, length=length)


async def restock_pen(user: User, pen_id: int, stock: int) -> Pen:
    if user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admins can restock pens")
    pen = await get_pen(pen_id)
    pen.stock += stock
    await pen.save()
    return pen


async def delete_pen(user: User, pen_id: int) -> None:
    if user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admins can delete pens")
    pen = await get_pen(pen_id)
    pen.is_deleted = True
    pen.stock = 0
    await pen.save()


async def get_transaction(user: User, id: int) -> Transaction:
    transaction = await Transaction.get_or_none(id=id)
    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )
    transaction_user = await transaction.user.get()
    if user.role == 'admin' or transaction_user.id == user.id:
        return transaction
    else:
        raise HTTPException(
            status_code=403,
            detail="Only admins can view other users' transactions")


async def list_transactions(user: User, show_own=True, status: Optional[str] = None) -> list[Transaction]:
    filter = {}
    if show_own or user.role != 'admin':
        filter['user'] = user
    if status:
        filter['status'] = status

    return await Transaction.filter(**filter)


async def request_pens(user: User, invoice: TransactionRequest) -> Transaction:
    total_price = 0.0
    for pen_request in invoice.order:
        pen = await get_pen(pen_request.id)
        if pen.stock < pen_request.count:
            raise HTTPException(
                status_code=400,
                detail="Not enough stock")
        total_price += pen.price * pen_request.count

    if user.credit < total_price:
        raise HTTPException(
            status_code=400,
            detail="Not enough credit")

    if user.role == 'admin':
        total_price = total_price * (1 - ADMIN_DISCOUNT)
    elif total_price > WHOLESALE_THRESHOLD:
        total_price = total_price * (1 - WHOLESALE_DISCOUNT)

    order = [{'penId': pen_id, 'number': pen_number} for pen_id, pen_number in invoice.order]
    return await Transaction.create(user=user, price=total_price, order=order)


async def complete_transaction(user: User, transaction_id: int) -> None:
    transaction = await get_transaction(user, transaction_id)
    if user.id != transaction.user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only complete your own transactions")
    if transaction.status != 'requested':
        raise HTTPException(
            status_code=400,
            detail="Transaction is already processed")
    if (datetime.now(timezone.utc) - transaction.timestamp).seconds > TRANSACTION_REQUEST_THRESHOLD * 60:
        transaction.status = 'cancelled'
        await transaction.save()
        raise HTTPException(
            status_code=400,
            detail="Transaction request is expired and will be cancelled")

    async with in_transaction():
        try:
            transaction.status = 'completed'
            await transaction.save()
            for pen_request in transaction.order:
                pen = await Pen.get(id=pen_request['penId'])
                if pen.stock < pen_request['number']:
                    raise HTTPException(
                        status_code=400,
                        detail="Not enough stock. Transaction will be cancelled")
                pen.stock -= pen_request['number']
                await pen.save()
                if user.credit < transaction.price:
                    raise HTTPException(
                        status_code=400,
                        detail="Not enough credit. Transaction will be cancelled")
                user.credit -= transaction.price
                await user.save()
        except HTTPException as e:
            transaction.status = 'cancelled'
            await transaction.save()
            raise e


async def cancel_transaction(user: User, transaction_id: int) -> None:
    transaction = await get_transaction(user, transaction_id)
    tr_user = await transaction.user.get()
    if user.id != tr_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only cancel your own transactions")
    if transaction.status != 'requested':
        raise HTTPException(
            status_code=400,
            detail="Transaction is already processed")
    transaction.status = 'cancelled'
    await transaction.save()


async def refund_transaction(user: User, transaction_id: int) -> None:
    transaction = await get_transaction(user, transaction_id)
    tr_user = await transaction.user.get()
    if user.id != tr_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only refund your own transactions")
    if transaction.status != 'completed':
        raise HTTPException(
            status_code=400,
            detail="Transaction is not completed")
    if (datetime.now(timezone.utc) - transaction.timestamp).seconds > TRANSACTION_REFUND_THRESHOLD * 60:
        raise HTTPException(
            status_code=400,
            detail="Transaction request is expired and cannot be refunded")

    async with in_transaction():
        transaction.status = 'refunded'
        await transaction.save()
        for pen_request in transaction.order:
            pen = await Pen.get(id=pen_request['penId'])
            pen.stock += pen_request['number']
            await pen.save()
        user.credit += transaction.price
        await user.save()
