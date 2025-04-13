import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str, model: str = "deepseek") -> str:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            payload = {
                "userInput": text,
                "model": model
            }

            full_response = []
            
            async with session.post(
                ai_url,
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    if line.startswith(b'data: '):
                        chunk = line[6:].strip()
                        if chunk == b'[DONE]':
                            break
                        try:
                            data = json.loads(chunk.decode('utf-8'))
                            content = data.get('content', '')
                            full_response.append(content)
                        except json.JSONDecodeError:
                            continue

            return ''.join(full_response)
                
    except aiohttp.ClientError as e:
        logger.error(f"Connection error: {str(e)}")
        return "Ошибка соединения с сервисом"
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return "Внутренняя ошибка сервиса"