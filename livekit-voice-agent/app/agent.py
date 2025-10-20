import os, json, asyncio
from livekit.agents import Agent, AgentSession, RunContext, function_tool
from livekit.plugins import deepgram, elevenlabs, openai as lk_openai
from .dispatcher import dispatch
from .fsm import State, ALLOWED_TOOLS, next_after
from .db.session import init_db
from .tools import plan_services as t_plan, estimate as t_est, slots_calendar as t_slots, booking_calendar as t_book, notify as t_notify
from .session_manager import SessionManager

# Load prompts
PROMPTS = json.load(open("app/config/prompts.json"))

# Tool implementations registry
IMPLS = {
    "plan_services": t_plan.plan_services,
    "estimate": t_est.estimate,
    "find_slots": t_slots.find_slots,
    "book": t_book.book,
    "notify": t_notify.notify,
}

class ServiceAgent(Agent):
    state: State = State.COLLECT
    turns: int = 0
    session_manager: SessionManager = None
    room_id: str = None
    _last_tool_result: tuple = None
    
    def __init__(self, room_id: str = None, **kwargs):
        super().__init__(**kwargs)
        self.room_id = room_id or "default-room"
        self.session_manager = SessionManager(self.room_id)
    
    async def initialize_session(self):
        """Initialize or load existing session"""
        existing_state = await self.session_manager.load_session_state()
        if existing_state:
            self.state = existing_state
            print(f"🔄 Restored session state: {self.state}")
        else:
            await self.session_manager.create_session(self.state)
            print(f"🆕 Created new session: {self.state}")
    
    async def save_session_state(self):
        """Save current session state to database"""
        await self.session_manager.update_session_state(self.state, self.turns)
    
    async def on_tool_result(self, tool_name: str, result: dict):
        """Handle tool execution results and generate appropriate responses"""
        print(f"🔧 Tool {tool_name} completed with result: {result}")
        
        # Generate appropriate response based on tool and result
        if tool_name == "plan_services" and "services" in result:
            services = result["services"]
            response = f"Based on your vehicle's issue, I recommend {', '.join(services)}. Let me get you an estimate for this service."
            print(f"🤖 Generated response: {response}")
            return response
            
        elif tool_name == "estimate" and "price_low" in result:
            price_low = result["price_low"]
            price_high = result["price_high"]
            duration = result["duration_minutes"]
            response = f"The estimated cost is ${price_low}-${price_high}, and it should take about {duration} minutes. Would you like me to find available appointment times?"
            print(f"🤖 Generated response: {response}")
            return response
            
        elif tool_name == "find_slots" and "slots" in result:
            slots = result["slots"]
            if slots:
                first_slot = slots[0]
                start_time = first_slot["start"]
                # Convert UTC time to readable format
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    readable_time = dt.strftime('%A, %B %d at %I:%M %p')
                    response = f"I found several available appointment times. The earliest is {readable_time}. Would you like to book this appointment?"
                except:
                    response = f"I found several available appointment times. The earliest is {start_time}. Would you like to book this appointment?"
                print(f"🤖 Generated response: {response}")
                return response
            else:
                response = "I'm sorry, but I don't see any available appointment times right now. Let me check with our scheduling system."
                print(f"🤖 Generated response: {response}")
                return response
                
        elif tool_name == "book" and "booking_id" in result:
            booking_id = result["booking_id"]
            response = f"Perfect! Your appointment has been booked successfully. Your booking ID is {booking_id}. I'll send you a confirmation message shortly."
            print(f"🤖 Generated response: {response}")
            return response
            
        elif tool_name == "notify":
            response = "Great! I've sent you a confirmation message with all the details. Is there anything else I can help you with today?"
            print(f"🤖 Generated response: {response}")
            return response
        
        return None

    @function_tool
    async def plan_services(self, context: RunContext, vehicle: dict, issues: list[str]):
        if "plan_services" not in ALLOWED_TOOLS[self.state]:
            return {"error": "TOOL_NOT_ALLOWED"}
        
        print(f"🔧 Executing plan_services with vehicle: {vehicle}, issues: {issues}")
        
        try:
            out = await dispatch("plan_services", {"vehicle": vehicle, "issues": issues}, IMPLS)
            print(f"🔧 plan_services result: {out}")
            
            if "ok" in out:
                self.state = next_after("plan_services", self.state)
                print(f"🔄 State changed to: {self.state}")
                await self.session_manager.log_tool_call("plan_services", success=True)
                await self.session_manager.log_customer_info({"vehicle": vehicle, "issues": issues})
                await self.save_session_state()
            else:
                await self.session_manager.log_tool_call("plan_services", success=False, error=str(out))
            
            result = out.get("result", out)
            print(f"🔧 Returning: {result}")
            self._last_tool_result = ("plan_services", result)
            print(f"🔧 Stored tool result: {self._last_tool_result}")
            return result
            
        except Exception as e:
            await self.session_manager.log_tool_call("plan_services", success=False, error=str(e))
            print(f"❌ plan_services error: {e}")
            return {"error": "TOOL_ERROR", "message": str(e)}

    @function_tool
    async def estimate(self, context: RunContext, vehicle: dict, services: list[str]):
        if "estimate" not in ALLOWED_TOOLS[self.state]:
            return {"error": "TOOL_NOT_ALLOWED"}
        
        print(f"💰 Executing estimate with vehicle: {vehicle}, services: {services}")
        
        try:
            out = await dispatch("estimate", {"vehicle": vehicle, "services": services}, IMPLS)
            print(f"💰 estimate result: {out}")
            
            if "ok" in out:
                self.state = next_after("estimate", self.state)
                print(f"🔄 State changed to: {self.state}")
                await self.session_manager.log_tool_call("estimate", success=True)
                await self.session_manager.log_customer_info({"services": services, "estimate": out.get("result")})
                await self.save_session_state()
            else:
                await self.session_manager.log_tool_call("estimate", success=False, error=str(out))
            
            result = out.get("result", out)
            print(f"💰 Returning: {result}")
            self._last_tool_result = ("estimate", result)
            print(f"💰 Stored tool result: {self._last_tool_result}")
            return result
            
        except Exception as e:
            await self.session_manager.log_tool_call("estimate", success=False, error=str(e))
            print(f"❌ estimate error: {e}")
            return {"error": "TOOL_ERROR", "message": str(e)}

    @function_tool
    async def find_slots(self, context: RunContext, duration_minutes: int, date_pref: str | None = None):
        if "find_slots" not in ALLOWED_TOOLS[self.state]:
            return {"error": "TOOL_NOT_ALLOWED"}
        
        print(f"📅 Executing find_slots with duration: {duration_minutes}min, date_pref: {date_pref}")
        
        try:
            out = await dispatch("find_slots", {"duration_minutes": duration_minutes, "date_pref": date_pref}, IMPLS)
            print(f"📅 find_slots result: {out}")
            
            if "ok" in out:
                self.state = next_after("find_slots", self.state)
                print(f"🔄 State changed to: {self.state}")
                await self.session_manager.log_tool_call("find_slots", success=True)
                await self.save_session_state()
            else:
                await self.session_manager.log_tool_call("find_slots", success=False, error=str(out))
            
            result = out.get("result", out)
            print(f"📅 Returning: {result}")
            self._last_tool_result = ("find_slots", result)
            print(f"📅 Stored tool result: {self._last_tool_result}")
            return result
            
        except Exception as e:
            await self.session_manager.log_tool_call("find_slots", success=False, error=str(e))
            print(f"❌ find_slots error: {e}")
            return {"error": "TOOL_ERROR", "message": str(e)}

    @function_tool
    async def book(self, context: RunContext, slot: dict, customer: dict, vehicle: dict, services: list[str], estimate: dict):
        if "book" not in ALLOWED_TOOLS[self.state]:
            return {"error": "TOOL_NOT_ALLOWED"}
        
        print(f"📝 Executing book with slot: {slot}, customer: {customer}, vehicle: {vehicle}, services: {services}")
        
        try:
            out = await dispatch("book", {"slot": slot, "customer": customer, "vehicle": vehicle,
                                          "services": services, "estimate": estimate}, IMPLS)
            print(f"📝 book result: {out}")
            
            if "ok" in out:
                self.state = next_after("book", self.state)
                print(f"🔄 State changed to: {self.state}")
                await self.session_manager.log_tool_call("book", success=True)
                await self.session_manager.log_customer_info({"customer": customer, "slot": slot})
                
                # Log successful booking
                booking_id = out.get("result", {}).get("booking_id")
                if booking_id:
                    await self.session_manager.log_booking(booking_id)
                
                # Mark session as successfully completed when booking is created
                await self.session_manager.complete_session(success=True, reason="booked")
                
                await self.save_session_state()
            else:
                await self.session_manager.log_tool_call("book", success=False, error=str(out))
            
            result = out.get("result", out)
            print(f"📝 Returning: {result}")
            self._last_tool_result = ("book", result)
            print(f"📝 Stored tool result: {self._last_tool_result}")
            return result
            
        except Exception as e:
            await self.session_manager.log_tool_call("book", success=False, error=str(e))
            print(f"❌ book error: {e}")
            return {"error": "TOOL_ERROR", "message": str(e)}

    @function_tool
    async def notify(self, context: RunContext, booking_id: str, channel: str = "sms"):
        if "notify" not in ALLOWED_TOOLS[self.state]:
            return {"error": "TOOL_NOT_ALLOWED"}
        
        print(f"📱 Executing notify with booking_id: {booking_id}, channel: {channel}")
        
        try:
            out = await dispatch("notify", {"booking_id": booking_id, "channel": channel}, IMPLS)
            print(f"📱 notify result: {out}")
            
            if "ok" in out:
                self.state = next_after("notify", self.state)
                print(f"🔄 State changed to: {self.state}")
                await self.session_manager.log_tool_call("notify", success=True)
                await self.save_session_state()
            else:
                await self.session_manager.log_tool_call("notify", success=False, error=str(out))
            
            result = out.get("result", out)
            print(f"📱 Returning: {result}")
            self._last_tool_result = ("notify", result)
            return result
            
        except Exception as e:
            await self.session_manager.log_tool_call("notify", success=False, error=str(e))
            print(f"❌ notify error: {e}")
            return {"error": "TOOL_ERROR", "message": str(e)}
    
    async def complete_session_with_reason(self, success: bool, reason: str):
        """Complete the session with a specific reason"""
        await self.session_manager.complete_session(success, reason)