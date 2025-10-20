#!/usr/bin/env python3
"""
Analytics script for the automotive voice agent
Usage: python analytics.py [--days 7] [--export]
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.session_manager import get_session_analytics, print_session_analytics
from app.db.session import get_session
from app.db.models import SessionLog, Booking
from sqlmodel import select

def export_analytics(days: int = 7, format: str = "json"):
    """Export analytics data to file"""
    analytics = get_session_analytics(days)
    
    if "error" in analytics:
        print(f"❌ {analytics['error']}")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == "json":
        filename = f"analytics_{days}days_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(analytics, f, indent=2)
        print(f"📊 Analytics exported to {filename}")
    
    elif format == "csv":
        filename = f"analytics_{days}days_{timestamp}.csv"
        with open(filename, 'w') as f:
            f.write("Metric,Value\n")
            f.write(f"Total Sessions,{analytics['total_sessions']}\n")
            f.write(f"Completed Sessions,{analytics['completed_sessions']}\n")
            f.write(f"Successful Sessions,{analytics['successful_sessions']}\n")
            f.write(f"Completion Rate,{analytics['completion_rate']}%\n")
            f.write(f"Success Rate,{analytics['success_rate']}%\n")
            f.write(f"Average Duration,{analytics['average_duration_seconds']}s\n")
            
            f.write("\nTool Usage\n")
            for tool, stats in analytics['tool_usage'].items():
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                f.write(f"{tool},{stats['total']} calls ({success_rate:.1f}% success)\n")
            
            f.write("\nCompletion Reasons\n")
            for reason, count in analytics['completion_reasons'].items():
                f.write(f"{reason},{count}\n")
        
        print(f"📊 Analytics exported to {filename}")

def show_recent_sessions(limit: int = 10):
    """Show recent session details"""
    with get_session() as s:
        sessions = s.exec(
            select(SessionLog)
            .order_by(SessionLog.created_at.desc())
            .limit(limit)
        ).all()
        
        if not sessions:
            print("📊 No sessions found")
            return
        
        print(f"\n📊 Recent Sessions (Last {limit})")
        print("=" * 80)
        print(f"{'ID':<4} {'Room':<15} {'State':<12} {'Success':<8} {'Duration':<10} {'Reason':<15} {'Created'}")
        print("-" * 80)
        
        for session in sessions:
            duration = "N/A"
            if session.completed_at:
                duration = f"{(session.completed_at - session.created_at).total_seconds():.0f}s"
            
            success_icon = "✅" if session.success else "❌"
            reason = session.completion_reason or "ongoing"
            
            print(f"{session.id:<4} {session.room_id:<15} {session.state:<12} {success_icon:<8} {duration:<10} {reason:<15} {session.created_at.strftime('%m/%d %H:%M')}")

def show_booking_summary():
    """Show booking summary"""
    with get_session() as s:
        bookings = s.exec(select(Booking)).all()
        
        if not bookings:
            print("📊 No bookings found")
            return
        
        print(f"\n📊 Booking Summary ({len(bookings)} total)")
        print("=" * 60)
        print(f"{'ID':<4} {'Customer':<15} {'Vehicle':<20} {'Services':<15} {'Price':<12} {'Date'}")
        print("-" * 60)
        
        for booking in bookings:
            vehicle = f"{booking.vehicle_year} {booking.vehicle_make} {booking.vehicle_model}"
            services = ", ".join(booking.services[:2])  # Show first 2 services
            if len(booking.services) > 2:
                services += "..."
            price = f"${booking.price_low}-${booking.price_high}"
            
            print(f"{booking.id:<4} {booking.customer_name:<15} {vehicle:<20} {services:<15} {price:<12} {booking.created_at.strftime('%m/%d %H:%M')}")

def main():
    parser = argparse.ArgumentParser(description="Automotive Voice Agent Analytics")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    parser.add_argument("--export", choices=["json", "csv"], help="Export analytics to file")
    parser.add_argument("--sessions", type=int, help="Show recent sessions (limit)")
    parser.add_argument("--bookings", action="store_true", help="Show booking summary")
    parser.add_argument("--all", action="store_true", help="Show all analytics")
    
    args = parser.parse_args()
    
    if args.all or (not args.export and not args.sessions and not args.bookings):
        # Default: show analytics summary
        print_session_analytics(args.days)
    
    if args.export:
        export_analytics(args.days, args.export)
    
    if args.sessions:
        show_recent_sessions(args.sessions)
    
    if args.bookings:
        show_booking_summary()

if __name__ == "__main__":
    main()
