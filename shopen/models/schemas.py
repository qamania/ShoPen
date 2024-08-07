from typing import Optional
from pydantic import (BaseModel, field_validator as validator,
                      ValidationError, conint, Field)


class UserCredentials(BaseModel):
    username: str
    password: str


class UserCredit(BaseModel):
    credit: float

    @validator('credit')
    def validate_credit(cls, value):
        if value < 0 or value > 10_000:
            raise ValidationError("Credit must be between 0 and 10 000")
        return value


class NewPen(BaseModel):
    brand: str
    price: float
    stock: int
    color: Optional[str] = None
    length: Optional[int] = None

    @validator('price')
    def validate_price(cls, value):
        if value < 0:
            raise ValidationError("Price must be non-negative")
        return value

    @validator('stock')
    def validate_stock(cls, value):
        if value < 0:
            raise ValidationError("Stock must be non-negative")
        return value

    @validator('length')
    def validate_length(cls, value):
        if value is not None and value < 0:
            raise ValidationError("Length must be non-negative")
        return value


class PenRequest(BaseModel):
    id: int
    count: conint(ge=1)


class TransactionRequest(BaseModel):
    order: list[PenRequest]


class TransactionStatus(BaseModel):
    status: str

    @validator('status')
    def validate_status(cls, value):
        if value not in ['complete', 'cancel', 'refund']:
            raise ValidationError("It is allowed to request only 'complete', 'cancel' or 'refund'")
        return value
