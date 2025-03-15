import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

async def generate(text: str, ai_url: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "userInput": text
            }

            async with session.post(
                ai_url,
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
                
                if isinstance(response_data, dict):
                    return response_data.get("content", "Пустой ответ")
                return "Некорректный формат ответа"
                
    except aiohttp.ClientError as e:
        logger.error(f"Connection error: {str(e)}")
        return "Ошибка соединения с сервисом"
    except json.JSONDecodeError:
        logger.error("Invalid JSON response")
        return "Ошибка формата ответа"
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return "Внутренняя ошибка сервиса"