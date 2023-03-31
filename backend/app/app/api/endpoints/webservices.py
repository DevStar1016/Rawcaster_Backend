from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from typing import List
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from datetime import datetime,date
from sqlalchemy import func,case
import re
import base64
import json

router = APIRouter() 


# For Testing
# @router.post("/test")
# async def test(db:Session=Depends(deps.get_db),auth_code:str=Form(...)):
#     auth_code=auth_code
#     auth_text="surya@gmail.com"
#     s=checkAuthCode(auth_code,auth_text)
#     return s
                         

# 1 Signup User
@router.post("/signup")
async def signup(db:Session=Depends(deps.get_db),signup_type:int=Form(...,description="1-Email,2-Phone Number",ge=1,le=2),first_name:str=Form(...,max_length=100),
                    last_name:str=Form(None,max_length=100),display_name:str=Form(None,max_length=100),gender:int=Form(None,ge=1,le=2,description="1-male,2-female"),
                    dob:date=Form(None),email_id:str=Form(None,max_length=100),country_code:int=Form(None),country_id:int=Form(None),
                    mobile_no:int=Form(None),password:str=Form(...),geo_location:str=Form(None),
                    latitude:int=Form(None),longitude:int=Form(None),ref_id:str=Form(None),auth_code:str=Form(...,description="SALT + email_id"),
                    device_id:str=Form(None),push_id:str=Form(None),device_type:int=Form(None),
                    voip_token:str=Form(None),app_type:int=Form(None,description="1-Android,2-IOS",ge=1,le=2),signup_social_ref_id:str=Form(None),
                    login_from:str=Form(None)):

    
    if auth_code.strip() == "":    
        return {"status":0,"msg":"Auth Code is missing"}
    
    elif first_name == "":
        return {"status":0,"msg":"Please provide your first name"}
    
    elif re.search("/[^A-Za-z0-9]/", first_name):
        return {"status":0,"msg":"Please provide valid name"}
    
    elif email_id and email_id.strip() == "":
        return {"status":0,"msg":"Please provide your valid email or phone number"}
    
    elif password.strip() == "":
        return {"status":0,"msg":"Password is missing"}
    
    else:
        auth_text=email_id.strip() if email_id else None
        # auth_text=email_id.strip() if signup_type == 1 else mobile_no
        if checkAuthCode(auth_code,auth_text) == False:
            return {"status":0,"msg":"Authentication failed!"}
        
        else:
            email_id=email_id.strip()
            check_email_or_mobile= EmailorMobileNoValidation(email_id)
            
            if check_email_or_mobile['status'] == 1:
                if check_email_or_mobile['type'] == signup_type:
                    if signup_type == 1:
                        email_id=check_email_or_mobile['email']
                        mobile_no=None
                    elif signup_type == 2:
                        email_id=None
                        mobile_no=check_email_or_mobile['mobile']
                else:
                    if signup_type == 1:
                        return {"status":0,"msg":"Email address is not valid"}
                        
                    elif signup_type == 2:
                        return {"status":0,"msg":"Phone number is not valid"}
                     
            else:
                if signup_type == 1:
                    
                    return {"status":0,"msg":"Email ID is not valid"}
                if signup_type == 2:
                    
                    return {"status":0,"msg":"Phone number is not valid"}
                
            check_email_id = 0
            check_phone = 0
            if email_id != "" and email_id != None:
                check_email_id=db.query(User).filter(User.email_id == email_id,User.status != 4).count()
            
            if mobile_no != '' and mobile_no != None:
                
                check_phone=db.query(User).filter(User.mobile_no == mobile_no,User.status != 4).count()
            
            check_user=db.query(User).filter(User.email_id == email_id,or_(User.is_mobile_no_verified == 0,User.is_email_id_verified == 0)).first()
            if check_user:
                
                send_otp=SendOtp(db,check_user.id,signup_type)
                
                return {"status" : 2,"otp_ref_id":send_otp, "msg" : "Verification Pending, Redirect to OTP Verify Page","first_time":0}
            
            if check_email_id > 0:
                
                return {"status" : 2, "msg" : "You are already registered with this email address. Please login"}
            
            if check_phone > 0:
               
                return {"status" : 2, "msg" : "You are already registered with this phone number. Please login"}
            
            else:
                userIP = get_ip()
                location="India" if not geo_location else geo_location
                
                if geo_location == None or geo_location == "" or len(geo_location)< 4 :
                    location_details=FindLocationbyIP(userIP)
                    
                    if location_details['status'] and location_details['status'] == 1:
                        location=location_details['country'] if location_details['country'] else "India"
                       
                        latitude=location_details['latitude']
                        longitude=location_details['longitude']
                
                if mobile_no != "" and mobile_no != None:
                    
                    mobile_check=CheckMobileNumber(db,mobile_no,location)
                    if not mobile_check:
                       
                        return {"status":0, "msg":"Unable to signup with mobile number"}
                    else:
                        if mobile_check['status'] and mobile_check['status'] == 1:
                            country_code=mobile_check['country_code']
                            country_id=mobile_check['country_id']
                            mobile_no=mobile_check['mobile_no']
                        else:
                            return mobile_check
                        
                result = hashlib.sha1(password.encode())
                hashed_password = result.hexdigest()
                add_user=User(email_id=email_id,is_email_id_verified=0,password=hashed_password,first_name=first_name,last_name=last_name,
                                display_name=display_name,gender=gender,dob=dob,country_code=country_code,mobile_no=mobile_no,
                                is_mobile_no_verified=0,country_id=country_id,user_code=None,signup_type=1,
                                signup_social_ref_id=signup_social_ref_id,geo_location=geo_location,latitude=latitude,
                                longitude=longitude,created_at=datetime.now(),status=0)
                db.add(add_user)
                db.commit()
                db.refresh(add_user)
                if add_user:
                    user_ref_id=GenerateUserRegID(add_user.id)
                    
                    # update ref id
                    get_user=db.query(User).filter(User.id == add_user.id).update({"user_ref_id":user_ref_id})
                    db.commit()
                    
                    # Set Default user settings
                    user_settings_model=UserSettings(user_id=add_user.id,online_status=1,friend_request='000',nuggets='000',events='000',status=1)
                    db.add(user_settings_model)
                    db.commit()
                    db.refresh(user_settings_model)
                    
                    # Set Default Friend Group
                    friends_group=FriendGroups(group_name='My Fans',group_icon='test',created_by=add_user.id,created_at=datetime.now(),status=1,chat_enabled=0)
                    db.add(friends_group)
                    db.commit()
                    db.refresh(friends_group)
                    
                    referred_id=0
                    # Add Friend Automatically From Referral
                    
                    if ref_id != None:
                        friend_ref_code=base64.b64decode(ref_id)
                        referrer_ref_id=friend_ref_code.split('//')
                        if len(referrer_ref_id) == 2:
                            referred_user=db.query(User).filter(User.user_ref_id == referrer_ref_id[0],User.status == 1).first()
                            if referred_user:
                                referred_id=referred_user.id
                                # update referrer id
                                update_referrer=db.query(User).filter(User.id == add_user.id).update({"referrer_id":referred_user.id,"invited_date":referrer_ref_id[1]})
                                db.commit()
                                
                                ref_friend=MyFriends(sender_id=referred_user.id,receiver_id=add_user.id,request_date=datetime.now(),request_status=1,status_date=None,status=1)
                                db.add(ref_friend)
                                db.commit()
                                
                                get_friend_group=db.query(FriendGroups).filter(FriendGroups.group_name == "My Fans",FriendGroups.created_by == referred_user.id ).first()
                                
                                if get_friend_group:
                                    add_follow_user=FollowUser(follower_userid=add_user.id,following_userid=referred_user.id,created_date=datetime.now())
                                    db.add(add_follow_user)
                                    db.commit()
                                    
                                    # Check FriendGroupMembers
                                    friend_group_member=db.query(FriendGroupMembers).filter(FriendGroupMembers.group_id == get_friend_group.id,FriendGroupMembers.user_id == referred_user.id).all()
                                    
                                    if not friend_group_member:
                                        add_friend_group_member=FriendGroupMembers(group_id=get_friend_group.id,user_id=add_user.id,added_date=datetime.now(),added_by=referred_user.id,is_admin=0,disable_notification=1,status=1)
                                        db.add(add_friend_group_member)
                                        db.commit()
                                        
                    # Referral Auto Add Friend Ends  
                    type=2
                    rawcaster_support_id= GetRawcasterUserID(db,type)  
                    
                    if rawcaster_support_id > 0 and referred_id != rawcaster_support_id :
                        add_my_friends=MyFriends(sender_id=rawcaster_support_id,receiver_id=add_user.id,request_date=datetime.now(),request_status=1,status_date=None,status=1)
                        db.add(add_my_friends)
                        db.commit()
                    
                    result = hashlib.sha1(password.encode())
                    password = result.hexdigest()
                    
                    if email_id == "" or email_id == None:
                        email_id=mobile_no
                        
                    # Send OTP for Email or MObile number Verification
                    
                    send_otp=SendOtp(db,add_user.id,signup_type)
                    
                    if send_otp:
                        otp_ref_id=send_otp
                    else:
                        return {"status":0,"msg":"Failed to send OTP"}
                        
                    
                    # reply=logins(db,email_id,password,device_type,device_id,push_id,login_from,voip_token,app_type)
                    
                    return {"status":1, "msg": "Success", "email": email_id,"otp_ref_id":otp_ref_id,"user_id":add_user.id,"acc_verify_status": 0,"first_time":1}  # First Time (1 - New to rawcaster, 0 - existing user)
                    
                else:
                    msg=await getModelError()  # Pending
                    
                    return {"status":0,"msg":msg}
                        
                                       

# 2 - Signup Verification by OTP
@router.post("/signupverify")
async def signupverify(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),otp_ref_id:str=Form(...,description="From service no. 1"),otp:int=Form(...),otp_flag:str=Form(None)):
    if auth_code.strip() == "":
        return {"status":0,"msg":"Auth Code is missing"}
    elif otp_ref_id.strip() == "":
        return {"status":0,"msg":"Reference id is missing"}
    else:
        otp_ref_id=otp_ref_id.strip()
        otp_flag='email'
        otp=otp
        auth_code=auth_code.strip()
        
        auth_text=otp_ref_id
        if checkAuthCode(auth_code,auth_text) == False:
            return {"status":0,"msg":"Authentication failed!"}
    
        else:
            
            get_otp_log=db.query(OtpLog).filter(OtpLog.id == otp_ref_id,OtpLog.otp == otp,OtpLog.status == 1).first()
            if not get_otp_log:
                return {"status":0,"msg":"OTP is invalid"}
            else:
                get_otp_log.status = 0
                db.commit()
                user_update=0
                if otp_flag =="sms":
                    update_user=db.query(User).filter(User.id == get_otp_log.user_id).update({"is_mobile_no_verified":1,"status":1})
                    user_update=get_otp_log.user_id
                    db.commit()
                else:
                    update_user=db.query(User).filter(User.id == get_otp_log.user_id).update({"is_email_id_verified":1,"status":1})
                    db.commit()
                    
                    user_update=get_otp_log.user_id
                if update_user:
                    get_user=db.query(User).filter(User.id == get_otp_log.user_id).first()
                    if get_user:
                        if get_user.referrer_id != None or get_user.referrer_id != "":
                            change_referral_date=ChangeReferralExpiryDate(db,get_user.referrer_id)
                            
                        if get_user.is_email_id_verified == 1:
                            to_mail=get_user.email_id
                            subject="Welcome to Rawcaster"
                            message=f"Done"
                            # mail_send=await send_email(to_mail,subject,message)
                            
                            # return {"status":1,"msg":"Verified Successfully."}
                            
                    return {"status" :1, "msg" :"Your account has been verified successfully."}
                        
                else:
                    return {"status" :0, "msg" :"Account verification failed. Please try again"}
    
    

