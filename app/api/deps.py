from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate access token and return current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenPayload(**payload)
        if datetime.utcnow() > token_data.exp:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    user = await db.db.users.find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
        
    return user