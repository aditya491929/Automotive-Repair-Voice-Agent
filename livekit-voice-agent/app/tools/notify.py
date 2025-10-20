import os
from sqlmodel import select
from ..dispatcher import NotifyIn
from ..db.session import get_session
from ..db.models import Booking

async def notify(inp: NotifyIn) -> dict:
    """Send notification to customer about their booking"""
    try:
        # Get booking details from database
        with get_session() as s:
            booking = s.exec(select(Booking).where(Booking.id == inp.booking_id)).first()
            if not booking:
                return {"error": "BOOKING_NOT_FOUND"}
        
        if inp.channel == "sms":
            # Try to send SMS via Twilio
            if all([os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), os.getenv("TWILIO_PHONE_NUMBER")]):
                try:
                    from twilio.rest import Client
                    
                    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
                    
                    message = f"Hi {booking.customer_name}! Your appointment is confirmed for {booking.vehicle_year} {booking.vehicle_make} {booking.vehicle_model}. Services: {', '.join(booking.services)}. Estimated cost: ${booking.price_low}-${booking.price_high}. Booking ID: {inp.booking_id}"
                    
                    sms = client.messages.create(
                        body=message,
                        from_=os.getenv("TWILIO_PHONE_NUMBER"),
                        to=booking.phone
                    )
                    
                    print(f"📱 SMS sent successfully: {sms.sid}")
                    return NotifyOut(success=True, message_id=sms.sid, channel="sms").model_dump()
                    
                except Exception as e:
                    print(f"❌ SMS sending failed: {e}")
                    return {"error": "SMS_SEND_FAILED", "message": str(e)}
            else:
                print("⚠️ Twilio credentials not found, skipping SMS")
                return {"error": "SMS_CREDENTIALS_MISSING"}
        
        elif inp.channel == "none":
            print(f"📝 Notification skipped for booking {inp.booking_id}")
            return NotifyOut(success=True, message_id="none", channel="none").model_dump()
        
        else:
            return {"error": "UNSUPPORTED_CHANNEL"}
            
    except Exception as e:
        print(f"❌ Notification error: {e}")
        return {"error": "NOTIFICATION_FAILED", "message": str(e)}