# 3 - Resend OTP

@router.post("/resendotp")
async def resendotp(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),otp_ref_id:str=Form(None),token:str=Form(None),otp_flag:str=Form(None)):
    if otp_flag and otp_flag.strip() == "" or otp_flag== None:
        otp_flag='email'
    
    auth_text = otp_ref_id if otp_ref_id is not None else "Rawcaster"
    if checkAuthCode(auth_code,auth_text) == False:
        return {"status":0,"msg": "Authentication failed!"}
    else:
    
        if otp_ref_id == None:
            if not token and token.strip() == "":
                return {"status":0,"msg":"Sorry! your login session expired. please login again."}
            
            else:
                login_user_id=0
                access_token=checkToken(db,token)
                
                if access_token == False:
                    return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
                else:
                    get_token_details=db.query(ApiTokens).filter(ApiTokens.token ==access_token).all()
                    for token in get_token_details:
                        login_user_id=token.user_id
                
                send_otp=SendOtp(db,login_user_id,signup_type=None)
                otp_ref_id=None
                if send_otp:
                    otp_ref_id=send_otp
                
                return {"status":1,"otp_ref_id":otp_ref_id,"msg":"Success"}
        else:  
            get_otp_log=db.query(OtpLog).filter(OtpLog.id == otp_ref_id,OtpLog.status == 0).first()
            
            if not get_otp_log:
                return {"status":0,"msg":"Invalid request!"}
            else:
                
                otp_time=datetime.now()
                
                get_otp_log.created_date=otp_time
                get_otp_log.status=1
                db.commit()
                
                otp=get_otp_log.otp
                
                if get_otp_log.otp_type == 1:  # if signup
                    mail_sub="Rawcaster - Account Verification"
                    mail_msg="Your OTP for Rawcaster account verification is : "
                    
                elif  get_otp_log.otp_type == 3 : # if forgot password
                    mail_sub="Rawcaster - Password Reset"
                    mail_msg="Your OTP for Rawcaster account password reset is"
                
                if otp_flag == "sms":
                    to=get_otp_log.user.mobile_no
                    print("SMS")
                else:
                    to=get_otp_log.user.email_id
                    
                    print("MAIL")
                
                remaining_seconds=0
                target_time= datetime.timestamp(otp_time) + 300
                current_time=datetime.now().timestamp()
                
                if current_time < target_time:
                    remaining_seconds=int(target_time - current_time)

                reply_msg=f'Please enter the One Time Password (OTP) sent to {to}'
                return {"status":1,"msg":reply_msg,"email":to,"otp_ref_id":otp_ref_id,"remaining_seconds":remaining_seconds}
                 
          

# # 3 - Resend OTP  (PHP Code)

# @router.post("/resendotp")
# async def resendotp(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),otp_ref_id:str=Form(None),token:str=Form(...),otp_flag:str=Form(None)):
#     if otp_flag and otp_flag.strip() == "" or otp_flag== None:
#         otp_flag='email'
    
#     auth_text = otp_ref_id if otp_ref_id is not None else "Rawcaster"
#     if checkAuthCode(auth_code,auth_text) == False:
#         return {"status":0,"msg": "Authentication failed!"}
#     else:
    
#         if otp_ref_id == None:
#             if token.strip():
#                 return {"status":0,"msg":"Sorry! your login session expired. please login again."}
#             else:
#                 login_user_id=0
#                 access_token=checkToken(token)
                
#                 if access_token == False:
#                     return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
#                 else:
#                     get_token_details=db.query(ApiTokens).filter(ApiTokens.token ==access_token).all()
#                     for token in get_token_details:
#                         login_user_id=token.user_id
                
#                 otp=generateOTP()
#                 otp_time=datetime.now()
#                 otp_model=OtpLog(user_id=login_user_id,otp=otp,otp_type=1,created_at=otp_time,status=1)
#                 db.add(otp_model)
#                 db.commit()
                
#                 if otp_model:
#                     otp_ref_id=otp_model.id
#         else:  
#             get_otp_log=db.query(OtpLog).filter(OtpLog.id == otp_ref_id,OtpLog.status == 1).first()
            
#             if not get_otp_log:
#                 return {"status":0,"msg":"Invalid request!"}
#             else:
                
#                 otp_time=datetime.now()
#                 otp_model.created_at=otp_time
#                 db.commit()
                
#                 otp=get_otp_log.otp
                
#                 if otp_model.otp_type == 1:  # if signup
#                     mail_sub="Rawcaster - Account Verification"
#                     mail_msg="Your OTP for Rawcaster account verification is : "
                    
#                 elif  otp_model.otp_type == 3 : # if forgot password
#                     mail_sub="Rawcaster - Password Reset"
#                     mail_msg="Your OTP for Rawcaster account password reset is"
                
#                 if otp_flag == "sms":
#                     to=otp_model.user.mobile_no
#                     print("SMS")
#                 else:
#                     to=otp_model.user.email_id
                    
#                     print("MAIL")
                
#                 remaining_seconds=0
#                 target_time= int(round(otp_time.timestamp())) + 300
#                 current_time=datetime.now()
#                 if current_time < target_time:
#                     remaining_seconds=target_time - current_time
                
#                 reply_msg=f'Please enter the One Time Password (OTP) sent to {to}'
#                 return {"status":1,"msg":reply_msg,"email":to,"otp_ref_id":otp_ref_id,"remaining_seconds":remaining_seconds}
            
#             # else:
#             #     return {"status" :0, "msg" :"Failed to resend otp, please try again"}
                    
                        


# 4 - Login
@router.post("/login")
async def login(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + username"),username:str=Form(...,description="Email ID"),
                    password:str=Form(...),device_id:str=Form(None),push_id:str=Form(None),device_type:int=Form(None,description="1-> Android,  2-> IOS, 3->Web"),voip_token:str=Form(None),
                    app_type:int=Form(None,description="1-> Android, 2-> IOS",ge=1,le=2),login_from:str=Form(None)):
    
    auth_text=username.strip()
    if checkAuthCode(auth_code.strip(),auth_text) == False:
        return {"status":0,"msg":"Authentication failed!"}
    else:
        if username.strip() != "" and password.strip() != "":
            password = hashlib.sha1(password.encode()).hexdigest()
            generate_access_token=logins(db,username,password,device_type,device_id,push_id,login_from,voip_token,app_type)
            return generate_access_token
        else:
            return {"status":0,"msg":"Please enter a valid username and password"}
            



# 5 - Logout
@router.post("/logout")
async def logout(db:Session=Depends(deps.get_db),token:str=Form(...)):
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry your access token missing!"}
    else:
        access_token=checkToken(db,token)
        if access_token == False:
            return {"status":-1,"msg":"Sorry your access token invalid!"}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token.strip()).first()
            if get_token_details:
                if get_token_details.device_type == 2:
                    user_id=get_token_details.user_id
                    # Update Friend Chat
                    update_friend_sender_chat=db.query(FriendsChat).filter(FriendsChat.sender_id == user_id).update({"sender_delete":1,"sender_deleted_datetime":datetime.now()})
                    update_friend_receiver_chat=db.query(FriendsChat).filter(FriendsChat.receiver_id == user_id).update({"receiver_delete":1,"receiver_deleted_datetime":datetime.now()})
                    db.commit()
                
                # Delete Token
                delete_token=db.query(ApiTokens).filter(ApiTokens.token == access_token.strip()).delete()
                db.commit()
                if delete_token:
                    return {"status":1,"msg":"Success"}
                
                else:
                    return {"status":0,"msg":"Failed to Logout"}
                    
            else:
                return {"status":0,"msg":"Success"}
                      
    



# 6 - Forgot Password
@router.post("/forgotpassword")
async def forgotpassword(db:Session=Depends(deps.get_db),username:str=Form(...,description="Email ID / Mobile Number"),auth_code:str=Form(...,description="SALT + username")):
    if auth_code.strip() == "":
        return {"status":0,"msg":"Auth Code is missing"}
    elif username.strip() == "":
        return {"status":0,"msg":"Email id is missing"}
    else:
        username=username.strip()
        auth_code=auth_code.strip()
        
        auth_text=username
        if checkAuthCode(auth_code,auth_text) == False:
            return {"status":0,"msg":"Authentication failed!"}
        else:
            get_user=db.query(User).filter(or_(User.email_id == username,User.mobile_no == username)).first()
            if not get_user:
                return {"status":0,"msg":"If the email/phone number is registered, you will receive an email/SMS in your inbox shortly with further details on how to reset your password."}
            
            elif get_user.status == 4:  # Account deleted
                return {"status":0,"msg":"Your account has been removed"}
                
            elif get_user.status == 3:  # Admin Blocked user!
                return {"status":0,"msg":"Your account is currently blocked!"}
            
            elif get_user.status == 2:  # Admin Blocked user!
                return {"status":0,"msg":"Your account is currently suspended!"}
            
            else: # account not verified or account active
                otp=generateOTP()
                otp_time=datetime.now()
                otp_ref_id=''
                remaining_seconds=0
                
                get_otp=db.query(OtpLog).filter_by(user_id = get_user.id,otp_type=3).order_by(OtpLog.id.desc()).first()
                if get_otp:
                    update_otp_log=db.query(OtpLog).filter_by(id =get_otp.id).update({"otp":otp,"created_date":otp_time,"status":1})
                    db.commit()
                    otp_ref_id=get_otp.id
                else:
                    add_otp_log=OtpLog(user_id = get_user.id,otp=otp,otp_type=3,created_date=otp_time,status=1)
                    db.add(add_otp_log)
                    db.commit()
                    
                    if add_otp_log:
                        otp_ref_id=add_otp_log.id
                
                target_time=otp_time.timestamp() + 300
                if otp_time.timestamp() < target_time:
                    remaining_seconds = target_time - otp_time.timestamp()
                msg=""
                if username.isnumeric():
                    to=get_user.mobile_no
                    sms=f"{otp} is your OTP for Rawcaster. PLEASE DO NOT SHARE THE OTP WITH ANYONE."
                    msg="A one time passcode (OTP) has been sent to the phone number you provided"
                    # SMS Pending
                
                elif check_mail(username) == True:
                    to=get_user.email_id
                    subject="Rawcaster - Reset Password"
                    
                    msg="A one time passcode (OTP) has been sent to the email address you provided"

                return {"status":1,"msg":msg,"otp_ref_id":otp_ref_id,"remaining_seconds":remaining_seconds}



