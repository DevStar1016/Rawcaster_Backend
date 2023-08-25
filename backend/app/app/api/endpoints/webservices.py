from fastapi import APIRouter, Depends, Form, File, UploadFile, BackgroundTasks
from app.models import *
from app.core import config
from app.core.security import *
from typing import List
from app.utils import *
from app.api import deps
import datetime
from sqlalchemy.orm import Session,aliased,joinedload
from datetime import datetime, date
from sqlalchemy import func, case, text, extract
import re
import base64
import json
import pytz
import boto3
from urllib.parse import urlparse
from .webservices_2 import croninfluencemember
import ast
from mail_templates.mail_template import *
from moviepy.video.io.VideoFileClip import VideoFileClip
import subprocess
from .chime_chat import *

router = APIRouter()


access_key = config.access_key
access_secret = config.access_secret
bucket_name = config.bucket_name


@router.post("/test")
async def test():
    return 'Done,Without db connection'

@router.post("/fetch_data")
async def fetch_data(db: Session = Depends(deps.get_db)):
    user=db.query(User).filter(User.status == 1)
    
    return user.first()


# 1 Signup User
@router.post("/signup")
async def signup(
    db: Session = Depends(deps.get_db),
    signup_type: str = Form(1, description="1-Email,2-Phone Number"),
    first_name: str = Form(None, max_length=100),
    last_name: str = Form(None, max_length=100),
    display_name: str = Form(None, max_length=100),
    gender: str = Form(None, description="1-male,2-female"),
    other_gender:str=Form(None),
    dob: Any = Form(None),
    email_id: str = Form(None, max_length=100, description="email or mobile number"),
    country_code: str = Form(None),
    country_id: str = Form(None),
    mobile_no: str = Form(None),
    password: str = Form(None),
    geo_location: str = Form(None),
    latitude: str = Form(None),
    longitude: str = Form(None),
    ref_id: str = Form(None),
    auth_code: str = Form(None, description="SALT + email_id"),
    device_id: str = Form(None),
    push_id: str = Form(None),
    device_type: str = Form(None),
    voip_token: str = Form(None),
    app_type: str = Form(None, description="1-Android,2-IOS"),
    signup_social_ref_id: str = Form(None),
    login_from: str = Form(None),
):
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth Code is missing"}

    elif not signup_type:
        return {"status": 0, "msg": "signup type is missing"}

    elif not signup_type.isnumeric():
        return {"status": 0, "msg": "Invalid signup type"}

    elif first_name == None or first_name.strip() == "":
        return {"status": 0, "msg": "Please provide your first name"}

    elif re.search("/[^A-Za-z0-9]/", first_name):
        return {"status": 0, "msg": "Please provide valid name"}

    elif email_id == None or email_id.strip() == "":
        return {"status": 0, "msg": "Please provide your valid email or phone number"}

    elif password == None or password.strip() == "":
        return {"status": 0, "msg": "Password is missing"}

    elif dob and is_date(dob) == False:
        return {"status": 0, "msg": "Invalid Date"}

    else:
        mobile_no = None
        auth_text = email_id.strip() if email_id else None
        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}

        else:
            signup_type = int(signup_type)
            email_id = email_id.strip()
            check_email_or_mobile = EmailorMobileNoValidation(email_id)

            if check_email_or_mobile["status"] == 1:
                if check_email_or_mobile["type"] == signup_type:
                    if signup_type == 1:
                        email_id = check_email_or_mobile["email"]
                        mobile_no = None

                    elif signup_type == 2:
                        email_id = None
                        mobile_no = check_email_or_mobile["mobile"]
                else:
                    if signup_type == 1:
                        return {"status": 0, "msg": "Email address is not valid"}

                    elif signup_type == 2:
                        return {"status": 0, "msg": "Phone number is not valid"}

            else:
                if signup_type == 1:
                    return {"status": 0, "msg": "Email ID is not valid"}
                if signup_type == 2:
                    return {"status": 0, "msg": "Phone number is not valid"}

            check_user = (
                db.query(User)
                .filter(
                    or_(
                        and_(User.email_id == email_id, User.email_id != None),
                        and_(User.mobile_no == mobile_no, User.mobile_no != None),
                    ),
                    User.status != 4,
                )
                .first()
            )
            if check_user:
                if check_user.status == 0:
                    send_otp = await SendOtp(db, check_user.id, signup_type)

                    # Generate token
                    user_id = check_user.id
                    characters = "".join(
                        random.choices(string.ascii_letters + string.digits, k=8)
                    )
                    token_text = ""
                    dt = str(int(datetime.datetime.utcnow().timestamp()))

                    salt_token = token_text + str(user_id) + str(characters) + str(dt)

                    salt = st.SALT_KEY
                    hash_code = str(token_text) + str(salt)

                    user_id = check_user.id
                    exptime = int(dt) + int(dt)

                    paylod = {
                        "iat": dt,
                        "iss": "localhost",
                        "exp": exptime,
                        "token": token_text,
                    }

                    # token = jwt.encode(paylod, st.SECRET_KEY)
                    userIP = get_ip()

                    add_token = ApiTokens(
                        user_id=user_id,
                        token=salt_token,
                        created_at=datetime.datetime.utcnow(),
                        renewed_at=datetime.datetime.utcnow(),
                        validity=1,
                        device_type=login_from,
                        app_type=app_type,
                        device_id=device_id,
                        push_device_id=push_id,
                        voip_token=voip_token,
                        device_ip=userIP,
                        status=1,
                    )
                    db.add(add_token)
                    db.commit()

                    return {
                        "status": 1,
                        "acc_verify_status": 0,
                        "alt_token_id": add_token.id,
                        "otp_ref_id": send_otp,
                        "signup_type": int(signup_type),
                        "msg": "Verification Pending, Redirect to OTP Verify Page",
                        "first_time": 1,
                        "remaining_seconds": 90,
                        "email_id": email_id if signup_type == 1 else mobile_no,
                    }

                elif signup_type == 1:
                    return {
                        "status": 2,
                        "msg": "You are already registered with this email address. Please login",
                    }

                elif signup_type == 2:
                    return {
                        "status": 2,
                        "msg": "You are already registered with this phone number. Please login",
                    }

            else:
                # New User Register
                userIP = get_ip()
                location = geo_location
                if geo_location == None or geo_location == "" or len(geo_location) < 4:
                    location_details = FindLocationbyIP(userIP)
                    if location_details["status"] and location_details["status"] == 1:
                        location = (
                            location_details["country"]
                            if location_details["country"]
                            else "India"
                        )

                        latitude = location_details["latitude"]
                        longitude = location_details["longitude"]

                if mobile_no:
                    mobile_check = CheckMobileNumber(db, mobile_no, location)

                    if not mobile_check:
                        return {
                            "status": 0,
                            "msg": "Unable to signup with mobile number",
                        }
                    else:
                        if mobile_check["status"] and mobile_check["status"] == 1:
                            country_code = mobile_check["country_code"]
                            country_id = mobile_check["country_id"]
                            mobile_no = mobile_check["mobile_no"]
                        else:
                            return mobile_check

                result = hashlib.sha1(password.encode())
                hashed_password = result.hexdigest()

                add_user = User(
                    email_id=email_id,
                    is_email_id_verified=0,
                    password=hashed_password,
                    first_name=first_name,
                    last_name=last_name,
                    display_name=display_name,
                    gender=gender if gender != None else None,
                    dob=dob,
                    country_code=country_code,
                    mobile_no=mobile_no,
                    cover_image=defaultimage("cover_img"),
                    is_mobile_no_verified=0,
                    country_id=country_id,
                    user_code=None,
                    other_gender=other_gender,
                    signup_type=signup_type,
                    profile_img=defaultimage("profile_img"),
                    signup_social_ref_id=signup_social_ref_id,
                    geo_location=geo_location,
                    latitude=latitude,
                    longitude=longitude,
                    created_at=datetime.datetime.utcnow(),
                    status=0,
                )
                db.add(add_user)
                db.commit()
                db.refresh(add_user)
                if add_user:
                    user_ref_id = GenerateUserRegID(add_user.id)

                    # update ref id
                    get_user = (
                        db.query(User)
                        .filter(User.id == add_user.id)
                        .update({"user_ref_id": user_ref_id})
                    )
                    db.commit()

                    # Set Default user settings
                    user_settings_model = UserSettings(
                        user_id=add_user.id,
                        online_status=1,
                        friend_request="000",
                        nuggets="000",
                        events="000",
                        status=1,
                    )
                    db.add(user_settings_model)
                    db.commit()
                    db.refresh(user_settings_model)

                    # Set Default Friend Group
                    friends_group = FriendGroups(
                        group_name="My Fans",
                        group_icon=defaultimage("group_icon"),
                        created_by=add_user.id,
                        created_at=datetime.datetime.utcnow(),
                        status=1,
                        chat_enabled=0,
                    )
                    db.add(friends_group)
                    db.commit()
                    db.refresh(friends_group)

                    channel_arn = None
                    user_arn = None
                    try:
                        # Add User in Chime Channel
                        create_chat_user = chime_chat.createchimeuser(add_user.email_id)
                        if create_chat_user["status"] == 1:
                            user_arn = create_chat_user["data"][
                                "ChimeAppInstanceUserArn"
                            ]
                            # Update User Chime ID
                            update_user = (
                                db.query(User)
                                .filter(User.id == get_user.id)
                                .update({"chime_user_id": user_arn})
                            )
                            db.commit()

                            # Add Channels
                            chime_bearer = user_arn
                            group_name = "My Fans"
                            channel_response = create_channel(chime_bearer, group_name)

                            channel_arn = (
                                channel_response["ChannelArn"]
                                if channel_response
                                else None
                            )

                    except Exception as e:
                        print(e)

                    referred_id = 0
                    # Add Friend Automatically From Referral

                    if ref_id:
                        friend_ref_code = base64.b64decode(ref_id).decode()

                        referrer_ref_id = friend_ref_code.split("//")
                        if len(referrer_ref_id) == 2:
                            referred_user = (
                                db.query(User)
                                .filter(
                                    User.user_ref_id == referrer_ref_id[0],
                                    User.status == 1,
                                )
                                .first()
                            )
                            if referred_user:
                                referred_id = referred_user.id
                                # update referrer id
                                update_referrer = (
                                    db.query(User)
                                    .filter(User.id == add_user.id)
                                    .update(
                                        {
                                            "referrer_id": referred_user.id,
                                            "invited_date": referrer_ref_id[1],
                                        }
                                    )
                                )
                                db.commit()

                                ref_friend = MyFriends(
                                    sender_id=referred_user.id,
                                    receiver_id=add_user.id,
                                    request_date=datetime.datetime.utcnow(),
                                    request_status=1,
                                    status_date=None,
                                    status=1,
                                )
                                db.add(ref_friend)
                                db.commit()

                                get_friend_group = (
                                    db.query(FriendGroups)
                                    .filter(
                                        FriendGroups.group_name == "My Fans",
                                        FriendGroups.created_by == referred_user.id,
                                    )
                                    .first()
                                )

                                if get_friend_group:
                                    add_follow_user = FollowUser(
                                        follower_userid=add_user.id,
                                        following_userid=referred_user.id,
                                        created_date=datetime.datetime.utcnow(),
                                    )
                                    db.add(add_follow_user)
                                    db.commit()

                                    # Check FriendGroupMembers
                                    friend_group_member = (
                                        db.query(FriendGroupMembers)
                                        .filter(
                                            FriendGroupMembers.group_id
                                            == get_friend_group.id,
                                            FriendGroupMembers.user_id
                                            == referred_user.id,
                                        )
                                        .all()
                                    )

                                    if not friend_group_member:
                                        add_friend_group_member = FriendGroupMembers(
                                            group_id=get_friend_group.id,
                                            user_id=add_user.id,
                                            added_date=datetime.datetime.utcnow(),
                                            added_by=referred_user.id,
                                            is_admin=0,
                                            disable_notification=1,
                                            status=1,
                                        )
                                        db.add(add_friend_group_member)
                                        db.commit()

                                        # Add Members in Channel
                                        channel_arn = channel_arn
                                        chime_bearer = user_arn
                                        member_id = (
                                            list(referred_user.chime_user_id)
                                            if referred_user.chime_user_id
                                            else None
                                        )
                                        try:
                                            addmembers(
                                                channel_arn, chime_bearer, member_id
                                            )
                                        except Exception as e:
                                            print(f"Referrer:{e}")

                    # Referral Auto Add Friend Ends
                    type = 2
                    rawcaster_support_id = GetRawcasterUserID(db, type)

                    if rawcaster_support_id > 0 and referred_id != rawcaster_support_id:
                        add_my_friends = MyFriends(
                            sender_id=rawcaster_support_id,
                            receiver_id=add_user.id,
                            request_date=datetime.datetime.utcnow(),
                            request_status=1,
                            status_date=None,
                            status=1,
                        )
                        db.add(add_my_friends)
                        db.commit()

                    result = hashlib.sha1(password.encode())
                    password = result.hexdigest()

                    if email_id == "" or email_id == None:
                        email_id = mobile_no

                    # Send OTP for Email or Mobile number Verification

                    send_otp = await SendOtp(db, add_user.id, signup_type)

                    if send_otp:
                        otp_ref_id = send_otp
                    else:
                        return {"status": 0, "msg": "Failed to send OTP"}

                    # Generate token
                    user_id = add_user.id

                    characters = "".join(
                        random.choices(string.ascii_letters + string.digits, k=8)
                    )
                    token_text = ""
                    dt = str(int(datetime.datetime.utcnow().timestamp()))

                    salt_token = token_text + str(user_id) + str(characters) + str(dt)
                    salt = st.SALT_KEY
                    exptime = int(dt) + int(dt)

                    userIP = get_ip()

                    add_token = ApiTokens(
                        user_id=user_id,
                        token=salt_token,
                        created_at=datetime.datetime.utcnow(),
                        renewed_at=datetime.datetime.utcnow(),
                        validity=1,
                        device_type=login_from,
                        app_type=app_type,
                        device_id=device_id,
                        push_device_id=push_id,
                        voip_token=voip_token,
                        device_ip=userIP,
                        status=1,
                    )
                    db.add(add_token)
                    db.commit()
                    db.refresh(add_token)

                    return {
                        "status": 1,
                        "msg": "Success",
                        "email_id": email_id,
                        "alt_token_id": add_token.id,
                        "otp_ref_id": otp_ref_id,
                        "user_id": add_user.id,
                        "acc_verify_status": 0,
                        "first_time": 1,
                        "remaining_seconds": 90,
                        "signup_type": int(signup_type),
                    }  # First Time (1 - New to rawcaster, 0 - existing user)

                else:
                    return {"status": 0, "msg": "Failed to add User"}


# 2 - Signup Verification by OTP
@router.post("/signupverify")
async def signupverify(
    db: Session = Depends(deps.get_db),
    auth_code: str = Form(None, description="SALT + otp_ref_id"),
    otp_ref_id: str = Form(None, description="From service no. 1"),
    otp: str = Form(None),
    otp_flag: str = Form(None),
    alt_token_id: str = Form(None),
):
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth Code is missing"}
    elif otp_ref_id == None or otp_ref_id.strip() == "":
        return {"status": 0, "msg": "Reference id is missing"}
    elif otp == None:
        return {"status": 0, "msg": "OTP is missing"}

    else:
        otp_ref_id = otp_ref_id.strip()
        otp_flag = "email" if not otp_flag else otp_flag
        otp = otp
        auth_code = auth_code.strip()

        auth_text = otp_ref_id

        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            get_otp_log = (
                db.query(OtpLog)
                .filter(OtpLog.id == otp_ref_id, OtpLog.otp == otp, OtpLog.status == 1)
                .first()
            )
            if not get_otp_log:
                return {"status": 0, "msg": "OTP is invalid"}
            else:
                get_otp_log.status = 0
                db.commit()

                user_update = 0
                if otp_flag == "sms":
                    update_user = (
                        db.query(User)
                        .filter(User.id == get_otp_log.user_id)
                        .update({"is_mobile_no_verified": 1, "status": 1})
                    )
                    user_update = get_otp_log.user_id
                    db.commit()
                else:
                    update_user = (
                        db.query(User)
                        .filter(User.id == get_otp_log.user_id)
                        .update({"is_email_id_verified": 1, "status": 1})
                    )
                    db.commit()

                    user_update = get_otp_log.user_id
                if update_user:
                    get_user = (
                        db.query(User).filter(User.id == get_otp_log.user_id).first()
                    )

                    if get_user:
                        if get_user.referrer_id != None or get_user.referrer_id != "":
                            change_referral_date = ChangeReferralExpiryDate(
                                db, get_user.referrer_id
                            )

                        if get_user.is_email_id_verified == 1:
                            to_mail = get_user.email_id
                            subject = "Welcome to Rawcaster"
                            content = welcome_mail()
                            body = mail_content(content)

                            try:
                                mail_send = await send_email(db, to_mail, subject, body)
                            except:
                                pass

                        if alt_token_id:
                            # Get Token
                            get_token = (
                                db.query(ApiTokens)
                                .filter(ApiTokens.id == alt_token_id)
                                .first()
                            )
                            if get_token:
                                username = (
                                    str(get_user.mobile_no)
                                    if get_user.mobile_no
                                    else None
                                    if otp_flag == "sms"
                                    else get_user.email_id
                                )

                                generate_access_token = await logins(
                                    db,
                                    username,
                                    get_user.password,
                                    get_token.device_type,
                                    get_token.device_id,
                                    get_token.push_device_id,
                                    get_token.device_type,
                                    get_token.voip_token,
                                    get_token.app_type,
                                    0,
                                )
                                return generate_access_token

                    return {
                        "status": 1,
                        "msg": "Your account has been verified successfully.",
                    }

                else:
                    return {
                        "status": 0,
                        "msg": "Account verification failed. Please try again",
                    }


# 3 - Resend OTP


@router.post("/resendotp")
async def resendotp(
    db: Session = Depends(deps.get_db),
    auth_code: str = Form(None, description="SALT + otp_ref_id"),
    otp_ref_id: str = Form(None),
    token: str = Form(None),
    otp_flag: str = Form(None),
):
    if otp_flag and otp_flag.strip() == "" or otp_flag == None:
        otp_flag = "email"

    auth_text = otp_ref_id if otp_ref_id != None else "Rawcaster"
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth code is missing"}

    if checkAuthCode(auth_code, auth_text) == False:
        return {"status": 0, "msg": "Authentication failed!"}

    else:
        otp_ref_id = otp_ref_id if otp_ref_id else None

        if not otp_ref_id:
            if not token and token.strip() == "":
                return {
                    "status": 0,
                    "msg": "Sorry! your login session expired. please login again.",
                }

            else:
                login_user_id = 0
                access_token = checkToken(db, token)

                if access_token == False:
                    return {
                        "status": -1,
                        "msg": "Sorry! your login session expired. please login again.",
                    }
                else:
                    get_token_details = (
                        db.query(ApiTokens)
                        .filter(ApiTokens.token == access_token)
                        .first()
                    )
                    login_user_id = get_token_details.user_id

                otp = generateOTP()
                otp_time = datetime.datetime.utcnow()

                add_model = OtpLog(
                    user_id=login_user_id,
                    otp=otp,
                    otp_type=1,
                    created_at=otp_time,
                    status=1,
                )
                db.add(add_model)
                db.commit()
                if add_model:
                    otp_ref_id = add_model.id

                # return {"status":1,"otp_ref_id":otp_ref_id,"msg":"Success"}

        get_otp_log = (
            db.query(OtpLog).filter(OtpLog.id == otp_ref_id, OtpLog.status == 0).first()
        )

        if not get_otp_log:
            return {"status": 0, "msg": "Invalid request!"}
        else:
            otp_time = datetime.datetime.utcnow()

            get_otp_log.created_date = otp_time
            get_otp_log.status = 1
            db.commit()

            otp = get_otp_log.otp
            mail_sub = ""
            mail_msg = ""
            if get_otp_log.otp_type == 1:  # if signup
                mail_sub = "Rawcaster - Account Verification"
                mail_msg = "Your OTP for Rawcaster account verification is "

            elif get_otp_log.otp_type == 3:  # if forgot password
                mail_sub = "Rawcaster - Password Reset"
                mail_msg = "Your OTP for Rawcaster account password reset is "

            if otp_flag == "sms":
                to = f"{get_otp_log.user.country_code}{get_otp_log.user.mobile_no}"
                sms = f"{otp} is your OTP for Rawcaster. PLEASE DO NOT SHARE THE OTP WITH ANYONE."
                if to:
                    try:
                        send_sms = sendSMS(to, sms)
                    except:
                        pass
            else:
                base_url = inviteBaseurl()
                code = EncryptandDecrypt(str(otp))
                link = f"{base_url}rawadmin/site/accountverify?hash={code}"
                # Email

                to = get_otp_log.user.email_id
                subject = mail_sub
                content = ""
                content += f'<table width="600" border="0" align="center" cellpadding="10" cellspacing="0" style="border: 1px solid #e8e8e8;"><tr><td>'
                content += f"Hi, Greetings from Rawcaster<br /><br />"
                content += f"{mail_msg} <b> {otp} </b><br />"

                if get_otp_log.otp_type == 1:
                    content += (
                        f"Click this link to validate your account {link} <br /><br />"
                    )
                else:
                    content += "<br />"

                content += 'Regards,<br />Administration Team<br /><a href="https://rawcaster.com/">Rawcaster.com</a> LLC'
                content += "</td></tr></table>"

                body = mail_content(content)
                try:
                    send_mail = await send_email(db, to, subject, body)
                except:
                    pass

            remaining_seconds = 0
            target_time = datetime.datetime.timestamp(otp_time) + 120
            current_time = datetime.datetime.utcnow().timestamp()

            if current_time < target_time:
                remaining_seconds = int(target_time - current_time)

            reply_msg = f"Please enter the One Time Password (OTP) sent to {to}"
            return {
                "status": 1,
                "msg": reply_msg,
                "email_id": to,
                "otp_ref_id": int(otp_ref_id),
                "remaining_seconds": remaining_seconds,
            }


# # 3 - Resend OTP  (PHP Code)

# @router.post("/resendotp")
# async def resendotp(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),otp_ref_id:str=Form(None),token:str=Form(None),otp_flag:str=Form(None)):
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
#                 otp_time=datetime.datetime.utcnow()
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

#                 otp_time=datetime.datetime.utcnow()
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
#                 current_time=datetime.datetime.utcnow()
#                 if current_time < target_time:
#                     remaining_seconds=target_time - current_time

#                 reply_msg=f'Please enter the One Time Password (OTP) sent to {to}'
#                 return {"status":1,"msg":reply_msg,"email":to,"otp_ref_id":otp_ref_id,"remaining_seconds":remaining_seconds}

#             # else:
#             #     return {"status" :0, "msg" :"Failed to resend otp, please try again"}


# 4 - Login
@router.post("/login")
async def login(
    db: Session = Depends(deps.get_db),
    auth_code: str = Form(None, description="SALT + username"),
    username: str = Form(None, description="Email ID"),
    password: str = Form(None),
    device_id: str = Form(None),
    push_id: str = Form(None),
    device_type: str = Form(None, description="1-> Android,  2-> IOS, 3->Web"),
    voip_token: str = Form(None),
    app_type: str = Form(None, description="1-> Android, 2-> IOS"),
    login_from: str = Form(None),
):
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Authcode is missing"}

    if username == None or username.strip() == "":
        return {"status": 0, "msg": "UserName is missing"}

    if password == None or password.strip() == "":
        return {"status": 0, "msg": "Password is missing"}

    if app_type and not app_type.isnumeric():
        return {"status": 0, "msg": "Invalid App Type"}

    elif device_type and not device_type.isnumeric():
        return {"status": 0, "msg": "Invalid device type"}

    auth_text = username.strip()
    if checkAuthCode(auth_code.strip(), auth_text) == False:
        return {"status": 0, "msg": "Authentication failed!"}

    else:
        app_type = int(app_type) if app_type else None
        device_type = int(device_type) if device_type else None

        if username.strip() != "" and password.strip() != "":
            password = hashlib.sha1(password.encode("utf-8")).hexdigest()

            generate_access_token = await logins(
                db,
                username,
                password,
                device_type,
                device_id,
                push_id,
                login_from,
                voip_token,
                app_type,
                0,
            )
            return generate_access_token

        else:
            return {"status": 0, "msg": "Please enter a valid username and password"}


# 5 - Logout
@router.post("/logout")
async def logout(db: Session = Depends(deps.get_db), token: str = Form(None)):
    if token == None or token.strip() == "":
        return {"status": -1, "msg": "Sorry your access token missing!"}
    else:
        access_token = checkToken(db, token)
        if access_token == False:
            return {"status": -1, "msg": "Sorry your access token invalid!"}
        else:
            get_token_details = (
                db.query(ApiTokens.device_type,ApiTokens.user_id)
                .filter(ApiTokens.token == access_token.strip())
                .first()
            )
            if get_token_details:
                if get_token_details.device_type == 2:
                    user_id = get_token_details.user_id
                    
                    # Update Friend Chat - Last Logout time upadte
                    update_friend_sender_chat = (
                        db.query(FriendsChat)
                        .filter(FriendsChat.sender_id == user_id)
                        .update(
                            {
                                "sender_delete": 1,
                                "sender_deleted_datetime": datetime.datetime.utcnow(),
                            }
                        )
                    )
                    update_friend_receiver_chat = (
                        db.query(FriendsChat)
                        .filter(FriendsChat.receiver_id == user_id)
                        .update(
                            {
                                "receiver_delete": 1,
                                "receiver_deleted_datetime": datetime.datetime.utcnow(),
                            }
                        )
                    )
                    db.commit()

                # Delete Token
                delete_token = (
                    db.query(ApiTokens)
                    .filter(ApiTokens.token == access_token.strip())
                    .delete()
                )
                db.commit()
                if delete_token:
                    return {"status": 1, "msg": "Success"}

                else:
                    return {"status": 0, "msg": "Failed to Logout"}

            else:
                return {"status": 0, "msg": "Success"}


# 6 - Forgot Password
@router.post("/forgotpassword")
async def forgotpassword(
    db: Session = Depends(deps.get_db),
    username: str = Form(None, description="Email ID / Mobile Number"),
    auth_code: str = Form(None, description="SALT + username"),
):
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth Code is missing"}

    elif username == None or username.strip() == "":
        return {"status": 0, "msg": "User name is missing"}

    else:
        username = username.strip()
        auth_code = auth_code.strip()

        auth_text = username
        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            get_user = (
                db.query(User.id,User.status,User.country_code,User.mobile_no,User.email_id)
                .filter(or_(User.email_id == username, User.mobile_no.like(username)))
                .first()
            )

            if not get_user:
                return {
                    "status": 0,
                    "msg": "If the email/phone number is registered, you will receive an email/SMS in your inbox shortly with further details on how to reset your password.",
                }

            elif get_user.status == 4:  # Account deleted
                return {"status": 0, "msg": "Your account has been removed"}

            elif get_user.status == 3:  # Admin Blocked user!
                return {"status": 0, "msg": "Your account is currently blocked!"}

            elif get_user.status == 2:  # Admin Blocked user!
                return {"status": 0, "msg": "Your account is currently suspended!"}

            else:  # account not verified or account active
                otp = generateOTP()
                otp_time = datetime.datetime.utcnow()
                otp_ref_id = ""
                remaining_seconds = 0

                get_otp = (
                    db.query(OtpLog)
                    .filter_by(user_id=get_user.id, otp_type=3)
                    .order_by(OtpLog.id.desc())
                    .first()
                )
                if get_otp:
                    get_otp.otp = otp
                    get_otp.created_at = otp_time
                    get_otp.status = 1
                    db.commit()    

                    otp_ref_id = get_otp.id
                else:
                    add_otp_log = OtpLog(
                        user_id=get_user.id,
                        otp=otp,
                        otp_type=3,
                        created_at=otp_time,
                        status=1,
                    )
                    db.add(add_otp_log)
                    db.commit()
                    db.refresh(add_otp_log)
                    
                    if add_otp_log:
                        otp_ref_id = add_otp_log.id

                target_time = otp_time.timestamp() + 120
                if otp_time.timestamp() < target_time:
                    remaining_seconds = target_time - otp_time.timestamp()
                msg = ""
                if username.isnumeric():
                    to = (
                        f"{get_user.country_code}{get_user.mobile_no}"
                        if get_user.mobile_no
                        else None
                    )
                    sms = f"{otp} is your OTP for Rawcaster. PLEASE DO NOT SHARE THE OTP WITH ANYONE."
                    msg = "A one time passcode (OTP) has been sent to the phone number you provided"
                    # Send SMS
                    if to:
                        try:
                            send_sms = sendSMS(to, sms)
                        except:
                            pass

                elif check_mail(username) == True:
                    to = get_user.email_id
                    subject = "Rawcaster - Reset Password"
                    content = ""
                    content += "<table width='600' border='0' align='center' cellpadding='10' cellspacing='0' style='border: 1px solid #e8e8e8;'><tr><td> "
                    content += "Hi, Greetings from Rawcaster<br /><br />"
                    content += f"Your OTP for Rawcaster account password reset is : <b> {otp } </b><br /><br />"
                    content += 'Regards,<br />Administration Team<br /><a href="https://rawcaster.com/">Rawcaster.com</a> LLC'
                    content += "</td></tr></table>"

                    body = mail_content(content)
                    try:
                        send_mail = await send_email(db, to, subject, body)
                    except:
                        pass

                    msg = "A one time passcode (OTP) has been sent to the email address you provided"

                return {
                    "status": 1,
                    "msg": msg,
                    "otp_ref_id": otp_ref_id,
                    "remaining_seconds": 90,
                }  # remaining_seconds


# 7 - Verify OTP and Reset Password
@router.post("/verifyotpandresetpassword")
async def verifyotpandresetpassword(
    db: Session = Depends(deps.get_db),
    otp_ref_id: str = Form(None),
    otp: str = Form(None),
    new_password: str = Form(None, min_length=5),
    confirm_password: str = Form(None, min_length=5),
    device_id: str = Form(None),
    push_id: str = Form(None, description="FCM  or APNS"),
    device_type: str = Form(None),
    auth_code: str = Form(None, description="SALT + otp_ref_id"),
):
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth Code is missing"}
    elif otp_ref_id == None:
        return {"status": 0, "msg": "Reference Id is missing"}
    elif otp == None:
        return {"status": 0, "msg": "OTP is missing"}
    elif new_password == None or new_password.strip() == "":
        return {"status": 0, "msg": "New Password is missing"}

    elif (
        confirm_password == None
        or new_password.strip() == ""
        or confirm_password.strip() == ""
    ):
        return {"status": 0, "msg": "Confirm Password is missing"}

    elif new_password.strip() != confirm_password.strip():
        return {"status": 0, "msg": "New & Confirm Password must be same"}

    else:
        auth_code = auth_code.strip()
        auth_text = otp_ref_id

        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            get_otp_log = (
                db.query(OtpLog)
                .filter(OtpLog.id == otp_ref_id, OtpLog.otp == otp)
                .first()
            )

            if not get_otp_log:
                return {"status": 0, "msg": "OTP is invalid"}

            else:
                new_password = hashlib.sha1(new_password.encode()).hexdigest()

                if (
                    get_otp_log.user.password and new_password
                ) == get_otp_log.user.password:
                    update = True
                else:
                    update = (
                        db.query(User)
                        .filter(User.id == get_otp_log.user_id)
                        .update(
                            {
                                "status": 1,
                                "is_email_id_verified": 1,
                                "password": new_password,
                            }
                        )
                    )
                    db.commit()

                if update:
                    get_otp_log.status = 0
                    db.commit()
                    return {
                        "status": 1,
                        "msg": "Your password has been updated successfully",
                    }
                else:
                    return {
                        "status": 0,
                        "msg": "Password update failed. Please try again",
                    }


# 8 - Change Password
@router.post("/changepassword")
async def changepassword(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    old_password: str = Form(None),
    new_password: str = Form(None),
    confirm_password: str = Form(None),
    auth_code: str = Form(None, description="SALT + token"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth code is missing"}
    elif old_password == None or old_password.strip() == "":
        return {"status": 0, "msg": "Old Password is missing"}
    elif new_password == None or new_password.strip() == "":
        return {"status": 0, "msg": "New Password is missing"}
    elif auth_code == None or auth_code.strip() == "":
        return {"status": -1, "msg": "Auth Code is missing"}
    elif confirm_password == None or confirm_password.strip() == "":
        return {"status": 0, "msg": "Confirm password is missing"}

    else:
        auth_text = token.strip()
        access_token = checkToken(db, auth_text)

        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }
            else:
                get_token_details = (
                    db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
                )

                login_user_id = get_token_details.user_id if get_token_details else None

                if old_password.strip() == "":
                    return {"status": 0, "msg": "Current password can not be empty"}

                if new_password.strip() == "":
                    return {"status": 0, "msg": "New password can not be empty"}

                if confirm_password.strip() == "":
                    return {"status": 0, "msg": "Confirm password can not be empty"}

                if new_password != confirm_password:
                    return {
                        "status": 0,
                        "msg": "New password and Confirm password should be same",
                    }

                else:
                    get_user = db.query(User).filter(User.id == login_user_id).first()
                    old_pwd = hashlib.sha1(old_password.encode()).hexdigest()

                    if get_user.password != old_pwd:
                        return {"status": 0, "msg": "Current password is wrong"}

                    else:
                        # Update Password
                        new_pwd = hashlib.sha1(new_password.encode())
                        
                        get_user.password = new_pwd.hexdigest()
                        db.commit()
                        
                        return {
                            "status": 1,
                            "msg": "Successfully updated new password",
                        }
                        


# 9 - Get country list
@router.post("/getcountylist")
async def getcountylist(db: Session = Depends(deps.get_db)):
    get_countries = (
        db.query(Country.id,Country.name,Country.country_code,Country.img).filter_by(status=1).order_by(Country.name.asc()).all()
    )
    if get_countries:
        country_list = []
        for place in get_countries:
            country_list.append(
                {
                    "id": place.id,
                    "name": place.name if place.name else "",
                    "phone_code": place.country_code if place.country_code else "",
                    "image": place.img if place.img else "",
                }
            )
        return {"status": 1, "msg": "Success", "country_list": country_list}
    else:
        return {"status": 0, "msg": "No result found!"}


# 10 - Contact us
@router.post("/contactus")
async def contactus(
    db: Session = Depends(deps.get_db),
    name: str = Form(None),
    email_id: str = Form(None),
    subject: str = Form(None),
    message: str = Form(None),
    auth_code: str = Form(None, description="SALT + email_id"),
):
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth Code is missing"}

    elif name == None or name.strip() == "":
        return {"status": 0, "msg": "Name is missing"}

    elif email_id == None or email_id.strip() == "":
        return {"status": 0, "msg": "Email id is missing"}

    elif subject == None or subject.strip() == "":
        return {"status": 0, "msg": "Subject is missing"}

    elif message == None or message.strip() == "":
        return {"status": 0, "msg": "Message is missing"}

    else:
        auth_text = email_id.strip()
        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}

        else:
            to_mail = "support@rawcaster.com"
            subject = f"New enquiry received from {name}"
            content = f'<table width="600" border="0" align="center" cellpadding="10" cellspacing="0" style="border: 1px solid #e8e8e8;"> <tr><th> Name : </th><td> {name} </td></tr> <tr><th> Email id : </th><td> {email_id} </td></tr> <tr><th> Subject : </th><td> {subject} </td></tr> <tr><th> Message : </th><td> {message} </td></tr> </table>'
            body = mail_content(content)

            try:
                send_mail = await send_email(db, to_mail, subject, body)
            except Exception as e:
                return {
                    "status": 0,
                    "msg": f"Something went wrong.Please Try Again later:{e}",
                }
            return {
                "status": 1,
                "msg": "Thank you for contacting us. we will get back to you soon.",
            }


def user_profile(db, id):
    get_user = db.query(User).filter(User.id == id).first()

    if get_user:
        get_account_status=db.query(VerifyAccounts).filter(VerifyAccounts.user_id == get_user.id).first()
        
        followers_count = db.query(FollowUser.id).filter_by(following_userid=id).count()
        following_count = db.query(FollowUser.id).filter_by(follower_userid=id).count()

        nugget_count = (
            db.query(Nuggets)
            .join(NuggetsMaster, Nuggets.nuggets_id == NuggetsMaster.id)
            .filter(
                Nuggets.user_id == id,
                Nuggets.status == 1,
                NuggetsMaster.status == 1,
                Nuggets.nugget_status != 2,
            )
            .count()
        )
    
        event_count = (
            db.query(Events.id).filter(Events.created_by == id, Events.status == 1).count()
        )

        friend_count = (
            db.query(MyFriends)
            .filter(
                MyFriends.status == 1,
                MyFriends.request_status == 1,
                or_(
                    MyFriends.sender_id == get_user.id,
                    MyFriends.receiver_id == get_user.id,
                ),
            )
            .count()
        )   
        # Get Save Nuggets Count
        get_saved_nuggets = (
            db.query(NuggetsSave)
            .filter(NuggetsSave.user_id == get_user.id, NuggetsSave.status == 1)
            .count()
        )
        user_details = {}
        
        
        user_details.update(
            {
                "user_id": get_user.id,
                "user_ref_id": get_user.user_ref_id if get_user.user_ref_id else "",
                "is_email_id_verified": get_user.is_email_id_verified
                if get_user.is_email_id_verified
                else 0,
                "is_mobile_no_verified": get_user.is_mobile_no_verified
                if get_user.is_mobile_no_verified
                else 0,
                "acc_verify_status": 1
                if get_user.is_email_id_verified == 1
                or get_user.is_mobile_no_verified == 1
                else 0,
                "is_profile_updated": 1
                if get_user.dob != "" and get_user.gender != ""
                else 0,
                "name": get_user.display_name if get_user.display_name else "",
                "email_id": get_user.email_id if get_user.email_id else "",
                "mobile": str(get_user.mobile_no) if get_user.mobile_no else "",
                "profile_image": get_user.profile_img
                if get_user.profile_img
                else defaultimage("profile_img"),
                "cover_image": get_user.cover_image
                if get_user.cover_image
                else defaultimage("cover_img"),
                "website": get_user.website if get_user.website else "",
                "first_name": get_user.first_name if get_user.first_name else "",
                "last_name": get_user.last_name if get_user.last_name else "",
                "gender": get_user.gender if get_user.gender else "",
                "other_gender":get_user.other_gender if get_user.other_gender else "",
                "dob": get_user.dob if get_user.dob else "",
                "country_code": get_user.country_code if get_user.country_code else "",
                "country_id": get_user.country_id if get_user.country_id else "",
                "user_code": get_user.user_code if get_user.user_code else "",
                "geo_location": get_user.geo_location if get_user.geo_location else "",
                "latitude": get_user.latitude if get_user.latitude else "",
                "longitude": get_user.longitude if get_user.longitude else "",
                "date_of_join": common_date(get_user.created_at)
                if get_user.created_at
                else "",
                "user_type": get_user.user_type_master.name
                if get_user.user_type_master
                else "",  # .....
                "user_status": get_user.user_status_master.name
                if get_user.user_status_master.name
                else "",  # -----
                "user_status_id": get_user.user_status_id,
                "bio_data": get_user.bio_data if get_user.bio_data else "",
                "followers_count": followers_count,
                "friend_count": friend_count,
                "following_count": following_count,
                "nugget_count": nugget_count,
                "event_count": event_count,
                "work_at": get_user.work_at if get_user.work_at else "",
                "studied_at": get_user.studied_at if get_user.studied_at else "",
                "influencer_category": get_user.influencer_category
                if get_user.influencer_category
                else "",
                "account_verify_type":(2 if get_account_status.verify_status == 1 else 1) if get_account_status else 0,# 0 -Request not send , 1- Pending ,2 - Verified
                "saved_nugget_count": get_saved_nuggets,
                "nugget_content_length": get_user.user_status_master.max_nugget_char
                if get_user.user_status_master.max_nugget_char
                else 0,
                "chime_user_id": get_user.chime_user_id
                if get_user.chime_user_id
                else None,
                "ai_content_length": 100
            }
        )
        token_text = (
            str(get_user.user_ref_id) + str(datetime.datetime.utcnow().timestamp())
        ).encode("ascii")
        invite_url = inviteBaseurl()
        join_link = f"{invite_url}signup?ref={token_text}"

        user_details.update({"referral_link": join_link})

        settings = (
            db.query(UserSettings).filter(UserSettings.user_id == get_user.id).first()
        )
        if settings:
            user_details.update(
                {"language": settings.language.name if settings.language_id else ""}
            )
        else:
            user_details.update({"language": "English"})

        two_type_verification = OTPverificationtype(db, get_user)

        user_details.update({"two_type_verification": two_type_verification})
        # Get Notification
        total_unread_count = (
            db.query(Notification).filter_by(status=1, is_read=0, user_id=id).count()
        )
        user_details.update({"unread_notification_count": total_unread_count})

        return {"status": 1, "msg": "Success", "profile": user_details}


# 11 - Get My Profile
@router.post("/getmyprofile")
async def getmyprofile(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    auth_code: str = Form(None, description="SALT + token"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif auth_code == None or auth_code.strip() == "":
        return {"status": -1, "msg": "Auth Code is missing"}

    else:
        access_token = checkToken(db, token.strip())
        auth_text = token.strip()

        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}

        else:
            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }

            else:
                get_token_details = (
                    db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
                )
                login_user_id = get_token_details.user_id if get_token_details else None

                get_user = db.query(User).filter(User.id == login_user_id).first()
                if get_user:
                    user_details = user_profile(db, login_user_id)
                    return user_details

                else:
                    return {"status": 0, "msg": "No result found!"}



# # 11 - Get My Profile
# @router.post("/getmyprofile")
# async def getmyprofile(
#     db: Session = Depends(deps.get_db),
#     token: str = Form(None),
#     auth_code: str = Form(None, description="SALT + token"),
# ):
#     if token == None or token.strip() == "":
#         return {
#             "status": -1,
#             "msg": "Sorry! your login session expired. please login again.",
#         }

#     elif auth_code == None or auth_code.strip() == "":
#         return {"status": -1, "msg": "Auth Code is missing"}

#     else:
#         access_token = checkToken(db, token.strip())
#         auth_text = token.strip()

#         if checkAuthCode(auth_code, auth_text) == False:
#             return {"status": 0, "msg": "Authentication failed!"}

#         else:
#             if access_token == False:
#                 return {
#                     "status": -1,
#                     "msg": "Sorry! your login session expired. please login again.",
#                 }

#             else:
#                 get_token_details = (
#                     db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
#                 )
#                 login_user_id = get_token_details.user_id if get_token_details else None

#                 get_user = db.query(User).filter(User.id == login_user_id).first()
                
#                 if get_user:
#                     followers_count = db.query(FollowUser.id).filter(FollowUser.following_userid == login_user_id).count()
#                     following_count = db.query(FollowUser.id).filter(FollowUser.follower_userid == login_user_id).count()
#                     # nugget_count = db.query(NuggetsMaster.id).join(Nuggets,Nuggets.nuggets_id == NuggetsMaster.id).\
#                     #     filter(NuggetsMaster.user_id == login_user_id,NuggetsMaster.status == 1).count()
#                     event_count=db.query(Events.id).filter(Events.created_by == login_user_id, Events.status == 1).count()
#                     # friends_count=db.query(MyFriends).filter(MyFriends.status == 1,MyFriends.request_status == 1,or_(MyFriends.sender_id == get_user.id,MyFriends.receiver_id == get_user.id)).count()
#                     get_account_status=db.query(VerifyAccounts).filter(VerifyAccounts.user_id == get_user.id).first()
#                     get_saved_nuggets = db.query(NuggetsSave)\
#                         .filter(NuggetsSave.user_id == get_user.id, NuggetsSave.status == 1)\
#                         .count()
                    
#                     user_details={}
#                     user_details.update({"user_id":get_user.id,
#                                         "user_ref_id":get_user.user_ref_id,
#                                         'is_email_id_verified':get_user.is_email_id_verified,
#                                         "is_mobile_no_verified":get_user.is_mobile_no_verified,
#                                         "acc_verify_status":1 if get_user.is_email_id_verified == 1 or get_user.is_mobile_no_verified == 1 else 0,
#                                         "is_profile_updated": 1 if get_user.dob != '' and get_user.gender != "" else 0,
#                                         "name":get_user.display_name if get_user.display_name != '' and get_user.display_name != None else "",
#                                         "email_id":get_user.email_id if get_user.email_id else "",
#                                         "mobile":str(get_user.mobile_no) if get_user.mobile_no else "",
#                                         "profile_image":get_user.profile_img if get_user.profile_img else defaultimage("profile_img"),
#                                         "cover_image":get_user.cover_image if get_user.cover_image else defaultimage("cover_img"),
#                                         "website":get_user.website if get_user.website else "",
#                                         "first_name":get_user.first_name if get_user.first_name else "",
#                                         "last_name":get_user.last_name if get_user.last_name else "",
#                                         "gender":get_user.gender if get_user.gender else "",
#                                         "dob":get_user.dob if get_user.dob else "",
#                                         "country_code":get_user.country_code if get_user.country_code else "",
#                                         "country_id":get_user.country_id if get_user.country_id else "",
#                                         "user_code":get_user.user_code if get_user.user_code else "",
#                                         "geo_location":get_user.geo_location if get_user.geo_location else "",
#                                         "latitude":get_user.latitude if get_user.latitude else "",
#                                         "longitude":get_user.longitude if get_user.longitude else "",
#                                         "date_of_join":common_date(get_user.created_at) if get_user.created_at else "",
#                                         "user_type":get_user.user_type_master.name if get_user.user_type_master else "",
#                                         "user_status":get_user.user_status_master.name if get_user.user_status_master else "",
#                                         "user_status_id":get_user.user_status_id,
#                                         "bio_data":get_user.bio_data if get_user.bio_data else "",
#                                         # "friends_count":friends_count,
#                                         "followers_count":followers_count,
#                                         "following_count":following_count,
#                                         # "nugget_count":nugget_count,
#                                         "event_count":event_count,  
#                                         "work_at":get_user.work_at if get_user.work_at else "",
#                                         'studied_at':get_user.studied_at if get_user.studied_at else "",
#                                         'influencer_category':get_user.influencer_category if get_user.influencer_category else "",
#                                         'account_verify_type':(2 if get_account_status.verify_status == 1 else 1) if get_account_status else 0,# 0 -Request not send , 1- Pending ,2 - Verified
#                                         'saved_nugget_count':get_saved_nuggets,
#                                         "nugget_content_length":get_user.user_status_master.max_nugget_char if get_user.user_status_master else 0,
#                                         "chime_user_id":get_user.chime_user_id if get_user.chime_user_id else None,
#                                         "ai_content_length":100
#                                          })
#                     token_text = (
#                         str(get_user.user_ref_id) + str(datetime.datetime.utcnow().timestamp())
#                         ).encode("ascii")
#                     invite_url = inviteBaseurl()
#                     join_link = f"{invite_url}signup?ref={token_text}"

#                     user_details.update({"referral_link": join_link})

#                     settings = (
#                         db.query(UserSettings).filter(UserSettings.user_id == get_user.id).first()
#                     )
#                     if settings:
#                         user_details.update(
#                             {"language": settings.language.name if settings.language_id else ""}
#                         )
#                     else:
#                         user_details.update({"language": "English"})

#                     two_type_verification = OTPverificationtype(db, get_user)

#                     user_details.update({"two_type_verification": two_type_verification})
#                     # Get Notification
#                     total_unread_count = (
#                         db.query(Notification).filter_by(status=1, is_read=0, user_id=id).count()
#                     )
#                     user_details.update({"unread_notification_count": total_unread_count})

#                     return {"status": 1, "msg": "Success", "profile": user_details}

#                 else:
#                     return {"status": 0, "msg": "No result found!"}


# 12. Update My Profile
@router.post("/updatemyprofile")
async def updatemyprofile(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    name: str = Form(None),
    first_name: str = Form(None),
    last_name: str = Form(None),
    gender: str = Form(None, description="0->Transgender,1->Male,2->Female"),
    other_gender:str=Form(None),
    dob: Any = Form(None),
    email_id: str = Form(None),
    website: str = Form(None),
    country_code: str = Form(None),
    country_id: str = Form(None),
    mobile_no: str = Form(None),
    profile_image: UploadFile = File(None),
    cover_image: UploadFile = File(None),
    auth_code: str = Form(None, description="SALT + token + name"),
    geo_location: str = Form(None),
    latitude: str = Form(None),
    longitude: str = Form(None),
    bio_data: str = Form(None),
    work_at: str = Form(None),
    studied_at: str = Form(None),
    influencer_category: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif auth_code == None or auth_code.strip() == "":
        return {"status": -1, "msg": "Auth Code is missing"}
    elif name == None or name.strip() == "":
        return {"status": -1, "msg": "Name is missing"}
    elif dob and is_date(dob) == False:
        return {"status": 0, "msg": "Invalid Date"}
    elif gender and not gender.isnumeric():
        return {"status": 0, "msg": "Invalid Gender type"}

    else:
        access_token = checkToken(db, token)
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            auth_text = f"{token}{name}"
            if checkAuthCode(auth_code, auth_text) == False:
                return {"status": 0, "msg": "Authentication failed!"}
            else:
                get_token_details = (
                    db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
                )

                login_user_id = get_token_details.user_id if get_token_details else None

                # Get User Profile
                get_user_profile = (
                    db.query(User).filter(User.id == login_user_id).first()
                )
                name = name
                first_name = first_name if first_name else get_user_profile.first_name
                last_name = last_name if last_name else get_user_profile.last_name
                gender = gender if gender != None else get_user_profile.gender
                dob = dob if dob else get_user_profile.dob
                country_code = (
                    country_code if country_code else get_user_profile.country_code
                )
                mobile_no = mobile_no if mobile_no else get_user_profile.mobile_no
                email_id = email_id if email_id else get_user_profile.email_id
                website = website if website else get_user_profile.website
                country_id = country_id if country_id else get_user_profile.country_id
                geo_location = (
                    geo_location if geo_location else get_user_profile.geo_location
                )
                latitude = latitude.strip() if latitude else get_user_profile.latitude
                longitude = (
                    longitude.strip() if longitude else get_user_profile.longitude
                )
                bio_data = bio_data.strip() if bio_data else get_user_profile.bio_data
                work_at = work_at.strip() if work_at else get_user_profile.work_at
                studied_at = (
                    studied_at.strip() if studied_at else get_user_profile.studied_at
                )
                # Email Validation
                check_email = (
                    db.query(User)
                    .filter(
                        User.email_id == email_id,
                        User.email_id != None,
                        User.id != login_user_id,
                    )
                    .count()
                )
                if check_email > 0:
                    return {"status": 0, "msg": "This email ID is already used"}
                
                # Mobile Number Validation
                check_phone = (
                    db.query(User)
                    .filter(
                        User.mobile_no == mobile_no,
                        User.mobile_no != None,
                        User.id != login_user_id,
                    )
                    .count()
                )
                if check_phone > 0:
                    return {"status": 0, "msg": "This phone number is already used"}

                elif re.search("/[^A-Za-z0-9]/", first_name.strip()):
                    return {"status": 0, "msg": "Please provide valid first name"}

                elif last_name and re.search("/[^A-Za-z0-9]/", last_name.strip()):
                    return {"status": 0, "msg": "Please provide valid last name"}

                else:
                    # Update User Details
                    get_user_profile.display_name = (
                        name.strip() if name else get_user_profile.display_name
                    )
                    get_user_profile.first_name = (
                        first_name.strip()
                        if first_name
                        else get_user_profile.first_name
                    )
                    get_user_profile.last_name = (
                        last_name.strip() if last_name else get_user_profile.last_name
                    )
                    get_user_profile.gender = (
                        gender if gender != None else get_user_profile.gender
                    )
                    get_user_profile.dob = dob if dob else get_user_profile.dob
                    get_user_profile.country_code = (
                        country_code if country_code else get_user_profile.country_code
                    )
                    get_user_profile.mobile_no = (
                        mobile_no if mobile_no else get_user_profile.mobile_no
                    )
                    get_user_profile.email_id = (
                        email_id.strip() if email_id else get_user_profile.email_id
                    )
                    get_user_profile.website = (
                        website.strip() if website else get_user_profile.website
                    )
                    get_user_profile.country_id = (
                        country_id if country_id else get_user_profile.country_id
                    )
                    get_user_profile.geo_location = (
                        geo_location.strip()
                        if geo_location
                        else get_user_profile.geo_location
                    )
                    get_user_profile.latitude = latitude
                    get_user_profile.longitude = longitude
                    get_user_profile.bio_data = bio_data
                    get_user_profile.work_at = work_at
                    get_user_profile.studied_at = studied_at
                    get_user_profile.influencer_category = (
                        influencer_category.strip() if influencer_category else None
                    )
                    get_user_profile.other_gender=other_gender
                    db.commit()
                    
                    # Profile Image Upload
                    if profile_image:
                        readed_file = profile_image
                        file_ext = os.path.splitext(profile_image.filename)[1]

                        extensions = [".jpeg", ".jpg", ".png"]

                        if file_ext not in extensions:
                            return {
                                "status": 0,
                                "msg": "Profile Image format does not support",
                            }

                        # Upload File to Server
                        uploaded_file_path = await file_upload(
                            readed_file, file_ext, compress=None
                        )
                        s3_file_path = f"profileimage/Image_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                        result = upload_to_s3(uploaded_file_path, s3_file_path)
                        if result["status"] == 1:
                            get_user_profile.profile_img = result["url"]
                            db.commit()
                        else:
                            return result

                    # Cover (Background Image Upload)
                    if cover_image:
                        read_file = cover_image

                        file_ext = os.path.splitext(cover_image.filename)[1]

                        extensions = [".jpeg", ".jpg", ".png"]

                        if file_ext not in extensions:
                            return {
                                "status": 0,
                                "msg": "Profile Image format does not support",
                            }

                        # Upload File to Server
                        output_dir = await file_upload(
                            read_file, file_ext, compress=None
                        )

                        s3_file_path = f"coverimage/coverimage_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}"

                        result = upload_to_s3(output_dir, s3_file_path)

                        if result and result["status"] == 1:
                            get_user_profile.cover_image = result["url"]
                            db.commit()
                        else:
                            return result

                    # Get Updated User Profile
                    user_details = user_profile(db, login_user_id)
                    return user_details


# 13 Search Rawcaster Users (for friends)
@router.post("/searchrawcasterusers")
async def searchrawcasterusers(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    auth_code: str = Form(None, description="SALT + token"),
    search_key: str = Form(None),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif auth_code == None or auth_code.strip() == "":
        return {"status": -1, "msg": "Auth Code is missing"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}

    else:
        access_token = checkToken(db, token.strip())
        auth_text = token.strip()
        if checkAuthCode(auth_code.strip(), auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }
            else:
                login_user_email = ""
                get_token_details = (
                    db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
                )

                login_user_id = get_token_details.user_id if get_token_details else None
                login_user_email = (
                    get_token_details.user.email_id if get_token_details else None
                )

                current_page_no = int(page_number)
                
                get_user = db.query(
                    User.id,
                    User.email_id,
                    User.user_ref_id,
                    User.first_name,
                    User.last_name,
                    User.display_name,
                    User.gender,
                    User.profile_img,
                    User.geo_location,
                    User.bio_data,
                    MyFriends.request_status.label('friend_request_status'),
                    FollowUser.id.label('follow_id')
                ).select_from(User).outerjoin(MyFriends, 
                    ((MyFriends.sender_id == User.id) | (MyFriends.receiver_id == User.id))
                    & (MyFriends.status == 1)
                    & ((MyFriends.sender_id == login_user_id) | (MyFriends.receiver_id == login_user_id))
                ).outerjoin(FollowUser,
                    (FollowUser.following_userid == User.id)
                    & (FollowUser.follower_userid == login_user_id)
                ).filter(User.status == 1, User.id != login_user_id)
                
                # Omit blocked users --
                request_status = 3
                response_type = 1
                requested_by = None
                get_all_blocked_users = get_friend_requests(
                    db, login_user_id, requested_by, request_status, response_type
                )
                blocked_users = get_all_blocked_users["blocked"]

                if blocked_users:
                    get_user = get_user.filter(User.id.not_in(blocked_users))

                if search_key:
                    get_user = get_user.filter(
                        or_(
                            User.email_id.ilike(search_key + "%"),
                            User.mobile_no.ilike(search_key + "%"),
                            User.display_name.ilike("%" + search_key + "%"),
                            User.first_name.ilike("%" + search_key + "%"),
                            User.last_name.ilike("%" + search_key + "%"),
                        )
                    )

                get_row_count = get_user.count()

                if get_row_count < 1:
                    if login_user_email == search_key:
                        return {"status": 0, "msg": "No Result found", "invite_flag": 0}
                    else:
                        return {"status": 0, "msg": "No Result found", "invite_flag": 1}
                else:
                    default_page_size = 25
                    limit, offset, total_pages = get_pagination(
                        get_row_count, current_page_no, default_page_size
                    )
                    # Apply Pagination
                    get_user = (
                        get_user.order_by(User.first_name.asc())
                        .limit(limit)
                        .offset(offset)
                        .all()
                    )

                    user_list = []
                    
                    for user in get_user:

                        get_follow_user_details = db.query(FollowUser).filter(
                            FollowUser.following_userid == user.id
                        )

                        get_follow_user = get_follow_user_details.filter(
                            FollowUser.follower_userid == login_user_id
                        ).first()

                        follow_count = get_follow_user_details.count()

                        mutual_friends = MutualFriends(db, login_user_id, user.id)

                        user_list.append(
                            {
                                "user_id": user.id,
                                "user_ref_id": user.user_ref_id,
                                "email_id": user.email_id if user.email_id else "",
                                "first_name": user.first_name
                                if user.first_name
                                else "",
                                "last_name": user.last_name if user.last_name else "",
                                "display_name": user.display_name
                                if user.display_name
                                else "",
                                "gender": user.gender if user.gender else "",
                                "profile_img": user.profile_img
                                if user.profile_img
                                else "",
                                "friend_request_status": user.friend_request_status
                                if user.friend_request_status != None
                                else "",
                                "follow": True if get_follow_user else False,
                                "follow_count": follow_count,
                                "location": user.geo_location
                                if user.geo_location
                                else "",
                                "mutual_friends": mutual_friends,
                                "bio_data": ProfilePreference(
                                    db,
                                    login_user_id,
                                    user.id,
                                    "bio_display_status",
                                    user.bio_data,
                                ),
                            }
                        )
                    return {
                        "status": 1,
                        "msg": "Success",
                        "total_pages": total_pages,
                        "current_page_no": current_page_no,
                        "users_list": user_list,
                    }

         
# 14 Invite to Rawcaster
@router.post("/invitetorawcaster")
async def invitetorawcaster(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    email_id: str = Form(None, description="email ids"),
    auth_code: str = Form(None, description="SALT + token"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif auth_code == None or auth_code.strip() == "":
        return {"status": -1, "msg": "Auth Code is missing"}
    elif email_id == None or email_id.strip() == "":
        return {"status": -1, "msg": "Email ID is missing"}

    else:
        access_token = checkToken(db, token.strip())
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }

        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )

            login_user_id = get_token_details.user_id
            login_user_name = get_token_details.user.first_name

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            if email_id == "" or email_id == []:
                return {"status": 0, "msg": "Please provide a valid email address"}

            else:
                auth_text = token.strip()
                if checkAuthCode(auth_code.strip(), auth_text) == False:
                    return {"status": 0, "msg": "Authentication failed!"}
                else:
                    success = 0
                    failed = 0
                    total = len(email_id)
                    email_id = ast.literal_eval(email_id) if email_id else None

                    for mail in email_id:
                        if check_mail(mail) == False:
                            failed += 1
                        else:
                            get_user = (
                                db.query(User)
                                .filter(User.email_id == str(mail).strip())
                                .first()
                            )

                            if get_user:
                                failed += 1

                            else:
                                # Invites Sents to Only for New User (Not a Rawcaster)
                                get_user = (
                                    db.query(User.user_ref_id)
                                    .filter(User.id == login_user_id)
                                    .first()
                                )

                                token_text = base64.b64encode(
                                    f"{get_user.user_ref_id}//{datetime.datetime.utcnow()}".encode()
                                ).decode()
                                invite_link = inviteBaseurl()
                                join_link = (
                                    f"{invite_link}signup?ref={token_text}&mail={mail}"
                                )

                                subject = f"Rawcaster - Invite from {login_user_name}"
                                body = invite_mail(join_link)
                                email_detail = {
                                    "email": mail,
                                    "subject": subject,
                                    "mail_message": body,
                                    "sms_message": "",
                                }
                                user = []
                                # Send Mail (before remove the production)
                                send_mail = await send_email(db, mail, subject, body)

                                add_notification_email = addNotificationSmsEmail(
                                    db, user, email_detail, login_user_id
                                )
                                success += success

                    if total == failed:
                        return {"status": 0, "msg": "Failed to send invites"}
                    if success == total:
                        return {"status": 1, "msg": "Invites sent"}
                    else:
                        return {"status": 1, "msg": "Invites sent"}


# 15 Send friend request to others
@router.post("/sendfriendrequests")
async def sendfriendrequests(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_ids: str = Form(None, description="ref ids"),
    auth_code: str = Form(None, description="SALT + token"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif auth_code == None or auth_code.strip() == "":
        return {"status": -1, "msg": "Auth Code is missing"}
    elif user_ids == None:
        return {"status": -1, "msg": "Auth Code is missing"}

    else:
        access_token = checkToken(db, token.strip())
        auth_text = token.strip()

        if checkAuthCode(auth_code, auth_text.strip()) == False:
            return {"status": 0, "msg": "Authentication failed!"}

        else:
            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }
            else:
                get_token_details = (
                    db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
                )

                login_user_id = get_token_details.user_id
                login_user_name = get_token_details.user.first_name
                
                if user_ids == []:
                    return {"status": -1, "msg": "Users list is missing"}
                else:
                    user_ids = json.loads(user_ids) if user_ids else None
                    
                    if user_ids == "" or user_ids == None:
                        return {"status": 0, "msg": "Please provide a valid users list"}
                    else:
                        friend_request_ids = []
                        get_user = db.query(User).filter(User.id == login_user_id).first()
                        hostname = get_user.display_name if get_user else None
                        
                        for user in user_ids:
                            users = db.query(User).filter(User.user_ref_id == user).first()
                            user_list = []
                            if users:
                                user_id = users.id
                                user_list.append(user_id)
                                
                                request_statuss = [0, 1]
                                get_my_friends = (
                                    db.query(MyFriends)
                                    .filter(MyFriends.status == 1,
                                        or_(
                                            MyFriends.sender_id == login_user_id,
                                            MyFriends.sender_id == user_id,
                                        ),
                                        or_(
                                            MyFriends.receiver_id == user_id,
                                            MyFriends.receiver_id == login_user_id,
                                        ),
                                        MyFriends.request_status.in_(request_statuss),
                                    )
                                    .order_by(MyFriends.id.desc())
                                )

                                get_friend_request = get_my_friends.first()

                                if not get_friend_request:
                                    get_user = (
                                        db.query(User).filter(User.id == user_id).first()
                                    )

                                    if get_user:
                                        add_my_friends = MyFriends(
                                            sender_id=login_user_id,
                                            receiver_id=user_id,
                                            request_date=datetime.datetime.utcnow(),
                                            request_status=0,
                                            status_date=None,
                                            status=1,
                                        )
                                        db.add(add_my_friends)
                                        db.commit()
                                        db.refresh(add_my_friends)

                                        if add_my_friends:
                                            add_notification = Insertnotification(
                                                db,
                                                user_id,
                                                login_user_id,
                                                11,
                                                add_my_friends.id,
                                            )

                                            friend_request_ids.append(add_my_friends.id)

                                            message_details = {}
                                            message_details.update(
                                                {
                                                    "message": f"{hostname} Sent a connection request",
                                                    "data": {
                                                        "refer_id": add_my_friends.id,
                                                        "type": "friend_request",
                                                    },
                                                    "type": "friend_request",
                                                }
                                            )

                                            push_notification = pushNotify(
                                                db,
                                                user_list,
                                                message_details,
                                                login_user_id,
                                            )

                                            body = ""
                                            sms_message = ""
                                            (
                                                sms_message,
                                                body,
                                            ) = friendRequestNotifcationEmail(
                                                db, login_user_id, user_id, 1
                                            )

                                            subject = "Rawcaster - Connection Request"
                                            email_detail = {
                                                "subject": subject,
                                                "mail_message": body,
                                                "sms_message": sms_message,
                                                "type": "friend_request",
                                            }
                                            send_notification = addNotificationSmsEmail(
                                                db, user_list, email_detail, login_user_id
                                            )
                                else:
                                    return {
                                        "status": 0,
                                        "msg": "Failed to send Connection request"
                                        }

                        if friend_request_ids:
                            return {
                                "status": 1,
                                "msg": "Connection request sent successfully",
                                "friend_request_ids": friend_request_ids,
                            }

                        else:
                            return {
                                "status": 0,
                                "msg": "Failed to send Connection request",
                                "friend_request_ids": friend_request_ids,
                            }


# 16 List all friend requests (all requests sent to this users from others)
@router.post("/listallfriendrequests")
async def listallfriendrequests(
    db: Session = Depends(deps.get_db), token: str = Form(None)
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        access_token = checkToken(db, token)
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None

            response_type = 0
            request_status = 0
            requested_by = 2
            pending_requests = get_friend_requests(
                db, login_user_id, requested_by, request_status, response_type
            )

            return {
                "status": 1,
                "msg": "Success",
                "pending_requests": pending_requests["pending"],
            }


# 17 Respond to friend request received from others
@router.post("/respondtofriendrequests")
async def respondtofriendrequests(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    friend_request_id: str = Form(None),
    notification_id: str = Form(None),
    response: str = Form(None, description="1-Accept,2-Reject,3-Block"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif response and not response.isnumeric():
        return {"status": 0, "msg": "Invalid Response type"}

    elif response == None or not 1 <= int(response) <= 3:
        return {"status": 0, "msg": "Response is missing"}

    else:
        response = int(response)
        access_token = checkToken(db, token)
        if not access_token:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )

            login_user_id = get_token_details.user_id

            my_friends = (
                db.query(MyFriends)
                .filter(
                    MyFriends.status == 1,
                    MyFriends.request_status == 0,
                    MyFriends.id == friend_request_id,
                    MyFriends.receiver_id == login_user_id,
                )
                .first()
            )

            if not my_friends:
                return {"status": 0, "msg": "Invalid Friend request/reject"}

            else:
                if response == 2:   # if reject
                    status = 0
                else:               # if accept or block
                    status = 1  
                
                channel_arn=None
                if response == 1:
                    # Create Channel for One to One Chat
                    chime_bearer = (
                        get_token_details.user.chime_user_id
                        if get_token_details.user.chime_user_id
                        else None
                    )
                    set_unique_channel=f"RAWCAST{int(datetime.datetime.utcnow().timestamp())}"
                    try:
                        channel_response = create_channel(chime_bearer, set_unique_channel)
                        # Update Channel ARN
                        channel_arn = (
                            channel_response["ChannelArn"] if channel_response else None
                        ) 
                    except Exception as e:
                        print(e)
                    
                update_my_friends = (
                    db.query(MyFriends)
                    .filter(MyFriends.id == friend_request_id)
                    .update(
                        {
                            "status": status,
                            "request_status": response,
                            "status_date": datetime.datetime.utcnow(),
                            "channel_arn":channel_arn
                        }
                    )
                )
                db.commit()

                if update_my_friends:
                    
                    # Add Members to Channel
                    member_id=my_friends.user1.chime_user_id if my_friends.sender_id else None
                    try:
                        addmembers(channel_arn, chime_bearer, member_id)
                    except Exception as e:
                        print(e)
                
                    if notification_id:
                        # if status == 1:
                        update_notification = (
                            db.query(Notification)
                            .filter(Notification.id == notification_id)
                            .update(
                                {
                                    "status": 0,
                                    "is_read": 1,
                                    "read_datetime": datetime.datetime.utcnow(),
                                }
                            )
                        )
                        db.commit()
                        # else:
                        #     update_notification=db.query(Notification).filter(Notification.id == notification_id).update({"status":0,"is_read":1,"read_datetime":datetime.datetime.utcnow()})
                    else:
                        update_notification = (
                            db.query(Notification)
                            .filter(
                                Notification.notification_origin_id
                                == my_friends.sender_id,
                                Notification.user_id == my_friends.receiver_id,
                                Notification.notification_type == 11,
                            )
                            .update(
                                {
                                    "status": 0,
                                    "is_read": 1,
                                    "read_datetime": datetime.datetime.utcnow(),
                                }
                            )
                        )
                        db.commit()

                    if response == 1: # 1-Accept
                        friend_requests = my_friends.user1
                        friend_details = {}
                        friend_details.update(
                            {
                                "friend_request_id": friend_requests.id,
                                "user_id": friend_requests.id,
                                "email_id": friend_requests.email_id,
                                "first_name": friend_requests.first_name,
                                "last_name": friend_requests.last_name,
                                "display_name": friend_requests.display_name,
                                "gender": friend_requests.gender,
                                "profile_img": friend_requests.profile_img,
                                "online": friend_requests.online,
                                "last_seen": friend_requests.last_seen,
                                "typing": 0,
                            }
                        )

                        sender_id = my_friends.sender_id
                        receiver_id = my_friends.receiver_id
                        notification_type = 12
                        insert_notification = Insertnotification(
                            db, sender_id, receiver_id, notification_type, receiver_id
                        )

                        friend_request_ids = [friend_requests.id]
                        body = ""
                        sms_message = ""
                        sms_message, body = friendRequestNotifcationEmail(
                            db, sender_id, login_user_id, 2
                        )

                        subject = "Rawcaster - Connection Request Accepted"

                        email_detail = {
                            "subject": subject,
                            "mail_message": body,
                            "sms_message": sms_message,
                            "type": "friend_request",
                        }
                        user_id = [sender_id]

                        add_notification = addNotificationSmsEmail(
                            db, user_id, email_detail, login_user_id
                        )

                        return {
                            "status": 1,
                            "msg": "Success",
                            "friend_details": friend_details,
                        }
                    else:
                        return {"status": 1, "msg": "Success"}
                else:
                    return {"status": 0, "msg": "Failed to update. please try again"}


# # 18 List all Friend Groups
# @router.post("/listallfriendgroups")
# async def listallfriendgroups(db:Session=Depends(deps.get_db),token:str=Form(None),search_key:str=Form(None),page_number:str=Form(default=1),flag:str=Form(None)):

#     if token == None or token.strip() == "":
#         return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
#     elif not str(page_number).isnumeric():
#         return {"status":0,"msg":"Invalid page Number"}
#     else:
#         access_token=checkToken(db,token)

#         if access_token == False:
#             return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
#         else:
#             get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()

#             login_user_id=get_token_details.user_id

#             current_page_no=int(page_number)

#             flag= flag if flag else 0

#             my_friend_group=db.query(FriendGroups).join(FriendGroupMembers,FriendGroupMembers.group_id == FriendGroups.id,isouter=True)

#             my_friend_group=my_friend_group.group_by(FriendGroups.id).filter(FriendGroups.status == 1,or_(FriendGroups.created_by == login_user_id,FriendGroupMembers.user_id == login_user_id))

#             if search_key and search_key.strip() == "":
#                 my_friend_group=my_friend_group.filter(FriendGroups.group_name.ilike(search_key+"%"))

#             get_row_count=my_friend_group.count()

#             if get_row_count < 1:
#                 return {"status":0,"msg":"No Result found"}

#             else:
#                 default_page_size=1000

#                 limit,offset,total_pages=get_pagination(get_row_count,current_page_no,default_page_size)

#                 my_friend_group=my_friend_group.order_by(FriendGroups.group_name.asc()).limit(limit).offset(offset).all()
#                 result_list=[]
#                 for res in my_friend_group:
#                     get_user=db.query(User).filter(User.id == res.created_by).first()

#                     get_frnd_group_count=db.query(FriendGroupMembers).filter(FriendGroupMembers.group_id == res.id).count()
#                     grouptype=1
#                     groupname=res.group_name

#                     # View Access
#                     group_access=0
#                     check_influencer_category=db.query(User.id,UserStatusMaster.type,UserSettings.lock_my_connection).filter(User.id == res.created_by,UserSettings.user_id == User.id).first()
#                     if check_influencer_category and check_influencer_category.type == 2 and check_influencer_category.lock_my_connection == 1:

#                         is_friend=db.query(MyFriends).filter(or_(MyFriends.sender_id == login_user_id,MyFriends.receiver_id == login_user_id),or_(MyFriends.sender_id == res.created_by,MyFriends.receiver_id == res.created_by),MyFriends.status == 1).first()
#                         if is_friend:
#                             group_access=0
#                         else:
#                             group_access=1

#                     elif check_influencer_category and check_influencer_category.type == 1 and check_influencer_category.lock_my_connection == 1:
#                         group_access=1

#                     group_category=None
#                     if groupname == "My Fans":
#                         grouptype=2
#                         group_category=1

#                     if groupname == "My Fans" and res.created_by != login_user_id:
#                         grouptype=1
#                         group_category=2
#                         groupname=f"Influencer: {(res.user.display_name if res.user.display_name else '') if res.created_by else ''}"

#                     if res.created_by == login_user_id and  groupname != "My Fans":
#                         grouptype=2
#                         group_category = 3


#                     get_group_chat=db.query(GroupChat).filter(GroupChat.status == 1,GroupChat.group_id == res.id).order_by(GroupChat.id.desc()).first()
#                     memberlist=[]
#                     members=[]

#                     if grouptype == 2:

#                         members.append(res.created_by)
#                         memberlist.append({
#                                             "user_id":res.created_by,
#                                             "email_id":get_user.email_id,
#                                             "first_name":get_user.first_name,
#                                             "last_name":get_user.last_name,
#                                             "display_name":get_user.display_name,
#                                             "gender":get_user.gender,
#                                             "profile_img":get_user.profile_img,
#                                             "online":get_user.online,
#                                             "last_seen":get_user.last_seen,
#                                             "typing":0
#                                             })

#                     get_friend_group_member=db.query(FriendGroupMembers).filter(FriendGroupMembers.group_id == res.id).all()
#                     for group_member in get_friend_group_member:
#                         members.append(group_member.user_id)
#                         memberlist.append({
#                                             "user_id":group_member.user_id,
#                                             "email_id":group_member.user.email_id if group_member.user_id else "",
#                                             "first_name":group_member.user.first_name if group_member.user_id else "",
#                                             "last_name":group_member.user.last_name if group_member.user_id else "",
#                                             "display_name":group_member.user.display_name if group_member.user_id else "",
#                                             "gender":group_member.user.gender if group_member.user_id else "",
#                                             "profile_img":group_member.user.profile_img if group_member.user_id else "",
#                                             "online":group_member.user.online if group_member.user_id else "",
#                                             "last_seen":group_member.user.last_seen if group_member.user_id else "",
#                                             "typing":0
#                                             })

#                     if group_access == 1 and get_user.user_status_id == 4 and grouptype == 2:
#                         result_list.append({
#                                             "group_id":res.id,
#                                             "group_name":groupname,
#                                             "group_icon":res.group_icon if res.group_icon else defaultimage('group_icon'),
#                                             "group_member_count":(get_frnd_group_count + 1 if grouptype == 1 else get_frnd_group_count)  if get_frnd_group_count else 0,
#                                             "locked":1
#                                             })
#                     else:
#                         result_list.append({
#                                             "group_id":res.id,
#                                             "group_name":groupname,
#                                             "locked":0,
#                                             "owner_membership_type":get_user.user_status_id,
#                                             "group_icon":res.group_icon if res.group_icon else defaultimage('group_icon'),
#                                             "group_member_count":(get_frnd_group_count + 1 if grouptype == 1 else get_frnd_group_count)  if get_frnd_group_count else 0,
#                                             "group_owner":res.created_by if res.created_by else 0,
#                                             "typing":0,
#                                             "chat_enabled":res.chat_enabled,
#                                             "group_type":grouptype,
#                                             "group_access":1 if group_access == 1 else 0,
#                                             "group_category":group_category if group_category else 3,
#                                             "last_msg":get_group_chat.message if get_group_chat else "",
#                                             "last_msg_datetime":(common_date(get_group_chat.sent_datetime) if get_group_chat.sent_datetime else "") if get_group_chat else "",
#                                             "result_list":3,
#                                             "group_member_ids":members,
#                                             "group_members_list":memberlist
#                                             })

#                 return {"status":1,"msg":"Success","group_count":get_row_count,"total_pages":total_pages,"current_page_no":current_page_no,"friend_group_list":result_list}


# 18 List all Friend Groups
@router.post("/listallfriendgroups")  # Chime Chat
async def listallfriendgroups(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    search_key: str = Form(None),
    page_number: str = Form(default=1),
    flag: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )

            login_user_id = get_token_details.user_id

            current_page_no = int(page_number)

            flag = flag if flag else 0

            my_friend_group = db.query(FriendGroups).join(
                FriendGroupMembers,
                FriendGroupMembers.group_id == FriendGroups.id,
                isouter=True,
            )

            my_friend_group = my_friend_group.group_by(FriendGroups.id).filter(
                FriendGroups.status == 1,
                or_(
                    FriendGroups.created_by == login_user_id,
                    FriendGroupMembers.user_id == login_user_id,
                ),
            )

            if search_key and search_key.strip() == "":
                my_friend_group = my_friend_group.filter(
                    FriendGroups.group_name.ilike(search_key + "%")
                )

            get_row_count = my_friend_group.count()

            if get_row_count < 1:
                return {"status": 0, "msg": "No Result found"}

            else:
                default_page_size = 1000

                limit, offset, total_pages = get_pagination(
                    get_row_count, current_page_no, default_page_size
                )

                my_friend_group = (
                    my_friend_group.order_by(FriendGroups.group_name.asc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )
                result_list = []
                for res in my_friend_group:
                    get_user = db.query(User).filter(User.id == res.created_by).first()

                    get_frnd_group_count = (
                        db.query(FriendGroupMembers)
                        .filter(FriendGroupMembers.group_id == res.id)
                        .count()
                    )
                    grouptype = 1
                    groupname = res.group_name

                    # View Access
                    group_access = 0
                    check_influencer_category = (
                        db.query(
                            User.id,
                            UserStatusMaster.type,
                            UserSettings.lock_my_connection,
                        )
                        .filter(
                            User.id == res.created_by, UserSettings.user_id == User.id
                        )
                        .first()
                    )
                    if (
                        check_influencer_category
                        and check_influencer_category.type == 2
                        and check_influencer_category.lock_my_connection == 1
                    ):
                        is_friend = (
                            db.query(MyFriends)
                            .filter(
                                or_(
                                    MyFriends.sender_id == login_user_id,
                                    MyFriends.receiver_id == login_user_id,
                                ),
                                or_(
                                    MyFriends.sender_id == res.created_by,
                                    MyFriends.receiver_id == res.created_by,
                                ),
                                MyFriends.status == 1,
                            )
                            .first()
                        )
                        if is_friend:
                            group_access = 0
                        else:
                            group_access = 1

                    elif (
                        check_influencer_category
                        and check_influencer_category.type == 1
                        and check_influencer_category.lock_my_connection == 1
                    ):
                        group_access = 1

                    group_category = None
                    # Group Category ( 1-My Group , 2- Influence , 3- Other groups )
                    if groupname == "My Fans" and res.created_by == login_user_id:
                        grouptype = 2
                        group_category = 1

                    elif groupname == "My Fans" and res.created_by != login_user_id:
                        grouptype = 1
                        group_category = 2
                        groupname = f"Influencer: {(res.user.display_name if res.user.display_name else '') if res.created_by else ''}"

                    elif groupname != "My Fans":
                        grouptype = 2
                        group_category = 3

                    get_group_chat = (
                        db.query(GroupChat)
                        .filter(GroupChat.status == 1, GroupChat.group_id == res.id)
                        .order_by(GroupChat.id.desc())
                        .first()
                    )
                    memberlist = []
                    members = []

                    if grouptype == 2:
                        members.append(res.created_by)
                        memberlist.append(
                            {
                                "user_id": res.created_by,
                                "email_id": get_user.email_id,
                                "member_arn": get_user.chime_user_id if get_user.chime_user_id else "",
                                "first_name": get_user.first_name,
                                "last_name": get_user.last_name,
                                "display_name": get_user.display_name,
                                "gender": get_user.gender,
                                "profile_img": get_user.profile_img,
                                "online": get_user.online,
                                "last_seen": get_user.last_seen,
                                "typing": 0,
                            }
                        )

                    get_friend_group_member = (
                        db.query(FriendGroupMembers)
                        .filter(FriendGroupMembers.group_id == res.id)
                        .all()
                    )
                    for group_member in get_friend_group_member:
                        members.append(group_member.user_id)
                        memberlist.append(
                            {
                                "user_id": group_member.user_id,
                                "email_id": group_member.user.email_id
                                if group_member.user_id
                                else "",
                                "member_arn": group_member.user.chime_user_id
                                if group_member.user_id
                                else "",
                                "first_name": group_member.user.first_name
                                if group_member.user_id
                                else "",
                                "last_name": group_member.user.last_name
                                if group_member.user_id
                                else "",
                                "display_name": group_member.user.display_name
                                if group_member.user_id
                                else "",
                                "gender": group_member.user.gender
                                if group_member.user_id
                                else "",
                                "profile_img": group_member.user.profile_img
                                if group_member.user_id
                                else "",
                                "online": group_member.user.online
                                if group_member.user_id
                                else "",
                                "last_seen": group_member.user.last_seen
                                if group_member.user_id
                                else "",
                                "typing": 0,
                            }
                        )

                    if (
                        group_access == 1
                        and get_user.user_status_id == 4
                        and grouptype == 1
                    ):
                        result_list.append(
                            {
                                "group_id": res.id,
                                "group_name": groupname,
                                "group_icon": res.group_icon
                                if res.group_icon
                                else defaultimage("group_icon"),
                                "group_member_count": (
                                    get_frnd_group_count + 1
                                    if grouptype == 1
                                    else get_frnd_group_count
                                )
                                if get_frnd_group_count
                                else 0,
                                "locked": 1,
                            }
                        )
                    else:
                        result_list.append(
                            {
                                "group_id": res.id,
                                "group_name": groupname,
                                "locked": 0,
                                "channel_arn": res.group_arn if res.group_arn else None,
                                "owner_membership_type": get_user.user_status_id,
                                "group_icon": res.group_icon
                                if res.group_icon
                                else defaultimage("group_icon"),
                                "group_member_count": (
                                    get_frnd_group_count + 1
                                    if grouptype == 1
                                    else get_frnd_group_count
                                )
                                if get_frnd_group_count
                                else 0,
                                "group_owner": res.created_by if res.created_by else 0,
                                "typing": 0,
                                "chat_enabled": res.chat_enabled,
                                "group_type": grouptype,
                                "group_access": 1 if group_access == 1 else 0,
                                "group_category": group_category
                                if group_category
                                else 3,
                                "last_msg": get_group_chat.message
                                if get_group_chat
                                else "",
                                "last_msg_datetime": (
                                    common_date(get_group_chat.sent_datetime)
                                    if get_group_chat.sent_datetime
                                    else ""
                                )
                                if get_group_chat
                                else "",
                                "result_list": 3,
                                "group_member_ids": members,
                                "group_members_list": memberlist,
                            }
                        )

                return {
                    "status": 1,
                    "msg": "Success",
                    "group_count": get_row_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "friend_group_list": result_list,
                }


# 19 List all Friends
@router.post("/listallfriends")
async def listallfriends(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    search_key: str = Form(None),
    group_ids: str = Form(None, description="Like ['12','13','14']"),
    nongrouped: str = Form(None, description="Send 1"),
    friends_count: str = Form(None),
    allfriends: str = Form(None, description="send 1"),
    age: str = Form(None),
    gender: str = Form(None),
    location: str = Form(None),
    user_id: str = Form(None),
    page_number: str = Form(default=1, description="send 1 for initial request"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif nongrouped and not nongrouped.isnumeric():
        return {"status": 0, "msg": "Invalid nongrouped flag"}
    elif not allfriends:
        return {"status": 0, "msg": "Invalid allfriends flag"}

    else:
        user_id = int(user_id) if user_id else None
        allfriends = int(allfriends) if allfriends else None
        nongrouped = int(nongrouped) if nongrouped else None

        access_token = checkToken(db, token)
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }

        else:
            login_from = 1
            get_token_details = (
                db.query(ApiTokens.user_id,ApiTokens.device_type).filter(ApiTokens.token == access_token).first()
            )
            current_user_id = get_token_details.user_id
            login_user_id = (
                (get_token_details.user_id if get_token_details else None)
                if not user_id
                else user_id
            )

            login_from = get_token_details.device_type

            my_friends_ids = []

            # Step 1) Get all active friends of logged in user (if requested for all friends list)
            if allfriends == 1:
                get_all_friends = (
                    db.query(MyFriends)
                    .filter(
                        MyFriends.status == 1,
                        MyFriends.request_status == 1,
                        or_(
                            MyFriends.sender_id == login_user_id,
                            MyFriends.receiver_id == login_user_id,
                        ),
                    )
                    .all()
                )

                if get_all_friends:
                    for frnds in get_all_friends:
                        my_friends_ids.append(frnds.id)

            get_my_friends = (
                db.query(MyFriends)
                .filter(
                    or_(
                        MyFriends.sender_id == login_user_id,
                        MyFriends.receiver_id == login_user_id,
                    )
                )
                .filter(MyFriends.status == 1, MyFriends.request_status == 1)
            )
            # get_my_friends=db.query(MyFriends).filter(or_(MyFriends.sender_id == login_user_id,MyFriends.receiver_id == login_user_id,MyFriends.sender_id.in_(followers),MyFriends.receiver_id.in_(followers))).filter(MyFriends.status == 1,MyFriends.request_status == 1)

            if search_key:
                get_user = (
                    db.query(User)
                    .filter(
                        or_(
                            User.email_id.ilike(search_key),
                            User.display_name.ilike(search_key),
                            User.first_name.ilike(search_key),
                            User.last_name.ilike(search_key),
                        )
                    )
                    .all()
                )
                user_ids = {usr.id for usr in get_user}

                get_my_friends = get_my_friends.filter(
                    or_(
                        MyFriends.sender_id.in_(user_ids),
                        MyFriends.receiver_id.in_(user_ids),
                    )
                )

            if age:
                if not age.isnumeric():
                    return {"status": 0, "msg": "Invalid Age"}
                else:
                    current_year = datetime.datetime.utcnow().year
                    get_user = (
                        db.query(User)
                        .filter(current_year - extract("year", User.dob) == age)
                        .all()
                    )
                    user_ages = {usr.id for usr in get_user}

                    get_my_friends = get_my_friends.filter(
                        or_(
                            MyFriends.sender_id.in_(user_ages),
                            MyFriends.receiver_id.in_(user_ages),
                        )
                    )

            if location:
                get_user = (
                    db.query(User.id).filter(User.geo_location.ilike(location + "%")).all()
                )
                user_location_ids = {usr.id for usr in get_user}

                get_my_friends = get_my_friends.filter(
                    or_(
                        MyFriends.sender_id.in_(user_location_ids),
                        MyFriends.receiver_id.in_(user_location_ids),
                    )
                )

            if gender:
                if not gender.isnumeric():
                    return {"status": 0, "msg": "Invalid Gender type"}
                else:
                    get_user_gender = db.query(User.id).filter(User.gender == gender).all()
                    get_user_ids = [usr.id for usr in get_user_gender]

                    get_my_friends = get_my_friends.filter(
                        or_(
                            MyFriends.sender_id.in_(get_user_ids),
                            MyFriends.receiver_id.in_(get_user_ids),
                        )
                    )

            get_my_friends_count = get_my_friends.count()

            if get_my_friends_count < 1:
                return {"status": 0, "msg": "No Result found"}

            else:
                friend_login_from_app = 0
                friend_login_from_web = 0
                friend_login_from = 0
                default_page_size = 1000

                get_my_friends = get_my_friends.all()

                friendid = 0
                request_frnds = []

                for friend_requests in get_my_friends:
                    get_follow_user_id = (
                        db.query(FollowUser)
                        .filter(
                            or_(
                                FollowUser.following_userid
                                == friend_requests.sender_id,
                                FollowUser.following_userid
                                == friend_requests.receiver_id,
                            ),
                            FollowUser.follower_userid == login_user_id,
                        )
                        .first()
                    )
                    # get My friends (Login User Friends)
                    my_frind = get_friend_requests(db, current_user_id, None, None, 1)
                    my_friends = my_frind["accepted"] + my_frind["pending"]

                    get_last_msg = (
                        db.query(FriendsChat)
                        .filter(
                            FriendsChat.sent_type == 1,
                            or_(
                                and_(
                                    FriendsChat.sender_id == friend_requests.sender_id,
                                    FriendsChat.receiver_id
                                    == friend_requests.receiver_id,
                                ),
                                and_(
                                    FriendsChat.sender_id
                                    == friend_requests.receiver_id,
                                    FriendsChat.receiver_id
                                    == friend_requests.sender_id,
                                ),
                            ),
                            or_(
                                and_(
                                    FriendsChat.sender_id == login_user_id,
                                    FriendsChat.sender_delete == None,
                                ),
                                and_(
                                    FriendsChat.receiver_id == login_user_id,
                                    FriendsChat.receiver_delete == None,
                                ),
                            ),
                        )
                        .order_by(FriendsChat.sent_datetime.desc())
                        .first()
                    )

                    if friend_requests.sender_id == login_user_id:
                        friendid = friend_requests.receiver_id

                        check_user = db.query(User).filter(User.id == friendid).first()
                        online = 0
                        if check_user:
                            app_online = friend_requests.user2.app_online
                            web_online = friend_requests.user2.web_online

                            online = 1 if web_online or app_online else 0
                        friend_status = 0

                        if friend_requests.receiver_id in my_friends:
                            friend_status = 1
                        status_type = "online_status"
                        request_frnds.append(
                            {
                                "friend_request_id": friend_requests.id
                                if friend_requests.id
                                else "",
                                "user_id": friend_requests.user2.id
                                if friend_requests.receiver_id
                                else "",
                                "user_ref_id": friend_requests.user2.user_ref_id
                                if friend_requests.receiver_id
                                else "",
                                
                                "channel_arn":friend_requests.channel_arn 
                                if friend_requests.channel_arn 
                                else "",
                                
                                "email_id": friend_requests.user2.email_id
                                if friend_requests.receiver_id
                                else "",
                                "first_name": friend_requests.user2.first_name
                                if friend_requests.receiver_id
                                else "",
                                "last_name": friend_requests.user2.last_name
                                if friend_requests.receiver_id
                                else "",
                                "display_name": friend_requests.user2.display_name
                                if friend_requests.receiver_id
                                else "",
                                "gender": friend_requests.user2.gender
                                if friend_requests.receiver_id
                                else "",
                                "profile_img": friend_requests.user2.profile_img
                                if friend_requests.receiver_id
                                else "",
                                "online": ProfilePreference(
                                    db,
                                    login_user_id,
                                    friend_requests.receiver_id,
                                    status_type,
                                    online,
                                ),
                                "last_seen": (
                                    common_date(friend_requests.user2.last_seen)
                                    if friend_requests.user2.last_seen
                                    else ""
                                )
                                if friend_requests.receiver_id
                                else "",
                                "typing": 0,
                                "unreadmsg": 0,
                                "follow": True if get_follow_user_id else False,
                                "last_msg": get_last_msg.message
                                if get_last_msg
                                else "",
                                "last_msg_datetime": (
                                    common_date(get_last_msg.sent_datetime)
                                    if get_last_msg.sent_datetime
                                    else ""
                                )
                                if get_last_msg
                                else None,
                                "login_from": friend_login_from,  #  1 - WEB, 2 - APP
                                "login_from_app": friend_requests.user2.app_online
                                if friend_requests.receiver_id
                                else "",  # 1 - true, 0 - False
                                "login_from_web": friend_requests.user2.web_online
                                if friend_requests.receiver_id
                                else "",  # 1 - true, 0 - False
                                "friend_status": friend_status,
                                "chime_user_id": friend_requests.user2.chime_user_id
                                if friend_requests.user2.chime_user_id
                                else None,
                            }
                        )
                    else:
                        friendid = friend_requests.sender_id
                        friend_status = 0
                        if friendid in my_friends:
                            friend_status = 1

                        online = (
                            1
                            if friend_requests.user1.app_online == 1
                            or friend_requests.user1.web_online == 1
                            else 0
                        )
                        status_type = "online_status"
                        request_frnds.append(
                            {
                                "friend_request_id": friend_requests.id
                                if friend_requests.id
                                else "",
                                "user_id": friend_requests.user1.id
                                if friend_requests.sender_id
                                else "",
                                "user_ref_id": friend_requests.user1.user_ref_id
                                if friend_requests.sender_id
                                else "",
                                "channel_arn":friend_requests.channel_arn 
                                if friend_requests.channel_arn 
                                else "",
                                "email_id": friend_requests.user1.email_id
                                if friend_requests.sender_id
                                else "",
                                "first_name": friend_requests.user1.first_name
                                if friend_requests.sender_id
                                else "",
                                "last_name": friend_requests.user1.last_name
                                if friend_requests.sender_id
                                else "",
                                "display_name": friend_requests.user1.display_name
                                if friend_requests.sender_id
                                else "",
                                "gender": friend_requests.user1.gender
                                if friend_requests.sender_id
                                else "",
                                "profile_img": friend_requests.user1.profile_img
                                if friend_requests.sender_id
                                else "",
                                "online": ProfilePreference(
                                    db,
                                    login_user_id,
                                    friend_requests.user1.id,
                                    status_type,
                                    online,
                                ),
                                "last_seen": friend_requests.user1.last_seen
                                if friend_requests.sender_id
                                else "",
                                "typing": 0,
                                "unreadmsg": 0,
                                "follow": True if get_follow_user_id else False,
                                "last_msg": get_last_msg.message
                                if get_last_msg
                                else "",
                                "last_msg_datetime": (
                                    common_date(get_last_msg.sent_datetime)
                                    if get_last_msg.sent_datetime
                                    else ""
                                )
                                if get_last_msg
                                else None,
                                "login_from": friend_login_from,  #  1 - WEB, 2 - APP
                                "login_from_app": friend_requests.user1.app_online
                                if friend_requests.sender_id
                                else "",  # 1 - true, 0 - False
                                "login_from_web": friend_requests.user1.web_online
                                if friend_requests.sender_id
                                else "",  # 1 - true, 0 - False
                                "friend_status": friend_status,
                                "chime_user_id": friend_requests.user1.chime_user_id
                                if friend_requests.user1.chime_user_id
                                else None,
                            }
                        )

                    if friendid != 0:
                        chat = (
                            db.query(FriendsChat)
                            .filter(
                                FriendsChat.sender_id == friendid,
                                FriendsChat.receiver_id == login_user_id,
                                FriendsChat.is_read == 0,
                                FriendsChat.type == 1,
                                FriendsChat.sender_delete == None,
                                FriendsChat.receiver_delete == None,
                            )
                            .count()
                        )
                        if login_from == 1:
                            chat = (
                                db.query(FriendsChat)
                                .filter(
                                    FriendsChat.sender_id == friendid,
                                    FriendsChat.receiver_id == login_user_id,
                                    FriendsChat.is_read == 0,
                                    FriendsChat.type == 1,
                                    FriendsChat.msg_from == 1,
                                    FriendsChat.sender_delete == None,
                                    FriendsChat.receiver_delete == None,
                                )
                                .count()
                            )

                        if chat > 0:
                            request_frnds.append({"unreadmsg": chat})

                return {
                    "status": 1,
                    "msg": "Success",
                    "friends_count": get_my_friends_count,
                    "total_pages": 1,
                    "current_page_no": 1,
                    "friends_list": request_frnds,
                }

        #  ---------------------------- Working -----


# 20 Add Friend Group
# @router.post("/addfriendgroup")
# async def addfriendgroup(db:Session=Depends(deps.get_db),token:str=Form(None),group_name:str=Form(None),group_members:str=Form(None,description=" User ids Like ['12','13','14']"),
#                          group_icon:UploadFile=File(None)):

#     if token == None or token.strip() == "":
#         return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
#     # elif group_name == None or group_name.strip() == "":
#     #     return {"status":0,"msg":"Sorry! Group name can not be empty."}

#     else:
#         access_token=checkToken(db,token)

#         if access_token == False:
#             return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
#         else:
#             get_token_details=db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
#             login_user_id=get_token_details.user_id

#             get_row_count=db.query(FriendGroups).filter(FriendGroups.status == 1,FriendGroups.created_by == login_user_id,FriendGroups.group_name == group_name).count()
#             if get_row_count:
#                 return {"status":0,"msg":"Group name already exists"}

#             else:
#                 # Add Friend Group
#                 add_friend_group=FriendGroups(group_name = group_name.strip(),group_icon=defaultimage('group_icon'),created_by=login_user_id,created_at=datetime.datetime.utcnow(),status =1)
#                 db.add(add_friend_group)
#                 db.commit()

#                 if add_friend_group:
#                     if group_members:
#                         group_members=json.loads(group_members) if group_members else []

#                         for member in group_members:
#                             get_user=db.query(User).filter(User.id == member).first()

#                             if get_user:
#                                 # add Friend Group member
#                                 add_member=FriendGroupMembers(group_id = add_friend_group.id,user_id=member,added_date=datetime.datetime.utcnow(),added_by=login_user_id,is_admin=0,disable_notification=0,status=1)
#                                 db.add(add_member)
#                                 db.commit()

#                                 # add Notification
#                                 add_group_noty=Insertnotification(db,member,login_user_id,17,add_member.id)

#                     # Profile Image
#                     if group_icon:
#                         # file_name=group_icon.filename
#                         # file_temp=group_icon.content_type
#                         file_ext = os.path.splitext(group_icon.filename)[1]

#                         extensions=[".jpeg", ".jpg", ".png"]

#                         if file_ext not in extensions:
#                             return {"status":0,"msg":"Profile Image format does not support"}

#                         s3_file_path=f'groupicon/groupicon_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}'

#                         uploaded_file_path=await file_upload(group_icon,file_ext,compress=1)

#                         result=upload_to_s3(uploaded_file_path,s3_file_path)
#                         if result['status'] == 1:
#                             add_friend_group.group_icon = result['url']
#                             db.commit()

#                         else:
#                             return result


#                     group_details= GetGroupDetails(db,login_user_id,add_friend_group.id)

#                     message_detail={"message":f"{add_friend_group.user.display_name} : created new group",
#                                     "title":add_friend_group.group_name,
#                                     "data":{"refer_id":add_friend_group.id,"type":"add_group"},
#                                     "type":"callend"
#                                     }
#                     notify_members=group_details['group_member_ids']

#                     if add_friend_group.created_by in notify_members:
#                         notify_members.remove(add_friend_group.created_by)

#                     push_notification=pushNotify(db,notify_members,message_detail,login_user_id)

#                     return {"status":1,"msg":"Successfully created group","group_details":group_details}
#                 else:
#                     return {"status":0,"msg":"Failed to create group"}


@router.post("/addfriendgroup")  # Chime Chat
async def addfriendgroup(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_name: str = Form(None),
    group_members: str = Form(None, description=" User ids Like ['12','13','14']"),
    group_icon: UploadFile = File(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    # elif group_name == None or group_name.strip() == "":
    #     return {"status":0,"msg":"Sorry! Group name can not be empty."}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            get_row_count = (
                db.query(FriendGroups)
                .filter(
                    FriendGroups.status == 1,
                    FriendGroups.created_by == login_user_id,
                    FriendGroups.group_name == group_name,
                )
                .count()
            )
            if get_row_count:
                return {"status": 0, "msg": "Group name already exists"}

            else:
                # Add Friend Group
                add_friend_group = FriendGroups(
                    group_name=group_name.strip(),
                    group_icon=defaultimage("group_icon"),
                    created_by=login_user_id,
                    created_at=datetime.datetime.utcnow(),
                    status=0,
                )
                db.add(add_friend_group)
                db.commit()

                if add_friend_group:
                    # Add Friend Group
                    chime_bearer = (
                        get_token_details.user.chime_user_id
                        if get_token_details.user.chime_user_id
                        else None
                    )
                    try:
                        channel_response = create_channel(chime_bearer, group_name)
                        add_friend_group.status = 1
                        # Update Groups ARN
                        add_friend_group.group_arn = (
                            channel_response["ChannelArn"] if channel_response else None
                        )
                        db.commit()
                        
                    except Exception as e:
                        print(e)

                    if group_members:
                        group_members = (
                            json.loads(group_members) if group_members else []
                        )
                        member_id = []
                        for member in group_members:
                            get_user = db.query(User).filter(User.id == member).first()

                            if get_user:
                                member_id.append(
                                    get_user.chime_user_id
                                    if get_user.chime_user_id
                                    else None
                                )
                                # add Friend Group member
                                add_member = FriendGroupMembers(
                                    group_id=add_friend_group.id,
                                    user_id=member,
                                    added_date=datetime.datetime.utcnow(),
                                    added_by=login_user_id,
                                    is_admin=0,
                                    disable_notification=0,
                                    status=1,
                                )
                                db.add(add_member)
                                db.commit()

                                # add Notification
                                add_group_noty = Insertnotification(
                                    db, member, login_user_id, 17, add_member.id
                                )

                        # Add Members to Channel
                        channel_arn = (
                            channel_response["ChannelArn"] if channel_response else None
                        )
                        try:
                            addmembers(channel_arn, chime_bearer, member_id)
                        except Exception as e:
                            print(e)

                    # Profile Image
                    if group_icon:

                        file_ext = os.path.splitext(group_icon.filename)[1]

                        extensions = [".jpeg", ".jpg", ".png"]

                        if file_ext not in extensions:
                            return {
                                "status": 0,
                                "msg": "Profile Image format does not support",
                            }

                        s3_file_path = f"groupicon/groupicon_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                        uploaded_file_path = await file_upload(
                            group_icon, file_ext, compress=1
                        )

                        result = upload_to_s3(uploaded_file_path, s3_file_path)
                        if result["status"] == 1:
                            add_friend_group.group_icon = result["url"]
                            db.commit()

                        else:
                            return result

                    group_details = GetGroupDetails(
                        db, login_user_id, add_friend_group.id
                    )

                    message_detail = {
                        "message": f"{add_friend_group.user.display_name} : created new group",
                        "title": add_friend_group.group_name,
                        "data": {"refer_id": add_friend_group.id, "type": "add_group"},
                        "type": "callend",
                    }
                    notify_members = group_details["group_member_ids"]

                    if add_friend_group.created_by in notify_members:
                        notify_members.remove(add_friend_group.created_by)

                    push_notification = pushNotify(
                        db, notify_members, message_detail, login_user_id
                    )

                    return {
                        "status": 1,
                        "msg": "Successfully created group",
                        "group_details": group_details,
                    }
                else:
                    return {"status": 0, "msg": "Failed to create group"}


# 21 Edit Friend Group
@router.post("/editfriendgroup")
async def editfriendgroup(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_name: str = Form(None),
    group_id: str = Form(None),
    group_icon: UploadFile = File(None),
    group_members: str = Form(None, description=" User ids Like ['12','13','14']"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif group_name == None or group_name.strip() == "":
        return {"status": 0, "msg": "Sorry! Group name can not be empty."}
    elif group_id == None:
        return {"status": 0, "msg": "Sorry! Group id can not be empty."}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

        if group_name.strip() == "":
            return {"status": 0, "msg": "Sorry! Group name can not be empty."}
        else:
            get_frnd_group_count = (
                db.query(FriendGroups)
                .filter(
                    FriendGroups.status == 1,
                    FriendGroups.created_by == login_user_id,
                    FriendGroups.group_name == group_name,
                    FriendGroups.id == group_id,
                )
                .filter(FriendGroups.id != group_id)
                .count()
            )

            if get_frnd_group_count > 0:
                return {"status": 0, "msg": "Group name already exists"}

            else:
                get_group = (
                    db.query(FriendGroups)
                    .filter(
                        FriendGroups.status == 1,
                        FriendGroups.created_by == login_user_id,
                        FriendGroups.id == group_id,
                    )
                    .first()
                )
                if not get_group:
                    return {"status": 0, "msg": "Invlaid Group"}

                else:
                    img_path = get_group.group_icon if get_group.group_icon else None
                    # Update Group Icon
                    if group_icon:

                        file_ext = os.path.splitext(group_icon.filename)[1]

                        extensions = [".jpeg", ".jpg", ".png"]

                        if file_ext not in extensions:
                            return {
                                "status": 0,
                                "msg": "Profile Image format does not support",
                            }

                        s3_file_path = f"groupicon/groupicon_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                        uploaded_file_path = await file_upload(
                            group_icon, file_ext, compress=1
                        )

                        result = upload_to_s3(uploaded_file_path, s3_file_path)
                        if result["status"] == 1:
                            get_group.group_icon = result["url"]
                            db.commit()
                            img_path = result["url"]

                        else:
                            return result

                    if get_group.group_name == "My Fans":
                        if group_icon:
                            update_frnd_group = (
                                db.query(FriendGroups)
                                .filter(FriendGroups.id == get_group.id)
                                .update({"group_icon": img_path})
                            )
                            db.commit()
                            group_details = GetGroupDetails(
                                db, login_user_id, get_group.id
                            )
                            return {
                                "status": 1,
                                "msg": "Successfully updated",
                                "group_details": group_details,
                            }

                        else:
                            return {
                                "status": 0,
                                "msg": "You can't edit the My Fans group.",
                            }

                    if group_members:
                        group_members = (
                            ast.literal_eval(group_members) if group_members else None
                        )
                        member_id = []
                        for member in group_members:
                            if member == get_group.created_by:
                                continue

                            get_user = db.query(User).filter(User.id == member).first()

                            if get_user:
                                check_member = (
                                    db.query(FriendGroupMembers)
                                    .filter(
                                        FriendGroupMembers.status == 1,
                                        FriendGroupMembers.group_id == group_id,
                                        FriendGroupMembers.user_id == member,
                                    )
                                    .first()
                                )

                                if not check_member:
                                    member_id.append(
                                        get_user.chime_user_id
                                        if get_user.chime_user_id
                                        else None
                                    )

                                    add_frnd_group = FriendGroupMembers(
                                        group_id=group_id,
                                        user_id=member,
                                        added_date=datetime.datetime.utcnow(),
                                        added_by=login_user_id,
                                        is_admin=0,
                                        disable_notification=1,
                                        status=1,
                                    )
                                    db.add(add_frnd_group)
                                    db.commit()

                        # Add Member in Channel
                        channel_arn = get_group.group_arn if get_group else None
                        chime_bearer = (
                            get_group.user.chime_user_id
                            if get_group.user.chime_user_id
                            else None
                        )
                        try:
                            addmembers(channel_arn, chime_bearer, member_id)
                        except Exception as e:
                            print(e)
                    update_frnd_group = (
                        db.query(FriendGroups)
                        .filter(FriendGroups.id == get_group.id)
                        .update({"group_name": group_name, "group_icon": img_path})
                    )
                    db.commit()

                    group_details = GetGroupDetails(db, login_user_id, group_id)

                    return {
                        "status": 1,
                        "msg": "Successfully updated",
                        "group_details": group_details,
                    }


# 22 Add Friends to Group
@router.post("/addfriendstogroup")
async def addfriendstogroup(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_members: str = Form(None, description=" User ids Like ['12','13','14']"),
    group_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif group_members == None:
        return {"status": 0, "msg": "Sorry! Group members can not be empty."}
    elif group_id == None:
        return {"status": 0, "msg": "Sorry! Group id can not be empty."}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id
            username = get_token_details.user.display_name

            group_members = json.loads(group_members) if group_members else []

            get_group = (
                db.query(FriendGroups)
                .filter(
                    FriendGroups.status == 1,
                    FriendGroups.created_by == login_user_id,
                    FriendGroups.id == group_id,
                )
                .first()
            )

            if not get_group:
                return {"status": 0, "msg": "Invalid request"}

            elif get_group.group_name == "My Fans":
                return {"status": 0, "msg": "You can't add member in My Fans group"}

            else:
                memberdetails = []
                if group_members != []:
                    member_id = []
                    for member in group_members:
                        get_user = db.query(User).filter(User.id == member).first()

                        if get_user:
                            check_member = (
                                db.query(FriendGroupMembers)
                                .filter(
                                    FriendGroupMembers.status == 1,
                                    FriendGroupMembers.group_id == group_id,
                                    FriendGroupMembers.user_id == member,
                                )
                                .first()
                            )

                            if not check_member:
                                member_id.append(
                                    get_user.chime_user_id
                                    if get_user.chime_user_id
                                    else None
                                )

                                add_frnd_group_member = FriendGroupMembers(
                                    group_id=group_id,
                                    user_id=member,
                                    added_date=datetime.datetime.utcnow(),
                                    added_by=login_user_id,
                                    is_admin=0,
                                    disable_notification=1,
                                    status=1,
                                )
                                db.add(add_frnd_group_member)
                                db.commit()

                                if add_frnd_group_member:
                                    memberdetails.append(
                                        {
                                            "display_name": add_frnd_group_member.user.display_name,
                                            "email_id": add_frnd_group_member.user.email_id,
                                            "first_name": add_frnd_group_member.user.first_name,
                                            "gender": add_frnd_group_member.user.gender,
                                            "last_name": add_frnd_group_member.user.last_name,
                                            "last_seen": add_frnd_group_member.user.last_seen,
                                            "online": "",
                                            "profile_img": add_frnd_group_member.user.profile_img,
                                            "typing": 0,
                                            "user_id": add_frnd_group_member.user_id,
                                        }
                                    )

                    # Add Member in Chime Channel Group
                    channel_arn = get_group.group_arn if get_group.group_arn else None
                    chime_bearer = (
                        get_group.user.chime_user_id
                        if get_group.user.chime_user_id
                        else None
                    )
                    try:
                        addmembers(channel_arn, chime_bearer, member_id)
                    except Exception as e:
                        print(e)

                    group_details = GetGroupDetails(db, login_user_id, get_group.id)

                    message_detail = {
                        "message": f"{username}: added members",
                        "title": get_group.group_name,
                        "data": {"refer_id": get_group.id, "type": "add_group"},
                        "type": "callend",
                    }
                    notify_members = group_details["group_member_ids"]

                    if get_group.created_by in notify_members:
                        notify_members.remove(get_group.created_by)

                    send_push_notification = pushNotify(
                        db, notify_members, message_detail, login_user_id
                    )

                    return {
                        "status": 1,
                        "msg": "Successfully Added",
                        "memberdetails": memberdetails,
                    }

                else:
                    return {"status": 0, "msg": "Failed to add"}


# 23 Remove Friends from Group
@router.post("/removefriendsfromgroup")
async def removefriendsfromgroup(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_members: str = Form(None, description=" User ids Like ['12','13','14']"),
    group_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif group_members == None:
        return {"status": 0, "msg": "Sorry! Group members can not be empty."}
    elif group_id == None:
        return {"status": 0, "msg": "Sorry! Group id can not be empty."}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            group_members = json.loads(group_members) if group_members else []

            get_group = (
                db.query(FriendGroups)
                .filter(
                    FriendGroups.status == 1,
                    FriendGroups.created_by == login_user_id,
                    FriendGroups.id == group_id,
                )
                .first()
            )
            if not get_group:
                return {"status": 0, "msg": "Invalid request"}

            elif get_group.group_name == "My Fans":
                return {"status": 0, "msg": "You can't remove member in My Fans group"}

            else:
                if group_members:
                    for member in group_members:
                        # Delete Member
                        
                        get_members = (
                            db.query(FriendGroupMembers)
                            .filter_by(group_id=group_id, user_id=member)
                        )
                        member_details=get_members.first()
                        
                        # Remove Member in Channel
                        channel_arn = (
                            get_group.group_arn if get_group.group_arn else None
                        )
                        chime_bearer = (
                            get_group.user.chime_user_id
                            if get_group.user.chime_user_id
                            else None
                        )
                        member_id = (
                            member_details.user.chime_user_id
                            if member_details.user.chime_user_id
                            else None
                        )

                        try:
                            delete_channel_membership(
                                channel_arn, chime_bearer, member_id
                            )
                        except Exception as e:
                            return {"status":0,"msg":e}
                        
                        delete_member=get_members.delete()
                        db.commit()

                return {"status": 1, "msg": "Successfully updated"}


# 24. Delete Friend Group
@router.post("/deletefriendgroup")
async def deletefriendgroup(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif group_id == None:
        return {"status": 0, "msg": "Sorry! Group id can not be empty."}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            get_group = (
                db.query(FriendGroups)
                .filter(
                    FriendGroups.created_by == login_user_id,
                    FriendGroups.id == group_id,
                )
                .first()
            )
            if not get_group:
                return {"status": 0, "msg": "Invalid group info"}

            elif get_group.group_name == "My Fans":
                return {"status": 0, "msg": "You can't delete My Fans group"}

            else:
                update_event_invitation = (
                    db.query(EventInvitations)
                    .filter_by(group_id=group_id)
                    .update({"status": 0})
                )
                update_friends_gp_memeber = (
                    db.query(FriendGroupMembers)
                    .filter_by(group_id=group_id)
                    .update({"status": 0})
                )
                update_friends_group = (
                    db.query(FriendGroups).filter_by(id=group_id).update({"status": 0})
                )

                db.commit()

                if update_friends_group:
                    # Delete Chime Channel
                    channel_arn = get_group.group_arn if get_group.group_arn else None
                    chime_bearer = (
                        get_group.user.chime_user_id
                        if get_group.user.chime_user_id
                        else None
                    )
                    try:
                        delete_channel(channel_arn, chime_bearer)
                    except Exception as e:
                        print(e)
                    return {"status": 1, "msg": "Successfully deleted"}

                else:
                    return {"status": 0, "msg": "Failed to delete. please try again"}


# Share Type

# 1 -> Public
# 2 -> Only me
# 3 -> Groups
# 4 -> Individual
# 5 -> Both Group & Individual
# 6 -> All My Friends
# 7-> Only fans

def process_data(
    db, uploaded_file_path, login_user_id, master_id, share_type, share_with
):
    input_file = uploaded_file_path
    output_prefix = f"rawcaster_uploads/output_part_{int(datetime.datetime.utcnow().timestamp())}"  # Prefix for the output video parts
    duration = 299  # Duration of each video part in seconds

    command = [
        "ffmpeg",
        "-i",
        input_file,
        "-c",
        "copy",
        "-map",
        "0",
        "-segment_time",
        str(duration),
        "-f",
        "segment",
        "-reset_timestamps",
        "1",
        output_prefix + "%03d.mp4",
    ]

    # Run the command using subprocess
    subprocess.run(command)

    # Generate the output file paths
    splited_file_path = []
    for i in range(0, 1000):  # Assuming up to 999 output parts
        file_path = output_prefix + f"{i:03d}.mp4"

        if not os.path.exists(file_path):
            break
        splited_file_path.append(file_path)

    
    #remove local file path
    os.remove(uploaded_file_path)
    
    # Connect to S3
    client_s3 = boto3.client(
        "s3", aws_access_key_id=access_key, aws_secret_access_key=access_secret
    )  
    row = 0
    nugget_id = None
    nugget_ids=[]
   
    # Reverse File Path
    tot_length=len(splited_file_path)
    content_location = 1
    content=None
    
    for local_file_pth in splited_file_path[::-1]:
        
        if row == 0:
            # Get last record
            getLastRecord=db.query(NuggetsMaster).filter(NuggetsMaster.user_id == login_user_id).order_by(NuggetsMaster.id.desc()).first()
            content = getLastRecord.content if getLastRecord else None
            getLastRecord.content=None
            db.commit()
            
        else:
            add_nuggets_master = NuggetsMaster(
                user_id=login_user_id,content=content if tot_length == content_location else None,created_date=datetime.datetime.utcnow(), status=0
            )
            db.add(add_nuggets_master)
            db.commit()
        
        content_location = content_location + 1

        s3_file_path = f"nuggets/video_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp4"

        with open(local_file_pth, "rb") as data:  # Upload File To S3
            upload = client_s3.upload_fileobj(
                data, bucket_name, s3_file_path, ExtraArgs={"ACL": "public-read"}
            )

        # Get File Size
        file_stat = os.stat(local_file_pth)
        file_size = file_stat.st_size
        os.remove(local_file_pth)

        # Update Data
        url_location = client_s3.get_bucket_location(Bucket=bucket_name)[
            "LocationConstraint"
        ]
        url = f"https://{bucket_name}.s3.{url_location}.amazonaws.com/{s3_file_path}"
        if url:
            add_nugget_attachment = NuggetsAttachment(
                user_id=login_user_id,
                nugget_id=master_id if row == 0 else add_nuggets_master.id,
                media_type="video",
                media_file_type="mp4",
                file_size=file_size,
                path=url,
                created_date=datetime.datetime.utcnow(),
                status=1,
            )
            db.add(add_nugget_attachment)
            db.commit()
            db.refresh(add_nugget_attachment)

        else:
            return {"status": 0, "msg": "Failed to Upload"}

        # Add Nuggets

        add_nuggets = Nuggets(
            nuggets_id=master_id if row == 0 else add_nuggets_master.id,
            user_id=login_user_id,
            type=1,
            share_type=share_type,
            created_date=datetime.datetime.utcnow(),
        )
        db.add(add_nuggets)
        db.commit()
        db.refresh(add_nuggets)
        
        nugget_ids.append(add_nuggets.id)
        
        nugget_id = add_nuggets.id

        if add_nuggets:
            nuggets = StoreHashTags(db, add_nuggets.id)

            totalmembers = []
            
            if share_type == 6 or share_type == 1:
                requested_by = None
                request_status = 1
                response_type = 1
                search_key = None
                get_member = get_friend_requests(
                    db, login_user_id, requested_by, request_status, response_type
                )

                totalmembers = totalmembers + get_member["accepted"]

            if share_type == 7:
                get_members = getFollowers(db, login_user_id)

            # If share type is Group or Individual
            if share_type == 3 or share_type == 4 or share_type == 5:
                if share_type == 4:
                    share_with["groups"] = ""
                if share_type == 3:
                    share_with["friends"] = ""

                if share_with:
                    for key, val in share_with.items():
                        if val:
                            for shareid in val:
                                type = 2 if key == "friends" else 1
                                add_NuggetsShareWith = NuggetsShareWith(
                                    nuggets_id=add_nuggets.id,
                                    type=type,
                                    share_with=shareid,
                                )
                                db.add(add_NuggetsShareWith)
                                db.commit()

                                if add_NuggetsShareWith:
                                    if key == "friends":
                                        totalmembers.append(shareid)
                                    else:
                                        getgroupmember = (
                                            db.query(FriendGroupMembers)
                                            .filter_by(group_id=shareid)
                                            .all()
                                        )

                                        for member in getgroupmember:
                                            if member.user_id not in totalmembers:
                                                totalmembers.append(member.user_id)
           
            if totalmembers:
                for users in totalmembers:
                    notification_type = 1
                    add_notification = Insertnotification(
                        db, users, login_user_id, notification_type, add_nuggets.id
                    )

                    get_user = db.query(User).filter(User.id == login_user_id).first()
                    user_name = ""
                    if get_user:
                        user_name = get_user.display_name

                    message_detail = {
                        "message": "Posted new Nugget",
                        "data": {"refer_id": add_nuggets.id, "type": "add_nugget"},
                        "type": "nuggets",
                    }
                    send_push_notification = pushNotify(
                        db, totalmembers, message_detail, login_user_id
                    )
                    body = ""
                    sms_message = ""

                    if add_nuggets.id and add_nuggets.id != "":
                        sms_message, body = nuggetNotifcationEmail(
                            db, add_nuggets.id
                        )  # Pending

                    subject = "Rawcaster - Notification"
                    email_detail = {
                        "subject": subject,
                        "mail_message": body,
                        "sms_message": sms_message,
                        "type": "nuggets",
                    }
                    add_notification_sms_email = addNotificationSmsEmail(
                        db, totalmembers, email_detail, login_user_id
                    )

            # # Update Nugget Master
            update_nuggets_master = (
                db.query(NuggetsMaster)
                .filter_by(id=master_id if row == 0 else add_nuggets_master.id)
                .update({"status": 1})
            )
            db.commit()

        row = row + 1

        # Send Push Notification
    message_detail = {
        "message": "Nugget Uploaded Successfully",
        "data": {"refer_id": master_id, "type": "add_nugget"},
        "type": "nuggets",
    }
    # send_push_notification = pushNotify(db, totalmembers, message_detail, login_user_id)

    # # Add Notification for Nugget post upload completed
    # notification_type = 18
    # Insertnotification(db, login_user_id, None, notification_type, nugget_id)
    return nugget_ids


# 25. Add Nuggets
@router.post("/addnuggets")
async def addnuggets(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    content: str = Form(None),
    share_type: str = Form(None),
    share_with: str = Form(None, description='friends":[1,2,3],"groups":[1,2,3]}'),
    nuggets_media: List[UploadFile] = File(None),
    poll_option: str = Form(None),
    poll_duration: str = Form(None),
    metadata: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not content and not nuggets_media:
        return {"status": 0, "msg": "Sorry! Nuggets content or Media can not be empty."}

    elif share_type == None or not share_type.isnumeric():
        return {"status": 0, "msg": "Sorry! Share type can not be empty."}

    else:
        share_type = int(share_type) if share_type else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

        if IsAccountVerified(db, login_user_id) == False:
            return {
                "status": 0,
                "msg": "You need to complete your account validation before you can do this",
            }

        share_with = json.loads(share_with) if share_with else []

        if (share_type == 3 or share_type == 4 or share_type == 5) and not share_with:
            return {"status": 0, "msg": "Sorry! Share with can not be empty."}

        elif share_type == 3 and (
            not share_with.get("groups") or not share_with["groups"]
        ):
            return {"status": 0, "msg": "Sorry! Share with groups list missing."}

        elif share_type == 4 and (
            not share_with.get("friends") or not share_with["friends"]
        ):
            return {"status": 0, "msg": "Sorry! Share with friends list missing."}

        elif share_type == 5 and (
            (not share_with.get("groups") or not share_with["groups"])
            and (not share_with.get("friends") or not share_with["friends"])
        ):
            return {
                "status": 0,
                "msg": "Sorry! Share with groups or friends list missing.",
            }

        else:
            check_content_length = (
                db.query(User)
                .filter(
                    User.id == login_user_id, UserStatusMaster.id == User.user_status_id
                )
                .first()
            )

            if (
                check_content_length
                and content
                and (check_content_length.user_status_master.max_nugget_char)
                < len(content.replace("\n", ""))
            ):
                return {
                    "status": 0,
                    "msg": f"Content length must be less than {check_content_length.user_status_master.max_nugget_char}",
                }

            anyissue = 0

            if share_type == 3 or share_type == 4 or share_type == 5:
                if share_with:
                    for key, val in share_with.items():
                        if val:
                            if key == "group" and (share_type == 3 or share_type == 5):
                                get_groups = db.query(FriendGroups).filter(
                                    FriendGroups.id == val,
                                    FriendGroups.status == 1,
                                    FriendGroups.created_by == login_user_id,
                                )

                                get_groups = {id: id for id, _ in get_groups.all()}

                                if len(get_groups) != len(val):
                                    anyissue = 1

                                elif key == "friends" and (
                                    share_type == 4 or share_type == 5
                                ):
                                    query = db.query(
                                        MyFriends.id,
                                        case(
                                            [
                                                (
                                                    MyFriends.receiver_id
                                                    == login_user_id,
                                                    MyFriends.sender_id,
                                                )
                                            ],
                                            else_=MyFriends.receiver_id,
                                        ).label("receiver_id"),
                                    )
                                    query = query.filter(
                                        MyFriends.status == 1,
                                        MyFriends.request_status == 1,
                                    )
                                    query = query.filter(
                                        (MyFriends.sender_id == login_user_id)
                                        | (MyFriends.receiver_id == login_user_id)
                                    )
                                    query = db.query(FriendGroups).filter(
                                        FriendGroups.id == val,
                                        FriendGroups.status == 1,
                                        FriendGroups.created_by == login_user_id,
                                    )

                                    get_friends = query.all()

                                    if len(set(val) - set(get_friends)) > 0:
                                        anyissue = 1
            if anyissue == 1:
                return {
                    "status": 0,
                    "msg": "Sorry! Share with groups or friends list not correct.",
                }
            else:
                # Set Content for a first Nugget (Only for splited file upload)
                splites_flag=0
                content_location = 1
                looping_count = len(nuggets_media) if nuggets_media else 1

                nugget_details = []
                for i in range(looping_count):
                    nugget_ids=[]
                    
                    nugget_content=detect_and_remove_offensive(content) if content else None
                    
                    add_nuggets_master = NuggetsMaster(
                        user_id=login_user_id,
                        content=nugget_content if looping_count == content_location else None,
                        _metadata=metadata,
                        poll_duration=poll_duration,
                        created_date=datetime.datetime.utcnow(),
                        status=0,
                    )
                    db.add(add_nuggets_master)
                    db.commit()
                    db.refresh(add_nuggets_master)
                    
                    content_location = content_location + 1
                    if add_nuggets_master:
                        # Poll Option save
                        if poll_option:
                            poll_option = json.loads(poll_option) if poll_option else []

                            for option in poll_option:
                                add_NuggetPollOption = NuggetPollOption(
                                    nuggets_master_id=add_nuggets_master.id,
                                    option_name=option.strip(),
                                    created_date=datetime.datetime.utcnow(),
                                    status=1,
                                )

                                db.add(add_NuggetPollOption)
                                db.commit()

                        # Nuggets Media

                        if nuggets_media:
                            master_id = add_nuggets_master.id
                            file_temp = nuggets_media[i - 1].content_type
                            
                            type = "image"
                            if "video" in file_temp:
                                type = "video"
                            elif "audio" in file_temp:
                                type = "audio"
                            # File Upload
                            ext = os.path.splitext(nuggets_media[i - 1].filename)[
                                1
                            ]
                            file_ext=ext if type == 'image' else '.mp3' if type == 'audio' else '.mp4' if type == 'video' else None
                            
                            uploaded_file_path = await file_upload(
                                nuggets_media[i - 1], file_ext, compress=1
                            )
                                                        
                            file_stat = os.stat(uploaded_file_path)
                            file_size = file_stat.st_size

                            if (
                                file_size > 1000000
                                and type == "image"
                                and file_ext != ".gif"
                            ):
                                s3_file_path = f"nuggets/Image_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                                result = upload_to_s3(uploaded_file_path, s3_file_path)
                                if result["status"] == 1:
                                    add_nugget_attachment = NuggetsAttachment(
                                        user_id=login_user_id,
                                        nugget_id=add_nuggets_master.id,
                                        media_type=type,
                                        media_file_type=file_ext,
                                        file_size=file_size,
                                        path=result["url"],
                                        created_date=datetime.datetime.utcnow(),
                                        status=1,
                                    )
                                    db.add(add_nugget_attachment)
                                    db.commit()
                                    db.refresh(add_nugget_attachment)

                                else:
                                    return result

                            else:
                                s3_file_path = f"nuggets/video_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp4"

                                if type == "video":
                                    video = VideoFileClip(
                                                uploaded_file_path
                                            )
                                    total_duration = video.duration
                                    if total_duration < 360:
                                        s3_file_path = f"nuggets/audio_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp4"

                                        result = upload_to_s3(
                                            uploaded_file_path, s3_file_path
                                        )
                                        if result["status"] == 1:
                                            add_nugget_attachment = NuggetsAttachment(
                                                user_id=login_user_id,
                                                nugget_id=add_nuggets_master.id,
                                                media_type=type,
                                                media_file_type=file_ext,
                                                file_size=file_size,
                                                path=result["url"],
                                                created_date=datetime.datetime.utcnow(),
                                                status=1,
                                            )
                                            db.add(add_nugget_attachment)
                                            db.commit()
                                            db.refresh(add_nugget_attachment)
                                        else:
                                            return result
                                    else:
                                        splites_flag=1
                                        splited_video_reposne=process_data(
                                            db,
                                            uploaded_file_path,
                                            login_user_id,
                                            master_id,
                                            share_type,
                                            share_with
                                        )
                                        nugget_ids += splited_video_reposne
                                        
                                    
                                elif type == "audio":
                                    base_dir = "rawcaster_uploads"
                                    try:
                                        os.makedirs(base_dir, mode=0o777, exist_ok=True)
                                    except OSError as e:
                                        sys.exit("Can't create {dir}: {err}".format(dir=base_dir, err=e))

                                    output_dir = base_dir + "/"

                                    characters = string.ascii_letters + string.digits
                                    # Generate the random string
                                    random_string = "".join(random.choice(characters) for i in range(18))

                                    filename = f"uploadfile_{random_string}{ext}"

                                    sub_process_path = f"{output_dir}{filename}"
                                    
                                    ffmpeg_command = ['ffmpeg', '-i', uploaded_file_path, sub_process_path]
                                    try:
                                        subprocess.run(ffmpeg_command, check=True)
                                        print('Audio conversion successful!')
                                    except subprocess.CalledProcessError as e:
                                        print('Error:', e)
                                    
                                    s3_file_path = f"nuggets/audio_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp3"

                                    result = upload_to_s3(
                                        sub_process_path, s3_file_path
                                    )
                                    if result["status"] == 1:
                                        add_nugget_attachment = NuggetsAttachment(
                                            user_id=login_user_id,
                                            nugget_id=add_nuggets_master.id,
                                            media_type=type,
                                            media_file_type=file_ext,
                                            file_size=file_size,
                                            path=result["url"],
                                            created_date=datetime.datetime.utcnow(),
                                            status=1,
                                        )
                                        db.add(add_nugget_attachment)
                                        db.commit()
                                        db.refresh(add_nugget_attachment)
                                    else:
                                        return result

                                else:
                                    result = upload_to_s3(
                                        uploaded_file_path, s3_file_path
                                    )

                                    if result["status"] == 1:
                                        add_nugget_attachment = NuggetsAttachment(
                                            user_id=login_user_id,
                                            nugget_id=add_nuggets_master.id,
                                            media_type=type,
                                            media_file_type=file_ext,
                                            file_size=file_size,
                                            path=result["url"],
                                            created_date=datetime.datetime.utcnow(),
                                            status=1,
                                        )
                                        db.add(add_nugget_attachment)
                                        db.commit()
                                        db.refresh(add_nugget_attachment)
                                    else:
                                        return result
                                    
                            if splites_flag == 0:
                                # Add New Nuggets
                                add_nuggets = Nuggets(
                                    nuggets_id=add_nuggets_master.id,
                                    user_id=login_user_id,
                                    type=1,
                                    share_type=share_type,
                                    created_date=datetime.datetime.utcnow(),
                                )
                                db.add(add_nuggets)
                                db.commit()
                                db.refresh(add_nuggets)

                                if add_nuggets:
                                    nuggets = StoreHashTags(db, add_nuggets.id)

                                    totalmembers = []

                                    if share_type == 6 or share_type == 1:
                                        requested_by = None
                                        request_status = 1
                                        response_type = 1
                                        search_key = None
                                        get_member = get_friend_requests(
                                            db,
                                            login_user_id,
                                            requested_by,
                                            request_status,
                                            response_type,
                                        )

                                        totalmembers = totalmembers + get_member["accepted"]

                                    if share_type == 7:
                                        get_members = getFollowers(db, login_user_id)

                                    # If share type is Group or Individual
                                    if (
                                        share_type == 3
                                        or share_type == 4
                                        or share_type == 5
                                    ):
                                        if share_type == 4:
                                            share_with["groups"] = ""
                                        if share_type == 3:
                                            share_with["friends"] = ""

                                        if share_with:
                                            for key, val in share_with.items():
                                                if val:
                                                    for shareid in val:
                                                        type = 2 if key == "friends" else 1
                                                        add_NuggetsShareWith = (
                                                            NuggetsShareWith(
                                                                nuggets_id=add_nuggets.id,
                                                                type=type,
                                                                share_with=shareid,
                                                            )
                                                        )
                                                        db.add(add_NuggetsShareWith)
                                                        db.commit()

                                                        if add_NuggetsShareWith:
                                                            if key == "friends":
                                                                totalmembers.append(shareid)
                                                            else:
                                                                getgroupmember = (
                                                                    db.query(
                                                                        FriendGroupMembers
                                                                    )
                                                                    .filter_by(
                                                                        group_id=shareid
                                                                    )
                                                                    .all()
                                                                )

                                                                for (
                                                                    member
                                                                ) in getgroupmember:
                                                                    if (
                                                                        member.user_id
                                                                        not in totalmembers
                                                                    ):
                                                                        totalmembers.append(
                                                                            member.user_id
                                                                        )

                                    if totalmembers:
                                        for users in totalmembers:
                                            notification_type = 1
                                            add_notification = Insertnotification(
                                                db,
                                                users,
                                                login_user_id,
                                                notification_type,
                                                add_nuggets.id,
                                            )

                                            get_user = (
                                                db.query(User)
                                                .filter(User.id == login_user_id)
                                                .first()
                                            )
                                            user_name = ""
                                            if get_user:
                                                user_name = get_user.display_name

                                            message_detail = {
                                                "message": "Posted new Nugget",
                                                "data": {
                                                    "refer_id": add_nuggets.id,
                                                    "type": "add_nugget",
                                                },
                                                "type": "nuggets",
                                            }
                                            send_push_notification = pushNotify(
                                                db,
                                                totalmembers,
                                                message_detail,
                                                login_user_id,
                                            )
                                            body = ""
                                            sms_message = ""

                                            if add_nuggets.id and add_nuggets.id != "":
                                                sms_message, body = nuggetNotifcationEmail(
                                                    db, add_nuggets.id
                                                )  # Pending

                                            subject = "Rawcaster - Notification"
                                            email_detail = {
                                                "subject": subject,
                                                "mail_message": body,
                                                "sms_message": sms_message,
                                                "type": "nuggets",
                                            }
                                            add_notification_sms_email = (
                                                addNotificationSmsEmail(
                                                    db,
                                                    totalmembers,
                                                    email_detail,
                                                    login_user_id,
                                                )
                                            )

                                    nugget_detail = get_nugget_detail(
                                        db, add_nuggets.id, login_user_id
                                    )  # Pending

                                    # Update Nugget Master
                                    update_nuggets_master = (
                                        db.query(NuggetsMaster)
                                        .filter_by(id=add_nuggets_master.id)
                                        .update({"status": 1})
                                    )
                                    db.commit()

                                    nugget_details.append(nugget_detail)
                                else:
                                    return {"status": 0, "msg": "Failed to create Nugget"}
                            else:
                                
                                for nugt in nugget_ids:
                                    
                                    nugget_detail = get_nugget_detail(
                                        db, nugt, login_user_id
                                    ) 
                                    nugget_details.append(nugget_detail)
                                    
                                
                        else:
                            
                            # Add New Nuggets
                            add_nuggets = Nuggets(
                                nuggets_id=add_nuggets_master.id,
                                user_id=login_user_id,
                                type=1,
                                share_type=share_type,
                                created_date=datetime.datetime.utcnow(),
                            )
                            db.add(add_nuggets)
                            db.commit()
                            db.refresh(add_nuggets)

                            if add_nuggets:
                                nuggets = StoreHashTags(db, add_nuggets.id)

                                totalmembers = []

                                if share_type == 6 or share_type == 1:
                                    requested_by = None
                                    request_status = 1
                                    response_type = 1
                                    search_key = None
                                    get_member = get_friend_requests(
                                        db,
                                        login_user_id,
                                        requested_by,
                                        request_status,
                                        response_type,
                                    )

                                    totalmembers = totalmembers + get_member["accepted"]

                                if share_type == 7:
                                    get_members = getFollowers(db, login_user_id)

                                # If share type is Group or Individual
                                if (
                                    share_type == 3
                                    or share_type == 4
                                    or share_type == 5
                                ):
                                    if share_type == 4:
                                        share_with["groups"] = ""
                                    if share_type == 3:
                                        share_with["friends"] = ""

                                    if share_with:
                                        for key, val in share_with.items():
                                            if val:
                                                for shareid in val:
                                                    type = 2 if key == "friends" else 1
                                                    add_NuggetsShareWith = (
                                                        NuggetsShareWith(
                                                            nuggets_id=add_nuggets.id,
                                                            type=type,
                                                            share_with=shareid,
                                                        )
                                                    )
                                                    db.add(add_NuggetsShareWith)
                                                    db.commit()

                                                    if add_NuggetsShareWith:
                                                        if key == "friends":
                                                            totalmembers.append(shareid)
                                                        else:
                                                            getgroupmember = (
                                                                db.query(
                                                                    FriendGroupMembers
                                                                )
                                                                .filter_by(
                                                                    group_id=shareid
                                                                )
                                                                .all()
                                                            )

                                                            for (
                                                                member
                                                            ) in getgroupmember:
                                                                if (
                                                                    member.user_id
                                                                    not in totalmembers
                                                                ):
                                                                    totalmembers.append(
                                                                        member.user_id
                                                                    )

                                if totalmembers:
                                    for users in totalmembers:
                                        notification_type = 1
                                        add_notification = Insertnotification(
                                            db,
                                            users,
                                            login_user_id,
                                            notification_type,
                                            add_nuggets.id,
                                        )

                                        get_user = (
                                            db.query(User)
                                            .filter(User.id == login_user_id)
                                            .first()
                                        )
                                        user_name = ""
                                        if get_user:
                                            user_name = get_user.display_name

                                        message_detail = {
                                            "message": "Posted new Nugget",
                                            "data": {
                                                "refer_id": add_nuggets.id,
                                                "type": "add_nugget",
                                            },
                                            "type": "nuggets",
                                        }
                                        send_push_notification = pushNotify(
                                            db,
                                            totalmembers,
                                            message_detail,
                                            login_user_id,
                                        )
                                        body = ""
                                        sms_message = ""

                                        if add_nuggets.id and add_nuggets.id != "":
                                            sms_message, body = nuggetNotifcationEmail(
                                                db, add_nuggets.id
                                            )  # Pending

                                        subject = "Rawcaster - Notification"
                                        email_detail = {
                                            "subject": subject,
                                            "mail_message": body,
                                            "sms_message": sms_message,
                                            "type": "nuggets",
                                        }
                                        add_notification_sms_email = (
                                            addNotificationSmsEmail(
                                                db,
                                                totalmembers,
                                                email_detail,
                                                login_user_id,
                                            )
                                        )

                                nugget_detail = get_nugget_detail(
                                    db, add_nuggets.id, login_user_id
                                )

                                # Update Nugget Master
                                update_nuggets_master = (
                                    db.query(NuggetsMaster)
                                    .filter_by(id=add_nuggets_master.id)
                                    .update({"status": 1})
                                )
                                db.commit()

                                nugget_details.append(nugget_detail)
                            else:
                                return {"status": 0, "msg": "Failed to create Nugget"}
                    else:
                        return {"status": 0, "msg": "Failed to create Nugget master"}

                return {
                    "status": 1,
                    "msg": "Nuggets created successfully!",
                    "nugget_detail": sorted(
                        nugget_details, key=lambda x: x["nugget_id"]
                    ),
                }
                
     
# 26. List Nuggets
@router.post("/listnuggets")  
async def listnuggets(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    my_nuggets: str = Form(None),
    filter_type: str = Form(None, description="1-Influencer"),
    category: str = Form(None, description="Influencer category"),
    user_id: str = Form(None),
    saved: str = Form(None),
    search_key: str = Form(None),
    page_number: str = Form(default=1),
    nugget_type: str = Form(None, description="1-video,2-Other than video,0-all"),
    ):
    
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_type and not nugget_type.isnumeric():
        return {"status": 0, "msg": "Invalid Nugget Type"}

    elif nugget_type and not 0 <= int(nugget_type) <= 2:
        return {"status": 0, "msg": "Invalid Nugget Type"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        nugget_type = int(nugget_type) if nugget_type else None
        filter_type = int(filter_type) if filter_type else None
        saved = int(saved) if saved else None

        access_token = checkToken(db, token) if token != "RAWCAST" else True
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
            )
            login_user_id=0
            user_public_nugget_display_setting = 1
            if get_token_details:
                login_user_id = get_token_details.user_id

                get_user_settings = (
                    db.query(UserSettings.public_nugget_display)
                    .filter(UserSettings.user_id == login_user_id)
                    .first()
                )
                if get_user_settings:
                    user_public_nugget_display_setting = (
                        get_user_settings.public_nugget_display
                    )

            current_page_no = int(page_number)
            user_id = int(user_id) if user_id else None

            group_ids = getGroupids(db, login_user_id)
            requested_by = None
            request_status = 1  # Pending
            response_type = 1
            my_frnds = get_friend_requests(
                db, login_user_id, requested_by, request_status, response_type
            )
            my_friends = my_frnds["accepted"]
            
            my_followings = getFollowings(db, login_user_id)

            type = None
            raw_id = GetRawcasterUserID(db, type)
            
            get_nuggets=db.query(Nuggets)\
                        .options(joinedload(Nuggets.nuggets_master))\
                        .join(User,Nuggets.user_id == User.id,isouter=True)\
                        .join(NuggetsMaster,Nuggets.nuggets_id == NuggetsMaster.id,isouter=True)\
                        .join(NuggetsShareWith,NuggetsShareWith.nuggets_id == Nuggets.id,isouter=True)\
                        .join(NuggetsSave,Nuggets.id == NuggetsSave.nugget_id,isouter=True)\
                        .filter(Nuggets.status == 1,
                                Nuggets.nugget_status == 1,
                                NuggetsMaster.status == 1)\
                        .group_by(Nuggets.id)
            
            if search_key:
                get_nuggets = get_nuggets.filter(
                    or_(
                        NuggetsMaster.content.ilike("%" + search_key + "%"),
                        User.display_name.ilike("%" + search_key + "%"),
                        User.first_name.ilike("%" + search_key + "%"),
                        User.last_name.ilike("%" + search_key + "%"),
                    )
                )
            if access_token == "RAWCAST":
                get_nuggets = get_nuggets.join( NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id).filter(Nuggets.share_type == 1)
                
                if nugget_type == 1:  # Video Nugget
                    get_nuggets = get_nuggets.filter(NuggetsAttachment.media_type == "video")

                elif nugget_type == 2:  # Other type
                    get_nuggets = get_nuggets.filter(
                        or_(
                            NuggetsAttachment.media_type == None,
                            NuggetsAttachment.media_type == "image",
                            NuggetsAttachment.media_type == "audio",
                        )
                    )  
            elif my_nuggets == 1:  # My Nuggets
                get_nuggets = get_nuggets.filter(Nuggets.user_id == login_user_id)
            
            elif saved == 1:     # Saved Nuggets
                get_nuggets = get_nuggets.filter(NuggetsSave.user_id == login_user_id)
                
            elif user_id:        # Other's Nuggets
                if login_user_id != user_id:
                    get_nuggets = get_nuggets.filter(
                        Nuggets.user_id == user_id, Nuggets.share_type == 1
                    )
                get_nuggets = get_nuggets.filter(Nuggets.user_id == user_id)
            
            else:
                if nugget_type == 1:  # Video
                    get_nuggets = get_nuggets.filter(
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                        NuggetsAttachment.media_type == "video",
                    )
                
                if nugget_type == 2:  # Audio and Image
                    get_nuggets = get_nuggets.outerjoin(
                        NuggetsAttachment,
                        Nuggets.nuggets_id == NuggetsAttachment.nugget_id,
                    ).filter(
                        or_(
                            NuggetsAttachment.media_type == None,
                            NuggetsAttachment.media_type == "image",
                            NuggetsAttachment.media_type == "audio",
                        )
                    )
                if filter_type == 1:
                    my_followers = []  # my_followers
                    follow_user = (
                        db.query(FollowUser.following_userid)
                        .filter(FollowUser.follower_userid == login_user_id)
                        .all()
                    )
                    if follow_user:
                        for group_list in follow_user:
                            my_followers.append(group_list.following_userid)
                    
                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(Nuggets.user_id.in_(my_followers)),
                            Nuggets.share_type != 2,
                        )
                    )
                    
                elif user_public_nugget_display_setting == 0:  # Rawcaster
                    get_nuggets = get_nuggets.filter(
                        or_(Nuggets.user_id == login_user_id, Nuggets.user_id == raw_id)
                    )
                    
                elif user_public_nugget_display_setting == 1:  # Public
                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(Nuggets.share_type == 1),
                            and_(
                                Nuggets.share_type == 2,
                                Nuggets.user_id == login_user_id,
                            ),
                            and_(
                                Nuggets.share_type == 3,
                                NuggetsShareWith.type == 1,
                                NuggetsShareWith.share_with.in_(group_ids),
                            ),
                            and_(
                                Nuggets.share_type == 4,
                                NuggetsShareWith.type == 2,
                                NuggetsShareWith.share_with.in_([login_user_id]),
                            ),
                            and_(
                                Nuggets.share_type == 6, Nuggets.user_id.in_(my_friends)
                            ),
                            and_(
                                Nuggets.share_type == 7,
                                Nuggets.user_id.in_(my_followings),
                            ),
                            and_(Nuggets.user_id == raw_id),
                        )
                    )    
                elif user_public_nugget_display_setting == 2:  # All Connections
                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(
                                Nuggets.user_id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 3:  # Specific Connections
                    my_friends = []  # Selected Connections id's

                    online_group_list = (
                        db.query(UserProfileDisplayGroup)
                        .filter(
                            UserProfileDisplayGroup.user_id == login_user_id,
                            UserProfileDisplayGroup.profile_id
                            == "public_nugget_display",
                        )
                        .all()
                    )

                    if online_group_list:
                        for group_list in online_group_list:
                            my_friends.append(group_list.groupid)
                    get_nuggets = get_nuggets.filter(
                        or_(
                            and_(Nuggets.user_id == login_user_id),
                            and_(
                                Nuggets.user_id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 4:  # All Groups
                    get_nuggets = get_nuggets.join(
                        FriendGroupMembers,
                        Nuggets.user_id == FriendGroupMembers.user_id,
                        isouter=True,
                    )
                    get_nuggets = get_nuggets.join(
                        FriendGroups, FriendGroupMembers.group_id == FriendGroups.id,isouter=True
                    ).filter(FriendGroups.status == 1)
                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(
                                FriendGroups.created_by == login_user_id,
                                Nuggets.share_type != 2,
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 5:  # Specific Groups
                    my_friends = []
                    online_group_list = (
                        db.query(UserProfileDisplayGroup)
                        .filter(
                            UserProfileDisplayGroup.user_id == login_user_id,
                            UserProfileDisplayGroup.profile_id
                            == "public_nugget_display",
                        )
                        .all()
                    )
                    if online_group_list:
                        for group_list in online_group_list:
                            my_friends.append(group_list.groupid)

                    get_nuggets = get_nuggets.join(
                        FriendGroupMembers,
                        Nuggets.user_id == FriendGroupMembers.user_id,
                    )
                    get_nuggets = get_nuggets.join(
                        FriendGroups, FriendGroupMembers.group_id == FriendGroups.id
                    ).filter(FriendGroups.status == 1)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(
                                FriendGroups.id.in_(my_friends), Nuggets.share_type != 2
                            ),
                        )
                    )

                elif user_public_nugget_display_setting == 6:  # My influencers
                    my_followers = []  # Selected Connections id's
                    follow_user = (
                        db.query(FollowUser)
                        .filter(FollowUser.follower_userid == login_user_id)
                        .all()
                    )
                    if follow_user:
                        for group_list in follow_user:
                            my_followers.append(group_list.following_userid)

                    get_nuggets = get_nuggets.filter(
                        or_(
                            Nuggets.user_id == login_user_id,
                            and_(Nuggets.user_id.in_(my_followers)),
                            Nuggets.share_type != 2,
                        )
                    )  
                else:
                    get_nuggets=get_nuggets.filter(User.influencer_category.like("%" + category + "%"))
                    
            # Omit blocked users nuggets
            requested_by = None
            request_status = 3  # Rejected
            response_type = 1

            get_all_blocked_users = get_friend_requests(
                db, login_user_id, requested_by, request_status, response_type
            )
            
            blocked_users = get_all_blocked_users["blocked"]

            if blocked_users:
                get_nuggets = get_nuggets.filter(Nuggets.user_id.not_in(blocked_users))

            get_nuggets = get_nuggets.order_by(Nuggets.created_date.desc())

            get_nuggets_count = get_nuggets.count()
            
            if get_nuggets_count < 1:
                return {"status": 0, "msg": "No Result found"}
            else:
                default_page_size = 20
                limit, offset, total_pages = get_pagination(
                    get_nuggets_count, current_page_no, default_page_size)
                
                get_nuggets = get_nuggets.limit(limit).offset(offset).all()
                
                nuggets_list=[]
                
                for nuggets in get_nuggets:
                    attachments=[]
                    poll_options=[]
                    is_downloadable=[]
                    shared_detail=[]
                    
                    total_likes=nuggets.total_like_count
                    total_comments=nuggets.total_comment_count
                    total_views=nuggets.total_view_count
                    total_poll=nuggets.total_poll_count
                    img_count=0
                    
                    if login_user_id == nuggets.user_id and nuggets.nuggets_share_with:
                        shared_group_ids=[]
                        type=0
                        nugget_share_details=nuggets.nuggets_share_with
                        
                        for share_nugget in nugget_share_details:
                            type=share_nugget.type
                            shared_group_ids.append(share_nugget.share_with)
                        
                        if type == 1:
                            friend_groups=db.query(FriendGroups.group_name,FriendGroups.group_icon)\
                                .filter(FriendGroups.id.in_(shared_group_ids)).all()
                            
                            for frnf_gp in friend_groups:
                                shared_detail.append({'name':frnf_gp.group_name,'img':frnf_gp.group_icon})

                        elif type == 2:
                            friend_groups=db.query(User.display_name,User.profile_img)\
                                .filter(User.id.in_(shared_group_ids)).all()
                            
                            for frnf_gp in friend_groups:
                                shared_detail.append({'name':frnf_gp.display_name,'img':frnf_gp.profile_img})

                    # Nugget Attachments
                    if nuggets.nuggets_master.nuggets_attachment:
                    
                        nugget_attachments=nuggets.nuggets_master.nuggets_attachment
                        for nug_attch in nugget_attachments:
                            
                            img_count += 1
                            if nug_attch.status == 1:
                                
                                if nugget_type == 2:
                                    if nug_attch.media_type != 'video':
                                        
                                        attachments.append(
                                                {
                                                    "media_id": nug_attch.id,
                                                    "media_type": nug_attch.media_type,
                                                    "media_file_type": nug_attch.media_file_type,
                                                    "path": nug_attch.path,
                                                }
                                            )
                                elif nugget_type == 1:
                                    
                                    if nug_attch.media_type == 'video':
                                        attachments.append(
                                                {
                                                    "media_id": nug_attch.id,
                                                    "media_type": nug_attch.media_type,
                                                    "media_file_type": nug_attch.media_file_type,
                                                    "path": nug_attch.path,
                                                }
                                            )
                                else:
                                    attachments.append(
                                                {
                                                    "media_id": nug_attch.id,
                                                    "media_type": nug_attch.media_type,
                                                    "media_file_type": nug_attch.media_file_type,
                                                    "path": nug_attch.path,
                                                }
                                            )
                                    
                    # Nugget Poll Options
                    if nuggets.nuggets_master.nugget_poll_option:
                        nugget_poll_options=nuggets.nuggets_master.nugget_poll_option
                        
                        for nug_poll in nugget_poll_options:
                            if nug_poll.status == 1:
                                poll_options.append({'option_id':nug_poll.id,"option_name":nug_poll.option_name,
                                                     "option_percentage":nug_poll.poll_vote_percentage,
                                                     "votes":nug_poll.votes})

                    following = (
                        db.query(FollowUser)
                        .filter(
                            FollowUser.follower_userid == login_user_id,
                            FollowUser.following_userid == nuggets.user_id,
                        )
                        .count()
                    )
                    
                    follow_count = (
                        db.query(FollowUser)
                        .filter(FollowUser.following_userid == nuggets.user_id)
                        .count()
                    )
                    
                    nugget_like = False
                    nugget_view=False
                    
                    checklike = (
                        db.query(NuggetsLikes)
                        .filter(
                            NuggetsLikes.nugget_id == nuggets.id,
                            NuggetsLikes.user_id == login_user_id,
                        )
                        .first()
                    )
                    checkview=db.query(NuggetView).filter(NuggetView.nugget_id == nuggets.id,NuggetView.user_id == login_user_id).first()
                    if checklike:
                        nugget_like=True
                    if checkview:
                        nugget_view=True
                    
                    if login_user_id == nuggets.user_id:
                        following=1
                    
                    voted = (
                        db.query(NuggetPollVoted)
                        .filter(
                            NuggetPollVoted.nugget_id == nuggets.id,
                            NuggetPollVoted.user_id == login_user_id,
                        )
                        .first()
                    )
                    saved = (
                        db.query(NuggetsSave)
                        .filter(
                            NuggetsSave.nugget_id == nuggets.id,
                            NuggetsSave.user_id == login_user_id,
                            NuggetsSave.status == 1,
                        )
                        .count()
                    )
                    
                    if nuggets.share_type == 1:
                        if following == 1:
                            is_downloadable=1
                        else:
                            user_id=nuggets.user_id
                            get_friend_request = db.query(MyFriends).filter(
                                MyFriends.status == 1, MyFriends.request_status == 1
                            )

                            get_friend_request = (
                                get_friend_request.filter(
                                    or_(
                                        and_(
                                            MyFriends.sender_id == login_user_id,
                                            MyFriends.receiver_id == user_id,
                                        ),
                                        and_(
                                            MyFriends.sender_id == user_id,
                                            MyFriends.receiver_id == login_user_id,
                                        ),
                                    )
                                )
                                .order_by(MyFriends.id.desc())
                                .first()
                            )

                            if get_friend_request:
                                is_downloadable = 1
                    else:
                        is_downloadable = 1 
                    
                    # Check account Verification
                    check_verify = (
                        db.query(VerifyAccounts)
                        .filter(
                            VerifyAccounts.user_id == nuggets.user_id,
                            VerifyAccounts.verify_status == 1,
                        )
                        .first()
                    )
                    
                    nuggets_list.append({"nugget_id":nuggets.id,
                                        "content": nuggets.nuggets_master.content,
                                        "metadata": nuggets.nuggets_master._metadata,
                                        'created_date':common_date(nuggets.created_date),
                                        'user_id':nuggets.user_id,
                                        'user_ref_id':nuggets.user.user_ref_id,
                                        'account_verify_type':1 if check_verify else 0,
                                        'type':nuggets.type,
                                        'original_user_id':nuggets.user.id,
                                        'original_user_name':nuggets.nuggets_master.user.display_name,
                                        'original_user_image':nuggets.nuggets_master.user.profile_img,
                                        'user_name':nuggets.user.display_name,
                                        'user_image':nuggets.user.profile_img,
                                        'user_status_id':nuggets.user.user_status_id,
                                        "liked":nugget_like,
                                        'viewed':0,
                                        "following":True if following else False,
                                        'follow_count':follow_count,
                                        'total_likes':total_likes,
                                        'total_comments':total_comments,
                                        'total_views':total_views,
                                        'total_media':img_count,
                                        'share_type':nuggets.share_type,
                                        'media_list':attachments,
                                        'is_nugget_owner':1 if nuggets.user_id == login_user_id else 0,
                                        'is_master_nugget_owner':1 if nuggets.nuggets_master.user_id == login_user_id else 0,
                                        'shared_detail':shared_detail,
                                        'shared_with':[],
                                        'is_downloadable':is_downloadable,
                                        'poll_option':poll_options,
                                        'poll_duration':nuggets.nuggets_master.poll_duration,
                                        'voted': 1 if voted else 0,
                                        'voted_option': voted.poll_option_id if voted else None,
                                        'total_vote':total_poll,
                                        'saved': True if saved else False
                                        })
                
                return {
                    "status": 1,
                    "msg": "Success",
                    "nuggets_count": get_nuggets_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "nuggets_list": nuggets_list
                    }     
 
            
# 27. Like And Unlike Nugget
@router.post("/likeandunlikenugget")
async def likeandunlikenugget(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
    like: str = Form(None, description="1-like,2-unlike"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_id == None and not nugget_id.isnumeric():
        return {"status": 0, "msg": "Nugget id is missing"}
    elif like == None:
        return {"status": 0, "msg": "Like flag is missing"}
    elif like and not like.isnumeric() and like != 1 and like != 2:
        return {"status": 0, "msg": "Like flag is invalid"}

    else:
        like = int(like) if like else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            access_check = NuggetAccessCheck(db, login_user_id, nugget_id)

            if not access_check:
                return {"status": 0, "msg": "Unauthorized access"}

            check_nuggets = db.query(Nuggets).filter(Nuggets.id == nugget_id).first()

            if check_nuggets:
                if like == 1:
                    checkpreviouslike = (
                        db.query(NuggetsLikes)
                        .filter(
                            NuggetsLikes.nugget_id == nugget_id,
                            NuggetsLikes.user_id == login_user_id,
                        )
                        .first()
                    )
                    if not checkpreviouslike:
                        nuggetlike = NuggetsLikes(
                            user_id=login_user_id,
                            nugget_id=nugget_id,
                            created_date=datetime.datetime.utcnow(),
                            status=1,
                        )
                        db.add(nuggetlike)
                        db.commit()

                        if nuggetlike:
                            # Update Total Like count in Nugget table
                            check_nuggets.total_like_count = check_nuggets.total_like_count + 1
                            db.commit()
                            
                            notification_type = 5
                            Insertnotification(
                                db,
                                check_nuggets.user_id,
                                login_user_id,
                                notification_type,
                                nugget_id,
                            )

                            return {"status": 1, "msg": "Success"}

                        else:
                            return {"status": 0, "msg": "failed to ilike"}

                    else:
                        return {"status": 0, "msg": "Your already liked this nugget"}

                elif like == 2:
                    checkpreviouslike = (
                        db.query(NuggetsLikes)
                        .filter(
                            NuggetsLikes.nugget_id == nugget_id,
                            NuggetsLikes.user_id == login_user_id,
                        )
                        .first()
                    )
                    if checkpreviouslike:
                        deleteresult = (
                            db.query(NuggetsLikes)
                            .filter_by(id=checkpreviouslike.id)
                            .delete()
                        )
                        db.commit()
                        
                        # Update Total Like count in Nugget table
                        check_nuggets.total_like_count = check_nuggets.total_like_count - 1 if check_nuggets.total_like_count else 0
                        db.commit()

                        if deleteresult:
                            return {"status": 1, "msg": "Success"}

                        else:
                            return {"status": 0, "msg": "failed to unlike"}

                    else:
                        return {"status": 0, "msg": "you not yet liked this nugget"}

                else:
                    return {"status": 0, "msg": "Invalid Like type"}


# 28. Delete Nugget
@router.post("/deletenugget")
async def deletenugget(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not nugget_id:
        return {"status": 0, "msg": "Nugget id is missing"}

    else:
        access_token = checkToken(db, token)
        nugget_id = int(nugget_id)
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            check_nugget_creater = (
                db.query(Nuggets)
                .filter(Nuggets.id == nugget_id, Nuggets.user_id == login_user_id)
                .first()
            )
            if check_nugget_creater:
                delete_nuggets = (
                    db.query(Nuggets)
                    .filter(Nuggets.id == check_nugget_creater.id)
                    .update({"nugget_status": 2})
                )
                db.commit()

                if delete_nuggets:
                    if check_nugget_creater.type == 1:
                        update_nugget_master = (
                            db.query(NuggetsMaster)
                            .filter_by(id=check_nugget_creater.nuggets_id)
                            .update({"status": 0})
                        )
                        update_notification = (
                            db.query(Notification).filter_by(ref_id=nugget_id).delete()
                        )
                        delete_save_nugget = (
                            db.query(NuggetsSave)
                            .filter(
                                NuggetsSave.user_id == login_user_id,
                                NuggetsSave.nugget_id == nugget_id,
                            )
                            .update({"status": 0})
                        )
                        db.commit()

                        return {"status": 1, "msg": "Nugget Deleted"}
                    else:
                        return {"status": 1, "msg": "Nugget Deleted"}

                else:
                    return {"status": 0, "msg": "Unable to delete"}

            else:
                return {"status": 0, "msg": "Invalid nugget id"}


# 29. Nugget Comment List
@router.post("/nuggetcommentlist")
async def nuggetcommentlist(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not nugget_id:
        return {"status": 0, "msg": "Nugget id is missing"}
    else:
        nugget_id = int(nugget_id)
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            access_check = NuggetAccessCheck(db, login_user_id, nugget_id)

            if not access_check:
                return {"status": 0, "msg": "Unauthorized access"}

            check_nuggets = db.query(Nuggets).filter_by(id=nugget_id).first()
            if check_nuggets:
                commentlist = (
                    db.query(
                        NuggetsComments, NuggetsCommentsLikes.user_id.label("liked")
                    )
                    .outerjoin(
                        NuggetsCommentsLikes,
                        (NuggetsCommentsLikes.comment_id == NuggetsComments.id)
                        & (NuggetsCommentsLikes.user_id == login_user_id),
                    )
                    .filter(NuggetsComments.nugget_id == check_nuggets.id)
                    .filter(NuggetsComments.parent_id == None)
                    .group_by(NuggetsComments.id)
                    .order_by(NuggetsComments.modified_date.asc())
                    .all()
                )

                result_list = []
                if commentlist:
                    count = 0
                    for comment in commentlist:
                        total_like = 0
                        get_cmt_likes = db.query(NuggetsCommentsLikes).filter(
                            NuggetsCommentsLikes.comment_id
                            == comment["NuggetsComments"].id
                        )
                        get_cmt_like = get_cmt_likes.all()

                        if get_cmt_like:
                            total_like = get_cmt_likes.count()

                        replyarray = []

                        get_cmt_like = (
                            db.query(NuggetsComments)
                            .filter(
                                NuggetsComments.parent_id
                                == comment["NuggetsComments"].id,
                                NuggetsComments.status == 1,
                            )
                            .all()
                        )
                        if get_cmt_like:
                            for reply in get_cmt_like:
                                ilike = False
                                likes = db.query(NuggetsCommentsLikes).filter(
                                    NuggetsCommentsLikes.nugget_id == nugget_id,
                                    NuggetsCommentsLikes.comment_id == reply.id,
                                )

                                if ilike:
                                    user_like = likes.filter(
                                        NuggetsCommentsLikes.user_id == reply.user_id
                                    ).first()
                                    if user_like:
                                        ilike = True
                                total_like = likes.count()
                                replyarray.append(
                                    {
                                        "comment_id": reply.id,
                                        "user_id": reply.user_id,
                                        "editable": True
                                        if login_user_id == reply.user_id
                                        else False,
                                        "name": reply.user.display_name,
                                        "profile_image": reply.user.profile_img,
                                        "comment": reply.content,
                                        "commented_date": reply.created_date,
                                        "liked": ilike,
                                        "like_count": total_like,
                                    }
                                )
                        result_list.append(
                            {
                                "comment_id": comment["NuggetsComments"].id,
                                "user_id": comment["NuggetsComments"].user_id,
                                "editable": True
                                if comment["NuggetsComments"].user_id == login_user_id
                                else False,
                                "name": comment["NuggetsComments"].user.display_name,
                                "profile_image": comment[
                                    "NuggetsComments"
                                ].user.profile_img,
                                "comment": comment["NuggetsComments"].content,
                                "commented_date": comment[
                                    "NuggetsComments"
                                ].created_date,
                                "liked": True
                                if comment["liked"] and comment["liked"] > 0
                                else False,
                                "like_count": total_like,
                                "reply": replyarray,
                            }
                        )

                    return {"status": 1, "msg": "Success", "comments": result_list}
                else:
                    return {"status": 0, "msg": "No Comments"}

            else:
                return {"status": 0, "msg": "Invalid Nugget id"}


# 30. Add or Reply Nugget Comment
@router.post("/addnuggetcomment")
async def addnuggetcomment(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    type: str = Form(None, description="1-comment,2-reply"),
    nugget_id: str = Form(None),
    comment_id: str = Form(None),
    comment: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif not nugget_id:
        return {"status": 0, "msg": "Nugget id is missing"}
    elif type and not type.isnumeric():
        return {"status": 0, "msg": "Invalid type flag"}
    elif comment_id and not comment_id.isnumeric():
        return {"status": 0, "msg": "Invalid comment id"}
    elif int(type) == 2 and not comment_id:
        return {"status": 0, "msg": "comment id required"}
    elif comment == None or comment.strip() == "":
        return {"status": 0, "msg": "comment is missing"}
    elif nugget_id and not nugget_id.isnumeric():
        return {"status": 0, "msg": "Nugget id is missing"}

    else:
        type = int(type) if type else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            access_check = NuggetAccessCheck(db, login_user_id, nugget_id)
            if not access_check:
                return {"status": 0, "msg": "Unauthorized access"}

            check_nuggets = db.query(Nuggets).filter_by(id=nugget_id).first()
            if check_nuggets:
                nugget_comment = NuggetsComments(
                    user_id=login_user_id,
                    parent_id=comment_id,
                    nugget_id=nugget_id,
                    content= detect_and_remove_offensive(comment) if comment else None,
                    created_date=datetime.datetime.utcnow(),
                    modified_date=datetime.datetime.utcnow(),
                )
                db.add(nugget_comment)
                db.commit()

                if nugget_comment:
                    # Add Nugget Comment count in Nugget Table
                    check_nuggets.total_comment_count = check_nuggets.total_comment_count + 1
                    db.commit()
                    
                    status = 1
                    msg = "Success"
                    result_list = {}
                    result_list.update(
                        {
                            "comment_id": nugget_comment.id,
                            "user_id": login_user_id,
                            "editable": True,
                            "name": (
                                nugget_comment.user.display_name
                                if nugget_comment.user.display_name
                                else ""
                            )
                            if nugget_comment.user_id
                            else "",
                            "profile_image": (
                                nugget_comment.user.profile_img
                                if nugget_comment.user.profile_img
                                else defaultimage("profile_img")
                            )
                            if nugget_comment.user_id
                            else "",
                            "comment": nugget_comment.content
                            if nugget_comment.content
                            else "",
                            "commented_date": common_date(nugget_comment.created_date)
                            if nugget_comment.created_date
                            else "",
                            "liked": False,
                            "like_count": 0,
                        }
                    )
                    if type == 1:
                        result_list.update({"reply": []})
                    notification_type = 3
                    Insertnotification(
                        db,
                        check_nuggets.user_id,
                        login_user_id,
                        notification_type,
                        nugget_id,
                    )
                else:
                    msg = "failed to add comment"
            if status == 1:
                return {"status": status, "msg": msg, "comment": result_list}

            else:
                return {"status": status, "msg": msg}


# 31. Edit Nuggets Comments
@router.post("/editnuggetcomment")
async def editnuggetcomment(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    comment_id: str = Form(None),
    comment: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif comment == None or comment.strip() == "":
        return {"status": 0, "msg": "Comment is missing"}
    elif comment_id == None or not comment_id.isnumeric():
        return {"status": 0, "msg": "Comment_id is missing"}
    else:
        access_token = checkToken(db, token)
        comment_id = int(comment_id)
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            check_nugget_comment = (
                db.query(NuggetsComments)
                .filter(
                    NuggetsComments.user_id == login_user_id,
                    NuggetsComments.id == comment_id,
                )
                .first()
            )
            if check_nugget_comment:
                check_nugget_comment.content = detect_and_remove_offensive(comment) if comment else None
                check_nugget_comment.modified_date = datetime.datetime.utcnow()
                db.commit()
                if check_nugget_comment:
                    status = 1
                    msg = "Success"
                else:
                    msg = "failed to add comment"

            return {"status": status, "msg": msg}


# 32. Delete Nuggets Comments
@router.post("/deletenuggetcomment")
async def deletenuggetcomment(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    comment_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif comment_id == None or not comment_id.isnumeric():
        return {"status": 0, "msg": "Comment_id is missing"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            comment_id = int(comment_id)

            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }
            else:
                check_nugget_comment = (
                    db.query(NuggetsComments)
                    .filter_by(user_id=login_user_id, id=comment_id)
                    .first()
                )

                if check_nugget_comment:
                    # Update Nugget Comment in Nugget Table
                    check_nugget_comment.nuggets.total_comment_count = check_nugget_comment.nuggets.total_comment_count - 1 if check_nugget_comment.nuggets.total_comment_count else 0
                    db.commit()
                    
                    # Delete Comment Likes
                    del_comment_like = (
                        db.query(NuggetsCommentsLikes)
                        .filter_by(comment_id=check_nugget_comment.id)
                        .delete()
                    )
                    # Nugget Comments Reply
                    get_nugget_comments = (
                        db.query(NuggetsComments)
                        .filter_by(parent_id=check_nugget_comment.id)
                        .all()
                    )
                    comment_ids = [nugg_cmt.id for nugg_cmt in get_nugget_comments]
                    # Delete Comment Likes
                    del_comment_likes = (
                        db.query(NuggetsCommentsLikes)
                        .filter(NuggetsCommentsLikes.comment_id.in_(comment_ids))
                        .delete()
                    )

                    # Nugget Comments
                    delete_comment = (
                        db.query(NuggetsComments)
                        .filter(NuggetsComments.parent_id == check_nugget_comment.id)
                        .delete()
                    )

                    delete_all_comment = (
                        db.query(NuggetsComments)
                        .filter(NuggetsComments.id == check_nugget_comment.id)
                        .delete()
                    )
                    db.commit()
                    if delete_all_comment:
                        return {"status": 1, "msg": "Success"}
                    else:
                        return {"status": 0, "msg": "Failed to delete comment"}

                else:
                    return {"status": 0, "msg": "Invalid comment id"}


# 33. Like and Unlike Nugget Comment


@router.post("/likeandunlikenuggetcomment")
async def likeandunlikenuggetcomment(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    comment_id: str = Form(None),
    like: str = Form(None, description="1->ilike 2->unlike"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif comment_id == None or not comment_id.isnumeric():
        return {"status": 0, "msg": "Comment id is missing"}
    elif not like:
        return {"status": 0, "msg": "Like flag is missing"}
    elif like and not like.isnumeric() and (like != 1 or like != 2):
        return {"status": 0, "msg": "Like flag is Invalid"}

    else:
        comment_id = int(comment_id) if comment_id else None
        like = int(like) if like else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid comment id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }
            else:
                check_nuggets_comment = (
                    db.query(NuggetsComments).filter_by(id=comment_id).first()
                )

                access_check = NuggetAccessCheck(
                    db, login_user_id, check_nuggets_comment.nugget_id
                )
                if not access_check:
                    return {"status": 0, "msg": "Unauthorized access"}

                if check_nuggets_comment:
                    if like == 1:
                        checkpreviouslike = (
                            db.query(NuggetsCommentsLikes)
                            .filter_by(
                                comment_id=comment_id, user_id=login_user_id, status=1
                            )
                            .first()
                        )
                        if not checkpreviouslike:
                            nuggetcommentlike = NuggetsCommentsLikes(
                                user_id=login_user_id,
                                nugget_id=check_nuggets_comment.nugget_id,
                                comment_id=comment_id,
                                created_date=datetime.datetime.utcnow(),
                            )
                            db.add(nuggetcommentlike)
                            db.commit()
                            status = 1
                            msg = "Success"

                            if check_nuggets_comment.parent_id == None:
                                Insertnotification(
                                    db,
                                    check_nuggets_comment.user_id,
                                    login_user_id,
                                    6,
                                    check_nuggets_comment.nugget_id,
                                )
                            else:
                                Insertnotification(
                                    db,
                                    check_nuggets_comment.user_id,
                                    login_user_id,
                                    7,
                                    check_nuggets_comment.nugget_id,
                                )

                        else:
                            msg = "Your already liked this comment"

                    elif like == 2:
                        checkpreviouslike = (
                            db.query(NuggetsCommentsLikes)
                            .filter_by(
                                comment_id=comment_id, user_id=login_user_id, status=1
                            )
                            .first()
                        )
                        if checkpreviouslike:
                            deleteresult = (
                                db.query(NuggetsCommentsLikes)
                                .filter_by(id=checkpreviouslike.id)
                                .delete()
                            )
                            db.commit()
                            status = 1
                            msg = "Success"
                        else:
                            msg = "you not yet liked this comment"

                    return {"status": status, "msg": msg}


# 34. Nugget and comment Liked user list


@router.post("/nuggetandcommentlikeeduserlist")
async def nuggetandcommentlikeeduserlist(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    id: str = Form(None, description="Nuggets,Comment"),
    type: str = Form(None, description="1-Nuggets,2->Comments"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif type == None:
        return {"status": 0, "msg": "type is missing"}
    elif type and not type.isnumeric() and (type != 1 and type != 2):
        return {"status": 0, "msg": "type is invalid"}
    elif id == None or not id.isnumeric():
        return {
            "status": 0,
            "msg": f"{'Nugget id is missing' if type == 1 else 'Comment id is missing' }",
        }

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            result = []
            type = int(type) if type else None
            if type == 1:
                access_check = NuggetAccessCheck(db, login_user_id, id)
                if not access_check:
                    return {"status": 0, "msg": "Unauthorized access"}
                check_nuggets = (
                    db.query(Nuggets)
                    .filter(Nuggets.id == id, Nuggets.status == 1)
                    .first()
                )
                if check_nuggets:
                    likelist = (
                        db.query(NuggetsLikes)
                        .filter_by(nugget_id=check_nuggets.id)
                        .all()
                    )
                else:
                    return {"status": 0, "msg": "Invalid Nugget id"}
            else:
                check_nuggets_comment = (
                    db.query(NuggetsComments)
                    .filter(NuggetsComments.id == id, NuggetsComments.status == 1)
                    .first()
                )
                if check_nuggets_comment:
                    access_check = NuggetAccessCheck(
                        db, login_user_id, check_nuggets_comment.nugget_id
                    )
                    if not access_check:
                        return {"status": 0, "msg": "Unauthorized access"}
                    likelist = (
                        db.query(NuggetsCommentsLikes)
                        .filter_by(comment_id=check_nuggets_comment.id)
                        .all()
                    )
                else:
                    return {"status": 0, "msg": "Invalid Comment id"}

            if likelist:
                friendlist = get_friend_requests(db, login_user_id, None, None, 1)
                friends = (
                    friendlist["pending"]
                    + friendlist["accepted"]
                    + friendlist["blocked"]
                )

                for likes in likelist:
                    if likes.user_id not in friends and likes.user_id != login_user_id:
                        num = 0
                    else:
                        num = 1

                    result.append(
                        {
                            "user_id": likes.user_id,
                            "name": likes.user.display_name,
                            "profile_image": likes.user.profile_img,
                            "user_ref_id": (
                                likes.user.user_ref_id if likes.user.user_ref_id else ""
                            )
                            if likes.user_id
                            else "",
                            "friend_request_status": num,
                        }
                    )
                return {"status": 1, "msg": "Success", "userlist": result}
            else:
                return {"status": 0, "msg": "No Likes"}


# 35. Edit Nugget
@router.post("/editnugget")
async def editnugget(
    *,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
    share_type: str = Form(None),
    metadata: str = Form(None),
    content: str = Form(None),
    delete_media_id: str = Form(None, description="[1,2,3]"),
    nuggets_media: List[UploadFile] = File(None),
    share_with: str = Form(None, description=' {"friends":[1,2,3],"groups":[1,2,3]} '),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_id == None or not nugget_id.isnumeric():
        return {"status": 0, "msg": "Nugget id is missing"}
    elif share_type == None or not share_type.isnumeric():
        return {"status": 0, "msg": "Sorry! Share type can not be empty."}

    elif (
        int(share_type) == 3 or int(share_type) == 4 or int(share_type) == 5
    ) and not share_with:
        return {"status": 0, "msg": "Sorry! Share with can not be empty."}

    else:
        share_type = int(share_type)
        access_token = checkToken(db, token)
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            check_nuggets = (
                db.query(Nuggets).filter_by(id=nugget_id, user_id=login_user_id).first()
            )
            if check_nuggets:
                content = detect_and_remove_offensive(content) if content else None

                share_with = json.loads(share_with) if share_with else None

                allmediacount = (
                    db.query(NuggetsAttachment)
                    .filter_by(nugget_id=check_nuggets.nuggets_id)
                    .count()
                )
                delete_media_id = json.loads(delete_media_id) if delete_media_id else []
                if delete_media_id:
                    getmediacount = (
                        db.query(NuggetsAttachment)
                        .filter(
                            NuggetsAttachment.nugget_id == check_nuggets.nuggets_id,
                            NuggetsAttachment.id.in_(delete_media_id),
                        )
                        .count()
                    )

                if delete_media_id and (getmediacount != len(delete_media_id)):
                    return {"status": 0, "msg": "Sorry! Invalid image id"}

                elif (
                    (allmediacount == len(delete_media_id))
                    and (content == "")
                    and not nuggets_media
                ):
                    return {
                        "status": 0,
                        "msg": "Sorry! Nuggets content or Media can not be empty....",
                    }

                elif ((share_type == 3) or (share_type == 4) or (share_type == 5)) and (
                    not share_with
                ):
                    return {"status": 0, "msg": "Sorry! Share with can not be empty."}

                elif (share_type == 3) and (
                    (not share_with.get("groups"))
                    or (share_with["groups"] == "")
                    or (not share_with["groups"])
                ):
                    return {
                        "status": 0,
                        "msg": "Sorry! Share with groups list missing.",
                    }

                elif (share_type == 4) and (
                    (not share_with.get("friends"))
                    or (share_with["friends"] == "")
                    or (not share_with["friends"])
                ):
                    return {
                        "status": 0,
                        "msg": "Sorry! Share with friends list missing.",
                    }

                elif (share_type == 5) and (
                    (
                        (not share_with.get("groups"))
                        or (share_with["groups"] == "")
                        or (not share_with["groups"])
                    )
                    and (
                        (not share_with.get("friends"))
                        or (share_with["friends"] == "")
                        or (not share_with["friends"])
                    )
                ):
                    return {
                        "status": 0,
                        "msg": "Sorry! Share with groups or friends list missing.",
                    }

                else:
                    check_content_length = (
                        db.query(User)
                        .filter(
                            User.id == login_user_id,
                            UserStatusMaster.id == User.user_status_id,
                        )
                        .first()
                    )

                    if (
                        check_content_length
                        and content
                        and (check_content_length.user_status_master.max_nugget_char)
                        < len(content.replace("\n", ""))
                    ):
                        return {
                            "status": 0,
                            "msg": f"Content length must be less than {check_content_length.user_status_master.max_nugget_char}",
                        }

                    anyissue = 0

                    if share_type == 3 or share_type == 4 or share_type == 5:
                        if share_with:
                            for key, val in share_with.items():
                                if val:
                                    if key == "groups" and (
                                        share_type == 3 or share_type == 5
                                    ):
                                        query = db.query(FriendGroups).filter(
                                            FriendGroups.id.in_(val),
                                            FriendGroups.status == 1,
                                            FriendGroups.created_by == login_user_id,
                                        )
                                        get_groups = {
                                            group.id: group.id for group in query.all()
                                        }

                                        if len(get_groups) != len(val):
                                            anyissue = 1

                                    elif key == "friends" and (
                                        share_type == 4 or share_type == 5
                                    ):
                                        query = (
                                            db.query(MyFriends)
                                            .with_entities(
                                                MyFriends.id,
                                                case(
                                                    [
                                                        (
                                                            MyFriends.receiver_id
                                                            == login_user_id,
                                                            MyFriends.sender_id,
                                                        )
                                                    ],
                                                    else_=MyFriends.receiver_id,
                                                ).label("receiver_id"),
                                            )
                                            .filter(
                                                MyFriends.status == 1,
                                                MyFriends.request_status == 1,
                                                or_(
                                                    MyFriends.sender_id
                                                    == login_user_id,
                                                    MyFriends.receiver_id
                                                    == login_user_id,
                                                ),
                                            )
                                        )

                                        get_friends = {
                                            friend.id: friend.receiver_id
                                            for friend in query.all()
                                        }

                                        if any(
                                            friend_id not in get_friends.values()
                                            for friend_id in val
                                        ):
                                            anyissue = 1
                    if anyissue == 1:
                        return {
                            "status": 0,
                            "msg": "Sorry! Share with groups or friends list not correct.",
                        }
                    else:
                        update_nuggets = (
                            db.query(Nuggets)
                            .filter_by(id=check_nuggets.id)
                            .update(
                                {
                                    "share_type": share_type,
                                    "modified_date": datetime.datetime.utcnow(),
                                }
                            )
                        )
                        db.commit()
                        if update_nuggets:
                            totalmembers = []

                            if share_type == 6 or share_type == 1:
                                requested_by = None
                                request_status = 1
                                response_type = 1
                                totalmember = get_friend_requests(
                                    db,
                                    login_user_id,
                                    requested_by,
                                    request_status,
                                    response_type,
                                )

                                totalmembers = totalmember["accepted"]

                            update_nugget_master = (
                                db.query(NuggetsMaster)
                                .filter(NuggetsMaster.id == check_nuggets.nuggets_id)
                                .update(
                                    {
                                        "content": content,
                                        "_metadata": metadata,
                                        "modified_date": datetime.datetime.utcnow(),
                                    }
                                )
                            )
                            db.commit()

                            if delete_media_id:
                                del_nugget_attac = (
                                    db.query(NuggetsAttachment)
                                    .filter(NuggetsAttachment.id.in_(delete_media_id))
                                    .delete()
                                )

                            add_hash_tag = StoreHashTags(db, check_nuggets.id)

                            # Nuggets Media
                            if nuggets_media:
                                master_id = check_nuggets.nuggets_id

                                for nugget_media in nuggets_media:
                                    file_name = nugget_media.filename
                                    file_temp = nugget_media.content_type

                                    # File Upload
                                    file_ext = os.path.splitext(nugget_media.filename)[
                                        1
                                    ]

                                    uploaded_file_path = await file_upload(
                                        nugget_media, file_ext, compress=1
                                    )
                                    file_stat = os.stat(uploaded_file_path)
                                    file_size = file_stat.st_size

                                    type = "image"
                                    path = "/uploads/nuggets"

                                    if "video" in file_temp:
                                        type = "video"
                                        
                                    elif "audio" in file_temp:
                                        type = "audio"

                                    if (
                                        file_size > 1000000
                                        and type == "image"
                                        and file_ext != ".gif"
                                    ):
                                        s3_file_path = f"nuggets/Image_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}"

                                        result = upload_to_s3(
                                            uploaded_file_path, s3_file_path
                                        )
                                        if result["status"] == 1:
                                            add_nugget_attachment = NuggetsAttachment(
                                                user_id=login_user_id,
                                                nugget_id=check_nuggets.nuggets_id,
                                                media_type=type,
                                                media_file_type=file_ext,
                                                file_size=file_size,
                                                path=result["url"],
                                                created_date=datetime.datetime.utcnow(),
                                                status=1,
                                            )
                                            db.add(add_nugget_attachment)
                                            db.commit()
                                            db.refresh(add_nugget_attachment)

                                        else:
                                            return result

                                    else:
                                        s3_file_path = f"nuggets/video_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                                        if type == "video":
                                            video = VideoFileClip(
                                                uploaded_file_path
                                            )  # Video Split ( 5 Minutes)
                                            total_duration = video.duration

                                            if total_duration < 300:
                                                result = upload_to_s3(
                                                    uploaded_file_path, s3_file_path
                                                )
                                                if result["status"] == 1:
                                                    add_nugget_attachment = NuggetsAttachment(
                                                        user_id=login_user_id,
                                                        nugget_id=check_nuggets.nuggets_id,
                                                        media_type=type,
                                                        media_file_type=file_ext,
                                                        file_size=file_size,
                                                        path=result["url"],
                                                        created_date=datetime.datetime.utcnow(),
                                                        status=1,
                                                    )
                                                    db.add(add_nugget_attachment)
                                                    db.commit()
                                                    db.refresh(add_nugget_attachment)

                                                else:
                                                    return result

                                            else:
                                                # background_tasks.add_task(
                                                #     process_data,
                                                #     db,
                                                #     uploaded_file_path,
                                                #     login_user_id,
                                                #     master_id,
                                                #     share_type,
                                                #     share_with,
                                                # )
                                                return {
                                                    "status": 0,
                                                    "msg": "Duration must be below five minutes"
                                                }

                                        elif type == "audio":
                                            base_dir = "rawcaster_uploads"
                                            try:
                                                os.makedirs(base_dir, mode=0o777, exist_ok=True)
                                            except OSError as e:
                                                sys.exit("Can't create {dir}: {err}".format(dir=base_dir, err=e))

                                            output_dir = base_dir + "/"

                                            characters = string.ascii_letters + string.digits
                                            # Generate the random string
                                            random_string = "".join(random.choice(characters) for i in range(18))

                                            filename = f"uploadfile_{random_string}.mp3"

                                            sub_process_path = f"{output_dir}{filename}"
                                            
                                            ffmpeg_command = ['ffmpeg', '-i', uploaded_file_path, sub_process_path]
                                            try:
                                                subprocess.run(ffmpeg_command, check=True)
                                                print('Audio conversion successful!')
                                            except subprocess.CalledProcessError as e:
                                                print('Error:', e)
                                            
                                            s3_file_path = f"nuggets/audio_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp3"
                                            os.remove(uploaded_file_path)
                                            
                                            result = upload_to_s3(
                                                sub_process_path, s3_file_path
                                            )
                                            if result["status"] == 1:
                                                add_nugget_attachment = NuggetsAttachment(
                                                    user_id=login_user_id,
                                                    nugget_id=check_nuggets.nuggets_id,
                                                    media_type=type,
                                                    media_file_type=file_ext,
                                                    file_size=file_size,
                                                    path=result["url"],
                                                    created_date=datetime.datetime.utcnow(),
                                                    status=1,
                                                )
                                                db.add(add_nugget_attachment)
                                                db.commit()
                                                db.refresh(add_nugget_attachment)
                                            else:
                                                return result

                                        else:
                                            result = upload_to_s3(
                                                uploaded_file_path, s3_file_path
                                            )

                                            if result["status"] == 1:
                                                add_nugget_attachment = NuggetsAttachment(
                                                    user_id=login_user_id,
                                                    nugget_id=check_nuggets.nuggets_id,
                                                    media_type=type,
                                                    media_file_type=file_ext,
                                                    file_size=file_size,
                                                    path=result["url"],
                                                    created_date=datetime.datetime.utcnow(),
                                                    status=1,
                                                )
                                                db.add(add_nugget_attachment)
                                                db.commit()
                                                db.refresh(add_nugget_attachment)
                                            else:
                                                return result

                            # Delete Share with
                            del_share_nuggets = (
                                db.query(NuggetsShareWith)
                                .filter(NuggetsShareWith.nuggets_id == check_nuggets.id)
                                .delete()
                            )
                            db.commit()

                            # If share type is Group or Individual
                            if share_type == 3 or share_type == 4 or share_type == 5:
                                if share_type == 3:
                                    share_with["friends"] = ""

                                if share_type == 4:
                                    share_with["groups"] = ""

                                if share_with:
                                    for key, val in share_with.items():
                                        if val:
                                            for shareid in val:
                                                nuggets_share_with = NuggetsShareWith(
                                                    nuggets_id=check_nuggets.id,
                                                    type=2 if key == "friends" else 1,
                                                    share_with=shareid,
                                                )
                                                db.add(nuggets_share_with)
                                                db.commit()

                                                if nuggets_share_with:
                                                    if key == "friends":
                                                        totalmembers.append(shareid)

                                                    else:
                                                        getgroupmember = (
                                                            db.query(FriendGroupMembers)
                                                            .filter_by(group_id=shareid)
                                                            .all()
                                                        )

                                                        if getgroupmember:
                                                            for (
                                                                member
                                                            ) in getgroupmember:
                                                                if (
                                                                    member.user_id
                                                                    in totalmembers
                                                                ):
                                                                    totalmembers.append(
                                                                        member.user_id
                                                                    )

                            if totalmembers:
                                for users in totalmembers:
                                    notify_type = 2
                                    insert_noty = Insertnotification(
                                        db,
                                        users,
                                        login_user_id,
                                        notify_type,
                                        notify_type,
                                    )

                                    get_user = (
                                        db.query(User)
                                        .filter_by(id=login_user_id)
                                        .first()
                                    )
                                    user_name = ""
                                    if get_user:
                                        user_name = get_user.display_name

                                    message_detail = {
                                        "message": "Edited the Nugget",
                                        "data": {
                                            "refer_id": nugget_id,
                                            "type": "edit_nugget",
                                        },
                                        "type": "nuggets",
                                    }

                                    push_notify = pushNotify(
                                        db, totalmembers, message_detail, login_user_id
                                    )

                                    subject = "Rawcaster -  Notification"
                                    body = ""
                                    sms_message = f"{user_name} Updated a Nugget"

                                    email_detail = {
                                        "subject": subject,
                                        "mail_message": body,
                                        "sms_message": sms_message,
                                        "type": "nuggets",
                                    }

                                    addNotificationSmsEmail(
                                        db, totalmembers, email_detail, login_user_id
                                    )

                            # Nugget detail object for response
                            nugget_detail = get_nugget_detail(
                                db, nugget_id, login_user_id
                            )
                            return {
                                "status": 1,
                                "msg": "Nugget updated",
                                "nugget_detail": nugget_detail,
                            }
                        else:
                            return {"status": 0, "msg": "Failed to update Nugget"}

            else:
                return {"status": 0, "msg": "Invalid nugget id"}


# 36. Share Nugget
@router.post("/sharenugget")
async def sharenugget(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
    share_type: str = Form(
        None,
        description="1-public,2-only me,3-groups,4-individual,5-both group & individual ,6-all my friends",
    ),
    share_with: str = Form(None, description='{"friends":[1,2,3],"groups":[1,2,3]}'),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_id == None or not nugget_id.isnumeric():
        return {"status": 0, "msg": "nugget_id is missing"}
    elif share_type == None or not share_type.isnumeric():
        return {"status": 0, "msg": "Invalid Share type"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            share_with = json.loads(share_with) if share_with else None

            share_type = int(share_type) if share_type else None

            if (
                share_type == 3 or share_type == 4 or share_type == 5
            ) and not share_with:
                return {"status": 0, "msg": "Sorry! Share with can not be empty."}

            elif share_type == 3 and not share_with["groups"]:
                return {"status": 0, "msg": "Sorry! Share with groups list missing."}

            elif share_type == 4 and not share_with["friends"]:
                return {"status": 0, "msg": "Sorry! Share with friends list missing."}

            elif share_type == 5 and (
                (
                    not hasattr(share_with, "groups")
                    or share_with.groups == ""
                    or len(share_with.groups) == 0
                )
                and (
                    not hasattr(share_with, "friends")
                    or share_with.friends == ""
                    or len(share_with.friends) == 0
                )
            ):
                return {
                    "status": 0,
                    "msg": "Sorry! Share with groups or friends list missing.",
                }

            else:
                get_token_details = (
                    db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
                )
                login_user_id = get_token_details.user_id

                if IsAccountVerified(db, login_user_id) == False:
                    return {
                        "status": 0,
                        "msg": "You need to complete your account validation before you can do this",
                    }

                access_check = NuggetAccessCheck(db, login_user_id, nugget_id)
                if not access_check:
                    return {"status": 0, "msg": "Unauthorized access"}

                anyissue = 0
                if share_type == 3 or share_type == 4 or share_type == 5:
                    if share_with:
                        for key, val in share_with.items():
                            if val:
                                if key == "groups" and (
                                    share_type == 3 or share_type == 5
                                ):
                                    query = db.query(FriendGroups).filter(
                                        FriendGroups.id.in_(val),
                                        FriendGroups.status == 1,
                                        FriendGroups.created_by == login_user_id,
                                    )
                                    get_groups = {row.id: row.id for row in query.all()}

                                    if len(get_groups) != len(val):
                                        anyissue = 1

                                elif key == "friends" and (
                                    share_type == 4 or share_type == 5
                                ):
                                    query = (
                                        db.query(
                                            MyFriends.id,
                                            case(
                                                [
                                                    (
                                                        MyFriends.receiver_id
                                                        == login_user_id,
                                                        MyFriends.sender_id,
                                                    )
                                                ],
                                                else_=MyFriends.receiver_id,
                                            ).label("receiver_id"),
                                        )
                                        .filter(
                                            MyFriends.status == 1,
                                            MyFriends.request_status == 1,
                                        )
                                        .filter(
                                            or_(
                                                MyFriends.sender_id == login_user_id,
                                                MyFriends.receiver_id == login_user_id,
                                            )
                                        )
                                    )
                                    result_list = query.all()
                                    get_friends = []

                                    for elem in result_list:
                                        # Assuming `id` and `receiver_id` are attributes of the `MyFriends` class
                                        get_friends.append(elem.receiver_id)

                                    my_friend_count = [
                                        x for x in val if x not in get_friends
                                    ]

                                    if len(my_friend_count) > 0:
                                        anyissue = 1

                if anyissue == 1:
                    return {
                        "status": 0,
                        "msg": "Sorry! Share with groups or friends list not correct.",
                    }
                else:
                    status = 0
                    nugget_detail = []
                    msg = "Invalid nugget id"

                    nugget_id = nugget_id if nugget_id else 0
                    check_nugget = (
                        db.query(Nuggets)
                        .filter_by(id=nugget_id, share_type=1, status=1)
                        .first()
                    )
                    if check_nugget:
                        share_nugget = Nuggets(
                            nuggets_id=check_nugget.nuggets_id,
                            user_id=login_user_id,
                            type=2,
                            share_type=share_type,
                            created_date=datetime.datetime.utcnow(),
                        )
                        db.add(share_nugget)
                        db.commit()
                        totalmembers = []
                        if share_nugget:
                            if share_type == 6 or share_type == 1:
                                requested_by = None
                                request_status = 1
                                response_type = 1
                                search_key = None
                                totalmember = get_friend_requests(
                                    db,
                                    login_user_id,
                                    requested_by,
                                    request_status,
                                    response_type,
                                )

                                totalmembers.append(totalmember["accepted"])

                            # If share type is Group or Individual
                            if share_type == 3 or share_type == 4 or share_type == 5:
                                if share_type == 3:
                                    share_with["friends"] = ""

                                if share_type == 4 and "groups" in share_with:
                                    share_with["groups"] = ""

                                if share_with:
                                    for key, val in share_with.items():
                                        if val:
                                            for shareid in val:
                                                type = 2 if key == "friends" else 1
                                                nuggets_share_with = NuggetsShareWith(
                                                    nuggets_id=share_nugget.id,
                                                    type=type,
                                                    share_with=shareid,
                                                )
                                                db.add(nuggets_share_with)
                                                db.commit()

                                                if nuggets_share_with:
                                                    if key == "friends":
                                                        totalmembers.append(shareid)

                                                    else:
                                                        getgroupmember = (
                                                            db.query(FriendGroupMembers)
                                                            .filter_by(group_id=shareid)
                                                            .all()
                                                        )

                                                        if getgroupmember:
                                                            for (
                                                                member
                                                            ) in getgroupmember:
                                                                if (
                                                                    member.user_id
                                                                    in totalmembers
                                                                ):
                                                                    totalmembers.append(
                                                                        member.user_id
                                                                    )

                            nugget_detail = get_nugget_detail(
                                db, share_nugget.id, login_user_id
                            )

                            status = 1
                            msg = "Success"

                            if totalmembers:
                                for users in totalmembers:
                                    ref_id = 8
                                    insert_notification = Insertnotification(
                                        db,
                                        check_nugget.user_id,
                                        login_user_id,
                                        ref_id,
                                        check_nugget.id,
                                    )
                        else:
                            status = 0
                            msg = "Failed"
                    else:
                        msg = "Invalid nugget id"

                return {"status": status, "msg": msg, "nugget_detail": nugget_detail}


# 37. Get individual nugget detail
@router.post("/getnuggetdetail")
async def getnuggetdetail(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_id == None or not nugget_id.isnumeric():
        return {"status": 0, "msg": "Nugget_id is missing"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            check_nuggets = NuggetAccessCheck(db, login_user_id, nugget_id)
            
            if check_nuggets == True:
                nugget_detail = get_nugget_detail(db, nugget_id, login_user_id)
                return {"status": 1, "msg": "success", "nugget_detail": nugget_detail}

            else:
                return {"status": 0, "msg": "Unauthorized access"}


# 38. Get Event type
@router.post("/geteventtype")
async def geteventtype(db: Session = Depends(deps.get_db), token: str = Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_eventtypes = db.query(EventTypes).filter_by(status=1).all()
            result_list = []
            for type in get_eventtypes:
                result_list.append(
                    {"id": type.id, "type": type.title if type.title else ""}
                )

            return {"status": 1, "msg": "Success", "event_types": result_list}


# 39. Get Event layout
@router.post("/geteventlayout")
async def geteventlayout(db: Session = Depends(deps.get_db), token: str = Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_eventlayouts = db.query(EventLayouts).filter_by(status=1).all()

            result_list = []

            for type in get_eventlayouts:
                result_list.append(
                    {"id": type.id, "name": type.title if type.title else ""}
                )

            return {"status": 1, "msg": "Success", "event_layouts": result_list}


# 40. Add Event
@router.post("/addevent")
async def addevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_title: str = Form(None),
    event_type: str = Form(None, description="1-Event,2-Talkshow,3-Live"),
    event_start_date: Any = Form(None),
    event_start_time: Any = Form(None),
    event_message: str = Form(None),
    event_participants: str = Form(None),
    event_duration: Any = Form(None),
    event_layout: str = Form(None),
    event_host_audio: str = Form(None),
    event_host_video: str = Form(None),
    event_guest_audio: str = Form(None),
    event_guest_video: str = Form(None),
    event_melody: UploadFile = File(None),
    event_invite_mails: str = Form(None),
    event_invite_groups: str = Form(None),
    event_invite_friends: str = Form(None),
    event_melody_id: str = Form(None),
    waiting_room: str = Form(None),
    join_before_host: str = Form(None),
    sound_notify: str = Form(None),
    user_screenshare: str = Form(None),
    event_banner: UploadFile = File(None),
):
    event_invite_friends = (
        json.loads(event_invite_friends) if event_invite_friends else None
    )
    
    event_invite_custom = json.loads(event_invite_mails) if event_invite_mails else None
    event_invite_groups = (
        json.loads(event_invite_groups) if event_invite_groups else None
    )

    if event_title == None or event_title.strip() == "":
        return {"status": 0, "msg": "Event title cant be blank."}
    elif event_type == None and not event_type.isnumeric():
        return {"status": 0, "msg": "Event type cant be blank."}
    elif event_start_date == None:
        return {"status": 0, "msg": "Event start date cant be blank."}
    elif event_start_time == None:
        return {"status": 0, "msg": "Event start time cant be blank."}
    elif event_participants == None or not event_participants.isnumeric():
        return {"status": 0, "msg": "Event participants cant be blank."}

    elif not event_duration:
        return {"status": 0, "msg": "Event duration cant be blank."}

    elif event_layout == None:
        return {"status": 0, "msg": "Event layout cant be blank."}
    elif event_host_audio == None:
        return {"status": 0, "msg": "Event host audio settings cant be blank."}
    elif event_host_video == None:
        return {"status": 0, "msg": "Event host video settings cant be blank."}
    elif event_guest_audio == None:
        return {"status": 0, "msg": "Event guest audio settings cant be blank."}
    elif event_guest_video == None:
        return {"status": 0, "msg": "Event guest video settings cant be blank."}
    elif not event_melody and not event_melody_id:
        return {"status": 0, "msg": "Event melody cant be blank."}
    elif event_start_date and is_date(event_start_date) == False:
        return {"status": 0, "msg": "Invalid Date"}

    elif event_start_time and isTimeFormat(event_start_time) == False:
        return {"status": 0, "msg": "Invalid Time format"}

    elif event_duration and isTimeFormat(event_duration) == False:
        return {"status": 0, "msg": "Invalid Time format"}

    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    else:
        event_duration = datetime.datetime.strptime(event_duration, "%H:%M").time()
        min_duration = datetime.datetime.strptime("10:00", "%H:%M").time()
        if event_duration > min_duration:
            return {"status": 0, "msg": "Event duration invalid"}

        event_participants = int(event_participants)
        if event_participants < 2:
            return {
                "status": 0,
                "msg": "Event participants count should be greater than 1",
            }

        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id if get_token_details else None

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            user = db.query(User).filter_by(id=login_user_id).first()

            if user:
                userstatus = (
                    db.query(UserStatusMaster).filter_by(id=user.user_status_id).first()
                )

                if userstatus:
                    max_parti = (
                        userstatus.max_event_participants_count
                    )  # Max Participants Count

            if event_participants > max_parti:
                return {
                    "status": 0,
                    "msg": "Event participants count should be less than 100.",
                }

            if event_participants < 2:
                return {
                    "status": 0,
                    "msg": "Event participants count should be greater than 1.",
                }

            else:
                event_type = int(event_type)
                setting = (
                    db.query(UserSettings).filter_by(user_id=login_user_id).first()
                )

                flag = (
                    "event_banner"
                    if event_type == 1
                    else "talkshow"
                    if event_type == 2
                    else "live"
                    if event_type == 3
                    else None
                )

                cover_img = defaultimage(flag)
                if setting:
                    cover_img = (
                        setting.meeting_header_image
                        if setting.meeting_header_image
                        else defaultimage(flag)
                    )

                server_id = None

                server = db.query(KurentoServers).filter_by(status=1).limit(1).first()

                if server:
                    server_id = server.server_id

                hostname = user.display_name
                
                
                reference_id = (
                    f"RC{random.randint(1,499)}{datetime.datetime.utcnow().timestamp()}"
                )
                
                # Create Meeting (Chime API Call)
                chime_meeting_id=None
                try:
                    user_id=login_user_id
                    shareScreen=True if user_screenshare == 1 else False
                    joinApprovalRequired=False if event_type == 1 else True 
                    data={'joinApprovalRequired': joinApprovalRequired,'allowOtherToShareScreen':shareScreen,'userId':user_id}
                    headers = {'Content-Type': 'application/json'}
                    url='https://devchimeapi.rawcaster.com/createmeeting'
                    
                    chime_meeting_response = requests.post(url, data = json.dumps(data),headers=headers)
                    
                    if chime_meeting_response.status_code == 200:
                        response=json.loads(chime_meeting_response.text)
                        chime_meeting_id=response['result']['Meeting']['MeetingId'] if response['status'] == 200 else None
                    
                except Exception as e:
                    print(e)
                    return {"status":0,"msg":"Something went wrong"}
                
                # Parse the strings into datetime objects
                date_obj = datetime.datetime.strptime(event_start_date, "%Y-%m-%d")
                time_obj = datetime.datetime.strptime(event_start_time, "%H:%M").time()

                # Combine the datetime objects
                datetime_str = datetime.datetime.combine(date_obj, time_obj)

                new_event = Events(
                    title= detect_and_remove_offensive(event_title),
                    ref_id=reference_id,
                    chime_meeting_id=chime_meeting_id,
                    server_id=server_id if server_id != None else None,
                    event_type_id=event_type,
                    description=detect_and_remove_offensive(event_message) if event_message else None,
                    event_layout_id=event_layout,
                    no_of_participants=event_participants,
                    duration=event_duration,
                    start_date_time=datetime_str,
                    created_at=datetime.datetime.utcnow(),
                    created_by=login_user_id,
                    cover_img=cover_img,
                    waiting_room=waiting_room,
                    join_before_host=join_before_host,
                    sound_notify=sound_notify,
                    user_screenshare=user_screenshare,
                )
                db.add(new_event)
                db.commit()
                db.refresh(new_event)

                if new_event:
                    totalfriends = []
                    if event_type == 1:
                        requested_by = None
                        request_status = 1
                        response_type = 1
                        search_key = None

                        totalfriend = get_friend_requests(
                            db,
                            login_user_id,
                            requested_by,
                            request_status,
                            response_type,
                        )
                        totalfriends = totalfriend["accepted"]

                    #  Default Audio Video Settings
                    new_default_av = EventDefaultAv(
                        event_id=new_event.id,
                        default_host_audio=event_host_audio,
                        default_host_video=event_host_video,
                        default_guest_audio=event_guest_audio,
                        default_guest_video=event_guest_video,
                    )

                    db.add(new_default_av)
                    db.commit()

                    # Banner Image
                    if event_banner:
                        file_ext = os.path.splitext(event_banner.filename)[1]

                        uploaded_file_path = await file_upload(
                            event_banner, file_ext, compress=None
                        )

                        file_stat = os.stat(uploaded_file_path)
                        file_size = file_stat.st_size
                        file_temp = event_banner.content_type

                        # file_name=event_banner.filename
                        # read_file=await event_banner.read()
                        # file_size=len(read_file)

                        type = "image"
                        if "video" in file_temp:
                            type = "video"

                        if file_size > 1024 and type == "image" and file_ext != ".gif":
                            s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path = uploaded_file_path
                            result = upload_to_s3(uploaded_file_path, s3_path)
                            if result["status"] == 1:
                                new_event.cover_img = result["url"]
                                db.commit()

                            else:
                                return result
                        else:
                            s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path = uploaded_file_path
                            result = upload_to_s3(uploaded_file_path, s3_path)
                            # Upload to S3
                            if result["status"] == 1:
                                new_event.cover_img = result["url"]
                                db.commit()
                            else:
                                return result

                    # Event Melody
                    if event_melody:
                        # file_name=event_melody.filename
                        file_temp = event_melody.content_type
                        # read_file=await event_melody.read()
                        # file_size=len(read_file)
                        file_ext = os.path.splitext(event_melody.filename)[1]

                        uploaded_file_path = await file_upload(
                            event_melody, file_ext, compress=None
                        )
                        file_stat = os.stat(uploaded_file_path)
                        file_size = file_stat.st_size

                        media_type = 1
                        type=''
                        if (
                            file_ext == ".png"
                            or file_ext == ".jpeg"
                            or file_ext == "jpg"
                        ):
                            type = "image"
                        elif file_ext == ".mp3":
                            type = "audio"
                            media_type = 3
                            
                        elif file_ext == "pptx" or file_ext == "ppt":
                            type = "ppt"
                            media_type = 4
                            
                        elif "video" in file_temp:
                            type = "video"
                            media_type = 2

                        if (
                            file_size > 1000000
                            and type == "image"
                            and file_ext != ".gif"
                        ):
                            s3_file_path = f"eventsmelody/eventsmelody{random.randint(11111,99999)}{new_event.id}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            upload_file_path = uploaded_file_path
                            result = upload_to_s3(upload_file_path, s3_file_path)

                            if result and result["status"] == 1:
                                new_melody = EventMelody(
                                    event_id=new_event.id,
                                    path=result["url"],
                                    type=media_type,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(new_melody)
                                db.commit()
                                db.refresh(new_melody)

                                if new_melody:
                                    new_event.event_melody_id = new_melody.id
                                    db.commit()
                            else:
                                return {"status": 0, "msg": "Not able to upload"}

                        else:
                            s3_file_path = f"eventsmelody/eventsmelody_{random.randint(11111,99999)}{new_event.id}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            upload_file_path = uploaded_file_path

                            if type == "video" and file_ext != ".mp4":
                                s3_file_path = f"eventsmelody/eventsmelody_{random.randint(11111,99999)}{new_event.id}{int(datetime.datetime.utcnow().timestamp())}.mp4"
                                upload_file_path = video_file_upload(
                                    event_melody, compress=1, file_ext=file_ext
                                )

                            result = upload_to_s3(upload_file_path, s3_file_path)

                            if result and result["status"] == 1:
                                add_new_melody = EventMelody(
                                    event_id=new_event.id,
                                    path=result["url"],
                                    type=media_type,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(add_new_melody)
                                db.commit()
                                
                                if add_new_melody:
                                    new_event.event_melody_id = add_new_melody.id
                                    db.commit()

                            else:
                                return {"status": 0, "msg": "Not able to upload"}

                    else:
                        temp = int(event_melody_id) if event_melody_id else 1
                        update_event_melody_id = (
                            db.query(Events)
                            .filter_by(id=new_event.id)
                            .update({"event_melody_id": temp if temp > 0 else 1})
                        )
                        db.commit()

                    if event_invite_friends:
                        for value in event_invite_friends:
                            invite_friends = EventInvitations(
                                type=1,
                                event_id=new_event.id,
                                user_id=value,
                                invite_sent=0,
                                created_at=datetime.datetime.utcnow(),
                                created_by=login_user_id,
                            )
                            db.add(invite_friends)
                            db.commit()

                            if value not in totalfriends:
                                totalfriends.append(value)

                    if event_invite_groups:
                        for value in event_invite_groups:
                            invite_groups = EventInvitations(
                                type=2,
                                event_id=new_event.id,
                                group_id=value,
                                invite_sent=0,
                                created_at=datetime.datetime.utcnow(),
                                created_by=login_user_id,
                            )
                            db.add(invite_groups)
                            db.commit()
                            getgroupmember = (
                                db.query(FriendGroupMembers)
                                .filter_by(group_id=value)
                                .all()
                            )

                            if getgroupmember:
                                for member in getgroupmember:
                                    if member.user_id not in totalfriends:
                                        totalfriends.append(member.user_id)

                    invite_url = inviteBaseurl()
                    link = f"{invite_url}join/event/{reference_id}"

                    subject = "Rawcaster - Event Invitation"
                    body = ""
                    sms_message = ""

                    if new_event:
                        sms_message, body = eventPostNotifcationEmail(db, new_event.id)

                    if event_invite_custom:
                        # event_invite_custom=event_invite_custom.split(',')
                        for value in event_invite_custom:
                            # check if e-mail address is well-formed
                            if check_mail(value):
                                invite_custom = EventInvitations(
                                    type=3,
                                    event_id=new_event.id,
                                    invite_mail=value,
                                    invite_sent=0,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(invite_custom)
                                db.commit()

                                if invite_custom:
                                    to = value
                                    try:
                                        send_mail = await send_email(
                                            db, to, subject, body
                                        )
                                    except:
                                        pass

                    event = get_event_detail(db, new_event.id, login_user_id)  # Pending

                    if totalfriends:
                        for users in totalfriends:
                            notification_type = 9

                            add_notitication = Insertnotification(
                                db,
                                users,
                                login_user_id,
                                notification_type,
                                new_event.id,
                            )

                            message_detail = {
                                "message": "Posted new event",
                                "data": {"refer_id": new_event.id, "type": "add_event"},
                                "type": "events",
                            }

                            pushNotify(db, totalfriends, message_detail, login_user_id)

                            email_detail = {
                                "subject": subject,
                                "mail_message": body,
                                "sms_message": sms_message,
                                "type": "events",
                            }
                            addNotificationSmsEmail(
                                db, totalfriends, email_detail, login_user_id
                            )

                    return {
                        "status": 1,
                        "msg": "Event saved successfully !",
                        "ref_id": reference_id,
                        "event_detail": event,
                    }

                else:
                    return {"status": 0, "msg": "Event cant be created."}


# 41. List Event       
@router.post("/listevents")
async def listevents(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_id: str = Form(None),
    event_type: str = Form(
        0, description="1->My Events, 2->Invited Events, 3->Public Events"
    ),
    type_filter: str = Form(None, description="1 - Event,2 - Talkshow,3 - Live"),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    elif user_id and not user_id.isnumeric():
        return {"status": 0, "msg": "Invalid User id"}
    elif event_type and not event_type.isnumeric():
        return {"status": 0, "msg": "Invalid Event type"}
    elif type_filter and not type_filter.isnumeric():
        return {"status": 0, "msg": "Invalid Type Filter"}

    else:
        type_filter = int(type_filter) if type_filter else None
        event_type = int(event_type) if event_type else None
        user_id = int(user_id) if user_id else None

        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens.user_id).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_user_setting = (
                db.query(UserSettings)
                .filter(UserSettings.user_id == login_user_id)
                .first()
            )
            if get_user_setting:
                user_public_event_display_setting = (
                    get_user_setting.public_event_display
                    if get_user_setting.public_event_display
                    else None
                )

            current_page_no = int(page_number)
            event_type = event_type if event_type else 0
            requested_by = None
            request_status = 1
            response_type = 1
        
            my_friend = get_friend_requests(
                db, login_user_id, requested_by, request_status, response_type
            )

            my_friends = my_friend["accepted"]
            my_followings = getFollowings(db, login_user_id)

            event_list = db.query(Events).filter_by(status=1, event_status=1)

            groups = (
                db.query(FriendGroupMembers.group_id)
                .filter_by(user_id=login_user_id)
                .group_by(FriendGroupMembers.group_id)
                .all()
            )
            
            group_ids = [group.group_id for group in groups]
            
            if event_type == 1:  # My events (Created by User)
                event_list = event_list.filter_by(created_by=login_user_id)
                
            elif event_type == 2:  # Invited Events
                event_list = event_list.join(EventInvitations,EventInvitations.event_id == Events.id).filter(
                    or_(
                        and_(
                            EventInvitations.type == 1,
                            EventInvitations.user_id == login_user_id,
                        ),
                        EventInvitations.group_id.in_(group_ids),
                    )
                )
            elif event_type == 3:  # Open Events
                event_list = event_list.filter(
                    and_(Events.event_type_id == 1, Events.created_by != login_user_id)
                )

            elif event_type == 5:
                event_list = event_list.filter(Events.created_by == login_user_id)

            elif user_id:
                if user_id == login_user_id:
                    event_list = event_list.join(
                        EventInvitations,
                        Events.id == EventInvitations.event_id,
                        isouter=True,
                    ).filter(
                        or_(
                            and_(
                                EventInvitations.type == 1,
                                EventInvitations.user_id == login_user_id,
                            ),
                            EventInvitations.group_id.in_(group_ids),
                            Events.created_by == login_user_id,
                            Events.event_type_id == 1,
                        )
                    )
                else:
                    event_list = event_list.filter(
                        Events.created_by == user_id, Events.event_type_id == 1
                    )

            else:
                my_followers = []  # Selected Connections id's
                followUser = (
                    db.query(FollowUser.following_userid).filter_by(follower_userid=login_user_id).all()
                )
                if followUser:
                    my_followers = [
                        group_list.following_userid for group_list in followUser
                    ]
                
                if user_public_event_display_setting == 0:  # Rawcaster
                    type = None

                    rawid = GetRawcasterUserID(db, type)
                    event_list = event_list.filter(Events.created_by == rawid)

                elif user_public_event_display_setting == 1:  # Public
                    event_list = event_list.join(
                        EventInvitations,
                        Events.id == EventInvitations.event_id,
                        isouter=True,
                    ).filter(
                        or_(
                            and_(
                                EventInvitations.type == 1,
                                EventInvitations.user_id == login_user_id,
                            ),
                            EventInvitations.group_id.in_(groups),
                            Events.created_by == login_user_id,
                            and_(
                                Events.event_type_id == 3,
                                Events.created_by.in_(my_followings),
                            ),
                            Events.event_type_id == 1,
                        )
                    )
                elif user_public_event_display_setting == 2:  # All Connections
                    event_list = event_list.join(
                        EventInvitations,
                        EventInvitations.event_id == Events.id,
                        isouter=True,
                    ).filter(
                        or_(
                            and_(
                                EventInvitations.type == 1,
                                EventInvitations.user_id == login_user_id,
                            ),
                            Events.created_by == login_user_id,
                            and_(
                                Events.event_type_id.in_([1, 2, 3]),
                                Events.created_by.in_(my_friends),
                            ),
                        )
                    )

                elif user_public_event_display_setting == 3:  # Specific Connections
                    specific_friends = []  # Selected Connections id's
                    online_group_list = (
                        db.query(UserProfileDisplayGroup.groupid)
                        .filter_by(
                            user_id=login_user_id, profile_id="public_event_display"
                        )
                        .all()
                    )

                    if online_group_list:
                        specific_friends = [
                            group_list.groupid for group_list in online_group_list
                        ]

                    event_list = event_list.join(
                        EventInvitations,
                        EventInvitations.event_id == Events.id,
                        isouter=True,
                    ).filter(
                        or_(
                            and_(
                                EventInvitations.type == 1,
                                EventInvitations.user_id == login_user_id,
                            ),
                            Events.created_by == login_user_id,
                            Events.created_by.in_(specific_friends),
                            and_(
                                Events.event_type_id.in_([1, 2, 3]),
                                Events.created_by.in_(specific_friends),
                            ),
                        )
                    )

                elif user_public_event_display_setting == 4:  # All Groups
                    event_list = (
                        event_list.join(
                            EventInvitations,
                            EventInvitations.event_id == Events.id,
                            isouter=True,
                        )
                        .join(
                            FriendGroupMembers,
                            Events.created_by == FriendGroupMembers.user_id,
                            isouter=True,
                        )
                        .join(
                            FriendGroups, FriendGroupMembers.group_id == FriendGroups.id
                        )
                        .filter(
                            or_(
                                and_(Events.created_by == login_user_id),
                                and_(FriendGroups.created_by == login_user_id),
                            )
                        )
                    )

                    event_list = event_list.filter(
                        or_(
                            and_(
                                Events.event_type_id == 2,
                                EventInvitations.type == 1,
                                EventInvitations.user_id == login_user_id,
                            ),
                            and_(
                                Events.event_type_id == 2,
                                EventInvitations.type == 2,
                                EventInvitations.group_id.in_(groups),
                            ),
                            and_(
                                Events.event_type_id == 3,
                                Events.created_by.in_(my_followers),
                            ),
                            and_(Events.event_type_id.in_([1])),
                            Events.created_by == login_user_id,
                        )
                    )

                elif user_public_event_display_setting == 5:  #  Specific Groups
                    my_friends = []  # Selected Connections id's
                    online_group_list = (
                        db.query(UserProfileDisplayGroup.groupid)
                        .filter_by(
                            user_id=login_user_id, profile_id="public_event_display"
                        )
                        .all()
                    )

                    if online_group_list:
                        my_friends = [
                            group_list.groupid for group_list in online_group_list
                        ]

                    event_list = (
                        event_list.join(
                            EventInvitations,
                            EventInvitations.event_id == Events.id,
                            isouter=True,
                        )
                        .join(
                            FriendGroupMembers,
                            Events.created_by == FriendGroupMembers.user_id,
                            isouter=True,
                        )
                        .join(
                            FriendGroups,
                            FriendGroupMembers.group_id == FriendGroups.id,
                            isouter=True,
                        )
                    )

                    event_list = event_list.filter(
                        or_(
                            Events.created_by == login_user_id,
                            and_(
                                FriendGroups.created_by == login_user_id,
                                FriendGroups.id.in_(my_friends),
                            ),
                        )
                    )

                    event_list = event_list.filter(
                        or_(
                            and_(
                                Events.event_type_id == 2,
                                EventInvitations.type == 1,
                                EventInvitations.user_id == login_user_id,
                            ),
                            and_(
                                Events.event_type_id == 2,
                                EventInvitations.type == 2,
                                EventInvitations.group_id.in_(groups),
                            ),
                            and_(
                                Events.event_type_id == 3,
                                Events.created_by.in_(my_followers),
                            ),
                            and_(Events.event_type_id.in_([1])),
                            Events.created_by == login_user_id,
                        )
                    )

                elif user_public_event_display_setting == 6:  # My influencers
                    event_list = event_list.outerjoin(
                        EventInvitations, EventInvitations.event_id == Events.id
                    ).filter(
                        or_(
                            Events.created_by.in_(my_followers),
                            Events.created_by == login_user_id,
                        )
                    ).filter(
                        (
                            (Events.event_type_id == 2)
                            & (EventInvitations.type == 1)
                            & (EventInvitations.user_id == login_user_id)
                        )
                        | (
                            (Events.event_type_id == 2)
                            & (EventInvitations.type == 2)
                            & EventInvitations.group_id.in_(groups)
                        )
                        | (Events.event_type_id.in_([1, 3]))
                        | (Events.created_by == login_user_id)
                    )

                else:  # Mine only
                    event_list = event_list.filter(Events.created_by == login_user_id)

            if event_type == 4:
                event_list = event_list.filter(
                    Events.start_date_time < datetime.datetime.utcnow()
                )

            elif event_type == 5:
                event_list = event_list

            else:
                event_list = event_list.filter(
                    text(
                        "DATE_ADD(events.start_date_time, INTERVAL SUBSTRING(events.duration, 1, CHAR_LENGTH(events.duration) - 3) HOUR_MINUTE) > :current_datetime"
                    )
                ).params(current_datetime=datetime.datetime.utcnow())

            event_list = event_list.filter(Events.status == 1)

            if type_filter:
                event_list = event_list.filter(Events.type.in_([type_filter]))

            event_list = event_list.group_by(Events.id)

            get_row_count = event_list.count()
            
            if get_row_count < 1:
                return {
                    "status": 1,
                    "msg": "No Result found",
                    "events_count": 0,
                    "total_pages": 1,
                    "current_page_no": 1,
                    "events_list": [],
                }
            else:
                if event_type == 4 or event_type == 5:
                    event_list = event_list.order_by(Events.start_date_time.desc())
                else:
                    event_list = event_list.order_by(Events.start_date_time.asc())

                default_page_size = 20

                limit, offset, total_pages = get_pagination(
                    get_row_count, current_page_no, default_page_size
                )
                event_list = event_list.limit(limit).offset(offset)

                event_list = event_list.all()

                result_list = []
                if event_list:
                    for event in event_list:
                        
                        waiting_room = event.user.user_settings[0].waiting_room if event.user.user_settings and event.user.user_settings[0].waiting_room != None else 1
                        join_before_host = event.user.user_settings[0].join_before_host if event.user.user_settings and event.user.user_settings[0].join_before_host != None else 1
                        sound_notify = event.user.user_settings[0].participant_join_sound if event.user.user_settings and event.user.user_settings[0].participant_join_sound != None else 1
                        user_screenshare = event.user.user_settings[0].screen_share_status if event.user.user_settings and event.user.user_settings[0].screen_share_status != None else 1

                        default_melody = (
                            db.query(EventMelody)
                            .filter_by(id=event.event_melody_id)
                            .first()
                        )

                        default_host_audio = 0
                        default_host_video = 0
                        default_guest_audio = 0
                        default_guest_video = 0
                        # event_default_av = (
                        #     db.query(EventDefaultAv.default_host_audio,EventDefaultAv.default_host_video,EventDefaultAv.default_guest_audio,
                        #              EventDefaultAv.default_guest_video)\
                        #         .filter_by(event_id=event.id).all()
                        # )
                        event_default_av=event.event_default_av
                        
                        for def_av in event_default_av:
                            default_host_audio=def_av.default_host_audio
                            default_host_video=def_av.default_host_video
                            default_guest_audio=def_av.default_guest_audio
                            default_guest_video=def_av.default_guest_video
                            
                            # default_host_audio.append(def_av.default_host_audio)
                            # default_host_video.append(def_av.default_host_video)
                            # default_guest_audio.append(def_av.default_guest_audio)
                            # default_guest_video.append(def_av.default_guest_video)

                        banner_image = (
                            (
                                event.user.user_settings and event.user.user_settings[0].meeting_header_image
                                if not event.cover_img
                                else event.cover_img
                            )
                            if event.type == 1
                            else (
                                event.user.user_settings and event.user.user_settings[0].talkshow_event_banner
                                if not event.cover_img
                                else event.cover_img
                            )
                            if event.type == 2
                            else (
                                event.user.user_settings and event.user.user_settings[0].live_event_banner
                                if not event.cover_img
                                else event.cover_img
                            )
                            if event.type == 3
                            else event.cover_img
                        )
                        
                        result_list.append(
                            {
                                "event_id": event.id,
                                "event_name": event.title,
                                "reference_id": event.ref_id,
                                "chime_meeting_id":event.chime_meeting_id if event.chime_meeting_id else "",
                                "type": event.type,
                                "event_type_id": event.event_type_id,
                                "event_layout_id": event.event_layout_id,
                                "message": event.description
                                if event.description
                                else "",
                                "start_date_time": (
                                    common_date(event.start_date_time)
                                    if event.start_date_time
                                    else ""
                                )
                                if event.created_at
                                else "",
                                "start_date": (
                                    common_date(event.start_date_time)
                                    if event.start_date_time
                                    else ""
                                )
                                if event.created_at
                                else "",
                                "start_time": common_date(event.start_date_time)
                                if event.start_date_time
                                else ""
                                if event.created_at
                                else "",
                                "duration": event.duration,
                                "no_of_participants": event.no_of_participants
                                if event.no_of_participants
                                else None,
                                # "banner_image":event.cover_img if event.cover_img else "",
                                "banner_image": banner_image,  # Event Images displayed event type wise
                                "is_host": 1 if event.created_by == login_user_id else 0,
                                "created_at": common_date(event.created_at)
                                if event.created_at
                                else "",
                                "original_user_name": event.user.display_name,
                                "original_user_id": event.user.id,
                                "original_user_image": event.user.profile_img,
                                "event_melody_id": event.event_melody_id,
                                "waiting_room": event.waiting_room
                                if event.waiting_room == 1 or event.waiting_room == 0
                                else waiting_room,
                                "join_before_host": event.join_before_host
                                if event.join_before_host == 1
                                or event.join_before_host == 0
                                else join_before_host,
                                "sound_notify": event.sound_notify
                                if event.sound_notify == 0 or event.sound_notify == 0
                                else sound_notify,
                                "user_screenshare": event.user_screenshare
                                if event.user_screenshare == 1
                                or event.user_screenshare == 0
                                else user_screenshare,
                                "melodies": {
                                    "path": default_melody.path,
                                    "type": default_melody.type,
                                    "is_default": default_melody.event_id,
                                } if default_melody else {'path':'','type':'','is_default':""},
                                
                                "default_host_audio": default_host_audio
                                if default_host_audio
                                else 0,
                                "default_host_video": default_host_video
                                if default_host_video
                                else 0,
                                "default_guest_audio": default_guest_audio
                                if default_guest_audio
                                else 0,
                                "default_guest_video": default_guest_video
                                if default_guest_video
                                else 0
                            }
                        )
                    
                return {
                    "status": 1,
                    ",msg": "Success",
                    "events_count": get_row_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "events_list": result_list,
                }


#  42. Delete Events
@router.post("/deleteevent")
async def deleteevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif event_id == None or not event_id.isnumeric():
        return {"status": 0, "msg": "Event id is missing"}
    elif not event_id.isnumeric():
        return {"status": 0, "msg": "Invalid Event id"}

    else:
        event_id = int(event_id) if event_id else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if not IsAccountVerified(db, login_user_id):
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }
            check_event_creater = (
                db.query(Events)
                .filter_by(id=event_id, created_by=login_user_id, status=1)
                .first()
            )
            if check_event_creater:
                delete_event = (
                    db.query(Events)
                    .filter_by(id=check_event_creater.id)
                    .update({Events.event_status: 0, Events.status: 0})
                )
                db.query(Notification).filter_by(ref_id=event_id).delete()
                db.commit()

                if delete_event:
                    return {"status": 1, "msg": "Event Deleted"}
                else:
                    return {"status": 0, "msg": "Unable to delete"}
            else:
                return {"status": 0, "mgs": "Invalid event id"}


# 43. View Event
@router.post("/viewevent")
async def viewevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif event_id == None or not event_id.isnumeric():
        return {"status": 0, "msg": "Event id is missing"}

    else:
        event_id = int(event_id) if event_id else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            access_check = EventAccessCheck(db, login_user_id, event_id)
            if not access_check:
                return {"status": 0, "msg": "Unauthorized Event access"}
            event_details = db.query(Events).filter_by(id=event_id, status=1).first()

            if event_details:
                event = get_event_detail(db, event_details.id, login_user_id)
                return {"status": 1, "msg": "success", "event_detail": event}
            else:
                return {"status": 0, "msg": "Event ended"}


# 44. Edit Event
@router.post("/editevent")
async def editevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_id: str = Form(None),
    event_title: str = Form(None),
    event_type: str = Form(None),
    event_start_date: Any = Form(None),
    event_start_time: Any = Form(None),
    event_message: str = Form(None),
    event_participants: str = Form(None, description="max no of participants"),
    event_duration: Any = Form(None, description="Duration of Event hh:mm"),
    event_layout: str = Form(None),
    event_melody_id: str = Form(None, description="Event melody id (56 api table)"),
    event_melody: UploadFile = File(None),
    event_banner: UploadFile = File(None),
    event_host_audio: str = Form(None, description="0->No ,1->Yes"),
    event_host_video: str = Form(None, description="0->No ,1->Yes"),
    event_guest_audio: str = Form(None, description="0->No ,1->Yes"),
    event_guest_video: str = Form(None, description="0->No ,1->Yes"),
    event_invite_mails: str = Form(
        None, description="example abc@mail.com , def@mail.com"
    ),
    event_invite_groups: str = Form(None, description="example [1,2,3]"),
    event_invite_friends: str = Form(None, description="example[ 1,2,3]"),
    delete_invite_friends: str = Form(None, description="example [1,2,3]"),
    delete_invite_groups: str = Form(None, description="example [1,2,3]"),
    delete_invite_mails: str = Form(
        None, description="example abc@gmail.com,xyz@mail.com"
    ),
    waiting_room: str = Form(None, description="0-No,1-Yes"),
    join_before_host: str = Form(None, description="0-No,1-Yes"),
    sound_notify: str = Form(None, description="0-No,1-Yes"),
    user_screenshare: str = Form(None, description="0-No,1-Yes"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not event_id or not event_id.isnumeric():
        return {"status": 0, "msg": "Event id is missing"}
    if not event_title or event_title.strip() == "":
        return {"status": 0, "msg": "Event title cant be blank."}
    elif not event_type or not event_type.isnumeric():
        return {"status": 0, "msg": "Event type cant be blank."}
    elif not event_start_date:
        return {"status": 0, "msg": "Event start date cant be blank."}
    elif not event_start_time:
        return {"status": 0, "msg": "Event start time cant be blank."}
    elif not event_participants:
        return {"status": 0, "msg": "Event participants cant be blank."}

    elif event_melody_id and not event_melody_id.isnumeric():
        return {"status": 0, "msg": "Invalid event melody id"}

    elif not event_duration:
        return {"status": 0, "msg": "Event duration cant be blank."}

    elif not event_layout:
        return {"status": 0, "msg": "Event layout cant be blank."}
    elif not event_host_audio:
        return {"status": 0, "msg": "Event host audio settings cant be blank."}
    elif not event_host_video:
        return {"status": 0, "msg": "Event host video settings cant be blank."}
    elif not event_guest_audio:
        return {"status": 0, "msg": "Event guest audio settings cant be blank."}
    elif not event_guest_video:
        return {"status": 0, "msg": "Event guest video settings cant be blank."}
    elif event_start_date and is_date(event_start_date) == False:
        return {"status": 0, "msg": "Invalid Date"}
    elif event_start_time and isTimeFormat(event_start_time) == False:
        return {"status": 0, "msg": "Invalid Time format"}

    elif event_duration and isTimeFormat(event_duration) == False:
        return {"status": 0, "msg": "Invalid Time format"}
    else:
        minimum_duration_time = time.strptime("00:10", "%H:%M")
        if minimum_duration_time > time.strptime(event_duration, "%H:%M"):
            return {"status": 0, "msg": "Event duration invalid"}

        event_type = int(event_type) if event_type else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            event_participants = int(event_participants)
            if event_participants < 2:
                return {
                    "status": 0,
                    "msg": "Event participants count should be greater than 1",
                }

            if not IsAccountVerified(db, login_user_id):
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }
          
            # delete_invite_custom=delete_invite_mails.split(',') if delete_invite_mails else []
            delete_invite_custom=json.loads(delete_invite_mails) if delete_invite_mails else None
            delete_invite_groups = (
                json.loads(delete_invite_groups) if delete_invite_groups else None
            )
            delete_invite_friends = (
                json.loads(delete_invite_friends) if delete_invite_friends else None
            )

            event_exist = (
                db.query(Events)
                .filter_by(id=event_id, created_by=login_user_id)
                .first()
            )

            if not event_exist:
                return {"status": 0, "msg": "Invalid Event ID."}

            else:
                # Delete Invites
                if delete_invite_friends:
                    delete_friends = (
                        db.query(EventInvitations)
                        .filter(
                            EventInvitations.event_id == event_id,
                            EventInvitations.user_id.in_(delete_invite_friends),
                        )
                        .delete()
                    )
                    db.commit()

                if delete_invite_groups:
                    event_invite_group = (
                        db.query(EventInvitations)
                        .filter(
                            and_(
                                EventInvitations.event_id == event_id,
                                EventInvitations.group_id.in_(delete_invite_groups),
                            )
                        )
                        .delete()
                    )
                    db.commit()

                if delete_invite_custom: 
                                       
                    delete_invite_mails = (
                        db.query(EventInvitations)
                        .filter(
                            and_(
                                EventInvitations.event_id == event_id,
                                EventInvitations.invite_mail.in_(delete_invite_custom),
                            )
                        )
                        .delete()
                    )
                    db.commit()

                if event_type == 3:
                    delete_query = (
                        db.query(EventInvitations)
                        .filter(EventInvitations.event_id == event_id)
                        .delete()
                    )
                    db.commit()

                user = db.query(User).filter(User.id == login_user_id).first()
                hostname = user.display_name if user else ""
                is_event_changed = 0

                edit_event = db.query(Events).filter(Events.id == event_id).first()

                old_start_datetime = edit_event.start_date_time if edit_event else None

                edit_event.title = detect_and_remove_offensive(event_title) if event_title else None
                edit_event.description = detect_and_remove_offensive(event_message) if event_message else None
                edit_event.event_type_id = event_type
                edit_event.event_layout_id = event_layout
                edit_event.no_of_participants = event_participants
                edit_event.duration = event_duration
                edit_event.start_date_time = (
                    str(event_start_date) + " " + str(event_start_time)
                )
                edit_event.waiting_room = (
                    waiting_room if waiting_room != None else edit_event.waiting_room
                )
                edit_event.join_before_host = (
                    join_before_host
                    if join_before_host != None
                    else edit_event.join_before_host
                )
                edit_event.sound_notify = (
                    sound_notify if sound_notify != None else edit_event.sound_notify
                )
                edit_event.user_screenshare = (
                    user_screenshare
                    if user_screenshare != None
                    else edit_event.user_screenshare
                )
                db.commit()
                if edit_event:
                    totalfriends = []
                    if event_type == 1:
                        totalfriends = get_friend_requests(
                            db,
                            login_user_id,
                            requested_by=None,
                            request_status=1,
                            response_type=1,
                        )
                        totalfriends = totalfriends["accepted"]

                    if old_start_datetime != edit_event.start_date_time:
                        is_event_changed = 1

                    #  Default Audio Video Settings
                    edit_default_av = (
                        db.query(EventDefaultAv)
                        .filter(EventDefaultAv.event_id == event_id)
                        .first()
                    )
                    if edit_default_av:
                        edit_default_av.default_host_audio = event_host_audio
                        edit_default_av.default_host_video = event_host_video
                        edit_default_av.default_guest_audio = event_guest_audio
                        edit_default_av.default_guest_video = event_guest_video
                        db.commit()

                    # Banner Image
                    if event_banner:
                        file_ext = os.path.splitext(event_banner.filename)[1]

                        uploaded_file_path = await file_upload(
                            event_banner, file_ext, compress=None
                        )

                        file_stat = os.stat(uploaded_file_path)
                        file_size = file_stat.st_size
                        file_temp = event_banner.content_type

                        # file_name=event_banner.filename
                        # read_file=await event_banner.read()
                        # file_size=len(read_file)

                        type = "image"
                        if "video" in file_temp:
                            type = "video"

                        if file_size > 1024 and type == "image" and file_ext != ".gif":
                            s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path = uploaded_file_path
                            result = upload_to_s3(uploaded_file_path, s3_path)
                            if result["status"] == 1:
                                edit_event.cover_img = result["url"]
                                db.commit()

                            else:
                                return result
                        else:
                            s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path = uploaded_file_path
                            result = upload_to_s3(uploaded_file_path, s3_path)
                            # Upload to S3
                            if result["status"] == 1:
                                edit_event.cover_img = result["url"]
                                db.commit()
                            else:
                                return result
                    else:
                        temp = int(event_melody_id) if event_melody_id else None
                        edit_event.event_melody_id = temp if temp and temp > 0 else 1
                        db.commit()

                    # Event Melody
                    if event_melody:
                        # file_name=event_melody.filename
                        file_temp = event_melody.content_type
                        # read_file=await event_melody.read()
                        # file_size=len(read_file)
                        file_ext = os.path.splitext(event_melody.filename)[1]

                        uploaded_file_path = await file_upload(
                            event_melody, file_ext, compress=None
                        )
                        file_stat = os.stat(uploaded_file_path)
                        file_size = file_stat.st_size

                        media_type = 1
                        if (
                            file_ext == ".png"
                            or file_ext == ".jpeg"
                            or file_ext == "jpg"
                        ):
                            type = "image"
                            
                        elif file_ext == ".mp3":
                            type = "audio"
                            media_type=3
                            
                        elif file_ext == "pptx" or file_ext == "ppt":
                            type = "ppt"
                            media_type=4
                            
                        elif "video" in file_temp:
                            type = "video"
                            media_type = 2

                        if (
                            file_size > 1000000
                            and type == "image"
                            and file_ext != ".gif"
                        ):
                            s3_file_path = f"eventsmelody/eventsmelody{random.randint(11111,99999)}{edit_event.id}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            upload_file_path = uploaded_file_path
                            result = upload_to_s3(upload_file_path, s3_file_path)

                            if result and result["status"] == 1:
                                new_melody = EventMelody(
                                    event_id=edit_event.id,
                                    path=result["url"],
                                    type=media_type,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(new_melody)
                                db.commit()
                                db.refresh(new_melody)

                                if new_melody:
                                    edit_event.event_melody_id = new_melody.id
                                    db.commit()
                            else:
                                return {"status": 0, "msg": "Not able to upload"}

                        else:
                            s3_file_path = f"eventsmelody/eventsmelody_{random.randint(11111,99999)}{edit_event.id}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            
                            if type == "video" and file_ext != ".mp4":
                                s3_file_path = f"eventsmelody/eventsmelody_{random.randint(11111,99999)}{edit_event.id}{int(datetime.datetime.utcnow().timestamp())}.mp4"
                                # upload_file_path = video_file_upload(
                                #     event_melody, compress=1, file_ext=file_ext
                                # )

                            result = upload_to_s3(uploaded_file_path, s3_file_path)

                            if result and result["status"] == 1:
                                add_new_melody = EventMelody(
                                    event_id=edit_event.id,
                                    path=result["url"],
                                    type=media_type,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(add_new_melody)
                                db.commit()
                                
                                if add_new_melody:
                                    edit_event.event_melody_id = add_new_melody.id
                                    db.commit()

                            else:
                                return {"status": 0, "msg": "Not able to upload"}

                    else:
                        temp = int(event_melody_id) if event_melody_id else 1
                        edit_event.event_melody_id = temp if temp > 0 else 1
                        db.commit()

                    if is_event_changed == 1:
                        update_invitation = (
                            db.query(EventInvitations)
                            .filter(EventInvitations.event_id == event_id)
                            .update({"is_changed": 1})
                        )
                        db.commit()

                    if event_invite_friends:
                        event_invite_friends = (
                            ast.literal_eval(event_invite_friends)
                            if event_invite_friends
                            else None
                        )

                        for invite_frnds in event_invite_friends:
                            check_invited_user=db.query(EventInvitations).filter(EventInvitations.event_id == event_id,EventInvitations.user_id == invite_frnds).first()
                            if not check_invited_user:
                                invite_friends = EventInvitations(
                                    type=1,
                                    event_id=event_id,
                                    user_id=invite_frnds,
                                    invite_sent=0,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(invite_friends)
                                db.commit()
                                db.refresh(invite_friends)

                                if invite_frnds not in totalfriends:
                                    totalfriends.append(invite_frnds)

                    if event_invite_groups:
                        event_invite_groups = (
                            ast.literal_eval(event_invite_groups)
                            if event_invite_groups
                            else None
                        )

                        for invite_frnds in event_invite_groups:
                            check_invited_group=db.query(EventInvitations).filter(EventInvitations.event_id == event_id,EventInvitations.group_id == invite_frnds).first()
                            if not check_invited_group:
                                invite_friends = EventInvitations(
                                    type=2,
                                    event_id=event_id,
                                    group_id=invite_frnds,
                                    invite_sent=0,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(invite_friends)
                                db.commit()
                                db.refresh(invite_friends)

                                getgroupmember = (
                                    db.query(FriendGroupMembers)
                                    .filter(FriendGroupMembers.group_id == invite_frnds)
                                    .all()
                                )
                                if getgroupmember:
                                    for member in getgroupmember:
                                        if member.user_id in totalfriends:
                                            totalfriends.append(member.user_id)

                    invite_url = inviteBaseurl()
                    link = f"{invite_url}join/event/{edit_event.ref_id}"
                    subject = "Rawcaster - Event Invitation"
                    content = ""
                    content += "Hi,greetings from Rawcaster.com.<br /><br/>"
                    content += f"You have been invited by {hostname} to an event titled {event_title}.<br/><br/>"
                    content += f"Use the following link to join the Rawcaster event.<br/> {link} <br/><br/>"
                    content += f"Regards,<br />Administration Team<br /><a href='https://rawcaster.com/'>Rawcaster.com</a> LLC"

                    body = event_mail_template(content)
                    if event_invite_mails:
                        invite_mails=json.loads(event_invite_mails)
                        # invite_mails=event_invite_mails.split(",")
                        
                        # event_invite_mails = (
                        #     ast.literal_eval(event_invite_mails)
                        #     if event_invite_mails
                        #     else None
                        # )
                        for invite_mail in invite_mails:
                            check_invite_mail=db.query(EventInvitations).filter(EventInvitations.event_id == event_id,EventInvitations.invite_mail == invite_mail).first()
                            if not check_invite_mail:
                                invite_friends = EventInvitations(
                                    type=3,
                                    event_id=event_id,
                                    invite_mail=invite_mail,
                                    invite_sent=0,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(invite_friends)
                                db.commit()
                                db.refresh(invite_friends)

                                if invite_friends:
                                    to = invite_mail
                                    try:
                                        send_mail = await send_email(db, to, subject, body)
                                    except:
                                        pass

                    event = get_event_detail(db, event_id, login_user_id)
                    if totalfriends:
                        for users in totalfriends:
                            insert_notification = Insertnotification(
                                db, users, login_user_id, 10, edit_event.id
                            )

                            message_detail = {
                                "message": "Updated an event",
                                "data": {
                                    "refer_id": edit_event.id,
                                    "type": "edit_event",
                                },
                                "type": "events",
                            }

                            push_notification = pushNotify(
                                db, totalfriends, message_detail, login_user_id
                            )

                            sms_message = f"Hi,greetings from Rawcaster.com.You have been invited by {hostname} to an event titled {event_title}.Use the following link to join the Rawcaster event.{link} "

                            email_detail = {
                                "subject": subject,
                                "mail_message": body,
                                "sms_message": sms_message,
                                "type": "events",
                            }
                            add_notification = addNotificationSmsEmail(
                                db, totalfriends, email_detail, login_user_id
                            )

                    return {
                        "status": 1,
                        "msg": "Event Updated successfully !",
                        "ref_id": edit_event.ref_id,
                        "event_detail": event,
                    }

                else:
                    return {"status": 0, "msg": "Event cant be updated."}


# 45. List Chat Messages
@router.post("/listchatmessages")
async def listchatmessages(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_id: str = Form(None),
    page_number: str = Form(default=1),
    search_key: str = Form(None),
    last_msg_id: str = Form(None),
    msg_from: str = Form(default=2),
    sender_delete: str = Form(None),
    receiver_delete: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif user_id == None or not user_id.isnumeric():
        return {"status": 0, "msg": "User id is missing"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            user_id = int(user_id) if user_id else None
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if not IsAccountVerified(db, login_user_id):
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            # criteria=db.query(FriendsChat).filter(FriendsChat.status==1,FriendsChat.is_deleted_for_both==0,
            #                                          FriendsChat.type==1,FriendsChat.sender_id==login_user_id if FriendsChat.sender_delete==None and FriendsChat.receiver_delete !=None else user_id
            #                                          ,FriendsChat.receiver_id==user_id if FriendsChat.sender_delete==None and FriendsChat.receiver_delete !=None else login_user_id
            #                                          )
            criteria = db.query(FriendsChat).filter(
                FriendsChat.status == 1,
                FriendsChat.is_deleted_for_both == 0,
                FriendsChat.type == 1,
                or_(
                    FriendsChat.sender_id == login_user_id,
                    FriendsChat.receiver_id == user_id,
                    FriendsChat.sender_delete != None,
                    FriendsChat.sender_id == user_id,
                    FriendsChat.receiver_id == login_user_id,
                    FriendsChat.receiver_delete == None,
                ),
            )
            if msg_from == 1:
                criteria.filter(FriendsChat.msg_from == msg_from)

            if search_key and search_key.strip() != "":
                criteria = criteria.filter(FriendsChat.message.ilike(search_key + "%"))

            if last_msg_id:
                criteria = criteria.filter(FriendsChat.id < last_msg_id)

            get_row_count = criteria.count()

            if get_row_count < 1:
                return {"status": 2, "msg": "No Result found"}
            else:
                default_page_size = 10
                limit, offset, total_pages = get_pagination(
                    get_row_count, page_number, default_page_size
                )
                get_result = (
                    criteria.order_by(FriendsChat.id.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )

                result_list = []
                for res in get_result:
                    result_list.append(
                        {
                            "id": res.id,
                            "uniqueId": res.msg_code if res.msg_code else None,
                            "senderId": res.sender_id if res.sender_id else None,
                            "senderName": (
                                res.user1.display_name if res.user1.display_name else ""
                            )
                            if res.sender_id
                            else None,
                            "userImage": (
                                res.user1.profile_img if res.user1.profile_img else ""
                            )
                            if res.sender_id
                            else None,
                            "receiverId": res.receiver_id if res.receiver_id else None,
                            "sentType": res.sent_type if res.sent_type else None,
                            "parentMsgId": res.parent_msg_id
                            if res.parent_msg_id
                            else None,
                            "forwarded_from": res.forwarded_from
                            if res.forwarded_from
                            else None,
                            "type": res.type if res.type else None,
                            "message": res.message if res.message else None,
                            "path": res.path if res.path else None,
                            "sent_datetime": common_date(res.sent_datetime)
                            if res.sent_datetime
                            else None,
                            "is_read": res.is_read if res.is_read else None,
                            "is_edited": res.is_edited if res.is_edited else None,
                            "read_datetime": common_date(res.read_datetime)
                            if res.read_datetime
                            else None,
                            "is_deleted_for_both": res.is_deleted_for_both
                            if res.is_deleted_for_both
                            else None,
                            "sender_delete": res.sender_delete
                            if res.sender_delete
                            else None,
                            "receiver_delete": res.receiver_delete
                            if receiver_delete
                            else None,
                            "sender_deleted_datetime": common_date(
                                res.sender_deleted_datetime
                            )
                            if res.sender_deleted_datetime
                            else None,
                            "receiver_deleted_datetime": common_date(
                                res.receiver_deleted_datetime
                            )
                            if res.receiver_deleted_datetime
                            else None,
                            "call_status": res.call_status if res.call_status else None,
                            "msg_from": res.msg_from if res.msg_from else None,
                        }
                    )

                return {
                    "status": 1,
                    "msg": "Success",
                    "total_pages": total_pages,
                    "current_page_no": page_number,
                    "chat_list": result_list,
                }


# 46. Upload Chat Attachment

@router.post("/uploadchatattachment")
async def uploadchatattachment(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    refid: str = Form(None),
    chatattachment: UploadFile = File(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif refid and refid.strip() == "":
        return {"status": 0, "msg": "Reference id is missing"}
    elif chatattachment == None:
        return {"status": 0, "msg": "File is missing"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            readed_file = await chatattachment.read()
            file_size = len(readed_file)
            file_ext = os.path.splitext(chatattachment.filename)[1]

            if file_size > 100000000:
                return {"status": 0, "msg": "Max 100MB allowed"}

            else:
                uploaded_file_path = await read_file_upload(
                    readed_file, file_ext, compress=None
                )
                s3_file_path = f"chat/attachment_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                result = upload_to_s3(uploaded_file_path, s3_file_path)
                if result["status"] == 1:
                    return {
                        "status": 1,
                        "msg": "Success",
                        "filepath": result["url"],
                        "refid": refid,
                        "file_type": file_ext.replace(".", ""),
                    }
                else:
                    return {"status": 0, "msg": "Not able to upload"}


# 47. List Notifications
@router.post("/listnotifications")
async def listnotifications(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    page_number: str = Form(default=1),
    notification_type: str = Form(
        None,
        description="1-Nugget,2-Event,3-Friend Request,4-Group,5-Fans,6-Poll Results",
    ),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}

    elif notification_type and not notification_type.isnumeric():
        return {"status": 0, "msg": "Invalid Notification Type"}

    else:
        notification_type = int(notification_type) if notification_type else None

        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens.user_id).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            current_page_no = int(page_number)

            get_notification = db.query(Notification).filter(
                Notification.status == 1, Notification.user_id == login_user_id
            )

            get_nuggets = db.query(Nuggets).filter(Nuggets.user_id == login_user_id)

            if notification_type == 6:  # Poll Notification
                get_nuggets = get_nuggets.filter(
                    Nuggets.nuggets_id == NuggetsMaster.id,
                    NuggetsMaster.poll_duration != None,
                    NuggetsMaster.poll_duration != "",
                )

                nuggets_id = []
                for polls in get_nuggets:
                    days, hours, minutes = (
                        map(int, (polls.nuggets_master.poll_duration).split(":"))
                        if polls.nuggets_master.poll_duration
                        else [0, 0, 0]
                    )
                    duration_seconds = (
                        (days * 24 * 3600) + (hours * 3600) + (minutes * 60)
                    )

                    poll_expire_date = polls.nuggets_master.created_date + timedelta(
                        seconds=duration_seconds
                    )

                    if datetime.datetime.utcnow() >= poll_expire_date:
                        nuggets_id.append(polls.nuggets_master.id)

                get_nuggets = get_nuggets.filter(
                    NuggetsMaster.id.in_(nuggets_id)
                ).order_by(Nuggets.id.desc())

            if notification_type == 1:  # Nugget
                filters = [1,3, 4, 5, 6, 7, 8, 18]

                get_notification = get_notification.filter(
                    Notification.notification_type.in_(filters)
                )

            if notification_type == 2:  # Event
                filters = [9, 10, 13]
                my_frnd_id = []
                # Get My Friends
                my_friends = (
                    db.query(MyFriends)
                    .filter(
                        or_(
                            MyFriends.sender_id == login_user_id,
                            MyFriends.receiver_id == login_user_id,
                        ),
                        MyFriends.request_status == 1,
                    )
                    .all()
                )
                for frnd in my_friends:
                    my_frnd_id.append(frnd.sender_id)
                    my_frnd_id.append(frnd.receiver_id)

                my_frnd_ids = set(my_frnd_id)
                if login_user_id in my_frnd_ids:
                    my_frnd_ids.remove(login_user_id)

                get_notification = get_notification.filter(
                    Notification.notification_type.in_(filters),
                    Notification.notification_origin_id.in_(my_frnd_ids),
                )

            if notification_type == 3:  # Friend Request Accept/Reject
                filters = [11, 12]
                get_notification = get_notification.filter(
                    Notification.notification_type.in_(filters)
                )

            if notification_type == 4:  # Group
                get_notification = get_notification.filter(
                    Notification.notification_type == 17
                )

            if notification_type == 5:  # Fans
                get_notification = get_notification.filter(
                    Notification.notification_type == 15
                )

            get_row_count = (
                get_nuggets.count()
                if notification_type == 6
                else get_notification.count()
            )

            if get_row_count < 1:
                return {"status": 0, "msg": "No Result found"}
            else:
                default_page_size = 25
                limit, offset, total_pages = get_pagination(
                    get_row_count, current_page_no, default_page_size
                )
                if notification_type == 6:
                    get_notification = (
                        get_nuggets.order_by(NuggetsMaster.id.desc())
                        .limit(limit)
                        .offset(offset)
                        .all()
                    )
                else:
                    get_notification = (
                        get_notification.order_by(Notification.id.desc())
                        .limit(limit)
                        .offset(offset)
                        .all()
                    )

                result_list = []

                for res in get_notification:
                    friend_request_id = None
                    friend_request_status = None

                    if notification_type != 6:
                        if res.notification_type == 11:
                            myfriends = (
                                db.query(MyFriends)
                                .filter_by(
                                    sender_id=res.notification_origin_id,
                                    receiver_id=res.user_id,
                                    request_status=0,
                                    status=1,
                                )
                                .first()
                            )
                            if myfriends:
                                friend_request_id = myfriends.id
                                friend_request_status = myfriends.request_status

                    if notification_type == 1:
                        get_nugget = (
                            db.query(Nuggets).filter(Nuggets.id == res.ref_id).first()
                        )
                        result_list.append(
                            {
                                "notification_id": res.id,
                                "user_id": res.notification_origin_id,
                                "userName": res.user2.display_name
                                if res.notification_origin_id
                                else "",
                                "userImage": res.user2.profile_img
                                if res.notification_origin_id
                                else "",
                                "type": res.notification_type,
                                "nugget_id": get_nugget.id if get_nugget else "",
                                "content": get_nugget.nuggets_master.content
                                if get_nugget
                                else "",
                                "created_datetime": common_date(res.created_datetime)
                                if res.created_datetime
                                else None,
                                "is_read": res.is_read if res.is_read else 0,
                            }
                        )
                    elif notification_type == 2:  # Event
                        get_event = (
                            db.query(Events).filter(Events.id == res.ref_id).first()
                        )

                        result_list.append(
                            {
                                "notification_id": res.id,
                                "event_id": get_event.id if get_event else None,
                                "user_id": res.notification_origin_id,
                                "userName": res.user2.display_name
                                if res.notification_origin_id
                                else "",
                                "userImage": res.user2.profile_img
                                if res.notification_origin_id
                                else "",
                                "type": res.notification_type,
                                "content": get_event.title if get_event else "",
                                "event_start_time": common_date(
                                    get_event.start_date_time
                                )
                                if get_event
                                else "",
                                "created_datetime": common_date(res.created_datetime)
                                if res.created_datetime
                                else None,
                                "is_read": res.is_read if res.is_read else 0,
                            }
                        )

                    elif notification_type == 3:  # Friend request
                        result_list.append(
                            {
                                "notification_id": res.id,
                                "user_id": res.notification_origin_id,
                                "userName": res.user2.display_name
                                if res.notification_origin_id
                                else "",
                                "userImage": res.user2.profile_img
                                if res.notification_origin_id
                                else "",
                                "type": res.notification_type,
                                "friend_request_id": friend_request_id,
                                "friend_request_status": friend_request_status,
                                "ref_id": res.ref_id if res.ref_id else None,
                                "is_read": res.is_read if res.is_read else 0,
                                "read_datetime": common_date(res.read_datetime)
                                if res.read_datetime
                                else None,
                                "created_datetime": common_date(res.created_datetime)
                                if res.created_datetime
                                else None,
                            }
                        )

                    elif notification_type == 4:  # Group
                        get_group_details = (
                            db.query(FriendGroupMembers)
                            .filter(FriendGroupMembers.id == res.ref_id)
                            .first()
                        )
                        result_list.append(
                            {
                                "notification_id": res.id,
                                "user_id": res.notification_origin_id,
                                "userName": res.user2.display_name
                                if res.notification_origin_id
                                else "",
                                "userImage": res.user2.profile_img
                                if res.notification_origin_id
                                else "",
                                "type": res.notification_type,
                                "content": get_group_details.friend_groups.group_name
                                if get_group_details
                                else "",
                                "friend_request_id": friend_request_id,
                                "friend_request_status": friend_request_status,
                                "ref_id": res.ref_id if res.ref_id else None,
                                "group_id":get_group_details.group_id if get_group_details else None,
                                "is_read": res.is_read if res.is_read else None,
                                "read_datetime": common_date(res.read_datetime)
                                if res.read_datetime
                                else None,
                                "created_datetime": common_date(res.created_datetime)
                                if res.created_datetime
                                else None,
                            }
                        )
                    elif notification_type == 5:  # Fans
                        result_list.append(
                            {
                                "notification_id": res.id,
                                "user_id": res.notification_origin_id,
                                "userName": res.user2.display_name
                                if res.notification_origin_id
                                else "",
                                "userImage": res.user2.profile_img
                                if res.notification_origin_id
                                else "",
                                "type": res.notification_type,
                                "content": "Following",
                                "created_datetime": common_date(res.created_datetime)
                                if res.created_datetime
                                else None,
                                "is_read": res.is_read if res.is_read else 0,
                            }
                        )
                    elif notification_type == 6:  # Poll Result
                        gte_poll_vote_option = db.query(NuggetPollOption).filter(
                            NuggetPollOption.nuggets_master_id == res.nuggets_master.id,
                            NuggetPollOption.status == 1,
                        )

                        total_vote = (
                            db.query(NuggetPollVoted)
                            .filter(
                                NuggetPollVoted.nugget_master_id
                                == res.nuggets_master.id
                            )
                            .count()
                        )
                        poll_options = []
                        for option in gte_poll_vote_option:
                            if option.status == 1:
                                poll_options.append(
                                    {
                                        "option_id": option.id,
                                        "option_name": option.option_name,
                                        "option_percentage": option.poll_vote_percentage,
                                        "votes": option.votes,
                                    }
                                )

                        result_list.append(
                            {
                                "nugget_id": res.id,  # Nugget Id
                                "userName": res.user.display_name
                                if res.user_id
                                else "",
                                "userImage": res.user.profile_img
                                if res.user_id
                                else defaultimage("profile_img"),
                                "content": res.nuggets_master.content,
                                "poll_option": poll_options,
                                "type": 16,
                                "total_vote": total_vote,
                                "created_datetime": common_date(
                                    res.nuggets_master.created_date
                                )
                                if res.nuggets_master.created_date
                                else None,
                            }
                        )
                    else:
                        result_list.append(
                            {
                                "notification_id": res.id,
                                "user_id": res.notification_origin_id,
                                "userName": res.user2.display_name
                                if res.notification_origin_id
                                else "",
                                "userImage": res.user2.profile_img
                                if res.notification_origin_id
                                else "",
                                "type": res.notification_type,
                                "friend_request_id": friend_request_id,
                                "friend_request_status": friend_request_status,
                                "ref_id": res.ref_id if res.ref_id else None,
                                "is_read": res.is_read if res.is_read else None,
                                "read_datetime": common_date(res.read_datetime)
                                if res.read_datetime
                                else None,
                                "created_datetime": common_date(res.created_datetime)
                                if res.created_datetime
                                else None,
                            }
                        )

                total_unread_count = (
                    db.query(Notification)
                    .filter_by(status=1, is_read=0, user_id=login_user_id)
                    .count()
                )

                return {
                    "status": 1,
                    "msg": "Success",
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "notification_list": result_list,
                    "total_unread_count": total_unread_count,
                    "notification_count": get_row_count,
                }


# 48. Delete Notification
@router.post("/deletenotification")
async def deletenotification(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    notification_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    if notification_id == None:
        return {"status": 0, "msg": "Notification ID missing"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_notification = (
                db.query(Notification).filter_by(id=notification_id, status=1).first()
            )

            if not get_notification:
                return {"status": 0, "msg": "Invalid Notification ID"}
            else:
                if get_notification.user_id == login_user_id:
                    delete_notification = (
                        db.query(Notification)
                        .filter_by(id=notification_id)
                        .update(
                            {
                                "status": 0,
                                "deleted_datetime": datetime.datetime.utcnow(),
                            }
                        )
                    )
                    db.commit()

                    if delete_notification:
                        return {"status": 1, "msg": "Success"}

                    else:
                        return {"status": 0, "msg": "Failed to delete the notification"}

                else:
                    return {
                        "status": 0,
                        "msg": "Your not authorized to delete this notification",
                    }


# 49. Read Notification
@router.post("/readnotification")
async def readnotification(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    notification_id: str = Form(None),
    mark_all_as_read: str = Form(default=0),
    notification_type: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if notification_type and not notification_type.isnumeric():
        return {"status": 0, "msg": "Invalid notification type"}

    else:
        notification_type = notification_type if notification_type else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            if notification_id:
                read_notify = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == login_user_id,
                        Notification.id == notification_id,
                    )
                    .update({"is_read": 1, "read_datetime": datetime.datetime.utcnow()})
                )

            if mark_all_as_read:
                read_notify = (
                    db.query(Notification)
                    .filter(Notification.user_id == login_user_id)
                    .update({"is_read": 1, "read_datetime": datetime.datetime.utcnow()})
                )

            if notification_type:
                read_notify = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == login_user_id,
                        Notification.notification_type == notification_type,
                    )
                    .update({"is_read": 1, "read_datetime": datetime.datetime.utcnow()})
                )

            db.commit()
            return {"status": 1, "msg": "Success"}


# 50. Unfriend a friend
@router.post("/unfriend")
async def unfriend(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_id: str = Form(None,description="user ref id"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if user_id == None:
        return {"status": 0, "msg": "User ID missing"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_user = db.query(User).filter_by(user_ref_id=user_id).first()
    
            if get_user:
          
                friends_rm = (
                    db.query(MyFriends)
                    .filter(
                        MyFriends.status == 1,
                        MyFriends.request_status == 1,
                        or_(
                            MyFriends.sender_id == login_user_id,
                            MyFriends.sender_id == get_user.id,
                        ),
                        or_(
                            MyFriends.receiver_id == get_user.id,
                            MyFriends.receiver_id == login_user_id,
                        ),
                    ).first()
                )
              

                if friends_rm:
                    # Update Status 0-remove
                    friends_rm.status = 0 
                    db.commit()
                    
                    get_friends = (
                        db.query(FriendGroupMembers)
                        .filter(
                            or_(
                                FriendGroupMembers.user_id == user_id,
                                FriendGroupMembers.user_id == login_user_id,
                            )
                        )
                        .filter(
                            FriendGroups.status == 1,
                            or_(
                                FriendGroups.created_by == login_user_id,
                                FriendGroups.created_by == user_id,
                            ),
                        )
                        .all()
                    )

                    frnd_group_member_ids = [frnd.id for frnd in get_friends]

                    del_frnd_group = (
                        db.query(FriendGroupMembers)
                        .filter(FriendGroupMembers.id.in_(frnd_group_member_ids))
                        .delete()
                    )
                    db.commit()

                    return {"status": 1, "msg": "Success"}
                else:
                    return {"status": 0, "msg": "Failed to update. please try again."}

            else:
                return {"status": 0, "msg": "Failed to update. please try again"}


# 51. GET OTHERS PROFILE
@router.post("/getothersprofile")
async def getothersprofile(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    auth_code: str = Form(None, description="SALT + token"),
    user_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth Code is missing"}
    elif user_id == None or not user_id.isnumeric():
        return {"status": 0, "msg": "User ID missing"}

    else:
        access_token = checkToken(db, token)

        if checkAuthCode(auth_code, token) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }
            else:
                user_id = int(user_id)
                get_token_details = (
                    db.query(ApiTokens.user_id).filter_by(token=access_token).first()
                )

                login_user_id = get_token_details.user_id if get_token_details else None

                # Omit blocked users
                requested_by = None
                request_status = 3
                response_type = 1

                get_all_blocked_users = get_friend_requests(
                    db, login_user_id, requested_by, request_status, response_type
                )

                blocked_users = get_all_blocked_users["blocked"]

                if (user_id in blocked_users) and blocked_users:
                    return {"status": 0, "msg": "No result found!"}

                else:
                    get_user = db.query(User).filter(User.id == user_id).first()

                    followers_count = (
                        db.query(FollowUser).filter_by(following_userid=user_id).count()
                    )

                    following_count = (
                        db.query(FollowUser).filter_by(follower_userid=user_id).count()
                    )

                    get_follow_user = (
                        db.query(FollowUser)
                        .filter(
                            FollowUser.following_userid == user_id,
                            FollowUser.follower_userid == login_user_id,
                        )
                        .first()
                    )

                    if not get_user:
                        return {"status": 0, "msg": "No result found!"}

                    else:
                        field = "bio_display_status"

                        get_friend_request = (
                            db.query(MyFriends)
                            .filter(
                                MyFriends.status == 1,
                                or_(
                                    MyFriends.sender_id == login_user_id,
                                    MyFriends.sender_id == user_id,
                                ),
                                or_(
                                    MyFriends.receiver_id == user_id,
                                    MyFriends.receiver_id == login_user_id,
                                ),
                            )
                            .order_by(MyFriends.id.desc())
                            .first()
                        )
                        # Check Claim Influence Or Not
                        get_unclaimed_account = (
                            db.query(User)
                            .join(
                                UserStatusMaster,
                                User.user_status_id == UserStatusMaster.id,
                                isouter=True,
                            )
                            .filter(
                                User.created_by == 1,
                                UserStatusMaster.type == 2,
                                User.id == user_id,
                            )
                            .first()
                        )
                        # Check Account Claimed Or Not From Admin Side
                        check_claim_account = (
                            db.query(ClaimAccounts)
                            .filter(
                                ClaimAccounts.user_id == login_user_id,
                                ClaimAccounts.influencer_id == user_id,
                            )
                            .first()
                        )
                        # check Account Verified
                        account_verify_status = (
                            db.query(VerifyAccounts)
                            .filter(VerifyAccounts.user_id == user_id)
                            .first()
                        )

                        result_list = {
                            "user_id": user_id,
                            "user_ref_id": get_user.user_ref_id
                            if get_user.user_ref_id
                            else "",
                            "name": get_user.display_name
                            if get_user.display_name
                            else "",
                            "email_id": get_user.email_id if get_user.email_id else "",
                            "mobile": ProfilePreference(
                                db,
                                login_user_id,
                                get_user.id,
                                "phone_display_status",
                                get_user.mobile_no,
                            )
                            if get_user.mobile_no
                            else "",
                            "dob": ProfilePreference(
                                db,
                                login_user_id,
                                get_user.id,
                                "dob_display_status",
                                get_user.dob,
                            )
                            if get_user.dob
                            else "",
                            "geo_location": ProfilePreference(
                                db,
                                login_user_id,
                                get_user.id,
                                "location_display_status",
                                get_user.geo_location,
                            )
                            if get_user.geo_location
                            else "",
                            "bio_data": ProfilePreference(
                                db, login_user_id, get_user.id, field, get_user.bio_data
                            ),
                            "profile_image": get_user.profile_img
                            if get_user.profile_img
                            else defaultimage("profile_img"),
                            "cover_image": get_user.cover_image
                            if get_user.cover_image
                            else defaultimage("cover_img"),
                            "website": get_user.website if get_user.website else "",
                            "first_name": get_user.first_name
                            if get_user.first_name
                            else "",
                            "last_name": get_user.last_name
                            if get_user.last_name
                            else "",
                            "gender": get_user.gender if get_user.gender else "",
                            "other_gender":get_user.other_gender if get_user.other_gender else "",
                            "country_code": get_user.country_code
                            if get_user.country_code
                            else "",
                            "country_id": get_user.country_id
                            if get_user.country_id
                            else "",
                            "user_code": get_user.user_code
                            if get_user.user_code
                            else "",
                            "latitude": get_user.latitude if get_user.latitude else "",
                            "longitude": get_user.longitude
                            if get_user.longitude
                            else "",
                            "date_of_join": common_date(get_user.created_at)
                            if get_user.created_at
                            else "",
                            "user_type": get_user.user_type_master.name
                            if get_user.user_type_master.name
                            else "",
                            "user_status": get_user.user_status_master.name
                            if get_user.user_status_master.name
                            else "",
                            "user_status_id": get_user.user_status_id
                            if get_user.user_status_id
                            else "",
                            "friends_count": FriendsCount(db, get_user.id),
                            "follow": True if get_follow_user else False,
                            "followers_count": followers_count,
                            "following_count": following_count,
                            "language": get_user.user_settings[0].language.name
                            if get_user.user_settings
                            else "English",
                            "friend_request_id": get_friend_request.id
                            if get_friend_request
                            else None,
                            "friend_status": get_friend_request.request_status
                            if get_friend_request
                            else None,
                            "is_friend_request_sender": 1
                            if get_friend_request
                            and get_friend_request.sender_id == get_user.id
                            else 0,
                            "lock_nugget": (
                                get_user.user_settings[0].lock_nugget if get_user.user_settings[0].lock_nugget else 0
                            )
                            if get_user.user_settings
                            else "",
                            "lock_fans": (
                                 get_user.user_settings[0].lock_fans if get_user.user_settings[0].lock_fans else 0
                            )
                            if get_user.user_settings
                            else "",
                            "lock_my_connection": (
                                get_user.user_settings[0].lock_my_connection
                                if get_user.user_settings[0].lock_my_connection
                                else 0
                            )
                            if get_user.user_settings
                            else "",
                            "lock_my_influencer": (
                                get_user.user_settings[0].lock_my_influencer
                                if get_user.user_settings[0].lock_my_influencer
                                else 0
                            )
                            if get_user.user_settings
                            else "",
                            "unclaimed_status": (1 if check_claim_account else 0)
                            if get_unclaimed_account
                            else 1,
                            "account_verify_type": (
                                2 if account_verify_status.verify_status == 1 else 1
                            )
                            if account_verify_status
                            else 0,
                            "chime_user_id": get_user.chime_user_id
                            if get_user.chime_user_id
                            else None,
                        }

                        return {"status": 1, "msg": "Success", "profile": result_list}


# 52. List all Blocked users

@router.post("/listallblockedusers")
async def listallblockedusers(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    search_key: str = Form(None),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id if get_token_details else None

            current_page_no = int(page_number)
            
            sender = aliased(User)
            receiver = aliased(User)
            # Perform the left joins
            get_friends =db.query(MyFriends)
            
            get_friends = get_friends.join(sender, MyFriends.sender_id == sender.id)\
                        .join(receiver, MyFriends.receiver_id == receiver.id)

            # Apply the WHERE conditions
            get_friends = get_friends.filter(MyFriends.status == 1, MyFriends.request_status == 3)
            get_friends = get_friends.filter(MyFriends.sender_id == login_user_id)

            # Check if search key is provided in the POST request
            if search_key:
                search_key= '%' + search_key + '%'
                
                get_friends = get_friends.filter(or_(
                    receiver.email_id.ilike(search_key),
                    receiver.display_name.ilike(search_key),
                    receiver.first_name.ilike(search_key),
                    receiver.last_name.ilike(search_key),
                    (receiver.first_name + ' ' + receiver.last_name).ilike(search_key)
                ))

            get_friends_count = get_friends.count()

            if get_friends_count < 1:
                return {"status": 0, "msg": "No Result found"}

            else:
                default_page_size = 50
                limit, offset, total_pages = get_pagination(
                    get_friends_count, current_page_no, default_page_size
                )

                get_friends = get_friends.limit(limit).offset(offset).all()
                friend_details = []
                for frnd_req in get_friends:
                    if frnd_req.sender_id == login_user_id:
                        friend_details.append(
                            {
                                "friend_request_id": frnd_req.id,
                                "user_id": frnd_req.receiver_id
                                if frnd_req.receiver_id
                                else "",
                                "user_ref_id": frnd_req.user2.user_ref_id
                                if frnd_req.receiver_id
                                else "",
                                "email_id": frnd_req.user2.email_id
                                if frnd_req.receiver_id
                                else "",
                                "first_name": frnd_req.user2.first_name
                                if frnd_req.receiver_id
                                else "",
                                "last_name": frnd_req.user2.last_name
                                if frnd_req.receiver_id
                                else "",
                                "display_name": frnd_req.user2.display_name
                                if frnd_req.receiver_id
                                else "",
                                "gender": frnd_req.user2.gender
                                if frnd_req.receiver_id
                                else "",
                                "profile_img": frnd_req.user2.profile_img
                                if frnd_req.receiver_id
                                else "",
                                "online": frnd_req.user2.online
                                if frnd_req.receiver_id
                                else "",
                                "last_seen": (
                                    (
                                        common_date(frnd_req.user2.last_seen)
                                        if frnd_req.user2.last_seen
                                        else ""
                                    )
                                    if frnd_req.user2.last_seen
                                    else None
                                )
                                if frnd_req.receiver_id
                                else "",
                                "typing": 0,
                            }
                        )

                    else:
                        friend_details.append(
                            {
                                "friend_request_id": frnd_req.id,
                                "user_id": frnd_req.user1.id
                                if frnd_req.sender_id
                                else "",
                                "user_ref_id": frnd_req.user1.user_ref_id
                                if frnd_req.sender_id
                                else "",
                                "email_id": frnd_req.user1.email_id
                                if frnd_req.sender_id
                                else "",
                                "first_name": frnd_req.user1.first_name
                                if frnd_req.request_id
                                else "",
                                "last_name": frnd_req.user1.last_name
                                if frnd_req.sender_id
                                else "",
                                "display_name": frnd_req.user1.display_name
                                if frnd_req.sender_id
                                else "",
                                "gender": frnd_req.user1.gender
                                if frnd_req.sender_id
                                else "",
                                "profile_img": frnd_req.user1.profile_img
                                if frnd_req.sender_id
                                else "",
                                "online": frnd_req.user1.online
                                if frnd_req.sender_id
                                else "",
                                "last_seen": (
                                    (
                                        common_date(frnd_req.user1.last_seen)
                                        if frnd_req.user1.last_seen
                                        else ""
                                    )
                                    if frnd_req.user1.last_seen
                                    else None
                                )
                                if frnd_req.sender_id
                                else "",
                                "typing": 0,
                            }
                        )

                return {
                    "status": 1,
                    "msg": "Success",
                    "friends_count": get_friends_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "blocked_list": friend_details,
                }


# 53. Block or Unblock a user
@router.post("/blockunblockuser")
async def blockunblockuser(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_id: str = Form(None),
    action: str = Form(None, description="1-Block,2-Unblock"),
):
    if token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif user_id == None:
        return {"status": 0, "msg": "User ID missing"}
    elif action == None:
        return {"status": 0, "msg": "Action is missing"}

    else:
        access_token = checkToken(db, token)
        action = int(action) if action else None
        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id if get_token_details else None

            if action == 1:  # Block User
                update_my_frnds = (
                    db.query(MyFriends)
                    .filter(
                        or_(
                            MyFriends.sender_id == login_user_id,
                            MyFriends.sender_id == user_id,
                        ),
                        or_(
                            MyFriends.receiver_id == login_user_id,
                            MyFriends.receiver_id == user_id,
                        ),
                    )
                    .update({"status": 0})
                )
                db.commit()
                # request_status 3 means Block
                add_frnd = MyFriends(
                    sender_id=login_user_id,
                    receiver_id=user_id,
                    request_date=datetime.datetime.utcnow(),
                    request_status=3,
                    status_date=datetime.datetime.utcnow(),
                    status=1,
                )
                db.add(add_frnd)
                db.commit()
                if not add_frnd:
                    return {"status": 0, "msg": "Failed to update. please try again"}

                # remove blocked user from group
                get_my_frnds = (
                    db.query(FriendGroupMembers)
                    .filter(
                        FriendGroups.status == 1,
                        or_(
                            FriendGroups.created_by == login_user_id,
                            FriendGroups.created_by == user_id,
                        ),
                    )
                    .filter(
                        or_(
                            FriendGroupMembers.user_id == user_id,
                            FriendGroupMembers.user_id == login_user_id,
                        )
                    )
                )

                get_my_frnds = get_my_frnds.all()
                for frnds in get_my_frnds:
                    del_frnd_group = (
                        db.query(FriendGroupMembers).filter_by(id=frnds.id).delete()
                    )
                    db.commit()

            else:
                get_friend_requests = (
                    db.query(MyFriends)
                    .filter(
                        MyFriends.status == 1,
                        MyFriends.sender_id == login_user_id,
                        MyFriends.receiver_id == user_id,
                    )
                    .order_by(MyFriends.id.desc())
                    .first()
                )

                if get_friend_requests and get_friend_requests.request_status == 3:
                    update_frnds = (
                        db.query(MyFriends)
                        .filter_by(id=get_friend_requests.id)
                        .update({"status": 0})
                    )
                    db.commit()

            return {"status": 1, "msg": "Success"}


# 54. Get User Settings
@router.post("/getusersettings")
async def getusersettings(db: Session = Depends(deps.get_db), token: str = Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_user_settings = (
                db.query(UserSettings)
                .filter_by(status=1, user_id=login_user_id)
                .first()
            )
            if not get_user_settings:
                add_settings = UserSettings(
                    user_id=login_user_id,
                    online_status=1,
                    friend_request="100",
                    nuggets="100",
                    events="100",
                    status=1,
                )
                db.add(add_settings)
                db.commit()
            result_list = {}

            user_status_list = (
                db.query(UserStatusMaster).filter_by(id=get_user_settings.id).first()
            )
            if user_status_list:
                result_list.update(
                    {
                        "referral_needed": user_status_list.referral_needed,
                        "max_event_duration": user_status_list.max_event_duration,
                        "max_event_participants_count": user_status_list.max_event_participants_count,
                    }
                )
            else:
                result_list.update(
                    {
                        "referral_needed": 0,
                        "max_event_duration": 1,
                        "max_event_participants_count": 5,
                    }
                )
            result_list.update({"online_status": get_user_settings.online_status})

            if get_user_settings.online_status == 3:
                online_group_list = (
                    db.query(UserProfileDisplayGroup)
                    .filter(
                        UserProfileDisplayGroup.user_id == login_user_id,
                        UserProfileDisplayGroup.profile_id == "online_status",
                    )
                    .all()
                )
                if online_group_list:
                    list = []

                    for gp_lst in online_group_list:
                        list.append(gp_lst.groupid)
                    result_list.update({"online_group_list": list})
            else:
                result_list.update({"online_group_list": []})

            result_list.update(
                {"phone_display_status": get_user_settings.phone_display_status}
            )

            if get_user_settings.phone_display_status == 3:
                online_group_list = (
                    db.query(UserProfileDisplayGroup)
                    .filter(
                        UserProfileDisplayGroup.user_id == login_user_id,
                        UserProfileDisplayGroup.profile_id == "phone_display_status",
                    )
                    .all()
                )

                if online_group_list:
                    list = []
                    for gp_list in online_group_list:
                        list.append(gp_list.groupid)

                    result_list.update({"phone_group_list": list})
            else:
                result_list.update({"phone_group_list": []})

            result_list.update(
                {"location_display_status": get_user_settings.location_display_status}
            )

            if get_user_settings.location_display_status == 3:
                online_group_list = (
                    db.query(UserProfileDisplayGroup)
                    .filter(
                        UserProfileDisplayGroup.user_id == login_user_id,
                        UserProfileDisplayGroup.profile_id == "location_display_status",
                    )
                    .all()
                )
                if online_group_list:
                    list = []
                    for gp_list in online_group_list:
                        list.append(gp_list.groupid)
                    result_list.update({"location_group_list": list})
            else:
                result_list.update({"location_group_list": []})

            result_list.update(
                {"dob_display_status": get_user_settings.dob_display_status}
            )

            if get_user_settings.dob_display_status == 3:
                online_group_list = (
                    db.query(UserProfileDisplayGroup)
                    .filter(
                        UserProfileDisplayGroup.user_id == login_user_id,
                        UserProfileDisplayGroup.profile_id == "dob_display_status",
                    )
                    .all()
                )
                if online_group_list:
                    list = []
                    for gp_list in online_group_list:
                        list.append(gp_list.groupid)
                    result_list.update({"dob_group_list": list})
            else:
                result_list.update({"dob_group_list": []})

            result_list.update(
                {"bio_display_status": get_user_settings.bio_display_status}
            )

            if get_user_settings.bio_display_status == 3:
                online_group_list = (
                    db.query(UserProfileDisplayGroup)
                    .filter(
                        UserProfileDisplayGroup.user_id == login_user_id,
                        UserProfileDisplayGroup.profile_id == "bio_display_status",
                    )
                    .all()
                )
                if online_group_list:
                    list = []
                    for gp_list in online_group_list:
                        list.append(gp_list.groupid)
                    result_list.update({"bio_group_list": list})
            else:
                result_list.update({"bio_group_list": []})

            result_list.update(
                {"public_nugget_display": get_user_settings.public_nugget_display}
            )

            if (
                get_user_settings.public_nugget_display == 3
                or get_user_settings.public_nugget_display == 5
            ):
                online_group_list = (
                    db.query(UserProfileDisplayGroup)
                    .filter(
                        UserProfileDisplayGroup.user_id == login_user_id,
                        UserProfileDisplayGroup.profile_id == "public_nugget_display",
                    )
                    .all()
                )
                if online_group_list:
                    list = []
                    for gp_list in online_group_list:
                        list.append(gp_list.groupid)
                    result_list.update({"nugget_display_list": list})
            else:
                result_list.update({"nugget_display_list": []})

            result_list.update(
                {"public_event_display": get_user_settings.public_event_display}
            )

            if (
                get_user_settings.public_event_display == 3
                or get_user_settings.public_event_display == 5
            ):
                online_group_list = (
                    db.query(UserProfileDisplayGroup)
                    .filter(
                        UserProfileDisplayGroup.user_id == login_user_id,
                        UserProfileDisplayGroup.profile_id == "public_event_display",
                    )
                    .all()
                )
                if online_group_list:
                    list = []
                    for gp_list in online_group_list:
                        list.append(gp_list.groupid)
                    result_list.update({"event_display_list": list})
            else:
                result_list.update({"event_display_list": []})

            default_melody = {}
            user_default_melody = (
                db.query(EventMelody)
                .filter(
                    EventMelody.created_by == login_user_id,
                    EventMelody.is_default == 1,
                    EventMelody.is_created_by_admin == 0,
                )
                .first()
            )

            if user_default_melody:
                default_melody.update(
                    {
                        "path": user_default_melody.path,
                        "type": user_default_melody.type,
                        "title": user_default_melody.title,
                    }
                )

            result_list.update(
                {
                    "event_type": get_user_settings.default_event_type,
                    "friend_request": get_user_settings.friend_request,
                    "nuggets": get_user_settings.nuggets,
                    "events": get_user_settings.events,
                    "passcode_status": get_user_settings.passcode_status,
                    "passcode": get_user_settings.passcode
                    if get_user_settings.passcode
                    else 0,
                    "waiting_room": get_user_settings.waiting_room,
                    "schmoozing_status": get_user_settings.schmoozing_status,
                    "breakout_status": get_user_settings.breakout_status,
                    "join_before_host": get_user_settings.join_before_host,
                    "auto_record": get_user_settings.auto_record,
                    "participant_join_sound": get_user_settings.participant_join_sound,
                    "screen_share_status": get_user_settings.screen_share_status,
                    "virtual_background": get_user_settings.virtual_background,
                    "host_audio": get_user_settings.host_audio,
                    "host_video": get_user_settings.host_video,
                    "participant_audio": get_user_settings.participant_audio,
                    "participant_video": get_user_settings.participant_video,
                    "melody": get_user_settings.melody,
                    "default_melody": default_melody if default_melody else "",
                    "meeting_header_image": get_user_settings.meeting_header_image,
                    "language_id": get_user_settings.language_id,
                    "time_zone": get_user_settings.time_zone,
                    "default_date_format": get_user_settings.date_format,
                    "mobile_default_page": get_user_settings.mobile_default_page,
                    "account_active_inactive": get_user_settings.manual_acc_active_inactive,
                    "lock_nugget": get_user_settings.lock_nugget
                    if get_user_settings.lock_nugget
                    else 0,
                    "lock_fans": get_user_settings.lock_fans
                    if get_user_settings.lock_fans
                    else 0,
                    "lock_my_connection": get_user_settings.lock_my_connection
                    if get_user_settings.lock_my_connection
                    else 0,
                    "lock_my_influencer": get_user_settings.lock_my_influencer
                    if get_user_settings.lock_my_influencer
                    else 0,
                    "live_event_banner": get_user_settings.live_event_banner
                    if get_user_settings.live_event_banner
                    else "",
                    "talkshow_event_banner": get_user_settings.talkshow_event_banner
                    if get_user_settings.talkshow_event_banner
                    else "",
                    "read_out_language_id": get_user_settings.read_out_language_id
                    if get_user_settings.read_out_language_id
                    else 3,
                    "read_out_language": get_user_settings.read_out_language.language
                    if get_user_settings.read_out_language_id
                    else "",
                }
            )

            return {"status": 1, "msg": "Success", "settings": result_list}


# 55 Update User Settings
@router.post("/updateusersettings")
async def updateusersettings(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    online_status: str = Form(
        None, description="0->Don't show,1->Public,2->Friends only,3->Special Group"
    ),
    phone_display_status: str = Form(
        None, description="0->Don't show,1->Public,2->Friends only,3->Special Group"
    ),
    location_display_status: str = Form(
        None, description="0->Don't show,1->Public,2->Friends only,3->Special Group"
    ),
    dob_display_status: str = Form(
        None, description="0->Don't show,1->Public,2->Friends only,3->Special Group"
    ),
    bio_display_status: str = Form(
        None, description="0->Don't show,1->Public,2->Friends only,3->Special Group"
    ),
    friend_request: str = Form(
        None,
        description="3 digit 000 to 111, 1st digit->Push notify , 2nd digit->Email notify,3rd digit->SMS",
    ),
    nuggets: str = Form(
        None,
        description="3 digit 000 to 111, 1st digit->Push notify , 2nd digit->Email notify,3rd digit->SMS",
    ),
    events: str = Form(
        None,
        description="3 digit 000 to 111, 1st digit->Push notify , 2nd digit->Email notify,3rd digit->SMS",
    ),
    passcode_status: str = Form(None, description="1->Enabled,0->Disabled"),
    passcode: str = Form(None),
    waiting_room: str = Form(None, description="1->Enabled,0->Disabled"),
    schmoozing_status: str = Form(None, description="1->Enabled,0->Disabled"),
    breakout_status: str = Form(None, description="1->Enabled,0->Disabled"),
    join_before_host: str = Form(None, description="1->Enabled,0->Disabled"),
    auto_record: str = Form(None, description="1->Enabled,0->Disabled"),
    participant_join_sound: str = Form(None, description="1->Sound On,0->Sound Off"),
    screen_share_status: str = Form(None, description="1->Enabled,0->Disabled"),
    virtual_background: str = Form(None, description="1->Enabled,0->Disabled"),
    host_audio: str = Form(None, description="1->On,0->Off"),
    host_video: str = Form(None),
    participant_audio: str = Form(None, description="1->On,0->Off"),
    participant_video: str = Form(None, description="1->On,0->Off"),
    melody: str = Form(None),
    meeting_header_image: UploadFile = File(None, description="event Banner"),
    language_id: str = Form(None, description="table 65"),
    time_zone: str = Form(None, description="get from 64"),
    date_format: str = Form(None),
    mobile_default_page: str = Form(None, description="1->nuggets,2->events,3->chats"),
    default_melody: UploadFile = File(None),
    event_type: str = Form(None),
    public_nugget_display: str = Form(None),
    public_event_display: str = Form(None),
    account_active_inactive: str = Form(None),
    lock_nugget: str = Form(None, description="1-Yes,0-No"),
    lock_fans: str = Form(None, description="1-Yes,0-No"),
    lock_my_connection: str = Form(None, description="1-Yes,0-No"),
    lock_my_influencer: str = Form(None, description="1-Yes,0-No"),
    live_event_banner: UploadFile = File(None),
    talkshow_event_banner: UploadFile = File(None),
    profile_field_name: str = Form(None),
    groupid: str = Form(None, description="example [1,2,3]"),
    group_update_type: str = Form(None),
    read_out_language_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not profile_field_name and groupid:
        return {"status": 0, "msg": "Profile field name required"}
    
    elif profile_field_name and not groupid:
        return {"status": 0, "msg": "Group id required"}
    elif read_out_language_id and not read_out_language_id.isnumeric():
        return {"status": 0, "msg": "Invalid read out language"}

    else:
        access_token = checkToken(db, token.strip())
        if access_token == False:
            return {
                "sttaus": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens)
                .filter(ApiTokens.token == access_token.strip())
                .first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None

            user_setting_id = ""

            get_user_settings = (
                db.query(UserSettings)
                .filter(UserSettings.status == 1, UserSettings.user_id == login_user_id)
                .first()
            )
            if get_user_settings:
                user_setting_id = get_user_settings.id
            else:
                model = UserSettings(
                    user_id=login_user_id,
                    online_status=1,
                    friend_request="100",
                    nuggets="100",
                    events="100",
                    status=1,
                )
                db.add(model)
                db.commit()
                user_setting_id = model.id

            if user_setting_id != "":
                settings = (
                    db.query(UserSettings)
                    .filter(
                        UserSettings.status == 1, UserSettings.id == user_setting_id
                    )
                    .first()
                )
                if settings:
                    default_melody_list = {}
                    edit_melody = (
                        db.query(EventMelody)
                        .filter(
                            EventMelody.created_by == login_user_id,
                            EventMelody.is_default == 1,
                            EventMelody.is_created_by_admin == 0,
                        )
                        .first()
                    )
                    if edit_melody:
                        default_melody_list.update(
                            {
                                "path": edit_melody.path,
                                "type": edit_melody.type,
                                "title": edit_melody.title,
                            }
                        )

                    if default_melody:
                        file_name = default_melody.filename
                        file_temp = default_melody.content_type
                        file_read = await default_melody.read()
                        file_size = len(file_read)
                        file_ext = os.path.splitext(default_melody.filename)[1]

                        media_type = 1
                        type = ""
                        if (
                            file_ext == ".png"
                            or file_ext == ".jpeg"
                            or file_ext == ".jpg"
                            or file_ext == ".gif"
                        ):
                            type = "image"
                        elif file_ext == ".mp3":
                            type = "audio"
                            media_type = 3
                        elif file_ext == ".pptx" or file_ext == ".ppt":
                            type = "ppt"
                            media_type = 4
                        elif "video" in file_temp:
                            type = "video"
                            media_type = 2

                        if (
                            file_size > 1000000
                            and type == "image"
                            and file_ext != ".gif"
                        ):
                            compress = 1
                            uploaded_file_path = await read_file_upload(
                                file_read, file_ext, compress
                            )

                            s3_file_path = f"eventsmelody/eventsmelody_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                            result = upload_to_s3(uploaded_file_path, s3_file_path)
                            if result["status"] == 1:
                                default_melody_list.update(
                                    {"path": result["url"], "type": media_type}
                                )
                                if edit_melody:
                                    edit_melody.path = result["url"]
                                    edit_melody.type = media_type
                                    db.commit()

                                    default_melody_list.update(
                                        {"title": edit_melody.title}
                                    )
                                else:
                                    new_melody = EventMelody(
                                        title="Your default",
                                        is_default=1,
                                        path=result["url"],
                                        type=media_type,
                                        created_at=datetime.datetime.utcnow(),
                                        created_by=login_user_id,
                                    )
                                    db.add(new_melody)
                                    db.commit()
                                    default_melody_list.update(
                                        {"title": new_melody.title}
                                    )

                            else:
                                return result

                        else:
                            compress = None
                            uploaded_file_path = await read_file_upload(
                                file_read, file_ext, compress
                            )

                            s3_file_path = f"eventsmelody/eventsmelody_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            if type == "video" and file_ext != ".mp4":
                                s3_file_path = f"eventsmelody/eventsmelody_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}.mp4"
                                uploaded_file_path = video_file_upload(
                                    default_melody, compress=1, file_ext=file_ext
                                )

                            result = upload_to_s3(uploaded_file_path, s3_file_path)

                            if result["status"] == 1:
                                default_melody_list.update(
                                    {"path": result["url"], "type": media_type}
                                )
                                if edit_melody:
                                    edit_melody.path = result["url"]
                                    edit_melody.type = media_type
                                    db.commit()

                                    default_melody_list.update(
                                        {"title": edit_melody.title}
                                    )
                                else:
                                    new_melody = EventMelody(
                                        title="Your default",
                                        is_default=1,
                                        path=result["url"],
                                        type=media_type,
                                        created_at=datetime.datetime.utcnow(),
                                        created_by=login_user_id,
                                    )
                                    db.add(new_melody)
                                    db.commit()
                                    default_melody_list.update(
                                        {"title": new_melody.title}
                                    )
                            else:
                                return {"status": 0, "msg": "Not able to upload"}

                    header_image = (
                        settings.meeting_header_image
                        if settings.meeting_header_image
                        else None
                    )

                    if meeting_header_image:
                        file_name = meeting_header_image.filename
                        file_temp = meeting_header_image.content_type
                        file_read = await meeting_header_image.read()
                        file_size = len(file_read)
                        file_ext = os.path.splitext(meeting_header_image.filename)[1]
                        local_file_upload = ""
                        extensions = [".jpeg", ".jpg", ".png"]

                        if not file_ext in extensions:
                            return {"status": 0, "msg": "Image format does not support"}

                        elif file_size > 10240000:
                            return {
                                "status": 0,
                                "msg": "Image size must be less than 10 MB",
                            }

                        else:
                            if file_size > 1024:
                                local_file_upload = await read_file_upload(
                                    file_read, file_ext, compress=1
                                )
                                header_image = local_file_upload
                            else:
                                local_file_upload = await read_file_upload(
                                    file_read, file_ext, compress=None
                                )
                                header_image = local_file_upload

                        if header_image:
                            s3_file_pth = f"meetingheaderimage/MeetingHeaderImage_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                            result = upload_to_s3(local_file_upload, s3_file_pth)
                            if result["status"] == 1:
                                header_image = result["url"]
                            else:
                                return result

                    live_banner = (
                        settings.live_event_banner
                        if settings.live_event_banner
                        else None
                    )
                    if live_event_banner:
                        file_name = live_event_banner.filename
                        file_temp = live_event_banner.content_type
                        file_read = await live_event_banner.read()
                        file_size = len(file_read)
                        file_ext = os.path.splitext(live_event_banner.filename)[1]
                        local_file_upload = ""
                        extensions = [".jpeg", ".jpg", ".png"]

                        if not file_ext in extensions:
                            return {"status": 0, "msg": "Image format does not support"}

                        elif file_size > 10240000:
                            return {
                                "status": 0,
                                "msg": "Image size must be less than 10 MB",
                            }

                        else:
                            if file_size > 1024:
                                local_file_upload = await read_file_upload(
                                    file_read, file_ext, compress=1
                                )
                                live_banner = local_file_upload
                            else:
                                local_file_upload = await read_file_upload(
                                    file_read, file_ext, compress=None
                                )
                                live_banner = local_file_upload

                        if live_banner:
                            s3_file_pth = f"meetingheaderimage/MeetingHeaderImage_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                            result = upload_to_s3(local_file_upload, s3_file_pth)
                            if result["status"] == 1:
                                live_banner = result["url"]
                            else:
                                return result

                    talkshow_banner = (
                        settings.talkshow_event_banner
                        if settings.talkshow_event_banner
                        else None
                    )
                    if talkshow_event_banner:
                        file_name = talkshow_event_banner.filename
                        file_temp = talkshow_event_banner.content_type
                        file_read = await talkshow_event_banner.read()
                        file_size = len(file_read)
                        file_ext = os.path.splitext(talkshow_event_banner.filename)[1]
                        local_file_upload = ""
                        extensions = [".jpeg", ".jpg", ".png"]

                        if not file_ext in extensions:
                            return {"status": 0, "msg": "Image format does not support"}

                        elif file_size > 10240000:
                            return {
                                "status": 0,
                                "msg": "Image size must be less than 10 MB",
                            }

                        else:
                            if file_size > 1024:
                                local_file_upload = await read_file_upload(
                                    file_read, file_ext, compress=1
                                )
                                talkshow_banner = local_file_upload
                            else:
                                local_file_upload = await read_file_upload(
                                    file_read, file_ext, compress=None
                                )
                                talkshow_banner = local_file_upload

                        if talkshow_banner:
                            s3_file_pth = f"meetingheaderimage/MeetingHeaderImage_{random.randint(1111,9999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"

                            result = upload_to_s3(local_file_upload, s3_file_pth)
                            if result["status"] == 1:
                                talkshow_banner = result["url"]
                            else:
                                return result

                    breakout_status = (
                        int(breakout_status)
                        if breakout_status and breakout_status.isnumeric()
                        else settings.breakout_status
                    )
                    waiting_room = (
                        int(waiting_room)
                        if waiting_room != None and waiting_room.isnumeric()
                        else settings.waiting_room
                    )
                    online_status = (
                        int(online_status)
                        if online_status != None and online_status.isnumeric()
                        else settings.online_status
                    )
                    phone_display_status = (
                        int(phone_display_status)
                        if phone_display_status != None
                        and phone_display_status.isnumeric()
                        else settings.phone_display_status
                    )
                    location_display_status = (
                        int(location_display_status)
                        if location_display_status != None
                        and location_display_status.isnumeric()
                        else settings.location_display_status
                    )
                    dob_display_status = (
                        int(dob_display_status)
                        if dob_display_status != None and dob_display_status.isnumeric()
                        else settings.dob_display_status
                    )
                    bio_display_status = (
                        int(bio_display_status)
                        if bio_display_status != None and bio_display_status.isnumeric()
                        else settings.bio_display_status
                    )
                    friend_request = (
                        friend_request
                        if friend_request != None and friend_request.isnumeric()
                        else settings.friend_request
                    )
                    passcode_status = (
                        int(passcode_status)
                        if passcode_status != None and passcode_status.isnumeric()
                        else settings.passcode_status
                    )
                    schmoozing_status = (
                        int(schmoozing_status)
                        if schmoozing_status != None and schmoozing_status.isnumeric()
                        else settings.schmoozing_status
                    )
                    join_before_host = (
                        int(join_before_host)
                        if join_before_host != None and join_before_host.isnumeric()
                        else settings.join_before_host
                    )
                    auto_record = (
                        int(auto_record)
                        if auto_record != None and auto_record.isnumeric()
                        else settings.auto_record
                    )
                    participant_join_sound = (
                        int(participant_join_sound)
                        if participant_join_sound != None
                        and participant_join_sound.isnumeric()
                        else settings.participant_join_sound
                    )
                    screen_share_status = (
                        int(screen_share_status)
                        if screen_share_status != None
                        and screen_share_status.isnumeric()
                        else settings.screen_share_status
                    )
                    virtual_background = (
                        int(virtual_background)
                        if virtual_background != None and virtual_background.isnumeric()
                        else settings.virtual_background
                    )
                    host_audio = (
                        int(host_audio)
                        if host_audio != None and host_audio.isnumeric()
                        else settings.host_audio
                    )
                    host_video = (
                        int(host_video)
                        if host_video != None and host_video.isnumeric()
                        else settings.host_video
                    )
                    participant_audio = (
                        int(participant_audio)
                        if participant_audio != None and participant_audio.isnumeric()
                        else settings.participant_audio
                    )
                    participant_video = (
                        int(participant_video)
                        if participant_video != None and participant_video.isnumeric()
                        else settings.participant_video
                    )
                    melody = (
                        int(melody)
                        if melody != None and melody.isnumeric()
                        else settings.melody
                    )
                    language_id = (
                        int(language_id)
                        if language_id and language_id.isnumeric()
                        else settings.language_id
                    )
                    time_zone = time_zone if time_zone else settings.time_zone
                    mobile_default_page = (
                        int(mobile_default_page)
                        if mobile_default_page != None
                        and mobile_default_page.isnumeric()
                        else settings.mobile_default_page
                    )
                    public_nugget_display = (
                        int(public_nugget_display)
                        if public_nugget_display != None
                        and public_nugget_display.isnumeric()
                        else settings.public_nugget_display
                    )
                    public_event_display = (
                        int(public_event_display)
                        if public_event_display != None
                        and public_event_display.isnumeric()
                        else settings.public_event_display
                    )
                    manual_acc_active_inactive = (
                        int(account_active_inactive)
                        if account_active_inactive != None
                        and account_active_inactive.isnumeric()
                        else settings.manual_acc_active_inactive
                    )
                    event_type = (
                        int(event_type)
                        if event_type and event_type.isnumeric()
                        else settings.default_event_type
                    )

                    lock_nugget = (
                        int(lock_nugget)
                        if lock_nugget and lock_nugget.isnumeric()
                        else settings.lock_nugget
                    )
                    lock_fans = (
                        int(lock_fans)
                        if lock_fans and lock_fans.isnumeric()
                        else settings.lock_fans
                    )
                    lock_my_connection = (
                        int(lock_my_connection)
                        if lock_my_connection and lock_my_connection.isnumeric()
                        else settings.lock_my_connection
                    )
                    lock_my_influencer = (
                        int(lock_my_influencer)
                        if lock_my_influencer and lock_my_influencer.isnumeric()
                        else settings.lock_my_influencer
                    )

                    settings.online_status = (
                        online_status
                        if online_status != None
                        else settings.online_status
                    )
                    settings.phone_display_status = (
                        phone_display_status
                        if phone_display_status != None
                        else settings.phone_display_status
                    )
                    settings.location_display_status = (
                        location_display_status
                        if location_display_status != None
                        else settings.location_display_status
                    )
                    settings.dob_display_status = (
                        dob_display_status
                        if dob_display_status != None
                        else settings.dob_display_status
                    )
                    settings.bio_display_status = (
                        bio_display_status
                        if bio_display_status != None
                        else settings.bio_display_status
                    )
                    settings.friend_request = (
                        friend_request
                        if friend_request != None and len(friend_request.strip()) == 3
                        else settings.friend_request
                    )
                    settings.nuggets = (
                        nuggets
                        if nuggets and len(nuggets.strip()) == 3
                        else settings.nuggets
                    )
                    settings.events = (
                        events
                        if events != None and len(events.strip()) == 3
                        else settings.events
                    )
                    settings.passcode_status = (
                        passcode_status
                        if passcode_status != None and 1 >= passcode_status >= 0
                        else settings.passcode_status
                    )
                    settings.passcode = (
                        passcode
                        if passcode != None and passcode.strip() != ""
                        else settings.passcode
                    )
                    settings.waiting_room = (
                        waiting_room
                        if waiting_room != None and 0 <= waiting_room <= 1
                        else settings.waiting_room
                    )
                    settings.schmoozing_status = (
                        schmoozing_status
                        if schmoozing_status != None and 0 <= schmoozing_status <= 1
                        else settings.schmoozing_status
                    )
                    settings.breakout_status = (
                        breakout_status
                        if breakout_status != None and 0 <= breakout_status <= 1
                        else settings.breakout_status
                    )
                    settings.join_before_host = (
                        join_before_host
                        if join_before_host != None and 0 <= join_before_host <= 1
                        else settings.join_before_host
                    )
                    settings.auto_record = (
                        auto_record
                        if auto_record != None and 0 <= auto_record <= 1
                        else settings.auto_record
                    )
                    settings.participant_join_sound = (
                        participant_join_sound
                        if participant_join_sound != None
                        and 0 <= participant_join_sound <= 1
                        else settings.participant_join_sound
                    )
                    settings.screen_share_status = (
                        screen_share_status
                        if screen_share_status != None and 0 <= screen_share_status <= 1
                        else settings.screen_share_status
                    )
                    settings.virtual_background = (
                        virtual_background
                        if virtual_background != None and 0 <= virtual_background <= 1
                        else settings.virtual_background
                    )
                    settings.host_audio = (
                        host_audio
                        if host_audio != None and 0 <= host_audio <= 1
                        else settings.host_audio
                    )
                    settings.host_video = (
                        host_video
                        if host_video != None and 0 <= host_video <= 1
                        else settings.host_video
                    )
                    settings.participant_audio = (
                        participant_audio
                        if participant_audio != None and 0 <= participant_audio <= 1
                        else settings.participant_audio
                    )
                    settings.participant_video = (
                        participant_video
                        if participant_video != None and 0 <= participant_video <= 1
                        else settings.participant_video
                    )
                    settings.melody = (
                        melody if melody and melody >= 0 else settings.melody
                    )
                    settings.meeting_header_image = header_image
                    settings.language_id = (
                        language_id
                        if language_id != None and language_id > 0
                        else settings.language_id
                    )
                    settings.time_zone = time_zone if time_zone else settings.time_zone
                    settings.date_format = (
                        date_format
                        if date_format != "" and date_format != None
                        else settings.date_format
                    )
                    settings.mobile_default_page = (
                        mobile_default_page
                        if mobile_default_page != None and 0 <= mobile_default_page <= 3
                        else settings.mobile_default_page
                    )
                    settings.public_nugget_display = (
                        public_nugget_display
                        if public_nugget_display != None
                        else settings.public_nugget_display
                    )
                    settings.public_event_display = (
                        public_event_display
                        if public_event_display != None
                        else settings.public_event_display
                    )
                    settings.manual_acc_active_inactive = (
                        manual_acc_active_inactive
                        if manual_acc_active_inactive != None
                        else settings.manual_acc_active_inactive
                    )
                    settings.default_event_type = (
                        event_type
                        if event_type != None
                        else settings.default_event_type
                    )
                    settings.lock_nugget = lock_nugget
                    settings.lock_fans = lock_fans
                    settings.lock_my_connection = lock_my_connection
                    settings.lock_my_influencer = lock_my_influencer
                    settings.live_event_banner = live_banner
                    settings.talkshow_event_banner = talkshow_banner
                    settings.read_out_language_id = read_out_language_id

                    db.commit()
                    if groupid and profile_field_name:
                        groupid = ast.literal_eval(groupid) if groupid else None
                        
                        if groupid:
                            delete_group = (
                                db.query(UserProfileDisplayGroup)
                                .filter(
                                    and_(
                                        UserProfileDisplayGroup.profile_id
                                        == profile_field_name,
                                        UserProfileDisplayGroup.user_id
                                        == login_user_id,
                                    )
                                )
                                .delete()
                            )
                            gcount = len(groupid)
                            listtype = type if group_update_type else 3
                            success = 0
                            for gid in groupid:
                                new_profile = UserProfileDisplayGroup(
                                    user_id=login_user_id,
                                    profile_id=profile_field_name,
                                    groupid=gid,
                                    created_date=datetime.datetime.utcnow(),
                                )
                                db.add(new_profile)
                                db.commit()
                                db.refresh(new_profile)
                                if new_profile:
                                    success += 1

                            if gcount == success:
                                update = db.query(UserSettings).filter(
                                    UserSettings.user_id == login_user_id
                                )
                                setattr(update, profile_field_name, listtype)
                                db.commit()
                                # return {"status":1,"msg":"Success"}
                                pass
                            else:
                                db.query(UserProfileDisplayGroup).filter_by(
                                    profile_id=profile_field_name, user_id=login_user_id
                                ).delete()
                                db.commit()
                                return {
                                    "status": 0,
                                    "msg": "Failed to update group list",
                                }
                        else:
                            return {"status": 0, "msg": "Invalid group list"}

                    return {
                        "status": 1,
                        "msg": "Success",
                        "url": meeting_header_image,
                        "default_melody": default_melody if default_melody else None,
                    }

                return {"status": 0, "msg": "Faild"}

            return {"status": 0, "msg": "Faild"}


#  56. Get Event Melody


@router.post("/geteventmelody")
async def geteventmelody(db: Session = Depends(deps.get_db), token: str = Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            login_user_id = 0
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            result_list = []
            getEventMelody = (
                db.query(EventMelody)
                .filter(
                    or_(
                        and_(
                            EventMelody.status == 1,
                            EventMelody.is_created_by_admin == 1,
                        ),
                        and_(
                            EventMelody.status == 1,
                            EventMelody.is_default == 1,
                            EventMelody.is_created_by_admin == 0,
                            EventMelody.created_by == login_user_id,
                        ),
                    )
                )
                .all()
            )
            if getEventMelody:
                result_list = []
                for melody in getEventMelody:
                    result_list.append(
                        {"id": melody.id, "title": melody.title, "path": melody.path}
                    )
                return {"status": 1, "msg": "Success", "melody": result_list}
            else:
                return {"status": 0, "msg": "Failed", "melody": []}


# 57. Block Multiple user


@router.post("/blockmultipleuser")
async def blockmultipleuser(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_id: str = Form(None, description="example 1,2,3"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if user_id == None:
        return {"status": 0, "msg": "User ID missing"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            login_user_id = 0
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id
            # return user_id
            userlist = ast.literal_eval(user_id) if user_id and user_id != None and user_id != 'null' else None

            if userlist:
                # userlist = json.loads(user_id)
                update = False
                for user_id in userlist:
                    # Update existing friend request status to blocked
                    db.query(MyFriends).filter(
                        or_(
                            and_(
                                MyFriends.sender_id == login_user_id,
                                MyFriends.receiver_id == user_id,
                            ),
                            and_(
                                MyFriends.sender_id == user_id,
                                MyFriends.receiver_id == login_user_id,
                            ),
                        )
                    ).update(
                        {
                            "request_status": 3,
                            "status_date": datetime.datetime.utcnow(),
                            "status": 0,
                        }
                    )

                    # Create new friend request with status blocked
                    model = MyFriends(
                        sender_id=login_user_id,
                        receiver_id=user_id,
                        request_date=datetime.datetime.utcnow(),
                        request_status=3,
                        status_date=datetime.datetime.utcnow(),
                        status=1,
                    )
                    db.add(model)
                    db.commit()
                    if model.id:
                        update = True

                    # Remove blocked user from groups
                    subquery1 = (
                        db.query(FriendGroups)
                        .filter(
                            and_(
                                FriendGroups.status == 1,
                                FriendGroups.created_by == login_user_id,
                            )
                        )
                        .with_entities(FriendGroups.id)
                        .first()
                    )
                    subquery2 = (
                        db.query(FriendGroups)
                        .filter(
                            and_(
                                FriendGroups.status == 1,
                                FriendGroups.created_by == user_id,
                            )
                        )
                        .with_entities(FriendGroups.id)
                        .first()
                    )
                    query = db.query(FriendGroupMembers).filter(
                        or_(
                            FriendGroupMembers.user_id == user_id,
                            FriendGroupMembers.user_id == login_user_id,
                        ),
                        FriendGroupMembers.group_id.in_([subquery1, subquery2]),
                    )
                    for group_member in query:
                        db.delete(group_member)

                if update:
                    return {"status": 1, "msg": "Success"}
                else:
                    return {"status": 0, "msg": "Failed to update. Please try again."}
            else:
                return {"status": 0, "msg": "User ID missing."}


# 58. Global Search Events


@router.post("/globalsearchevents")
async def globalsearchevents(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    search_key: str = Form(None),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not search_key or search_key.strip() == "":
        return {"status": 0, "msg": "Search Key missing"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            login_user_id = 0
            get_token_details = (
                db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            search_key = search_key.strip()

            current_page_no = int(page_number)
            criteria = (
                db.query(Events).join(User,User.id == Events.created_by,isouter=True)\
                .filter(
                    Events.status == 1,
                    Events.event_status == 1,
                    Events.event_type_id == 1,
                    or_(
                        Events.title.like( "%" +search_key + "%" ),
                        User.display_name.like( "%" +search_key + "%" ),
                        User.first_name.like( "%" +search_key + "%" ),
                        User.last_name.like( "%" +search_key + "%" ),
                        User.first_name.like( "%" +search_key + "%" )
                    ),
                    Events.start_date_time > datetime.datetime.utcnow()
                )
            )
            
            # Execute the query
            get_row_count = criteria.count()

            if get_row_count < 1:
                return {
                    "status": 1,
                    "msg": "No Result found",
                    "events_count": 0,
                    "total_pages": 1,
                    "current_page_no": 1,
                    "events_list": [],
                }
            else:
                default_page_size = 10
                limit, offset, total_pages = get_pagination(
                    get_row_count, current_page_no, default_page_size
                )
                
                event_list=criteria.order_by(Events.start_date_time.asc()).limit(limit).offset(offset).all()
                result_list = []
                if event_list:
                    waiting_room = 0
                    join_before_host = 0
                    sound_notify = 0
                    user_screenshare = 0
                    settings = (
                        db.query(UserSettings.waiting_room,UserSettings.join_before_host,UserSettings.participant_join_sound,UserSettings.screen_share_status)
                        .filter(UserSettings.user_id == login_user_id)
                        .first()
                    )
                    if settings:
                        waiting_room = settings.waiting_room
                        join_before_host = settings.join_before_host
                        sound_notify = settings.participant_join_sound
                        user_screenshare = settings.screen_share_status
                
                    for event in event_list:
                        default_melody = (
                            db.query(EventMelody)
                            .filter_by(id=event.event_melody_id)
                            .first()
                        )
                        default_av = (
                            db.query(EventDefaultAv)
                            .filter(EventDefaultAv.event_id == event.id)
                            .order_by(EventDefaultAv.id.desc())
                            .first()
                        )

                        result_list.append(
                            {
                                "event_id": event.id,
                                "event_name": event.title,
                                "reference_id": event.ref_id,
                                "event_type_id": event.event_type_id,
                                "event_layout_id": event.event_layout_id,
                                "message": event.description,
                                "start_date_time": event.start_date_time,
                                "start_date": event.start_date_time.strftime("%b %d")
                                if event.start_date_time
                                else "",
                                "start_time": event.start_date_time.strftime("%I:%M %p")
                                if event.start_date_time
                                else "",
                                "duration": event.duration,
                                "no_of_participants": event.no_of_participants,
                                "banner_image": event.cover_img,
                                "is_host": 1
                                if login_user_id == event.created_by
                                else 0,
                                "created_at": event.created_at.strftime(
                                    "%Y-%m-%d %I:%M %p"
                                )
                                if event.created_at
                                else "",
                                "original_user_name": event.user.display_name
                                if event.created_by
                                else "",
                                "original_user_id": event.created_by
                                if event.created_by
                                else "",
                                "original_user_image": event.user.profile_img
                                if event.created_by
                                else "",
                                "waiting_room": event.waiting_room
                                if event.waiting_room in [0, 1]
                                else waiting_room,
                                "join_before_host": event.join_before_host
                                if event.join_before_host in [0, 1]
                                else join_before_host,
                                "sound_notify": event.sound_notify
                                if event.sound_notify in [0, 1]
                                else sound_notify,
                                "user_screenshare": event.user_screenshare
                                if (
                                    event.user_screenshare == 1
                                    or event.user_screenshare == 0
                                )
                                else user_screenshare,
                                "event_melody_id": event.event_melody_id,
                                "melodies": {
                                    "path": default_melody.path
                                    if default_melody
                                    else "",
                                    "type": default_melody.type
                                    if default_melody
                                    else "",
                                    "is_default": None,
                                },  # default_melody.event_id is None
                                "default_host_audio": default_av.default_host_audio
                                if default_av
                                else "",
                                "default_host_video": default_av.default_host_video
                                if default_av
                                else "",
                                "default_guest_audio": default_av.default_guest_audio
                                if default_av
                                else "",
                                "default_guest_video": default_av.default_guest_video
                                if default_av
                                else "",
                            }
                        )

                return {
                    "status": 1,
                    "msg": "success",
                    "events_count": int(get_row_count),
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "events_list": result_list,
                }


#  59. Global Search Nuggets


@router.post("/globalsearchnuggets")
async def globalsearchnuggets(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    search_key: str = Form(None),
    page_number: str = Form(1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if search_key == None:
        return {"status": 0, "msg": "Search Key missing"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid Page Number"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            login_user_id = 0
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            search_key = search_key.strip()

            current_page_no = int(page_number)

            group_ids = getGroupids(db, login_user_id)
            my_friends = get_friend_requests(
                db,
                login_user_id,
                requested_by=None,
                request_status=1,
                response_type=1,
                search_key=None,
            )
            my_friends = my_friends["accepted"]

            criteria = (
                db.query(Nuggets)
                .join(Nuggets.user)
                .join(Nuggets.master)
                .outerjoin(Nuggets.likes.filter_by(status=1))
                .outerjoin(Nuggets.comments.filter_by(status=1))
                .outerjoin(Nuggets.share_with)
                .with_entities(
                    Nuggets.id,
                    Nuggets.nuggets_id,
                    Nuggets.user_id,
                    Nuggets.type,
                    Nuggets.share_type,
                    Nuggets.created_date,
                    Nuggets.nugget_status,
                    Nuggets.status,
                    case(
                        [
                            (Nuggets.likes.any(user_id=login_user_id), 1),
                        ],
                        else_=0,
                    ).label("liked"),
                    func.count(Nuggets.likes.distinct(Nuggets.likes.id)).label(
                        "total_likes"
                    ),
                    func.count(Nuggets.comments.distinct(Nuggets.comments.id)).label(
                        "total_comments"
                    ),
                )
                .filter(
                    Nuggets.status == 1,
                    Nuggets.nugget_status == 1,
                    Nuggets.master.status == 1,
                    (
                        Nuggets.master.content.ilike(f"%{search_key}%")
                        | Nuggets.user.display_name.ilike(f"%{search_key}%")
                        | Nuggets.user.first_name.ilike(f"%{search_key}%")
                        | Nuggets.user.last_name.ilike(f"%{search_key}%")
                        | (
                            Nuggets.user.first_name + " " + Nuggets.user.last_name
                        ).ilike(f"%{search_key}%")
                    ),
                    (
                        (Nuggets.share_type == 1)
                        | (
                            (Nuggets.share_type == 2)
                            & (Nuggets.user_id == login_user_id)
                        )
                        | (
                            (Nuggets.share_type == 3)
                            & (Nuggets.share_with.type == 1)
                            & (Nuggets.share_with.share_with.in_(group_ids))
                        )
                        | (
                            (Nuggets.share_type == 4)
                            & (Nuggets.share_with.type == 2)
                            & (Nuggets.share_with.share_with.in_([login_user_id]))
                        )
                        | (
                            (Nuggets.share_type == 6)
                            & (Nuggets.user_id.in_(my_friends))
                        )
                    ),
                )
            )

            get_all_blocked_users = get_friend_requests(
                login_user_id,
                requested_by=None,
                request_status=3,
                response_type=1,
                search_key=None,
            )
            blocked_users = get_all_blocked_users.blocked
            if blocked_users:
                criteria = criteria.filter(
                    and_(Nuggets.user_id.notin_(blocked_users)),
                )
            criteria = criteria.order_by(Nuggets.created_date.desc()).group_by(
                Nuggets.id
            )
            get_row_count = criteria.count()
            if get_row_count < 1:
                return {"status": 0, "msg": "No Result found"}
            else:
                default_page_size = 10
                limit, offset, total_pages = get_pagination(
                    get_row_count, current_page_no, default_page_size
                )
                criteria = criteria.limit(limit)
                criteria = criteria.offset(offset)
                get_result = criteria.all()
                result_list = []

                count = 0
                for nuggets in get_result:
                    attachments = []
                    total_likes = nuggets.total_likes if nuggets.total_likes > 0 else 0
                    total_comments = (
                        nuggets.total_comments if nuggets.total_comments > 0 else 0
                    )
                    img_count = 0
                    attachments = []
                    if nuggets.nuggets.nuggetsAttachments:
                        for attachmentdetails in (
                            db.query(NuggetsAttachment)
                            .filter(NuggetsAttachment.nuggets == nuggets.nuggets)
                            .all()
                        ):
                            if attachmentdetails.status == 1:
                                attachments.append(
                                    {
                                        "media_id": attachmentdetails.id,
                                        "media_type": attachmentdetails.media_type,
                                        "media_file_type": attachmentdetails.media_file_type,
                                        "path": attachmentdetails.path,
                                    }
                                )
                    following = (
                        db.query(FollowUser)
                        .filter(
                            FollowUser.follower_userid == login_user_id,
                            FollowUser.following_userid == nuggets.user_id,
                        )
                        .count()
                    )
                    follow_count = (
                        db.query(FollowUser)
                        .filter(FollowUser.following_userid == nuggets.user_id)
                        .count()
                    )
                    if login_user_id == nuggets.user_id:
                        following = 1
                    result_list.append(
                        {
                            "nugget_id": nuggets.id,
                            "content": str(nuggets.nuggets.content),
                            "metadata": nuggets.nuggets.metadata,
                            "created_date": nuggets.created_date,
                            "user_id": nuggets.user_id,
                            "user_ref_id": nuggets.user.user_ref_id,
                            "type": nuggets.type,
                            "original_user_id": nuggets.nuggets.user.id,
                            "original_user_name": str(
                                nuggets.nuggets.user.display_name
                            ),
                            "original_user_image": str(
                                nuggets.nuggets.user.profile_img
                            ),
                            "user_name": str(nuggets.user.display_name),
                            "user_image": str(nuggets.user.profile_img),
                            "liked": True if nuggets.liked > 0 else False,
                            "following": True if following > 0 else False,
                            "follow_count": int(follow_count),
                            "total_likes": int(total_likes),
                            "total_comments": int(total_comments),
                            "total_media": img_count,
                            "share_type": nuggets.share_type,
                            "media_list": attachments,
                            "is_nugget_owner": 1
                            if nuggets.user_id == login_user_id
                            else 0,
                            "is_master_nugget_owner": 1
                            if nuggets.nuggets.user_id == login_user_id
                            else 0,
                            "shared_with": [],
                        }
                    )
                return {
                    "status": 1,
                    "msg": "Success",
                    "nuggets_count": get_row_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "nuggets_list": result_list,
                }


# 60 Report Nugget Abuse
@router.post("/nuggetabusereport")
async def nuggetabusereport(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
    message: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_id == None:
        return {"status": 0, "msg": "Nugget ID Missing"}
    elif message == None:
        return {"status": 0, "msg": "Message Missing"}
    elif len(message) > 500:
        return {"status": 0, "msg": "Message Length should be less than 500"}

    else:
        access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        login_user_id = 0
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        login_user_id = get_token_details.user_id

        access_check = NuggetAccessCheck(db, login_user_id, nugget_id)
        if not access_check:
            return {"status": 0, "msg": "Unauthorized access"}

        report = (
            db.query(NuggetReport)
            .filter(
                NuggetReport.user_id == login_user_id,
                NuggetReport.nugget_id == nugget_id,
            )
            .first()
        )

        if not report:
            nugget = db.query(Nuggets).filter(Nuggets.id == nugget_id).first()

            if nugget:
                nuggetreport = NuggetReport(
                    user_id=login_user_id,
                    nugget_id=nugget.id,
                    message=message,
                    reported_date=datetime.datetime.utcnow(),
                )
                db.add(nuggetreport)
                db.commit()

                return {
                    "status": 1,
                    "msg": "Thanks for the reporting, we will take the action",
                }
            else:
                return {"status": 0, "msg": "Nugget ID not correct"}
        else:
            return {
                "status": 0,
                "msg": "You have already reported this nugget posting.",
            }


# 61. Read Message
@router.post("/messageread")
async def messageread(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    senderid: str = Form(None),
    receiverid: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif senderid == None:
        return {"status": 0, "msg": "Sender ID Missing"}
    elif receiverid == None:
        return {"status": 0, "msg": "Receiver ID Missing"}
    else:
        access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        login_user_id = 0
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        login_user_id = get_token_details.user_id

        report = (
            db.query(FriendsChat)
            .filter(
                FriendsChat.sender_id == senderid,
                FriendsChat.receiver_id == receiverid,
                FriendsChat.is_read == 0,
            )
            .update({"is_read": 1, "read_datetime": datetime.datetime.utcnow()})
        )
        db.commit()

        if report:
            return {"status": 1, "msg": "Success"}
        else:
            return {"status": 0, "msg": "Failed"}


#   62.Event Join Validation
@router.post("/eventjoinvalidation")
async def eventjoinvalidation(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    eventid: str = Form(None),
    emailid: str = Form(None),
    name: str = Form(None),
):
    if token == None or token.strip() == "":
        return {"status": 0, "msg": "Token Missing"}
    if eventid == None:
        return {"status": 0, "msg": "Event ID Missing"}
    elif emailid == None:
        return {"status": 0, "msg": "Email ID Missing"}
    elif name == None:
        return {"status": 0, "msg": "Name Missing"}
    else:
        userid = 0

        result_list = {}

        userdetails = (
            db.query(User).filter(User.email_id == emailid, User.status == 1).first()
        )
        if userdetails:
            userid = userdetails.id
        else:
            access_token = 0
            access_token = checkToken(db, token)
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).all()
            )
            for res in get_token_details:
                userid = res.user_id

            userdetails = (
                db.query(User).filter(User.id == userid, User.status == 1).first()
            )
            if userdetails:
                emailid = userdetails.email_id

        if eventid.startswith("http") and urlparse(eventid).scheme:
            url_components = urlparse(eventid)
            if url_components.path:
                param = url_components.path.split("/")
                eventid = param[-1]

        if eventid:
            event = db.query(Events).filter(Events.ref_id == eventid).first()
            if event:
                if (
                    event.event_type_id == 2 or event.event_type_id == 3
                ) and userid == 0:
                    return {"status": 0, "msg": "Please login to join this event."}
                if event.event_type_id == 2:
                    if userid != 0:
                        checksgare = (
                            db.query(EventInvitations)
                            .filter(
                                EventInvitations.event_id == event.id,
                                EventInvitations.type == 3,
                                EventInvitations.invite_mail == emailid,
                            )
                            .first()
                        )
                        if not checksgare:
                            checkusershare = (
                                db.query(EventInvitations)
                                .filter(
                                    EventInvitations.event_id == event.id,
                                    EventInvitations.type == 1,
                                    EventInvitations.invite_mail == userid,
                                )
                                .first()
                            )
                            if not checkusershare:
                                checkgroupsharequery = (
                                    db.query(EventInvitations.group_id)
                                    .join(
                                        FriendGroupMembers,
                                        FriendGroupMembers.group_id
                                        == EventInvitations.group_id,
                                    )
                                    .join(User, User.id == FriendGroupMembers.user_id)
                                    .filter(
                                        EventInvitations.event_id == event.id,
                                        EventInvitations.type == 2,
                                        User.email_id == emailid,
                                    )
                                )
                                checkgroupshare = checkgroupsharequery.all()

                                # check results
                                if not checkgroupshare and userid != event.created_by:
                                    return {
                                        "status": 0,
                                        "msg": "Your are not allowed to join this event. Please contact the Host 1",
                                    }

                    else:
                        checksgare = (
                            db.query(EventInvitations)
                            .filter(
                                EventInvitations.event_id == event.id,
                                EventInvitations.type == 3,
                                EventInvitations.invite_mail == emailid,
                            )
                            .first()
                        )
                        if not checksgare:
                            return {
                                "status": 0,
                                "msg": "Your are not allowed to join this event. Please contact the Host 2",
                            }
                if event.event_type_id == 3:
                    follow = db.query(FollowUser).filter(
                        FollowUser.follower_userid == userid,
                        FollowUser.following_userid == event.created_by,
                    )
                    if not follow and userid != event.created_by:
                        return {
                            "status": 0,
                            "msg": "Your are not allowed to join this event. Please contact the Host",
                        }

                waiting_room = 0
                join_before_host = 0
                sound_notify = 0
                user_screenshare = 0

                settings = (
                    db.query(UserSettings).filter_by(user_id=event.created_by).first()
                )

                if settings:
                    waiting_room = settings.waiting_room
                    join_before_host = settings.join_before_host
                    sound_notify = settings.participant_join_sound
                    user_screenshare = settings.screen_share_status

                default_melody = (
                    db.query(EventMelody)
                    .filter(EventMelody.id == event.event_melody_id)
                    .first()
                )
                melody = {}
                if default_melody:
                    melody = {
                        "path": default_melody.path,
                        "type": default_melody.type,
                        "is_default": default_melody.event_id is None,
                    }
                # Default AVs
                get_event_default_avs = (
                    db.query(EventDefaultAv)
                    .filter(EventDefaultAv.event_id == event.id)
                    .order_by(EventDefaultAv.id.desc())
                    .first()
                )

                result_list.update(
                    {
                        "event_id": event.id,
                        "event_name": event.title,
                        "reference_id": event.ref_id,
                        "type": event.type,
                        "event_type_id": event.event_type_id,
                        "event_layout_id": event.event_layout_id,
                        "message": event.description,
                        "start_date_time": event.start_date_time,
                        "start_date": datetime.strptime(
                            str(event.start_date_time), "%Y-%m-%d %H:%M:%S"
                        ).strftime("%b %d"),
                        "start_time": datetime.strptime(
                            str(event.start_date_time), "%Y-%m-%d %H:%M:%S"
                        ).strftime("%I:%M %p"),
                        "duration": event.duration,
                        "no_of_participants": event.no_of_participants,
                        "banner_image": event.cover_img,
                        "is_host": 1 if userid == event.created_by else 0,
                        "created_at": datetime.strptime(
                            str(event.created_at), "%Y-%m-%d %H:%M:%S"
                        ).strftime("%Y-%m-%d %I:%M %p"),
                        "original_user_name": event.user.display_name,
                        "original_user_id": event.user.id,
                        "original_user_image": event.user.profile_img,
                        "waiting_room": event.waiting_room
                        if event.waiting_room == 1 or event.waiting_room == 0
                        else waiting_room,
                        "join_before_host": event.join_before_host
                        if event.join_before_host == 1 or event.join_before_host == 0
                        else join_before_host,
                        "sound_notify": event.sound_notify
                        if event.sound_notify == 1 or event.sound_notify == 0
                        else sound_notify,
                        "user_screenshare": event.user_screenshare
                        if event.user_screenshare == 1 or event.user_screenshare == 0
                        else user_screenshare,
                        "melodies": melody,
                        "default_host_audio": (
                            True if get_event_default_avs.default_host_audio else False
                        )
                        if get_event_default_avs
                        else False,
                        "default_host_video": (
                            True if get_event_default_avs.default_host_video else False
                        )
                        if get_event_default_avs
                        else False,
                        "default_guest_audio": (
                            True if get_event_default_avs.default_guest_audio else False
                        )
                        if get_event_default_avs
                        else False,
                        "default_guest_video": (
                            True if get_event_default_avs.default_guest_video else False
                        )
                        if get_event_default_avs
                        else False,
                    }
                )

                userdetail = {}

                if userid != 0:
                    userdetail.update(
                        {
                            "id": userid,
                            "email": userdetails.email_id,
                            "name": userdetails.display_name,
                            "profile_image": userdetails.profile_img,
                            "user_status_type": userdetails.user_status_id,
                        }
                    )

                else:
                    userdetail.update(
                        {
                            "id": random.randint(100, 999),
                            "email": emailid,
                            "name": name,
                            "profile_image": defaultimage("profile_img"),
                            "user_status_type": 1,
                        }
                    )

                return {
                    "status": 1,
                    "msg": "Success",
                    "event": result_list,
                    "user": userdetail,
                }

            return {"status": 0, "msg": "Event ID Not Correct"}

        return {"status": 0, "msg": "Event ID Missing"}


# 63. Get Event Details
@router.post("/geteventdetails")
async def geteventdetails(
    db: Session = Depends(deps.get_db), eventid: str = Form(None)
):
    # Event Id - ref_id
    if eventid == None:
        return {"status": 0, "msg": "Event ID Missing"}

    result_list = {}

    event = (
        db.query(Events)
        .filter(Events.ref_id == eventid, Events.event_type_id == 1)
        .first()
    )
    if event:
        result_list.update(
            {
                "event_name": event.title if event.title else "",
                "reference_id": event.ref_id if event.ref_id else "",
                "chime_meeting_id":event.chime_meeting_id if event.chime_meeting_id else "",
                "message": event.description if event.description else "",
                "start_date_time": common_date(event.start_date_time)
                if event.start_date_time
                else "",
                "start_date": event.start_date_time.strftime("%b %d"),
                "start_time": event.start_date_time.strftime("%I:%M %p"),
                "duration": event.duration if event.duration else "",
                "no_of_participants": event.no_of_participants
                if event.no_of_participants
                else 0,
                "banner_image": event.cover_img if event.cover_img else "",
                "original_user_name": event.user.display_name
                if event.created_by
                else "",
                "original_user_image": event.user.profile_img
                if event.created_by
                else "",
            }
        )

        return {"status": 1, "msg": "Success", "event": result_list}

    else:
        return {"status": 0, "msg": "Event ID Not Correct"}


# 64 Get All TimeZone
@router.post("/gettimezone")
async def gettimezone(db: Session = Depends(deps.get_db)):
    def action_get_timezone():
        abbr = pytz.all_timezones
        timezones_dont_want_to_display = [
            "CET",
            "EET",
            "EST",
            "GB",
            "GMT",
            "HST",
            "MET",
            "MST",
            "NZ",
            "PRC",
            "ROC",
            "ROK",
            "UCT",
            "UTC",
            "WET",
        ]
        options = {}

        for timezone_id in abbr:
            if timezone_id == "Canada/East-Saskatchewan":
                continue

            offset = get_offset_of_time_zone(timezone_id)
            options[timezone_id] = f"{timezone_id} ({offset})"

        options = dict(sorted(options.items()))

        for key in list(options.keys()):
            if key in timezones_dont_want_to_display:
                del options[key]

        optionArr = [
            {"id": i + 1, "name": val} for i, val in enumerate(options.values())
        ]
        reply = {"status": 1, "msg": "success", "timezone_list": optionArr}
        return reply

    def get_offset_of_time_zone(timezone_id):
        now = datetime.datetime.now(pytz.timezone(timezone_id))
        offset = now.strftime("%z")
        return offset

    result = action_get_timezone()

    return result

    # timezones_dont_want_to_display = ['CET', 'EET', 'EST', 'GB', 'GMT', 'HST', 'MET', 'MST', 'NZ', 'PRC', 'ROC', 'ROK', 'UCT', 'UTC', 'WET']
    # options = {}
    # for tz in pytz.all_timezones:
    #     if tz in timezones_dont_want_to_display or tz == 'Canada/East-Saskatchewan':
    #         continue
    #     timezone = pytz.timezone(tz)
    #     offset = datetime.datetime.now(timezone).strftime('%z')
    #     options[tz] = f"{tz} ({offset})"
    # sorted_options = sorted(options.items(), key=lambda x: x[1])
    # optionArr = []
    # temp = 1
    # for key, val in sorted_options:
    #     optionArr.append({'id': temp, 'name': val})
    #     temp += 1
    # reply = {"status": 1, "msg": "success", "timezone_list": optionArr}
    # return reply


# 65. Get All Language List


@router.post("/getlanguagelist")
async def getlanguagelist(db: Session = Depends(deps.get_db)):
    # Language
    get_language = (
        db.query(Language)
        .filter(Language.status == 1)
        .order_by(Language.name.asc())
        .all()
    )

    result_list = []
    for language in get_language:
        result_list.append(
            {
                "id": language.id,
                "name": language.name
                if language.name and language.name != None
                else "",
            }
        )

    # Read Out Language
    get_readout_language = (
        db.query(ReadOutLanguage)
        .filter(ReadOutLanguage.status == 1)
        .order_by(ReadOutLanguage.language.asc())
        .all()
    )

    read_out_languages = []
    for language in get_readout_language:
        read_out_languages.append(
            {
                "id": language.id,
                "name": language.language if language.language else "",
                "language_code": language.language_code
                if language.language_code
                else "",
            }
        )

    return {
        "status": 1,
        "msg": "success",
        "language_list": result_list,
        "read_out_language_list": read_out_languages,
    }


# 66  Profile Details Display preference update (Only Group)


@router.post("/grouplistupdate")
async def grouplistupdate(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    profile_field_name: str = Form(None),
    groupid: str = Form(None, description="example [1,2,3]"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif profile_field_name == None:
        return {"status": 0, "msg": "Profile Field Name Missing"}
    elif groupid == None:
        return {"status": 0, "msg": "Group ID Missing"}

    else:
        access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        login_user_id = 0
        get_token_details = (
            db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
        )
        login_user_id = get_token_details.user_id
        parameter_id = profile_field_name.strip()
        groupid = ast.literal_eval(groupid) if groupid else None

        if len(groupid) > 1:
            db.query(UserProfileDisplayGroup).filter(
                and_(
                    UserProfileDisplayGroup.profile_id == parameter_id,
                    UserProfileDisplayGroup.user_id == login_user_id,
                )
            ).delete()
            gcount = len(groupid)
            listtype = type
            success = 0
            for gid in groupid:
                new_profile = UserProfileDisplayGroup(
                    user_id=login_user_id,
                    profile_id=parameter_id,
                    groupid=gid,
                    created_date=datetime.datetime.utcnow().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )

                db.add(new_profile)
                db.commit()
                if new_profile:
                    success += 1

            if gcount == success:
                update = db.query(UserSettings).filter(
                    UserSettings.user_id == login_user_id
                )
                setattr(update, parameter_id, listtype)
                db.commit()
                return {"status": 1, "msg": "Success"}
            else:
                db.query(UserProfileDisplayGroup).filter_by(
                    profile_id=parameter_id, user_id=login_user_id
                ).delete()
                db.commit()
                return {"status": 0, "msg": "Failed to update group list"}
        else:
            return {"status": 0, "msg": "Invalid group list"}


# 67. Settings
@router.post("/getsettings")
async def getsettings(db: Session = Depends(deps.get_db), token: str = Form(None)):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    else:
        access_token = checkToken(db, token)

    if access_token == False:
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    else:
        settings = db.query(Settings).filter(Settings.status == 1).all()
        data = []
        for setting in settings:
            data.append({"settings_topic": setting.settings_value})
        return {"status": 1, "msg": "", "data": data}


# 68. Faq
@router.post("/getfaq")
async def getfaq(db: Session = Depends(deps.get_db)):
    faqs = db.query(Faq).filter(Faq.status == 1).all()
    faq_list = []
    for faq in faqs:
        faq_list.append({"id": faq.id, "question": faq.question, "answer": faq.answer})
    return {"status": 1, "msg": "", "data": faq_list}


# 69. open nuggets details
@router.post("/getopennuggetdetail")
async def getopennuggetdetail(
    db: Session = Depends(deps.get_db), nugget_id: str = Form(None)
):
    if nugget_id == None:
        return {"status": 0, "msg": "Nugget id is missing"}
    else:
        check_nuggets = (
            db.query(Nuggets)
            .filter(Nuggets.id == nugget_id, Nuggets.share_type == 1)
            .count()
        )
        if check_nuggets > 0:
            nugget_detail = {}

            # construct the query
            get_nugget = (
                db.query(Nuggets)
                .join(NuggetsMaster, Nuggets.nuggets_id == NuggetsMaster.id)
                .join(
                    NuggetsShareWith,
                    NuggetsShareWith.nuggets_id == Nuggets.id,
                    isouter=True,
                )
                .filter(Nuggets.id == nugget_id)
                .first()
            )

            if get_nugget:
                total_likes = (
                    db.query(NuggetsLikes)
                    .filter(
                        NuggetsLikes.nugget_id == get_nugget.id,
                        NuggetsLikes.status == 1,
                    )
                    .count()
                )
                total_comments = (
                    db.query(NuggetsComments)
                    .filter(
                        NuggetsComments.nugget_id == get_nugget.id,
                        NuggetsComments.status == 1,
                    )
                    .count()
                )

                attachments = []
                get_nugget_attachemnt = db.query(NuggetsAttachment).filter(
                    NuggetsAttachment.nugget_id == get_nugget.nuggets_id
                )
                get_attachemnt = get_nugget_attachemnt.all()
                get_attachemnt_count = get_nugget_attachemnt.count()
                if get_attachemnt:
                    for attch in get_attachemnt:
                        if attch.status == 1:
                            attachments.append(
                                {
                                    "media_id": attch.id,
                                    "media_type": attch.media_type,
                                    "media_file_type": attch.media_file_type,
                                    "path": attch.path,
                                }
                            )

                shared_with = []
                result_list = []

                commentlist = (
                    db.query(NuggetsComments)
                    .join(
                        NuggetsCommentsLikes,
                        NuggetsCommentsLikes.comment_id == NuggetsComments.id,
                        isouter=True,
                    )
                    .filter(
                        NuggetsComments.nugget_id == nugget_id,
                        NuggetsComments.parent_id == None,
                    )
                    .group_by(NuggetsComments.id)
                    .order_by(NuggetsComments.modified_date.asc())
                    .all()
                )

                if commentlist:
                    for comment in commentlist:
                        tot_likes = (
                            db.query(NuggetsCommentsLikes)
                            .filter(NuggetsCommentsLikes.comment_id == comment.id)
                            .count()
                        )

                        total_like = tot_likes

                        result_list.append(
                            {
                                "comment_id": comment.id,
                                "user_id": comment.user_id,
                                "editable": False,
                                "name": comment.user.display_name,
                                "profile_image": comment.user.profile_img,
                                "comment": comment.content,
                                "commented_date": comment.created_date,
                                "liked": True if comment.liked > 0 else False,
                                "like_count": total_like,
                            }
                        )

                nugget_detail.update(
                    {
                        "nugget_id": get_nugget.id,
                        "content": get_nugget.nuggets_master.content,
                        "metadata": get_nugget.nuggets_master._metadata,
                        "created_date": common_date(get_nugget.created_date)
                        if get_nugget.created_date
                        else "",
                        "user_id": get_nugget.user_id if get_nugget.user_id else "",
                        "type": get_nugget.type if get_nugget.type else "",
                        "original_user_image": get_nugget.nuggets_master.user.profile_img,
                        "user_name": get_nugget.user.display_name,
                        "user_image": get_nugget.user.profile_img,
                        "liked": False,
                        "total_likes": total_likes,
                        "total_comments": total_comments,
                        "total_media": get_attachemnt_count,
                        "share_type": get_nugget.share_type
                        if get_nugget.share_type
                        else "",
                        "media_list": attachments,
                        "shared_with": shared_with,
                        "comments": result_list,
                    }
                )

                return {"status": 1, "msg": "success", "nugget_detail": nugget_detail}
            else:
                return {"status": 0, "msg": "Invalid nugget id"}


# 70. Get User Settings
@router.post("/followandunfollow")
async def followandunfollow(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    follow_userid: str = Form(None),
    type: str = Form(None, description="1-Follow,2-unfollow"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if follow_userid == None:
        return {"status": 0, "msg": "ID is Missing"}
    elif type == None:
        return {"status": 0, "msg": "Type is missing"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            type = int(type) if type else None
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_user = db.query(User).filter(User.user_ref_id == follow_userid).first()
            if get_user:
                follow_userid = get_user.id

                get_user_detail = (
                    db.query(User)
                    .filter(User.id == follow_userid, User.status == 1)
                    .first()
                )

                follow_user = (
                    db.query(FollowUser)
                    .filter(
                        FollowUser.follower_userid == login_user_id,
                        FollowUser.following_userid == follow_userid,
                    ).first()
                )

                friend_groups = (
                    db.query(FriendGroups)
                    .filter(
                        FriendGroups.group_name == "My Fans",
                        FriendGroups.created_by == follow_userid,
                    ).first()
                )

                if (type == 1 and get_user_detail and not follow_user and login_user_id != follow_userid):  # Follow
                    add_follow_user = FollowUser(
                        follower_userid=login_user_id,
                        following_userid=follow_userid,
                        created_date=datetime.datetime.utcnow(),
                    )
                    db.add(add_follow_user)
                    db.commit()
                    db.refresh(add_follow_user)
                    
                    if add_follow_user and friend_groups:
        
                        friend_group_member = (
                            db.query(FriendGroupMembers)
                            .filter(
                                FriendGroupMembers.group_id == friend_groups.id,
                                FriendGroupMembers.user_id == follow_userid,
                            )
                            .all()
                        )

                        if not friend_group_member:
                            add_frnd_group = FriendGroupMembers(
                                group_id=friend_groups.id,
                                user_id=login_user_id,
                                added_date=datetime.datetime.utcnow(),
                                added_by=follow_userid,
                                is_admin=0,
                                disable_notification=1,
                                status=1,
                            )
                            db.add(add_frnd_group)
                            db.commit()

                            notification_type = 15
                            add_notification = Insertnotification(
                                db,
                                follow_userid,
                                login_user_id,
                                notification_type,
                                add_frnd_group.id,
                            )

                        # Add Member in Channel
                        channel_arn = (
                            friend_groups.group_arn
                            if friend_groups.group_arn
                            else None
                        )
                        chime_bearer = (
                            friend_groups.user.chime_user_id
                            if friend_groups.user.chime_user_id
                            else None
                        )
                        member_id = (
                            list(add_frnd_group.user.chime_user_id)
                            if add_frnd_group.user.chime_user_id
                            else None
                        )
                        try:
                            addmembers(channel_arn, chime_bearer, member_id)
                        except Exception as e:
                            print(f"Follow:{e}")

                        get_influence_count = croninfluencemember(db, get_user.id)

                        return {
                            "status": 1,
                            "msg": f"Now you are fan of {add_follow_user.user2.display_name}",
                        }
                    else:
                        return {
                            "status": 0,
                            "msg": "Something went wrong.",
                            }
                        

                elif type == 2:
                    if friend_groups:
                        get_friend_group_member = (
                            db.query(FriendGroupMembers)
                            .filter(
                                FriendGroupMembers.group_id == friend_groups.id,
                                FriendGroupMembers.user_id == login_user_id,
                            )
                        )
                        getUserId=get_friend_group_member.first()
                        
                        #  Remove Member in Channel
                        channel_arn = (
                            friend_groups.group_arn if friend_groups.group_arn else None
                        )
                        chime_bearer = (
                            friend_groups.user.chime_user_id
                            if friend_groups.user
                            else None
                        )
                        member_id = (
                            getUserId.user.chime_user_id
                            if getUserId
                            else None
                        )
                        try:
                            delete_channel_membership(
                                channel_arn, chime_bearer, member_id
                            )
                        except Exception as e:
                            print(f"UnFollow:{e}")
                            
                        delFriendGroups=get_friend_group_member.delete()
                        
                        db.commit()  # Remove member in Friend group member table

                    msg = f"{follow_user.user2.display_name if follow_user else ''} not influencing you"
                    get_influence_count = croninfluencemember(db, get_user.id)
                    # notification_type=15
                    # add_notification=Insertnotification(db,follow_userid,login_user_id,notification_type,add_frnd_group.id)

                    del_follow_user = (
                        db.query(FollowUser)
                        .filter(
                            FollowUser.follower_userid == login_user_id,
                            FollowUser.following_userid == follow_userid,
                        )
                        .delete()
                    )
                    db.commit()

                    return {"status": 1, "msg": msg}

                else:
                    return {"status": 0, "msg": "Already requested"}

            else:
                return {"status": 0, "msg": "Invalid Follower"}


# -----------------last 3 parameters check-------------------------#
# 71 Get follower and following list
@router.post("/getfollowlist")
async def getfollowlist(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    user_id: str = Form(None),
    type: str = Form(None, description="1->follower,2->following"),
    search_key: str = Form(None),
    location: str = Form(None),
    gender: str = Form(None),
    age: str = Form(None),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif type == None or not type.isnumeric():
        return {"status": 0, "msg": "Type is missing"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        type = int(type) if type else None
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens)
                .filter(ApiTokens.token == access_token)
                .order_by(ApiTokens.id.desc())
                .first()
            )
            login_user_id = get_token_details.user_id if get_token_details else None

            current_page_no = int(page_number)

            get_follow_user = db.query(FollowUser)

            if type == 1:  # Followers
                if not user_id:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.follower_userid == login_user_id
                    )

                else:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.follower_userid == user_id
                    )

            else:  # Following
                if not user_id:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.following_userid == login_user_id
                    )
                else:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.following_userid == user_id
                    )

            if search_key and search_key.strip() != "":
                get_follow_user = get_follow_user.filter(
                    or_(
                        User.email_id.ilike("%" + search_key + "%"),
                        User.display_name.ilike("%" + search_key + "%"),
                        User.first_name.ilike("%" + search_key + "%"),
                        User.last_name.ilike("%" + search_key + "%"),
                    )
                )
            if location:
                get_user = (
                    db.query(User).filter(User.geo_location.ilike(location + "%")).all()
                )
                user_location_ids = {usr.id for usr in get_user}
                if type == 1:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.following_userid.in_(user_location_ids)
                    )
                if type == 2:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.follower_userid.in_(user_location_ids)
                    )

                # get_follow_user=get_follow_user.filter(or_(or_(FollowUser.following_userid.in_(user_location_ids),FollowUser.follower_userid.in_(user_location_ids)),FollowUser.following_userid.in_(user_location_ids),FollowUser.follower_userid.in_(user_location_ids)))

            if gender:
                gender = int(gender) if gender else None
                get_user_gender = (
                    db.query(User)
                    .filter(User.gender == gender, User.gender != None)
                    .all()
                )
                get_user_ids = [usr.id for usr in get_user_gender]

                if type == 1:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.following_userid.in_(get_user_ids)
                    )
                if type == 2:
                    get_follow_user = get_follow_user.filter(
                        FollowUser.follower_userid.in_(get_user_ids)
                    )

            if age:
                if not age.isnumeric():
                    return {"status": 0, "msg": "Invalid Age"}
                else:
                    current_year = datetime.datetime.utcnow().year
                    get_user = (
                        db.query(User)
                        .filter(current_year - extract("year", User.dob) == age)
                        .all()
                    )
                    user_ages = {usr.id for usr in get_user}

                    if type == 1:
                        get_follow_user = get_follow_user.filter(
                            FollowUser.following_userid.in_(user_ages)
                        )
                    if type == 2:
                        get_follow_user = get_follow_user.filter(
                            FollowUser.follower_userid.in_(user_ages)
                        )

                    # get_follow_user=get_follow_user.filter(or_(or_(FollowUser.following_userid.in_(user_ages),FollowUser.follower_userid.in_(user_ages)),FollowUser.following_userid.in_(user_ages),FollowUser.follower_userid.in_(user_ages)))

            get_row_count = get_follow_user.count()

            if get_row_count < 1:
                return {"status": 0, "msg": "Unable to get Profile"}
            else:
                default_page_size = 50
                limit, offset, total_pages = get_pagination(
                    get_row_count, current_page_no, default_page_size
                )

                get_result = get_follow_user.limit(limit).offset(offset).all()

                result_list = []

                for follow in get_result:
                    if type == 1:
                        followback = (
                            db.query(FollowUser)
                            .filter(
                                FollowUser.follower_userid == login_user_id,
                                FollowUser.following_userid == follow.following_userid,
                            )
                            .first()
                        )

                        friend_details = {
                            "user_id": follow.user2.id if follow.user2.id != "" else "",
                            "user_ref_id": follow.user2.user_ref_id
                            if follow.user2.user_ref_id != ""
                            else "",
                            "email_id": follow.user2.email_id
                            if follow.user2.email_id != ""
                            else "",
                            "first_name": follow.user2.first_name
                            if follow.user2.first_name != ""
                            else "",
                            "last_name": follow.user2.last_name
                            if follow.user2.last_name != ""
                            else "",
                            "display_name": follow.user2.display_name
                            if follow.user2.display_name != ""
                            else "",
                            "gender": follow.user2.gender
                            if follow.user2.gender != ""
                            else "",
                            "profile_img": follow.user2.profile_img
                            if follow.user2.profile_img != ""
                            else "",
                            "online": ProfilePreference(
                                db,
                                login_user_id,
                                follow.user2.id,
                                "online_status",
                                follow.user2.online,
                            ),
                            "last_seen": (
                                common_date(follow.user2.last_seen)
                                if follow.user2.last_seen
                                else ""
                            )
                            if follow.user2.last_seen != ""
                            else "",
                            "follow": True if followback else False,
                        }
                    else:
                        followback = (
                            db.query(FollowUser)
                            .filter(
                                FollowUser.following_userid == login_user_id,
                                FollowUser.follower_userid == follow.follower_userid,
                            )
                            .first()
                        )
                        follow_count = (
                            db.query(FollowUser)
                            .filter(FollowUser.following_userid == follow.user1.id)
                            .count()
                        )

                        friend_details = {
                            "user_id": follow.user1.id if follow.user1.id != "" else "",
                            "user_ref_id": follow.user1.user_ref_id
                            if follow.user1.user_ref_id != ""
                            else "",
                            "email_id": follow.user1.email_id
                            if follow.user1.email_id != ""
                            else "",
                            "first_name": follow.user1.first_name
                            if follow.user1.first_name != ""
                            else "",
                            "last_name": follow.user1.last_name
                            if follow.user1.last_name != ""
                            else "",
                            "display_name": follow.user1.display_name
                            if follow.user1.display_name != ""
                            else "",
                            "gender": follow.user1.gender
                            if follow.user1.gender != ""
                            else "",
                            "profile_img": follow.user1.profile_img
                            if follow.user1.profile_img != ""
                            else "",
                            "online": ProfilePreference(
                                db,
                                login_user_id,
                                follow.user1.id,
                                "online_status",
                                follow.user1.online,
                            ),
                            "last_seen": (
                                (
                                    common_date(follow.user1.last_seen)
                                    if follow.user1.last_seen
                                    else ""
                                )
                                if follow.user1.last_seen
                                else ""
                            )
                            if follow.user1.last_seen != ""
                            else "",
                            "follow": True if followback else False,
                            "follow_count": follow_count,
                        }

                    result_list.append(friend_details)

                return {
                    "status": 1,
                    "msg": "Success",
                    "follow_count": get_row_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "follow_list": result_list,
                }


# 72. Add nuggets view count
@router.post("/addnuggetview")
async def addnuggetview(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None, description="[1,2,3]"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if not nugget_id:
        return {"status": 0, "msg": "Nugget id is missing"}
    # elif not nugget_id.isnumeric():
    #     return {"status":0,"msg":"Invalid Nugget id type"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).all()
            )
            for res in get_token_details:
                login_user_id = res.user_id

            nugget_ids = ast.literal_eval(nugget_id) if nugget_id else None
            for nugget_id in nugget_ids:
                nugget_id = int(nugget_id) if int(nugget_id) > 0 else ""

                access_check = NuggetAccessCheck(db, login_user_id, nugget_id)
                if not access_check:
                    return {"status": 0, "msg": "Unauthorized access"}

                model = NuggetView(
                    user_id=login_user_id,
                    nugget_id=nugget_id,
                    created_date=datetime.datetime.utcnow(),
                )
                db.add(model)
                db.commit()
                nuggets = db.query(Nuggets).filter(Nuggets.id == nugget_id).first()
                if nuggets:
                    nuggets.total_view_count = nuggets.total_view_count + 1
                    db.commit()
                    return {"status": 1, "msg": "Success"}
                else:
                    return {"status": 0, "msg": "Invalid nugget"}


# 73. Get Referral List


@router.post("/getreferrallist")
async def getreferrallist(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            referral_count = 0
            referral_need_count = 0

            get_referrer = db.query(User).filter(User.id == login_user_id).first()
            if get_referrer:
                referral_count = get_referrer.total_referral_point

                if get_referrer.user_status_id == 1:
                    get_user_status = (
                        db.query(UserStatusMaster)
                        .filter(UserStatusMaster.id == 3)
                        .first()
                    )
                    referral_need_count = (
                        get_user_status.referral_needed - referral_count
                        if get_user_status
                        else 0
                    )

            current_page_no = int(page_number)

            get_user = db.query(User).filter(User.referrer_id == login_user_id)
            get_user_count = get_user.count()
            if get_user_count < 1:
                return {
                    "status": 1,
                    "msg": "No Result found",
                    "referral_count": referral_count,
                    "referral_needed_count": referral_need_count,
                    "current_page_no": 1,
                }
            else:
                default_page_size = 50

                limit, offset, total_pages = get_pagination(
                    get_user_count, current_page_no, default_page_size
                )

                get_user = get_user.limit(limit).offset(offset).all()

                result_list = []

                for user in get_user:
                    result_list.append(
                        {
                            "user_id": user.id if user.id else "",
                            "user_ref_id": user.user_ref_id if user.user_ref_id else "",
                            "email_id": user.email_id if user.email_id else "",
                            "first_name": user.first_name if user.first_name else "",
                            "last_name": user.last_name if user.last_name else "",
                            "display_name": user.display_name
                            if user.display_name
                            else "",
                            "profile_img": user.profile_img if user.profile_img else "",
                            "invited_date": user.invited_date
                            if user.invited_date
                            else "",
                            "signedup_date": user.created_at if user.created_at else "",
                            "account_verified": user.is_email_id_verified
                            if user.is_email_id_verified
                            else "",
                        }
                    )

                return {
                    "status": 1,
                    "msg": "Success",
                    "referral_count": referral_count,
                    "referral_needed_count": referral_need_count,
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "referral_list": result_list,
                }


# 74. Create Live Event


@router.post("/addliveevent")
async def addliveevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_title: str = Form(None),
    event_type: str = Form(None, description="1-Event, 2-Talkshow,3-Live"),
    event_start_date: Any = Form(None),
    event_start_time: Any = Form(None),
    event_banner: UploadFile = File(None),
    event_invite_mails: str = Form(
        None, description="example abc@mail.com,xyz@gmail.com"
    ),
    event_invite_groups: str = Form(None, description="example [14,27,32]"),
    event_invite_friends: str = Form(None, description="example [5,7,3]"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif event_type == None or not event_type.isnumeric():
        return {"status": 0, "msg": "Event type is missing"}

    # elif event_banner == None:
    #     return {"status":0,"msg":"Event Banner is missing"}

    elif event_start_date and is_date(event_start_date) == False:
        return {"status": 0, "msg": "Invalid Date"}

    elif event_start_time and isTimeFormat(event_start_time) == False:
        return {"status": 0, "msg": "Invalid Time format"}

    else:
        event_type = int(event_type)
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            event_title = (
                detect_and_remove_offensive(event_title)
                if event_title and event_title != None or event_title.strip() != ""
                else None
            )
            event_type = event_type if event_type and event_type > 0 else None
            event_start_date = event_start_date if event_start_date else None
            event_start_time = event_start_time if event_start_time else None

            event_invite_custom= json.loads(event_invite_mails) if event_invite_mails else None
            
            # event_invite_custom = (
            #     event_invite_mails
            #     if event_invite_mails and event_invite_mails.strip() != ""
            #     else None
            # )

            # if event_invite_custom:
                
            #     event_invite_custom = (
            #         ast.literal_eval(event_invite_custom)
            #         if event_invite_custom
            #         else None
            #     )
            event_invite_groups=json.loads(event_invite_groups) if event_invite_groups else None
            # event_invite_groups = (
            #     event_invite_groups
            #     if event_invite_groups and event_invite_groups.strip() != ""
            #     else None
            # )
            # if event_invite_groups:
            #     event_invite_groups = (
            #         ast.literal_eval(event_invite_groups)
            #         if event_invite_groups
            #         else None
            #     )
            event_invite_friends=json.loads(event_invite_friends) if event_invite_friends else None
            # event_invite_friends = (
            #     event_invite_friends
            #     if event_invite_friends and event_invite_friends.strip() != ""
            #     else None
            # )
            # if event_invite_friends:
            #     event_invite_friends = (
            #         json.loads(event_invite_friends) if event_invite_friends else []
            #     )

            if not event_title:
                return {"status": 0, "msg": "Live event title cant be blank."}

            elif not event_type:
                return {"status": 0, "msg": "Live event type cant be blank."}

            elif not event_start_date:
                return {"status": 0, "msg": "Live event start date cant be blank."}

            elif not event_start_time:
                return {"status": 0, "msg": "Live event start time cant be blank."}

            else:
                setting = (
                    db.query(UserSettings)
                    .filter(UserSettings.user_id == login_user_id)
                    .first()
                )
                
                img_flag = "talkshow" 
                cover_img = defaultimage(img_flag)

                if setting and setting.talkshow_event_banner != None:
                    cover_img = setting.talkshow_event_banner

                server_id = None
                server = (
                    db.query(KurentoServers)
                    .filter(KurentoServers.status == 1)
                    .order_by(func.random())
                    .limit(1)
                    .first()
                )

                if server:
                    server_id = server.server_id

                user = db.query(User).filter(User.id == login_user_id).first()
                userstatus = (
                    db.query(UserStatusMaster)
                    .filter(UserStatusMaster.id == user.user_status_id)
                    .first()
                )

                duration = userstatus.max_event_duration * 3600
                duration = (
                    datetime.datetime.min + timedelta(seconds=duration)
                ).strftime("%H:%M:%S")

                reference_id = f"RC{str(random.randint(1, 499))}{str(int(datetime.datetime.utcnow().timestamp()))}"

                # Create Meeting (Chime API Call)
                chime_meeting_id=None
                try:
                    user_id=login_user_id
                   
                    data={'joinApprovalRequired': False,'allowOtherToShareScreen':False,'userId':user_id}
                    headers = {'Content-Type': 'application/json'}
                    url='https://devchimeapi.rawcaster.com/createmeeting'
                    
                    chime_meeting_response = requests.post(url, data = json.dumps(data),headers=headers)
                    
                    if chime_meeting_response.status_code == 200:
                        response=json.loads(chime_meeting_response.text)
                        chime_meeting_id=response['result']['Meeting']['MeetingId'] if response['status'] == 200 else None
                    
                except Exception as e:
                    print(e)
                    return {"status":0,"msg":"Something went wrong"}
                
                new_event = Events(
                    title=event_title,
                    type=2,
                    ref_id=reference_id,
                    chime_meeting_id=chime_meeting_id,
                    server_id=server_id if server_id else None,
                    event_type_id=event_type,
                    event_layout_id=1,
                    duration=duration,
                    created_at=datetime.datetime.utcnow(),
                    created_by=login_user_id,
                    cover_img=cover_img,
                    start_date_time=str(event_start_date) + " " + str(event_start_time),
                )

                db.add(new_event)
                db.commit()
                if new_event:
                    totalfriend = []

                    if event_type == 1:
                        totalfriends = get_friend_requests(
                            db,
                            login_user_id,
                            requested_by=None,
                            request_status=1,
                            response_type=1,
                        )
                        totalfriend = totalfriend + totalfriends["accepted"]

                    if event_banner:
                        file_name = event_banner.filename
                        file_temp = event_banner.content_type
                        file_read = await event_banner.read()
                        file_size = len(file_read)
                        file_ext = os.path.splitext(event_banner.filename)[1]

                        type = "image"
                        if "video" in file_temp:
                            type = "video"

                        if file_size > 1024 and type == "image" and file_ext != ".gif":
                            s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path = await read_file_upload(
                                file_read, file_ext, compress=1
                            )

                            result = upload_to_s3(uploaded_file_path, s3_path)
                            if result["status"] == 1:
                                new_event.cover_img = result["url"]
                                db.commit()

                            else:
                                return result
                        else:
                            s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                            uploaded_file_path = await read_file_upload(
                                file_read, file_ext, compress=None
                            )

                            result = upload_to_s3(uploaded_file_path, s3_path)
                            # Upload to S3
                            if result["status"] == 1:
                                new_event.cover_img = result["url"]
                                db.commit()
                            else:
                                return result

                    if event_invite_friends:
                        for value in event_invite_friends:
                            invite_friends = EventInvitations(
                                type=1,
                                event_id=new_event.id,
                                user_id=value,
                                invite_sent=0,
                                created_at=datetime.datetime.utcnow(),
                                created_by=login_user_id,
                            )
                            db.add(invite_friends)
                            db.commit()
                            if value not in totalfriend:
                                totalfriend.append(value)

                    if event_invite_groups:
                        for value in event_invite_groups:
                            invite_groups = EventInvitations(
                                type=2,
                                event_id=new_event.id,
                                group_id=value,
                                invite_sent=0,
                                created_at=datetime.datetime.utcnow(),
                                created_by=login_user_id,
                            )

                            db.add(invite_groups)
                            db.commit()

                            get_group_member = (
                                db.query(FriendGroupMembers)
                                .filter_by(group_id=value)
                                .all()
                            )
                            if get_group_member:
                                for member in get_group_member:
                                    if member.user_id not in totalfriend:
                                        totalfriend.append(member.user_id)

                    invite_url = inviteBaseurl()
                    link = f"{invite_url}join/event/{reference_id}"
                    subject = "Rawcaster - Talkshow Invitation"
                    body = ""
                    sms_message = ""

                    if new_event.id:  # Created Event
                        sms_message, body = eventPostNotifcationEmail(db, new_event.id)

                    if event_invite_custom and event_invite_custom != "":
                        for (
                            value
                        ) in (
                            event_invite_custom
                        ):  # check if e-mail address is well-formed
                            if check_mail(value) == True:
                                invite_custom = EventInvitations(
                                    type=3,
                                    event_id=new_event.id,
                                    invite_mail=value,
                                    invite_sent=0,
                                    created_at=datetime.datetime.utcnow(),
                                    created_by=login_user_id,
                                )
                                db.add(invite_custom)
                                db.commit()
                                to = value

                                if invite_custom:
                                    try:
                                        send_mail = await send_email(
                                            db, to, subject, body
                                        )
                                    except:
                                        pass

                    event = get_event_detail(db, new_event.id, login_user_id)
                    message_detail = {}
                    email_detail = {}
                    if totalfriend:
                        for users in totalfriend:
                            Insertnotification(
                                db, users, login_user_id, 13, new_event.id
                            )

                        message_detail.update(
                            {
                                "message": "Posted new talkshow",
                                "data": {"refer_id": new_event.id, "type": "add_event"},
                                "type": "events",
                            }
                        )

                        push_notification = pushNotify(
                            db, totalfriend, message_detail, login_user_id
                        )

                        email_detail.update(
                            {
                                "subject": subject,
                                "mail_message": body,
                                "sms_message": sms_message,
                                "type": "events",
                            }
                        )

                        addNotificationSmsEmail(
                            db, totalfriend, email_detail, login_user_id
                        )

                    return {
                        "status": 1,
                        "msg": "Event saved successfully !",
                        "ref_id": reference_id,
                        "event_detail": event,
                    }
                else:
                    return {"status": 0, "msg": "Event cant be created."}


# 75.Edit Live Event
@router.post("/editliveevent")
async def editliveevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_id: str = Form(None),
    event_title: str = Form(None),
    event_type: str = Form(None),
    event_start_date: Any = Form(None),
    event_start_time: Any = Form(None),
    event_banner: UploadFile = File(None),
    event_invite_mails: str = Form(
        None, description="Example abc@mail.com,def@mail.com"
    ),
    event_invite_groups: str = Form(None, description="Example 1,2,3"),
    event_invite_friends: str = Form(None, description="Example 1,2,3"),
    delete_invite_mails: str = Form(
        None, description=" Example abc@mail.com,def@mail.com"
    ),
    delete_invite_groups: str = Form(None, description="Example 1,2,3"),
    delete_invite_friends: str = Form(None, description="Example 2,3,4"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif event_title == None or event_title.strip() == "":
        return {"status": 0, "msg": "Event Title cant be blank"}
    elif not event_start_date:
        return {"status": 0, "msg": "Event start date is missing"}
    elif not event_start_time:
        return {"status": 0, "msg": "Event start time is missing"}
    elif not event_id:
        return {"status": 0, "msg": "Event ID cant be blank"}
    elif not event_id.isnumeric():
        return {"status": 0, "msg": "Invalid Event id "}
    elif event_start_date and is_date(event_start_date) == False:
        return {"status": 0, "msg": "Invalid Date"}
    elif event_start_time and isTimeFormat(event_start_time) == False:
        return {"status": 0, "msg": "Invalid Time format"}
    elif event_type and not event_type.isnumeric():
        return {"status": 0, "msg": "Invalid Event Type"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"

            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            event_id = int(event_id) if event_id else None
            event_title = (
                detect_and_remove_offensive(event_title)
                if event_title and event_title.strip() != "" or event_title != None
                else None
            )
            event_type = int(event_type) if event_type else None
            event_start_date = event_start_date if event_start_date else None
            event_start_time = event_start_time if event_start_time else None
            
            event_invite_custom=json.loads(event_invite_mails) if event_invite_mails else None
            # event_invite_custom = (
            #     ast.literal_eval(event_invite_mails) if event_invite_mails else None
            # )
            event_invite_groups=json.loads(event_invite_groups) if event_invite_groups else None
            # event_invite_groups = (
            #     ast.literal_eval(event_invite_groups) if event_invite_groups else None
            # )
            event_invite_friends=json.loads(event_invite_friends) if event_invite_friends else None
            # event_invite_friends = (
            #     ast.literal_eval(event_invite_friends) if event_invite_friends else None
            # )
            delete_invite_custom=json.loads(delete_invite_mails) if delete_invite_mails else None
            # delete_invite_custom = (
            #     ast.literal_eval(delete_invite_mails) if delete_invite_mails else None
            # )
            delete_invite_groups=json.loads(delete_invite_groups) if delete_invite_groups else None
            # delete_invite_groups = (
            #     ast.literal_eval(delete_invite_groups) if delete_invite_groups else None
            # )
            delete_invite_friends=json.loads(delete_invite_friends) if delete_invite_friends else None
            # delete_invite_friends = (
            #     ast.literal_eval(delete_invite_friends) if delete_invite_friends else None
            # )

            event_exist = (
                db.query(Events)
                .filter(Events.id == event_id, Events.created_by == login_user_id)
                .count()
            )
            if event_exist == 0:
                return {"status": 0, "msg": "Invalid Event ID."}
            elif event_title.strip() == "" or event_title == None:
                return {"status": 0, "msg": "Event title cant be blank."}
            else:
                if delete_invite_friends:
                    db.query(EventInvitations).filter(
                        and_(
                            EventInvitations.event_id == event_id,
                            EventInvitations.user_id.in_(delete_invite_friends),
                        )
                    ).delete()
                    db.commit()
                if delete_invite_groups:
                    
                    db.query(EventInvitations).filter(
                        and_(
                            EventInvitations.event_id == event_id,
                            EventInvitations.group_id.in_(delete_invite_groups),
                        )
                    ).delete()
                    db.commit()
                if delete_invite_custom:
                    
                    deleteUser=db.query(EventInvitations).filter(
                        and_(
                            EventInvitations.event_id == event_id,
                            EventInvitations.invite_mail.in_(delete_invite_custom),
                        )
                    ).delete()
                    db.commit()
                if event_type == 3:
                    db.query(EventInvitations).filter(
                        EventInvitations.event_id == event_id
                    ).delete()
                    db.commit()

                user = db.query(User).filter(User.id == login_user_id).first()
                hostname = user.display_name

                is_event_changed = 0
                edit_event = db.query(Events).filter(Events.id == event_id).first()

                old_start_datetime = edit_event.start_date_time
                edit_event.title = event_title
                edit_event.event_type_id = event_type
                edit_event.start_date_time = (
                    str(event_start_date) + " " + str(event_start_time)
                )

                db.commit()
                totalfriend = []

                if event_type == 1:
                    totalfriends = get_friend_requests(
                        db,
                        login_user_id,
                        requested_by=None,
                        request_status=1,
                        response_type=1,
                    )
                    totalfriend = totalfriend + totalfriends["accepted"]

                if old_start_datetime != edit_event.start_date_time:
                    is_event_changed = 1

                # Upload Banner Image
                if event_banner:
                    file_name = event_banner.filename
                    file_temp = event_banner.content_type
                    file_read = await event_banner.read()
                    file_size = len(file_read)
                    file_ext = os.path.splitext(event_banner.filename)[1]

                    type = "image"
                    if "video" in file_temp:
                        type = "video"

                    if file_size > 1024 and type == "image" and file_ext != ".gif":
                        # Compress Image
                        compress = 1
                        uploaded_file_path = await read_file_upload(
                            file_read, file_ext, compress
                        )

                        s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                        # Upload to S3
                        result = upload_to_s3(uploaded_file_path, s3_path)
                        if result["status"] == 1:
                            edit_event.cover_img = result["url"]
                            db.commit()

                        else:
                            return result
                    else:
                        compress = None
                        uploaded_file_path = await read_file_upload(
                            file_read, file_ext, compress
                        )

                        s3_path = f"events/image_{random.randint(11111,99999)}{int(datetime.datetime.utcnow().timestamp())}{file_ext}"
                        result = upload_to_s3(uploaded_file_path, s3_path)
                        if result["status"] == 1:
                            edit_event.cover_img = result["url"]
                            db.commit()
                        else:
                            return result

                if is_event_changed == 1:
                    db.query(EventInvitations).filter(
                        EventInvitations.event_id == event_id
                    ).update({"is_changed": 1})
                    db.commit()
                if event_invite_friends and len(event_invite_friends) > 0:
                    for value in event_invite_friends:
                        checkEventFriends=db.query(EventInvitations).filter(EventInvitations.event_id == event_id,EventInvitations.user_id == int(value)).first()
                        if not checkEventFriends:
                            
                            invite_friends = EventInvitations(
                                type=1,
                                event_id=event_id,
                                user_id=int(value),
                                invite_sent=0,
                                created_at=datetime.datetime.utcnow().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                created_by=login_user_id,
                            )
                            db.add(invite_friends)
                            db.commit()
                            if value not in totalfriend:
                                totalfriend.append(value)

                if event_invite_groups:
                    for value in event_invite_groups:
                        # check event group
                        checkEventGroup=db.query(EventInvitations).filter(EventInvitations.event_id == event_id,EventInvitations.group_id == int(value)).first()
                        if not checkEventGroup:
                            invite_friends = EventInvitations(
                                type=2,
                                event_id=event_id,
                                group_id=int(value),
                                invite_sent=0,
                                created_at=datetime.datetime.utcnow().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                created_by=login_user_id,
                            )
                            db.add(invite_friends)
                            db.commit()

                            getgroupmember = (
                                db.query(FriendGroupMembers)
                                .filter(FriendGroupMembers.group_id == int(value))
                                .all()
                            )
                            if getgroupmember:
                                for member in getgroupmember:
                                    if member.user_id not in totalfriend:
                                        totalfriend.append(member.user_id)

                link = inviteBaseurl() + "" + "join/talkshow/" + edit_event.ref_id
                subject = "Rawcaster - Event Invitation"
                content = f"""
                    Hi, greetings from Rawcaster.com.<br /><br/>
                    You have been invited by {hostname} to a talkshow titled {event_title}.<br/><br/>
                    Use the following link to join the Rawcaster talkshow.<br/>{link}<br/><br/>
                    Regards,<br />Administration Team<br /><a href="https://rawcaster.com/">Rawcaster.com</a> LLC
                """
                body = event_mail_template(content)

                if event_invite_custom and len(event_invite_custom) > 0:
                    for value in event_invite_custom:
                        # check exist mail
                        check_mail=db.query(EventInvitations).filter(EventInvitations.event_id == event_id,EventInvitations.invite_mail.like(value)).first()
                        if not check_mail:
                            if value.strip() != "":
                                invite_friends = EventInvitations(
                                    type=3,
                                    event_id=event_id,
                                    invite_mail=value,
                                    invite_sent=0,
                                    created_at=datetime.datetime.utcnow().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                    created_by=login_user_id,
                                )
                                db.add(invite_friends)
                                db.commit()
                                to = value
                                try:
                                    send_mail = await send_email(db, to, subject, body)
                                except:
                                    pass

                event = get_event_detail(db, event_id, login_user_id)
                message_detail = []
                if totalfriend and totalfriend != []:
                    for users in totalfriend:
                        add_notitication = Insertnotification(
                            db, users, login_user_id, 10, edit_event.id
                        )

                    message_detail = {
                        "message": "Updated the Event",
                        "data": {"refer_id": edit_event.id, "type": "edit_event"},
                        "type": "events",
                    }
                    pushNotify(db, totalfriend, message_detail, login_user_id)

                    sms_message = f"""
                                Hi,greetings from Rawcaster.com.
                                You have been invited by {hostname} to an event titled {event_title}.
                                Use the following link to join the Rawcaster event. {link}"""
                    email_detail = {
                        "subject": subject,
                        "mail_message": body,
                        "sms_message": sms_message,
                        "type": "events",
                    }
                    addNotificationSmsEmail(
                        db, totalfriend, email_detail, login_user_id
                    )
                return {
                    "status": 1,
                    "msg": "Event Updated successfully !",
                    "ref_id": edit_event.ref_id,
                    "event_detail": event,
                }


# 76. Add Go Live Event


@router.post("/addgoliveevent")
async def addgoliveevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_title: str = Form(None),
    event_type: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif event_title == None or event_title.strip() == "":
        return {"status": 0, "msg": "Go live event title cant be blank."}
    elif event_type == None:
        return {"status": 0, "msg": "Go live event type cant be blank."}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            if event_title.strip() == "":
                return {"status": 0, "msg": "Go live event title can't be blank."}

            else:
                setting = (
                    db.query(UserSettings)
                    .filter(UserSettings.user_id == login_user_id)
                    .first()
                )
                img_type = "live"
                cover_img = defaultimage(img_type)

                if setting and setting.meeting_header_image != None:
                    cover_img = setting.meeting_header_image

                server_id = None
                server = (
                    db.query(KurentoServers)
                    .filter(KurentoServers.status == 1)
                    .limit(1)
                    .first()
                )

                if server:
                    server_id = server.server_id

                user = db.query(User).filter(User.id == login_user_id).first()
                userstatus = (
                    db.query(UserStatusMaster)
                    .filter(UserStatusMaster.id == user.user_status_id)
                    .first()
                )

                duration = (
                    timedelta(seconds=userstatus.max_event_duration * 3600)
                    if userstatus.max_event_duration
                    else 1 * 3600
                )
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours}:{minutes}:{seconds}"

                reference_id = f"RC{random.randint(1,499)}{int(datetime.datetime.utcnow().timestamp())}"

                new_event = Events(
                    title=event_title,
                    type=3,
                    ref_id=reference_id,
                    server_id=server_id,
                    event_type_id=event_type,
                    event_layout_id=1,
                    duration=duration,
                    start_date_time=datetime.datetime.utcnow(),
                    created_at=datetime.datetime.utcnow(),
                    created_by=login_user_id,
                    cover_img=cover_img,
                    status=0,
                )
                db.add(new_event)
                db.commit()
                if new_event:
                    event = get_event_detail(db, new_event.id, login_user_id)
                    return {
                        "status": 1,
                        ",msg": "Go Live event saved successfully !",
                        "ref_id": reference_id,
                        "event_detail": event,
                    }

                else:
                    return {"status": 0, ",msg": "Go Live event cant be created."}


# 77 Enable golive event


@router.post("/enablegoliveevent")
async def enablegoliveevent(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    event_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if event_id == None:
        return {"status": 0, "msg": "Event ID cant be blank."}
    elif not event_id.isnumeric():
        return {"status": 0, "msg": "Invalid Event ID"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            status = 0
            msg = "Invalid nugget id"
            get_token_details = (
                db.query(ApiTokens).filter(ApiTokens.token == access_token).first()
            )
            login_user_id = get_token_details.user_id

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            event_id = int(event_id) if int(event_id) > 0 else None
            if event_id == None:
                return {"status": 0, "msg": "Event ID cant be blank."}
            else:
                edit_event = (
                    db.query(Events)
                    .filter(
                        Events.ref_id == event_id, Events.created_by == login_user_id
                    )
                    .first()
                )
                if edit_event:
                    edit_event.status = 1
                    db.commit()
                    totalfriends = []
                    message_detail = []
                    if edit_event.event_type_id == 1:
                        totalfriends = get_friend_requests(
                            login_user_id,
                            requested_by=None,
                            request_status=1,
                            response_type=1,
                            search_key=None,
                        )
                        totalfriends.append(totalfriends.accepted)
                    if totalfriends and len(totalfriends) > 0:
                        for users in totalfriends:
                            add_notification = Insertnotification(
                                users, login_user_id, 14, edit_event.id
                            )
                        message_detail.append(
                            {
                                "message": "Live Now",
                                "data": {
                                    "refer_id": edit_event.id,
                                    "type": "add_event",
                                },
                                "type": "events",
                            }
                        )

                        pushNotify(totalfriends, message_detail, login_user_id)
                    event = get_event_detail(edit_event.id, login_user_id)
                    return {
                        "status": 1,
                        "event_detail": event,
                        "msg": "Go Live event successfully enabled!",
                    }

                return {"status": 0, "msg": "Go Live event not able to enable."}


# 78 actionGetinfluencercategory

@router.post("/getinfluencercategory")
async def getinfluencercategory(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    auth_code: str = Form(None, description="auth_code + token"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again",
        }

    elif auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth Code is missing"}

    else:
        result_list = []
        access_token = checkToken(db, token.strip())
        auth_code = auth_code.strip()

        auth_text = token.strip()

        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }
            else:
                get_token_details = (
                    db.query(ApiTokens)
                    .filter(ApiTokens.token == access_token)
                    .order_by(ApiTokens.id.desc())
                    .first()
                        )
                login_user_id = get_token_details.user_id if get_token_details else None

                GetInfluencerCategory = (
                    db.query(InfluencerCategory)
                    .filter_by(status=1)
                    .order_by(InfluencerCategory.name.asc())
                    .all()
                )
                if not GetInfluencerCategory:
                    return {"status": 0, "msg": "No result found!"}
                else:
                    get_followers=db.query(FollowUser).filter(
                        FollowUser.follower_userid == login_user_id
                    ).all()
                    user_ids=set([follower.following_userid for follower in get_followers])
                    
                    # Get Category
                    get_category=db.query(User.influencer_category).filter(User.id.in_(user_ids),User.status == 1,User.influencer_category != None).all()
                    category_ids=set([category.influencer_category for category in get_category])
                    influencer_category_ids= [int(item) for sublist in category_ids for item in sublist.split(',')]

                    for category in GetInfluencerCategory:
                        result_list.append(
                            {
                                "id": category.id,
                                "name": category.name
                                if category.name
                                and (category.name != None or category.name != "")
                                else None,
                                "my_category":1 if category.id in influencer_category_ids else 0
                            }
                        )
                    return {
                        "status": 1,
                        "msg": "Success",
                        "influencer_category": result_list,
                    }


# 79 actionSocialmedialogin
@router.post("/socialmedialogin")
async def socialmedialogin(
    db: Session = Depends(deps.get_db),
    signin_type: str = Form(
        None, description="2->Apple,3->Twitter,4->Instagram,5->Google"
    ),
    first_name: str = Form(None),
    last_name: str = Form(None),
    dispaly_name: str = Form(None),
    gender: str = Form(None, description="1->Male,2->Female"),
    dob: Any = Form(None),
    email_id: str = Form(None),
    country_code: str = Form(None),
    mobile_no: str = Form(None),
    geo_location: str = Form(None),
    latitude: str = Form(None),
    longitude: str = Form(None),
    ref_id: str = Form(None),
    auth_code: str = Form(None, description="SALT+email_id"),
    device_id: str = Form(None, description="Uniq ilike IMEI number"),
    push_id: str = Form(None),
    device_type: str = Form(None, description="1->Android,2->IOS,3->Web"),
    auth_codes: str = Form(None, description="SALT+username"),
    voip_token: str = Form(None),
    app_type: str = Form(None, description="1->Android,2->IOS"),
    password: str = Form(None),
    login_from: str = Form(None),
    signup_social_ref_id: str = Form(None),
):
    if auth_code.strip() == "" or auth_code.strip() == None:
        return {"status": 0, "msg": "Auth Code is missing"}
    elif first_name.strip() == "" or first_name.strip() == None:
        return {"status": 0, "msg": "Please provide your first name"}
    elif signin_type and not signin_type.isnumeric():
        return {"status": 0, "msg": "Invalid Signin type"}
    elif signin_type and int(signin_type) <= 1:
        return {"status": 0, "msg": "signin type is missing"}
    elif first_name == None or first_name.strip() == "":
        return {"status": 0, "msg": "First Name is missing"}
    elif auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth code is missing"}
    elif app_type and not app_type.isnumeric():
        return {"status": 0, "msg": "App type is missing"}
    # elif password == None or password.strip() == "":
    #     return {"status":0,"msg":"Password is missing"}
    elif dob and is_date(dob) == False:
        return {"status": 0, "msg": "Invalid Date"}
    else:
        signin_type = int(signin_type)

        mobile_no = mobile_no if mobile_no != "" or mobile_no != None else None

        password = password.strip() if password else None
        last_name = last_name.strip() if last_name else None
        display_name = (
            f"{first_name.strip()} {last_name.strip()}"
            if last_name
            else first_name.strip()
        )
        profile_img = defaultimage("profile_img")
        cover_image = defaultimage("cover_img")
        geo_location = (
            geo_location.strip()
            if geo_location and geo_location.strip() != ""
            else None
        )
        latitude = latitude.strip() if latitude and latitude.strip() != "" else None
        longitude = longitude.strip() if longitude and longitude.strip() != "" else None
        friend_ref_code = ref_id.strip() if ref_id and ref_id.strip() != "" else None

        device_type = device_type if device_type and int(device_type) > 0 else None
        device_id = device_id if device_id != "" or device_id != None else None
        push_id = push_id if push_id != "" or push_id != None else None
        auth_code = auth_code if auth_code != "" or auth_code != None else None
        login_from = login_from if login_from != "" or login_from != None else 2
        voip_token = voip_token if voip_token != "" or voip_token != None else None
        app_type = int(app_type) if app_type else 0

        # Extra parameter
        gender = gender if gender and int(gender) > 0 else None
        signup_social_ref_id = (
            signup_social_ref_id
            if signup_social_ref_id and signup_social_ref_id.strip() != ""
            else None
        )

        auth_text = email_id
        if checkAuthCode(auth_code, auth_text) == False:
            return {"sttaus": 0, "msg": "Authentication failed!"}
        else:
            check_email_or_mobile = EmailorMobileNoValidation(email_id)
            if check_email_or_mobile["status"] and check_email_or_mobile["status"] == 1:
                if check_email_or_mobile["type"] and (
                    check_email_or_mobile["type"] == 1
                    or check_email_or_mobile["type"] == 2
                ):
                    if check_email_or_mobile["type"] == 1:
                        email_id = check_email_or_mobile["email"]
                        mobile_no = None
                    elif check_email_or_mobile["type"] == 2:
                        mobile_no = check_email_or_mobile["mobile"]
                        email_id = None
                else:
                    return {"status": 0, "msg": "Unable to signup"}
            else:
                return {"status": 0, "msg": "Unable to signup"}

            check_email_id = 0
            check_phone = 0

            if email_id:
                check_email_id = (
                    db.query(User)
                    .filter(
                        and_(User.email_id == email_id, User.status.in_([0, 1, 2, 3]))
                    )
                    .count()
                )

            if mobile_no:
                check_phone = (
                    db.query(User)
                    .filter(
                        and_(User.mobile_no == mobile_no, User.status.in_([0, 1, 2, 3]))
                    )
                    .count()
                )

            if check_email_id:
                reply = await logins(
                    db,
                    email_id,
                    password,
                    device_type,
                    device_id,
                    push_id,
                    login_from,
                    voip_token,
                    app_type,
                    1,
                )
                return reply

            if check_phone:
                reply = await logins(
                    db,
                    email_id,
                    password,
                    device_type,
                    device_id,
                    push_id,
                    login_from,
                    voip_token,
                    app_type,
                    1,
                )
                return reply

            else:
                userIP = get_ip()

                if geo_location == None or geo_location == "" or len(geo_location) < 4:
                    Location_details = FindLocationbyIP(userIP)

                    if Location_details["status"] and Location_details["status"] == 1:
                        geo_location = Location_details["country"]
                        latitude = Location_details["latitude"]
                        longitude = Location_details["longitude"]

                country_id = None
                if mobile_no:
                    mobile_check = CheckMobileNumber(db, mobile_no, geo_location)
                    if not mobile_check:
                        return {
                            "status": 0,
                            "msg": "Unable to signup with mobile number",
                        }
                    else:
                        if mobile_check["status"] and mobile_check["status"] == 1:
                            country_code = mobile_check["country_code"]
                            country_id = mobile_check["country_id"]
                            mobile_no = mobile_check["mobile_no"]
                        else:
                            return mobile_check

                password = ""
                model = User(
                    email_id=email_id,
                    is_email_id_verified=1,
                    first_name=first_name,
                    last_name=last_name,
                    display_name=display_name,
                    gender=gender,
                    dob=dob,
                    country_code=country_code,
                    mobile_no=mobile_no,
                    is_mobile_no_verified=0,
                    country_id=country_id,
                    user_code=None,
                    cover_image=cover_image,
                    signup_type=1,
                    signup_social_ref_id=signup_social_ref_id,
                    profile_img=profile_img,
                    geo_location=geo_location,
                    latitude=latitude,
                    longitude=longitude,
                    created_at=datetime.datetime.utcnow(),
                    status=1,
                )
                db.add(model)
                db.commit()
                db.refresh(model)
                if model:
                    user_ref_id = GenerateUserRegID(model.id)
                    password = user_ref_id

                    update_user = (
                        db.query(User)
                        .filter_by(id=model.id)
                        .update(
                            {
                                "user_ref_id": user_ref_id,
                                "password": hashlib.sha1(
                                    user_ref_id.encode()
                                ).hexdigest(),
                            }
                        )
                    )
                    db.commit()

                    # Set Default user settings
                    user_settings_model = UserSettings(
                        user_id=model.id,
                        online_status=1,
                        friend_request="000",
                        nuggets="000",
                        events="000",
                        status=1,
                    )
                    db.add(user_settings_model)
                    db.commit()

                    # Set Default user settings
                    friends_group = FriendGroups(
                        group_name="My Fans",
                        group_icon=defaultimage("group_icon"),
                        created_by=model.id,
                        created_at=datetime.datetime.utcnow(),
                        status=1,
                        chat_enabled=0,
                    )
                    db.add(friends_group)
                    db.commit()

                    # Add Channel
                    channel_arn = None
                    user_arn = None
                    try:
                        # Add User in Chime Channel
                        create_chat_user = chime_chat.createchimeuser(model.email_id)
                        if create_chat_user["status"] == 1:
                            user_arn = create_chat_user["data"][
                                "ChimeAppInstanceUserArn"
                            ]
                            # Update User Chime ID
                            update_user = (
                                db.query(User)
                                .filter(User.id == model.id)
                                .update({"chime_user_id": user_arn})
                            )
                            db.commit()

                            # Add Channels
                            chime_bearer = user_arn
                            group_name = "My Fans"
                            channel_response = create_channel(chime_bearer, group_name)

                            channel_arn = (
                                channel_response["ChannelArn"]
                                if channel_response
                                else None
                            )

                    except Exception as e:
                        print(e)

                    referred_id = 0
                    if friend_ref_code:
                        friend_ref_code = base64.b64decode(friend_ref_code)

                        referrer_ref_id = friend_ref_code.split("//")
                        if len(referrer_ref_id) == 2:
                            referred_user = (
                                db.query(User)
                                .filter(
                                    User.user_ref_id == referrer_ref_id[0],
                                    User.status == 1,
                                )
                                .first()
                            )
                            if referred_user:
                                referred_id = referred_user.id

                                update_user = (
                                    db.query(User)
                                    .filter_by(id=model.id)
                                    .update(
                                        {
                                            "referrer_id": referred_user.id,
                                            "invited_date": datetime.strptime(
                                                referrer_ref_id[1], "%Y-%m-%d %H:%M:%S"
                                            ),
                                        }
                                    )
                                )
                                db.commit()

                                ref_friend = MyFriends(
                                    sender_id=referred_user.id,
                                    receiver_id=model.id,
                                    request_date=datetime.datetime.utcnow(),
                                    request_status=1,
                                    status_date=None,
                                    status=1,
                                )
                                db.add(ref_friend)
                                db.commit()
                                query = db.query(FriendGroups).filter(
                                    FriendGroups.group_name == "My Fans",
                                    FriendGroups.created_by == referred_user.id,
                                )
                                group = query.first()

                                if group:
                                    Followmodel = FollowUser(
                                        follower_userid=model.id,
                                        following_userid=referred_user.id,
                                        created_date=datetime.datetime.utcnow(),
                                    )
                                    db.add(Followmodel)
                                    db.commit()
                                    friend_group_member = (
                                        db.query(FriendGroupMembers)
                                        .filter(
                                            FriendGroupMembers.group_id == group.id,
                                            FriendGroupMembers.user_id
                                            == referred_user.id,
                                        )
                                        .all()
                                    )
                                    if not friend_group_member:
                                        friend_model = FriendGroupMembers(
                                            group_id=group.id,
                                            user_id=model.id,
                                            added_date=datetime.datetime.utcnow(),
                                            added_by=referred_user.id,
                                            is_admin=0,
                                            disable_notification=1,
                                            status=1,
                                        )
                                        db.add(friend_model)
                                        db.commit()

                                        # Add Member in Channel
                                        channel_arn = channel_arn
                                        chime_bearer = user_arn
                                        member_id = (
                                            list(friend_model.user.chime_user_id)
                                            if referred_user.chime_user_id
                                            else None
                                        )
                                        try:
                                            addmembers(
                                                channel_arn, chime_bearer, member_id
                                            )
                                        except Exception as e:
                                            print(f"Referrer:{e}")

                    # Referral Auto Add Friend Ends
                    rawcaster_support_id = GetRawcasterUserID(db, 2)  # Type = 2
                    if rawcaster_support_id and referred_id != rawcaster_support_id:
                        myfriend = MyFriends(
                            sender_id=rawcaster_support_id,
                            receiver_id=model.id,
                            request_date=datetime.datetime.utcnow(),
                            request_status=1,
                            status_date=None,
                            status=1,
                        )
                        db.add(myfriend)
                        db.commit()

                    password = hashlib.sha1(password.encode()).hexdigest()
                    if email_id == "":
                        email_id = mobile_no

                    reply = await logins(
                        db,
                        email_id,
                        password,
                        device_type,
                        device_id,
                        push_id,
                        login_from,
                        voip_token,
                        app_type,
                        0,
                    )
                    return reply
                else:
                    return {
                        "status": 0,
                        "msg": "Something went wrong when creating a User",
                    }


# 80  actionInfluencerlist
@router.post("/influencerlist")
async def influencerlist(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    search_key: str = Form(None),
    auth_code: str = Form(None, description="SALT+token"),
    category: str = Form(None, description="influencer category"),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again",
        }
    elif auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth code is missing"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}

    access_token = checkToken(db, token) if token != "RAWCAST" else True
    auth_code = auth_code.strip()

    auth_text = token.strip()
    if checkAuthCode(auth_code, auth_text) == False:
        return {"status": 0, "msg": "Authentication failed!"}
    else:
        if access_token == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            page_number = int(page_number)
            login_user_id = 0
            get_token_details = (
                db.query(ApiTokens.user_id).filter(ApiTokens.token == access_token).first()
            )
            if get_token_details:
                login_user_id = get_token_details.user_id

            api_search_key = (
                search_key
                if search_key
                and (search_key.strip() != None or search_key.strip() != "")
                else None
            )
            api_category = category if category else None

            current_page_no = int(page_number) if int(page_number) > 0 else 1

            criteria = db.query(
                User.id,
                User.influencer_category,
                User.bio_data,
                User.email_id,
                User.user_ref_id,
                User.first_name,
                User.last_name,
                User.display_name,
                User.gender,
                User.profile_img,
                User.user_status_id,
                User.geo_location,
                FollowUser.id.label("follow_id"),
            )
            criteria = criteria.join(
                FollowUser,
                and_(
                    FollowUser.following_userid == User.id,
                    FollowUser.follower_userid == login_user_id,
                ),
                isouter=True,
            )
            criteria = criteria.filter(User.id != login_user_id, User.status == 1)
            criteria = criteria.filter(FollowUser.id == None)

            # Omit blocked users
            get_all_blocked_users = get_friend_requests(
                db, login_user_id, requested_by=None, request_status=3, response_type=1
            )
            blocked_users = get_all_blocked_users["blocked"]

            if blocked_users:
                criteria = criteria.filter(User.id.not_in(blocked_users))

            if api_search_key != None and api_search_key.strip() != "":
                criteria = criteria.filter(
                    and_(
                        or_(
                            User.email_id.ilike(api_search_key + "%"),
                            User.mobile_no.ilike(api_search_key + "%"),
                            User.display_name.ilike(api_search_key + "%"),
                            User.first_name.ilike(api_search_key + "%"),
                            User.last_name.ilike(api_search_key + "%"),
                        )
                    )
                )

            if api_category != None and api_category != "":
                criteria = criteria.filter(
                    User.influencer_category.ilike("%" + api_category + "%")
                )

            get_row_count = criteria.count()

            if get_row_count < 1:
                return {"status": 0, "msg": "No Result found"}
            else:
                default_page_size = 24
                result_list = []
                limit, offset, total_pages = get_pagination(
                    get_row_count, current_page_no, default_page_size
                )
                criteria = criteria.order_by(User.first_name.asc())

                get_result = criteria.limit(limit).offset(offset).all()

                for res in get_result:
                    influencer_category = []
                    follow_count = (
                        db.query(FollowUser).filter_by(following_userid=res.id).count()
                    )
                    if res.influencer_category:
                        influencer_category = (
                            db.query(InfluencerCategory)
                            .filter(
                                InfluencerCategory.id.in_(
                                    res.influencer_category.split(",")
                                )
                            )
                            .all()
                        )

                    result_list.append(
                        {
                            "user_id": res.id,
                            "user_ref_id": res.user_ref_id,
                            "email_id": res.email_id
                            if res.email_id and res.email_id != ""
                            else "",
                            "first_name": res.first_name
                            if res.first_name and res.first_name != ""
                            else "",
                            "last_name": res.last_name
                            if res.last_name and res.last_name != ""
                            else "",
                            "display_name": res.display_name
                            if res.display_name and res.display_name != ""
                            else "",
                            "gender": res.gender
                            if res.gender and res.gender != ""
                            else "",
                            "profile_img": res.profile_img
                            if res.profile_img and res.profile_img != ""
                            else "",
                            "follow": True
                            if hasattr(res, "follow_id") and res.follow_id != ""
                            else False,
                            "location": res.geo_location
                            if hasattr(res, "geo_location") and res.geo_location != ""
                            else "",
                            "followers": follow_count,
                            "category": [
                                influencer.name for influencer in influencer_category
                            ]
                            if influencer_category
                            else "",
                            "user_status_id": res.user_status_id,
                            "bio_data": ProfilePreference(
                                db,
                                login_user_id,
                                res.id,
                                "bio_display_status",
                                res.bio_data,
                            ),
                        }
                    )
                return {
                    "status": 1,
                    "msg": "Success",
                    "total_pages": total_pages,
                    "current_page_no": current_page_no,
                    "users_list": result_list,
                    "total_influencer_count": get_row_count,
                }


# 81. Influencer Follow
@router.post("/influencerfollow")
async def influencerfollow(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    auth_code: str = Form(None, description="SALT+ Token"),
    follow_userid: str = Form(
        None, description='["RA286164941105720824",”RA286164941105720957”]'
    ),
    select_all: str = Form(None, description="1-all,0-not select"),
    category:str=Form(None),
    search_key:str=Form(None)
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    if auth_code == None or auth_code.strip() == "":
        return {"status": 0, "msg": "Auth code is missing"}
    if select_all and not select_all.isnumeric():
        return {"status": 0, "msg": "Invalid key"}
    if category and not category.isnumeric():
        return {"status": 0, "msg": "Invalid Category id"}

    else:
        auth_code = auth_code
        auth_text = token.strip()

        select_all = int(select_all) if select_all else 0

        if checkAuthCode(auth_code, auth_text) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            access_token = checkToken(db, token)

            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }
            else:
                get_token_details = (
                    db.query(ApiTokens).filter_by(token=access_token).first()
                )

                login_user_id = get_token_details.user_id if get_token_details else None

                follow_userids = []

                if select_all == 1:
                    
                    criteria = db.query(User.user_ref_id).join(
                        FollowUser,
                        and_(
                            FollowUser.following_userid == User.id,
                            FollowUser.follower_userid == login_user_id,
                        ),
                        isouter=True,
                    )
                    criteria = criteria.filter(
                        User.id != login_user_id, User.status == 1
                    )
                    criteria = criteria.filter(FollowUser.id == None)
                    
                    if search_key:
                        criteria = criteria.filter(
                                and_(
                                    or_(
                                        User.email_id.ilike(search_key + "%"),
                                        User.mobile_no.ilike(search_key + "%"),
                                        User.display_name.ilike(search_key + "%"),
                                        User.first_name.ilike(search_key + "%"),
                                        User.last_name.ilike(search_key + "%"),
                                    )
                                )
                            )

                    # Omit blocked users
                    get_all_blocked_users = get_friend_requests(
                        db,
                        login_user_id,
                        requested_by=None,
                        request_status=3,
                        response_type=1,
                    )
                    blocked_users = get_all_blocked_users["blocked"]

                    if blocked_users:
                        criteria = criteria.filter(User.id.not_in(blocked_users))
                        
                    if category:
                        criteria=criteria.filter(User.influencer_category.like("%"+category+"%"))
                    
                    # Selected Influencer
                    selected_follow_userid = eval(follow_userid)

                    follow_userids = [ref_id.user_ref_id for ref_id in criteria] + selected_follow_userid

                else:
                    follow_userids = eval(follow_userid)

                if not isinstance(follow_userids, list):
                    return {"status": 0, "msg": "Invalid follow user list"}

                else:
                    total = len(follow_userids)
                    success = 0
                    failed = 0
                    reason = ""

                    for follow_user_id in follow_userids:
                        users = (
                            db.query(User)
                            .filter(User.user_ref_id == follow_user_id)
                            .first()
                        )

                        if users:
                            follow_userid = users.id

                            user = (
                                db.query(User)
                                .filter(User.id == follow_userid, User.status == 1)
                                .first()
                            )

                            follow_user = (
                                db.query(FollowUser)
                                .filter(
                                    FollowUser.follower_userid == login_user_id,
                                    FollowUser.following_userid == follow_userid,
                                )
                                .first()
                            )

                            friend_group = (
                                db.query(FriendGroups)
                                .filter(
                                    FriendGroups.group_name == "My Fans",
                                    FriendGroups.created_by == follow_userid,
                                )
                                .first()
                            )

                            if (
                                user
                                and not follow_user
                                and login_user_id != follow_userid
                            ):
                                add_follow_user = FollowUser(
                                    follower_userid=login_user_id,
                                    following_userid=follow_userid,
                                    created_date=datetime.datetime.utcnow(),
                                    status=1,
                                )
                                db.add(add_follow_user)
                                db.commit()

                                if add_follow_user:
                                    if friend_group:
                                        friend_group_member = (
                                            db.query(FriendGroupMembers)
                                            .filter(
                                                FriendGroupMembers.group_id
                                                == friend_group.id,
                                                FriendGroupMembers.user_id
                                                == login_user_id,
                                            )
                                            .all()
                                        )

                                        if not friend_group_member:
                                            add_group_member = FriendGroupMembers(
                                                group_id=friend_group.id,
                                                user_id=login_user_id,
                                                added_date=datetime.datetime.utcnow(),
                                                added_by=follow_userid,
                                                is_admin=0,
                                                disable_notification=1,
                                                status=1,
                                            )
                                            db.add(add_group_member)
                                            db.commit()

                                            if add_group_member:
                                                success = success + 1

                                            else:
                                                reason += f"{reason} unable to save fan group, "
                                                failed = failed + 1

                                        else:
                                            success = success + 1

                                    else:
                                        success = success + 1

                                else:
                                    reason += f"{follow_user_id} unable to save, "
                                    failed = failed + 1

                            else:
                                reason += f"{follow_user_id} Not allowed, "
                                failed = failed + 1

                        else:
                            reason += f"{follow_user_id} Unable to get user details, "
                            failed = failed + 1

                if total == success:
                    return {"status": 1, "msg": "Success"}
                else:
                    return {"status": 0, "msg": reason}


# 82. Poll Vote


@router.post("/pollvote")
async def pollvote(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
    poll_option_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif nugget_id == None or not nugget_id.isnumeric():
        return {"status": 0, "msg": "Nugget ID is missing"}

    elif poll_option_id == None or not poll_option_id.isnumeric():
        return {"status": 0, "msg": "Poll option is missing"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id if get_token_details else None

            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            access_check = NuggetAccessCheck(db, login_user_id, nugget_id)
            if not access_check:
                return {"status": 0, "msg": "Unauthorized access"}

            check_nuggets = db.query(Nuggets).filter(Nuggets.id == nugget_id).first()

            if check_nuggets:
                checkpreviousvote = (
                    db.query(NuggetPollVoted)
                    .filter(
                        NuggetPollVoted.nugget_id == nugget_id,
                        NuggetPollVoted.user_id == login_user_id,
                    )
                    .first()
                )

                if not checkpreviousvote:
                    add_nugget_vote = NuggetPollVoted(
                        nugget_master_id=check_nuggets.nuggets_id,
                        nugget_id=nugget_id,
                        user_id=login_user_id,
                        poll_option_id=poll_option_id,
                        created_date=datetime.datetime.utcnow(),
                    )
                    db.add(add_nugget_vote)
                    db.commit()
                    db.refresh(add_nugget_vote)
                    if add_nugget_vote:
                        # Update Nugget Poll count in Nugget Table
                        check_nuggets.total_poll_count = check_nuggets.total_poll_count + 1
                        db.commit()
                        
                        poll_vote_calc = PollVoteCalculation(
                            db, check_nuggets.nuggets_id
                        )

                        # ref_id=13
                        # insert_notify=Insertnotification(db,check_nuggets.user_id,login_user_id,ref_id,nugget_id)
                        # add_nugget_vote.status = 1
                        # db.commit()

                        return {"status": 1, "msg": "Success"}

                    else:
                        return {"status": 0, "msg": "failed to vote"}

                else:
                    return {"status": 0, "msg": "Your already voted this poll"}


# 83.Tags List


@router.post("/tagslist")
async def tagslist(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    search_tag: str = Form(None),
    auth_code: str = Form(None),
    page_number: str = Form(default=1),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif auth_code == None:
        return {"status": 0, "msg": "Authcode is missing"}
    elif not str(page_number).isnumeric():
        return {"status": 0, "msg": "Invalid page Number"}
    else:
        if checkAuthCode(auth_code.strip(), token.strip()) == False:
            return {"status": 0, "msg": "Authentication failed!"}
        else:
            access_token = checkToken(db, token)

            if access_token == False:
                return {
                    "status": -1,
                    "msg": "Sorry! your login session expired. please login again.",
                }
            else:
                get_token_details = (
                    db.query(ApiTokens).filter_by(token=access_token).first()
                )

                login_user_id = get_token_details.user_id

                current_page_no = int(page_number)

                get_nuggets = (
                    db.query(
                        NuggetHashTags.hash_tag,
                        NuggetHashTags.country_id,
                        func.count(Nuggets.id).label("total_nuggets"),
                    )
                    .filter(
                        NuggetHashTags.nugget_master_id == NuggetsMaster.id,
                        NuggetHashTags.nugget_id == Nuggets.id,
                    )
                    .filter(
                        NuggetHashTags.status == 1,
                        Nuggets.nugget_status == 1,
                        NuggetsMaster.status == 1,
                    )
                )

                if search_tag and search_tag.strip() != "":
                    get_nuggets = get_nuggets.filter(
                        NuggetHashTags.hash_tag.ilike("%" + search_tag + "%")
                    )

                get_nuggets = get_nuggets.group_by(
                    NuggetHashTags.hash_tag, NuggetHashTags.country_id
                )

                get_nuggets_count = get_nuggets.count()

                if get_nuggets_count < 1:
                    return {"status": 0, "msg": "No Result found"}

                else:
                    default_page_size = 24
                    limit, offset, total_pages = get_pagination(
                        get_nuggets_count, current_page_no, default_page_size
                    )
                    get_nuggets = get_nuggets.order_by(NuggetHashTags.hash_tag.asc())
                    get_nuggets = get_nuggets.limit(limit).offset(offset)

                    result_list = []
                    for nug in get_nuggets:
                        nuggettrend = (
                            db.query(
                                func.hour(Nuggets.created_date).label("Hours"),
                                func.count(Nuggets.id).label("total_nuggets"),
                            )
                            .join(
                                NuggetHashTags, NuggetHashTags.nugget_id == Nuggets.id
                            )
                            .filter(
                                NuggetHashTags.nugget_master_id == NuggetsMaster.id,
                                NuggetHashTags.status == 1,
                                Nuggets.nugget_status == 1,
                                NuggetsMaster.status == 1,
                                NuggetHashTags.hash_tag.ilike(nug.hash_tag),
                                Nuggets.created_date.between(
                                    datetime.datetime.utcnow() - timedelta(days=1),
                                    datetime.datetime.utcnow(),
                                ),
                            )
                            .group_by(func.hour(Nuggets.created_date))
                            .all()
                        )

                        trends = []
                        for i in range(25):
                            if nuggettrend:
                                for trend in nuggettrend:
                                    if trend.Hours == i:
                                        trends.append(
                                            {
                                                "total_nuggets": str(
                                                    trend.total_nuggets
                                                ),
                                                "hours": i,
                                            }
                                        )
                                    else:
                                        trends.append({"total_nuggets": 0, "hours": i})

                        result_list.append(
                            {
                                "tag": nug.hash_tag,
                                "nugget_count": nug.total_nuggets,
                                "country": nug.country_id,
                                "trends": trends,
                            }
                        )

                    return {
                        "status": 1,
                        "msg": "Success",
                        "total_pages": total_pages,
                        "current_page_no": current_page_no,
                        "tags": result_list,
                    }


# 84. Save And Unsave Nugget
@router.post("/saveandunsavenugget")
async def saveandunsavenugget(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    nugget_id: str = Form(None),
    save: str = Form(None, description="1-save,2-unsave"),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }

    elif nugget_id == None or not nugget_id.isnumeric():
        return {"status": 0, "msg": "Nugget Id is required"}
    elif not save or not save.isnumeric():
        return {"status": 0, "msg": "Save flag is missing"}

    if int(save) != 1 and int(save) != 2:
        return {"status": 0, "msg": "Save flag is invalid"}

    else:
        save = int(save) if save else None

        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }

        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id
            if IsAccountVerified(db, login_user_id) == False:
                return {
                    "status": 0,
                    "msg": "You need to complete your account validation before you can do this",
                }

            access_check = NuggetAccessCheck(db, login_user_id, nugget_id)

            if access_check == False:
                return {"status": 0, "msg": "Unauthorized access"}

            check_nuggets = db.query(Nuggets).filter(Nuggets.id == nugget_id).first()
            if check_nuggets:
                get_saved_nugget = (
                    db.query(NuggetsSave)
                    .filter(
                        NuggetsSave.user_id == login_user_id, NuggetsSave.status == 1
                    )
                    .count()
                )

                if save == 1:  # Save
                    checkprevioussave = (
                        db.query(NuggetsSave)
                        .filter(
                            NuggetsSave.nugget_id == nugget_id,
                            NuggetsSave.user_id == login_user_id,
                        )
                        .first()
                    )
                    if not checkprevioussave:
                        nuggetsave = NuggetsSave(
                            user_id=login_user_id,
                            nugget_id=nugget_id,
                            created_date=datetime.datetime.utcnow(),
                        )
                        db.add(nuggetsave)
                        db.commit()
                        db.refresh(nuggetsave)

                        if nuggetsave:
                            ref_id = 5
                            insert_notification = Insertnotification(
                                db,
                                check_nuggets.user_id,
                                login_user_id,
                                ref_id,
                                nugget_id,
                            )

                            return {
                                "status": 1,
                                "msg": "Success",
                                "saved_nugget_count": get_saved_nugget + 1,
                            }
                        else:
                            return {"status": 0, "msg": "failed to save"}
                    else:
                        return {"status": 0, "msg": "Your already saved this nugget"}

                elif save == 2:  # Unsave
                    checkprevioussave = (
                        db.query(NuggetsSave)
                        .filter(
                            NuggetsSave.nugget_id == nugget_id,
                            NuggetsSave.user_id == login_user_id,
                        )
                        .first()
                    )

                    if checkprevioussave:
                        deleteresult = (
                            db.query(NuggetsSave)
                            .filter(NuggetsSave.id == checkprevioussave.id)
                            .delete()
                        )
                        db.commit()

                        if deleteresult:
                            return {
                                "status": 1,
                                "msg": "Success",
                                "saved_nugget_count": get_saved_nugget - 1  if get_saved_nugget else 0,
                            }

                        else:
                            return {"status": 0, "msg": "failed to unsave"}

                    else:
                        return {"status": 0, "msg": "you not yet saved this nugget"}

            else:
                return {"status": 0, "msg": "Invalid nugget"}


# 88 Exit from group


@router.post("/exitfromgroup")
async def saveandunsavenugget(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_id: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not group_id:
        return {"status": 0, "msg": "Sorry! Group id can not be empty."}
    elif group_id and not group_id.isnumeric():
        return {"status": 0, "msg": "Invalid group id"}
    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id

            get_group = (
                db.query(FriendGroups)
                .filter(FriendGroups.status == 1, FriendGroups.id == group_id)
                .first()
            )
            if not get_group:
                return {"status": 0, "msg": "Invalid request"}
            elif get_group.group_name == "My Fans":
                return {"status": 0, "msg": "You can't exit from Fans group"}
            elif get_group.created_by == login_user_id:
                return {"status": 0, "msg": "You can't exit from your group"}
            else:
                # Delete friend Group Members
                try:
                    group_members = (
                        db.query(FriendGroupMembers)
                        .filter(
                            FriendGroupMembers.group_id == group_id,
                            FriendGroupMembers.user_id == login_user_id,
                        )
                        .delete()
                    )
                    db.commit()
                    return {"status": 1, "msg": "Successfully updated"}
                except:
                    return {"status": 0, "msg": "Failed to Exit from the group"}


# Group Abuse Report
@router.post("/groupabusereport")
async def groupabusereport(
    db: Session = Depends(deps.get_db),
    token: str = Form(None),
    group_id: str = Form(None),
    message: str = Form(None),
):
    if token == None or token.strip() == "":
        return {
            "status": -1,
            "msg": "Sorry! your login session expired. please login again.",
        }
    elif not group_id or not group_id.isnumeric():
        return {"status": 0, "msg": "Sorry! Group id can not be empty."}
    elif not message:
        return {"status": 0, "msg": "Message Missing"}
    elif message and len(message) > 500:
        return {"status": 0, "msg": "Message Length should be less than 500"}

    else:
        access_token = checkToken(db, token)

        if access_token == False:
            return {
                "status": -1,
                "msg": "Sorry! your login session expired. please login again.",
            }
        else:
            get_token_details = (
                db.query(ApiTokens).filter_by(token=access_token).first()
            )

            login_user_id = get_token_details.user_id
            groupid = group_id
            message = message.strip()

            # Get Report
            get_report = (
                db.query(GroupReport)
                .filter_by(user_id=login_user_id, group_id=groupid)
                .first()
            )
            if not get_report:
                group = (
                    db.query(FriendGroups).filter(FriendGroups.id == groupid).first()
                )
                if group:
                    add_report = GroupReport(
                        user_id=login_user_id,
                        group_id=group.id,
                        message=message,
                        reported_date=datetime.datetime.utcnow(),
                        status=1,
                    )
                    db.add(add_report)
                    db.commit()
                    db.refresh(add_report)

                    if add_report:
                        if group.created_by == login_user_id:
                            return {
                                "status": 1,
                                "msg": "Thanks for the reporting, we will take the action",
                            }
                        else:
                            # Delete Friend Group
                            try:
                                group_members = (
                                    db.query(FriendGroupMembers)
                                    .filter(
                                        FriendGroupMembers.group_id == group_id,
                                        FriendGroupMembers.user_id == login_user_id,
                                    )
                                    .delete()
                                )
                                # UnFollow User
                                del_follow_user = (
                                    db.query(FollowUser)
                                    .filter(
                                        FollowUser.follower_userid == login_user_id,
                                        FollowUser.following_userid == group.created_by,
                                    )
                                    .delete()
                                )
                                db.commit()

                                return {
                                    "status": 1,
                                    "msg": "Thanks for the reporting, we will take the action",
                                }
                            except:
                                return {
                                    "status": 0,
                                    "msg": "Failed to Exit from the group",
                                }
                    else:
                        return {"status": 0, "msg": "Failed to add report"}
                else:
                    return {"status": 0, "msg": "Group ID not correct"}
            else:
                return {"status": 0, "msg": "You have already reported this group."}
