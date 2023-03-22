from typing import Generator, Any, Optional
from jose import jwt
from sqlalchemy import or_
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import datetime
from pydantic import ValidationError
from sqlalchemy.orm import Session
import random
from app.models import *
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal
from datetime import datetime,timedelta

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token")

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_by_user(db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(or_(User.email == username,mobile_no == username),User.status != -1).first()


def authenticate(db: Session, *, username: str, password: str) -> Optional[User]:
        user = get_by_user(db, username=username) 
        if user.password == None:
            return 1 # Send Mail to set the password
        if not security.verify_password(password, user.password):
            return None
            
        return user

def is_active(user: User):
    
    return user.status
        
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)) -> User:
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[{"msg":"Could not validate credentials"}],
        )
    user = get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail=[{"msg":"User not found"}])
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)):
    
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get(db: Session, id: Any) -> Optional[User]:
    user = db.query(User.id, User.user_type, User.mobile_no,User.password, User.email, User.status).filter(User.id == id, User.status != -1).first()
    return user

def get_user(db:Session, user_id:Any):
    if user_id:
        user=db.query(models.User).filter(models.User.id == user_id, models.User.status != -1).first()
        if user:
            return user.username
        else:
            return None
    else:
        return None

def get_user_type(user_type: Any):
    if user_type == 1:
        return "Admin"

    elif user_type == 2:
        return "Customer"

    else:
        return ""

def get_tank_type(tank_type: Any):
    if tank_type == 1:
        return "Circle"

    elif tank_type == 2:
        return "Rectangle"

    else:
        return ""


def get_otp():
    otp = ''
    reset = ""
    characters = '0123456789'
    reset_character = 'qwertyuioplkjhgfdsazxcvbnm0123456789QWERTYUIOPLKJHGFDSAZXCVBNM'
    
    otp = random.randint(111111, 999999)
  
    for j in range(0, 20):
        reset += reset_character[random.randint(
            0, len(reset_character) - 1)]

    created_at = datetime.now(settings.tz_NY)
    expire_time = created_at +timedelta(minutes=1)
    expire_at = expire_time.strftime("%Y-%m-%d %H:%M:%S")
    otp_valid_upto = expire_time.strftime("%d-%m-%Y %I:%M %p")

    return [otp, reset , created_at, expire_time, expire_at, otp_valid_upto] 