# 7 - Verify OTP and Reset Password
@router.post("/verifyotpandresetpassword")
async def verifyotpandresetpassword(db:Session=Depends(deps.get_db),otp_ref_id:int=Form(...),otp:int=Form(...),
                                    new_password:str=Form(...,min_length=5),confirm_password:str=Form(...,min_length=5),device_id:str=Form(None),
                                    push_id:str=Form(None,description="FCM  or APNS"),device_type:int=Form(None),
                                    auth_code:str=Form(...,description="SALT + otp_ref_id")):
    
    if auth_code.strip() == "":
        return {"status":0,"msg":"Auth Code is missing"}
    
    elif new_password.strip() == "":
        return {"status":0,"msg":"New Password is missing"}
    
    elif new_password.strip() == "" or confirm_password.strip() == "":
        return {"status":0,"msg":"Confirm Password is missing"}

    elif new_password.strip() != confirm_password.strip():
        return {"status":0,"msg":"New & Confirm Password must be same"}
    
    else:
        
        auth_code=auth_code.strip()
        auth_text=otp_ref_id
        
        if checkAuthCode(auth_code,auth_text) == False:
            return {"status":0,"msg":"Authentication failed!"}
        else:
            get_otp_log=db.query(OtpLog).filter(OtpLog.id == otp_ref_id,OtpLog.otp == otp,OtpLog.status == 1).first()
            
            if not get_otp_log:
                return {"status":0,"msg":"OTP is invalid"}
                
            else:
                update=False
                new_password=hashlib.sha1(new_password.encode()).hexdigest()
                if (get_otp_log.user.password and new_password) == get_otp_log.user.password:
                    update=True
                else:
                    get_otp_log.user.password = new_password  # Update Password
                    db.commit()
                
                if update:
                    get_otp_log.status = 0
                    db.commit()
                    return {"status":1,"msg":"Your password has been updated successfully"}
                else:
                    return {"status":0,"msg":"Password update failed. Please try again"}
                    
                    
                

# 8 - Change Password
@router.post("/changepassword")
async def changepassword(db:Session=Depends(deps.get_db),token:str=Form(...),old_password:str=Form(...),new_password:str=Form(...),confirm_password:str=Form(...),auth_code:str=Form(...,description="SALT + token")):

    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        
    elif auth_code.strip() == "":
        return {"status" : -1, "msg" :"Auth Code is missing"}

    else:
        auth_text=token.strip()
        access_token=checkToken(db,auth_text)
        
        if checkAuthCode(auth_code,auth_text) == False:
            return {"status" : 0, "msg" :"Authentication failed!"}
        else:
            if access_token == False:
                return {"status" : -1, "msg" :"Sorry! your login session expired. please login again."}
            else:
                get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
                
                login_user_id=get_token_details.user_id if get_token_details else None
                
                if old_password.strip() == "":
                    return {"status" : 0, "msg" :"Current password can not be empty"}
                    
                if new_password.strip() == "":
                    return {"status" : 0, "msg" :"New password can not be empty"}
                
                if confirm_password.strip() == "":
                    return {"status" : 0, "msg" :"Confirm password can not be empty"}
                
                if new_password != confirm_password:
                    return {"status" : 0, "msg" :"New password and Confirm password should be same"}
                
                else:
                    get_user=db.query(User).filter(User.id == login_user_id).first()
                    old_pwd=hashlib.sha1(old_password.encode()).hexdigest()
                    
                    if get_user.password != old_pwd:
                        return {"status" : 0, "msg" :"Current password is wrong"}
                        
                    else:
                        # Update Password
                        new_pwd=hashlib.sha1(new_password.encode()).hexdigest()
                        update_pwd=db.query(User).filter(User.id == login_user_id).update({"password":new_pwd})
                        db.commit()
                        if update_pwd:
                            return {"status" : 1, "msg" :"Successfully updated new password"}
                        else:
                            
                            return {"status" : 0, "msg" :"Failed to update new password. try again"}
                    
                
                
# 9 - Get country list
@router.post("/getcountylist")
async def getcountylist(db:Session=Depends(deps.get_db)):
    get_countries=db.query(Country).filter_by(status = 1).order_by(Country.name.asc()).all()
    if get_countries:
        country_list=[]
        for place in get_countries:
            country_list.append({"id":place.id,
                                 "name":place.name if place.name else "",
                                 "phone_code":place.country_code if place.country_code else "",
                                 "image":place.img if place.img else ""
                                })
        return {"status":1,"msg":"Success","country_list":country_list}
    else:
        return {"status" : 0, "msg" :"No result found!"}
        
        




# 10 - Contact us
@router.post("/contactus")
async def contactus(db:Session=Depends(deps.get_db),name:str=Form(...),email_id:str=Form(...),subject:str=Form(...),message:str=Form(...),
                    auth_code:str=Form(...,description="SALT + email_id")):
    
    if auth_code.strip() == "":
        return {"status" : 0, "msg" :"Auth Code is missing"}
    
    elif name.strip() == "":
        return {"status" : 0, "msg" :"Name is missing"}
    
    elif email_id.strip() == "":
        return {"status" : 0, "msg" :"Email id is missing"}

    elif subject.strip() == "":
        return {"status" : 0, "msg" :"Subject is missing"}
    
    elif message.strip() == "":
        return {"status" : 0, "msg" :"Message is missing"}
        
    else:
        auth_text=email_id.strip()
        if checkAuthCode(auth_code,auth_text) == False:
            
            return {"status" : 0, "msg" :"Authentication failed!"}
    
        else:
            to_mail='support@rawcaster.com'
            subject=f'New enquiry received from {name}'
            message=f'<table width="600" border="0" align="center" cellpadding="10" cellspacing="0" style="border: 1px solid #e8e8e8;"> <tr><th> Name : </th><td> {name} </td></tr> <tr><th> Email id : </th><td> {email_id} </td></tr> <tr><th> Subject : </th><td> {subject} </td></tr> <tr><th> Message : </th><td> {message} </td></tr> </table>'
            
            send_mail=await send_email(to_mail,subject,message)
            # Pending
            
            return {"status" : 1, "msg" :"Thank you for contacting us. we will get back to you soon."}
        

def user_profile(db,id):
    get_user=db.query(User).filter(User.id ==id).first() 
    if get_user:       
        followers_count=db.query(FollowUser).filter_by(following_userid = id).count()
        following_count=db.query(FollowUser).filter_by(follower_userid = id).count()
        nugget_count=db.query(NuggetsMaster).join(Nuggets).filter(NuggetsMaster.user_id == id,NuggetsMaster.status == 1,Nuggets.nuggets_id == NuggetsMaster.id).count()
        event_count=db.query(Events).filter_by(created_by = id,status = 1).count()
        
        friend_count=db.query(MyFriends).filter(MyFriends.status == 1,MyFriends.request_status == 1,or_(MyFriends.sender_id == get_user.id,MyFriends.receiver_id == get_user.id)).count()
        
        
        user_details={}
        user_details.update({"user_id":get_user.id,
                            "user_ref_id":get_user.user_ref_id,
                            "is_email_id_verified":get_user.is_email_id_verified,
                            "is_mobile_no_verified":get_user.is_mobile_no_verified,
                            "acc_verify_status":1 if get_user.is_email_id_verified == 1 or get_user.is_mobile_no_verified == 1 else 0, 
                            "is_profile_updated":1 if get_user.dob != "" and get_user.gender != "" else 0,
                            "name":get_user.display_name if get_user.display_name else "",
                            "email_id":get_user.email_id,
                            "mobile":get_user.mobile_no,
                            "profile_image":get_user.profile_img,
                            "cover_image":get_user.cover_image,
                            "website":get_user.website,
                            "first_name":get_user.first_name,
                            "last_name":get_user.last_name,
                            "gender":get_user.gender,
                            "dob":get_user.dob,
                            "country_code":get_user.country_code,
                            "country_id":get_user.country_id,
                            "user_code":get_user.user_code,
                            "geo_location":get_user.geo_location,
                            "latitude":get_user.latitude,
                            "longitude":get_user.longitude,
                            "date_of_join":get_user.created_at,
                            "user_type":get_user.user_type_master.name if get_user.user_type_id else "",  # .....
                            "user_status":get_user.user_status_master.name if get_user.user_status_id else "", #-----
                            "user_status_id":get_user.user_status_id,
                            "bio_data":get_user.bio_data,
                            "followers_count":followers_count,
                            "friend_count":friend_count,
                            "following_count":following_count,
                            "nugget_count":nugget_count,
                            "event_count":event_count
                            
                        })
        token_text=(str(get_user.user_ref_id) + str(datetime.now().timestamp())).encode("ascii")
        invite_url=inviteBaseurl()
        join_link=f"{invite_url}signup?ref={token_text}"
        
        user_details.update({"referral_link":join_link})
        
        settings=db.query(UserSettings).filter(UserSettings.user_id == get_user.id).first()
        if settings:
            user_details.update({"language":settings.language.name if settings.language_id else ""})
        else:
            user_details.update({"language":"English"})
        
        two_type_verification=OTPverificationtype(db,get_user)
        
        user_details.update({"two_type_verification":two_type_verification})
        
        return {"status":1,"msg":"Success","profile":user_details}
        
    

# 11 - Get My Profile
@router.post("/getmyprofile")
async def getmyprofile(db:Session=Depends(deps.get_db),token:str=Form(...),auth_code:str=Form(...,description="SALT + token")):
    if token.strip() == "":
        return {"status" : -1, "msg" :"Sorry! your login session expired. please login again."}
        
    elif auth_code.strip() == "":
        return {"status" : -1, "msg" :"Auth Code is missing"}
    
    else:
        access_token=checkToken(db,token.strip())
        auth_text=token.strip()
        
        if checkAuthCode(auth_code,auth_text) == False:
            return {"status" : 0, "msg" :"Authentication failed!"}
            
        else:
            if access_token == False:
                return {"status" : -1, "msg" :"Sorry! your login session expired. please login again."}
                
            else:
                get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
                login_user_id=get_token_details.user_id if get_token_details else None
                
                
                get_user=db.query(User).filter(User.id ==login_user_id).first()
                if get_user:
                    user_details= user_profile(db,login_user_id)
                    return user_details 
                
                else:
                    return {"status" : 0, "msg" :"No result found!"}
                    


