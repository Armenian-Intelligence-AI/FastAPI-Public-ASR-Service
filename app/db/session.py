import motor.motor_asyncio
from app.core.config import settings

# Setting maxPoolSize to control the maximum number of connections in the pool
client = motor.motor_asyncio.AsyncIOMotorClient(
    settings.MONGODB_URL,
    maxPoolSize=30,  # Adjust based on load and instance capacity
    minPoolSize=5    # Optional: set a minimum pool size
)
db = client.stt_fastbank

async def get_db():
    yield db