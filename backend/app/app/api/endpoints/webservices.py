from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from datetime import datetime,date
import re
import socket
import base64

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
                    
                    # reply=logins(db,email_id,password,device_type,device_id,push_id,login_from,voip_token,app_type)
                    
                    return {"status":1, "msg": "Success", "email": email_id,"user_id":add_user.id,"acc_verify_status": 0}
                    
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
                user_update=0
                if otp_flag =="sms":
                    update_user=db.query(User).filter(User.id == get_otp_log.user_id).update({"is_mobile_no_verified":1,"status":1})
                    user_update=update_user.id
                    db.commit()
                else:
                    update_user=db.query(User).filter(User.id == get_otp_log.user_id).update({"is_email_id_verified":1,"status":1})
                    user_update=update_user.id
                    db.commit()
                if update_user:
                    get_user=db.query(User).filter(User.id == get_otp_log.user_id).first()
                    if get_user:
                        if get_user.referrer_id != None:
                            change_referral_date=ChangeReferralExpiryDate(db,get_user.referrer_id)
                            
                        if get_user.is_email_id_verified == 1:
                            print("Mail Pending")
                    else:
                        return {"status" :1, "msg" :"Your account has been verified successfully."}
                        
                else:
                    return {"status" :0, "msg" :"Account verification failed. Please try again"}
                    



# 3 - Resend OTP

@router.post("/resendotp")
async def resendotp(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),otp_ref_id:int=Form(None),token:str=Form(...),otp_flag:str=Form(None)):
    if otp_flag and otp_flag.strip() == "" or otp_flag== None:
        otp_flag='email'
    
    
    auth_text="Rawcaster" if otp_ref_id and otp_ref_id == 0 or otp_ref_id == None else otp_ref_id
    if checkAuthCode(auth_code,auth_text) == False:
        return {"status":0,"msg": "Authentication failed!"}
    else:
    
        if otp_ref_id == None:
            if token.strip():
                return {"status":0,"msg":"Sorry! your login session expired. please login again."}
            else:
                login_user_id=0
                access_token=checkToken(token)
                
                if access_token == False:
                    return {"status":-1,"msg":"Sorry! your login session expired. please login again."}
                else:
                    get_token_details=db.query(ApiTokens).filter(ApiTokens.token ==access_token).all()
                    for token in get_token_details:
                        login_user_id=token.user_id
                
                otp=generateOTP()
                otp_time=datetime.now()
                otp_model=OtpLog(user_id=login_user_id,otp=otp,otp_type=1,created_at=otp_time,status=1)
                db.add(otp_model)
                db.commit()
                
                if otp_model:
                    otp_time=datetime.now()
                    otp_model.created_at=otp_time
                    db.commit()
                    
                    if otp_model.otp_type == 1:  # if signup
                        mail_sub="Rawcaster - Account Verification"
                        mail_msg="Your OTP for Rawcaster account verification is : "
                        
                    elif  otp_model.otp_type == 3 : # if forgot password
                        mail_sub="Rawcaster - Password Reset"
                        mail_msg="Your OTP for Rawcaster account password reset is"
                    
                    if otp_flag == "sms":
                        to=otp_model.user.mobile_no
                        print("SMS")
                    else:
                        to=otp_model.user.email_id
                        
                        print("MAIL")
                    
                    remaining_seconds=0
                    target_time= int(round(otp_time.timestamp())) + 300
                    current_time=datetime.now()
                    if current_time < target_time:
                        remaining_seconds=target_time - current_time
                    
                    reply_msg=f'Please enter the One Time Password (OTP) sent to {to}'
                    return {"status":1,"msg":reply_msg,"email":to,"otp_ref_id":otp_ref_id,"remaining_seconds":remaining_seconds}
                    
                else:
                    return {"status" :0, "msg" :"Failed to resend otp, please try again"}
                    
                        


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
    return "done"