# 12. Update My Profile
@router.post("/updatemyprofile")
async def updatemyprofile(db:Session=Depends(deps.get_db),token:str=Form(...),name:str=Form(...),first_name:str=Form(...),last_name:str=Form(None),
                          gender:int=Form(None,description="0->Transgender,1->Male,2->Female",ge=0,le=2),dob:date=Form(None),
                          email_id:str=Form(...),website:str=Form(None),country_code:int=Form(None),country_id:int=Form(None),
                          mobile_no:int=Form(None),profile_image:UploadFile=File(None),cover_image:UploadFile=File(None),
                          auth_code:str=Form(...,description="SALT + token + name"),geo_location:str=Form(None),latitude:str=Form(None),
                          longitude:str=Form(None),bio_data:str=Form(None)):
    if token.strip() == "":
        return {"status" : -1, "msg" :"Sorry! your login session expired. please login again."}
        
    elif auth_code.strip() == "":
        return {"status" : -1, "msg" :"Auth Code is missing"}
    
    elif name.strip() == "":
        return {"status" : -1, "msg" :"Name is missing"}

    else:
        access_token=checkToken(db,token)
        if access_token == False:
            return {"status" : -1, "msg" :"Sorry! your login session expired. please login again."}
        else:
            auth_text=f"{token}{name}"
            if checkAuthCode(auth_code,auth_text) == False:
                return {"status" : 0, "msg" :"Authentication failed!"}
            else:
                get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
                
                login_user_id=get_token_details.user_id if get_token_details else None
                
                get_user_profile=db.query(User).filter(User.id == login_user_id).first()
                
                check_email=db.query(User).filter(User.email_id == email_id,User.id != login_user_id).first()
                check_phone=db.query(User).filter(User.mobile_no == mobile_no,User.id != login_user_id).first()
                
                if check_email:
                    return {"status" : 0, "msg" :"This email ID is already used"}
                elif check_phone:
                    return {"status" : 0, "msg" :"This phone number is already used"}
                
                elif re.search("/[^A-Za-z0-9]/", first_name.strip()):
                    return {"status" : 0, "msg" :"Please provide valid first name"}
                
                elif re.search("/[^A-Za-z0-9]/", last_name.strip()):
                    return {"status" : 0, "msg" :"Please provide valid last name"}
                   
                else:
                    # Update User
                    get_user_profile.display_name=name.strip() if name else get_user_profile.display_name
                    get_user_profile.first_name=first_name.strip() if first_name else get_user_profile.first_name
                    get_user_profile.last_name=last_name.strip() if last_name else get_user_profile.last_name
                    get_user_profile.gender=gender if gender else get_user_profile.gender
                    get_user_profile.dob=dob if dob else get_user_profile.dob
                    get_user_profile.country_code=country_code if country_code else get_user_profile.country_code
                    get_user_profile.mobile_no=mobile_no if mobile_no else get_user_profile.mobile_no
                    get_user_profile.email_id=email_id.strip() if email_id else get_user_profile.email_id
                    get_user_profile.website=website.strip() if website else get_user_profile.website
                    get_user_profile.country_id=country_id if country_id else get_user_profile.country_id
                    get_user_profile.geo_location=geo_location.strip() if geo_location else get_user_profile.geo_location
                    get_user_profile.latitude=latitude.strip() if latitude else get_user_profile.latitude
                    get_user_profile.longitude=longitude.strip() if longitude else get_user_profile.longitude
                    get_user_profile.bio_data=bio_data.strip() if bio_data else get_user_profile.bio_data
                    db.commit()
                    
                    # Image Part Pending
                    
                    
                    # Get Updated User Profile
                    get_user=db.query(User).filter(User.id ==login_user_id).first()
                    if get_user:
                        user_details=user_profile(db,get_user.id)
                        return user_details

                    else:
                        return {"status":0,"msg":"Something went wrong!"}
                        

# 13 Search Rawcaster Users (for friends)
@router.post("/searchrawcasterusers")
async def searchrawcasterusers(db:Session=Depends(deps.get_db),token:str=Form(...,description="Any name, email"),auth_code:str=Form(...,description="SALT + token"),
                               search_for:int=Form(None,description="0-Pending,1-Accepted,2-Rejected,3-Blocked",ge=0,le=3),page_number:int=Form(default=1),search_key:str=Form(None)):
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    elif auth_code.strip() == "":
        return {"status":-1,"msg":"Auth Code is missing"}
    else:
        access_token=checkToken(db,token.strip())
        auth_text=token.strip()
        if checkAuthCode(auth_code.strip(),auth_text) == False:
            return {"status":0,"msg":"Authentication failed!"}
        else:
            if access_token == False:
                return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
            else:
                login_user_email=''
                get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token ).first()
                
                login_user_id=get_token_details.user_id if get_token_details else None
                login_user_email=get_token_details.user.email_id if get_token_details else None
                
                current_page_no=page_number
                get_user=db.query(User.id,User.email_id,User.user_ref_id,User.first_name,User.last_name,User.display_name,User.gender,User.profile_img,User.geo_location,MyFriends.request_status.label("friend_request_status"),FollowUser.id.label("follow_id")).filter(User.status == 1,User.id != login_user_id,or_(MyFriends.sender_id == User.id,MyFriends.receiver_id == User.id),or_(MyFriends.sender_id == login_user_id,MyFriends.receiver_id == login_user_id),FollowUser.following_userid == User.id,FollowUser.follower_userid == login_user_id)
                
                # Omit blocked users
                request_status=3
                response_type=1
                requested_by=None
                get_all_blocked_users=get_friend_requests(db,login_user_id,requested_by,request_status,response_type,search_key)
                blocked_users=get_all_blocked_users['blocked']
                
                if blocked_users:
                    get_user=get_user.filter(User.id.not_in(blocked_users))
                
                if search_key and (search_key != None or search_key != ""):
                    
                    get_user=get_user.filter(or_(User.email_id.like(search_key+"%"),User.mobile_no.like(search_key+"%"),User.display_name.like(search_key+"%"),User.first_name.like(search_key+"%"),User.last_name.like(search_key+"%")))
                
                get_row_count=get_user.count()
                
                if get_row_count < 1 :
                    if login_user_email == search_key:
                        return {"status":0,"msg":"No Result found","invite_flag":0}
                    else:
                        
                        return {"status":0,"msg":"No Result found","invite_flag":1}
                else:
                    default_page_size=25
                    limit,offset=get_pagination(get_row_count,current_page_no,default_page_size)
                    
                    get_user=get_user.order_by(User.first_name.asc()).limit(limit).offset(offset).all()
                    
                    user_list=[]
                    for user in get_user:
                        mutual_friends=MutualFriends(db.login_user_id,user.id)
                        user_list.append({  "user_id":user.id,
                                            "user_ref_id":user.user_ref_id,
                                            "email_id":user.email_id if user.email_id else "",
                                            "first_name":user.first_name if user.first_name else "",
                                            "last_name":user.last_name if user.last_name else "",
                                            "display_name":user.display_name if user.display_name else "",
                                            "gender":user.gender if user.gender else "",
                                            "profile_img":user.profile_img if user.profile_img else "",
                                            "friend_request_status":user.friend_request_status if user.friend_request_status else "",
                                            "follow":user.follow,
                                            "location":user.location,
                                            "mutual_friends":mutual_friends
                                        })
                    return {"status":1,"msg":"Success","total_pages":get_row_count,"current_page_no":current_page_no,"users_list":user_list}
                    



# 14 Invite to Rawcaster
@router.post("/invitetorawcaster")
async def invitetorawcaster(db:Session=Depends(deps.get_db),token:str=Form(...),email_id:list=Form(...,description="email ids"),
                               auth_code:str=Form(...,description="SALT + token")):
    
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    elif auth_code.strip() == "":
        return {"status":-1,"msg":"Auth Code is missing"}

    else:
        access_token=checkToken(db,token.strip())
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            
            login_user_id=get_token_details.user_id
            login_user_name=get_token_details.user.first_name
            
            if IsAccountVerified(db,login_user_id) == False:
                return {"status":0,"msg":"You need to complete your account validation before you can do this"}
            
            if email_id == "" or email_id == []:
                return {"status":0,"msg":"Please provide a valid email address"}
                
            else:
                auth_text=token.strip()
                if checkAuthCode(auth_code.strip(),auth_text) == False:
                    return {"status":0,"msg":"Authentication failed!"}
                else:
                    success=0
                    failed=0
                    total=len(email_id)
                    
                    for mail in email_id:
                        if check_mail(mail) == False:
                            
                            failed += 1
                        else:
                           
                            get_user=db.query(User).filter(User.email_id == str(mail).strip()).first()
                            
                            if get_user:
                                failed += 1
                            
                            else:
                                # Invites Sents Only for New User (Not a Rawcaster)
                                get_user=db.query(User).filter(User.id == login_user_id).first()
                                token_text = base64.b64encode(f"{get_user.user_ref_id}//{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".encode()).decode()
                                invite_link=inviteBaseurl()
                                join_link=f"{invite_link}signup?ref={token_text}&mail={mail}"
                
                                subject=f"Rawcaster - Invite from '.{login_user_name}"
                                # Pending
                    
                    if total == failed:
                        return {"status":0,"msg":"Failed to send invites"}
                    if success == total:
                        return {"status":1,"msg":"Invites sent"}
                    else:
                        return {"status":1,"msg":"Invites sent"}
                        
                                

# 15 Send friend request to others
@router.post("/sendfriendrequests")
async def sendfriendrequests(db:Session=Depends(deps.get_db),token:str=Form(...),user_ids:list=Form(...,description="email ids"),
                               auth_code:str=Form(None,description="SALT + token")):
    
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    if auth_code.strip() == "":
        return {"status":-1,"msg":"Auth Code is missing"}
    
    else:
        access_token=checkToken(token.strip())
        auth_text=token.strip()
        
        if checkAuthCode(auth_code,auth_text.strip()) == False:
            return {"status":0,"msg":"Authentication failed!"}
    
        else:
            if access_token == False:
                return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
            else:
                get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
                
                login_user_id=get_token_details.user_id
                login_user_name=get_token_details.user.first_name
            if user_ids == []:
                return {"status":-1,"msg":"Users list is missing"}
            else:
                
                del user_ids[login_user_id]
                
                if user_ids == "" or user_ids == None:
                    return {"status":0,"msg":"Please provide a valid users list"}
                else:
                    friend_request_ids=[]
                    get_user=db.query(User).filter(User.id == login_user_id).first()
                    hostname=get_user.display_name if get_user else None
                    
                    for user in user_ids:
                        users=db.query(User).filter(User.user_ref_id == user).first()
                        
                        if users:
                            user_id=users.id
                            request_status=[0,1,3]
                            get_my_friends=db.query(MyFriends).filter(MyFriends.status == 1,MyFriends.request_status.in_(request_status),or_(MyFriends.sender_id == login_user_id,MyFriends.sender_id == user),or_(MyFriends.sender_id == user,MyFriends.receiver_id == login_user_id)).order_by(MyFriends.id.desc())
                            
                            get_friend_request=get_my_friends.first()
                            
                            if not get_friend_request:
                                get_user=db.query(User).filter(User.id == user).first()
                                
                                if get_user:
                                    add_my_friends=MyFriends(sender_id=login_user_id,receiver_id=user,request_date=datetime.now(),request_status=0,status_date=None,status=1)
                                    db.add(add_my_friends)
                                    db.commit()
                                    
                                    if add_my_friends:
                                        add_notification=Insertnotification(db,user_id,login_user_id,11,login_user_id)
                                        
                                        friend_request_ids.append(add_my_friends.id)
                                        
                                        message_details={}
                                        message_details.update({"message":f"{hostname} Sent a connection request","data":{"refer_id":add_my_friends.id,"type":"friend_request"},"type":"friend_request"})

                                        push_notification=pushNotify(db,user,message_details,login_user_id)
                                        
                                        body=''
                                        sms_message=''
                                        sms_message,body= friendRequestNotifcationEmail(db,login_user_id,user,1)
                                        
                                        subject='Rawcaster - Connection Request'
                                        email_detail = {"subject": subject, "mail_message": body, "sms_message": sms_message, "type": "friend_request"}
                                        send_notification=addNotificationSmsEmail(db,user,email_detail,login_user_id)
                    if friend_request_ids:
                        return {"status":1,"msg":"Connection request sent successfully","friend_request_ids":friend_request_ids}
                
                    else:
                        return {"status":0,"msg":"Failed to send Connection request","friend_request_ids":friend_request_ids}
                        



