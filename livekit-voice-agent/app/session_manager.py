import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlmodel import select, update
from .db.session import get_session
from .db.models import SessionLog
from .fsm import State

class SessionManager:
    """Manages conversation session state and metrics"""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.session_id: Optional[int] = None
        self.start_time = datetime.utcnow()
        self.tool_calls: Dict[str, int] = {}
        self.errors: list = []
        self.customer_info: Dict[str, Any] = {}
        self.booking_id: Optional[str] = None
        
    async def create_session(self, initial_state: State = State.COLLECT) -> int:
        """Create a new session log entry"""
        with get_session() as s:
            session_log = SessionLog(
                room_id=self.room_id,
                state=initial_state.value,
                turns=0,
                metrics={
                    "start_time": self.start_time.isoformat(),
                    "tool_calls": {},
                    "errors": [],
                    "customer_info": {},
                    "booking_id": None
                },
                success=False,
                completion_reason=None
            )
            s.add(session_log)
            s.commit()
            s.refresh(session_log)
            self.session_id = session_log.id
            print(f"📊 Created session {self.session_id} for room {self.room_id} with success=False")
            return session_log.id
    
    async def update_session_state(self, state: State, turns: int = None):
        """Update the current state and turn count"""
        if not self.session_id:
            await self.create_session(state)
            return
            
        with get_session() as s:
            # Update the session record
            session = s.exec(select(SessionLog).where(SessionLog.id == self.session_id)).first()
            if session:
                session.state = state.value
                if turns is not None:
                    session.turns = turns
                session.updated_at = datetime.utcnow()
                
                # Update metrics
                metrics = session.metrics.copy()
                metrics["current_state"] = state.value
                metrics["last_activity"] = datetime.utcnow().isoformat()
                metrics["tool_calls"] = self.tool_calls.copy()
                metrics["errors"] = self.errors.copy()
                metrics["customer_info"] = self.customer_info.copy()
                if self.booking_id:
                    metrics["booking_id"] = self.booking_id
                
                session.metrics = metrics
                s.commit()
                print(f"📊 Updated session {self.session_id}: {state.value} (turn {turns})")
    
    async def log_tool_call(self, tool_name: str, success: bool = True, error: str = None):
        """Log a tool call for metrics tracking"""
        if tool_name not in self.tool_calls:
            self.tool_calls[tool_name] = {"total": 0, "successful": 0, "failed": 0}
        
        self.tool_calls[tool_name]["total"] += 1
        if success:
            self.tool_calls[tool_name]["successful"] += 1
        else:
            self.tool_calls[tool_name]["failed"] += 1
            if error:
                self.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "tool": tool_name,
                    "error": error
                })
        
        # Update session immediately
        await self.update_session_state(State(self.get_current_state()))
    
    async def log_customer_info(self, info: Dict[str, Any]):
        """Log customer information for analytics"""
        self.customer_info.update(info)
        await self.update_session_state(State(self.get_current_state()))
    
    async def log_booking(self, booking_id: str):
        """Log successful booking"""
        self.booking_id = booking_id
        await self.update_session_state(State(self.get_current_state()))
    
    async def complete_session(self, success: bool, reason: str):
        """Mark session as completed with success status"""
        if not self.session_id:
            print(f"⚠️ Cannot complete session: no session_id")
            return
            
        with get_session() as s:
            session = s.exec(select(SessionLog).where(SessionLog.id == self.session_id)).first()
            if session:
                session.success = success
                session.completion_reason = reason
                session.completed_at = datetime.utcnow()
                
                # Calculate final metrics
                duration = (session.completed_at - session.created_at).total_seconds()
                metrics = session.metrics.copy()
                metrics["duration_seconds"] = duration
                metrics["final_state"] = session.state
                metrics["completion_reason"] = reason
                metrics["tool_calls"] = self.tool_calls.copy()
                metrics["errors"] = self.errors.copy()
                metrics["customer_info"] = self.customer_info.copy()
                if self.booking_id:
                    metrics["booking_id"] = self.booking_id
                
                session.metrics = metrics
                s.commit()
                
                status_emoji = "✅" if success else "❌"
                print(f"📊 {status_emoji} Completed session {self.session_id}: {reason} (duration: {duration:.1f}s)")
    
    def get_current_state(self) -> str:
        """Get current state from database"""
        if not self.session_id:
            return State.COLLECT.value
            
        with get_session() as s:
            session = s.exec(select(SessionLog).where(SessionLog.id == self.session_id)).first()
            return session.state if session else State.COLLECT.value
    
    async def load_session_state(self) -> Optional[State]:
        """Load existing session state from database"""
        with get_session() as s:
            # Look for the most recent incomplete session for this room
            session = s.exec(
                select(SessionLog)
                .where(SessionLog.room_id == self.room_id)
                .where(SessionLog.completed_at.is_(None))
                .order_by(SessionLog.created_at.desc())
            ).first()
            
            if session:
                self.session_id = session.id
                self.tool_calls = session.metrics.get("tool_calls", {})
                self.errors = session.metrics.get("errors", [])
                self.customer_info = session.metrics.get("customer_info", {})
                self.booking_id = session.metrics.get("booking_id")
                print(f"📊 Loaded existing session {self.session_id}: {session.state}")
                return State(session.state)
        return None

