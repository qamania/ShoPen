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
