from fastapi import APIRouter, Depends, HTTPException, Form,File,UploadFile
from typing import Optional,List
from fastapi.encoders import jsonable_encoder
from app.models import *
from app.core.security import *
from app.utils import common_date,file_storage,paginate,pagination
from app.api import deps
from sqlalchemy.orm import Session
from app.core.security import settings
from datetime import datetime,date

router = APIRouter()


# 1 Signup User
@router.post("/signup")
async def signup(db:Session=Depends(deps.get_db),signup_type:int=Form(...,description="1-Email,2-Phone Number",ge=1,le=2),first_name:str=Form(...,max_length=100),
                    last_name:str=Form(None,max_length=100),display_name:str=Form(None,max_length=100),gender:int=Form(None,ge=1,le=2,description="1-male,2-female"),
                    dob:date=Form(None),email_id:str=Form(None,max_length=100),country_code:int=Form(None),country_id:int=Form(None),
                    mobile_no:int=Form(None),password:str=Form(...),confirm_password:str=Form(...),geo_location:str=Form(None),
                    latitude:int=Form(None),longitude:int=Form(None),ref_id:str=Form(None),auth_code:str=Form(...,description="SALT + email_id"),
                    device_id:str=Form(None),push_id:str=Form(None),device_type:int=Form(None),auth_code1:str=Form(...,description="SALT +username"),
                    voip_token:str=Form(None),app_type:int=Form(...,description="1-Android,2-IOS",ge=1,le=2)):

    return "done"


# 2 - Signup Verification by OTP
@router.post("/signupverify")
async def signupverify(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),otp_ref_id:str=Form(...,description="From service no. 1"),otp:int=Form(...)):
    return "done"          


# 3 - Resend OTP

@router.post("/resendotp")
async def resendotp(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),otp_ref_id:int=Form(None),token:str=Form(...),otp_flag:str=Form(None)):
    return "done"



# 4 - Login
@router.post("/login")
async def login(db:Session=Depends(deps.get_db),auth_code:str=Form(...,description="SALT + otp_ref_id"),username:str=Form(...,description="Email ID"),
                    password:str=Form(...),device_id:str=Form(None),push_id:str=Form(None),device_type:int=Form(None),voip_token:str=Form(None),
                    app_type:int=Form(None,description="1-> Android, 2-> IOS",ge=1,le=2)):
    return "done"





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
@router.post("/invitetorawcaster")
async def invitetorawcaster(db:Session=Depends(deps.get_db),token:str=Form(...),email_id:list=Form(...,description="email ids"),
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