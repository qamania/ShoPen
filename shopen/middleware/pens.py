from datetime import datetime
from fastapi import HTTPException
from tortoise.transactions import in_transaction
from shopen.models.models import User, Session, Pen, Transaction
from shopen.models.schemas import (PenRequest, TransactionRequest,
                                   TransactionStatus, NewPen)
from shopen.settings import (ADMIN_DISCOUNT, WHOLESALE_DISCOUNT,
                             WHOLESALE_THRESHOLD,
                             TRANSACTION_REQUEST_THRESHOLD,
                             TRANSACTION_REFUND_THRESHOLD)


async def list_pens(
        brand: list[str] = None,
        min_price: float = None,
        max_price: float = None,
        min_stock: float = None,
        color: list[str] = None,
        min_length: float = None,
        max_length: float = None) -> list[Pen]:
    return await Pen.filter(
        brand__in=brand,
        price__gte=min_price,
        price__lte=max_price,
        stock__gt=min_stock,
        color__in=color,
        length__gte=min_length,
        length__lte=max_length,
        is_deleted=False)


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
    if user.role == 'admin' or transaction.user.id == user.id:
        return transaction
    else:
        raise HTTPException(
            status_code=403,
            detail="Only admins can view other users' transactions")


async def list_transactions(user: User, show_own=True, status: str = None) -> list[Transaction]:
    if show_own:
        return await Transaction.filter(user=user, status=status)
    elif user.role == 'admin':
        return await Transaction.filter(status=status)


async def request_pens(user: User, invoice: TransactionRequest) -> Transaction:
    total_price = 0
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
    if (datetime.now() - transaction.timestamp).seconds > TRANSACTION_REQUEST_THRESHOLD * 60:
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
    if user.id != transaction.user.id:
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
    if user.id != transaction.user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only refund your own transactions")
    if transaction.status != 'completed':
        raise HTTPException(
            status_code=400,
            detail="Transaction is not completed")
    if (datetime.now() - transaction.timestamp).seconds > TRANSACTION_REQUEST_THRESHOLD * 60:
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
