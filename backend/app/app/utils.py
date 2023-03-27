from sqlalchemy import or_
import datetime
import math
from app.core.config import settings as st
from datetime import datetime,timedelta
from app.models import *
import random
import hashlib
from email_validator import validate_email, EmailNotValidError
import socket
import math
import requests
import string
from dateutil.relativedelta import relativedelta
from jose import jwt

def check_mail(email):
    try:
        v = validate_email(email)
        email = v["email"] 
        return True
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        return False


def checkAuthCode(authcode, auth_text):
    salt=st.SALT_KEY
    auth_text=salt+auth_text
    result = hashlib.sha1(auth_text.encode())
    if authcode == result.hexdigest():
        return True
    else:
        return None
    
    
def EmailorMobileNoValidation(email_id):
    email_id=email_id.strip()
    
    if check_mail(email_id) == True:
        return  {'status':1, 'type':1, 'email':email_id, 'mobile':None}
    
    elif email_id:
        
        return {'status':1, 'type':2, 'email':None, 'mobile':email_id}
    else:
        return {'status':0, 'type':2, 'email':None, 'mobile':None}
       
       
 
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
            return {"status":2,'type':type['type'],"msg" : "Login Failed. invalid email id or password"}
        else:
            return {"status":0,"msg" : "Login Failed. invalid email id or password"}
            
    elif get_user.password != password and socual != 1:
        
        if get_user.status == 2:
            return {"status":0,"msg" : "Your account is currently blocked!"}
        else:
           
            userIP = get_ip()
            add_failure_login=LoginFailureLog(user_id=get_user.id,ip=userIP,created_at=datetime.now())
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
                    msg=f'{total_block_dur}minutes'
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
            profile_image=get_user.profile_img
            salt=st.SALT_KEY
            hash_code=str(token_text)+str(salt)
            
            new_auth_code=hashlib.sha1(hash_code.encode()).hexdigest()
            
            user_id=get_user.id
            paylod={ 'iat': dt,
                    'iss' : 1,
                    'exp' : exptime,
                    'token' : token_text}
        
            
            ALGORITHM = "HS256"
            
            token_text = jwt.encode(paylod, st.SECRET_KEY, algorithm=ALGORITHM) 
            
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
    referrer=db.qurey(User).filter(User.id == referrerid).first()
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
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        if payload != "":
            access_token=payload.token
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
    return random.randint( 100000,999999)
      
        
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



# def pagination(row_count=0, page = 1, size=10):
#     current_page_no = page if page >= 1 else 1

#     total_pages = math.ceil(row_count / size)

#     if current_page_no > total_pages:
#         current_page_no = total_pages
    
#     limit =  current_page_no * size
#     offset = limit - size

#     if limit > row_count:
#         limit = offset + (row_count % size)
    
#     limit = limit - offset

#     if offset < 0:
#         offset = 0
    
#     return [limit, offset]


# def paginate(page, size, data, total):
#     reply = {"items": data, "total":total, "page": page, "size":size}
#     return reply



    
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



