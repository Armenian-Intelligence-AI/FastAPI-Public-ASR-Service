import asyncio
from jose import jwt, JWTError

async def encode(data: dict, secret: str, algorithm: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, jwt.encode, data, secret, algorithm)

async def decode(token: str, secret: str, algorithms: list):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, jwt.decode, token, secret, algorithms)