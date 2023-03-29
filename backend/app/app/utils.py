from sqlalchemy import or_,and_
import datetime
import math
from app.core.config import settings as st
from datetime import datetime,timedelta
from app.models import *
import random
import hashlib
from email_validator import validate_email, EmailNotValidError
import re
import math
import requests
import string
from dateutil.relativedelta import relativedelta
from jose import jwt
from pyfcm import FCMNotification
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import base64



def check_mail(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if re.match(pattern, email):
        return True
    else:
        return False
    
    
    # try:
    #     v = validate_email(email)
    #     email = v["email"] 
    #     return True
    # except EmailNotValidError as e:
    #     # email is not valid, exception message is human-readable
    #     return False


def checkAuthCode(authcode, auth_text):
    salt=st.SALT_KEY
    auth_text=str(salt)+str(auth_text)
    result = hashlib.sha1(auth_text.encode())
    if authcode == result.hexdigest():
        return True
    else:
        return None
    
    
def EmailorMobileNoValidation(email_id):
    email_id=email_id.strip()
    
    if check_mail(email_id) == True:
        return  {'status':1, 'type':1, 'email':email_id, 'mobile':None}
    
    elif email_id.isnumeric():
        return {'status':1, 'type':2, 'email':None, 'mobile':email_id}
    
    else:
        res=email_id.replace("()+-", "")
        
        if res.isnumeric():
            return {'status': 1, 'type': 2, 'email': None, 'mobile': res}
        
        else:
            
            return {'status': 0, 'type': 0, 'email': None, 'mobile': None}
       
def pushNotify(db,user_ids,details,login_user_id):
    api_key="AAAAJndtCwI:APA91bEdwo6X4izLPWkAaoYDIt9zUzrQ8pi_jHUFVne-xMuEDNiqCn1KBSse4TuxRd_5nakioin7l5p8mY7-OhdnXS-SubCqsc-UJS2mDtjJVEY3jq7K9kkE_-3O9LuKJTqPds8Ughi4"
    title=details.title if details.title else "New notification"
    type=details.type if details.type else "nuggets"
    message=details.message if details.message else ""
    data=details.data if details.data else ""
    
    get_user=db.query(User).filter(User.id == login_user_id).first()
    
    if get_user and type != "callend":
        title=get_user.display_name
    
    get_api_token=db.query(ApiTokens.user_id,ApiTokens.device_type,ApiTokens.push_device_id,UserSettings.nuggets,UserSettings.events,UserSettings.friend_request)
    get_api_token=get_api_token.filter(UserSettings.user_id == ApiTokens.user_id,ApiTokens.status == 1,and_(or_(ApiTokens.push_device_id != None,ApiTokens.push_device_id != ""))).group_by(ApiTokens.push_device_id)
    
    if (user_ids != None or user_ids != "") and type(user_ids) == list:
        get_api_token=get_api_token.filter(ApiTokens.user_id.in_(user_ids))
    elif user_ids != "":
        get_api_token=get_api_token.filter(ApiTokens.user_id ==user_ids)
    
    get_api_token=get_api_token.all()
    registration_ids=[]
    
    if get_api_token:
        for token in get_api_token:
            permission_arr = list(str((type == 'callend') and '111' or token[type]))
            if len(permission_arr) > 2 and permission_arr[0] == '1':
                push_id=token.push_device_id
                registration_ids.append(push_id)
    
    registration_ids = [registration_ids[i:i+500] for i in range(0, len(registration_ids), 500)]
    
    if registration_ids:
        fcmMsg={}
        fcmFields=[]
        fcmMsg.update({"title":title,
                       "body":message,
                       "sound":'default'})

        for register_id in registration_ids:
            if type == 'callend' and message == "Call Ended":
                fcmFields.append({"registration_ids":register_id,  #  expects an array of ids
                                  "priority":'high',
                                  'notification':fcmMsg,
                                  'data':data})
            
            else:
                fcmFields.append({"registration_ids":register_id,  # expects an array of ids
                                #   "priority":'high',
                                  'notification':fcmMsg,
                                  'data':data})
            
            url = 'https://fcm.googleapis.com/fcm/send'
            headers = {
                'Authorization': 'key=' + api_key,
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers=headers, json=fcmFields)
            result = response.text

            if response.status_code != 200:
                return False
                # print('FCM Send Error:', result) 
            else:
                pass
                # do something with result
                
    return True

def encryptionString():
    return 'rawcaster@!@#$QWERTxcvbn'

def friendRequestNotifcationEmail(db,senderId,receiverId,flag):   # flag = 1 Friend Request Received flag = 2 Friend Request Accepted
    if senderId != "" and receiverId != "":
        to=''
        sunject=''
        body=''
        phone=''
        sms_message=''
        
        my_friends=db.query(MyFriends).filter(MyFriends.sender_id == senderId,MyFriends.receiver_id == receiverId)
        if flag == 1:
            my_friends=my_friends.filter(MyFriends.request_status == 0).first()
            
            if my_friends:
                displayName=my_friends.user1.display_name if my_friends.sender_id else None
                email_id=my_friends.user1.email_id if my_friends.sender_id else None
                profile_img=my_friends.user1.profile_img if my_friends.sender_id else None
                phone=my_friends.user1.mobile_no if my_friends.sender_id else None
                
                to=email_id
                subject="New Connection Request"
                invite_url=inviteBaseurl()
                encrypt_string=encryptionString()
                url_path=base64.b64encode(f"{senderId}{encrypt_string}")
                url=f"{invite_url}signin/{url_path}/connectionrequest"
                
                body=""  # Pending
                
                sms_message=f'New Connection Request From {displayName} in rawcaster.com'
                
        elif flag == 2:
            my_friends =my_friends.filter(MyFriends.request_status == 1).first()
            if my_friends:
                displayName=my_friends.user2.display_name if my_friends.receiver_id else None
                email_id=my_friends.user2.email_id if my_friends.receiver_id else None
                profile_img=my_friends.user2.profile_img if my_friends.receiver_id else None
                phone=my_friends.user2.mobile_no if my_friends.receiver_id else None
            
                to=email_id
                subject="Connection Accepted Notification"
                invite_url=inviteBaseurl()
                encrypt_string=encryptionString()
                url_path=base64.b64encode(f"{senderId}{encrypt_string}")
                url=f"{invite_url}signin/{url_path}/connectionrequest"
                
                body =''
                sms_message=f'Connection Accepted From {displayName} You`re now connected with {displayName} Clicks on Facebook. You can see his photos, posts and more on his profile'
        return sms_message,body  
    else:
        print("Invalid Parameters")
                
def addNotificationSmsEmail(db,user,email_detail,login_user_id):
    sms_message = email_detail.sms_message if email_detail.sms_message else ""
    mail_message = email_detail.mail_message if email_detail.mail_message else ""
    subject = email_detail.subject if email_detail.subject else ""
    type_ = email_detail.type if email_detail.type else "nuggets"
    email = email_detail.email if email_detail.email else ""

    mobile_nos = ""
    if user:
        get_user =db.query(User.id,User.country_code,User.email_id,User.mobile_no,UserSettings.nuggets,UserSettings.events,UserSettings.friend_request)
        get_user=get_user.filter(UserSettings.user_id == User.id,User.status == 1,User.id.in_(user)).all()
        
        for user in get_user:
            permission_arr = list(user[type_])
            if len(permission_arr) > 2 and permission_arr[1] == "1":
                email += user["email_id"] + ","
            elif len(permission_arr) > 2 and permission_arr[2] == "1" and user["mobile_no"]:
                mobile_nos += user["country_code"] + user["mobile_no"] + ","

    if email:
        add_notification = NotificationSmsEmail(
            user_id=login_user_id,
            type=2,
            mobile_no_email_id=email,
            subject=subject,
            message=mail_message,
            created_at=datetime.now(),
            status=0
        )
        db.add(add_notification)
        db.commit()

    if mobile_nos:
        add_notification = NotificationSmsEmail(
            user_id=login_user_id,
            type=1,
            mobile_no_email_id=mobile_nos,
            subject="",
            message=sms_message,
            created_at=datetime.now(),
            status=0
        )
        db.add(add_notification)
        db.commit()

    return True


def get_friend_requests(db,login_user_id,requested_by,request_status,response_type):
    pending = []
    accepted = []
    rejected = []
    blocked = []

    my_friends =db.query(MyFriends).filter(MyFriends.status == 1)

    if requested_by == 1:  # Friend request sent from this user to others
        my_friends = my_friends.filter_by(sender_id = login_user_id)
        
    elif requested_by == 2:  # Friend request reveived from other users to this user
        my_friends = my_friends.filter_by(receiver_id = login_user_id)
        
    else:  # Both sent and received requests
        my_friends = my_friends.filter(or_(MyFriends.sender_id == login_user_id,MyFriends.receiver_id == login_user_id))

    if request_status and len(request_status) > 0:
        my_friends = my_friends.filter_by(MyFriends.request_status.in_(request_status))

    get_friend_requests = my_friends.all()
    
    if get_friend_requests:
        friend_details=[]
        for friend_requests in get_friend_requests:
            if friend_requests.sender_id == login_user_id:
                friend_id=friend_requests.receiver_id
                
                friend_details.append({"friend_request_id":friend_requests.id,
                                        "user_ref_id":friend_requests.user2.user_ref_id if friend_requests.receiver_id else "",
                                        "user_id":(friend_requests.user2.id if friend_requests.user2.id else "") if friend_requests.receiver_id else "",
                                        "email_id":(friend_requests.user2.email_id if friend_requests.user2.email_id else "") if friend_requests.receiver_id else "",
                                        "first_name":(friend_requests.user2.first_name if friend_requests.user2.first_name else "") if friend_requests.receiver_id else "",
                                        "last_name":(friend_requests.user2.last_name if friend_requests.user2.last_name else "") if friend_requests.receiver_id else "",
                                        "display_name":(friend_requests.user2.display_name if friend_requests.user2.display_name else "") if friend_requests.receiver_id else "",
                                        "gender":(friend_requests.user2.gender if friend_requests.user2.gender else "") if friend_requests.receiver_id else "",
                                        "profile_img":(friend_requests.user2.profile_img if friend_requests.user2.profile_img else "") if friend_requests.receiver_id else ""
                                    })
                
            else:
                friend_id=friend_requests.sender_id
                friend_details.append({"friend_request_id":friend_requests.id,
                                        "user_ref_id":friend_requests.user1.user_ref_id if friend_requests.sender_id else "",
                                        "user_id":(friend_requests.user1.id if friend_requests.user1.id else "") if friend_requests.sender_id else "",
                                        "email_id":(friend_requests.user1.email_id if friend_requests.user1.email_id else "") if friend_requests.sender_id else "",
                                        "first_name":(friend_requests.user1.first_name if friend_requests.user1.first_name else "") if friend_requests.sender_id else "",
                                        "last_name":(friend_requests.user1.last_name if friend_requests.user1.last_name else "") if friend_requests.sender_id else "",
                                        "display_name":(friend_requests.user1.display_name if friend_requests.user1.display_name else "") if friend_requests.sender_id else "",
                                        "gender":(friend_requests.user1.gender if friend_requests.user1.gender else "") if friend_requests.sender_id else "",
                                        "profile_img":(friend_requests.user1.profile_img if friend_requests.user1.profile_img else "") if friend_requests.sender_id else ""
                                    })
            
            if response_type == 1: # only user ids
                if friend_requests.request_status == 0:
                    pending.append(friend_id)  # if pending
                if friend_requests.request_status == 1:
                    accepted.append(friend_id)  #if accepted
                if friend_requests.request_status == 2:
                    rejected.append(friend_id)  # if rejected
                if friend_requests.request_status == 3:
                    blocked.append(friend_id)  # if blocked
            
            else:
                if friend_requests.request_status == 0:
                    pending.append(friend_details)
                if friend_requests.request_status == 1:
                    accepted.append(friend_details)
                if friend_requests.request_status == 2:
                    rejected.append(friend_details)
                if friend_requests.request_status == 3:
                    blocked.append(friend_details)

    return {"pending":pending,"accepted":accepted,"rejected":rejected,"blocked":blocked}            
                
    
    
    
    
def Insertnotification(db,user_id,notification_origin_id,notification_type,ref_id):
    if user_id != notification_origin_id:
        add_notification=Notification(user_id=user_id,notification_origin_id=notification_origin_id,notification_type=notification_type,ref_id=ref_id,created_datetime=datetime.now())
        db.add(add_notification)
        db.commit()
        
        
def get_ip():
    response = requests.get('https://api64.ipify.org?format=json').json()
    return response["ip"]
        
def FindLocationbyIP(userIP):
    userIP = get_ip()
    response = requests.get(f'https://ipwhois.app/json/{userIP}/').json()
    
    if response['success'] == True:
        return {
            "status":1,
            "ip": userIP,
            "city": response.get("city"),
            "region": response.get("region"),
            "country": response.get("country_name"),
            "latitude":response.get("latitude"),
            "longitude":response.get("longitude")
            }
    else:
        return {"status":0}
    
def CheckMobileNumber(db,mobile_no,geo_location):
    result= {'status':0,'msg':'Please enter a valid phone number.'}
    if geo_location != "" and geo_location != None:
        country=geo_location.split(',')
        
        if (country != "") and mobile_no != "":
            found=0
            
            for place in country:
                
                cty=place.strip()
                user_country=db.query(Country).filter(Country.name == cty).first()
                if user_country and user_country.mobile_no_length != "":
                    mobileno=str(mobile_no).replace("+" ,"")
                    mobileno=str(mobile_no).replace("-" ,"")
                    
                    if user_country.id == 156 and geo_location[0:1] == 0:
                        mobileno=geo_location[1:]
                    
                    # When Country name & State Name Same
                    if user_country.mobile_no_length == len(mobile_no):
                        
                        found = 1
                        result={
                                'status':1,
                                'country_code':user_country.country_code,
                                'country_id':user_country.id,
                                'mobile_no':mobileno
                            }
                    else:
                        
                        country_code = len(user_country.country_code) - 1
                        formated_mobileno=mobileno[country_code:]
                        if int(user_country.mobile_no_length) == len(formated_mobileno):
                            
                            found = 1
                            result={
                                    'status':1,
                                    'country_code':user_country.country_code,
                                    'country_id':user_country.id,
                                    'mobile_no':formated_mobileno
                                }
            if found == 0:
                result= {"status":0,"msg":f"Unable to get country in DB '{geo_location}'"} 
                
        else:
            result = {'status':0,'msg':'Mobile number is empty'}
    
    else:
        result = {'status':0,'msg':'Unable to get user location'}
    return result


def inviteBaseurl():
    return 'https://rawcaster.com/'


def OTPverificationtype(db,get_user):
    type=0
    country=''
    if (get_user and get_user.mobile_no != "") or get_user.email_id != "":
        if get_user.geo_location != "":
            country=(get_user.geo_location).split()
            country=country[len(country) - 1]
            country=country.rstrip('.')
        if country != "":
            user_country=db.query(Country).filter(Country.sms_enabled == 1 ,Country.name == country).first()
            if user_country:
                type =1
                update_user=db.query(User).filter(User.id == get_user.id).update({"country_code":user_country.country_code,"country_id":user_country.id})
                db.commit()
                
    return type


def get_friend_requests(db,login_user_id,requested_by,request_status,response_type):
    get_my_friends=db.query(MyFriends).filter(MyFriends.status == 1)
    
    pending=[]
    accepted=[]
    rejected=[]
    blocked=[]
    if requested_by == 1: # Friend request sent from this user to others
        get_my_friends=get_my_friends.filter(MyFriends.sender_id == login_user_id)
        
    elif requested_by == 2: # Friend request reveived from other users to this user
        get_my_friends=get_my_friends.filter(MyFriends.receiver_id == login_user_id)
    
    else:
        get_my_friends=get_my_friends.filter(or_(MyFriends.sender_id == login_user_id ,MyFriends.receiver_id == login_user_id))
        
    if request_status:
        get_my_friends=get_my_friends.filter(MyFriends.request_status.in_([request_status]))
    
    get_my_friends=get_my_friends.all()
    if get_my_friends:
        friend_details=[]
        for frnd_request in get_my_friends:
            if get_my_friends.sender_id == login_user_id:
                friend_id=frnd_request.receiver_id
                friend_details.append({"friend_request_id":friend_id.friend_request_id if friend_id.friend_request_id else None,
                                       "user_ref_id":friend_id.user_ref_id if friend_id.user_ref_id else None,
                                       "user_id":friend_id.user_id if friend_id.user_id else None,
                                       "email_id":friend_id.email_id if friend_id.email_id else "",
                                       "first_name":friend_id.first_name if friend_id.first_name else "",
                                       "last_name":friend_id.last_name if friend_id.last_name else "",
                                       "display_name":friend_id.display_name if friend_id.display_name else "",
                                       "gender":friend_id.gender if friend_id.gender else "",
                                       "profile_img":friend_id.profile_img if friend_id.profile_img else ""
                                    })
                
            else:
                friend_id=get_my_friends.sender_id
                friend_details.append({"friend_request_id":friend_id.friend_request_id if friend_id.friend_request_id else None,
                                       "user_ref_id":friend_id.user_ref_id if friend_id.user_ref_id else None,
                                       "user_id":friend_id.user_id if friend_id.user_id else None,
                                       "email_id":friend_id.email_id if friend_id.email_id else "",
                                       "first_name":friend_id.first_name if friend_id.first_name else "",
                                       "last_name":friend_id.last_name if friend_id.last_name else "",
                                       "display_name":friend_id.display_name if friend_id.display_name else "",
                                       "gender":friend_id.gender if friend_id.gender else "",
                                       "profile_img":friend_id.profile_img if friend_id.profile_img else ""
                                    })
            if response_type == 1:  # only user ids
                if frnd_request.request_status == 0:
                    pending.append(friend_id) # if pending
                elif frnd_request.request_status == 1:
                    accepted.append(friend_id)  # if accepted
                elif frnd_request.request_status == 2:
                    rejected.append(friend_id)  # if rejected
                elif frnd_request.request_status == 3:
                    blocked.append(friend_id) # if blocked
            else:
                if frnd_request.request_status == 0:
                    pending.append(friend_details)
                elif frnd_request.request_status == 1:
                    accepted.append(friend_details)
                elif frnd_request.request_status == 2:
                    rejected.append(friend_details)
                elif frnd_request.request_status == 3:
                    blocked.append(friend_details)
                
    return {"pending":pending,"accepted":accepted,"rejected":rejected,"blocked":blocked}
                  
                  
                  
def MutualFriends(db,login_user_id,user_id):
    mutual_friends=0
    myfriends=get_friend_requests(db,login_user_id,None,None,1)
    otherfriends=get_friend_requests(db,user_id,None,None,1)
    
    if myfriends and otherfriends:
        if myfriends.accepted and otherfriends.accepted:
            mutual_friends =len(set(myfriends.accepted).intersection(otherfriends.accepted))
        else:
            return {"status":0,"msg":"Mutual Friends failed"}
    return mutual_friends

def IsAccountVerified(db,user_id):
    status=False
    get_user=db.query(User).filter(User.id == user_id).first()
    
    if get_user and (get_user.is_email_id_verified == 1 or get_user.is_mobile_no_verified == 1) :
        status=True
    
    return status


    
def get_pagination(row_count=0, page = 1, size=10):
    current_page_no = page if page >= 1 else 1

    total_pages = math.ceil(row_count / size)

    if current_page_no > total_pages:
        current_page_no = total_pages
    
    limit =  current_page_no * size
    offset = limit - size

    if limit > row_count:
        limit = offset + (row_count % size)
    
    limit = limit - offset

    if offset < 0:
        offset = 0
    
    return [limit, offset]



def defaultimage(flag):
    url=''
    if flag == 'profile_img':
        url = ('/uploads/user/default.png', 'https')
    elif flag == 'cover_img':
        url = ('/uploads/user/default_cover.png', 'https')
    elif flag == 'group_icon':
        url = ('/uploads/group/default.png', 'https')
    elif flag == 'event_banner':
        url =('/uploads/eventbanner/eventbanner_default.jpg', 'https')
    elif flag == 'talkshow':
        url = ('/uploads/eventbanner/talkshowbanner_default.jpg', 'https')
    elif flag == 'live':
        url = ('/uploads/eventbanner/livebanner_default.jpg', 'https')
    
    return url


def GetGroupDetails(db,id):
    members=[]
    memberlist=[]
    friendGroup=db.query(FriendGroups).filter(FriendGroups.status == 1,FriendGroups.id == id).first()
    if friendGroup:
        friendGroupMembers=db.query(FriendGroupMembers).filter(FriendGroupMembers.group_id == friendGroup.id).all()
        members.append(friendGroup.id)
        memberlist.append({
                            "user_id":friendGroup.created_by if friendGroup.created_by else "",
                            "email_id":friendGroup.user.email_id if friendGroup.created_by else "",
                            "first_name":friendGroup.user.first_name if friendGroup.created_by else "",
                            "last_name":friendGroup.user.last_name if friendGroup.created_by else "",
                            "display_name":friendGroup.user.display_name if friendGroup.created_by else "",
                            "gender":friendGroup.user.gender if friendGroup.created_by else "",
                            "profile_img":friendGroup.user.profile_img if friendGroup.created_by else ""
                        })
        membercount=1
        if friendGroupMembers:
            for frnd_group in friendGroupMembers:
                members.append(frnd_group.id)
                memberlist.append({
                            "user_id":friendGroup.user_id if friendGroup.user_id else "",
                            "email_id":friendGroup.user.email_id if friendGroup.user_id else "",
                            "first_name":friendGroup.user.first_name if friendGroup.user_id else "",
                            "last_name":friendGroup.user.last_name if friendGroup.user_id else "",
                            "display_name":friendGroup.user.display_name if friendGroup.user_id else "",
                            "gender":friendGroup.user.gender if friendGroup.user_id else "",
                            "profile_img":friendGroup.user.profile_img if friendGroup.user_id else "",
                            "last_seen":friendGroup.user.last_seen if friendGroup.user_id else "",
                            "online":"",
                            "typing":0
                           
                        })
                membercount= membercount+1
                
        group_details={
                        "group_id":friendGroup.id,
                        "group_name":friendGroup.group_name,
                        "group_icon":friendGroup.group_icon,
                        "group_member_count":membercount,
                        "group_owner":friendGroup.created_by,
                        "chat_enabled":friendGroup.chat_enabled,
                        "group_type":1,
                        "group_member_ids":members,
                        "group_members_list":memberlist,
                        "typing":0,
                    }
        return group_details
                
                
    

def paginate(page, size, data, total):
    reply = {"items": data, "total":total, "page": page, "size":size}
    return reply 
        
        
def SendOtp(db,user_id,signup_type):
    # Send OTP for Email or MObile number Verification
    otp=generateOTP()
    otp_time=datetime.now()
    
    check_user_otp_log=db.query(OtpLog).filter(OtpLog.user_id == user_id).first()
    if check_user_otp_log:
        
        check_user_otp_log.otp=otp
        check_user_otp_log.created_date=otp_time
        check_user_otp_log.status=1
        
        db.commit()
        otp_ref_id=check_user_otp_log.id
        
    else:
        add_otp_to_log=OtpLog(otp_type=1, # SignUp
                                user_id=user_id,
                                otp=otp,
                                created_date=otp_time,
                                status=1
                                )
        db.add(add_otp_to_log)
        db.commit()
        
        otp_ref_id=add_otp_to_log.id
    
    get_user=db.query(User).filter(User.id == user_id).first()
    to_mail=get_user.email_id
    subject=f"One Time Password - {otp}"
    message=f"{otp} is your One Time Password"
    if signup_type == 1:
        mail_send=send_email(to_mail,subject,message)
    elif signup_type == 2:
        print("SEND SMS")
    else:
        pass
    return otp_ref_id



async def send_email(to_mail,subject,message):
    if type(to_mail)==list:
        to_mail=to_mail
    else:
        to_mail=[to_mail]

    conf = ConnectionConfig(
        MAIL_USERNAME="AKIAYFYE6EFYF3SQOJHI", 
        MAIL_PASSWORD="BPkaC3u48gAj15i/YBLMDnICroNWdHXRWHMBYGWlDT6Q", 
        MAIL_FROM="rawcaster@rawcaster.com",
        MAIL_PORT=587,
        MAIL_SERVER="email-smtp.us-west-2.amazonaws.com",  # "smtp.gmail.com",
        MAIL_FROM_NAME="Rawcaster",
        MAIL_TLS=True,
        MAIL_SSL=False,
        USE_CREDENTIALS=True
    )
  
    message = MessageSchema(
        subject=subject,
        recipients=to_mail,
        body=message,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return ({"msg": "Email has been sent"})

    
def GenerateUserRegID(id):
    dt = str(int(datetime.utcnow().timestamp()))
    
    refid = "RA"+str(id)+str(dt)+str(random.randint(10000,50000))
    return refid

def GetRawcasterUserID(db,type):
    if type == 2:
        email="helpdesk@rawcaster.com"
    else:
        email="helpdesk@rawcaster.com"
    
    get_user=db.query(User).filter(User.email_id == email,User.status == 1).first()
    if get_user:
        return get_user.id
    else:
        return 0
    
    
    
def logins(db,username, password, device_type, device_id, push_id,login_from,voip_token,app_type,socual=0):
    username=username.strip()
    
    get_user=db.query(User).filter(or_(User.email_id == username,User.mobile_no == username),or_(User.email_id != None,User.mobile_no != None)).first()
    
    if get_user == None or not get_user:
        
        type=EmailorMobileNoValidation(username)
        
        if type['status'] and type['status'] == 1:
            return {"status":2,'type':type['type'],"msg" : "Login Failed. Invalid email id or password"}
        else:
            return {"status":0,"msg" : "Login Failed. Invalid email id or password"}
            
    elif get_user.password != password and socual != 1:
        
        if get_user.status == 2:
            return {"status":0,"msg" : "Your account is currently blocked!"}
        else:
           
            userIP = get_ip()
            add_failure_login=LoginFailureLog(user_id=get_user.id,ip=userIP,created_at=datetime.now(),status=1)
            db.add(add_failure_login)
            db.commit()
            
            get_settings=db.query(Settings).filter(Settings.settings_topic == 'login_block_time').first()
            if get_settings:
                total_block_dur=get_settings.settings_value
                
                curretTime=datetime.now() - timedelta(minutes=total_block_dur)
            else:
                total_block_dur=30
                curretTime=datetime.now() - timedelta(minutes=30)
            
            failure_count=db.query(LoginFailureLog).filter(LoginFailureLog.user_id == get_user.id,LoginFailureLog.created_at > curretTime).count()
            
            if failure_count > 2:
                msg=""
                if total_block_dur < 60:
                    msg=f'{total_block_dur} minutes'
                elif total_block_dur == 60:
                    msg='1 hour'
                elif total_block_dur > 60:
                    msg = f'{math.floor(total_block_dur/60)} hours {total_block_dur % 60} minutes'
                
                return {"status":0, "msg" :f'Your account is currently blocked. Please try again after {msg}'}
                
            return {"status":0, "msg" :'Login Failed. invalid email id or password'}
    
    elif get_user.status == 4: # Account deleted
        return {"status":0, "msg" :'Your account has been removed'}
           
    elif get_user.status == 3: # Admin Blocked user!
        return {"status":0, "msg" :'Your account has been removed'}
        
    elif get_user.status == 2:  # dmin suspended user!
        return {"status":0, "msg" :'Your account is currently blocked!'}
        
    elif get_user.admin_verified_status != 1: # Admin has to verify!
        return {"status":0, "msg" :'This is a beta version of Rawcaster. We are allowing limited number of users at the moment. Your account is currently undergoing an approval process by the administrator. Try to logon again later or contact the Rawcaster personnel that requested your participation in the beta program.'}
    else:
        get_failur_login=db.query(LoginFailureLog).filter(LoginFailureLog.user_id == get_user.id).delete()
        db.commit()
        user_id=get_user.id
        characters=''.join(random.choices(string.ascii_letters+string.digits, k=8))
        token_text=""
        dt = str(int(datetime.utcnow().timestamp()))
        
        token_text=token_text + str(user_id)+str(characters)+str(dt)
        
        if login_from == 2:
            delete_token=db.query(ApiTokens).filter(ApiTokens.user_id == user_id,ApiTokens.device_type == 2).delete()
            db.commit()
        if login_from == 1:
            delete_token=db.query(ApiTokens).filter(ApiTokens.user_id == user_id,ApiTokens.device_type == 1).delete()
            db.commit()
        
        salt_token=token_text
        userIP = get_ip()
        
        add_token=ApiTokens(user_id=user_id,token=token_text,created_at=datetime.now(),renewed_at=datetime.now(),validity=1,
                            device_type=login_from,app_type=app_type,device_id=device_id,push_device_id=push_id,voip_token=voip_token,
                            device_ip=userIP,status=1)
        db.add(add_token)
        db.commit()
        
        if add_token:
            exptime=int(dt)+int(dt)
          
            name=get_user.display_name
            profile_image=get_user.profile_img if get_user.profile_img else None
            salt=st.SALT_KEY
            hash_code=str(token_text)+str(salt)
            
            new_auth_code=hashlib.sha1(hash_code.encode()).hexdigest()
            
            user_id=get_user.id
            paylod={ 'iat': dt,
                    'iss' : 'localhost',
                    'exp' : exptime,
                    'token' : token_text}
        
            
            token_text = jwt.encode(paylod, st.SECRET_KEY) 
            
            exptime= datetime.fromtimestamp(int(exptime))
            if login_from == 2:
                # Update Sender
                update_sender=db.query(FriendsChat).filter(FriendsChat.sender_id == user_id).update({"sender_delete":1,"sender_deleted_datetime":datetime.now()}).all()
                update_recevicr=db.query(FriendsChat).filter(FriendsChat.receiver_id == user_id).update({"receiver_delete":1,"receiver_deleted_datetime":datetime.now()}).all()
                db.commit()
            
            if get_user.referral_expiry_date != None and get_user.user_status_id == 3:
                if dt >= get_user.referral_expiry_date:
                    update_user=db.query(User).filter(User.id == get_user.id).update({'user_status_id':1,'referral_expiry_date':None})
                    db.commit()
            return {"status":1,"msg":"Success","salt_token":salt_token,"token":token_text,"email":username,"expirytime":exptime,"profile_image":profile_image,"name":name,"user_id":user_id,"authcode":new_auth_code,"acc_verify_status":get_user.is_email_id_verified}
        else:
            return {"status":0,"msg" : "Failed to Generate Access Token. try again"}
            
            
def getModelError(errors):
    if errors != "" or errors != None:
        reply=""
        for err in errors:
            if err != "" and err != None:
                reply=err
        
        return reply
            

def ChangeReferralExpiryDate(db,referrerid):
    referrer=db.query(User).filter(User.id == referrerid).first()
    if referrer:
        expiry_date=referrer.referral_expiry_date
        user_status_id=referrer.user_status_id
        if referrer.user_status_id == 1:
            user_status=db.query(UserStatusMaster).filter(UserStatusMaster.id == 3).first()
            if user_status:
                total_referral_point=int(referrer.total_referral_point)+ 1
                if user_status.referral_needed <= total_referral_point:
                    expiry_date=datetime.now()
                    if referrer.referral_expiry_date != None:
                        expiry_date=referrer.referral_expiry_date
                    expiry_date=datetime.now() + relativedelta(months = 1)
                  
                    total_referral_point=total_referral_point - user_status.referral_needed
                    user_status_id=3
            
        else:
            total_referral_point=referrer+total_referral_point + 1
        
        update_user=db.query(User).filter(User.id == referrer.id).update({"user_status_id":user_status_id,"referral_expiry_date":expiry_date,"total_referral_point":total_referral_point})
        db.commit()
        
        
def checkToken(db,access_token):
    try:
    
        payload = jwt.decode(access_token, st.SECRET_KEY, algorithms=['HS256'])        
        
        if payload != "" or payload != None:
            access_token=payload['token']
            get_token_details=db.query(ApiTokens).filter(ApiTokens.status == 1,ApiTokens.token == access_token.strip()).first()
            if not get_token_details:
                return False
            current_time=int(datetime.utcnow().timestamp())

            last_request_time= int(round((get_token_details.renewed_at).timestamp()))
            if last_request_time + 604800 < current_time:
                get_token_details.status = -1
                db.commit()
                return False
            else:
                get_token_details.renewed_at =datetime.now()
                db.commit()
                return access_token
                
        else:
            return False
    except:
        return False   
    

def generateOTP():
    # return random.randint( 100000,999999)
    return 123456
      
        
#   --------------------------------------------------
# def file_storage(file):
    
#     base_dir = st.BASE_UPLOAD_FOLDER+"/upload_files/"

#     dt = str(int(datetime.utcnow().timestamp()))
   
#     try:
#         os.makedirs(base_dir, mode=0o777, exist_ok=True)
#     except OSError as e:
#         sys.exit("Can't create {dir}: {err}".format(
#             dir=base_dir, err=e))
    
#     filename=file.filename

#     file_properties = filename.split(".")

#     file_extension = file_properties[-1]

#     file_properties.pop()
#     file_splitted_name = file_properties[0]
    

#     write_path = f"{base_dir}{file_splitted_name}{dt}.{file_extension}"
#     db_path = f"/upload_files/{file_splitted_name}{dt}.{file_extension}"
   
#     with open(write_path, "wb") as new_file:
#         shutil.copyfileobj(file.file, new_file)
        
#     return db_path




    
# def common_date(date, without_time=None):

#     datetime = date.strftime("%d-%m-%Y %I:%M:%S %p")

#     if without_time == 1:
#         datetime = date.strftime("%d-%m-%Y")

#     return datetime

# def common_date_only(date, without_time=None):

#     datetime = date.strftime("%d-%m-%y")

#     if without_time == 1:
#         datetime = date.strftime("%d-%m-%y")

#     return datetime
# def common_time_only(date, without_time=None):

#     datetime = date.strftime("%H:%M:%S")

#     return datetime


