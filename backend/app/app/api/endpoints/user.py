from fastapi import APIRouter, Depends, HTTPException, Form,File,UploadFile
from typing import Optional,List
from fastapi.encoders import jsonable_encoder
from app.models import *
from app.core.security import *
from app.utils import common_date,file_storage,paginate,pagination
from app.api import deps
from sqlalchemy.orm import Session
from app.core.security import settings
from datetime import datetime

router = APIRouter()


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