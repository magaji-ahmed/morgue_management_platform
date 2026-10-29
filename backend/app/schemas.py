from typing import Optional
from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class PasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class UserIn(BaseModel):
    username: str = Field(min_length=3)
    full_name: str
    password: str = Field(min_length=8)
    role: str = "staff"


class UserPatch(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)


class BodyIn(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    date_of_death: Optional[str] = None
    cause_of_death: Optional[str] = None
    notes: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_relation: Optional[str] = None


class ServiceIn(BaseModel):
    name: str
    price: float = Field(ge=0)
    active: bool = True


class ApplyService(BaseModel):
    service_id: int


class PaymentIn(BaseModel):
    amount: float = Field(gt=0)
    note: Optional[str] = None


class BodyCreate(BodyIn):
    service_ids: list[int] = []  # services chosen at registration


class DoneIn(BaseModel):
    done: bool


def user_out(u):
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "role": u.role,
        "status": u.status,
        "must_change_password": u.must_change_password,
        "created_at": u.created_at,
    }
