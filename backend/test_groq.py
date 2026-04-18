import asyncio
from groq import AsyncGroq
import os

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def test_groq():
    try:
        res = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("✅ Groq working:", res.choices[0].message.content)
    except Exception as e:
        print("❌ Groq error:", e)

asyncio.run(test_groq())