import os, datetime as dt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def _get_credentials():
    """Get valid user credentials from storage or run OAuth flow."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), "token.json")
    credentials_path = os.path.join(os.path.dirname(__file__), "credentials.json")
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(token_path):
        print("📅 Loading credentials from token.json")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("📅 Refreshing expired credentials")
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print("⚠️ credentials.json not found, using fallback slots")
                return None
            print("📅 Running OAuth flow for first-time setup")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        print("📅 Credentials saved to token.json")
    
    return creds

def freebusy_windows(duration_minutes=60, days_ahead=14):
    try:
        # Get credentials using token.json
        creds = _get_credentials()
        if not creds:
            print("⚠️ Google Calendar credentials not available, using fallback slots")
            return _generate_fallback_slots(duration_minutes, days_ahead)
        
        print("📅 Connecting to Google Calendar API...")
        service = build("calendar", "v3", credentials=creds)
        cal_id = os.getenv("CALENDAR_ID", "primary")
        
        now = dt.datetime.utcnow().isoformat() + "Z"
        end = (dt.datetime.utcnow() + dt.timedelta(days=days_ahead)).isoformat() + "Z"
        
        print(f"📅 Querying calendar {cal_id} from {now} to {end}")
        fb = service.freebusy().query(body={
            "timeMin": now,
            "timeMax": end,
            "items": [{"id": cal_id}]
        }).execute()
        
        busy = fb["calendars"][cal_id].get("busy", [])
        print(f"📅 Found {len(busy)} busy periods in calendar")
        
        # synthesize slots between 9a-6p local, skipping busy ranges
        slots = []
        base = dt.datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc)
        for d in range(0, 5):
            start = base + dt.timedelta(days=d)
            for h in [0,1,2,3,4,5,6,7,8]:
                st = start + dt.timedelta(hours=h)
                en = st + dt.timedelta(minutes=duration_minutes)
                # naive conflict check
                conflict = False
                for b in busy:
                    bstart = dt.datetime.fromisoformat(b["start"].replace("Z","+00:00"))
                    bend = dt.datetime.fromisoformat(b["end"].replace("Z","+00:00"))
                    if not (en <= bstart or st >= bend):
                        conflict = True; break
                if not conflict:
                    slots.append({"start": st.isoformat(), "end": en.isoformat()})
        
        print(f"📅 Generated {len(slots)} available slots from Google Calendar")
        return slots[:10]
        
    except HttpError as error:
        print(f"❌ Google Calendar API HTTP error: {error}")
        print("🔄 Using fallback slots")
        return _generate_fallback_slots(duration_minutes, days_ahead)
    except Exception as e:
        print(f"❌ Google Calendar API error: {e}")
        print("🔄 Using fallback slots")
        return _generate_fallback_slots(duration_minutes, days_ahead)

def _generate_fallback_slots(duration_minutes=60, days_ahead=14):
    """Generate fallback slots when Google Calendar is not available"""
    slots = []
    base = dt.datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0, tzinfo=dt.timezone.utc)
    
    # Generate slots for next 5 business days, 9 AM to 5 PM
    for d in range(0, min(5, days_ahead)):
        start = base + dt.timedelta(days=d)
        for h in [0,1,2,3,4,5,6,7,8]:  # 9 AM to 5 PM
            st = start + dt.timedelta(hours=h)
            en = st + dt.timedelta(minutes=duration_minutes)
            slots.append({"start": st.isoformat(), "end": en.isoformat()})
    
    print(f"📅 Generated {len(slots)} fallback slots")
    return slots[:10]

def create_event(title: str, start_iso: str, end_iso: str, description: str = "") -> str:
    try:
        # Get credentials using token.json
        creds = _get_credentials()
        if not creds:
            print("⚠️ Google Calendar credentials not available, using fallback booking ID")
            return f"fallback-booking-{int(dt.datetime.utcnow().timestamp())}"
        
        print("📝 Connecting to Google Calendar API to create event...")
        service = build("calendar", "v3", credentials=creds)
        cal_id = os.getenv("CALENDAR_ID", "adityamalwade902@gmail.com")
        
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_iso},
            "end": {"dateTime": end_iso},
        }
        
        print(f"📝 Creating event in calendar {cal_id}: {title}")
        ev = service.events().insert(calendarId=cal_id, body=event).execute()
        print(f"📝 Successfully created calendar event: {ev['id']}")
        return ev["id"]
        
    except HttpError as error:
        print(f"❌ Google Calendar API HTTP error: {error}")
        print("🔄 Using fallback booking ID")
        return f"fallback-booking-{int(dt.datetime.utcnow().timestamp())}"
    except Exception as e:
        print(f"❌ Google Calendar event creation error: {e}")
        print("🔄 Using fallback booking ID")
        return f"fallback-booking-{int(dt.datetime.utcnow().timestamp())}"