# 16 List all friend requests (all requests sent to this users from others)
@router.post("/listallfriendrequests")
async def listallfriendrequests(db:Session=Depends(deps.get_db),token:str=Form(...)):
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id
            login_user_name=get_token_details.user.first_name
            
            response_type=0
            request_status=0
            requested_by=2
            pending_requests=get_friend_requests(db,login_user_id,requested_by,request_status,response_type)
        
            return {"status":1,"msg":"Success","pending_requests":pending_requests.pending}



# 17 Respond to friend request received from others
@router.post("/respondtofriendrequests")
async def respondtofriendrequests(db:Session=Depends(deps.get_db),token:str=Form(...),friend_request_id:int=Form(...),notification_id:int=Form(...),
                                  response:int=Form(...,description="1-Accept,2-Reject,3-Block",ge=1,le=3)):
                         
    if token.strip() == '':
        return {"status": -1, "msg": "Sorry! your login session expired. please login again."}
    else:
        access_token = checkToken(token)
        if not access_token:
            return {"status": -1, "msg": "Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            
            login_user_id=get_token_details.user_id
            login_user_name=get_token_details.user.first_name

            my_friends=db.query(MyFriends).filter(MyFriends.status == 1,MyFriends.request_status== 0,MyFriends.id == friend_request_id,MyFriends.receiver_id == login_user_id ).first()

            if not my_friends:
                return {"status": 0, "msg": "Invalid request"}
                
            else:
                if response == 2:
                    status=0
                else:
                    status=1
                
                update_my_friends=db.query(MyFriends).filter(MyFriends.id == friend_request_id).update({"status":status,"request_status":response,"status_date":datetime.now()})
                db.commit()
                
                if update_my_friends:
                    if notification_id:
                        # if status == 1:
                        update_notification=db.query(Notification).filter(Notification.id == notification_id).update({"status":0,"is_read":1,"read_datetime":datetime.now()})
                        db.commi()
                        # else:
                        #     update_notification=db.query(Notification).filter(Notification.id == notification_id).update({"status":0,"is_read":1,"read_datetime":datetime.now()})
                    else:
                        update_notification=db.query(Notification).filter(Notification.notification_origin_id == my_friends.sender_id,Notification.user_id ==my_friends.receiver_id,Notification.notification_type == 11).update({"status":0,"is_read":1,"read_datetime":datetime.now()})
                        db.commi()
                    
                    if response == 1:
                        friend_requests=my_friends.user1
                        friend_details={}
                        friend_details.update({
                                                "friend_request_id":friend_requests.id,
                                                "user_id":friend_requests.id,
                                                "email_id":friend_requests.email_id,
                                                "first_name":friend_requests.first_name,
                                                "last_name":friend_requests.last_name,
                                                "display_name":friend_requests.display_name,
                                                "gender":friend_requests.gender,
                                                "profile_img":friend_requests.profile_img,
                                                "online":friend_requests.online,
                                                "last_seen":friend_requests.last_seen,
                                                "typing":0
                                            })
                        
                        sender_id=my_friends.sender_id
                        receiver_id=my_friends.receiver_id
                        notification_type=12
                        insert_notification=Insertnotification(db,sender_id,receiver_id,notification_type,receiver_id)
                    
                        friend_request_ids=[friend_requests.id]
                        body=''
                        sms_message=''
                        sms_message,body=friendRequestNotifcationEmail(db,sender_id,login_user_id,2)
                        
                        subject='Rawcaster - Connection Request Accepted'
                        
                        email_detail = {"subject": subject, "mail_message": body, "sms_message": sms_message, "type": "friend_request"}
                        
                        add_notification=addNotificationSmsEmail(db,list(sender_id),email_detail,login_user_id)
                        
                        return {"status":1,"msg":"Success","friend_details":friend_details}
                    else:
                        return {"status":1,"msg":"Success"}
                else:
                    return {"status":0,"msg":"Failed to update. please try again"}
                    
                        
                    
                    
# 18 List all Friend Groups
@router.post("/listallfriendgroups")
async def listallfriendgroups(db:Session=Depends(deps.get_db),token:str=Form(...),search_key:str=Form(None),page_number:int=Form(default=1),flag:str=Form(None)):
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            
            login_user_id=get_token_details.user_id
            
            current_page_no=page_number
            
            flag=flag if flag else 0
            
            my_friend_group=db.query(FriendGroups.id,FriendGroups.chat_enabled,FriendGroups.created_by,FriendGroups.group_name,FriendGroups.group_icon,func.count(FriendGroupMembers.id.label("members_count")))
            my_friend_group=my_friend_group.group_by(FriendGroups.id).filter(FriendGroups.status == 1,or_(FriendGroups.created_by == login_user_id,FriendGroupMembers.user_id == login_user_id))
            # Query Pending
            
            if search_key and search_key.strip() == "":
                my_friend_group=my_friend_group.filter(FriendGroups.group_name.like(search_key+"%"))
                
            get_row_count=my_friend_group.count()
            
            if get_row_count < 1:
                return {"status":0,"msg":"No Result found"}
            
            else:
                default_page_size=1000
                
                limit,offset=get_pagination(get_row_count,current_page_no,default_page_size)
                
                my_friend_group=my_friend_group.order_by(FriendGroups.group_name.asc()).limit(limit).offset(offset).all()
                result_list=[]
                for res in my_friend_group:
                    grouptype=1
                    groupname=res.group_name
                    
                    if groupname == "My Fans":
                        grouptype=2
                    
                    if groupname == "My Fans" and res.created_by != login_user_id:
                        groupname=f"Influencer: {(res.user.display_name if res.user.display_name else '') if res.created_by else ''}"
            
                    result_list.append({
                                        "group_id":res.id,
                                        "group_name":groupname,
                                        "group_icon":res.group_icon if res.group_icon else "",
                                        "group_member_count":res.members_count + 1 if res.members_count else 0,
                                        "group_owner":res.created_by if res.created_by else 0,
                                        "typing":0,
                                        "chat_enabled":res.chat_enabled,
                                        "group_type":grouptype
                                        })
                    
                    get_group_chat=db.query(GroupChat).filter(GroupChat.status == 1,GroupChat.group_id == res.id).order_by(GroupChat.id.desc()).first()
                    
                    result_list.append({"last_msg":get_group_chat.message if get_group_chat else "","last_msg_datetime":get_group_chat.sent_datetime if get_group_chat.sent_datetime else "","result_list":3})
            
                    memberlist=[]
                    members=[]
                    membercount=0
                    if grouptype == 1:
                        members.append(res.created_by)
                        memberlist.append({
                                            "user_id":res.created_by,
                                            "email_id":res.user.email_id,
                                            "first_name":res.user.first_name,
                                            "last_name":res.user.last_name,
                                            "display_name":res.user.display_name,
                                            "gender":res.user.gender,
                                            "profile_img":res.user.profile_img,
                                            "online":res.user.online,
                                            "last_seen":res.user.last_seen,
                                            "typing":0
                                            })
                        
                    get_friend_group_member=db.query(FriendGroupMembers).filter(FriendGroupMembers.group_id == res.id).all()
                    for group_member in get_friend_group_member:
                        members.append(group_member.user_id)
                        memberlist.append({
                                            "user_id":group_member.user_id,
                                            "email_id":group_member.user.email_id if group_member.user_id else "",
                                            "first_name":group_member.user.first_name if group_member.user_id else "",
                                            "last_name":group_member.user.last_name if group_member.user_id else "",
                                            "display_name":group_member.user.display_name if group_member.user_id else "",
                                            "gender":group_member.user.gender if group_member.user_id else "",
                                            "profile_img":group_member.user.profile_img if group_member.user_id else "",
                                            "online":group_member.user.online if group_member.user_id else "",
                                            "last_seen":group_member.user.last_seen if group_member.user_id else "",
                                            "typing":0
                                            })
                    
                    result_list.append({"group_member_ids":members,"group_members_list":memberlist})
                        
                return {"status":1,"msg":"Success","group_count":get_row_count,"total_pages":get_row_count,"current_page_no":current_page_no,"friend_group_list":result_list}
            
            
            
# 19 List all Friends
@router.post("/listallfriends")
async def listallfriends(db:Session=Depends(deps.get_db),token:str=Form(...),search_key:str=Form(None),group_ids:str=Form(None,description="Like ['12','13','14']"),
                         nongrouped:int=Form(None,description="Send 1",ge=1,le=1),friends_count:int=Form(None),allfriends:int=Form(None,description="send 1",ge=1,le=1),
                         page_number:int=Form(None,description="send 1 for initial request")):
                         
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        
    else:
        access_token=checkToken(db,token)
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
            
        else:
            login_from=1
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id
            login_from=get_token_details.device_type
            
            current_page_no=page_number
            my_friends_ids=[]
            
            # Step 1) Get all active friends of logged in user (if requested for all friends list)
            if allfriends and allfriends == 1:
                get_all_friends=db.query(MyFriends).filter(MyFriends.status == 1,MyFriends.request_status == 1,or_(MyFriends.sender_id == login_user_id,MyFriends.receiver_id == login_user_id)).all()
                
                if get_all_friends:
                    my_friends_ids=[frnds.id for frnds in get_all_friends]
            
                else:  #  # Step 2) Get all active friends of logged in user (based on requested conditions)
                    # Step 2.1) Get all non grouped friends
                    all_group_friends=set()
                    
                    if nongrouped and nongrouped == 1:
                        get_all_group_friends=db.query(FriendGroupMembers).filter(FriendGroupMembers.group_id == FriendGroups.id,FriendGroupMembers.status == 1,FriendGroups.status == 1,FriendGroups.created_by == login_user_id).all()
                        
                        all_group_friends=[gp_user.user_id for gp_user in get_all_group_friends]

                        # Step 2.1.2) Get all friends who are all not invloved any one of the group
                        get_all_non_group_friends=db.query(MyFriends).filter(MyFriends.status == 1 ,MyFriends.request_status == 1)

                        if all_group_friends:
                            group_members_ids= ",".join(all_group_friends)
                            get_all_non_group_friends=get_all_non_group_friends.filter(or_(MyFriends.sender_id == login_user_id,MyFriends.sender_id.not_in(group_members_ids)),or_(MyFriends.receiver_id.not_in(group_members_ids),MyFriends.receiver_id == login_user_id))
                        else:
                            get_all_non_group_friends=get_all_non_group_friends.filter(or_(MyFriends.sender_id == login_user_id,MyFriends.receiver_id == login_user_id))

                        get_all_non_group_friends=get_all_non_group_friends.all()
                        
                        if get_all_non_group_friends:
                            my_friends_ids=[enemy.id for enemy in get_all_non_group_friends]
                    
                    # Step 2.2) Get all friends who are already in requested groups
                    if group_ids and group_ids.split != "":
                        requested_group_friends=set()
                        requested_group_ids=group_ids
                        
                        if requested_group_ids and requested_group_ids != []:
                            # Step 2.2.1) Get all friends who are already in requested groups
                            get_requested_group_members=db.query(FriendGroupMembers).filter(FriendGroupMembers.group_id == FriendGroups.id,FriendGroupMembers.status == 1,FriendGroups.status == 1,FriendGroups.created_by ==login_user_id)
                            get_requested_group_members=get_requested_group_members.filter(FriendGroupMembers.group_id.in_(requested_group_ids)).all()
                            
                            if get_requested_group_members:
                                requested_group_friends=[req_frnd.user_id for req_frnd in get_requested_group_members]
                        
                                # Step 2.2.2) Get all friends who are already in requested groups
                                get_all_requested_group_friends=db.query(MyFriends).filter(MyFriends.status == 1,MyFriends.request_status == 1)

                                if requested_group_friends:
                                    requested_group_friends_ids= ",".join(requested_group_friends)
                                    get_all_requested_group_friends=get_all_requested_group_friends.filter(or_(MyFriends.sender_id == login_user_id,MyFriends.sender_id.in_(requested_group_friends_ids)),or_(MyFriends.receiver_id.in_(requested_group_friends_ids),MyFriends.receiver_id == login_user_id ))

                                    get_all_requested_group_friends=get_all_requested_group_friends.all()
                                    
                                    if get_all_requested_group_friends:
                                        my_friends_ids=[req_frnd.id for req_frnd in get_all_requested_group_friends]
                        
                # Get Final result after applied all requested conditions    [[[[  SUB QUERY  ]]]]
                get_row_count=db.query(MyFriends,FollowUser.id.label("follow_id"),any(db.query(FriendsChat.meaasge).filter(FriendsChat.sent_type == 1,or_(FriendsChat.sender_id == MyFriends.sender_id,FriendsChat.sender_id == MyFriends.receiver_id),or_(FriendsChat.receiver_id == MyFriends.receiver_id,FriendsChat.receiver_id == MyFriends.sender_id),or_(FriendsChat.sender_id == login_user_id,FriendsChat.receiver_id == login_user_id),or_(FriendsChat.receiver_delete == None,FriendsChat.sender_delete == None)).order_by(FriendsChat.sent_datetime.desc())))
                
                
                # Pending

# 20 Add Friend Group
@router.post("/addfriendgroup")
async def addfriendgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_name:str=Form(...),group_members:str=Form(None,description=" User ids Like ['12','13','14']"),
                         group_icon:UploadFile=File(None)):
                         
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}

    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id
            
            if group_name.strip() == "":
                return {"status":0,"msg":"Sorry! Group name can not be empty."}
            else:
                get_row_count=db.query(FriendGroups).filter(FriendGroups.status == 1,FriendGroups.created_by == login_user_id,FriendGroups.group_name == group_name).count()
                if get_row_count:
                    return {"status":0,"msg":"Group name already exists"}
                    
                else:
                    # Add Friend Group
                    group_icon='group_icon'
                    add_friend_group=FriendGroups(group_name = group_name,group_icon=defaultimage(group_icon),created_by=login_user_id,created_at=datetime.now(),status =1)
                    db.add(add_friend_group)
                    db.commit()
                    
                    if add_friend_group:
                        if group_members:
                            for member in group_members:
                                get_user=db.query(User).filter(User.id == member).first()
                                
                                if get_user:
                                    # add Friend Group member
                                    add_member=FriendGroupMembers(group_id = add_friend_group.id,user_id=member,added_date=datetime.now(),added_by=login_user_id,is_admin=0,disable_notification=0,status=1)
                                    db.add(add_member)
                                    db.commit()
                                    
                        # Profile Image
                        if group_icon:
                            # Pending
                            print("Pending")
                            
                        group_details= GetGroupDetails(db,add_friend_group.id)
                            
                        message_detail={"message":f"{add_friend_group.user.display_name} : created new group",
                                        "title":add_friend_group.group_name,
                                        "data":{"refer_id":add_friend_group.id,"type":"add_group"},
                                        "type":"callend"
                                        }
                        notify_members=group_details['group_member_ids']
                        
                        if add_friend_group.created_by in notify_members:
                            notify_members.remove(add_friend_group.created_by) 
                        
                        push_notification=pushNotify(db,notify_members,message_detail,login_user_id)
                        
                        return {"status":1,"msg":"Successfully created group","group_details":group_details}
                    else:
                        return {"status":0,"msg":"Failed to create group"}
                        
                        
                        

