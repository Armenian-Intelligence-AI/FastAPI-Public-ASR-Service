import motor.motor_asyncio
from app.core.config import settings
import pymongo

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
db = client.stt_fastbank

async def get_db():
    yield db
