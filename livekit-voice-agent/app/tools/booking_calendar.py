from sqlmodel import select
from ..dispatcher import BookIn, BookOut
from ..db.session import get_session
from ..db.models import Booking
from ..lib.calendar import create_event

async def book(inp: BookIn) -> dict:
    print(f"📝 Book function called with input: {inp}")
    print(f"📝 Slot: {inp.slot}")
    print(f"📝 Customer: {inp.customer}")
    print(f"📝 Vehicle: {inp.vehicle}")
    print(f"📝 Services: {inp.services}")
    print(f"📝 Estimate: {inp.estimate}")
    
    title = f"[BOOKING] {inp.customer.name} – {', '.join(inp.services)}"
    print(f"📝 Creating event with title: {title}")
    print(f"📝 Start time: {inp.slot.start}")
    print(f"📝 End time: {inp.slot.end}")
    
    ev_id = create_event(title, inp.slot.start, inp.slot.end,
                         description=f"{inp.vehicle.year} {inp.vehicle.make} {inp.vehicle.model}")
    print(f"📝 Event created with ID: {ev_id}")
    
    with get_session() as s:
        b = Booking(
            customer_name=inp.customer.name,
            phone=inp.customer.phone,
            vehicle_year=inp.vehicle.year,
            vehicle_make=inp.vehicle.make,
            vehicle_model=inp.vehicle.model,
            services=inp.services,
            slot_id=0,  # simplistic demo
            price_low=inp.estimate.price_low,
            price_high=inp.estimate.price_high,
            status="CONFIRMED",
        )
        s.add(b); s.commit()
        print(f"📝 Booking saved to database with ID: {b.id}")
        return BookOut(booking_id=ev_id).model_dump()
