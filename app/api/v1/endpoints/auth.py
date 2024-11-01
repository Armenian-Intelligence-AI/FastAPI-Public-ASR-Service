import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.celery.tasks import send_email_confirmation_otp_email, send_password_reset_otp_email
from app.db.schemas import ChangePasswordRequest, ResetPasswordRequest, SuccessResponse, UserCreate, UserDB, RefreshTokenRequest, VerifyOTPRequest
from app.db.session import get_db
from app.api.deps import user_permission, email_verified_user_permission
from app.utils.auth_helpers import change_user_password, create_user_dict, get_password_hash, resend_and_save_otp, verify_otp_attempts, verify_password, create_access_token, create_refresh_token, decode_token, generate_otp
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

@router.post("/register", response_model=UserDB)
async def register(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if not user.email or not user.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user_in_db = await db["users"].find_one({"email": user.email})
    if user_in_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = await get_password_hash(user.password)
    user_dict = await create_user_dict(user, hashed_password)

    await db["users"].insert_one(user_dict)
    send_email_confirmation_otp_email.delay(user.email, user_dict['otp'])
    return UserDB(**user_dict)

@router.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db["users"].find_one({"email": form_data.username})
    if not user or not await verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(data={"sub": user["email"]}, token_version=user['token_version'])
    refresh_token = await create_refresh_token(data={"sub": user["email"]}, token_version=user['token_version'])
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/test-hash")
async def test_hash(password: str):
    try:
        # Hash the password
        hashed_password = await get_password_hash(password)
        
        # Verify the password against the hash
        is_verified = await verify_password(password, hashed_password)
        
        return {
            "hashed_password": hashed_password,
            "is_verified": is_verified
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/test-token")
async def test_token():
    # Sample data to encode
    data = {"sub": "test@example.com"}
    token_version = 1

    # Create access and refresh tokens
    access_token = await create_access_token(data=data, token_version=token_version)
    refresh_token = await create_refresh_token(data=data, token_version=token_version)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.post("/token/refresh", response_model=dict)
async def refresh_access_token(refresh_token_request: RefreshTokenRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    refresh_token = refresh_token_request.refresh_token
    payload, token_version = await decode_token(refresh_token, db)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = await create_access_token(data={"sub": email}, token_version=token_version)
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/resend-otp", response_model=SuccessResponse)
async def resend_otp(
    current_user: UserDB = Depends(user_permission),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db["users"].find_one({"email": current_user.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["email_verified"]:
        raise HTTPException(status_code=400, detail="Email is already verified")

    # Check if the OTP was recently sent (within the last 60 seconds)
    last_otp_sent_at = user.get("last_otp_sent_at").replace(tzinfo=datetime.timezone.utc)
    current_time = datetime.datetime.now(datetime.UTC)
    if last_otp_sent_at and (current_time - last_otp_sent_at).total_seconds() < 60:
        raise HTTPException(status_code=400, detail="You can only request a new OTP after 1 minute.")

    await resend_and_save_otp(current_user.email, db)
    return {"detail": "OTP has been resent"}

@router.post("/verify-otp")
async def verify_otp(
    request: VerifyOTPRequest,
    current_user: UserDB = Depends(user_permission),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    otp = request.otp
    user = await db["users"].find_one({"email": current_user.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["email_verified"]:
        raise HTTPException(status_code=400, detail="Email is already verified")

    # Ensure UTC-aware datetime
    current_time = datetime.datetime.now(tz=datetime.timezone.utc)

    # Verify OTP attempts and expiration
    await verify_otp_attempts(user, otp, db, current_time)

    # OTP is valid, mark the email as verified
    await db["users"].update_one(
        {"email": current_user.email},
        {
            "$set": {
                "email_verified": True,
            },
            "$unset": {
                "otp": "",
                "otp_expires_at": "",
                "otp_attempts": "",
                "blocked_until": "",
                "last_otp_sent_at": ""
            }
        }
    )

    return {"detail": "Email successfully verified"}

@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserDB = Depends(user_permission),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Call the helper function to change the password
    await change_user_password(
        user_email=current_user.email,
        old_password=request.old_password,
        new_password=request.new_password,
        db=db
    )
    return {"detail": "Password changed successfully"}

@router.post("/request-password-reset", response_model=SuccessResponse)
async def request_password_reset(email: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if an OTP was recently sent (within the last 5 minutes)
    last_otp_sent_at = user.get("last_reset_password_otp_sent_at")
    current_time = datetime.datetime.now(datetime.UTC)
    
    if last_otp_sent_at:
        last_otp_sent_at = last_otp_sent_at.replace(tzinfo=datetime.timezone.utc)  # Ensure correct timezone
        if (current_time - last_otp_sent_at).total_seconds() < 300:
            raise HTTPException(
                status_code=400,
                detail="You can only request a new OTP every 5 minutes."
            )

    # Generate a new OTP for password reset
    otp = await generate_otp()
    otp_expires_at = current_time + datetime.timedelta(minutes=5)

    # Update the user record with the OTP, expiration time, and when the OTP was last sent
    await db["users"].update_one(
        {"email": email},
        {
            "$set": {
                "reset_password_otp": otp,
                "reset_password_otp_expires_at": otp_expires_at,
                "reset_password_attempts": 0,
                "last_reset_password_otp_sent_at": current_time
            }
        }
    )

    # Send the OTP to the user's email
    send_password_reset_otp_email.delay(email, otp)

    return {"detail": "Password reset OTP has been sent to your email"}

@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    request: ResetPasswordRequest,
    otp: int,
    email: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Find the user by email
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the reset password OTP is valid
    current_time = datetime.datetime.now(datetime.UTC)
    if user.get("reset_password_otp_expires_at") and  user.get("reset_password_otp_expires_at").replace(tzinfo=datetime.timezone.utc) < current_time:
        raise HTTPException(status_code=400, detail="OTP has expired")

    if user.get("reset_password_attempts", 0) >= 5:
        raise HTTPException(status_code=400, detail="Too many failed attempts. You are blocked.")

    if user.get("reset_password_otp") != otp:
        # Increment the failed attempts
        await db["users"].update_one(
            {"email": email},
            {"$inc": {"reset_password_attempts": 1}}
        )
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Hash the new password
    hashed_new_password = await get_password_hash(request.new_password)

    # Increment the token_version to invalidate old tokens
    token_version = user.get("token_version", 0) + 1

    # Update the user's password and reset the password-related fields
    await db["users"].update_one(
        {"email": email},
        {
            "$set": {"hashed_password": hashed_new_password, "token_version": token_version},
            "$unset": {
                "reset_password_otp": "",
                "reset_password_otp_expires_at": "",
                "reset_password_attempts": "",
                "last_reset_password_otp_sent_at": ""
            }
        }
    )

    return {"detail": "Password has been reset successfully"}

@router.get("/me", response_model=UserDB)
async def read_users_me(current_user: UserDB = Depends(user_permission)):
    return current_user
