#!/usr/bin/env python3
"""
Test script to verify tool functionality
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agent import ServiceAgent
from app.fsm import State

async def test_tools():
    """Test if tools are working correctly"""
    print("🧪 Testing Agent Tools")
    print("=" * 30)
    
    # Create agent instance
    agent = ServiceAgent(
        room_id="test-room",
        instructions="You are a test agent. Use tools when you have information.",
        tools=[ServiceAgent.plan_services, ServiceAgent.estimate, ServiceAgent.find_slots, ServiceAgent.book, ServiceAgent.notify]
    )
    
    print(f"✅ Agent created with state: {agent.state}")
    print(f"✅ Available tools: {[tool.__name__ for tool in agent.tools]}")
    
    # Test plan_services tool
    print(f"\n🔧 Testing plan_services tool...")
    print(f"Current state: {agent.state}")
    print(f"Allowed tools for {agent.state}: {agent.state in ['COLLECT']}")
    
    try:
        # Simulate a tool call
        result = await agent.plan_services(
            context=None,
            vehicle={"year": 2022, "make": "Ford", "model": "Explorer"},
            issues=["suspension problem"]
        )
        print(f"✅ plan_services result: {result}")
        print(f"✅ New state: {agent.state}")
    except Exception as e:
        print(f"❌ plan_services failed: {e}")
    
    # Test estimate tool
    print(f"\n💰 Testing estimate tool...")
    try:
        result = await agent.estimate(
            context=None,
            vehicle={"year": 2022, "make": "Ford", "model": "Explorer"},
            services=["suspension_inspection"]
        )
        print(f"✅ estimate result: {result}")
        print(f"✅ New state: {agent.state}")
    except Exception as e:
        print(f"❌ estimate failed: {e}")
    
    # Test find_slots tool
    print(f"\n📅 Testing find_slots tool...")
    try:
        result = await agent.find_slots(
            context=None,
            duration_minutes=60,
            date_pref=None
        )
        print(f"✅ find_slots result: {result}")
        print(f"✅ New state: {agent.state}")
    except Exception as e:
        print(f"❌ find_slots failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tools())
