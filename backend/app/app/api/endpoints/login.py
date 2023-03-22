import re
from fastapi import APIRouter, Depends, HTTPException, Form
from app.models import *
from app.core.security import *
from app.api import deps
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core import config,security
from app.core.security import settings
from datetime import datetime,timedelta
import hashlib

router = APIRouter()

# Login Access
@router.post("/login/access-token")
def login_access_token(
        db: Session = Depends(deps.get_db), *, username: str = Form(...,description="Mobile number or email"), password: str = Form(...),device_type:int=Form(None,description="1-android,2-ios"),push_id:str=Form(None)):
    
    user_name=username.strip()
    pwd=password.strip()
    
    user = deps.authenticate(db, username=user_name,password=pwd)
    # return user
    if user == 1:
        get_user=db.query(User).filter(or_(User.mobile_no == user_name,User.email == user_name)).first()
        # Send Mail to Guest Check out Client for Password Reset
        included_variable = (str(get_user.id)).encode("utf-8")
        real_hash = hashlib.sha1(included_variable).hexdigest()

        assign_password_url=f"{settings.BASE_DOMAIN}/clinibuy/password_setting/{real_hash}"
        print(assign_password_url)
        raise HTTPException(
            status_code=404,
            detail=[{"msg":"Verify your Account"}])
    elif not user:
        raise HTTPException(
            status_code=404,
            detail=[{"msg":"Invalid username or password"}])

    elif not deps.is_active(user):
       raise HTTPException(
            status_code=404,
            detail=[{"msg":"Inactive user"}])
    
 
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token=security.create_access_token(user.id, expires_delta=access_token_expires)        

    if user.otp_verified_status == 1:
        # check_password
        check_password=verify_password(pwd,user.password)
        if check_password:
            return {"access_token":token,"user_id":user.id,"user_type":user.user_type,"type_name":"Admin" if user.user_type == 1 else "Vendor" if user.user_type == 2 else "Customer","token_type": "bearer","msg":"Login Successfully!","otp_verification_status":user.otp_verified_status}
        else:
            raise HTTPException(
            status_code=404,
            detail=[{"msg":"Invalid username or password"}])
    
    otp, reset, created_at, expire_time, expire_at, otp_valid_upto = deps.get_otp()

    user.otp=1234
    user.otp_created_at=created_at
    user.reset_key=reset
    db.commit()
    return {"reset_key":reset,"otp_verification_status":0 if user.otp_verified_status == 0 else 1}


# # Verify OTP
# @router.post("/verify_otp")
# def verify_otp(db: Session = Depends(deps.get_db)):
   
#     check_otp=db.query(User).filter(User.reset_key == verify_otp.reset_key,User.otp == verify_otp.otp,User.status == 1).first()
  
#     if check_otp:
#         check_otp.otp_verified_status=1
#         check_otp.otp=None
#         check_otp.reset_key=None
#         db.commit()
#         return "Success"
#     else:
#         raise HTTPException(
#         status_code=400,
#         detail=[{"msg":"Invalid OTP"}],
#         )
   

# # Verify OTP
# @router.post("/resend_otp")
# def resend_otp(db: Session = Depends(deps.get_db), *,resend_otp:schemas.UserBase):
#     get_customers=db.query(User).filter(User.email == resend_otp.email,User.mobile_no == resend_otp.mobile_no,User.status == 1).first()
#     if get_customers:
#         otp, reset, created_at, expire_time, expire_at, otp_valid_upto = deps.get_otp()
#         get_customers.otp=1234
#         get_customers.reset_key=reset
#         get_customers.otp_created_at=datetime.now(settings.tz_NY)
#         db.commit()
#         return {"status":1,"reset_key":reset,"msg":"OTP is send Your Mobile Number"}
    
#     else:
#         raise HTTPException(
#         status_code=400,
#         detail=[{"msg":"Invalid User"}],
#         )


# # # Reset Password
# @router.post("/forgot_password")
# async def forgot_password(db: Session = Depends(deps.get_db),*,change_password:schemas.ForgotPassword):
   
#     get_user=db.query(User).filter(User.reset_key ==change_password.reset_key,User.status ==1,User.otp == change_password.otp).first() 
#     if get_user:
#         get_user.otp_verify_code=None
#         get_user.otp_created_at=None
#         get_user.last_password_reset=datetime.now(settings.tz_NY)
#         get_user.resetpassword=0
#         get_user.otp_verified_status=1
#         get_user.email_verified=1
        
#         get_user.password=get_password_hash(change_password.new_password)
#         db.commit() 
#         return "Password changed successfully!"
        

#     else:
#         raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Incorrect OTP!"}]
#         )
    

# # included_variable = (str(users.id)).encode("utf-8")
# #         user_id = hashlib.sha1(included_variable).hexdigest()
        
# #         if franchise_id == user_id:

# # Password Create
# @router.post("/password_setting")
# async def password_setting(db: Session = Depends(deps.get_db),*,change_password:schemas.InitialAssign):
#     check_user=db.query(User).filter(User.user_type == 3).all()
    
#     for users in check_user:
#         included_variable = (str(users.id)).encode("utf-8")
#         user_id = hashlib.sha1(included_variable).hexdigest()
        
#         if change_password.token == user_id:
#             # return change_password.password
            
#             users.password=get_password_hash(change_password.password)
#             users.otp_verified_status=1
#             db.commit() 
#             return "Success"
    
#     else:
#         raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Invalid User"}]
#         )