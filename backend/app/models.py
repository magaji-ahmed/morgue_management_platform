from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # stored as naive UTC


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10), default="staff")  # admin | staff
    status: Mapped[str] = mapped_column(
        String(10), default="active"
    )  # active | suspended | deleted
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    price: Mapped[float] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Body(Base):
    __tablename__ = "bodies"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag_no: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    full_name: Mapped[Optional[str]] = mapped_column(
        String(160)
    )  # empty = unidentified
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    age: Mapped[Optional[int]]
    date_of_death: Mapped[Optional[str]] = mapped_column(String(10))
    cause_of_death: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    contact_name: Mapped[Optional[str]] = mapped_column(String(160))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(40))
    contact_relation: Mapped[Optional[str]] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(
        String(10), default="stored"
    )  # stored | released
    admitted_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    registered_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    services: Mapped[list["BodyService"]] = relationship(order_by="BodyService.id")
    payments: Mapped[list["Payment"]] = relationship(order_by="Payment.id")


class BodyService(Base):
    __tablename__ = "body_services"
    __table_args__ = (
        UniqueConstraint("body_id", "service_id", name="uq_body_service"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    body_id: Mapped[int] = mapped_column(ForeignKey("bodies.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    name: Mapped[str] = mapped_column(String(80))
    price: Mapped[float] = mapped_column(Float)  # snapshot at selection time
    added_by: Mapped[Optional[str]] = mapped_column(String(50))
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=now, server_default=func.now()
    )
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    done_by: Mapped[Optional[str]] = mapped_column(String(50))
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    body_id: Mapped[int] = mapped_column(ForeignKey("bodies.id"))
    amount: Mapped[float] = mapped_column(Float)
    note: Mapped[Optional[str]] = mapped_column(String(160))
    received_by: Mapped[str] = mapped_column(String(50))
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=now)
    user_id: Mapped[Optional[int]]
    username: Mapped[str] = mapped_column(
        String(50)
    )  # copied so the trail survives account deletion
    body_id: Mapped[Optional[int]] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(60))
    detail: Mapped[Optional[str]] = mapped_column(Text)
