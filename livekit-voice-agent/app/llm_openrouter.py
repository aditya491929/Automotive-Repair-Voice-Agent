from openai import OpenAI
import os

client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL","https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

async def chat(messages, model=None):
    model = model or os.getenv("OPENROUTER_MODEL")
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type":"json_object"},
        temperature=0.3
    )
    return resp.choices[0].message.content
