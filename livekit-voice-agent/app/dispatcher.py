import json
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal, Any

# ---- IO SCHEMAS ----
class Vehicle(BaseModel):
    year: int = Field(ge=1990, le=2100)
    make: str
    model: str
    mileage: Optional[int] = None

class PlanIn(BaseModel):
    vehicle: Vehicle
    issues: List[str]

class PlanOut(BaseModel):
    services: List[str]

class EstimateIn(BaseModel):
    vehicle: Vehicle
    services: List[str]

class EstimateOut(BaseModel):
    price_low: float
    price_high: float
    duration_minutes: int

class FindSlotsIn(BaseModel):
    duration_minutes: int
    date_pref: Optional[str] = None

class SlotItem(BaseModel):
    start: str
    end: str

class FindSlotsOut(BaseModel):
    slots: List[SlotItem]

class Customer(BaseModel):
    name: str
    phone: str

class BookIn(BaseModel):
    slot: SlotItem
    customer: Customer
    vehicle: Vehicle
    services: List[str]
    estimate: EstimateOut

class BookOut(BaseModel):
    booking_id: str

class NotifyIn(BaseModel):
    booking_id: str
    channel: Literal["sms","none"] = "sms"

class NotifyOut(BaseModel):
    success: bool
    message_id: str
    channel: str

# ---- DISPATCHER ----
TOOL_SCHEMAS = {
    "plan_services": PlanIn,
    "estimate": EstimateIn,
    "find_slots": FindSlotsIn,
    "book": BookIn,
    "notify": NotifyIn,
}

async def dispatch(tool_name: str, args: dict, impls: dict[str, Any]) -> dict:
    if tool_name not in TOOL_SCHEMAS:
        return {"error": "UNKNOWN_TOOL"}
    try:
        payload = TOOL_SCHEMAS[tool_name](**args)
    except ValidationError as e:
        return {"error": "INVALID_ARGS", "details": json.loads(e.json())}
    try:
        fn = impls[tool_name]
        result = await fn(payload) if callable(fn) else None
        return {"ok": True, "result": result}
    except Exception as ex:
        return {"error": "TOOL_ERROR", "message": str(ex)}