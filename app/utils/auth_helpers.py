import random
import asyncio
from fastapi import HTTPException
from passlib.context import CryptContext
import datetime
from app.celery.tasks import send_email_confirmation_otp_email
from app.core.config import settings
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorDatabase
from .async_jose import encode as async_jwt_encode, decode as async_jwt_decode

from app.db.schemas import UserCreate

pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__memory_cost=512,  # Reduce memory cost to lower CPU load
    argon2__time_cost=2,      # Lower time cost for faster hashing
)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, pwd_context.verify, plain_password, hashed_password)

async def get_password_hash(password: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, pwd_context.hash, password)

async def create_access_token(data: dict, token_version: int):
    to_encode = data
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"token_version": token_version, "exp": expire})
    return await async_jwt_encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)

async def create_refresh_token(data: dict, token_version: int):
    to_encode = data
    to_encode.update({"token_version": token_version})
    return await async_jwt_encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def decode_token(token: str, db: AsyncIOMotorDatabase):
    try:
        # Decode the JWT token
        payload = async_jwt_decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        
        if email:
            user = await db["users"].find_one({"email": email})
            if not user:
                return None, None

            # Compare token version
            if payload.get("token_version") != user.get("token_version", 0):
                return None, None  # Token version mismatch, token is invalid

            return payload, user.get("token_version", 0)
    except JWTError as e:
        print(f"JWTError: {e}")
        return None, None

async def generate_otp():
    datetime_now = datetime.datetime.now(datetime.UTC)
    otp_expires_at = datetime_now + datetime.timedelta(minutes=5)
    return random.randint(100000, 999999), otp_expires_at, datetime_now

async def create_user_dict(user: UserCreate, hashed_password: str) -> dict:
    """Create a dictionary with user fields to be inserted into the database."""
    otp, otp_expires_at, last_otp_sent_at = await generate_otp()
    return {
        "email": user.email,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "registered_at": datetime.datetime.now(datetime.UTC),
        "email_verified": False,
        "total_transcription_duration_seconds": 0,
        "balance": 5.00,
        "token_version": 0,
        "otp": otp,
        "last_otp_sent_at": last_otp_sent_at,
        "otp_expires_at": otp_expires_at,
        "otp_attempts": 0,
        "blocked_until": None,
    }

async def resend_and_save_otp(user_email: str, db: AsyncIOMotorDatabase):
    """Generate and send a new OTP, then update the user in the database."""
    otp, otp_expires_at, last_otp_sent_at = await generate_otp()
    await db["users"].update_one(
        {"email": user_email},
        {
            "$set": {
                "otp": otp,
                "otp_expires_at": otp_expires_at,
                "otp_attempts": 0,
                "last_otp_sent_at": last_otp_sent_at,
            },
            "$unset": {"blocked_until": ""},
        }
    )
    send_email_confirmation_otp_email.delay(user_email, otp)

async def verify_otp_attempts(user: dict, otp: int, db: AsyncIOMotorDatabase, current_time: datetime.datetime):
    """Check if the OTP is valid and handle failed attempts."""
    if user.get("blocked_until") and user["blocked_until"].replace(tzinfo=datetime.timezone.utc) > current_time:
        raise HTTPException(
            status_code=400,
            detail=f"Too many failed attempts. You are blocked until {user['blocked_until']}."
        )

    if user["otp_expires_at"] and user["otp_expires_at"].replace(tzinfo=datetime.timezone.utc) < current_time:
        raise HTTPException(status_code=400, detail="OTP has expired")

    if user["otp_attempts"] >= 5:
        blocked_until = current_time + datetime.timedelta(minutes=1)
        await db["users"].update_one(
            {"email": user["email"]},
            {"$set": {"blocked_until": blocked_until, "otp_attempts": 0}}
        )
        raise HTTPException(status_code=400, detail="Maximum verification attempts exceeded. You are blocked for 1 minute.")
 
    if user["otp"] != otp:
        await db["users"].update_one(
            {"email": user["email"]},
            {"$inc": {"otp_attempts": 1}}
        )
        raise HTTPException(status_code=400, detail="Invalid OTP")

async def change_user_password(
    user_email: str, 
    old_password: str, 
    new_password: str, 
    db: AsyncIOMotorDatabase
):
    """Change the user's password after verifying the old one."""
    user = await db["users"].find_one({"email": user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify the old password
    if not await verify_password(old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Check if the new password is the same as the old one
    if await verify_password(new_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="New password must be different from the old password")
    
    # Hash the new password
    hashed_new_password = await get_password_hash(new_password)

    # Increment the token_version to invalidate old tokens
    token_version = user.get("token_version", 0) + 1

    # Update the user's password and token_version in the database
    await db["users"].update_one(
        {"email": user_email},
        {"$set": {"hashed_password": hashed_new_password, "token_version": token_version}}
    )
