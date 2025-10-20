from __future__ import annotations
from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, List
from datetime import datetime

class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str
    name: str
    labor_hours: float
    base_parts_cost: float

class Pricing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    labor_rate_per_hour: float
    shop_fee_flat: float
    tax_rate: float

class Slot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start_ts: datetime
    end_ts: datetime
    available: bool = True

class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str
    phone: str
    vehicle_year: int
    vehicle_make: str
    vehicle_model: str
    services: list = Field(default_factory=list, sa_column=Column(JSON))
    slot_id: int
    price_low: float
    price_high: float
    status: str = "CONFIRMED"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SessionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: str
    state: str
    turns: int = 0
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    success: bool = False
    completion_reason: Optional[str] = None  # "booked", "abandoned", "escalated", "error"