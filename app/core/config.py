import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    PROJECT_NAME: str = "STT_FastBank"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    STT_S3_PAIRS_BUCKET_NAME: str = os.getenv("STT_S3_PAIRS_BUCKET_NAME")
    SAGEMAKER_ENDPOINT_NAME: str = os.getenv("SAGEMAKER_ENDPOINT_NAME")
    STRIPE_SECRET: str = os.getenv("STRIPE_SECRET")
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME")
    REDIS_URL: str = os.getenv("REDIS_URL")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))

settings = Settings()