# 6 - Forgot Password
@router.post("/forgotpassword")
async def forgotpassword(db:Session=Depends(deps.get_db),username:str=Form(...,description="Email ID / Mobile Number"),auth_code:str=Form(...,description="SALT + username")):
    return "done"





# 7 - Verify OTP and Reset Password
@router.post("/verifyotpandresetpassword")
async def verifyotpandresetpassword(db:Session=Depends(deps.get_db),otp_ref_id:int=Form(...),otp:int=Form(...),
                                    new_password:str=Form(...),confirm_password:str=Form(...),device_id:str=Form(None),
                                    push_id:str=Form(None,description="FCM  or APNS"),device_type:int=Form(None),
                                    auth_code:str=Form(...,description="SALT + otp_ref_id")):
    return "done"




# 8 - Change Password
@router.post("/changepassword")
async def changepassword(db:Session=Depends(deps.get_db),token:str=Form(...),old_password:int=Form(...),new_password:int=Form(...),confirm_password:int=Form(...),auth_code:int=Form(...,description="SALT + token")):
    return "done"


# 9 - Get country list
@router.post("/getcountylist")
async def getcountylist(db:Session=Depends(deps.get_db)):
    return "done"




# 10 - Contact us
@router.post("/contactus")
async def contactus(db:Session=Depends(deps.get_db),name:str=Form(...),email_id:str=Form(...),subject:str=Form(...),message:str=Form(...),
                    auth_code:str=Form(...,description="SALT + email_id")):
    return "done"



# 11 - Get My Profile
@router.post("/getmyprofile")
async def getmyprofile(db:Session=Depends(deps.get_db),token:str=Form(...),auth_code:str=Form(...,description="SALT + token")):
    return "done"


# 12. Update My Profile
@router.post("/updatemyprofile")
async def updatemyprofile(db:Session=Depends(deps.get_db),token:str=Form(...),name:str=Form(...),first_name:str=Form(...),last_name:str=Form(None),
                          gender:int=Form(None,description="0->Transgender,1->Male,2->Female",ge=0,le=2),dob:date=Form(None),
                          email_id:str=Form(...),website:str=Form(None),country_code:int=Form(None),country_id:int=Form(None),
                          mobile_no:int=Form(None),profile_image:UploadFile=File(None),cover_image:UploadFile=File(None),
                          auth_code:str=Form(...,description="SALT + token + name"),geo_location:str=Form(None),latitude:str=Form(None),
                          longitude:str=Form(None)):
    return "done"


# 13 Search Rawcaster Users (for friends)
@router.post("/searchrawcasterusers")
async def searchrawcasterusers(db:Session=Depends(deps.get_db),token:str=Form(...,description="Any name, email"),auth_code:str=Form(...,description="SALT + token"),
                               search_for:int=Form(None,description="0-Pending,1-Accepted,2-Rejected,3-Blocked",ge=0,le=3),page_number:int=Form(None)):
                         
    return "done"



# 14 Invite to Rawcaster
@router.post("/invitetorawcaster")
async def invitetorawcaster(db:Session=Depends(deps.get_db),token:str=Form(...),email_id:list=Form(...,description="email ids"),
                               auth_code:int=Form(None,description="SALT + token")):
                         
    return "done"




# 15 Invite to Rawcaster
@router.post("/sendfriendrequests")
async def sendfriendrequests(db:Session=Depends(deps.get_db),token:str=Form(...),email_id:list=Form(...,description="email ids"),
                               auth_code:int=Form(None,description="SALT + token")):
                         
    return "done"



# 16 List all friend requests (all requests sent to this users from others)
@router.post("/listallfriendrequests")
async def listallfriendrequests(db:Session=Depends(deps.get_db),token:str=Form(...)):
                         
    return "done"



# 17 Respond to friend request received from others
@router.post("/respondtofriendrequests")
async def respondtofriendrequests(db:Session=Depends(deps.get_db),token:str=Form(...),friend_request_id:int=Form(...),notification_id:int=Form(...),
                                  response:int=Form(...,description="1-Accept,2-Reject,3-Block",ge=1,le=3)):
                         
    return "done"




