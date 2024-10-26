from datetime import datetime, UTC
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search("[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search("[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search("[0-9]", v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserDB(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    email_verified: bool
    balance: float
    token_version: int

    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    username: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# VerifyOTPRequest schema for verifying OTP
class VerifyOTPRequest(BaseModel):
    otp: int = Field(..., description="One-Time Password to verify user's email")
    
    @field_validator('otp')
    def validate_otp(cls, v):
        if len(str(v)) != 6:
            raise ValueError('OTP must be a 6-digit number')
        return v

# Success response model
class SuccessResponse(BaseModel):
    detail: str = Field(..., description="Success message")

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search("[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search("[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search("[0-9]", v):
            raise ValueError('Password must contain at least one digit')
        return v

    
class ResetPasswordRequest(BaseModel):
    new_password: str

    @field_validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search("[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search("[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search("[0-9]", v):
            raise ValueError('Password must contain at least one digit')
        return v
