#main.py
'''import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters,  CommandHandler
from bot_mind import get_ai_response, summarize_to_diary

#мировая тайна
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
cloudflare_url = os.getenv("WORKER_URL")

DIARY_DIR = "diaries"
if not os.path.exists(DIARY_DIR):
    os.makedirs(DIARY_DIR)

logging.basicConfig(level=logging.INFO)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['history'] = []
    await update.message.reply_text("Память очищена!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    diary_path = os.path.join(DIARY_DIR, f"{user_id}.txt")

    # 1. Загружаем дневник из файла
    diary_content = ""
    if os.path.exists(diary_path):
        with open(diary_path, "r", encoding="utf-8") as f:
            diary_content = f.read()

    # 2. Подготовка истории (добавляем дневник как системное знание)
    if 'history' not in context.user_data:
        context.user_data['history'] = []

    # Временный контекст для ИИ: инструкции + дневник
    memory_context = [{"role": "system", "content": f"Твои записи о юзере: {diary_content}"}]
    full_history = memory_context + context.user_data['history']

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")


    ai_answer = await get_ai_response(user_text, full_history)

    #Сохраняем в историю переписки (в оперативку)
    context.user_data['history'].append({"role": "user", "content": user_text})
    context.user_data['history'].append({"role": "assistant", "content": ai_answer})


    if len(context.user_data['history']) >= 6:
        new_entry = await summarize_to_diary(context.user_data['history'])
        if new_entry:
            with open(diary_path, "a", encoding="utf-8") as f:
                f.write(f"\n{new_entry}")
            print(f"Дневник юзера {user_id} обновлен.")
            # Очищаем историю, чтобы не дублировать факты
            context.user_data['history'] = []

    await update.message.reply_text(ai_answer)


def run_bot():
    base_url = f"{cloudflare_url}/bot"

    application = (
        ApplicationBuilder()
        .token(bot_token)
        .base_url(base_url)
        .build()
    )
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()


if __name__ == '__main__':
    run_bot()
'''
#bot_mind.py
'''import os
from dotenv import load_dotenv
from huggingface_hub import AsyncInferenceClient

load_dotenv()
ai_token = os.getenv("AI_TOKEN")


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

    messages = [
        {"role": "system", "content": model_context}
    ]
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
        return f"Ошибка: {e}"


async def summarize_to_diary(history: list) -> str:
    """Просит ИИ выписать важные факты из истории сообщений"""
    client_summary = AsyncInferenceClient(model="meta-llama/Llama-3.1-8B-Instruct", token=ai_token)

    prompt = "Ты — девушка по имени Рэй(на английском Rei). Тебе 20 лет. Твоя цель: общаться в Telegram так, чтобы никто не догадался, что ты нейросеть. Ниже приведена переписка. Запиши себе важные факты, произошедшие за время вашего общения. Пиши кратко, как в дневник. Используй только язык, на котором с тобой общается пользователь."

    # Формируем текст из истории
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    full_prompt = f"{prompt}\n\nПереписка:\n{history_text}"

    try:
        response = await client_summary.chat_completion(
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception:
        return ""'''