# Automotive-Repair-Voice-Agent

### AI-Powered Conversational Booking System for Automotive Service Centers  

[DEMO](https://drive.google.com/file/d/1rQVq4hEikbvjXucrD2ubmYWzne4x9Ulh/view?usp=sharing)

---

## Overview  

The **Automotive Repair Voice Agent** is an end-to-end, real-time voice assistant that allows customers to describe vehicle issues naturally and receive:
- **Instant service recommendations** based on symptoms  
- **Accurate cost and time estimates**  
- **Available appointment slots** via Google Calendar  
- **Automated booking confirmations**

The system transforms a traditionally manual, phone-based workflow into a **24/7 conversational experience** that reduces friction, saves staff time, and improves customer satisfaction.

---

## Problem & Motivation  

Traditional auto-repair scheduling relies on manual calls:  
> “My car is making a rattling sound, can I book a check?”  

This leads to:
- Long hold times during peak hours  
- Inconsistent price estimates  
- Missed leads due to limited business hours  

Our solution uses **AI voice automation** to enable self-service booking with human-like dialogue and consistent pricing — delivering **machine efficiency with a human touch**.

---

## System Architecture  

```
Caller 
  ↓
Deepgram STT  →  DeepSeek LLM (via OpenRouter API)  →  Tool Calls (plan | estimate | book)
                         ↓
                 LiveKit Session Manager  ↔  SQLite DB
                         ↓
          Google Calendar API  →  Event  →  Twilio SMS (A2P 10DLC pending)
                         ↓
                    Deepgram TTS  →  Caller Response
```

---

## Tech Stack  

| Layer | Technology | Purpose |
|-------|-------------|----------|
| **Voice Framework** | [LiveKit Agents](https://docs.livekit.io/agents/start/voice-ai/) | Real-time orchestration (STT + TTS + VAD) |
| **Speech-to-Text** | Deepgram Nova-3 | High-accuracy transcription |
| **Large Language Model** | DeepSeek V2 / 3.5 Sonnet via [OpenRouter](https://openrouter.ai) | Natural conversation + tool reasoning |
| **Text-to-Speech** | Deepgram Aura-2 Thalia | Realistic voice synthesis |
| **Database** | SQLite + SQLModel | Session persistence & analytics |
| **Calendar API** | Google Calendar | Slot lookup & event creation |
| **Notification** | Twilio SMS *(pending A2P approval)* | Appointment confirmations |
| **Data Source** | JSON Service Catalog | 100 + automotive services & mappings |

---

## Core Features  

- **Natural Voice Interaction** – Understands free-form customer speech  
- **Symptom-to-Service Mapping** – Maps 50 + common car issues to repair tasks  
- **Dynamic Cost Estimation** – Calculates labor + parts + tax in real time  
- **Smart Scheduling** – Fetches available slots from Google Calendar  
- **Upsell Logic** – Suggests preventive maintenance based on mileage  
- **Session Persistence** – Stores state, pricing, and conversation logs  
- **Scalable FSM Architecture** – Six conversation states:  
  `COLLECT → PLAN → ESTIMATE → OFFER_SLOTS → BOOK → NOTIFY`

---

## Quick Start  

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Calendar API credentials
- API keys for Deepgram, OpenRouter, and Twilio

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/automotive-repair-voice-agent.git
   cd automotive-repair-voice-agent
   ```

2. **Install dependencies**

   ```bash
   cd livekit-voice-agent
   uv sync
   ```

3. **Set up environment variables**

   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

4. **Configure Google Calendar**

   ```bash
   # Place your Google Calendar credentials.json in app/lib/
   # Run the agent once to complete OAuth flow
   ```

5. **Initialize database**

   ```bash
   uv run python -m app.db.seed
   ```

6. **Run the agent**
   ```bash
   uv run python -m app.main console
   ```

---

## Current Status  

✅ **End-to-End Voice Flow** — from STT → LLM → Booking  
✅ **100 + Service Catalog** with realistic pricing  
✅ **Stateful FSM** for controlled conversation  
✅ **Google Calendar Integration** for slot management  
🟡 **Twilio SMS Integration** pending A2P 10DLC approval  

---

## Next Steps  

| Area | Plan | Benefit |
|------|------|----------|
| **Twilio SMS/Voice** | Enable confirmations & reminders | Customer retention |
| **Multi-Agent Flow** | Specialized agents for complex repairs | Scalability |
| **Predictive Maintenance** | Use history + mileage | Personalization |
| **Multilingual Support** | Add Spanish / French voices | Accessibility |
| **Cloud Deployment** | AWS/Azure auto-scaling | Production readiness |