# 21 Edit Friend Group
@router.post("/editfriendgroup")
async def editfriendgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_name:str=Form(...),group_id:int=Form(...),
                         group_icon:UploadFile=File(None),group_members:List[int]=Form(None)):
  
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id
        
        if group_name.strip() == "":
            return {"status":0,"msg":"Sorry! Group name can not be empty."}
        else:
            get_frnd_group_count=db.query(FriendGroups).filter(FriendGroups.status == 1 ,FriendGroups.created_by == login_user_id,FriendGroups.group_name == group_name,or_(FriendGroups.id == group_id,FriendGroups.id != group_id)).count()
            
            if get_frnd_group_count > 0:
                return {"status":0,"msg":"Group name already exists"}
                
            else:
                get_group=db.query(FriendGroups).filter(FriendGroups.status == 1,FriendGroups.created_by == login_user_id,FriendGroups.id == group_id).first()
                if not get_group:
                    return {"status":0,"msg":"Invlaid request"}

                elif get_group.group_name == "My Fans":
                    return {"status":0,"msg":"You can't edit the My Fans group."}
                    
                else:
                    img_path=get_group.group_icon
                    
                    # Profile Image
                    if group_icon:
                        print("Imga eupload pending")
                    
                    if group_members:
                        for member in group_members:
                            if member == member.created_by:
                                pass
                            get_user=db.query(User).filter(User.id == member).first()
                            
                            if get_user:
                                check_member=db.query(FriendGroupMembers).filter(FriendGroupMembers.status == 1,FriendGroupMembers.group_id == group_id,FriendGroupMembers.user_id == member).first()
                                
                                if not check_member:
                                    add_frnd_group=FriendGroupMembers(group_id = group_id,user_id = member,added_date=datetime.now(),added_by=login_user_id,is_admin=0,disable_notification=1,status=1)
                                    db.add(add_frnd_group)
                                    db.commit()
                    update_frnd_group=db.query(FriendGroups).filter(FriendGroups.id == get_group.id).update({"group_name":group_name,"group_icon":'pending',})               
                    db.commit()
                    
                    group_details=GetGroupDetails(db,group_id)
                    
                    return {"status":1,"msg":"Successfully updated","group_details":group_details}

                


# 22 Add Friends to Group
@router.post("/addfriendstogroup")
async def addfriendstogroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_members:str=Form(...,description=" User ids Like ['12','13','14']"),group_id:int=Form(...)):
    
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id
            username =get_token_details.user.display_name
            
            group_members = json.loads(group_members)
            
            get_group=db.query(FriendGroups).filter(FriendGroups.status == 1,FriendGroups.created_by == login_user_id,FriendGroups .id == group_id).first()
            
            if not get_group:
                return {"status":0,"msg":"Invalid request"}
            
            elif get_group.group_name == "My Fans":
                return {"status":0,"msg":"You can't add member in My Fans group"}
            
            else:
                memberdetails=[]
                if group_members != []:
                    memcount=0
                    
                    for member in group_members:
                        get_user=db.query(User).filter(User.id == member).first()
                        
                        if get_user:
                            check_member=db.query(FriendGroupMembers).filter(FriendGroupMembers.status == 1,FriendGroupMembers.group_id == group_id,FriendGroupMembers.user_id == member).first()
                            
                            if not check_member:
                                add_frnd_group_member=FriendGroupMembers(group_id = group_id,user_id = member,added_date=datetime.now(),added_by=login_user_id,is_admin=0,disable_notification=1,status=1)
                                db.add(add_frnd_group_member)
                                db.commit()
                                
                                if add_frnd_group_member:
                                    memberdetails.append({
                                                        "display_name":add_frnd_group_member.user.display_name,
                                                        "email_id":add_frnd_group_member.user.email_id,
                                                        "first_name":add_frnd_group_member.user.first_name,
                                                        "gender":add_frnd_group_member.user.gender,
                                                        "last_name":add_frnd_group_member.user.last_name,
                                                        "last_seen":add_frnd_group_member.user.last_seen,
                                                        "online":'',
                                                        "profile_img":add_frnd_group_member.user.profile_img,
                                                        "typing":0,
                                                        "user_id":add_frnd_group_member.user_id
                                                        })
                                    
                    group_details=GetGroupDetails(db,get_group.id)
                    
                    message_detail={
                                    "message":f"{username}: added members",
                                    "title":get_group.group_name,
                                    "data":{"refer_id":get_group.id,"type":"add_group"},
                                    "type":"callend"
                                }
                    notify_members=group_details['group_member_ids']
                    
                    if get_group.created_by in notify_members:
                        key = notify_members.index(get_group.created_by)
                        notify_members.pop(key)
                    
                    send_push_notification=pushNotify(db,notify_members,message_detail,login_user_id)
                    
                    return {"status":1,"msg":"Successfully Added","memberdetails":memberdetails}
 
                else:
                    return {"status":0,"msg":"Failed to add"}
            


# 23 Remove Friends from Group
@router.post("/removefriendsfromgroup")
async def removefriendsfromgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_members:str=Form(...,description=" User ids Like ['12','13','14']"),group_id:int=Form(...)):
             
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id    
            
            group_members = json.loads(group_members)
            
            get_group=db.query(FriendGroups).filter(FriendGroups.status == 1,FriendGroups.created_by == login_user_id,FriendGroups.id == group_id).first()
            if not get_group:
                return {"status":0,"msg":"Invalid request"}
                
            elif get_group.group_name == "My Fans":
                return {"status":0,"msg":"You can't remove member in My Fans group"}
                
            else:
                if group_members:
                    for member in group_members:
                        delete_members=db.query(FriendGroupMembers).filter_by(group_id =group_id,user_id =member).delete()
                        db.commit()
                
                return {"status":1,"msg":"Successfully updated"}



# 24. Delete Friend Group
@router.post("/deletefriendgroup")
async def deletefriendgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_id:int=Form(...)):
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id        
                      
            get_group=db.query(FriendGroups).filter(FriendGroups.created_by == login_user_id,FriendGroups.id == group_id).first()
            if not get_group:
                return {"status":0,"msg":"Invalid group info"}
            
            elif get_group.group_name == "My Fans":
                return {"status":0,"msg":"You can't delete My Fans group"}
            
            else:
                update_event_invitation=db.query(EventInvitations).filter_by(group_id=group_id).update({"status":0})
                update_friends_gp_memeber=db.query(FriendGroupMembers).filter_by(group_id=group_id).update({"status":0})
                update_friends_group=db.query(FriendGroups).filter_by(id=group_id).update({"status":0})
                
                db.commit()
                
                if update_friends_group:
                    return {"status":1,"msg":"Successfully deleted"}
                
                else:
                    return {"status":0,"msg":"Failed to delete. please try again"}
                



