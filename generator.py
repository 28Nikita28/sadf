import aiohttp
import json
import logging
from pprint import pformat

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str, model: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            payload = {"userInput": text, "model": model}

            async with session.post(ai_url, json=payload, headers=headers) as response:
                response.raise_for_status()
                response_data = await response.json()

                # Форматирование сложных структур
                if isinstance(response_data, dict):
                    content = response_data.get("content", "")
                    if any(kw in content for kw in ["{", "}", "[", "]", "="]):
                        return pformat(content, width=80)
                    return content
                return "⚠️ Некорректный формат ответа"

    except aiohttp.ClientError as e:
        logger.error(f"Connection error: {e}")
        return "🔌 Ошибка соединения с сервисом"
    except json.JSONDecodeError:
        logger.error("Invalid JSON response")
        return "📄 Ошибка формата ответа"
    except Exception as e:
        logger.error(f"General error: {e}")
        return "⚙️ Внутренняя ошибка сервиса"