# 18 List all Friend Groups
@router.post("/listallfriendgroups")
async def listallfriendgroups(db:Session=Depends(deps.get_db),token:str=Form(...),search_key:str=Form(None),page_number:int=Form(default=1)):
                         
    return "done"


# 19 List all Friends
@router.post("/listallfriends")
async def listallfriends(db:Session=Depends(deps.get_db),token:str=Form(...),search_key:str=Form(None),group_ids:str=Form(None,description="Like ['12','13','14']"),
                         nongrouped:int=Form(None,description="Send 1",ge=1,le=1),friends_count:int=Form(None),allfriends:int=Form(None,description="send 1",ge=1,le=1),
                         page_number:int=Form(None,description="send 1 for initial request")):
                         
    return "done"




# 20 Add Friend Group
@router.post("/addfriendgroup")
async def addfriendgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_name:str=Form(...),group_members:str=Form(None,description=" User ids Like ['12','13','14']"),
                         group_icon:UploadFile=File(None)):
                         
    return "done"



# 21 Edit Friend Group
@router.post("/editfriendgroup")
async def editfriendgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_name:str=Form(...),group_id:int=Form(...),
                         group_icon:UploadFile=File(None)):
                         
    return "done"




# 22 Add Friends to Group
@router.post("/addfriendstogroup")
async def addfriendstogroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_members:str=Form(None,description=" User ids Like ['12','13','14']"),group_id:int=Form(...)):
                         
    return "done"




# 23 Remove Friends from Group
@router.post("/removefriendsfromgroup")
async def removefriendsfromgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_members:str=Form(None,description=" User ids Like ['12','13','14']"),group_id:int=Form(...)):
                         
    return "done"



# 24. Delete Friend Group
@router.post("/deletefriendgroup")
async def deletefriendgroup(db:Session=Depends(deps.get_db),token:str=Form(...),group_id:int=Form(...)):
                         
    return "done"




# 25. Add Nuggets
@router.post("/addnuggets")
async def addnuggets(db:Session=Depends(deps.get_db),token:str=Form(...),content:str=Form(...),share_type:int=Form(None),share_with:str=Form(...,description='friends":[1,2,3],"groups":[1,2,3]}'),
                     nuggets_media:UploadFile=File(...),poll_option:str=Form(None),poll_duration:str=Form(None)):
                         
    return "done"




# 26. List Nuggets
@router.post("/listnuggets")
async def listnuggets(db:Session=Depends(deps.get_db),token:str=Form(...),my_nuggets:int=Form(None),filter_type:int=Form(None),user_id:int=Form(None),
                     saved:int=Form(None),search_key:str=Form(None),page_number:int=Form(None),nugget_type:int=Form(None,description="1-video,2-Other than video,0-all",ge=0,le=2)):
                         
    return "done"




# 27. Like And Unlike Nugget
@router.post("/likeandunlikenugget")
async def likeandunlikenugget(db:Session=Depends(deps.get_db),token:str=Form(...),nugget_id:int=Form(...),like:int=Form(...,description="1-like,2-unlike")):
                         
    return "done"




# 28. Delete Nugget
@router.post("/deletenugget")
async def deletenugget(db:Session=Depends(deps.get_db),token:str=Form(...),nugget_id:int=Form(...)):
                         
    return "done"




# 29. Nugget Comment List
@router.post("/nuggetcommentlist")
async def nuggetcommentlist(db:Session=Depends(deps.get_db),token:str=Form(...),nugget_id:int=Form(...)):
                         
    return "done"




# 30. Add or Reply Nugget Comment
@router.post("/addnuggetcomment")
async def addnuggetcomment(db:Session=Depends(deps.get_db),token:str=Form(...),type:int=Form(None,description="1-comment,2-reply"),nugget_id:int=Form(...),
                           comment_id:int=Form(None),comment:str=Form(...)):
    
    if type == 2 and not comment_id:
        return {"status":0,"msg":"comment id required"}
        
                         
    return "done"


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