# 25. Add Nuggets
@router.post("/addnuggets")
async def addnuggets(db:Session=Depends(deps.get_db),token:str=Form(...),content:str=Form(...),share_type:int=Form(None),share_with:str=Form(None,description='friends":[1,2,3],"groups":[1,2,3]}'),
                     nuggets_media:UploadFile=File(...),poll_option:str=Form(None),poll_duration:str=Form(None),metadata:str=Form(None)):
                         
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id   
            
        if IsAccountVerified(db,login_user_id) == False:
            return {"status":0,"msg":"You need to complete your account validation before you can do this"}
            
        share_with= json.loads(share_with) if share_with else []
        
        if (share_type == 3 or share_type == 4 or share_type == 5) and not share_with:
            return {"status": 0, "msg": "Sorry! Share with can not be empty."}
        
        elif share_type == 3 and (not share_with.get("groups") or not share_with["groups"]):
            return {"status": 0, "msg": "Sorry! Share with groups list missing."}
        
        elif share_type == 4 and (not share_with.get("friends") or not share_with["friends"]):
            return {"status": 0, "msg": "Sorry! Share with friends list missing."}
        
        elif share_type == 5 and ((not share_with.get("groups") or not share_with["groups"]) and (not share_with.get("friends") or not share_with["friends"])):
            return {"status": 0, "msg": "Sorry! Share with groups or friends list missing."}
        
        else:
            anyissue = 0
            
            if share_type == 3 or share_type == 4 or share_type == 5:
                if share_with:
                    for key, val in share_with.items():
                        if val:
                            if key == "group" and (share_type == 3 or share_type == 5):
                                get_groups=db.query(FriendGroups).filter(FriendGroups.id == val,FriendGroups.status == 1,FriendGroups.created_by == login_user_id)

                                get_groups = {id: id for id, _ in get_groups.all()}

                                if len(get_groups) != len(val):
                                    anyissue=1
                                
                                elif key == "friends" and (share_type == 4 or share_type == 5):
                                    
                                    query = db.query(MyFriends.id, case([(MyFriends.receiver_id == login_user_id, MyFriends.sender_id)], else_=MyFriends.receiver_id).label('receiver_id'))
                                    query = query.filter(MyFriends.status == 1, MyFriends.request_status == 1)
                                    query = query.filter((MyFriends.sender_id == login_user_id) | (MyFriends.receiver_id == login_user_id))
                                    query=db.query(FriendGroups).filter(FriendGroups.id == val,FriendGroups.status == 1,FriendGroups.created_by == login_user_id)
                                    
                                    get_friends = query.all()
                                    
                                    if len(set(val) - set(get_friends)) > 0:
                                        anyissue = 1
            if anyissue == 1:
                return {"status": 0, "msg": "Sorry! Share with groups or friends list not correct."}
            else:
                add_nuggets_master=NuggetsMaster(user_id=login_user_id,content=content,metadata1=metadata,poll_duration=poll_duration,created_date=datetime.now(),status=1)
                db.add(add_nuggets_master)
                db.commit()
                
                if add_nuggets_master:
                    # Poll Option save
                    if poll_option:
                        for option in poll_option:
                            add_NuggetPollOption=NuggetPollOption(nuggets_master_id=add_nuggets_master.id,option_name=option.strip(),
                                                                    created_date=datetime.now(),status=1)
                    
                            db.add(add_NuggetPollOption)
                            db.commit()
                    attachment_count=0  
                    
                    # Nuggets Media
                    if nuggets_media:
                        print("Pending")
                    
                    add_nuggets=Nuggets(nuggets_id=add_nuggets_master.id,user_id=login_user_id,type=1,share_type=share_type,created_date=datetime.now())
                    db.add(add_nuggets)
                    db.commit()
                    
                    if add_nuggets:
                        nuggets=StoreHashTags(db,add_nuggets)
                        totalmembers=[]
                        
                        if share_type == 6 or share_type == 1:
                            requested_by=None
                            request_status=1
                            response_type=1
                            search_key=None
                            get_member=get_friend_requests(db,login_user_id,requested_by,request_status,response_type,search_key)

                            totalmembers.append(totalmembers.accepted)
                        
                        if share_type == 7:
                            get_members=getFollowers(db,login_user_id)

                        # If share type is Group or Individual
                        if share_type == 3 or share_type == 4 or share_type == 5:
                            if share_type == 4:
                                share_with.group =''
                            if share_type == 3:
                                share_with.friends =''
                            
                            if share_with:
                                for key,val in share_with:
                                    if val:
                                        for shareid in val:
                                            type= 2 if key == 'friends' else 1
                                            add_NuggetsShareWith=NuggetsShareWith(nuggets_id=add_nuggets.id,type =type,share_with=shareid)
                                            db.add(add_NuggetsShareWith)
                                            db.commit()
                                            
                                            if add_NuggetsShareWith:
                                                if key == 'friends':
                                                    totalmembers.append(shareid)
                                                else:
                                                    getgroupmember=db.query(FriendGroupMembers).filter_by(group_id =shareid).all()
                                                    
                                                    for member in getgroupmember:
                                                        if member.user_id not in totalmembers:
                                                            totalmembers.append(member.user_id)
                                                
                        if totalmembers:
                            for users in totalmembers:
                                notification_type=1
                                add_notification=Insertnotification(db,users,login_user_id,notification_type,add_nuggets.id)
                                    
                                get_user=db.query(User).filter(User.id == login_user_id).first()
                                user_name=''
                                if get_user:
                                    user_name=get_user.display_name
                                
                                message_detail={
                                        "message":"Posted new Nugget",
                                        "data":{"refer_id":add_nuggets.id,"type":"add_nugget"},
                                        "type":"nuggets"
                                    }
                                send_push_notification=pushNotify(totalmembers,message_detail,login_user_id)
                                body=''
                                sms_message=''
                                
                                if add_nuggets.id and add_nuggets.id != '':
                                    sms_message,body=nuggetNotifcationEmail(db,add_nuggets.id)  # Pending
                                    
                                subject='Rawcaster - Notification'
                                email_detail={"subject":subject,"mail_message":body,"sms_message":sms_message,"type":"nuggets"}
                                add_notification_sms_email= addNotificationSmsEmail(db,totalmembers,email_detail,login_user_id)

                        nugget_detail=get_nugget_detail(db,add_nuggets.id,login_user_id)  # Pending

                        return {"status":1,"msg":"Nuggets created successfully!","nugget_detail":nugget_detail}
                    else:
                        return {"status":0,"msg":"Failed to create Nugget"}
                    
                else:
                    return {"status":0,"msg":"Failed to create Nugget master"}


# 26. List Nuggets
@router.post("/listnuggets")
async def listnuggets(db:Session=Depends(deps.get_db),token:str=Form(...),my_nuggets:int=Form(None),filter_type:int=Form(None),user_id:int=Form(None),
                     saved:int=Form(None),search_key:str=Form(None),page_number:int=Form(None),nugget_type:int=Form(None,description="1-video,2-Other than video,0-all",ge=0,le=2)):
                         
    return "done"




# 27. Like And Unlike Nugget
@router.post("/likeandunlikenugget")
async def likeandunlikenugget(db:Session=Depends(deps.get_db),token:str=Form(...),nugget_id:int=Form(...),like:int=Form(...,description="1-like,2-unlike",ge=1,le=2)):
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            status=0
            msg="Invalid nugget id"
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id

            if IsAccountVerified(db,login_user_id) == False:
                return {"status":0,"msg":"You need to complete your account validation before you can do this"}
            
            access_check=NuggetAccessCheck(db,login_user_id,nugget_id)
            
            if not access_check:
                return {"status":0,"msg":"Unauthorized access"}
            
            check_nuggets=db.query(Nuggets).filter(Nuggets.id == nugget_id).first()
            
            if check_nuggets:
                if like == 1:
                    checkpreviouslike=db.query(NuggetsLikes).filter(NuggetsLikes.nugget_id == nugget_id,NuggetsLikes.user_id == login_user_id).first()
                    if checkpreviouslike:
                        nuggetlike=NuggetsLikes(user_id=login_user_id,nugget_id=nugget_id,created_date=datetime.now())
                        db.add(nuggetlike)
                        db.commit()
                        
                        if nuggetlike:
                            notification_type=5
                            Insertnotification(db,check_nuggets.user_id,login_user_id,notification_type,nugget_id)
                            status=1
                            msg = 'Success'
                        else:
                            msg='failed to like'
                            
                    else:
                        msg = 'Your already liked this nugget'
                elif like == 2:
                    checkpreviouslike=db.query(NuggetsLikes).filter(NuggetsLikes.nugget_id == nugget_id,NuggetsLikes.user_id == login_user_id).first()
                    if checkpreviouslike:
                        deleteresult=db.query(NuggetsLikes).filter_by(id = checkpreviouslike.id ).delete()
                        if deleteresult:
                            status = 1
                            msg="Success"
                        else:
                            msg='failed to unlike'
                    else:
                        msg='you not yet liked this nugget'
            return {"status":status,"msg":msg}            
        
        
        

# 28. Delete Nugget
@router.post("/deletenugget")
async def deletenugget(db:Session=Depends(deps.get_db),token:str=Form(...),nugget_id:int=Form(...)):
                         
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            status=0
            msg="Invalid nugget id"
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id

            if IsAccountVerified(db,login_user_id) == False:
                return {"status":0,"msg":"You need to complete your account validation before you can do this"}
            
            check_nugget_creater=db.query(Nuggets).filter(Nuggets.id == nugget_id,Nuggets.user_id == login_user_id).first()
            if check_nugget_creater:
                delete_nuggets=db.query(Nuggets).filter(Nuggets.id == check_nugget_creater.id).update({"nugget_status":2})
                db.commit()
                
                if delete_nuggets:
                    if check_nugget_creater.type == 1:
                        update_nugget_master=db.query(NuggetsMaster).filter_by(id = check_nugget_creater.nuggets_id).update({"status":0})
                        update_notification=db.query(Notification).filter_by(ref_id=nugget_id).delete()
                        db.commit()
                        
                        return {"status":1,"msg":"Nugget Deleted"}
                    else:
                        return {"status":1,"msg":"Nugget Deleted"}
                           
                else:
                    return {"status":0,"msg":"Unable to delete"}
                           
            else:
                return {"status":0,"msg":"Invalid nugget id"}
                       
                



# 29. Nugget Comment List
@router.post("/nuggetcommentlist")
async def nuggetcommentlist(db:Session=Depends(deps.get_db),token:str=Form(...),nugget_id:int=Form(...)):
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            status=0
            msg="Invalid nugget id"
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id

            if IsAccountVerified(db,login_user_id) == False:
                return {"status":0,"msg":"You need to complete your account validation before you can do this"}
            
            access_check=NuggetAccessCheck(db,login_user_id,nugget_id)
            if not access_check:
                return {"status":0,"msg":"Unauthorized access"}
                
            check_nuggets=db.query(Nuggets).filter_by(id = nugget_id).first()
            if check_nuggets:
                commentlist=db.query(NuggetsComments).filter(NuggetsComments.id == NuggetsCommentsLikes.comment_id).filter(NuggetsCommentsLikes.user_id == login_user_id,NuggetsComments.nugget_id == check_nuggets.id)
                commentlist=commentlist.filter(NuggetsComments.parent_id == None).group_by(NuggetsComments.id).order_by(NuggetsComments.modified_date.asc()).all()
                
                if commentlist:
                    count=0
                    for comment in commentlist:
                        get_cmt_likes=db.query(NuggetsCommentsLikes).filter(NuggetsCommentsLikes.comment_id == comment.id)
                        get_cmt_like=get_cmt_likes.all()
                        total_like=0
                        if get_cmt_like:
                            total_like=get_cmt_likes.count()
                            
                        result_list=[]
                        result_list.append({
                                            "comment_id":comment.id,
                                            "user_id":comment.user_id,
                                            "editable":True if comment.user_id == login_user_id else False,
                                            "name":comment.user.display_name,
                                            "profile_image":comment.user.profile_img,
                                            "comment":comment.content,
                                            "commented_date":comment.created_date,
                                            "liked":True if comment.liked > 0 else False,
                                            "like_count":total_like
                                        })
                        replyarray=[]
                        
                        if get_cmt_like:
                            replycount=0
                            for reply in get_cmt_like:
                                like=False
                                if total_like > 0:
                                    for likes in reply:
                                        if likes.user_id == login_user_id:
                                            like=True

                                replyarray.append({
                                                    "comment_id":reply.id,
                                                    "user_id":reply.user_id,
                                                    "editable":True if login_user_id == reply.user_id else False,
                                                    "name":reply.user.display_name,
                                                    "profile_image":reply.user.profile_img,
                                                    "comment":reply.content,
                                                    "commented_date":reply.created_date,
                                                    "liked":like,
                                                    "like_count":total_like
                                                })

                        result_list.append({"reply":replyarray})
                    
                    return {"status":1,"msg":"Success","comments":result_list}
                else:
                    return {"status":0,"msg":"No Comments"}
                    
            else:
                return {"status":0,"msg":"Invalid Nugget id"}
            
            
                

