# generator.py
import json
import aiohttp
import logging
import asyncio

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str, model: str) -> str:
    max_retries = 3
    timeout = aiohttp.ClientTimeout(total=120)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
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
                    
                    if response.status == 503:
                        logger.warning(f"Сервис недоступен, попытка {attempt+1}")
                        await asyncio.sleep(10 * (attempt + 1))
                        continue
                        
                    response.raise_for_status()
                    
                    if response.content_type == 'application/json':
                        data = await response.json()
                        return data.get("content", "Пустой ответ")
                        
                    return await response.text()
                    
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP ошибка {e.status}: {e.message}")
            if attempt < max_retries - 1:
                await asyncio.sleep(10)
                continue
           