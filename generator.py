# generator.py
import json
import aiohttp
import logging
import asyncio
from pprint import pformat

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str, model: str) -> str:
    max_retries = 2
    timeout = aiohttp.ClientTimeout(total=90)
    
    async def process_response(response):
        try:
            content = await response.text()
            if response.content_type == 'application/json':
                return json.loads(content).get("content", "")
                
            if 'text/event-stream' in response.content_type:
                events = []
                async for line in response.content:
                    if line.startswith(b'data: '):
                        try:
                            data = json.loads(line[6:].decode())
                            events.append(data.get("content", ""))
                        except:
                            continue
                return "".join(events)
                
            return content
        
        except Exception as e:
            logger.error(f"Ошибка обработки ответа: {e}")
            return ""

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                payload = {"userInput": text, "model": model}
                
                async with session.post(ai_url, json=payload) as response:
                    if response.status >= 500:
                        logger.warning(f"Ошибка сервера: {response.status}")
                        await asyncio.sleep(3 * (attempt + 1))
                        continue
                        
                    response.raise_for_status()
                    return await process_response(response)

        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP ошибка: {e.status} - {e.message}")
            if e.status == 503:
                await asyncio.sleep(10)
                continue
            return f"HTTP ошибка: {e.status}"
            
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Сетевая ошибка: {e}")
            await asyncio.sleep(5)
            continue
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return "Ошибка сервера"
    
    return "Сервис временно недоступен, попробуйте позже"