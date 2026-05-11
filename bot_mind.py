import os
from dotenv import load_dotenv
from huggingface_hub import AsyncInferenceClient

load_dotenv()
ai_token = os.getenv("AI_TOKEN")

try:
    with open('prompt_for_diary.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
except FileNotFoundError:
    print("Предупреждение: файл prompt_for_diary.txt не найден.")


try:
    with open('model_context.txt', 'r', encoding='utf-8') as f:
        model_context = f.read()
except FileNotFoundError:
    print("Предупреждение: файл model_context.txt не найден.")


client = AsyncInferenceClient(
    model="meta-llama/Llama-3.1-8B-Instruct",
    token=ai_token
)

async def get_ai_response(text: str, history: list = None) -> str:
    if history is None:
        history = []

    messages = [{"role": "system", "content": model_context}]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    try:
        response = await client.chat_completion(
            messages=messages,
            max_tokens=500,
            stream=False,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка ИИ: {e}"


async def summarize_to_diary(old_diary: str, history: list) -> str:
    history_text = ""
    for msg in history:
        role = "Собеседник" if msg["role"] == "user" else "Бот"
        history_text += f"{role}: {msg['content']}\n"

    summary_prompt = f"""{prompt}

    СТАРЫЙ ДНЕВНИК:
    {old_diary if old_diary else "Записей пока нет."}

    НОВАЯ ПЕРЕПИСКА:
    {history_text}
    """

    messages = [{"role": "system", "content": summary_prompt}]

    try:
        response = await client.chat.completions.create(
            model="local-model",
            messages=messages,
            max_tokens=500,
            temperature=0.2,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка суммаризации: {e}")
        return old_diary
