import random
import re
from fastapi import HTTPException
from passlib.context import CryptContext
import datetime
from app.celery.tasks import send_email_confirmation_otp_email
from app.core.config import settings
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.schemas import UserCreate

# Ensure the CryptContext is only using bcrypt and no other deprecated schemes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, token_version: int):
    to_encode = data.copy()
    to_encode.update({"token_version": token_version})
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict, token_version: int):
    to_encode = data.copy()
    to_encode.update({"token_version": token_version})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def decode_token(token: str, db: AsyncIOMotorDatabase):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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

def generate_otp():
    return random.randint(100000, 999999)

def create_user_dict(user: UserCreate, hashed_password: str) -> dict:
    """Create a dictionary with user fields to be inserted into the database."""
    return {
        "email": user.email,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "registered_at": datetime.datetime.now(datetime.UTC),
        "email_verified": False,
        "total_transcription_duration_seconds": 0,
        "balance": 5.00,
        "token_version": 0,
        "otp": None,
        "otp_expires_at": None,
        "otp_attempts": 0,
        "blocked_until": None,
    }

async def send_and_save_otp(user_email: str, db: AsyncIOMotorDatabase):
    """Generate and send a new OTP, then update the user in the database."""
    otp = generate_otp()
    otp_expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5)
    await db["users"].update_one(
        {"email": user_email},
        {
            "$set": {
                "otp": otp,
                "otp_expires_at": otp_expires_at,
                "otp_attempts": 0,
                "last_otp_sent_at": datetime.datetime.now(datetime.UTC),
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
    if not verify_password(old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Check if the new password is the same as the old one
    if verify_password(new_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="New password must be different from the old password")
    
    # Hash the new password
    hashed_new_password = get_password_hash(new_password)

    # Increment the token_version to invalidate old tokens
    token_version = user.get("token_version", 0) + 1

    # Update the user's password and token_version in the database
    await db["users"].update_one(
        {"email": user_email},
        {"$set": {"hashed_password": hashed_new_password, "token_version": token_version}}
    )
