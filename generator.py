# generator.py
import json
import aiohttp
import logging
import asyncio
from pprint import pformat

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str, model: str) -> str:
    max_retries = 3
    timeout = aiohttp.ClientTimeout(total=120)
    
    async def process_response(response):
        try:
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                data = await response.json()
                return data.get("content", "")
                
            if 'text/event-stream' in content_type:
                full_response = []
                async for line in response.content:
                    if line.startswith(b'data: '):
                        try:
                            chunk = json.loads(line[6:].decode())
                            full_response.append(chunk.get("content", ""))
                        except json.JSONDecodeError:
                            continue
                return "".join(full_response)
                
            return await response.text()
            
        except Exception as e:
            logger.error(f"Ошибка обработки ответа: {str(e)[:200]}")
            return ""

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                payload = {
                    "userInput": text,
                    "model": model,
                    "stream": True
                }
                
                async with session.post(ai_url, json=payload) as response:
                    if response.status >= 500:
                        logger.warning(f"Ошибка сервера: {response.status}")
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                        
                    response.raise_for_status()
                    return await process_response(response)

        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP ошибка {e.status}: {e.message}")
            if e.status == 503:
                await asyncio.sleep(15)
                continue
            return f"HTTP ошибка: {e.status}"
            
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Сетевая ошибка: {str(e)[:200]}")
            await asyncio.sleep(10)
            continue
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)[:200]}")
            return "Ошибка сервера"
    
    return "Сервис временно недоступен, попробуйте позже"