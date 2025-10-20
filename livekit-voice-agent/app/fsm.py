from enum import Enum

class State(str, Enum):
    COLLECT="COLLECT"
    PLAN="PLAN_SERVICES"
    ESTIMATE="ESTIMATE"
    OFFER_SLOTS="OFFER_SLOTS"
    CONFIRM="CONFIRM"
    BOOKED="BOOKED"
    NOTIFY="NOTIFY"
    CLARIFY="CLARIFY"
    ESCALATE="ESCALATE"

ALLOWED_TOOLS = {
    State.COLLECT: ["plan_services"],
    State.PLAN: ["estimate"],
    State.ESTIMATE: ["find_slots"],
    State.OFFER_SLOTS: ["book"],
    State.CONFIRM: ["book"],
    State.BOOKED: ["notify"],
}

def next_after(tool: str, cur: State) -> State:
    if cur == State.COLLECT and tool == "plan_services": return State.PLAN
    if cur == State.PLAN and tool == "estimate": return State.ESTIMATE
    if cur == State.ESTIMATE and tool == "find_slots": return State.OFFER_SLOTS
    if cur in (State.OFFER_SLOTS, State.CONFIRM) and tool == "book": return State.BOOKED
    if cur == State.BOOKED and tool == "notify": return State.NOTIFY
    return cur
