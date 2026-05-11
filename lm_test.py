import asyncio
from openai import AsyncOpenAI

async def test():
    client = AsyncOpenAI(base_url="http://127.0.0", api_key="lm-studio")
    try:
        resp = await client.chat.completions.create(
            model="meta-llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "Привет"}]
        )
        print(resp.choices[0].message.content)
    except Exception as e:
        print(f"Ошибка: {e}")

asyncio.run(test())