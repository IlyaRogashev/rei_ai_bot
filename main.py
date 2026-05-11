import os
import logging
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from bot_mind import get_ai_response, summarize_to_diary
import asyncio
from telegram.constants import ChatAction

#Мировая тайна
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


    diary_content = ""
    if os.path.exists(diary_path):
        with open(diary_path, "r", encoding="utf-8") as f:
            diary_content = f.read()

    if 'history' not in context.user_data:
        context.user_data['history'] = []


# Передаем дневник ии
    memory_context = [{"role": "system", "content": f"Твои записи о юзере:\n{diary_content}"}]
    full_history = memory_context + context.user_data['history']

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    except Exception as e:
        print(f"Не удалось отправить статус печати: {e}")
#_______________________________________________________________________________________________________________________
#Получение ответа
    ai_answer = await get_ai_response(user_text, full_history)
    try:
        typing_duration = min(len(ai_answer) * 0.04, 6.0) 
        typing_duration += random.uniform(0.5, 1.5)
    
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(typing_duration)
    except Exception as e:
        print(f"Ошибка при имитации печати: {e}")
#Оперативка
    context.user_data['history'].append({"role": "user", "content": user_text})
    context.user_data['history'].append({"role": "assistant", "content": ai_answer})

# Обновление дневника
    if len(context.user_data['history']) >= 6:
        history_copy = context.user_data['history'].copy()
        context.user_data['history'] = []

        async def background_diary_update(h_copy, d_path, d_content):
            try:
                new_version = await summarize_to_diary(d_content, h_copy)
                if new_version:
                    with open(d_path, "w", encoding="utf-8") as f:
                        f.write(new_version)
            except Exception as e:
                print(f"Ошибка фонового дневника: {e}")

        asyncio.create_task(background_diary_update(history_copy, diary_path, diary_content))

    try:
        await update.message.reply_text(ai_answer)
    except Exception as e:
        logging.error(f"Ошибка при отправке ответа: {e}")


def run_bot():
    base_url = f"{cloudflare_url}/bot"
    application = (
        ApplicationBuilder()
        .token(bot_token)
        .base_url(base_url)
        .read_timeout(100)
        .connect_timeout(120)
        .get_updates_read_timeout(120)
        .build()
    )
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(timeout=100)


if __name__ == '__main__':
    run_bot()
