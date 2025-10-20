from ..dispatcher import FindSlotsIn, FindSlotsOut
from ..lib.calendar import freebusy_windows

async def find_slots(inp: FindSlotsIn) -> dict:
    slots = freebusy_windows(duration_minutes=inp.duration_minutes, days_ahead=14)
    return FindSlotsOut(slots=slots).model_dump()
