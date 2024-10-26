from typing import Callable
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from app.core.config import settings
from app.db.session import get_db
from app.db.schemas import UserDB
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

async def get_user_from_token(token: str, db: AsyncIOMotorDatabase):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db["users"].find_one({"email": email})
    if user is None:
        raise credentials_exception
    
    return UserDB(**user)

# Dependency to get the current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_db)):
    return await get_user_from_token(token, db)

# Base permission dependency class
class PermissionDependency:
    def __init__(self, permissions: Callable):
        self.permissions = permissions

    def __call__(self, current_user: UserDB = Depends(get_current_user)):
        if not self.permissions(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the necessary permissions",
            )
        return current_user

# Permission check functions
def is_user(user: UserDB):
    return bool(user)

def is_email_verified_user(user: UserDB):
    return user.email_verified

# Create instances of PermissionDependency for each permission
user_permission = PermissionDependency(is_user)
email_verified_user_permission = PermissionDependency(is_email_verified_user)