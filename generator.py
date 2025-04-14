# generator.py
import json
import aiohttp
import logging
import asyncio
from pprint import pformat  # Восстановлен импорт

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str, model: str) -> str:
    max_retries = 3
    timeout = aiohttp.ClientTimeout(total=120)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"  # Явное указание формата ответа
    }
    
    payload = {
        "userInput": text,
        "model": model
    }

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    ai_url, 
                    json=payload, 
                    headers=headers
                ) as response:
                    
                    # Обработка статуса 503
                    if response.status == 503:
                        logger.warning(f"Сервис недоступен, попытка {attempt+1}")
                        await asyncio.sleep(10 * (attempt + 1))
                        continue
                        
                    response.raise_for_status()
                    
                    # Явная проверка Content-Type
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' not in content_type:
                        raise ValueError(f"Неожиданный Content-Type: {content_type}")
                    
                    data = await response.json()
                    
                    # Форматирование ответа с помощью pformat
                    content = data.get("content", "Пустой ответ")
                    return pformat(content, width=80)  # Использование pformat
                    
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {str(e)[:200]}")
            return "Ошибка формата ответа"
            
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP ошибка {e.status}: {e.message}")
            if attempt < max_retries - 1:
                await asyncio.sleep(10)
                continue
            return f"Ошибка API: {e.status}"
            
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Сетевая ошибка: {str(e)[:200]}")
            if attempt < max_retries - 1:
                await asyncio.sleep(15)
                continue
            return "Сетевая ошибка"
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)[:200]}")
            return "Внутренняя ошибка"

    return "Сервис временно недоступен"