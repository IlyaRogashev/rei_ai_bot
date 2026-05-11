from duckduckgo_search import DDGS

async def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n\n".join(results)
    except Exception:
        return "Поиск не удался."