# 30. Add or Reply Nugget Comment
@router.post("/addnuggetcomment")
async def addnuggetcomment(db:Session=Depends(deps.get_db),token:str=Form(...),type:int=Form(None,description="1-comment,2-reply",ge=1,le=2),nugget_id:int=Form(...),
                           comment_id:int=Form(None),comment:str=Form(...)):
    
    if type == 2 and not comment_id:
        return {"status":0,"msg":"comment id required"}
    
    if token.strip() == "":
        return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
    else:
        access_token=checkToken(db,token)
        
        if access_token == False:
            return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
        else:
            status=0
            msg="Invalid nugget id"
            get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            login_user_id=get_token_details.user_id

            if IsAccountVerified(db,login_user_id) == False:
                return {"status":0,"msg":"You need to complete your account validation before you can do this"}
            
            access_check=NuggetAccessCheck(db,login_user_id,nugget_id)
            if not access_check:
                return {"status":0,"msg":"Unauthorized access"}

            check_nuggets=db.query(Nuggets).filter_by(id = nugget_id).first()
            if check_nuggets:
                nugget_comment=NuggetsComments(user_id=login_user_id,parent_id=comment_id,nugget_id=nugget_id,content=comment,created_date=datetime.now(),modified_date=datetime.now())
                db.add(nugget_comment)
                db.commit()
                
                if nugget_comment:
                    status=1
                    msg="Success"
                    result_list={}
                    result_list.update({
                                        "comment_id":nugget_comment.id,
                                        "user_id":login_user_id,
                                        "editable":True,
                                        "name":nugget_comment.user.display_name,
                                        "profile_image":nugget_comment.user.profile_image,
                                        "comment":nugget_comment.content,
                                        "commented_date":nugget_comment.created_date,
                                        "liked":False,
                                        "like_count":0
                                        })
                    if type == 1:
                        result_list.update({"reply":[]})
                    notification_type=3
                    Insertnotification(db,check_nuggets.user_id,login_user_id,notification_type,nugget_id)
                else:
                    msg="failed to add comment"       
            if status == 1:
                return {"status":status,"msg":msg,"comment":result_list}
            
            else:
                return {"status":status,"msg":msg}
                      
            

# 31. Edit Nugget Comment
@router.post("/editnuggetcomment")
async def editnuggetcomment(db:Session=Depends(deps.get_db),token:str=Form(...),comment_id:int=Form(...),comment:str=Form(...)):
                         
    return "done"



# 32. Delete Nugget Comment
@router.post("/deletenuggetcomment")
async def deletenuggetcomment(db:Session=Depends(deps.get_db),token:str=Form(...),comment_id:int=Form(...)):
                         
    return "done"






# 33. Like And Unlike Nugget Comment
@router.post("/likeandunlikenuggetcomment")
async def likeandunlikenuggetcomment(db:Session=Depends(deps.get_db),token:str=Form(...),comment_id:int=Form(...),like:int=Form(...,description="1-Like,2-Unlike",ge=1,le=2)):
                         
    return "done"




# 34. Nugget and Comment liked User List
@router.post("/nuggetandcommentlikeeduserlist")
async def nuggetandcommentlikeeduserlist(db:Session=Depends(deps.get_db),token:str=Form(...),id:int=Form(...,description="Nugget id or Comment id"),type:int=Form(...,description="1-Nugget,2-Comment",ge=1,le=2)):
                         
    return "done"




# 35. Edit Nugget
@router.post("/editnugget")
async def editnugget(db:Session=Depends(deps.get_db),token:str=Form(...),nugget_id:int=Form(...),content:str=Form(None),share_type:int=Form(...,description="1-public,2-only me,3-groups,4-individual,5-both group & individual ,6-all my friends"),
                     share_with:str=Form(None,description='{"friends":[1,2,3],"groups":[1,2,3]}')):
    
    if share_type == 3 or share_type == 4 :
        if not share_with:
            return {"status":0,"msg":"share with required"}
        
    return "done"



# # Change password 
# @router.post("/change_password")
# async def change_password(db:Session=Depends(deps.get_db), current_user:User=Depends(deps.get_current_user),*,change_password_details:schemas.ChangePassword):
   
#     if current_user:
        
#         get_user=db.query(User).filter(User.id == current_user.id,User.status == 1).first()
        
#         if get_user:
           
#             check_pwd=db.query(User).filter(User.id == get_user.id,User.status == 1,User.password == verify_password(change_password_details.current_password)).first()
#             if not check_pwd:
#                 raise HTTPException(
#                 status_code=400,
#                 detail=[{"msg":"Please,Check your Old password"}],
#                 )
            
#             get_user.password=get_password_hash(change_password_details.new_password)

#             return "Password Changed Successfully"

#         else:
#             raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"User not found"}],
#             )
#     else:
#         raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Invalid request"}],
#         )


# # Change password 
# @router.get("/view_profile/{user_id}")
# async def view_profile(db:Session=Depends(deps.get_db),*,current_user:User=Depends(deps.get_current_user),user_id:int):
   
#     if current_user:
#         get_user=user.get(db,id=user_id)
#         user_details={}
#         if get_user:
#             get_address_details=db.query(CustomerAddress).filter(CustomerAddress.user_id == user_id,CustomerAddress.status == 1).all()
#             user_address=[]
            
#             for adres in get_address_details:
  
#                 user_address.append({"address_id":adres.id,"address_type":adres.address_type,
#                                     "address_type_name":"Hospital" if adres.address_type == 1 else "Clinic" if adres.address_type == 2 else "Warehouse" if adres.address_type == 3 else None,
#                                     "address":adres.address,"city":adres.city,"state":adres.state,"pin_code":adres.pin_code})
            
#             user_details.update({"user_id":get_user.id,"name":get_user.name,"email":get_user.email if get_user.email else "",
#                                     "mobile_no":get_user.mobile_no if get_user.mobile_no else "",
#                                     "customer_address":user_address if user_address!= [] else 0,
#                                     "created_at":common_date(get_user.created_at,without_time=1)})
#             return user_details
#         else:
#             raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Invalid user"}],
#             )
    
#     else:
#         raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Invalid request"}],
#         )

# # Add Customer Address
# @router.post("/add_address")
# def add_address(db: Session = Depends(deps.get_db),current_user:User=Depends(deps.get_current_user), *,address_details:schemas.AddAddress):
#     if current_user.user_type == 3:
#         get_user=user.get(db,id=address_details.user_id)
#         if not get_user:
#             raise HTTPException(
#                 status_code=400,
#                 detail=[{"msg":"Invalid user"}],
#                 )
#         # Check City And State
#         check_city=db.query(Cities).filter(Cities.id ==address_details.city,Cities.state_id==address_details.state).first()
#         if check_city:
        
#             check_address=db.query(CustomerAddress).filter(CustomerAddress.user_id == address_details.user_id,CustomerAddress.address_type == address_details.address_type,CustomerAddress.status == 1).first()
#             if check_address:
#                 check_address.name=address_details.name
#                 check_address.email=address_details.email
#                 check_address.phone_number=address_details.mobile_no
#                 check_address.address=address_details.address
#                 check_address.city=check_city.id
#                 check_address.state=check_city.state_id
#                 check_address.pin_code=address_details.pin_code
#                 db.commit()
#                 return "Update successfully"
                
#             else:
#                 add_address=CustomerAddress(user_id=address_details.user_id,name=get_user.name,email=get_user.email,phone_number=address_details.mobile_no,
#                                             address_type=address_details.address_type,address=address_details.address,city=address_details.city,state=address_details.state,
#                                             pin_code=address_details.pin_code,status=1,created_at=datetime.now(settings.tz_NY))
#                 db.add(add_address)
#                 db.commit()
#                 return "Add Address Successfully."
#         else:
#             raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Check your City and State"}],
#             )
#     else:
#         raise HTTPException(
#         status_code=400,
#         detail=[{"msg":"Invalid user"}],
#         )



# # List User
# @router.post("/list users")
# async def list_users(db:Session=Depends(deps.get_db), current_user:User=Depends(deps.get_current_user),*,page:int=1,size:int=10,user_type:int=Form(...,description="2-vendor,3-customer",ge=2,le=3),name:str=Form(None),email:str=Form(None),mobile_no:str=Form(None)):
   
#     if current_user.user_type == 1:
#         get_user_list=db.query(User).filter(User.user_type == user_type,User.status == 1)

#         if name:
#             get_user_list=get_user_list.filter(User.name.like(name+"%"))
#         if email:
#             get_user_list=get_user_list.filter(User.email.like(email+"%"))

#         if mobile_no:
#             get_user_list=get_user_list.filter(User.mobile_no.like(mobile_no+"%"))

#         get_user_list=get_user_list.order_by(User.status.asc())

#         get_user_list_count=get_user_list.count()


#         limit,offset=pagination(get_user_list_count,page,size)

#         get_user_list=get_user_list.limit(limit).offset(offset).all()
#         list_of_user=[]
#         for user in get_user_list:
#             list_of_user.append({"user_id":user.id,"name":user.name if user.name else "","email":user.email if user.email else "",
#                                 "mobile_no":user.mobile_no if user.mobile_no else "","user_type":user.user_type,
#                                 "user_type_name":"Vendor" if user.user_type == 2 else "Customer" if user.user_type == 3 else ""})
        
#         return paginate(page,size,list_of_user,get_user_list_count)
#     else:
#         raise HTTPException(
#         status_code=400,
#         detail=[{"msg":"Invalid user"}],
#         )




# @router.delete("/delete_user")
# def delete_user(*,db: Session = Depends(deps.get_db),current_user: User = Depends(deps.get_current_user),user_id:int=Form(...)):
#     if current_user.user_type == 1:

#         check_user=db.query(User).filter(User.id == user_id,User.status == 1).first()
    
#         if check_user:
#             check_user.status = -1
#             db.commit()
#             return "Deleted Successfully"

#         else:
#             raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Invalid user"}])
    
#     else:
#         raise HTTPException(
#             status_code=400,
#             detail=[{"msg":"Invalid user"}])