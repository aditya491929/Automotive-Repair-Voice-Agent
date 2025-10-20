import os, json, asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, AgentSession
from livekit.plugins import deepgram, elevenlabs, openai as lk_openai, silero
from app.agent import ServiceAgent, PROMPTS
from app.db.session import init_db

load_dotenv()

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    init_db()
    
    # Seed database with initial data
    from app.db.seed import run_seed
    try:
        run_seed()
        print("✅ Database seeded successfully")
    except Exception as e:
        print(f"⚠️ Database seeding failed: {e}")
        print("🔄 Continuing with existing data...")

    # --- STT / LLM / TTS ---
    stt = deepgram.STT(model="nova-3", api_key=os.getenv("DEEPGRAM_API_KEY"))  # Deepgram STT

    # Use LiveKit OpenAI plugin pointed to OpenRouter (OpenAI-compatible)
    llm = lk_openai.LLM(
        model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.3,
        parallel_tool_calls=True,
    )  # base_url + api_key override => OpenRouter backend. (Doc-supported.)  # :contentReference[oaicite:3]{index=3}

    # Try ElevenLabs TTS with error handling
    try:
        # tts = elevenlabs.TTS(
        #     api_key=os.getenv("ELEVENLABS_API_KEY"),
        #     voice_id=os.getenv("ELEVENLABS_VOICE_ID", "ODq5zmih8GrVes37Dizd"),
        #     model=os.getenv("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2"),
        # )
        tts = deepgram.TTS(
            model="aura-2-thalia-en",
            api_key=os.getenv("DEEPGRAM_API_KEY"),
        )
        print("✅ Deepgram TTS initialized")
    except Exception as e:
        print(f"❌ Deepgram TTS failed: {e}")
        print("🔄 Falling back to OpenAI TTS...")
        # Fallback to OpenAI TTS
        tts = lk_openai.TTS(
            model="tts-1",
            voice="alloy",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )

    agent = ServiceAgent(
        room_id=ctx.room.name,
        instructions=PROMPTS["system"],
    )

    session = AgentSession(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=silero.VAD.load(),
    )
    
    # Add comprehensive logging
    @session.on("agent_speech_committed")
    def on_agent_speech(text: str):
        print(f"🤖 Agent said: {text}")
    
    @session.on("user_speech_committed") 
    def on_user_speech(text: str):
        print(f"👤 User said: {text}")
    
    @session.on("llm_response")
    def on_llm_response(response: str):
        print(f"🧠 LLM Response: {response}")
    
    @session.on("tool_call")
    def on_tool_call(tool_name: str, args: dict):
        print(f"🔧 Tool Call: {tool_name} with args: {args}")
    
    # Listen for tool execution completion and generate responses
    @session.on("tools_execution_completed")
    def on_tools_execution_completed(speech_id: str):
        print(f"🔧 Tools execution completed for speech: {speech_id}")
        
        async def handle_completion():
            try:
                # Get the last tool result from the agent and generate a response
                if hasattr(agent, '_last_tool_result') and agent._last_tool_result:
                    tool_name, result = agent._last_tool_result
                    print(f"🔧 Processing tool result: {tool_name} -> {result}")
                    response = await agent.on_tool_result(tool_name, result)
                    if response:
                        print(f"🎤 Sending tool response: {response}")
                        await session.generate_reply(instructions=response)
                    else:
                        print(f"⚠️ No response generated for tool: {tool_name}")
                else:
                    print(f"⚠️ No tool result available for speech: {speech_id}")
            except Exception as e:
                print(f"❌ Error handling tool completion: {e}")
                import traceback
                traceback.print_exc()
        
        asyncio.create_task(handle_completion())
    
    # Add more detailed logging for debugging
    @session.on("agent_message")
    def on_agent_message(message: str):
        print(f"💬 Agent Message: {message}")
    
    @session.on("user_message")
    def on_user_message(message: str):
        print(f"💬 User Message: {message}")

    # Initialize session tracking
    await agent.initialize_session()
    
    await session.start(agent=agent, room=ctx.room)
    print(f"🎤 Sending greeting: {PROMPTS['first_turn']}")
    await session.generate_reply(instructions=PROMPTS["first_turn"])

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="inbound-agent",
        ))