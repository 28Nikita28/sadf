import aiohttp 
import json

async def generate(text):
    try:
        async with aiohttp.ClientSession() as session:
            data = {"userInput": text}
            full_response = []
            
            async with session.post('https://hdghs.onrender.com/chat', json=data) as resp:
                async for chunk in resp.content:
                    decoded = chunk.decode()
                    if decoded:
                        try:
                            data = json.loads(decoded)
                            full_response.append(data['content'])
                            if data.get('done'):
                                return ''.join(full_response)
                        except json.JSONDecodeError:
                            continue
                            
                return ''.join(full_response)
                
    except aiohttp.ClientConnectorError:
        return 'Не удалось подключиться к серверу ИИ'
    except Exception as e:
        return f'Произошла ошибка: {str(e)}'