from duckduckgo_search import DDGS

async def search_internet(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='ru-ru', safesearch='moderate', max_results=3))
            if not results:
                return "Информация в сети не найдена."
            
            context = "\n\nРЕЗУЛЬТАТЫ ИЗ ИНТЕРНЕТА:\n"
            for res in results:
                context += f"Заголовок: {res['title']}\nОписание: {res['body']}\n\n"
            return context
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return ""

async def needs_search(text: str, client) -> bool:
    # 1. Простая проверка на короткие фразы
    words = text.lower().split()
    if len(words) < 2 and words[0] in ["привет", "хай", "ку", "здравствуй"]:
        return False

    # 2. Промпт с примерами
    decision_prompt = (
        "Ты — диспетчер поиска. Отвечай только ДА, если вопрос требует поиска фактов, "
        "биографий, дат или новостей. Отвечай НЕТ, если это простое общение или пользователь спрашивает личные факты о тебе.\n"
        f"Запрос: '{text}'\n"
        "Нужен поиск? Ответ (ДА/НЕТ):"
    )

    try:
        response = await client.chat_completion(
            messages=[{"role": "user", "content": decision_prompt}],
            max_tokens=5,
            temperature=0.0 
        )
        answer = response.choices[0].message.content.strip().lower()
        print(f"[DEBUG] Решение поиска для '{text}': {answer}", flush=True)
        
        return "да" in answer
    except Exception as e:
        print(f"[DEBUG] Ошибка классификатора: {e}")
        return False
