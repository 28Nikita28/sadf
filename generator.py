# generator.py
import json
import aiohttp
import logging
import asyncio
from pprint import pformat

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str, model: str) -> str:
    max_retries = 3
    timeout = aiohttp.ClientTimeout(total=60)
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {"Content-Type": "application/json"}
                payload = {"userInput": text, "model": model}

                async with session.post(ai_url, json=payload, headers=headers) as response:
                    if response.status == 503:
                        logger.info(f"Сервис спит, попытка {attempt + 1}")
                        await asyncio.sleep(10 * (attempt + 1))
                        continue
                        
                    response.raise_for_status()
                    response_data = await response.json()

                    # Обработка ответа
                    if isinstance(response_data, dict):
                        content = response_data.get("content", "")
                        if any(kw in content for kw in ["{", "}", "[", "]", "="]):
                            return pformat(content, width=80)
                        return content
                    return "⚠️ Некорректный формат ответа"

        except aiohttp.ClientError as e:
            logger.error(f"Ошибка соединения: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                continue
            return "🔌 Сервис запускается..."
            
        except json.JSONDecodeError:
            logger.error("Невалидный JSON")
            return "Ошибка формата ответа"
            
        except Exception as e:
            logger.error(f"Общая ошибка: {e}")
            return "⚙️ Внутренняя ошибка"
    
    return "🔌 Сервис недоступен"