# Analytics functions
def get_session_analytics(days: int = 7) -> Dict[str, Any]:
    """Get analytics for recent sessions"""
    with get_session() as s:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all sessions in date range
        sessions = s.exec(
            select(SessionLog).where(SessionLog.created_at >= cutoff_date)
        ).all()
        
        if not sessions:
            return {"error": "No sessions found"}
        
        total_sessions = len(sessions)
        completed_sessions = [s for s in sessions if s.completed_at]
        successful_sessions = [s for s in completed_sessions if s.success]
        
        # Calculate metrics
        completion_rate = len(completed_sessions) / total_sessions if total_sessions > 0 else 0
        success_rate = len(successful_sessions) / len(completed_sessions) if completed_sessions else 0
        
        # Average duration
        durations = [(s.completed_at - s.created_at).total_seconds() for s in completed_sessions]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Tool usage statistics
        tool_stats = {}
        for session in sessions:
            for tool, stats in session.metrics.get("tool_calls", {}).items():
                if tool not in tool_stats:
                    tool_stats[tool] = {"total": 0, "successful": 0, "failed": 0}
                tool_stats[tool]["total"] += stats.get("total", 0)
                tool_stats[tool]["successful"] += stats.get("successful", 0)
                tool_stats[tool]["failed"] += stats.get("failed", 0)
        
        # Completion reasons
        completion_reasons = {}
        for session in completed_sessions:
            reason = session.completion_reason or "unknown"
            completion_reasons[reason] = completion_reasons.get(reason, 0) + 1
        
        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "completed_sessions": len(completed_sessions),
            "successful_sessions": len(successful_sessions),
            "completion_rate": round(completion_rate * 100, 1),
            "success_rate": round(success_rate * 100, 1),
            "average_duration_seconds": round(avg_duration, 1),
            "tool_usage": tool_stats,
            "completion_reasons": completion_reasons,
            "generated_at": datetime.utcnow().isoformat()
        }

def print_session_analytics(days: int = 7):
    """Print formatted session analytics"""
    analytics = get_session_analytics(days)
    
    if "error" in analytics:
        print(f"📊 {analytics['error']}")
        return
    
    print(f"\n📊 Session Analytics (Last {days} days)")
    print("=" * 50)
    print(f"Total Sessions: {analytics['total_sessions']}")
    print(f"Completed: {analytics['completed_sessions']} ({analytics['completion_rate']}%)")
    print(f"Successful: {analytics['successful_sessions']} ({analytics['success_rate']}%)")
    print(f"Avg Duration: {analytics['average_duration_seconds']}s")
    
    print(f"\n🔧 Tool Usage:")
    for tool, stats in analytics['tool_usage'].items():
        success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {tool}: {stats['total']} calls ({success_rate:.1f}% success)")
    
    print(f"\n📋 Completion Reasons:")
    for reason, count in analytics['completion_reasons'].items():
        print(f"  {reason}: {count}")
    
    print("=" * 50)
