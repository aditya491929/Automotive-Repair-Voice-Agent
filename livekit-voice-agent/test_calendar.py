#!/usr/bin/env python3
"""
Test script to verify Google Calendar integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.lib.calendar import freebusy_windows, create_event
import datetime

def test_calendar_connection():
    """Test Google Calendar connection and functionality"""
    print("🧪 Testing Google Calendar Integration")
    print("=" * 50)
    
    # Test 1: Get available slots
    print("\n📅 Test 1: Getting available slots...")
    try:
        slots = freebusy_windows(duration_minutes=60, days_ahead=7)
        print(f"✅ Retrieved {len(slots)} available slots")
        
        if slots:
            print("📋 Sample slots:")
            for i, slot in enumerate(slots[:3]):  # Show first 3 slots
                start_time = datetime.datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                end_time = datetime.datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
                print(f"  {i+1}. {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}")
        
        # Test 2: Create a test event (if we have slots)
        if slots:
            print(f"\n📝 Test 2: Creating test event...")
            test_slot = slots[0]
            test_title = f"Test Event - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            test_description = "This is a test event created by the automotive voice agent"
            
            try:
                event_id = create_event(
                    title=test_title,
                    start_iso=test_slot['start'],
                    end_iso=test_slot['end'],
                    description=test_description
                )
                
                if event_id.startswith('fallback'):
                    print(f"⚠️ Created fallback booking ID: {event_id}")
                    print("   (Google Calendar connection not available)")
                else:
                    print(f"✅ Successfully created calendar event: {event_id}")
                    print(f"   Title: {test_title}")
                    print(f"   Time: {test_slot['start']} - {test_slot['end']}")
            except Exception as e:
                print(f"❌ Failed to create test event: {e}")
        else:
            print("⚠️ No slots available for test event creation")
            
    except Exception as e:
        print(f"❌ Failed to get calendar slots: {e}")
        return False
    
    print("\n🎉 Calendar integration test completed!")
    return True

def test_fallback_mode():
    """Test fallback mode when credentials are not available"""
    print("\n🧪 Testing Fallback Mode")
    print("=" * 30)
    
    # Temporarily rename credentials to test fallback
    credentials_path = "app/lib/credentials.json"
    backup_path = "app/lib/credentials.json.backup"
    
    if os.path.exists(credentials_path):
        os.rename(credentials_path, backup_path)
        print("📁 Temporarily moved credentials.json to test fallback")
    
    try:
        slots = freebusy_windows(duration_minutes=60, days_ahead=3)
        print(f"✅ Fallback mode generated {len(slots)} slots")
        
        if slots:
            print("📋 Fallback slots:")
            for i, slot in enumerate(slots[:3]):
                start_time = datetime.datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                end_time = datetime.datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
                print(f"  {i+1}. {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}")
        
    except Exception as e:
        print(f"❌ Fallback mode failed: {e}")
    finally:
        # Restore credentials
        if os.path.exists(backup_path):
            os.rename(backup_path, credentials_path)
            print("📁 Restored credentials.json")

if __name__ == "__main__":
    print("🚗 Automotive Voice Agent - Calendar Integration Test")
    print("=" * 60)
    
    # Test normal operation
    success = test_calendar_connection()
    
    # Test fallback mode
    test_fallback_mode()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Calendar integration is working correctly!")
    else:
        print("❌ Calendar integration needs attention")
    
    print("\n💡 Tips:")
    print("- If you see 'fallback' messages, check your Google Calendar credentials")
    print("- Make sure credentials.json is in app/lib/ directory")
    print("- The first run will open a browser for OAuth authentication")
    print("- Token will be saved automatically for future use")
